# Knowledge Graph 구축 및 평가 보고서

## 1. 프로젝트 개요

본 프로젝트는 2026년 축제 데이터를 기반으로 축제·장소·프로그램·체험·숙박 등의 정보를 Knowledge Graph로 구축하고, 추출·검증·Entity Resolution·검색·질의응답 성능을 평가하는 것을 목적으로 한다.

평가 대상은 Triple 추출 및 자동 검증, Reject 원인 분석, Evidence Grounding, Entity Resolution, Neo4j 그래프 적재, Graph Analysis이다.

ER Golden Set의 정량적 정확도 평가는 별도 평가 데이터가 없어 실제 병합 처리 결과만 기록한다.

---

## 2. 핵심 평가 요약

| 평가 항목                 |     결과 | 근거                           |
| ------------------------- | -------: | ------------------------------ |
| 원천 문서 수              |    700건 | preprocessing_report.json      |
| 최종 문서 수              |    700건 | preprocessing_report.json      |
| 전체 추출 Triple          | 13,470건 | validation_summary_v2.json     |
| 검증 통과 Triple          | 13,302건 | validation_summary_v2.json     |
| Reject Triple             |    168건 | validation_summary_v2.json     |
| Ontology 준수율           |   98.75% | 13,302 / 13,470                |
| Reject 비율               |    1.25% | 168 / 13,470                   |
| Evidence 미확인 Reject    |     34건 | validation_summary_v2.json     |
| Relation Signature Reject |     63건 | validation_summary_v2.json     |
| 중복 Reject               |     71건 | validation_summary_v2.json     |
| Triple Precision          |   83.33% | 수동 평가 54건 중 45건 Correct |
| ER 병합 Entity 수         |     96건 | final/er_report.json           |
| 최종 Entity 수            | 12,804건 | final/er_report.json           |
| 최종 Node 수              | 24,185건 | load_report.json               |
| 최종 Relationship 수      | 51,937건 | load_report.json               |
| 적재 실패 배치            |      0건 | load_report.json               |
| Retrieval Smoke Test      | 5/5 성공 | retrieval_smoke_report.json    |

---

## 3. 전처리 결과

전처리 대상 문서는 700건이며, 중복 문서 ID·짧은 문서·본문 누락으로 제거된 문서는 없다.

| 항목           |     결과 |
| -------------- | -------: |
| 원천 문서 수   |      700 |
| 최종 문서 수   |      700 |
| 중복 문서 ID   |        0 |
| 짧은 문서 제거 |        0 |
| 본문 누락      |        0 |
| 전처리 Reject  |        0 |
| 최소 본문 길이 |    195자 |
| 최대 본문 길이 |  3,267자 |
| 평균 본문 길이 | 약 668자 |

Intro 데이터 누락은 없었으며, Info 데이터는 1건이 누락되었다.

---

## 4. Triple Validation 결과

Triple은 Schema, Entity Type, Relation, Relation Signature, Evidence의 원문 포함 여부, 중복 여부 순서로 자동 검증하였다.

| 구분        |   건수 |    비율 |
| ----------- | -----: | ------: |
| 전체 Triple | 13,470 | 100.00% |
| 검증 통과   | 13,302 |  98.75% |
| Reject      |    168 |   1.25% |

```text
Ontology 준수율 = 13,302 / 13,470 × 100 = 98.75%
```

### Reject 사유별 분포

| Reject 사유                      | 건수 | 전체 Triple 대비 | Reject 대비 |
| -------------------------------- | ---: | ---------------: | ----------: |
| 허용되지 않은 Relation Signature |   63 |            0.47% |      37.50% |
| Evidence 미확인                  |   34 |            0.25% |      20.24% |
| 중복 Triple                      |   71 |            0.53% |      42.26% |
| 합계                             |  168 |            1.25% |     100.00% |

Reject의 가장 큰 비중은 중복 Triple이며, 그 다음은 Relation Signature 오류다.

- 중복 Triple의 경우 동일한 사실관계가 여러 번 등장해서 생겼으므로 오류로 판단하지 않고 제거하였다.
- Evidence 미확인의 경우 원문의 표현을 LLM이 의역한 경우로 오류라고 판단하여 제거하였다.
- Relation Signature 오류의 경우 프로그램의 하위 프로그램과의 관계가 누락된 경우가 89%를 차지하여 온톨로지 개선이 필요하나, 짧은 기간 내에 개선하기 어렵다고 판단하여 제거하고 상위프로그램만을 표시하도록 하였다.

