# 데이터 수집 명세서

## 1. 문서 목적

본 문서는 축제 Knowledge Graph 구축에 사용한 원천 데이터의 출처, 수집 방법, 주요 필드, 결측 현황, 라이선스 관련 확인사항을 정리한다. 수집 시점과 저장된 파일을 기준으로 작성했으며, 원천 API가 제공하지 않는 정보는 임의로 보완하지 않는다.

## 2. 데이터 수집 범위

| 데이터 구분            | 원천 파일                               |       수집 건수 | 활용 목적                                 |
| ---------------------- | --------------------------------------- | --------------: | ----------------------------------------- |
| 축제 기본·목록 데이터 | `data/raw/festival_raw.json`          |             700 | Festival 노드와 기본 메타데이터 생성      |
| 축제 소개 상세         | `data/raw/festival_intro_2026.json`   |             700 | 축제 설명·본문 전처리                    |
| 축제 상세 부가정보     | `data/raw/festival_info_2026.json`    |             700 | 프로그램·장소·대상·테마 관련 본문 생성 |
| 주변 체험관광          | `data/extra/experience_raw.json`      |           1,835 | Experience 노드 및 축제 주변 정보         |
| 주변 숙박              | `data/extra/stays_all.json`           |           3,004 | Accommodation 노드 및 주변 정보           |
| 축제 주변 5km 관광정보 | `data/extra/festival_nearby_5km.json` | 700개 축제 기준 | `NEARBY` 관계와 거리 정보 생성          |

## 3. 수집 출처 및 방법

### 3.1 축제 데이터

- 출처: 한국관광공사 관광정보 API(`data.go.kr`, TourAPI 계열)
- 목록 API: `searchFestival2`
- 상세 API: `detailCommon2`
- 수집 기간 조건: 2026-01-01 ~ 2026-12-31
- 요청 방식: JSON 응답, 페이지 단위 수집 후 `contentid`별 상세 조회
- 저장 방식: 목록 응답과 상세 응답을 병합하여 JSON 배열로 저장
- 관련 코드: `src/collection/collect_festival.py`

### 3.2 체험관광 데이터

- 출처: 한국관광공사 관광정보 API(`data.go.kr`, TourAPI 계열)
- 목록 API: `areaBasedList2`
- 필터: `lclsSystm1=EX`
- 상세 API: `detailCommon2`
- 수집 방식: 목록을 수집한 후 `overview`가 없는 항목을 중심으로 상세정보를 보완
- 저장 파일: `data/extra/experience_raw.json`
- 관련 코드: `src/collection/collect_experience.py`

### 3.3 숙박 및 주변 관광정보

- 출처: 한국관광공사 관광정보 API 기반 추가 수집 코드
- 숙박 데이터: `stays_all.json`
- 주변 체험 데이터: `experience_raw.json`
- 축제별 주변 데이터: `festival_nearby_5km.json`
- 전처리 결과: `data/processed/01_preprocessing/extra_accommodations.jsonl`, `extra_experiences.jsonl`, `extra_nearby.jsonl`
- 관련 코드: `src/collection/extra_api.py`, `src/preprocessing/extra_preprocessing.py`

## 4. 주요 필드 명세

### 4.1 공통 식별·명칭 필드

| 필드              | 설명                        | 사용 방식                                     |
| ----------------- | --------------------------- | --------------------------------------------- |
| `contentid`     | 관광정보 원천 콘텐츠 식별자 | 원천 객체 식별 및 연결 키                     |
| `title`         | 원천 콘텐츠명               | Festival, Experience, Accommodation 명칭 후보 |
| `contenttypeid` | 관광정보 콘텐츠 유형 코드   | 데이터 유형 구분                              |
| `createdtime`   | 원천 등록 시각              | 메타데이터                                    |
| `modifiedtime`  | 원천 수정 시각              | 최신성 확인용 메타데이터                      |
| `source_doc_id` | 전처리 문서 식별자          | 추출 트리플과 근거 문서 연결                  |

### 4.2 위치·연락처 필드

