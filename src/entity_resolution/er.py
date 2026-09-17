"""검증된 Triple의 Entity mention을 canonical entity로 통합하는 ER 골격."""

from typing import Any, Mapping, Sequence
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import json
from pathlib import Path

FUZZY_AUTO_MERGE_THRESHOLD = 0.85

INPUT_FILENAME = "validated_triples.json"

OUTPUT_FILENAMES = {
    "entities": "resolved_entities.json",
    "triples": "resolved_triples.json",
    "candidates": "er_candidates.json",
    "report": "er_report.json",
}

_PARENTHESIS_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
# Keep Unicode letters/numbers and normalize punctuation to separators.
_NON_NAME_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")

# 입력: validated_triples.json 또는 ValidationRecord의 clean Triple 목록
# 출력: resolved_entities.json, resolved_triples.json, er_candidates.json, er_report.json
# TODO 1. subject/object와 타입, 문서 ID, role을 Entity mention 목록으로 수집한다.
# TODO 2. 공백·특수문자·괄호 처리 규칙을 고정한 comparison_name 정규화 함수를 만든다.
# TODO 3. (entity_type, comparison_name)을 기준으로 exact match를 그룹화한다.
# TODO 4. 같은 타입 안에서만 fuzzy 후보를 만들고 similarity와 decision을 보존한다.
# TODO 5. embedding은 자동 병합이 아니라 후보 보강용으로만 연결한다.
# TODO 6. canonical_name을 결정하고 원본 이름과 매핑한다.
# TODO 7. 모든 Triple의 subject/object를 canonical_name으로 치환한다.
# TODO 8. ER 이후 중복 Triple을 제거하고 source_doc_id와 evidence를 보존한다.
# TODO 9. 병합 전후 Entity 수, 후보 수, 자동/수동 판정 수를 er_report에 저장한다.


# TODO 10. ER input/output file contract: validated_triples.json -> resolved_entities.json,
#           resolved_triples.json, er_candidates.json, er_report.json.
# TODO 11. extra_accommodations.jsonl/extra_nearby.jsonl의 ID와 Festival entity 연결 규칙을 정한다.

