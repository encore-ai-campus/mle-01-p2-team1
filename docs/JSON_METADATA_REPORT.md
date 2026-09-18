# 2026 축제 JSON 메타데이터 정리 보고서

분석 대상: `festivals_2026_full.json` 및 `data/extra/*.json`

## 1. 한눈에 보는 파일별 역할

| 파일 | 구조/건수 | 역할 | 정리 판단 |
|---|---:|---|---|
| `festivals_2026_full.json` | 배열 700건 | 축제 검색 결과(`search`)와 상세 공통정보(`common`)를 한 레코드에 결합 | 축제 목록 화면에는 필요. `search`와 `common`의 중복 필드는 한쪽만 남겨도 됨 |
| `data/extra/festival_intro_2026.json` | 배열 700건 | 행사장·주최·운영시간·프로그램 등 축제 상세 소개 | 상세 페이지에 필요할 때 보존 |
| `data/extra/festival_info_2026.json` | 배열 700건 | 행사소개/이용안내 등 가변적인 추가 안내 항목 | 상세 페이지나 검색 색인에 필요할 때 보존 |
| `data/extra/festival_nearby_5km.json` | 배열 700건 | 축제 좌표 기준 반경 5km 관광지 목록 | 주변 추천 기능이 없으면 제거 가능. 사용 시 `nearby`만 별도 테이블화 권장 |
| `data/extra/stays_all.json` | 배열 3,004건 | 전국 숙박 장소 목록 | 숙박 추천 기능이 없으면 제거 가능. 축제 데이터와 직접 연결되지 않음 |
| `data/extra/classification_codes.json` | 배열 10개 | 관광 API 분류코드와 하위 코드 트리 | 코드명 해석/필터에 필요. 코드가 이미 정규화되어 있으면 운영 데이터에는 제외 가능 |

## 2. 공통 규칙

- 날짜 필드는 대부분 `YYYYMMDD` 문자열, 시각 필드는 `YYYYMMDDHHmmss` 문자열이다. 날짜 계산 전 날짜형으로 변환한다.
- `contentid`는 관광 콘텐츠의 식별자이며 파일 간 연결 키다. `festivals_2026_full`의 축제와 상세/주변 데이터는 이 값으로 조인한다.
- `contenttypeid`는 관광 API 콘텐츠 유형 코드다. 축제는 보통 `15`, 숙박은 `32`다.
- 좌표 `mapx`는 경도(longitude), `mapy`는 위도(latitude)이며 원본은 문자열이다. 거리 계산 전 숫자로 변환한다.
- 빈 문자열(`""`)은 값이 없음/미수집을 뜻한다. `null`과 함께 결측으로 처리하되, API 오류 여부와 혼동하지 않는다.
- `cat1`, `cat2`, `cat3`는 관광 API 분류코드 1·2·3단계, `lclsSystm1~3`는 지역/관광 콘텐츠의 분류 시스템 코드다. 실제 화면 표시명은 `classification_codes.json` 또는 별도 코드표로 해석한다.

## 3. `festivals_2026_full.json`

각 레코드는 `search`와 `common` 객체를 가진다. 두 객체는 같은 축제의 검색 API 결과와 상세 공통 API 결과이며, 다음 필드가 중복된다.

### `search` 필드

| 필드 | 의미 |
|---|---|
| `addr1` | 기본 주소 |
| `addr2` | 상세 주소/장소 설명 |
| `zipcode` | 우편번호 |
| `cat1`, `cat2`, `cat3` | 관광 API 1·2·3단계 분류코드 |
| `contentid` | 축제 콘텐츠 ID; 조인 키 |
| `contenttypeid` | 콘텐츠 유형 ID; 축제는 대체로 15 |
| `createdtime` | 원천 콘텐츠 등록 시각 |
| `eventstartdate`, `eventenddate` | 행사 시작일·종료일 |
| `firstimage`, `firstimage2` | 대표 이미지 URL과 대체/두 번째 이미지 URL |
| `cpyrhtDivCd` | 이미지/콘텐츠 저작권 구분 코드 |
| `mapx`, `mapy` | 경도·위도 |
| `mlevel` | 지도 표시 레벨/확대 수준 |
| `modifiedtime` | 원천 콘텐츠 최종 수정 시각 |
| `areacode` | 광역 지역 코드 |
| `sigungucode` | 시·군·구 코드 |
| `tel` | 문의 전화번호 |
| `title` | 축제명 |
| `lDongRegnCd` | 법정동/행정 지역 광역 코드 |
| `lDongSignguCd` | 법정동/행정 지역 시·군·구 코드 |
| `lclsSystm1`, `lclsSystm2`, `lclsSystm3` | 관광 분류 체계의 1·2·3단계 코드 |
| `progresstype` | 진행 유형(예: 선택 없음/상시 등 원천 표기) |
| `festivaltype` | 축제 유형(원천 데이터에 없으면 빈 문자열) |