| 필드                          | 설명                          |
| ----------------------------- | ----------------------------- |
| `addr1`, `addr2`          | 주소                          |
| `areacode`, `sigungucode` | 지역 및 시군구 코드           |
| `mapx`, `mapy`            | 좌표                          |
| `mlevel`                    | 좌표 관련 지도 레벨           |
| `zipcode`                   | 우편번호                      |
| `tel`                       | 전화번호                      |
| `radius_meter`              | 주변 검색 반경 또는 거리 정보 |

### 4.3 축제 일정·본문·이미지 필드

| 필드                                 | 설명                             |
| ------------------------------------ | -------------------------------- |
| `eventstartdate`, `eventenddate` | 축제 시작일·종료일              |
| `intro`                            | 축제 소개 응답                   |
| `info`                             | 축제 상세정보 응답               |
| `overview`                         | 관광정보 개요·설명              |
| `firstimage`, `firstimage2`      | 대표 이미지 URL                  |
| `cat1`, `cat2`, `cat3`         | 관광 분류 코드                   |
| `festival_title`                   | 주변 데이터에서 참조하는 축제명  |
| `festival_contentid`               | 주변 데이터에서 참조하는 축제 ID |
| `nearby`                           | 축제 주변 관광정보 목록          |

## 5. 전처리 및 품질 규칙

1. `contentid` 또는 문서 식별자를 기준으로 원천 문서를 구분한다.
2. 본문에 사용할 문자열 필드만 결합하고, 중첩 객체·배열은 문서 본문에 무분별하게 포함하지 않는다.
3. 축제 문서는 소개·상세정보를 결합하여 `festivals_documents.jsonl`로 저장한다.
4. 주변 숙박·체험·관광 데이터는 별도 JSONL로 정규화한 뒤 그래프에 추가한다.
5. 필수 식별자와 본문이 없거나 형식이 잘못된 데이터는 reject 로그에 기록한다.
6. 중복 문서 ID, 짧은 본문, 누락 본문 여부를 전처리 리포트로 집계한다.

## 6. 결측 현황

전처리 리포트(`data/processed/05_reports/preprocessing_report.json`) 기준 축제 문서 700건에 대해 다음과 같이 확인되었다.

| 항목                 | 건수 |
| -------------------- | ---: |
| 원천 문서 수         |  700 |
| 최종 문서 수         |  700 |
| 중복 문서 ID         |    0 |
| 짧은 본문 제거       |    0 |
| 기타 제거            |    0 |
| 전처리 reject        |    0 |
| 소개 데이터 누락     |    0 |
| 상세정보 데이터 누락 |    1 |

상세정보 1건의 누락은 전처리 실패로 간주하지 않고, 해당 문서에 존재하는 다른 본문과 메타데이터를 사용해 처리했다. 주변 숙박·체험 데이터의 개별 필드 결측은 원천 API 응답을 보존하며, 전처리 단계에서 필드별 기본값 또는 빈 값으로 정규화한다.

## 7. 출처·라이선스

- 원천 데이터는 한국관광공사 관광정보 API를 통해 수집했다.
- 원천 응답의 `cpyrhtDivCd` 필드를 보존하여 저작권 관련 원천 메타데이터를 확인할 수 있도록 했다.
- 해당 API는 공공데이터포털 기준 무료로 제공되며 이용허락범위는 ‘제한 없음’으로 명시되어 있다. 단, API에서 제공되는 이미지 자료는 개별 공공누리 유형 및 별도 이용조건이 적용될 수 있으므로 본 프로젝트에서는 텍스트 기반 관광정보를 중심으로 활용하였다.

## 8. 저장 경로 및 후속 산출물

```text
data/raw/                         원천 축제 응답
data/extra/                       추가 숙박·체험·주변 응답
data/processed/01_preprocessing/  정규화된 문서·추가 데이터
data/processed/02_extraction/    LLM 추출 트리플
data/processed/03_er/             Entity Resolution 결과
data/processed/04_graph/          Neo4j 적재용 노드·관계
data/processed/05_reports/        전처리·검증·적재 품질 리포트
```