def collect_entity_mentions(
    validated_triples: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Triple의 subject/object를 Entity mention 레코드로 수집한다."""

    mentions = []

    for idx, record in enumerate(validated_triples):
        triple = _as_triple_dict(record)
        source_doc_id = triple.get("source_doc_id")

        for role in ("subject", "object"):
            name = triple.get(role)
            entity_type = triple.get(f"{role}_type")

            error = None

            if not name:
                error = f"missing_{role}"
            elif not entity_type:
                error = f"missing_{role}_type"

            mentions.append({
                "mention_id": f"{idx}:{role}",
                "name": name,
                "entity_type": entity_type,
                "source_doc_id": source_doc_id,
                "role": role,
                "error": error,
            })

    return mentions


def _as_triple_dict(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        nested = record.get("triple")
        if isinstance(nested, Mapping):
            return dict(nested)
        return dict(record)

    triple = getattr(record, "triple", None)
    if isinstance(triple, Mapping):
        return dict(triple)

    model_dump = getattr(record, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            triple = dumped.get("triple")
            if isinstance(triple, Mapping):
                return dict(triple)
            if "subject" in dumped or "object" in dumped:
                return dict(dumped)

    raise TypeError("각 입력 항목은 dict 또는 ValidationRecord여야 합니다.")

def normalize_comparison_name(name: str) -> str:
    """Entity 비교용 이름을 정규화한다. 원본 name은 변경하지 않는다."""

    if not isinstance(name, str):
        return ""

    comparison_name = name.strip().lower()

    # 괄호와 괄호 안 내용 제거
    comparison_name = _PARENTHESIS_RE.sub(" ", comparison_name)

    # 특수문자를 공백으로 통일
    comparison_name = _NON_NAME_RE.sub(" ", comparison_name)

    # 연속 공백을 하나로 정리
    comparison_name = _WHITESPACE_RE.sub(" ", comparison_name).strip()

    return comparison_name

def group_exact_matches(
    mentions: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """(entity_type, comparison_name)을 기준으로 exact match를 그룹화한다."""

    grouped = defaultdict(list)

    for mention in mentions:
        comparison_name = normalize_comparison_name(
            mention.get("name", "")
        )

        mention["comparison_name"] = comparison_name

        key = (
            mention.get("entity_type"),
            comparison_name,
        )

        if mention.get("error") is not None or not comparison_name:
            continue
        grouped[key].append(mention)

    exact_groups = []

    for group_id, ((entity_type, comparison_name), members) in enumerate(
        grouped.items()
    ):
        exact_groups.append({
            "group_id": f"exact_{group_id}",
            "entity_type": entity_type,
            "comparison_name": comparison_name,
            "mentions": members,
        })

    return exact_groups

def resolve_entities(
    mentions: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """exact/fuzzy 후보를 만들고 canonical entity와 매핑 결과를 반환한다."""

    entities = []
    candidates = []
    mention_to_entity = {}

    prepared = []

    for mention in mentions:
        if mention.get("error") is not None:
            continue

        row = dict(mention)

        comparison_name = row.get("comparison_name")

        if not comparison_name:
            comparison_name = normalize_comparison_name(
                row.get("name", "")
            )

        row["comparison_name"] = comparison_name
        prepared.append(row)

    exact_groups = {}

    for mention in prepared:
        key = (
            mention.get("entity_type"),
            mention.get("comparison_name"),
        )

        exact_groups.setdefault(key, []).append(mention)

    for idx, ((entity_type, comparison_name), members) in enumerate(
        exact_groups.items()
    ):
        entity_id = f"entity_{idx}"

        entities.append({
            "entity_id": entity_id,
            "canonical_name": members[0].get("name"),
            "entity_type": entity_type,
            "comparison_name": comparison_name,
            "mention_ids": [
                member.get("mention_id")
                for member in members
            ],
        })

        for member in members:
            mention_to_entity[member.get("mention_id")] = entity_id

    parent = list(range(len(entities)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left_index: int, right_index: int) -> None:
        left_root = find(left_index)
        right_root = find(right_index)
        if left_root != right_root:
            parent[right_root] = left_root

    blocks = defaultdict(list)
    for index, entity in enumerate(entities):
        name = entity["comparison_name"]
        blocks[(entity["entity_type"], name[:2], len(name) // 3)].append(index)

    pairs = {
        (i, j)
        for block in blocks.values()
        for offset, i in enumerate(block)
        for j in block[offset + 1:]
    }
    for i, j in pairs:
            left = entities[i]
            right = entities[j]

            # 타입이 다르면 절대 비교하거나 병합하지 않는다.
            if left["entity_type"] != right["entity_type"]:
                continue

            if left["comparison_name"] == right["comparison_name"]:
                continue

            similarity = SequenceMatcher(
                None,
                left["comparison_name"],
                right["comparison_name"],
            ).ratio()

            decision = (
                "review"
                if similarity >= FUZZY_AUTO_MERGE_THRESHOLD
                else "separate"
            )

            candidates.append({
                "left_entity_id": left["entity_id"],
                "right_entity_id": right["entity_id"],
                "entity_type": left["entity_type"],
                "left_name": left["canonical_name"],
                "right_name": right["canonical_name"],
                "similarity": round(similarity, 4),
                "candidate_type": "fuzzy",
                "decision": decision,
            })

    entity_groups = defaultdict(list)
    for index, entity in enumerate(entities):
        entity_groups[find(index)].append(entity)

    merged_entities = []
    old_to_new = {}

    for new_index, members in enumerate(entity_groups.values()):
        entity = dict(members[0])
        entity["entity_id"] = f"entity_{new_index}"
        entity["mention_ids"] = [
            mention_id
            for member in members
            for mention_id in member["mention_ids"]
        ]
        merged_entities.append(entity)
        for member in members:
            old_to_new[member["entity_id"]] = entity["entity_id"]

    for mention_id, entity_id in mention_to_entity.items():
        mention_to_entity[mention_id] = old_to_new[entity_id]

    merged_candidates = []
    for candidate in candidates:
        left_id = old_to_new[candidate["left_entity_id"]]
        right_id = old_to_new[candidate["right_entity_id"]]
        candidate = dict(candidate)
        candidate["left_entity_id"] = left_id
        candidate["right_entity_id"] = right_id
        if left_id == right_id:
            candidate["merged_entity_id"] = left_id
        merged_candidates.append(candidate)

    return {
        "entities": merged_entities,
        "mention_to_entity": mention_to_entity,
        "candidates": merged_candidates,
    }

def add_embedding_candidates(
    resolution: dict[str, Any],
    embed_texts,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Embedding은 자동 병합하지 않고 fuzzy 후보 보강용으로만 사용한다."""

    entities = resolution["entities"]
    candidates = list(resolution["candidates"])

    if not entities:
        return resolution

    names = [entity["canonical_name"] for entity in entities]
    vectors = embed_texts(names)

    candidate_by_pair = {
        tuple(sorted((
            candidate["left_entity_id"],
            candidate["right_entity_id"],
        ))): candidate
        for candidate in candidates
    }

    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            left = entities[i]
            right = entities[j]

            # 같은 타입만 비교
            if left["entity_type"] != right["entity_type"]:
                continue

            pair_key = tuple(sorted((
                left["entity_id"],
                right["entity_id"],
            )))

            # cosine similarity
            left_vec = vectors[i]
            right_vec = vectors[j]

            dot = sum(a * b for a, b in zip(left_vec, right_vec))
            left_norm = sum(value * value for value in left_vec) ** 0.5
            right_norm = sum(value * value for value in right_vec) ** 0.5

            if left_norm == 0 or right_norm == 0:
                similarity = 0.0
            else:
                similarity = dot / (left_norm * right_norm)

            if similarity < threshold:
                continue

            # 기존 fuzzy 후보가 있으면 embedding 점수만 보강
            if pair_key in candidate_by_pair:
                candidate_by_pair[pair_key]["embedding_similarity"] = round(
                    similarity, 4
                )

            # 기존 후보가 없으면 검토 후보로 추가
            else:
                candidates.append({
                    "left_entity_id": left["entity_id"],
                    "right_entity_id": right["entity_id"],
                    "entity_type": left["entity_type"],
                    "left_name": left["canonical_name"],
                    "right_name": right["canonical_name"],
                    "similarity": None,
                    "embedding_similarity": round(similarity, 4),
                    "candidate_type": "embedding",
                    "decision": "review",
                })

                candidate_by_pair[pair_key] = candidates[-1]

    return {
        **resolution,
        "candidates": candidates,
    }

def build_canonical_mapping(
    resolution: dict[str, Any],
    mentions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """canonical_name을 결정하고 원본 mention 정보를 보존한다."""

    entities = resolution["entities"]

    mention_by_id = {
        mention["mention_id"]: mention
        for mention in mentions
    }

    name_mapping = []

    for entity in entities:
        mention_ids = entity.get("mention_ids", [])

        members = [
            mention_by_id[mention_id]
            for mention_id in mention_ids
            if mention_id in mention_by_id
        ]

        if not members:
            continue

        name_counts = Counter(
            member.get("name")
            for member in members
            if member.get("name")
        )

        # Freeze point:
        # 가장 자주 등장한 원본 이름
        # -> 동률이면 짧은 이름
        # -> 그래도 동률이면 사전순
        if name_counts:
            canonical_name = sorted(
                name_counts,
                key=lambda name: (
                    -name_counts[name],
                    len(name),
                    name.lower(),
                ),
            )[0]
        else:
            canonical_name = ""

        entity["canonical_name"] = canonical_name

        # 원본 이름 / 문서 ID / role 재현용
        entity["source_mentions"] = [
            {
                "mention_id": member.get("mention_id"),
                "name": member.get("name"),
                "source_doc_id": member.get("source_doc_id"),
                "role": member.get("role"),
            }
            for member in members
        ]

        # Festival-extra 연결 등에 사용
        entity["source_doc_ids"] = list(dict.fromkeys(
            member.get("source_doc_id")
            for member in members
            if member.get("source_doc_id")
        ))

        for member in members:
            name_mapping.append({
                "mention_id": member.get("mention_id"),
                "original_name": member.get("name"),
                "entity_type": member.get("entity_type"),
                "source_doc_id": member.get("source_doc_id"),
                "role": member.get("role"),
                "entity_id": entity["entity_id"],
                "canonical_name": canonical_name,
            })

    return {
        **resolution,
        "entities": entities,
        "name_mapping": name_mapping,
    }

def replace_with_canonical_names(
    validated_triples: Sequence[dict[str, Any]],
    resolution: dict[str, Any],
) -> list[dict[str, Any]]:
    """모든 Triple의 subject/object를 canonical_name으로 치환한다."""

    name_mapping = resolution.get("name_mapping", [])

    canonical_map = {
        (
            row.get("entity_type"),
            normalize_comparison_name(row.get("original_name", "")),
        ): row.get("canonical_name")
        for row in name_mapping
    }

    resolved_triples = []

    for triple in validated_triples:
        resolved = dict(triple)

        subject_key = (
            triple.get("subject_type"),
            normalize_comparison_name(triple.get("subject", "")),
        )
        object_key = (
            triple.get("object_type"),
            normalize_comparison_name(triple.get("object", "")),
        )

        resolved["subject"] = canonical_map.get(
            subject_key,
            triple.get("subject"),
        )

        resolved["object"] = canonical_map.get(
            object_key,
            triple.get("object"),
        )

        resolved_triples.append(resolved)

    return resolved_triples

def deduplicate_resolved_triples(
    resolved_triples: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """ER 이후 중복 Triple을 제거하고 source_doc_id와 evidence를 보존한다."""

    grouped = {}
    source_doc_ids_by_key = defaultdict(dict)
    evidences_by_key = defaultdict(dict)

    for triple in resolved_triples:
        key = (
            triple.get("subject"),
            triple.get("subject_type"),
            triple.get("relation"),
            triple.get("object"),
            triple.get("object_type"),
        )

        if key not in grouped:
            row = dict(triple)

            grouped[key] = row

        source_doc_id = triple.get("source_doc_id")
        evidence = triple.get("evidence")

        if source_doc_id:
            source_doc_ids_by_key[key].setdefault(source_doc_id, None)

        if evidence:
            evidences_by_key[key].setdefault(evidence, None)

    deduplicated = []

    for key, row in grouped.items():
        # 기존 단일 필드는 제거하고 리스트 형태로 보존
        row.pop("source_doc_id", None)
        row.pop("evidence", None)
        row["source_doc_ids"] = list(source_doc_ids_by_key[key])
        row["evidences"] = list(evidences_by_key[key])

        deduplicated.append(row)

    return deduplicated


def link_extra_to_festival(
    extras: Sequence[dict[str, Any]],
    resolved_entities: Sequence[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, Any]]:
    """extra 행의 related_festival_id를 Festival entity ID에 연결한다."""

    if isinstance(resolved_entities, dict):
        entities = resolved_entities.get("entities", [])
    else:
        entities = resolved_entities

    festival_id_to_entity: dict[str, str] = {}
    for entity in entities:
        if entity.get("entity_type") != "Festival":
            continue

        entity_id = entity.get("entity_id")
        if not entity_id:
            continue

        identifiers = set()
        for field in ("festival_id", "contentid", "source_doc_id"):
            value = entity.get(field)
            if value is not None and str(value).strip():
                identifiers.add(str(value).strip())
        identifiers.update(
            str(value).strip()
            for value in entity.get("source_doc_ids", [])
            if value is not None and str(value).strip()
        )
        identifiers.update(
            str(mention.get("source_doc_id")).strip()
            for mention in entity.get("source_mentions", [])
            if mention.get("source_doc_id") is not None
            and str(mention.get("source_doc_id")).strip()
        )

        for identifier in identifiers:
            festival_id_to_entity.setdefault(identifier, entity_id)

    linked = []
    for extra in extras:
        row = dict(extra)
        festival_id = row.get("related_festival_id")
        if festival_id is not None:
            festival_id = str(festival_id).strip()
        row["festival_entity_id"] = festival_id_to_entity.get(festival_id)
        linked.append(row)

    return linked

def build_er_report(
    mentions: Sequence[dict[str, Any]],
    resolution: dict[str, Any],
) -> dict[str, Any]:
    """ER 병합 전후 Entity 수와 후보/판정 통계를 만든다."""

    entities = resolution.get("entities", [])
    candidates = resolution.get("candidates", [])

    # 병합 전: (entity_type, 원본 name) 기준 고유 Entity 수
    before_entity_count = len({
        (
            mention.get("entity_type"),
            mention.get("name"),
        )
        for mention in mentions
        if mention.get("name")
    })

    # 병합 후: canonical entity 수
    after_entity_count = len(entities)

    automatic_count = 0
    manual_count = 0
    exact_merge_count = 0
    fuzzy_review_count = 0
    embedding_review_count = 0
    approved_merge_count = 0
    rejected_merge_count = 0

    for candidate in candidates:
        decision = candidate.get("decision")

        if decision in {"merge", "separate", "exact_merge"}:
            automatic_count += 1
        if decision == "exact_merge" or candidate.get("candidate_type") == "exact":
            exact_merge_count += 1
        if candidate.get("candidate_type") == "embedding" or candidate.get("embedding_similarity") is not None:
            embedding_review_count += 1
        elif decision == "review":
            fuzzy_review_count += 1
        if decision == "review":
            manual_count += 1
        human_decision = candidate.get("human_decision")
        if human_decision in {"approved_merge", "merge"}:
            approved_merge_count += 1
        elif human_decision in {"rejected_merge", "separate"}:
            rejected_merge_count += 1

    reduction_rate = (
        (before_entity_count - after_entity_count) / before_entity_count
        if before_entity_count else 0.0
    )
    reviewed_merges = approved_merge_count + rejected_merge_count
    merge_precision = (
        approved_merge_count / reviewed_merges if reviewed_merges else None
    )
    entity_by_id = {entity.get("entity_id"): entity for entity in entities}
    mention_to_entity = resolution.get("mention_to_entity", {})
    consistent_mentions = 0
    valid_mentions = [mention for mention in mentions if not mention.get("error") and mention.get("name")]
    for mention in valid_mentions:
        entity = entity_by_id.get(mention_to_entity.get(mention.get("mention_id")))
        if entity and entity.get("canonical_name") and entity.get("entity_type") == mention.get("entity_type"):
            consistent_mentions += 1
    consistency = consistent_mentions / len(valid_mentions) if valid_mentions else 0.0

    er_report = {
        "entity_count_before": before_entity_count,
        "entity_count_after": after_entity_count,
        "merged_entity_count": before_entity_count - after_entity_count,
        "entity_reduction_rate": round(reduction_rate, 6),
        "candidate_count": len(candidates),
        "automatic_decision_count": automatic_count,
        "manual_review_count": manual_count,
        "exact_merge_count": exact_merge_count,
        "fuzzy_review_count": fuzzy_review_count,
        "embedding_review_count": embedding_review_count,
        "approved_merge_count": approved_merge_count,
        "rejected_merge_count": rejected_merge_count,
        "merge_precision": merge_precision,
        "er_consistency": round(consistency, 6),
    }

    return er_report

def run_entity_resolution_from_triples(
    validated_triples: Sequence[dict[str, Any]],
    embed_texts=None,
) -> dict[str, Any]:
    """ValidationRecord의 clean Triple 목록 또는 dict Triple 목록으로 ER을 수행한다."""

    validated_triples = [
        _as_triple_dict(record)
        for record in validated_triples
    ]
    mentions = collect_entity_mentions(validated_triples)

    resolution = resolve_entities(mentions)

    if embed_texts is not None:
        resolution = add_embedding_candidates(
            resolution,
            embed_texts,
        )

    resolution = build_canonical_mapping(
        resolution,
        mentions,
    )

    resolved_triples = replace_with_canonical_names(
        validated_triples,
        resolution,
    )

    resolved_triples = deduplicate_resolved_triples(
        resolved_triples,
    )

    er_report = build_er_report(
        mentions,
        resolution,
    )

    return {
        "resolved_entities": resolution["entities"],
        "resolved_triples": resolved_triples,
        "er_candidates": resolution["candidates"],
        "er_report": er_report,
    }

def run_entity_resolution(
    input_path: str | Path = INPUT_FILENAME,
    output_dir: str | Path = ".",
    embed_texts=None,
) -> dict[str, Any]:
    """validated_triples.json을 읽고 ER 결과 4개 파일을 저장한다."""

    input_path = Path(input_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as f:
        validated_triples = json.load(f)

    result = run_entity_resolution_from_triples(
        validated_triples,
        embed_texts=embed_texts,
    )

    outputs = {
        OUTPUT_FILENAMES["entities"]: result["resolved_entities"],
        OUTPUT_FILENAMES["triples"]: result["resolved_triples"],
        OUTPUT_FILENAMES["candidates"]: result["er_candidates"],
        OUTPUT_FILENAMES["report"]: result["er_report"],
    }

    for filename, data in outputs.items():
        with (output_dir / filename).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    return result

# 최소 예시: {"name": "유플페", "entity_type": "Festival", "source_doc_id": "1", "role": "subject"}
# 완료 조건: 타입이 다른 Entity는 병합하지 않고, 원본 이름·문서 ID·role을 재현할 수 있다.
# Freeze point: canonical_name 결정 규칙과 자동 병합 threshold는 팀 승인 없이 바꾸지 않는다.