### `common` 필드

`common`의 필드는 아래처럼 검색 결과와 의미가 동일한 공통 필드와, 상세 조회에서 추가되는 필드로 나뉜다.

- 중복 공통 필드: `contentid`, `contenttypeid`, `title`, `createdtime`, `modifiedtime`, `tel`, `firstimage`, `firstimage2`, `cpyrhtDivCd`, `areacode`, `sigungucode`, `lDongRegnCd`, `lDongSignguCd`, `lclsSystm1`, `lclsSystm2`, `lclsSystm3`, `cat1`, `cat2`, `cat3`, `addr1`, `addr2`, `zipcode`, `mapx`, `mapy`, `mlevel`. 의미는 위 `search` 설명과 같다.

| 추가 필드 | 의미 |
|---|---|
| `telname` | 전화번호의 담당 기관/문의처 이름 |
| `homepage` | 행사 또는 기관 홈페이지 URL |
| `overview` | 축제의 긴 소개/개요 문장 |

※ `search`와 `common`을 모두 보관하면 원본 응답 추적에는 유리하지만 저장량과 중복이 늘어난다. 운영용 축제 테이블은 `contentid` 기준으로 하나의 통합 레코드로 합치는 것이 적절하다.

## 4. `festival_intro_2026.json`

최상위 필드 `contentid`, `title`은 축제 식별·표시용이다. `intro`는 보통 0~1개의 상세 객체 배열이며, `error`는 해당 API 호출 오류 정보(정상 응답이면 `null`)다.

| `intro` 필드 | 의미 |
|---|---|
| `contentid`, `contenttypeid` | 축제 ID와 콘텐츠 유형 |
| `sponsor1`, `sponsor1tel` | 제1 주최/주관 기관과 전화번호 |
| `sponsor2`, `sponsor2tel` | 제2 주최/주관 기관과 전화번호 |
| `eventstartdate`, `eventenddate` | 행사 시작일·종료일 |
| `playtime` | 운영/공연 시간 |
| `eventplace` | 행사 개최 장소명 |
| `eventhomepage` | 행사 전용 홈페이지 URL |
| `agelimit` | 관람/참여 연령 제한 |
| `bookingplace` | 예약·예매 장소 또는 채널 |
| `placeinfo` | 장소 이용/위치 안내 |
| `subevent` | 부대 행사 |
| `program` | 주요 프로그램 |
| `usetimefestival` | 이용 시간 또는 행사 이용 안내 |
| `discountinfofestival` | 할인 정보 |
| `spendtimefestival` | 예상 소요 시간 |
| `festivalgrade` | 축제 등급/분류 원천값 |
| `progresstype` | 진행 유형 |
| `festivaltype` | 축제 유형 |

## 5. `festival_info_2026.json`

최상위 `contentid`, `title`은 축제 식별·표시용이고, `error`는 API 오류 정보다. `info`는 항목 수가 행사마다 달라질 수 있는 배열이다.

| `info` 필드 | 의미 |
|---|---|
| `contentid`, `contenttypeid` | 축제 ID와 콘텐츠 유형 |
| `serialnum` | 해당 안내 항목의 순번 |
| `infoname` | 안내 항목명(예: 행사소개, 이용안내) |
| `infotext` | 안내 항목의 실제 내용 |
| `fldgubun` | 안내 항목/필드 구분값 |

`info`는 고정 컬럼으로 펼치기보다 `(contentid, serialnum, infoname, infotext)` 형태의 자식 테이블로 두는 편이 안전하다.

