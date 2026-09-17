"""ER 완료 Triple을 Neo4j 적재용 Node/Relationship JSON으로 변환하는 골격."""

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any, Sequence

from src.extraction.ontology import is_allowed_signature


# 입력: resolved_triples.json
# 출력: neo4j_nodes.json, neo4j_relationships.json
# TODO 2. 같은 이름이라도 EntityType이 다르면 별도 Node로 유지한다.
# TODO 3. Triple을 relationship row로 변환하고 source_doc_id/evidence를 보존한다.
# TODO 4. 같은 subject-relation-object 관계의 evidence/source_doc_id 병합 규칙을 결정한다.
# TODO 5. 실제 ontology signature와 다른 row는 적재 전에 Reject한다.
# TODO 6. 적재용 JSON을 저장하고 다시 읽어 구조를 확인한다.


# TODO 7. resolved_triples.json 기반 Node/Relationship 입력 형식을 확정한다.
# TODO 8. extra_accommodations.jsonl을 Accommodation Node로 변환하고 ID, 이름, 주소,
#           좌표, 설명, source_file을 Node metadata로 보존한다.
# TODO 9. extra_nearby.jsonl을 Experience/nearby Node로 변환하고 extra_id 중복을 방지한다.
# TODO 10. Festival과 Accommodation/Experience 사이의 NEARBY 관계를 생성한다.
# TODO 11. Relationship metadata에 distance_meters, source_file, source_doc_id를 보존한다.
# TODO 12. Node metadata와 Relationship metadata의 최종 field mapping을 확정한다.

