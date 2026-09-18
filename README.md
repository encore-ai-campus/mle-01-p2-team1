# Festival Knowledge Graph

2026년 축제·프로그램·장소·체험·숙박 데이터를 기반으로 Knowledge Graph를 구축하는 프로젝트입니다. 한국관광공사 관광정보 API에서 수집한 데이터를 전처리하고, LLM으로 Entity와 Relation을 추출한 뒤 온톨로지 검증, Entity Resolution, Neo4j 적재와 그래프 분석까지 수행합니다.

## 프로젝트 목표

- 축제 원천 데이터를 문서 형태로 정규화
- LLM 기반 Entity·Relation 자동 추출
- 온톨로지와 Evidence 기반 품질 검증
- 중복 Entity를 정규화하여 Neo4j Knowledge Graph 구축
- Full-text·Vector 검색 인덱스 구성
- PageRank와 Louvain Community Detection으로 그래프 구조 분석

## 전체 파이프라인

```text
한국관광공사 API → 데이터 수집 → 문서 전처리 → LLM 추출
→ Ontology·Evidence 검증 → Entity Resolution
→ Neo4j 변환·적재 → 검색 인덱스 → Graph Analysis
```

## 데이터

주요 원천 데이터는 한국관광공사 관광정보 API에서 수집했습니다.

| 데이터 | 건수 | 주요 용도 |
|---|---:|---|
| 축제 기본 데이터 | 700 | Festival 노드 생성 |
| 축제 소개·상세 데이터 | 각 700 | 문서 본문과 Evidence 구성 |
| 체험관광 데이터 | 1,835 | Experience 노드 및 주변 정보 |
| 숙박 데이터 | 3,004 | Accommodation 노드 및 주변 정보 |
| 축제별 주변 관광 데이터 | 700개 축제 기준 | `NEARBY` 관계 생성 |

상세한 출처, API, 필드, 결측, 라이선스 확인사항은 [데이터 수집 명세서](docs/data_collection_spec.md)를 참고하세요.

## Knowledge Graph 스키마

### Entity Type

```text
Festival, Location, Organization, Program, Theme,
Audience, Artist, Product, Accommodation, Experience
```

### 주요 Relation

| Subject | Relation | Object | 의미 |
|---|---|---|---|
| Festival | `HELD_IN` | Location | 축제가 특정 장소에서 개최됨 |
| Festival | `TARGETS` | Audience | 축제가 특정 대상을 대상으로 함 |
| Festival | `HAS_PROGRAM` | Program | 축제가 프로그램을 포함함 |
| Festival | `HAS_THEME` | Theme | 축제가 특정 주제와 관련됨 |
| Festival | `FEATURES` | Artist | 축제에 아티스트가 참여함 |
| Festival | `PROVIDES` | Product | 축제가 상품을 제공함 |
| Organization | `ORGANIZES` | Festival | 기관이 축제를 주최함 |
| Program | `HELD_IN` | Location | 프로그램이 특정 장소에서 진행됨 |
| Program | `TARGETS` | Audience | 프로그램이 특정 대상을 대상으로 함 |
| Festival | `NEARBY` | Accommodation / Experience | 축제 주변 숙박·체험 정보 |

온톨로지 원본은 [`src/extraction/ontology.py`](src/extraction/ontology.py)에 있습니다.

## 핵심 구현

### LLM 추출

- 구조화 출력 스키마: `src/extraction/schemas.py`
- 추출 프롬프트: `src/extraction/prompts.py`
- 문서·배치 추출: `src/extraction/extract.py`
- 재시도 및 raw 응답 보존 지원

### 품질 검증

- 허용 Entity Type 및 Relation Signature 검증
- Evidence가 원문에 실제 존재하는지 검증
- 중복 Triple 검출
- 잘못된 타입 조합과 관계 방향 검출

### Entity Resolution

- Entity Type과 canonical name 기반 후보 생성
- 문자열·문맥·임베딩 기반 후보 검토
- 승인된 병합 후보를 반영해 중복 Entity 정규화
- 병합 전후 Entity 수와 승인·거부 후보를 리포트로 저장

### Neo4j

