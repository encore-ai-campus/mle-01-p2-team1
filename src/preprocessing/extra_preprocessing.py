"""extra 원본 데이터를 ER과 RAG에 전달할 수 있는 공통 문서 형태로 정리한다.

이 모듈은 experience_raw.json, festival_nearby_5km.json, stays_all.json을
festivals_documents.jsonl에 합치지 않는다. 파일별 원본 구조를 확인하고,
ID·이름·설명·주소·좌표·축제 연결 후보를 공통 필드로 정규화하는 골격만 제공한다.

공통 출력 계약:
{
    "extra_id": str,
    "source_type": str,
    "title": str,
    "text": str,
    "address": str,
    "latitude": float | None,
    "longitude": float | None,
    "related_festival_id": str | None,
    "source_file": str,
}
"""

import json
from pathlib import Path
from typing import Any


def load_extra_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise TypeError("최상위 JSON 자료형은 list여야 합니다.")

    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise TypeError(f"{index}번째 row가 dict가 아닙니다.")

    return data


def _first_value(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field_name in fields:
        value = row.get(field_name)

        if value is not None and str(value).strip():
            return value

    return ""


def _to_float(value: Any) -> float | None:
    if value is None or not str(value).strip():
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_extra_row(
    row: dict[str, Any],
    source_type: str,
    source_file: str,
) -> dict[str, Any]:
    extra_id = _first_value(
        row,
        ("extra_id", "contentid", "id", "facility_id"),
    )

    title = _first_value(
        row,
        ("title", "name", "facltNm", "facility_name"),
    )

    text = _first_value(
        row,
        ("text", "overview", "description", "intro", "content"),
    )

    address = _first_value(
        row,
        ("address", "addr1", "addr", "location"),
    )

    latitude = _to_float(
        _first_value(row, ("latitude", "lat", "mapy"))
    )

    longitude = _to_float(
        _first_value(row, ("longitude", "lon", "lng", "mapx"))
    )

    related_festival_id = _first_value(
        row,
        ("related_festival_id", "festival_id", "festival_contentid"),
    )

    return {
        "extra_id": str(extra_id).strip(),
        "source_type": source_type,
        "title": str(title).strip(),
        "text": str(text).strip(),
        "address": str(address).strip(),
        "latitude": latitude,
        "longitude": longitude,
        "related_festival_id": (
            str(related_festival_id).strip()
            if related_festival_id
            else None
        ),
        "source_file": source_file,
    }


def normalize_extra_rows(
    rows: list[dict[str, Any]],
    source_type: str,
    source_file: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_rows = []
    rejected_rows = []
    seen_ids = set()

    for index, row in enumerate(rows):
        normalized = normalize_extra_row(
            row=row,
            source_type=source_type,
            source_file=source_file,
        )

        if not normalized["extra_id"]:
            rejected_rows.append({
                "row_index": index,
                "reason": "missing_extra_id",
                "row": row,
            })
            continue

        if normalized["extra_id"] in seen_ids:
            rejected_rows.append({
                "row_index": index,
                "reason": "duplicate_extra_id",
                "row": row,
            })
            continue

        if not normalized["title"] and not normalized["text"]:
            rejected_rows.append({
                "row_index": index,
                "reason": "missing_title_and_text",
                "row": row,
            })
            continue

        seen_ids.add(normalized["extra_id"])
        normalized_rows.append(normalized)

    return normalized_rows, rejected_rows


def normalize_nearby_rows(
    rows: list[dict[str, Any]],
    source_file: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """festival_nearby_5km의 중첩 nearby 항목을 공통 문서로 펼친다."""
    normalized_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    seen_ids: set[tuple[str, str]] = set()

    for festival_index, festival_row in enumerate(rows):
        festival_id = str(festival_row.get("festival_contentid", "")).strip()
        nearby_items = festival_row.get("nearby", [])

        if not isinstance(nearby_items, list):
            rejected_rows.append({
                "row_index": festival_index,
                "reason": "nearby_is_not_list",
                "row": festival_row,
            })
            continue

        for nearby_index, nearby in enumerate(nearby_items):
            if not isinstance(nearby, dict):
                rejected_rows.append({
                    "row_index": f"{festival_index}:{nearby_index}",
                    "reason": "nearby_item_is_not_dict",
                    "row": nearby,
                })
                continue

            extra_id = str(nearby.get("contentid", "")).strip()
            if not extra_id:
                rejected_rows.append({
                    "row_index": f"{festival_index}:{nearby_index}",
                    "reason": "missing_extra_id",
                    "row": nearby,
                })
                continue

            key = (festival_id, extra_id)
            if key in seen_ids:
                rejected_rows.append({
                    "row_index": f"{festival_index}:{nearby_index}",
                    "reason": "duplicate_extra_id_for_festival",
                    "row": nearby,
                })
                continue

            normalized = normalize_extra_row(
                row=nearby,
                source_type="nearby",
                source_file=source_file,
            )
            normalized["related_festival_id"] = festival_id or None
            normalized["distance_meters"] = _to_float(nearby.get("dist"))
            normalized["metadata"] = {
                "address": normalized["address"],
                "latitude": normalized["latitude"],
                "longitude": normalized["longitude"],
                "distance_meters": normalized["distance_meters"],
                "festival_title": festival_row.get("festival_title", ""),
                "festival_latitude": _to_float(festival_row.get("festival_mapy")),
                "festival_longitude": _to_float(festival_row.get("festival_mapx")),
            }

            if not normalized["title"] and not normalized["text"]:
                rejected_rows.append({
                    "row_index": f"{festival_index}:{nearby_index}",
                    "reason": "missing_title_and_text",
                    "row": nearby,
                })
                continue

            seen_ids.add(key)
            normalized_rows.append(normalized)

    return normalized_rows, rejected_rows


def save_jsonl(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )


def preprocess_extra_file(
    input_path: Path,
    output_path: Path,
    source_type: str,
) -> dict[str, Any]:
    rows = load_extra_json(input_path)

    if source_type == "nearby":
        normalized_rows, rejected_rows = normalize_nearby_rows(
            rows=rows,
            source_file=input_path.name,
        )
    else:
        normalized_rows, rejected_rows = normalize_extra_rows(
            rows=rows,
            source_type=source_type,
            source_file=input_path.name,
        )

    save_jsonl(output_path, normalized_rows)

    reject_path = output_path.parent / "rejected" / (
        f"{output_path.stem}_rejected.jsonl"
    )
    save_jsonl(reject_path, rejected_rows)

    return {
        "source_file": input_path.name,
        "input_count": len(rows),
        "normalized_count": len(normalized_rows),
        "rejected_count": len(rejected_rows),
        "output_path": str(output_path),
        "reject_path": str(reject_path),
    }


def run_extra_preprocessing(
    data_dir: Path,
    output_dir: Path,
) -> list[dict[str, Any]]:
    jobs = [
        (
            data_dir / "extra" / "experience_raw.json",
            output_dir / "extra_experiences.jsonl",
            "experience",
        ),
        (
            data_dir / "extra" / "festival_nearby_5km.json",
            output_dir / "extra_nearby.jsonl",
            "nearby",
        ),
        (
            data_dir / "extra" / "stays_all.json",
            output_dir / "extra_accommodations.jsonl",
            "accommodation",
        ),
    ]

    summaries = []

    for input_path, output_path, source_type in jobs:
        if not input_path.exists():
            summaries.append({
                "source_file": input_path.name,
                "status": "missing",
            })
            continue

        summaries.append(
            preprocess_extra_file(
                input_path=input_path,
                output_path=output_path,
                source_type=source_type,
            )
        )

    return summaries

if __name__ == "__main__":
    summaries = run_extra_preprocessing(
        data_dir=Path("data"),
        output_dir=Path("data/processed/01_preprocessing"),
    )

    print(json.dumps(summaries, ensure_ascii=False, indent=2))
