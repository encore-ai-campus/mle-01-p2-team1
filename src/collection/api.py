import requests
import json
import time
import os

from dotenv import load_dotenv
from config import FESTIVAL_FULL_SAMPLE_PATH

load_dotenv()

SERVICE_KEY = os.getenv("TOUR_API_SERVICE_KEY")
if not SERVICE_KEY:
    raise RuntimeError("TOUR_API_SERVICE_KEY가 .env에 설정되어 있지 않습니다.")

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"


# --------------------------------------------------
# 공통 API 호출 함수
# --------------------------------------------------
def call_api(endpoint, params):
    common_params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalGraphRAG",
        "_type": "json",
    }

    common_params.update(params)

    for attempt in range(3):
        try:
            response = requests.get(
                f"{BASE_URL}/{endpoint}",
                params=common_params,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if "response" not in data:
                print(f"[API 오류] {endpoint}: {data}")
                return []

            body = data["response"]["body"]
            items = body.get("items")

            if not items:
                return []

            return items.get("item", [])

        except requests.exceptions.Timeout:
            print(
                f"[Timeout] {endpoint} "
                f"{attempt + 1}/3회 실패 → 재시도"
            )
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"[요청 오류] {endpoint}: {e}")
            return []

    print(f"[실패] {endpoint} 3회 재시도 실패")
    return []


# --------------------------------------------------
# 1. 2026년 축제 전체 목록 수집
# --------------------------------------------------
all_festivals = []

page_no = 1
num_of_rows = 100

while True:
    params = {
        "eventStartDate": "20260101",
        "eventEndDate": "20261231",
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }

    response = requests.get(
        f"{BASE_URL}/searchFestival2",
        params={
            "serviceKey": SERVICE_KEY,
            "MobileOS": "ETC",
            "MobileApp": "FestivalGraphRAG",
            "_type": "json",
            **params,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    body = data["response"]["body"]

    items = body.get("items", {}).get("item", [])
    total_count = body["totalCount"]

    all_festivals.extend(items)

    print(
        f"목록 {page_no}페이지 완료 "
        f"({len(all_festivals)} / {total_count})"
    )

    if len(all_festivals) >= total_count:
        break

    page_no += 1


print()
print(f"축제 목록 총 {len(all_festivals)}개 수집 완료")


# --------------------------------------------------
# 2. 각 축제의 overview 본문 수집
# --------------------------------------------------
festival_details = []

for i, festival in enumerate(all_festivals, start=1):

    content_id = festival["contentid"]

    print(
        f"[{i}/{len(all_festivals)}] "
        f"{festival.get('title')} 수집 중..."
    )

    common = call_api(
        "detailCommon2",
        {
            "contentId": content_id,
        },
    )

    # detailCommon2 응답이 있으면 첫 번째 데이터 사용
    common_data = common[0] if common else {}

    merged = {
        "search": festival,
        "common": common_data,
    }

    festival_details.append(merged)

    # 너무 빠른 연속 요청 방지
    time.sleep(0.1)


print()
print("전체 축제 상세 본문 수집 완료")


# --------------------------------------------------
# 3. JSON 파일 저장
# --------------------------------------------------
output_file = FESTIVAL_FULL_SAMPLE_PATH
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        festival_details,
        f,
        ensure_ascii=False,
        indent=2,
    )


print(f"{output_file} 저장 완료")