- Entity Type별 노드 생성
- Ontology 방향에 맞는 관계 생성
- 관계에 `source_doc_id`, `evidence`, 거리 등 근거 속성 보존
- `MERGE` 기반 재실행 시 중복 방지

### 검색 인덱스

- Entity Type별 Full-text Index
- Entity Type별 Vector Index
- `text-embedding-3-small`, 1,536차원, cosine similarity
- `Accommodation`과 `Experience` 검색용 Vector Index 포함

## 주요 결과

| 평가 항목 | 결과 |
|---|---:|
| 최종 전처리 문서 | 700건 |
| 전처리 Reject | 0건 |
| 추출 Triple | 13,470건 |
| 검증 통과 Triple | 13,302건 |
| Ontology 준수율 | 98.75% |
| Evidence 자동 검증 통과 추정치 | 99.75% |
| Triple Sample Precision | 83.33% (45/54) |
| Entity Resolution 전 Entity | 12,900개 |
| Entity Resolution 후 Entity | 12,804개 |
| 최종 Neo4j Node | 24,185건 처리 |
| 최종 Neo4j Relationship | 51,937건 |
| 적재 실패 배치 | 0건 |
| PageRank Top 결과 | 10건 |
| Louvain Community | 5,208개 |

Triple Precision은 수동 검토 샘플 기준이며 전체 Triple의 전수 정밀도가 아닙니다. ER Golden Set 기반 재현율·오병합 정량 평가는 별도 선택 평가 항목으로 관리했습니다.

## 프로젝트 구조

```text
src/
├─ collection/          API 데이터 수집
├─ preprocessing/       문서 생성·정규화
├─ extraction/          LLM 추출·온톨로지·검증
├─ entity_resolution/   Entity 후보 생성·병합
├─ graph/               Neo4j 변환·적재·검증·인덱스·분석
├─ rag/                 검색·Text2Cypher·답변 생성
└─ ui/                  UI 모듈

data/
├─ raw/                 원천 축제 데이터
├─ extra/               숙박·체험·주변 데이터
└─ processed/
   ├─ 01_preprocessing/
   ├─ 02_extraction/
   ├─ 03_er/
   ├─ 04_graph/
   └─ 05_reports/

docs/
├─ data_collection_spec.md
├─ report.md
└─ JSON_METADATA_REPORT.md
```

## 실행 환경

- Python 3.12 이상
- `uv` 권장
- Neo4j 또는 Neo4j Aura
- LLM 추출·임베딩 사용 시 OpenAI API Key

### 의존성 설치

```bash
uv sync
```

### 환경변수

로컬 실행 시 `.env`에 다음 값을 설정합니다. `.env`는 Git에 커밋하지 않습니다.

```env
TOUR_API_SERVICE_KEY=...
OPENAI_API_KEY=...
NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

Aura 적재용 스크립트에서는 다음 별칭도 사용할 수 있습니다.

```env
AURA_URI=...
AURA_USER=neo4j
AURA_PASSWORD=...
```

## 주요 실행 예시

### Vector Index 및 임베딩

```bash
python scripts/build_vector_indexes.py
```

### 테스트

```bash
uv run pytest
```

## 산출물

- [종합 평가 리포트](docs/report.md)
- [데이터 수집 명세서](docs/data_collection_spec.md)
- [JSON 메타데이터 리포트](docs/JSON_METADATA_REPORT.md)
- [전처리 리포트](data/processed/05_reports/preprocessing_report.json)
- [Triple 검증 리포트](data/processed/05_reports/validation_summary_v2.json)
- [Neo4j 적재 리포트](data/processed/05_reports/load_report.json)
- [Aura 적재 리포트](data/processed/05_reports/aura_load_report.json)
- [검색 인덱스 리포트](data/processed/05_reports/index_report.json)
- [Graph Analysis 리포트](data/processed/05_reports/graph_analysis_report.json)

## 참고

원천 데이터의 공개·재배포 시에는 한국관광공사 및 공공데이터 제공 조건과 API 이용약관을 확인해야 합니다. 원천 응답의 `cpyrhtDivCd` 필드는 데이터에 보존되어 있습니다.