def build_nodes(resolved_triples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolved Triple에서 Neo4j Node 목록을 만든다."""
    nodes: dict[tuple[Any, Any], dict[str, Any]] = {}

    for raw in resolved_triples:
        triple = _payload(raw)
        for name, type_name in (("subject", "subject_type"), ("object", "object_type")):
            key = (triple[type_name], triple[name])
            nodes.setdefault(
                key,
                {
                    "entity_type": triple[type_name],
                    "canonical_name": triple[name],
                },
            )

    return list(nodes.values())


def build_relationships(resolved_triples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolved Triple을 Neo4j Relationship row로 변환한다."""
    relationships = {}

    for raw in resolved_triples:
        triple = _payload(raw)
        subject = {"entity_type": triple["subject_type"], "canonical_name": triple["subject"]}
        object_ = {"entity_type": triple["object_type"], "canonical_name": triple["object"]}
        key = (subject["entity_type"], subject["canonical_name"], triple["relation"], object_["entity_type"], object_["canonical_name"])
        row = relationships.setdefault(key, {"subject": subject, "relation": triple["relation"], "object": object_, "source_doc_id": [], "evidence": []})
        _add_unique(row["source_doc_id"], triple.get("source_doc_id"))
        _add_unique(row["evidence"], triple.get("evidence"))

    return list(relationships.values())


def prepare_neo4j_data(
    resolved_triples: Sequence[dict[str, Any]],
    extra_accommodations_path: str | Path | None = None,
    extra_nearby_path: str | Path | None = None,
    festivals_path: str | Path | None = None,
    nearby_radius_km: float = 3.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Node와 Relationship을 함께 생성한다."""

    nodes = build_nodes(resolved_triples)
    relationships = build_relationships(resolved_triples)

    extras = []
    accommodations = read_jsonl(extra_accommodations_path) if extra_accommodations_path else []
    nearby = read_jsonl(extra_nearby_path) if extra_nearby_path else []
    if festivals_path and accommodations:
        festivals = read_jsonl(festivals_path)
        accommodations = link_accommodations_to_festivals(accommodations, festivals, nearby_radius_km)
    extras.extend(accommodations)
    extras.extend(nearby)
    if extras:
        nodes.extend(build_extra_nodes(extras))
        festival_names = {
            str(record.get("related_festival_id")): record.get("metadata", {}).get("festival_title")
            for record in extras
            if record.get("related_festival_id") is not None and record.get("metadata", {}).get("festival_title")
        }
        relationships.extend(build_extra_relationships(extras, festival_names))

    return nodes, relationships


def build_extra_nodes(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accommodation/nearby 레코드를 Neo4j Node row로 변환한다."""
    nodes = {}
    for record in records:
        extra_id = str(record["extra_id"])
        source_type = record.get("source_type", "nearby")
        entity_type = "Accommodation" if source_type == "accommodation" else "Experience"
        nodes.setdefault((entity_type, extra_id), {
            "entity_type": entity_type,
            "canonical_name": record.get("title", extra_id),
            "extra_id": extra_id,
            "name": record.get("title", extra_id),
            "address": record.get("address"),
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude"),
            "text": record.get("text", ""),
            "source_file": record.get("source_file"),
        })
    return list(nodes.values())


def build_extra_relationships(
    records: Sequence[dict[str, Any]],
    festival_names_by_id: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """extra 레코드의 Festival-Extra NEARBY 관계를 만든다."""
    relationships = []
    festival_names_by_id = festival_names_by_id or {}
    for record in records:
        festival_id = record.get("related_festival_id")
        festival_name = festival_names_by_id.get(str(festival_id)) if festival_id is not None else record.get("metadata", {}).get("festival_title")
        if not festival_name:
            continue
        extra_type = "Accommodation" if record.get("source_type") == "accommodation" else "Experience"
        properties = {"source_file": record.get("source_file")}
        if record.get("distance_meters") is not None:
            properties["distance_meters"] = record["distance_meters"]
        relationships.append({
            "subject": {"entity_type": "Festival", "canonical_name": festival_name},
            "relation": "NEARBY",
            "object": {"entity_type": extra_type, "canonical_name": record.get("title", str(record["extra_id"]))},
            **properties,
        })
    return relationships


def link_accommodations_to_festivals(
    accommodations: Sequence[dict[str, Any]],
    festivals: Sequence[dict[str, Any]],
    radius_km: float = 3.0,
) -> list[dict[str, Any]]:
    """좌표 기준으로 3km 이내 가장 가까운 Festival을 숙소에 연결한다."""
    festival_points = []
    for festival in festivals:
        metadata = festival.get("metadata", festival)
        if metadata.get("latitude") is not None and metadata.get("longitude") is not None:
            festival_points.append((str(festival["doc_id"]), festival.get("title", festival["doc_id"]), metadata))

    linked = []
    for accommodation in accommodations:
        record = dict(accommodation)
        lat, lon = record.get("latitude"), record.get("longitude")
        candidates = []
        if lat is not None and lon is not None:
            for festival_id, title, metadata in festival_points:
                distance = _haversine_km(lat, lon, metadata["latitude"], metadata["longitude"])
                if distance <= radius_km:
                    candidates.append((distance, festival_id, title))
        if candidates:
            distance, festival_id, title = min(candidates)
            record["related_festival_id"] = festival_id
            record["distance_meters"] = round(distance * 1000, 3)
            record.setdefault("metadata", {})["festival_title"] = title
        if candidates:
            linked.append(record)
    return linked


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    d_lat, d_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """JSONL 파일을 읽는다."""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def enrich_accommodations_file(
    accommodations_path: str | Path,
    festivals_path: str | Path,
    output_path: str | Path,
    radius_km: float = 3.0,
) -> None:
    """숙소와 가장 가까운 3km 이내 Festival 정보를 linked JSONL로 저장한다."""
    linked = link_accommodations_to_festivals(
        read_jsonl(accommodations_path), read_jsonl(festivals_path), radius_km
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in linked),
        encoding="utf-8",
    )


def reject_invalid_triples(resolved_triples: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted, rejected = [], []
    for raw in resolved_triples:
        triple = _payload(raw)
        (accepted if is_allowed_signature(triple["subject_type"], triple["relation"], triple["object_type"]) else rejected).append(raw)
    return accepted, rejected


def save_neo4j_data(path: str | Path, nodes: Sequence[dict[str, Any]], relationships: Sequence[dict[str, Any]]) -> None:
    Path(path).write_text(json.dumps({"nodes": list(nodes), "relationships": list(relationships)}, ensure_ascii=False, indent=2), encoding="utf-8")


def _payload(raw: dict[str, Any]) -> dict[str, Any]:
    triple = raw.get("triple", raw)
    def endpoint(name: str):
        value = triple[name]
        return value.get("canonical_name", value.get("name")) if isinstance(value, dict) else value
    return {**triple, "subject": endpoint("subject"), "object": endpoint("object"),
            "subject_type": triple.get("subject_type", triple["subject"].get("entity_type") if isinstance(triple["subject"], dict) else None),
            "object_type": triple.get("object_type", triple["object"].get("entity_type") if isinstance(triple["object"], dict) else None)}


def _add_unique(values: list[Any], value: Any) -> None:
    for item in (value if isinstance(value, list) else [value]):
        if item is not None and item not in values:
            values.append(item)


# 최소 예시: {"name": "유플페", "entity_type": "Festival"}
# 완료 조건: 모든 Relationship의 양 끝 Node가 Node 목록에 존재한다.
# Freeze point: Node key와 Relationship property 이름은 적재 전 승인 없이 변경하지 않는다.
