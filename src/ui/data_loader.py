"""Shared local data access for the Streamlit team modules."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]

REGION_NAMES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}

AUDIENCE_KEYWORDS = {
    "전 연령": ("전 연령", "전연령", "누구나", "남녀노소", "모든 연령"),
    "어린이": ("어린이", "아동", "유아", "초등", "키즈"),
    "청소년": ("청소년", "중학생", "고등학생"),
    "성인": ("성인", "대학생"),
    "가족": ("가족", "보호자", "부모"),
    "시니어": ("시니어", "노인", "어르신", "장년"),
}

# The graph currently stores free-text HAS_THEME objects. Keep those values for
# traceability, but expose this small controlled vocabulary to recommendation
# filters so one-off phrases do not become dropdown options.
THEME_CATEGORY_ORDER = [
    "문화예술",
    "음악공연",
    "전통역사",
    "음식미식",
    "자연생태",
    "가족체험",
    "스포츠레저",
    "야간관광",
    "지역특산",
    "계절축제",
    "환경지속가능",
    "청년지역공동체",
    "기타",
]

THEME_CATEGORY_KEYWORDS = {
    "문화예술": (
        "문화",
        "예술",
        "미술",
        "전시",
        "문학",
        "영화",
        "연극",
        "뮤지컬",
        "콘텐츠",
        "웹툰",
        "도서",
    ),
    "음악공연": (
        "음악",
        "콘서트",
        "공연",
        "가요",
        "국악",
        "오페라",
        "밴드",
        "재즈",
        "클래식",
        "합창",
        "연주",
        "라이브",
    ),
    "전통역사": (
        "역사",
        "전통",
        "문화유산",
        "국가유산",
        "유산",
        "조선",
        "백제",
        "신라",
        "삼국유사",
        "민속",
        "한옥",
        "궁궐",
        "사찰",
        "독립운동",
    ),
    "음식미식": (
        "음식",
        "먹거리",
        "맛",
        "미식",
        "와인",
        "맥주",
        "커피",
        "차",
        "김치",
        "유자",
        "빵",
        "떡",
        "한우",
        "치맥",
        "막걸리",
        "수산",
        "바비큐",
        "요리",
        "식도락",
    ),
    "자연생태": (
        "자연",
        "생태",
        "숲",
        "산",
        "바다",
        "해변",
        "강",
        "호수",
        "꽃",
        "벚꽃",
        "단풍",
        "반딧불",
        "정원",
        "노을",
        "생명",
    ),
    "가족체험": (
        "가족",
        "어린이",
        "키즈",
        "체험",
        "놀이",
        "교육",
        "청소년",
        "아이",
        "참여",
        "워크숍",
    ),
    "스포츠레저": (
        "스포츠",
        "체육",
        "마라톤",
        "걷기",
        "달리기",
        "러닝",
        "레저",
        "자전거",
        "등산",
        "트레킹",
        "수영",
        "요가",
        "체조",
        "대회",
    ),
    "야간관광": (
        "야간",
        "밤",
        "달밤",
        "별빛",
        "불빛",
        "야행",
        "야경",
        "라이트",
    ),
    "지역특산": (
        "지역",
        "특산",
        "농산물",
        "수확",
        "장터",
        "전통시장",
        "산업",
        "특산품",
        "로컬",
        "마을",
        "농촌",
        "어촌",
    ),
    "계절축제": (
        "봄",
        "여름",
        "가을",
        "겨울",
        "벚꽃",
        "단풍",
        "눈꽃",
        "크리스마스",
        "해맞이",
        "계절",
    ),
    "환경지속가능": (
        "지속가능",
        "탄소",
        "기후",
        "환경",
        "친환경",
        "저탄소",
        "재활용",
        "에너지",
    ),
    "청년지역공동체": (
        "청년",
        "시민",
        "공동체",
        "주민",
        "사회",
        "나눔",
        "봉사",
        "지역문화",
    ),
}


def normalize_region(address: str) -> str:
    """Return a short province or metropolitan-city name from an address."""
    text = str(address or "")
    return next(
        (short_name for full_name, short_name in REGION_NAMES.items() if full_name in text),
        "",
    )


def classify_fee(value: str) -> str:
    """Classify fee text as 무료, 유료, or empty when no fee is known."""
    text = str(value or "").strip()
    if not text:
        return ""
    if "유료" in text or re.search(r"\d[\d,]*\s*원", text):
        return "유료"
    if "무료" in text:
        return "무료"
    return ""


def normalize_audiences(values: list[str]) -> list[str]:
    """Map free-text audience descriptions to stable recommendation categories."""
    text = " ".join(str(value) for value in values if value)
    return [
        category
        for category, keywords in AUDIENCE_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]


def normalize_theme_categories(values: list[str]) -> list[str]:
    """Map graph free text to deterministic, user-facing theme categories."""
    text = " ".join(str(value) for value in values if value).strip()
    if not text:
        return []
    categories = [
        category
        for category in THEME_CATEGORY_ORDER
        if category != "기타"
        and any(keyword in text for keyword in THEME_CATEGORY_KEYWORDS[category])
    ]
    return categories or ["기타"]


def summarize_festival(value: str, max_length: int = 120) -> str:
    """Return a compact first-sentence summary for recommendation cards."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text or max_length <= 0:
        return ""
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    summary = next((sentence.strip() for sentence in sentences if sentence.strip()), text)
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 1].rstrip() + "…"


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
    sponsor1: str = ""
    sponsor2: str = ""
    image_url: str = ""
    firstimage: str = ""
    firstimage2: str = ""
    image: str = ""
    thumbnail: str = ""
    thumbnail_url: str = ""

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
            sponsor1=metadata.get("sponsor1", ""),
            sponsor2=metadata.get("sponsor2", ""),
            image_url=metadata.get("image_url", ""),
            firstimage=metadata.get("firstimage", ""),
            firstimage2=metadata.get("firstimage2", ""),
            image=metadata.get("image", ""),
            thumbnail=metadata.get("thumbnail", ""),
            thumbnail_url=metadata.get("thumbnail_url", ""),
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