---

## 5. Triple Precision(샘플 정밀도) 평가

첨부된 수동 평가표 54건을 기준으로 Subject·Relation·Object·Evidence의 의미가 원문과 일치하는지 평가하였다.

| 평가 항목        | 건수 |    비율 |
| ---------------- | ---: | ------: |
| 수동 평가 Triple |   54 | 100.00% |
| Correct          |   45 |  83.33% |
| Incorrect        |    9 |  16.67% |

```text
Triple Precision
= Correct Triple 수 / 전체 수동 평가 Triple 수 × 100
= 45 / 54 × 100
= 83.33%
```

### 5.1 오류 유형별 분석

수동 평가표의 메모를 기준으로 Incorrect 사례를 분류하면 다음과 같다.

| 오류 유형                         | 건수 | 설명                                                                        |
| --------------------------------- | ---: | --------------------------------------------------------------------------- |
| Subject Entity 식별 오류          |    3 | 실제 축제명 대신 설명구·일반 지시어가 Subject로 추출됨                     |
| Entity Type 또는 대상 적절성 오류 |    3 | Audience·Organization·Program으로 보기 어려운 대상을 해당 Type으로 추출함 |
| Theme 의미 과추출                 |    2 | 캠페인·기획 배경 또는 가치 표현을 축제의 단일 Theme으로 추출함             |
| Object/Product 적절성 오류        |    1 | 상품이 아닌 공간·시설을 Product로 추출함                                   |
| 합계                              |    9 | 100%                                                                        |

### 5.2 대표 오류 사례

| 추출 Triple 요약                                                          | 판정      | 오류 내용                                                         |
| ------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------- |
| 여름 물놀이 문화축제 — HELD_IN — 낙동강                                 | Incorrect | 실제 축제명은 ‘안동 수(水)페스타’이나 설명구가 Subject로 추출됨 |
| 한산모시문화제 — TARGETS — 미래세대                                     | Incorrect | 계승 대상·목적일 수 있으나 실제 참가 대상이라고 단정하기 어려움  |
| 만석거 새빛축제 — HAS_THEME — 2026 수원 방문의 해                       | Incorrect | 축제 Theme이 아니라 연계 캠페인·기획 배경에 가까움               |
| 진주남강유등축제 — HAS_THEME — 사랑                                     | Incorrect | 여러 가치 중 하나로 단일 Theme으로 보기 어려움                    |
| 클리퍼 레이스 기항지 행사 — PROVIDES — 푸드 부스                        | Incorrect | Product가 아니라 음식 제공 공간·시설임                           |
| 올해 축제 — PROVIDES — 담양농특산물                                     | Incorrect | ‘올해 축제’라는 일반 지시어가 Subject로 추출됨                  |
| 성남동 지역 상인과 커피 업계 종사자들 — ORGANIZES — 성남동 커피페스티벌 | Incorrect | 특정 Organization Entity가 아닌 임의 집단임                       |
| A스팟 — TARGETS — 모든 관객                                             | Incorrect | 장소/구역명이며 Program이 아님                                    |

### 5.3 Precision 평가 해석

54건 표본에서 Triple Precision은 83.33%로 측정되었다. 오류는 Relation 자체보다 Entity 경계와 Entity Type 판정에서 주로 발생했다. 특히 설명구·일반 지시어가 축제명으로 추출되는 Subject 오류와, 장소·집단·캠페인·가치 표현을 Program·Organization·Theme·Product로 잘못 분류하는 문제가 확인되었다.

따라서 추출 Prompt에 다음 규칙을 강화할 필요가 있다.

- Subject는 원문에 명시된 실제 축제·행사명만 사용한다.
- ‘올해 축제’와 같은 지시어·설명구는 Entity로 생성하지 않는다.
- 장소·구역명과 Program을 구분한다.
- 임의 집단과 식별 가능한 Organization을 구분한다.
- 캠페인·기획 배경·가치 표현을 축제 Theme으로 과도하게 확장하지 않는다.
- Product는 실제 음식·상품명으로 제한하고 판매 공간은 제외한다.

---

## 6. Evidence Grounding 평가

Evidence가 원문에 존재하지 않아 Reject된 Triple은 34건이다.

| 항목                      |   건수 |
| ------------------------- | -----: |
| 전체 Triple               | 13,470 |
| Evidence 검증 실패        |     34 |
| Evidence 검증 통과 추정치 | 13,436 |

