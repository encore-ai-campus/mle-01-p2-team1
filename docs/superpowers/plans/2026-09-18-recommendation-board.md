# Recommendation Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace only the recommendation page with real data-backed filters, five recommendation presets, and a maximum of four festival cards.

**Architecture:** Enrich each festival once in `load_app_data` by joining knowledge-graph triples through `doc_id`/`source_doc_ids`. Keep all option building, date matching, combined filtering, and ranking in a new pure `src/ui/recommendations.py` module; `main_page.py` remains responsible only for Streamlit controls and presentation.

**Tech Stack:** Python 3.12, Pydantic, Streamlit 1.57+, pytest, Streamlit `AppTest`

**Spec:** `docs/superpowers/specs/2026-09-18-recommendation-board-design.md`

## Global Constraints

- Modify only the recommendation feature and shared festival enrichment needed by that feature.
- Preserve home, map, detail, chatbot, and knowledge-graph page behavior.
- Do not add a hero image to the recommendation page.
- Never include `미분류` in a filter option.
- Treat partially paid festivals as `유료`.
- Rank `인기` by descending knowledge-graph relation count.
- Display no more than four recommendation cards.
- Use native Streamlit widgets; use `width="stretch"` rather than deprecated `use_container_width` in new code.

---

### Task 1: Enrich festival records with recommendation metadata

**Files:**
- Modify: `src/ui/data_loader.py:13-89`
- Modify: `tests/test_data_loader.py`

**Interfaces:**
- Consumes: festival records produced by `Festival.from_document` and triples loaded from `resolved_triples.json`.
- Produces: `normalize_region(address: str) -> str`, `classify_fee(value: str) -> str`, `normalize_audiences(values: list[str]) -> list[str]`, and `enrich_festivals(festivals: list[dict[str, Any]], triples: list[dict[str, Any]]) -> list[dict[str, Any]]`.
- Each enriched festival contains `region: str`, `themes: list[str]`, `audiences: list[str]`, `fee_category: str`, and `relation_count: int`.

- [ ] **Step 1: Write failing normalization tests**

Add these imports and tests to `tests/test_data_loader.py`:

```python
from src.ui.data_loader import (
    Festival,
    classify_fee,
    enrich_festivals,
    load_app_data,
    normalize_audiences,
    normalize_region,
)


def test_normalize_region_uses_province_from_address():
    assert normalize_region("경기도 고양시 일산동구 중앙로 1") == "경기"
    assert normalize_region("서울특별시 종로구 세종대로 1") == "서울"
    assert normalize_region("") == ""


def test_classify_fee_keeps_partial_payment_out_of_free_filter():
    assert classify_fee("무료") == "무료"
    assert classify_fee("무료 (일부 프로그램 유료)") == "유료"
    assert classify_fee("입장권 10,000원") == "유료"
    assert classify_fee("") == ""


def test_normalize_audiences_maps_graph_text_to_stable_categories():
    assert normalize_audiences(["어린이를 동반한 가족", "전 연령"]) == [
        "전 연령",
        "어린이",
        "가족",
    ]
```

- [ ] **Step 2: Run the normalization tests and verify RED**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/test_data_loader.py -k 'normalize_region or classify_fee or normalize_audiences' -v
```

Expected: collection fails because the three functions do not exist.

- [ ] **Step 3: Implement the normalization helpers**

Add constants and helpers to `src/ui/data_loader.py`:

```python
import re
from collections import defaultdict

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


def normalize_region(address: str) -> str:
    text = str(address or "")
    return next((short for full, short in REGION_NAMES.items() if full in text), "")


