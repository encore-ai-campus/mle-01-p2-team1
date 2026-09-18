"""Pure option, filtering, and ranking helpers for festival recommendations."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .data_loader import THEME_CATEGORY_ORDER


ALL = "전체"
PRESETS = [ALL, "인기", "이번 달", "곧 시작", "가족 추천"]
AUDIENCE_ORDER = ["전 연령", "어린이", "청소년", "성인", "가족", "시니어"]
RECOMMENDATION_PAGE_SIZE = 15


def _parse_date(value: Any) -> date | None:
    text = str(value or "").replace("-", "").replace(".", "")[:8]
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


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
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return months


def _event_intersects_month(row: dict[str, Any], year: int, month: int) -> bool:
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date")) or start
    if start is None or end is None:
        return False

    month_start = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    month_end = next_month - timedelta(days=1)
    return start <= month_end and end >= month_start


def _theme_values(row: dict[str, Any]) -> list[str]:
    """Read canonical categories, with a raw-theme fallback for old callers."""
    categories = row.get("theme_categories")
    if categories:
        return [str(value) for value in categories if value]
    return [str(value) for value in row.get("themes", []) if value]


def build_filter_options(festivals: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Build user-facing options from populated recommendation fields only."""
    regions = sorted({str(row.get("region") or "") for row in festivals} - {""})
    present_themes = {value for row in festivals for value in _theme_values(row)}
    themes = [value for value in THEME_CATEGORY_ORDER if value in present_themes]
    themes.extend(sorted(present_themes - set(themes)))
    present_audiences = {
        str(value)
        for row in festivals
        for value in row.get("audiences", [])
        if value
    }
    audiences = [value for value in AUDIENCE_ORDER if value in present_audiences]
    return {
        "regions": [ALL, *regions],
        "themes": [ALL, *themes],
        "months": [ALL, *[f"{month}월" for month in range(1, 13)]],
        "audiences": [ALL, *audiences],
        "fees": [ALL, "무료", "유료"],
    }


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
    limit: int = RECOMMENDATION_PAGE_SIZE,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Filter and rank festivals, returning the visible rows and total count."""
    rows = list(festivals)
    if region != ALL:
        rows = [row for row in rows if row.get("region") == region]
    if theme != ALL:
        rows = [row for row in rows if theme in _theme_values(row)]
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
            row
            for row in rows
            if family_categories.intersection(row.get("audiences", []))
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
    start = max(offset, 0)
    return rows[start : start + max(limit, 0)], total