```text
Evidence 통과율 = (13,470 - 34) / 13,470 × 100 = 99.75%
```

별도 Grounding Rate 보고서가 없으므로 전체 추출 Triple 기준의 단순 참고값으로 해석한다.

---

## 7. Entity Resolution 결과

| 항목                  |   결과 |
| --------------------- | -----: |
| 병합 전 Entity 수     | 12,900 |
| 병합 후 Entity 수     | 12,804 |
| 최종 Entity 수 감소분 |     96 |
| 승인된 병합 후보 쌍   |    261 |
| 거부된 병합 후보 쌍   |    113 |
| 전체 의사결정 수      |    375 |

```text
Entity 감소율 = 96 / 12,900 × 100 = 0.74%
```

Golden Set 기반 정확도·재현율은 별도 결과가 없어 산출하지 않았다.

승인된 병합 후보 쌍 261건은 병합 대상으로 판단된 Entity 쌍의 개수이며, 최종 Entity 수 감소분 96건과 동일한 지표가 아니다. 여러 승인 후보 쌍이 하나의 Entity 그룹으로 연결될 수 있으므로, 후보 쌍의 개수와 병합 후 Entity 수 감소분 사이에 차이가 발생할 수 있다.

---

## 8. Neo4j 그래프 적재 결과

### 그래프 규모

| 항목            |   결과 |
| --------------- | -----: |
| Node 수         | 24,185 |
| Relationship 수 | 51,937 |
| 적재 실패 배치  |      0 |

### Node Type별 개수

| Node Type     |   개수 |
| ------------- | -----: |
| Experience    | 10,922 |
| Program       |  7,715 |
| Accommodation |  1,546 |
| Location      |  1,127 |
| Theme         |    759 |
| Festival      |    650 |
| Artist        |    602 |
| Product       |    374 |
| Audience      |    316 |
| Organization  |    109 |

### Relationship Type별 개수

| Relationship |   개수 |
| ------------ | -----: |
| NEARBY       | 41,126 |
| HAS_PROGRAM  |  8,789 |
| HELD_IN      |  1,498 |
| TARGETS      |    896 |
| HAS_THEME    |    815 |
| FEATURES     |    641 |
| PROVIDES     |    477 |
| ORGANIZES    |    126 |

### 인덱스

Full-text 10개, Vector 11개, Range 28개, Lookup 2개, Text 1개가 생성되었다. Festival, Program, Accommodation, Location 등에 Full-text와 Vector 인덱스가 모두 존재하며 Vector 차원은 1,536이다.

---

## 9. Graph Analysis

Neo4j GDS 기반 Graph Projection에서 PageRank와 Louvain Community Detection을 실행하였다.

### 9.1 분석 대상

| 항목                       |              결과 |
| -------------------------- | ----------------: |
| Projection Node 수         |            11,652 |
| Projection Relationship 수 |            13,242 |
| Community 수               |             5,208 |
| PageRank Top 결과          |              10건 |
| 알고리즘                   | PageRank, Louvain |
| Projection 삭제            |              완료 |

### 9.2 PageRank Top 10

| Rank | Entity        | Type     | PageRank Score |
| ---: | ------------- | -------- | -------------: |
|    1 | 어린이        | Audience |       3.077284 |
|    2 | 금남로        | Location |       2.540452 |
|    3 | 관람객        | Audience |       1.915029 |
|    4 | 남녀노소      | Audience |       1.640015 |
|    5 | 남문광장      | Location |       1.477762 |
|    6 | 헬기장        | Location |       1.429545 |
|    7 | 체험 프로그램 | Program  |       1.373970 |
|    8 | 내국인        | Audience |       1.271779 |
|    9 | 무창포광장    | Location |       1.253515 |
|   10 | 전시동        | Location |       1.212210 |

PageRank 상위에는 Audience와 Location Entity가 다수 포함되었다. 이는 여러 축제·프로그램과 연결되는 일반 대상 집단 및 장소가 그래프에서 높은 연결 중심성을 갖기 때문으로 해석할 수 있다. 단, 현재 PageRank 결과는 방향성 관계와 관계 가중치를 별도로 적용하지 않은 기본 분석 결과다.

### 9.3 Community Detection 결과

Louvain 분석 결과 5,208개의 Community가 확인되었다. 가장 큰 Community 5개는 다음과 같다.

