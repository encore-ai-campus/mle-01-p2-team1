# Streamlit Festival UI Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a merge-friendly Streamlit scaffold split across four owners, with explicit TODO comments and stable interfaces.

**Architecture:** `app.py` owns navigation only. `data_loader.py` owns local JSON/JSONL loading and normalization. Page modules own rendering and call shared helpers. External Neo4j/LLM integration remains optional and is isolated behind TODO hooks.

**Tech Stack:** Python 3.12, Streamlit, pandas, Plotly optional, JSON/JSONL.

**Spec:** Design approved in chat on 2026-09-18.

## Global Constraints

- Keep page modules independently editable by four contributors.
- Use relative paths from the repository root, not machine-specific absolute paths.
- Do not require Neo4j or an API key for the local scaffold to start.
- Preserve the existing GraphRAG QA behavior in a separate legacy entry point until integration is completed.

### Task 1: Shared data layer

**Files:** Create `src/ui/data_loader.py`, `src/ui/components.py`.

- [ ] Add typed records, safe JSON/JSONL loading, and normalized festival/triple accessors.
- [ ] Add reusable card, metric, and empty-state rendering helpers.
- [ ] 스키마별 매핑 확인이 필요한 곳에 할 일 주석을 남깁니다.

### Task 2: Main and recommendation owner

**Files:** Create `src/ui/main_page.py`.

- [ ] Implement home metrics/search shell and recommendation filters.
- [ ] Return selected festival IDs through Streamlit session state for later detail navigation.
- [ ] 검색 순위 고도화를 위한 할 일 지점을 남깁니다.

### Task 3: Map and detail owner

**Files:** Create `src/ui/map_page.py`.

- [ ] Implement region/month filters, map dataframe, up to three festival previews, and detail view.
- [ ] Use coordinates when available and show a table fallback otherwise.
- [ ] 주변 관광지와 목록 넘기기 기능을 위한 할 일 지점을 남깁니다.

### Task 4: Chat and graph owner

**Files:** Create `src/ui/chat_graph_page.py`.

- [ ] Implement local keyword chatbot fallback with links and evidence excerpts.
- [ ] Implement graph filtering and a relationship count slider from 5 to 200.
- [ ] 운영용 RAG와 그래프 시각화를 위한 할 일 지점을 남깁니다.

### Task 5: Integration entry point

**Files:** Replace `src/ui/app.py` with the new navigation entry point; preserve old QA code in `src/ui/legacy_qa.py`.

- [ ] Add page selector and shared data loading.
- [ ] Make imports work with `streamlit run src/ui/app.py`.
- [ ] Run compile checks and a local data-loading smoke test.
