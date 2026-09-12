import os
import json
import time

import requests
from dotenv import load_dotenv

# 환경변수 설정

load_dotenv()

SERVICE_KEY = os.getenv("TOUR_API_SERVICE_KEY")

if not SERVICE_KEY:
    raise ValueError(
        "TOUR_API_SERVICE_KEY가 설정되어 있지 않습니다. "
        ".env 파일을 확인해주세요."
    )

# 설정

LIST_URL = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"
DETAIL_URL = "https://apis.data.go.kr/B551011/KorService2/detailCommon2"

START_DATE = "20260101"
END_DATE = "20261231"

NUM_OF_ROWS = 100
OUTPUT_PATH = "data/raw/festival_raw.json"


# 1. 2026년 축제 전체 목록 수집


all_items = []
page_no = 1

while True:

    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": NUM_OF_ROWS,
        "pageNo": page_no,
        "MobileOS": "ETC",
        "MobileApp": "KGProject",
        "_type": "json",
        "arrange": "C",
        "eventStartDate": START_DATE,
        "eventEndDate": END_DATE
    }

    res = requests.get(
        LIST_URL,
        params=params,
        timeout=30
    )
    res.raise_for_status()

    data = res.json()

    body = data["response"]["body"]

    total_count = body["totalCount"]

    items = body.get("items", {})

    # 더 이상 데이터가 없으면 종료
    if not items:
        break

    page_items = items.get("item", [])

    if not page_items:
        break

    all_items.extend(page_items)

    print(
        f"목록 수집 중: {len(all_items)} / {total_count}"
    )

    # 전체 데이터 다 받았으면 종료
    if len(all_items) >= total_count:
        break

    page_no += 1


print()
print("2026년 축제 목록 수:", len(all_items))


# 2. 각 축제 상세정보 조회


festival_raw = []

for i, item in enumerate(all_items, start=1):

    contentid = item["contentid"]

    detail_params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "KGProject",
        "_type": "json",
        "contentId": contentid
    }

    try:

        r = requests.get(
            DETAIL_URL,
            params=detail_params,
            timeout=30
        )
        r.raise_for_status()

        detail_data = r.json()

        detail_items = (
            detail_data["response"]["body"]
            .get("items", {})
        )

        # 상세정보가 있는 경우
        if detail_items:

            detail_list = detail_items.get("item", [])

            if detail_list:
                detail = detail_list[0]
            else:
                detail = {}

        else:
            detail = {}

        # 목록 + 상세정보 합치기

        merged = item.copy()

        # 상세정보를 추가
        # 동일한 컬럼은 상세정보 값으로 덮어씀
        merged.update(detail)

        festival_raw.append(merged)

        print(
            f"[{i}/{len(all_items)}] "
            f"{item.get('title', '')}"
        )

    except Exception as e:

        print(
            f"오류 발생: "
            f"{contentid} / "
            f"{item.get('title', '')}"
        )

        print(e)

        # 상세조회 실패해도 목록 정보는 남김
        festival_raw.append(item)

    # API에 너무 빠르게 요청하지 않도록 약간 쉬기
    time.sleep(0.05)


# 3. JSON 저장

# 저장 폴더가 없을 경우 생성
os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        festival_raw,
        f,
        ensure_ascii=False,
        indent=2
    )


# 4. 확인

print()
print("=" * 50)
print("저장 완료")
print("파일:", OUTPUT_PATH)
print("총 축제 수:", len(festival_raw))

overview_count = sum(
    1
    for row in festival_raw
    if row.get("overview", "")
)

print("overview 있는 축제:", overview_count)