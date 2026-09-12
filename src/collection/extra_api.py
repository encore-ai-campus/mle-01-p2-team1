import json
import time
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# =========================================================
# 설정
# =========================================================

load_dotenv()

SERVICE_KEY = os.getenv("TOUR_API_SERVICE_KEY")
if not SERVICE_KEY:
    raise RuntimeError("TOUR_API_SERVICE_KEY가 .env에 설정되어 있지 않습니다.")

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"

# 기존 api.py에서 만들어둔 축제 데이터
FESTIVAL_FILE = "festivals_2026_full.json"

# 결과 저장 폴더
OUTPUT_DIR = Path("data/extra")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 주변 관광정보 반경
RADIUS = 5000  # 5km

# 요청 간 대기시간
REQUEST_DELAY = 0.15

# Timeout 재시도 횟수
MAX_RETRIES = 3


# =========================================================
# 공통 API 호출 함수
# =========================================================

def call_api(endpoint, params):
    request_params = {
        "serviceKey": SERVICE_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalGraphRAG",
        "_type": "json",
        **params,
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = requests.get(
                f"{BASE_URL}/{endpoint}",
                params=request_params,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            # API 자체 에러
            if "response" not in data:
                print(
                    f"[API 오류] {endpoint} "
                    f"attempt={attempt}/{MAX_RETRIES}"
                )
                print(data)

                # 일시적인 오류일 가능성이 있으므로 재시도
                if attempt < MAX_RETRIES:
                    time.sleep(3)
                    continue

                return {
                    "items": [],
                    "totalCount": 0,
                    "error": data,
                }

            body = data["response"]["body"]

            items_container = body.get("items")

            if not items_container:
                items = []

            else:
                items = items_container.get("item", [])

                # 간혹 item이 list가 아니라 dict 1개로 올 경우 대비
                if isinstance(items, dict):
                    items = [items]

            return {
                "items": items,
                "totalCount": body.get("totalCount", len(items)),
                "error": None,
            }

        except requests.exceptions.Timeout:
            print(
                f"[TIMEOUT] {endpoint} "
                f"{attempt}/{MAX_RETRIES}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(
                f"[REQUEST ERROR] {endpoint}: {e}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(3)
            else:
                return {
                    "items": [],
                    "totalCount": 0,
                    "error": str(e),
                }

        except ValueError as e:
            print(
                f"[JSON ERROR] {endpoint}: {e}"
            )

            return {
                "items": [],
                "totalCount": 0,
                "error": str(e),
            }

    return {
        "items": [],
        "totalCount": 0,
        "error": "retry exhausted",
    }


# =========================================================
# JSON 저장
# =========================================================

def save_json(filename, data):

    path = OUTPUT_DIR / filename

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n저장 완료: {path}")


# =========================================================
# 기존 축제 데이터 불러오기
# =========================================================

def load_festivals():

    with open(
        FESTIVAL_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    festivals = []

    for row in data:

        # 기존 구조:
        # {
        #   "search": {...},
        #   "common": {...}
        # }

        search = row.get("search", {})
        common = row.get("common", {})

        content_id = (
            search.get("contentid")
            or common.get("contentid")
        )

        content_type_id = (
            search.get("contenttypeid")
            or common.get("contenttypeid")
        )

        title = (
            search.get("title")
            or common.get("title")
        )

        map_x = (
            search.get("mapx")
            or common.get("mapx")
        )

        map_y = (
            search.get("mapy")
            or common.get("mapy")
        )

        festivals.append(
            {
                "contentid": content_id,
                "contenttypeid": content_type_id,
                "title": title,
                "mapx": map_x,
                "mapy": map_y,
            }
        )

    return festivals


# =========================================================
# 1. detailIntro2
# 2026 축제 700건 소개정보
# =========================================================

def collect_intro(festivals):

    print("\n========================================")
    print("1. detailIntro2 전체 수집")
    print("========================================")

    results = []

    for i, festival in enumerate(festivals, start=1):

        print(
            f"[{i}/{len(festivals)}] "
            f"{festival['title']}"
        )

        result = call_api(
            "detailIntro2",
            {
                "contentId": festival["contentid"],
                "contentTypeId": festival["contenttypeid"],
            },
        )

        results.append(
            {
                "contentid": festival["contentid"],
                "title": festival["title"],
                "intro": result["items"],
                "error": result["error"],
            }
        )

        # 50건마다 중간 저장
        if i % 50 == 0:
            save_json(
                "festival_intro_2026.json",
                results,
            )

        time.sleep(REQUEST_DELAY)

    save_json(
        "festival_intro_2026.json",
        results,
    )

    return results


# =========================================================
# 2. detailInfo2
# 2026 축제 700건 반복 상세정보
# =========================================================

def collect_info(festivals):

    print("\n========================================")
    print("2. detailInfo2 전체 수집")
    print("========================================")

    results = []

    for i, festival in enumerate(festivals, start=1):

        print(
            f"[{i}/{len(festivals)}] "
            f"{festival['title']}"
        )

        result = call_api(
            "detailInfo2",
            {
                "contentId": festival["contentid"],
                "contentTypeId": festival["contenttypeid"],
            },
        )

        results.append(
            {
                "contentid": festival["contentid"],
                "title": festival["title"],
                "info": result["items"],
                "error": result["error"],
            }
        )

        if i % 50 == 0:
            save_json(
                "festival_info_2026.json",
                results,
            )

        time.sleep(REQUEST_DELAY)

    save_json(
        "festival_info_2026.json",
        results,
    )

    return results


# =========================================================
# 3. searchStay2
# 전국 숙박정보 전체 수집
# =========================================================

def collect_stays():

    print("\n========================================")
    print("3. searchStay2 전국 숙박 전체 수집")
    print("========================================")

    results = []

    page_no = 1
    num_of_rows = 100

    while True:

        result = call_api(
            "searchStay2",
            {
                "numOfRows": num_of_rows,
                "pageNo": page_no,
                "arrange": "A",
            },
        )

        items = result["items"]
        total_count = result["totalCount"]

        if result["error"]:
            print(
                f"숙박 {page_no}페이지 오류"
            )
            break

        if not items:
            break

        results.extend(items)

        print(
            f"숙박 {page_no}페이지 완료 "
            f"({len(results)} / {total_count})"
        )

        # 중간 저장
        save_json(
            "stays_all.json",
            results,
        )

        if len(results) >= total_count:
            break

        page_no += 1

        time.sleep(REQUEST_DELAY)

    save_json(
        "stays_all.json",
        results,
    )

    return results


# =========================================================
# 4. locationBasedList2
# 700개 축제 각각 주변 5km 관광정보
# =========================================================

def collect_nearby(festivals):

    print("\n========================================")
    print("4. locationBasedList2 주변 관광정보 수집")
    print("========================================")

    results = []

    valid_festivals = [
        f
        for f in festivals
        if f.get("mapx") and f.get("mapy")
    ]

    for i, festival in enumerate(
        valid_festivals,
        start=1,
    ):

        print(
            f"[{i}/{len(valid_festivals)}] "
            f"{festival['title']} 주변 {RADIUS // 1000}km"
        )

        result = call_api(
            "locationBasedList2",
            {
                "mapX": festival["mapx"],
                "mapY": festival["mapy"],
                "radius": RADIUS,
                "arrange": "E",
                "numOfRows": 100,
                "pageNo": 1,
            },
        )

        results.append(
            {
                "festival_contentid":
                    festival["contentid"],

                "festival_title":
                    festival["title"],

                "festival_mapx":
                    festival["mapx"],

                "festival_mapy":
                    festival["mapy"],

                "radius_meter":
                    RADIUS,

                "nearby":
                    result["items"],

                "totalCount":
                    result["totalCount"],

                "error":
                    result["error"],
            }
        )

        # 20개 축제마다 중간 저장
        if i % 20 == 0:
            save_json(
                "festival_nearby_5km.json",
                results,
            )

        time.sleep(REQUEST_DELAY)

    save_json(
        "festival_nearby_5km.json",
        results,
    )

    return results


# =========================================================
# 5. lclsSystmCode2
# 관광 분류체계 전체 계층
# =========================================================

def collect_classification_codes():

    print("\n========================================")
    print("5. lclsSystmCode2 분류체계 수집")
    print("========================================")

    final = []

    # -----------------------------------------
    # 1Depth
    # -----------------------------------------

    level1_result = call_api(
        "lclsSystmCode2",
        {
            "numOfRows": 100,
            "pageNo": 1,
        },
    )

    level1_items = level1_result["items"]

    print(
        f"1Depth: {len(level1_items)}개"
    )

    for i, level1 in enumerate(
        level1_items,
        start=1,
    ):

        code1 = level1.get("lclsSystm1")

        print(
            f"[1Depth {i}/{len(level1_items)}] "
            f"{code1}"
        )

        # -------------------------------------
        # 2Depth
        # -------------------------------------

        level2_result = call_api(
            "lclsSystmCode2",
            {
                "lclsSystm1": code1,
                "numOfRows": 100,
                "pageNo": 1,
            },
        )

        level2_nodes = []

        for level2 in level2_result["items"]:

            code2 = level2.get("lclsSystm2")

            # ---------------------------------
            # 3Depth
            # ---------------------------------

            level3_result = call_api(
                "lclsSystmCode2",
                {
                    "lclsSystm1": code1,
                    "lclsSystm2": code2,
                    "numOfRows": 100,
                    "pageNo": 1,
                },
            )

            level2_nodes.append(
                {
                    **level2,
                    "children":
                        level3_result["items"],
                }
            )

            time.sleep(REQUEST_DELAY)

        final.append(
            {
                **level1,
                "children": level2_nodes,
            }
        )

        save_json(
            "classification_codes.json",
            final,
        )

        time.sleep(REQUEST_DELAY)

    save_json(
        "classification_codes.json",
        final,
    )

    return final


# =========================================================
# MAIN
# =========================================================

def main():

    festivals = load_festivals()

    print(
        f"기존 축제 데이터 "
        f"{len(festivals)}건 로드 완료"
    )

    # 1
    collect_intro(festivals)

    # 2
    collect_info(festivals)

    # 3
    collect_stays()

    # 4
    collect_nearby(festivals)

    # 5
    collect_classification_codes()

    print("\n========================================")
    print("모든 추가 데이터 수집 완료")
    print("========================================")


if __name__ == "__main__":
    main()
