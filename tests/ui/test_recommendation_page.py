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
