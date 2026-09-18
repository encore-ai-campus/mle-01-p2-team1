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
                "themes": [] if index == 1 else ["문화예술"],
                "audiences": [] if index == 1 else ["가족"],
                "fee_category": "무료",
                "usage_fee": "무료",
                "start_date": "20260920",
                "end_date": "20260921",
                "relation_count": index,
            }
            for index in range(1, 31)
        ],
        "triples": [],
    }
    render_recommendations(st, data)


def test_recommendation_page_renders_real_filters_and_fourteen_cards_per_page():
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
    assert len([button for button in at.button if button.label == "상세 보기"]) == 14
    assert any(button.label == "다음" for button in at.button)
    assert any("가족이 함께 즐기는 축제" in markdown.value for markdown in at.markdown)
    assert not any("**요금**" in markdown.value for markdown in at.markdown)
    assert any("recommendation-pagination" in markdown.value for markdown in at.markdown)
    assert any("margin-top: auto" in markdown.value for markdown in at.markdown)
    assert any(
        "height: 280px" in markdown.value
        and "overflow: hidden" in markdown.value
        and "-webkit-line-clamp: 2" in markdown.value
        for markdown in at.markdown
    )
    assert any(
        "st-key-recommend-card-" in markdown.value
        and "overflow-y: hidden" in markdown.value
        for markdown in at.markdown
    )
    assert any("recommendation-labels-empty" in markdown.value for markdown in at.markdown)
    assert any(".recommendation-labels" in markdown.value and "min-height" in markdown.value for markdown in at.markdown)


def test_recommendation_page_moves_to_next_page():
    at = AppTest.from_function(recommendation_app, default_timeout=30).run()

    next_button = next(button for button in at.button if button.label == "다음")
    next_button.click().run()

    assert len([button for button in at.button if button.label == "상세 보기"]) == 14
    assert any(button.label == "이전" for button in at.button)