## 6. `festival_nearby_5km.json`

최상위 `festival_contentid`, `festival_title`, `festival_mapx`, `festival_mapy`는 기준 축제 정보이며, `radius_meter`는 검색 반경(현재 5,000m)이다. `nearby`는 주변 장소 배열, `totalCount`는 반환된 주변 장소 수, `error`는 API 오류 정보다.

`nearby`의 필드: `addr1`(주소), `addr2`(상세 주소), `zipcode`(우편번호), `areacode`(광역 지역 코드), `cat1~cat3`(분류코드), `contentid`(주변 장소 ID), `contenttypeid`(콘텐츠 유형), `createdtime`(등록 시각), `dist`(기준 축제와의 거리; 원천 문자열), `firstimage`·`firstimage2`(이미지 URL), `cpyrhtDivCd`(저작권 코드), `mapx`·`mapy`(경도·위도), `mlevel`(지도 레벨), `modifiedtime`(수정 시각), `sigungucode`(시·군·구 코드), `tel`(전화번호), `title`(장소명), `lDongRegnCd`·`lDongSignguCd`(지역 코드), `lclsSystm1~3`(분류 체계 코드).

## 7. `stays_all.json`

3,004개의 숙박 장소를 평탄화한 배열이다. 행사별 연결 키는 없으므로 축제 주변 숙박으로 사용할 때는 `mapx`, `mapy`로 거리 계산하거나 별도 조인 결과를 만들어야 한다.

필드 의미는 다음과 같다: `addr1`(기본 주소), `addr2`(상세 주소), `areacode`(광역 지역 코드), `sigungucode`(시·군·구 코드), `cat1~cat3`(관광 분류코드), `contentid`(숙박 콘텐츠 ID), `contenttypeid`(콘텐츠 유형; 대체로 32), `createdtime`(등록 시각), `firstimage`·`firstimage2`(이미지 URL), `cpyrhtDivCd`(저작권 구분), `mapx`·`mapy`(경도·위도), `mlevel`(지도 레벨), `modifiedtime`(수정 시각), `tel`(전화번호), `title`(숙박시설명), `zipcode`(우편번호), `lDongRegnCd`·`lDongSignguCd`(지역 코드), `lclsSystm1~3`(분류 체계 코드).

## 8. `classification_codes.json`

최상위 배열은 10개의 1차 코드다. 각 노드는 `code`(분류 코드), `name`(사람이 읽는 분류명), `rnum`(표시/정렬 순번), `children`(하위 분류 배열)을 가진다. 현재 트리는 동일한 10개 코드가 하위에도 반복되는 형태이므로, 실제 분류 필터에서는 `code`를 키로 사용하고 `children`은 코드 사전 구축용으로만 보관하면 된다.

주요 1차 코드: `AC` 숙박, `C01` 추천코스, `EV` 축제·공연·행사, `EX` 체험관광, `FD` 음식점, `HS` 역사관광, `LS` 레포츠, `NA` 자연관광, `SH` 쇼핑, `VE` 문화관광.

## 9. 정리 권고

1. 축제 목록/상세 기능만 필요하면 `festivals_2026_full.json`을 핵심으로 두고, `festival_intro_2026.json`과 `festival_info_2026.json`을 상세 기능용으로 보존한다.
2. `festivals_2026_full.json`에서는 `search`·`common`의 중복을 제거하고, `contentid`를 기본 키로 한 통합 축제 레코드로 만든다.
3. 주변 추천이 없으면 `festival_nearby_5km.json`, 숙박 추천이 없으면 `stays_all.json`은 운영 배포본에서 제외할 수 있다. 원본 보관본과 운영본은 분리한다.
4. `classification_codes.json`은 코드명을 화면에 보여주거나 필터링할 때만 필요하다. 코드가 애플리케이션에 상수로 들어가 있다면 원본 JSON은 개발용으로만 보관한다.
5. `error`가 `null`인 정상 응답과 실제 오류 객체를 구분해 적재하고, 빈 문자열은 결측값으로 표준화한다.
6. 한글이 깨져 보이는 도구가 있다면 파일 자체보다 표시 인코딩 문제일 가능성이 있으므로 UTF-8로 읽는다.