def _source_doc_ids(triple: dict[str, Any]) -> list[str]:
    values = triple.get("source_doc_ids")
    if isinstance(values, list):
        return [str(value) for value in values if value not in (None, "")]
    value = triple.get("source_doc_id")
    return [str(value)] if value not in (None, "") else []


def enrich_festivals(
    festivals: list[dict[str, Any]],
    triples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach recommendation metadata from the resolved knowledge graph."""
    themes_by_doc: dict[str, list[str]] = defaultdict(list)
    targets_by_doc: dict[str, list[str]] = defaultdict(list)
    relation_count_by_doc: dict[str, int] = defaultdict(int)

    for triple in triples:
        doc_ids = _source_doc_ids(triple)
        for doc_id in doc_ids:
            relation_count_by_doc[doc_id] += 1
            value = str(triple.get("object") or "").strip()
            if triple.get("relation") == "HAS_THEME" and value:
                themes_by_doc[doc_id].append(value)
            if triple.get("relation") == "TARGETS" and value:
                targets_by_doc[doc_id].append(value)

    enriched: list[dict[str, Any]] = []
    for festival in festivals:
        row = dict(festival)
        doc_id = str(row.get("doc_id") or "")
        row["region"] = normalize_region(str(row.get("address") or ""))
        row["summary"] = summarize_festival(str(row.get("text") or ""))
        row["themes"] = list(dict.fromkeys(themes_by_doc[doc_id]))
        row["theme_categories"] = normalize_theme_categories(row["themes"])
        row["audiences"] = normalize_audiences(
            [*targets_by_doc[doc_id], str(row.get("age_limit") or "")]
        )
        row["fee_category"] = classify_fee(str(row.get("usage_fee") or ""))
        row["relation_count"] = relation_count_by_doc[doc_id]
        enriched.append(row)
    return enriched


def load_app_data() -> dict[str, Any]:
    """Return all UI inputs in one stable shape for every page owner."""
    documents = load_jsonl("data/processed/01_preprocessing/festivals_documents.jsonl")
    raw_festivals = load_json("data/raw/festival_raw.json", [])
    raw_by_id = {
        str(item.get("contentid")): item
        for item in raw_festivals
        if isinstance(item, dict) and item.get("contentid")
    } if isinstance(raw_festivals, list) else {}
    triples = load_json("data/processed/03_er/final/resolved_triples.json", [])
    if isinstance(triples, dict):
        triples = triples.get("triples", [])
    festivals: list[dict[str, Any]] = []
    for row in documents:
        source = raw_by_id.get(str(row.get("doc_id")), {})
        metadata = dict(row.get("metadata") or {})
        for key in ("firstimage", "firstimage2"):
            if not metadata.get(key) and source.get(key):
                metadata[key] = source[key]
        normalized_row = {**row, "metadata": metadata}
        festival = Festival.from_document(normalized_row)
        if festival.name != "이름 없는 축제":
            festivals.append(festival.model_dump())
    normalized_triples = triples if isinstance(triples, list) else []
    return {
        "festivals": enrich_festivals(festivals, normalized_triples),
        "triples": normalized_triples,
        "documents": documents,
    }


def festival_name(row: dict[str, Any]) -> str:
    return str(row.get("festival") or row.get("name") or row.get("title") or "이름 없는 축제")


def festival_text(row: dict[str, Any]) -> str:
    return str(row.get("text") or row.get("content") or row.get("description") or "")