| Community ID | Node 수 | 대표 Entity    | Type     |
| -----------: | ------: | -------------- | -------- |
|            7 |     349 | 헬기장         | Location |
|          980 |     324 | 체험 프로그램  | Program  |
|        10014 |     187 | 1층            | Location |
|          188 |     184 | 어린이         | Audience |
|        10523 |     104 | 국립중앙도서관 | Location |

Community는 projection에 포함된 Festival, Location, Audience, Program, Theme, Artist, Product, Organization Node와 관계를 기준으로 계산하였다. 대표 Entity는 각 Community에서 PageRank가 가장 높은 Node이다.

---

## 10. 검색 및 질의응답 필수 항목

커리큘럼 기준상 Vector Search와 Full-text Search를 5개 질문으로 비교하는 항목과 그래프 질의응답 데모는 필수이다. 다만 본 보고서에서는 30개 QA Golden 전체 정량 평가와 상세 문항별 비교표는 선택 평가로 제외하고, 필수 검색 비교와 데모 구현 여부만 기록한다.

### 10.1 검색 비교

Retrieval Smoke Test 기준으로 5개 검색 테스트를 실행했으며, 5건 모두 성공했다.

| 항목         |                            결과 |
| ------------ | ------------------------------: |
| 비교 질문 수 |                             5건 |
| 실행 성공    |                             5건 |
| 실행 실패    |                             0건 |
| 비교 대상    | Vector Search, Full-text Search |

### 10.2 질의응답

Streamlit 기반 그래프 질의응답 기능과 Text2Cypher 경로가 구현되어 있다. 질의응답 결과에는 그래프 조회 결과와 함께 Evidence 및 Source Document를 제공하는 구조를 사용한다.

---

## 11. 종합 평가

### 주요 강점

- 700개 문서가 모두 전처리되었고 전처리 Reject는 0건이다.
- Triple 자동 검증 통과율은 98.75%이다.
- Evidence 원문 포함 여부를 자동 검증하며, Evidence 단순 통과율은 99.75%이다.
- Triple Sample Precision은 54건 중 45건 정답으로 83.33%이다.
- Entity Resolution을 통해 12,900개 Entity를 12,804개로 정규화했다.
- 24,185개 Node와 51,937개 Relationship을 적재했고 적재 실패 배치는 0건이다.
- Full-text 및 Vector 검색 인덱스가 구성되어 있다.
- PageRank Top 10과 Louvain Community Detection 결과를 저장했다.
- 필수 검색 비교 5건을 모두 실행했고, 그래프 질의응답 데모 구조를 구현했다.

### 주요 한계

- ER Golden Set 기반 재현율·오병합 정량 평가는 선택 항목으로 별도 산출하지 않았다.
- 30개 QA Golden 전체 지표와 문항별 답변 비교는 본 필수 평가에서 제외했다.
- 그래프 원본과 적재 보고서의 Relationship 수가 서로 다르므로 산출 기준을 명확히 해야 한다.

### 개선 방향

1. Triple Sample Precision을 확대 평가하여 표본의 대표성을 높인다.
2. 선택 항목인 ER Golden Set을 수행할 경우 재현율과 오병합을 별도로 측정한다.
3. PageRank와 Community Detection 결과를 정기적으로 갱신한다.
4. 그래프 적재 전후 Node·Relationship 집계 기준을 통일한다.
5. 허용 Relation Signature와 Evidence 보존 규칙을 Prompt에 명시한다.
6. Entity 및 Relation 정규화를 강화하여 중복 Triple을 줄인다.

---

## 12. 최종 결론

현재 저장된 결과를 기준으로 Knowledge Graph 파이프라인은 전처리, Triple 검증, Entity Resolution, Neo4j 적재, 검색 인덱스 생성, Graph Analysis까지 정상적으로 동작했다.

Triple 검증 통과율은 98.75%, 전처리 Reject는 0건, Neo4j 적재 실패 배치는 0건, Retrieval Smoke Test는 5/5 성공이다.

Triple Sample Precision은 54건 표본에서 83.33%로 확인되었고, Evidence·Ontology·ER·Neo4j 적재 품질을 정량적으로 확인했다. PageRank Top 10과 Louvain Community Detection도 실행 및 저장을 완료했다. 필수 검색 비교는 5건 모두 실행 성공했으며 그래프 질의응답 데모 구조도 구현했다. 30개 QA Golden 전체 정량 평가와 ER Golden Set 평가는 실시하지