def classify_fee(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "유료" in text or re.search(r"\d[\d,]*\s*원", text):
        return "유료"
    if "무료" in text:
        return "무료"
    return ""


def normalize_audiences(values: list[str]) -> list[str]:
    text = " ".join(str(value) for value in values if value)
    return [
        category
        for category, keywords in AUDIENCE_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
```

- [ ] **Step 4: Run the normalization tests and verify GREEN**

Run the command from Step 2.

Expected: all selected tests pass.

- [ ] **Step 5: Write a failing graph-enrichment test**

Add to `tests/test_data_loader.py`:

```python
def test_enrich_festivals_joins_theme_audience_and_relation_count_by_doc_id():
    festivals = [
        {
            "doc_id": "123",
            "name": "봄 축제",
            "address": "서울특별시 종로구",
            "age_limit": "전 연령",
            "usage_fee": "무료",
        }
    ]
    triples = [
        {
            "relation": "HAS_THEME",
            "object": "벚꽃",
            "source_doc_ids": ["123"],
        },
        {
            "relation": "TARGETS",
            "object": "어린이 동반 가족",
            "source_doc_ids": ["123"],
        },
        {
            "relation": "HAS_PROGRAM",
            "object": "봄 음악회",
            "source_doc_ids": ["123"],
        },
    ]

    enriched = enrich_festivals(festivals, triples)[0]

    assert enriched["region"] == "서울"
    assert enriched["themes"] == ["벚꽃"]
    assert enriched["audiences"] == ["전 연령", "어린이", "가족"]
    assert enriched["fee_category"] == "무료"
    assert enriched["relation_count"] == 3
```

- [ ] **Step 6: Run the enrichment test and verify RED**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/test_data_loader.py::test_enrich_festivals_joins_theme_audience_and_relation_count_by_doc_id -v
```

Expected: failure because `enrich_festivals` is not implemented.

- [ ] **Step 7: Implement graph enrichment and call it from `load_app_data`**

Add the following behavior to `src/ui/data_loader.py`:

```python
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
    themes_by_doc: dict[str, list[str]] = defaultdict(list)
    targets_by_doc: dict[str, list[str]] = defaultdict(list)
    relation_count_by_doc: dict[str, int] = defaultdict(int)

    for triple in triples:
        for doc_id in _source_doc_ids(triple):
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
        row["themes"] = list(dict.fromkeys(themes_by_doc[doc_id]))
        row["audiences"] = normalize_audiences(
            [*targets_by_doc[doc_id], str(row.get("age_limit") or "")]
        )
        row["fee_category"] = classify_fee(str(row.get("usage_fee") or ""))
        row["relation_count"] = relation_count_by_doc[doc_id]
        enriched.append(row)
    return enriched
```

In `load_app_data`, replace the final raw festival list with `enrich_festivals(festivals, triples)` while preserving all three top-level return keys.

- [ ] **Step 8: Run all loader tests**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/test_data_loader.py -v
```

Expected: all loader tests pass and the existing serialization assertions remain green.

- [ ] **Step 9: Commit Task 1**

```powershell
git add src/ui/data_loader.py tests/test_data_loader.py
git commit -m "feat: enrich festivals for recommendation filters"
```

---

### Task 2: Implement pure filtering and recommendation presets

**Files:**
- Create: `src/ui/recommendations.py`
- Create: `tests/ui/test_recommendations.py`

**Interfaces:**
- Consumes: enriched festival dictionaries from Task 1.
- Produces: `build_filter_options(festivals: list[dict[str, Any]]) -> dict[str, list[str]]`.
- Produces: `recommend_festivals(festivals: list[dict[str, Any]], *, region: str = "전체", theme: str = "전체", month: str = "전체", audience: str = "전체", fee: str = "전체", preset: str = "전체", today: date | None = None, limit: int = 4) -> tuple[list[dict[str, Any]], int]`.

- [ ] **Step 1: Write failing option and combined-filter tests**

Create `tests/ui/test_recommendations.py`:

```python
from datetime import date

from src.ui.recommendations import build_filter_options, recommend_festivals


def festival(
    name: str,
    *,
    region: str = "서울",
    themes: list[str] | None = None,
    audiences: list[str] | None = None,
    fee: str = "무료",
    start: str = "20260920",
    end: str = "20260921",
    relations: int = 1,
) -> dict:
    return {
        "name": name,
        "region": region,
        "themes": themes or [],
        "audiences": audiences or [],
        "fee_category": fee,
        "start_date": start,
        "end_date": end,
        "relation_count": relations,
    }


def test_build_filter_options_uses_real_values_without_unclassified():
    rows = [
        festival("봄 축제", themes=["벚꽃"], audiences=["가족"]),
        festival("빈 축제", region="", themes=[], audiences=[], fee=""),
    ]

    options = build_filter_options(rows)

    assert options["regions"] == ["전체", "서울"]
    assert options["themes"] == ["전체", "벚꽃"]
    assert options["audiences"] == ["전체", "가족"]
    assert options["fees"] == ["전체", "무료", "유료"]
    assert "미분류" not in str(options)


def test_recommend_festivals_combines_all_selected_filters():
    rows = [
        festival("선택됨", themes=["벚꽃"], audiences=["가족"]),
        festival("다른 지역", region="부산", themes=["벚꽃"], audiences=["가족"]),
        festival("유료 축제", themes=["벚꽃"], audiences=["가족"], fee="유료"),
    ]

    selected, total = recommend_festivals(
        rows,
        region="서울",
        theme="벚꽃",
        month="9월",
        audience="가족",
        fee="무료",
        today=date(2026, 9, 18),
    )

    assert [row["name"] for row in selected] == ["선택됨"]
    assert total == 1
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/ui/test_recommendations.py -k 'filter_options or combines' -v
```

Expected: collection fails because `src.ui.recommendations` does not exist.

- [ ] **Step 3: Implement option building, date parsing, and AND filters**

Create `src/ui/recommendations.py` with these public constants and functions:

```python
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

ALL = "전체"
PRESETS = [ALL, "인기", "이번 달", "곧 시작", "가족 추천"]
AUDIENCE_ORDER = ["전 연령", "어린이", "청소년", "성인", "가족", "시니어"]


def _parse_date(value: Any) -> date | None:
    text = str(value or "").replace("-", "").replace(".", "")[:8]
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def _event_intersects_month(row: dict[str, Any], year: int, month: int) -> bool:
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date")) or start
    if start is None or end is None:
        return False
    month_start = date(year, month, 1)
    next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
    month_end = next_month - timedelta(days=1)
    return start <= month_end and end >= month_start


def build_filter_options(festivals: list[dict[str, Any]]) -> dict[str, list[str]]:
    regions = sorted({str(row.get("region") or "") for row in festivals} - {""})
    themes = sorted({str(value) for row in festivals for value in row.get("themes", []) if value})
    present_audiences = {
        str(value) for row in festivals for value in row.get("audiences", []) if value
    }
    audiences = [value for value in AUDIENCE_ORDER if value in present_audiences]
    return {
        "regions": [ALL, *regions],
        "themes": [ALL, *themes],
        "months": [ALL, *[f"{month}월" for month in range(1, 13)]],
        "audiences": [ALL, *audiences],
        "fees": [ALL, "무료", "유료"],
    }


def _event_months(row: dict[str, Any]) -> set[int]:
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date")) or start
    if start is None or end is None or end < start:
        return set()
    cursor = date(start.year, start.month, 1)
    final = date(end.year, end.month, 1)
    months: set[int] = set()
    while cursor <= final:
        months.add(cursor.month)
        cursor = date(
            cursor.year + (cursor.month == 12),
            1 if cursor.month == 12 else cursor.month + 1,
            1,
        )
    return months


def recommend_festivals(
    festivals: list[dict[str, Any]],
    *,
    region: str = ALL,
    theme: str = ALL,
    month: str = ALL,
    audience: str = ALL,
    fee: str = ALL,
    preset: str = ALL,
    today: date | None = None,
    limit: int = 4,
) -> tuple[list[dict[str, Any]], int]:
    del preset, today
    rows = list(festivals)
    if region != ALL:
        rows = [row for row in rows if row.get("region") == region]
    if theme != ALL:
        rows = [row for row in rows if theme in row.get("themes", [])]
    if month != ALL:
        month_number = int(month.removesuffix("월"))
        rows = [row for row in rows if month_number in _event_months(row)]
    if audience != ALL:
        rows = [row for row in rows if audience in row.get("audiences", [])]
    if fee != ALL:
        rows = [row for row in rows if row.get("fee_category") == fee]
    rows.sort(
        key=lambda row: (
            _parse_date(row.get("start_date")) or date.max,
            str(row.get("name") or ""),
        )
    )
    total = len(rows)
    return rows[:limit], total
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the command from Step 2.

Expected: both focused tests pass.

- [ ] **Step 5: Write failing preset, ranking, and limit tests**

Append to `tests/ui/test_recommendations.py`:

```python
def test_popular_preset_ranks_by_relation_count_and_limits_to_four():
    rows = [festival(f"축제 {index}", relations=index) for index in range(1, 7)]

    selected, total = recommend_festivals(rows, preset="인기", limit=4)

    assert total == 6
    assert [row["relation_count"] for row in selected] == [6, 5, 4, 3]


def test_date_and_family_presets_use_reference_date():
    rows = [
        festival("진행 중", start="20260901", end="20260930", audiences=["성인"]),
        festival("곧 시작", start="20261001", end="20261003", audiences=["성인"]),
        festival("가족 행사", start="20261101", end="20261103", audiences=["가족"]),
        festival("지난 행사", start="20260801", end="20260803", audiences=["성인"]),
    ]
    today = date(2026, 9, 18)

    this_month, _ = recommend_festivals(rows, preset="이번 달", today=today)
    upcoming, _ = recommend_festivals(rows, preset="곧 시작", today=today)
    family, _ = recommend_festivals(rows, preset="가족 추천", today=today)

    assert [row["name"] for row in this_month] == ["진행 중"]
    assert [row["name"] for row in upcoming] == ["곧 시작"]
    assert [row["name"] for row in family] == ["가족 행사"]
```

- [ ] **Step 6: Run the new preset tests and verify RED**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/ui/test_recommendations.py -k 'popular or presets' -v
```

Expected: assertions fail until preset-specific filtering and ranking are implemented.

- [ ] **Step 7: Complete preset filtering and deterministic ranking**

Replace `recommend_festivals` with the completed implementation while retaining `_event_months` and the exact filter behavior from Step 3:

```python
def recommend_festivals(
    festivals: list[dict[str, Any]],
    *,
    region: str = ALL,
    theme: str = ALL,
    month: str = ALL,
    audience: str = ALL,
    fee: str = ALL,
    preset: str = ALL,
    today: date | None = None,
    limit: int = 4,
) -> tuple[list[dict[str, Any]], int]:
    rows = list(festivals)
    if region != ALL:
        rows = [row for row in rows if row.get("region") == region]
    if theme != ALL:
        rows = [row for row in rows if theme in row.get("themes", [])]
    if month != ALL:
        month_number = int(month.removesuffix("월"))
        rows = [row for row in rows if month_number in _event_months(row)]
    if audience != ALL:
        rows = [row for row in rows if audience in row.get("audiences", [])]
    if fee != ALL:
        rows = [row for row in rows if row.get("fee_category") == fee]

    reference_date = today or date.today()
    if preset == "이번 달":
        rows = [
            row
            for row in rows
            if _event_intersects_month(row, reference_date.year, reference_date.month)
        ]
    elif preset == "곧 시작":
        deadline = reference_date + timedelta(days=30)
        rows = [
            row
            for row in rows
            if (start := _parse_date(row.get("start_date"))) is not None
            and reference_date <= start <= deadline
        ]
    elif preset == "가족 추천":
        family_categories = {"가족", "어린이", "전 연령"}
        rows = [
            row for row in rows if family_categories.intersection(row.get("audiences", []))
        ]

    if preset == "인기":
        rows.sort(
            key=lambda row: (
                -int(row.get("relation_count") or 0),
                _parse_date(row.get("start_date")) or date.max,
                str(row.get("name") or ""),
            )
        )
    else:
        rows.sort(
            key=lambda row: (
                _parse_date(row.get("start_date")) or date.max,
                str(row.get("name") or ""),
            )
        )

    total = len(rows)
    return rows[:limit], total
```

- [ ] **Step 8: Run the complete recommendation-logic tests**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/ui/test_recommendations.py -v
```

Expected: all recommendation tests pass.

- [ ] **Step 9: Commit Task 2**

```powershell
git add src/ui/recommendations.py tests/ui/test_recommendations.py
git commit -m "feat: add festival recommendation filters"
```

---

### Task 3: Replace the recommendation page UI

**Files:**
- Modify: `src/ui/main_page.py:1-236`
- Create: `tests/ui/test_recommendation_page.py`

**Interfaces:**
- Consumes: `build_filter_options`, `PRESETS`, and `recommend_festivals` from Task 2.
- Produces: `render_recommendations(st: Any, data: dict[str, Any]) -> None` with four data-backed selectboxes, two segmented controls, and at most four detail buttons.

- [ ] **Step 1: Inspect the installed Streamlit widget API**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m streamlit docs st.selectbox
& '.\.venv\Scripts\python.exe' -m streamlit docs st.segmented_control
```

Expected: local signatures confirm `key`, `default`, and current width behavior before the UI code is changed.

- [ ] **Step 2: Write a failing Streamlit page test**

Create `tests/ui/test_recommendation_page.py`:

```python
from streamlit.testing.v1 import AppTest


def recommendation_app():
    import streamlit as st

    from src.ui.main_page import render_recommendations

    data = {
        "festivals": [
            {
                "doc_id": str(index),
                "name": f"축제 {index}",
                "text": "가족이 함께 즐기는 축제",
                "region": "서울",
                "themes": ["문화예술"],
                "audiences": ["가족"],
                "fee_category": "무료",
                "usage_fee": "무료",
                "start_date": "20260920",
                "end_date": "20260921",
                "relation_count": index,
            }
            for index in range(1, 7)
        ],
        "triples": [],
    }
    render_recommendations(st, data)


def test_recommendation_page_renders_real_filters_and_at_most_four_cards():
    at = AppTest.from_function(recommendation_app, default_timeout=30).run()

    assert [widget.label for widget in at.selectbox] == [
        "지역",
        "테마",
        "기간",
        "대상층",
    ]
    assert "미분류" not in at.selectbox[1].options
    assert list(at.segmented_control[0].options) == ["전체", "무료", "유료"]
    assert list(at.segmented_control[1].options) == [
        "전체",
        "인기",
        "이번 달",
        "곧 시작",
        "가족 추천",
    ]
    assert len([button for button in at.button if button.label == "상세 보기"]) == 4
```

- [ ] **Step 3: Run the page test and verify RED**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/ui/test_recommendation_page.py -v
```

Expected: failures show the old page has no fee/preset segmented controls and renders more than four detail buttons.

- [ ] **Step 4: Implement the filter board and four-card grid**

Update imports in `src/ui/main_page.py`:

```python
from datetime import date

from .recommendations import PRESETS, build_filter_options, recommend_festivals
```

Replace only `render_recommendations` and add focused private helpers:

```python
def _format_period(row: dict[str, Any]) -> str:
    def display(value: Any) -> str:
        text = str(value or "").replace("-", "")
        if len(text) >= 8 and text[:8].isdigit():
            return f"{text[:4]}.{text[4:6]}.{text[6:8]}"
        return text or "일정 정보 없음"

    return f"{display(row.get('start_date'))} ~ {display(row.get('end_date'))}"


def _render_recommendation_card(st: Any, row: dict[str, Any], key: str) -> None:
    with st.container(border=True):
        st.subheader(str(row.get("name") or "축제명 정보 없음"))
        st.caption(
            f":material/location_on: {row.get('region') or '지역 정보 없음'}  ·  "
            f":material/calendar_month: {_format_period(row)}"
        )
        st.markdown(f"**요금**  {row.get('usage_fee') or '요금 정보 없음'}")
        labels = [*row.get("themes", [])[:2], *row.get("audiences", [])[:2]]
        if labels:
            st.caption(" · ".join(f"#{label}" for label in labels))
        if st.button("상세 보기", key=key, width="stretch"):
            festival_detail_callback(st, row)
```

`render_recommendations` must:

1. Render `st.title("축제 추천")` and a short caption.
2. Call `build_filter_options(data.get("festivals", []))`.
3. Render region, theme, period, and audience selectboxes inside `st.container(border=True)` using stable keys `recommend_region`, `recommend_theme`, `recommend_month`, and `recommend_audience`.
4. Render fee with `st.segmented_control("요금", options["fees"], default="전체", key="recommend_fee")`.
5. Render preset with `st.segmented_control("추천 유형", PRESETS, default="전체", key="recommend_preset")`.
6. Call `recommend_festivals(..., today=date.today(), limit=4)` with every selected value.
7. Show `총 {total}개 중 {len(rows)}개 추천`.
8. Render the returned rows in `st.columns(2)` and call `_render_recommendation_card` once per row.
9. Call `empty_state(st, "조건에 맞는 축제가 없습니다.")` when no rows match.

- [ ] **Step 5: Run the page test and verify GREEN**

Run the command from Step 3.

Expected: the test passes with four selectboxes, both segmented controls, no `미분류`, and exactly four cards.

- [ ] **Step 6: Run all focused UI and loader tests**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest tests/test_data_loader.py tests/ui/test_recommendations.py tests/ui/test_recommendation_page.py -v
```

Expected: all focused tests pass.

- [ ] **Step 7: Commit Task 3**

```powershell
git add src/ui/main_page.py tests/ui/test_recommendation_page.py
git commit -m "feat: build recommendation filter board"
```

---

### Task 4: Verify the complete recommendation feature

**Files:**
- Verify: `src/ui/data_loader.py`
- Verify: `src/ui/recommendations.py`
- Verify: `src/ui/main_page.py`
- Verify: `tests/test_data_loader.py`
- Verify: `tests/ui/test_recommendations.py`
- Verify: `tests/ui/test_recommendation_page.py`

**Interfaces:**
- Consumes: the finished recommendation feature from Tasks 1-3.
- Produces: test and runtime evidence that the feature works with repository data and other pages remain intact.

- [ ] **Step 1: Validate live-data coverage**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -c "from src.ui.data_loader import load_app_data; from src.ui.recommendations import build_filter_options; d=load_app_data(); o=build_filter_options(d['festivals']); print({'festivals': len(d['festivals']), 'regions': len(o['regions']) - 1, 'themes': len(o['themes']) - 1, 'audiences': len(o['audiences']) - 1, 'free': sum(r.get('fee_category') == '무료' for r in d['festivals']), 'paid': sum(r.get('fee_category') == '유료' for r in d['festivals'])}); assert '미분류' not in str(o); assert len(o['regions']) > 1; assert len(o['themes']) > 1"
```

Expected: non-zero region and theme counts, populated fee counts, and exit code 0.

- [ ] **Step 2: Run the full test suite**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q
```

Expected: exit code 0 with no failed tests.

- [ ] **Step 3: Start the real Streamlit entry point on an unused port**

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m streamlit run 'src\ui\app.py' --server.port=8502 --server.headless=true
```

Expected: Streamlit prints `Local URL: http://localhost:8502` and remains running.

- [ ] **Step 4: Verify the server responds**

In a second PowerShell process, run:

```powershell
$response = Invoke-WebRequest -Uri 'http://localhost:8502' -UseBasicParsing -TimeoutSec 10
if ($response.StatusCode -ne 200) { throw "Unexpected HTTP status: $($response.StatusCode)" }
```

Expected: exit code 0 and HTTP status 200.

- [ ] **Step 5: Review the final diff for scope**

Run:

```powershell
git status --short
git diff --check
git diff --stat HEAD~3..HEAD
```

Expected: only the recommendation implementation, its shared enrichment, and related tests/documentation appear; no whitespace errors are reported.
