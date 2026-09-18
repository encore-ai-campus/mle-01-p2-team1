"""Shared local data access for the Streamlit team modules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Festival(BaseModel):
    """Canonical UI-facing festival fields extracted from a source document."""

    model_config = ConfigDict(extra="ignore")

    doc_id: str = ""
    name: str
    text: str = ""
    start_date: str = ""
    end_date: str = ""
    address: str = ""
    longitude: float | None = None
    latitude: float | None = None
    homepage: str = ""
    event_place: str = ""
    playtime: str = ""
    age_limit: str = ""
    usage_fee: str = ""
    region: str = ""
    location: str = ""
    theme: str = ""
    date: str = ""
    period: str = ""
    programs: Any = None

    @classmethod
    def from_document(cls, row: dict[str, Any]) -> "Festival":
        metadata = row.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        return cls(
            doc_id=row.get("doc_id", metadata.get("doc_id", "")),
            name=festival_name(row),
            text=festival_text(row),
            start_date=metadata.get("event_start", ""),
            end_date=metadata.get("event_end", ""),
            address=metadata.get("address", ""),
            longitude=metadata.get("longitude"),
            latitude=metadata.get("latitude"),
            homepage=metadata.get("homepage", ""),
            event_place=metadata.get("eventplace", ""),
            playtime=metadata.get("playtime", ""),
            age_limit=metadata.get("agelimit", ""),
            usage_fee=metadata.get("usetimefestival", ""),
            region=row.get("region", metadata.get("region", "")),
            location=row.get("location", metadata.get("location", "")),
            theme=row.get("theme", metadata.get("theme", "")),
            date=row.get("date", metadata.get("date", "")),
            period=row.get("period", metadata.get("period", "")),
            programs=row.get("programs", row.get("program")),
        )


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
    festivals: list[dict[str, Any]] = []
    for row in documents:
        festival = Festival.from_document(row)
        if festival.name != "이름 없는 축제":
            festivals.append(festival.model_dump())
    return {"festivals": festivals, "triples": triples if isinstance(triples, list) else [], "documents": documents}


def festival_name(row: dict[str, Any]) -> str:
    return str(row.get("festival") or row.get("name") or row.get("title") or "이름 없는 축제")


def festival_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("content") or row.get("description") or "")
