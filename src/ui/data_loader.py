"""Shared local data access for the Streamlit team modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: str | Path, default: Any = None) -> Any:
    """Load JSON without making the UI fail when an optional artifact is absent."""
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default if default is not None else {}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load non-empty JSONL rows, skipping malformed optional rows."""
    rows: list[dict[str, Any]] = []
    try:
        lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
        except json.JSONDecodeError:
            continue
    return rows


def load_app_data() -> dict[str, Any]:
    """Return all UI inputs in one stable shape for every page owner."""
    documents = load_jsonl("data/processed/01_preprocessing/festivals_documents.jsonl")
    triples = load_json("data/processed/03_er/final/resolved_triples.json", [])
    if isinstance(triples, dict):
        triples = triples.get("triples", [])
    # TODO(데이터 담당): 대표 축제 필드명을 확정하고 타입 모델을 추가합니다.
    festivals = []
    for row in documents:
        name = festival_name(row)
        if name != "이름 없는 축제":
            normalized = dict(row)
            normalized["name"] = name
            normalized["text"] = festival_text(row)
            festivals.append(normalized)
    return {"festivals": festivals, "triples": triples if isinstance(triples, list) else [], "documents": documents}


def festival_name(row: dict[str, Any]) -> str:
    return str(row.get("festival") or row.get("name") or row.get("title") or "이름 없는 축제")


def festival_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("content") or row.get("description") or "")
