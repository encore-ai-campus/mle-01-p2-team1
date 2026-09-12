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

LIST_URL = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"
DETAIL_URL = "https://apis.data.go.kr/B551011/KorService2/detailCommon2"

NUM_OF_ROWS = 100
OUTPUT_PATH = "data/raw/experience_raw.json"


# 1. 기존 파일 확인


if os.path.exists(OUTPUT_PATH):

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        experience_raw = json.load(f)

    print("기존 파일을 불러왔습니다.")
    print("전체 데이터 수:", len(experience_raw))

else:

    # 2. 체험관광 전체 목록 수집

    all_items = []
    page_no = 1

    while True:

        params = {
            "serviceKey": SERVICE_KEY,
            "MobileOS": "ETC",
            "MobileApp": "KGProject",
            "_type": "json",
            "numOfRows": NUM_OF_ROWS,
            "pageNo": page_no,
            "arrange": "C",
            "lclsSystm1": "EX"
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

        if not items:
            break

        page_items = items.get("item", [])

        if not page_items:
            break

        all_items.extend(page_items)

        print(
            f"목록 수집 중: "
            f"{len(all_items)} / {total_count}"
        )

        if len(all_items) >= total_count:
            break

        page_no += 1

    experience_raw = all_items

    print()
    print("체험관광 전체 목록 수:", len(experience_raw))


# 3. overview 없는 항목 확인


missing = [
    row
    for row in experience_raw
    if not row.get("overview")
]

print()
print(
    "현재 overview 있음:",
    len(experience_raw) - len(missing)
)

print(
    "재수집 대상:",
    len(missing)
)


# 4. 상세정보 수집


success = 0
failed = 0

for i, row in enumerate(missing, start=1):

    contentid = row["contentid"]

    params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "KGProject",
        "_type": "json",
        "contentId": contentid
    }

    try:

        r = requests.get(
            DETAIL_URL,
            params=params,
            timeout=30
        )

        # 일일 호출 제한
        if r.status_code == 429:

            print()
            print("일일 API 호출 한도 도달")
            print("현재까지 저장하고 종료합니다.")

            break

        r.raise_for_status()

        data = r.json()

        detail = (
            data["response"]["body"]
            ["items"]["item"][0]
        )

        row.update(detail)

        success += 1

    except Exception as e:

        failed += 1

        print(
            f"오류: "
            f"{contentid} / "
            f"{row.get('title', '')}"
        )

        print(e)

    if i % 100 == 0:

        print(
            f"진행: {i}/{len(missing)} "
            f"| 성공: {success} "
            f"| 실패: {failed}"
        )

    time.sleep(0.1)


# 5. JSON 저장


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
        experience_raw,
        f,
        ensure_ascii=False,
        indent=2
    )


# 6. 최종 확인


overview_count = sum(
    bool(row.get("overview"))
    for row in experience_raw
)

print()
print("=" * 50)
print("저장 완료")
print("파일:", OUTPUT_PATH)
print("전체 체험관광 수:", len(experience_raw))
print("overview 있음:", overview_count)
print(
    "overview 없음:",
    len(experience_raw) - overview_count
)
print("이번 실행 성공:", success)
print("이번 실행 실패:", failed)