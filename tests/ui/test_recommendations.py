from datetime import date

from src.ui.recommendations import build_filter_options, recommend_festivals


def festival(
    name: str,
    *,
    region: str = "서울",
    themes: list[str] | None = None,
    theme_categories: list[str] | None = None,
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
        "theme_categories": theme_categories or [],
        "audiences": audiences or [],
        "fee_category": fee,
        "start_date": start,
        "end_date": end,
        "relation_count": relations,
    }


def test_build_filter_options_uses_real_values_without_unclassified():
    rows = [
        festival("봄 축제", themes=["벚꽃"], theme_categories=["자연생태"], audiences=["가족"]),
        festival("빈 축제", region="", themes=[], audiences=[], fee=""),
    ]

    options = build_filter_options(rows)

    assert options["regions"] == ["전체", "서울"]
    assert options["themes"] == ["전체", "자연생태"]
    assert options["audiences"] == ["전체", "가족"]
    assert options["fees"] == ["전체", "무료", "유료"]
    assert "미분류" not in str(options)


def test_recommend_festivals_combines_all_selected_filters():
    rows = [
        festival("선택됨", themes=["벚꽃"], theme_categories=["자연생태"], audiences=["가족"]),
        festival("다른 지역", region="부산", themes=["벚꽃"], theme_categories=["자연생태"], audiences=["가족"]),
        festival("유료 축제", themes=["벚꽃"], theme_categories=["자연생태"], audiences=["가족"], fee="유료"),
    ]

    selected, total = recommend_festivals(
        rows,
        region="서울",
        theme="자연생태",
        month="9월",
        audience="가족",
        fee="무료",
        today=date(2026, 9, 18),
    )

    assert [row["name"] for row in selected] == ["선택됨"]
    assert total == 1


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
