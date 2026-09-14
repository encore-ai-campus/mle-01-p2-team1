"""Festival JSON 로딩과 contentid 기반 lookup 생성을 담당한다.

이 모듈은 입력 구조만 준비하며 텍스트 정제나 Document 생성은 수행하지 않는다.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from config import FESTIVAL_INFO_PATH, FESTIVAL_INTRO_PATH, FESTIVAL_RAW_PATH


FESTIVAL_FIELDS = (
    "contentid",
    "title",
    "eventstartdate",
    "eventenddate",
    "addr1",
    "mapx",
    "mapy",
    "homepage",
    "modifiedtime",
    "overview",
)

DESCRIPTION_INFO_NAMES = frozenset({"행사소개", "행사내용", "출연"})


def _normalize_content_id(value: Any) -> str:
    """누락된 식별자는 빈 문자열로, 나머지는 문자열로 통일한다."""

    return "" if value is None else str(value)


@dataclass
class LoadDiagnostics:
    """중단하지 않고 건너뛴 입력과 중복 식별자를 모은다."""

    festival_missing_rows: list[dict[str, Any]] = field(default_factory=list)
    festival_duplicate_ids: list[str] = field(default_factory=list)
    intro_duplicate_ids: list[str] = field(default_factory=list)
    intro_skipped_rows: list[dict[str, Any]] = field(default_factory=list)
    info_skipped_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class FestivalSources:
    """후속 전처리 단계에 전달하는 이름 있는 입력 묶음이다."""

    festival_rows: list[dict[str, Any]]
    intro_lookup: dict[str, dict[str, Any]]
    info_lookup: dict[str, list[dict[str, Any]]]
    diagnostics: LoadDiagnostics


def load_json(path: str | Path) -> list[Any] | dict[str, Any]:
    """UTF-8 JSON 파일을 읽어 원래 자료 구조 그대로 반환한다."""

    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_festival(row: dict[str, Any]) -> dict[str, Any]:
    """후속 단계가 사용하는 축제 필드를 빠짐없이 갖춘 새 dict를 만든다."""

    normalized = {field: row.get(field, "") for field in FESTIVAL_FIELDS}
    normalized["contentid"] = _normalize_content_id(normalized["contentid"])
    return normalized


def build_lookup(
    rows: Iterable[dict[str, Any]],
    key: str = "contentid",
    *,
    multiple: bool = False,
    missing_rows: list[dict[str, Any]] | None = None,
    duplicate_ids: list[str] | None = None,
) -> dict[str, Any]:
    """식별자 lookup을 만들고 누락 row와 중복 ID를 선택적으로 기록한다.

    ``multiple=False``이면 먼저 나온 레코드를 보존하고, ``multiple=True``이면
    같은 ID의 모든 레코드를 입력 순서대로 그룹화한다.
    """

    lookup: dict[str, Any]
    lookup = defaultdict(list) if multiple else {}
    seen_ids: set[str] = set()

    for row_index, row in enumerate(rows):
        raw_id = row.get(key, "")
        content_id = _normalize_content_id(raw_id)
        if not content_id.strip():
            if missing_rows is not None:
                missing_rows.append({"row_index": row_index, "row": row})
            continue

        if content_id in seen_ids and duplicate_ids is not None:
            if content_id not in duplicate_ids:
                duplicate_ids.append(content_id)

        if multiple:
            lookup[content_id].append(row)
        elif content_id not in lookup:
            lookup[content_id] = row

        seen_ids.add(content_id)

    return lookup


def build_intro_lookup(
    intro_rows: Iterable[dict[str, Any]],
    *,
    skipped_rows: list[dict[str, Any]] | None = None,
    duplicate_ids: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """intro API wrapper를 해제하여 contentid별 첫 상세 dict를 반환한다."""

    lookup: dict[str, dict[str, Any]] = {}
    for row_index, row in enumerate(intro_rows):
        content_id = _normalize_content_id(row.get("contentid", ""))
        error = row.get("error")
        details = row.get("intro", [])

        if error:
            if skipped_rows is not None:
                skipped_rows.append(
                    {
                        "row_index": row_index,
                        "contentid": content_id,
                        "reason": "api_error",
                        "error": error,
                    }
                )
            continue

        if not details:
            if skipped_rows is not None:
                skipped_rows.append(
                    {
                        "row_index": row_index,
                        "contentid": content_id,
                        "reason": "empty_intro",
                    }
                )
            continue

        if content_id in lookup:
            if duplicate_ids is not None and content_id not in duplicate_ids:
                duplicate_ids.append(content_id)
            continue

        lookup[content_id] = details[0]

    return lookup


def build_info_lookup(
    info_rows: Iterable[dict[str, Any]],
    *,
    skipped_rows: list[dict[str, Any]] | None = None,
) -> defaultdict[str, list[dict[str, Any]]]:
    """info API wrapper를 해제하여 상세 dict를 contentid별로 그룹화한다."""

    lookup: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row_index, row in enumerate(info_rows):
        wrapper_id = _normalize_content_id(row.get("contentid", ""))
        error = row.get("error")
        details = row.get("info", [])

        if error:
            if skipped_rows is not None:
                skipped_rows.append(
                    {
                        "row_index": row_index,
                        "contentid": wrapper_id,
                        "reason": "api_error",
                        "error": error,
                    }
                )
            continue

        if not details:
            if skipped_rows is not None:
                skipped_rows.append(
                    {
                        "row_index": row_index,
                        "contentid": wrapper_id,
                        "reason": "empty_info",
                    }
                )
            continue

        for detail in details:
            content_id = _normalize_content_id(detail.get("contentid", ""))
            if not content_id.strip():
                if skipped_rows is not None:
                    skipped_rows.append(
                        {
                            "row_index": row_index,
                            "contentid": wrapper_id,
                            "reason": "missing_detail_contentid",
                        }
                    )
                continue
            lookup[content_id].append(detail)

    return lookup


def select_info_texts(
    info_items: Iterable[dict[str, Any]],
) -> list[str]:
    """설명형 info 항목의 비어 있지 않은 infotext만 입력 순서대로 고른다."""

    texts: list[str] = []
    for item in info_items:
        if item.get("infoname") not in DESCRIPTION_INFO_NAMES:
            continue
        text = item.get("infotext")
        if isinstance(text, str) and text.strip():
            texts.append(text)
    return texts


def _validate_row_list(
    value: Any,
    path: Path,
    *,
    wrapper_field: str | None = None,
) -> list[dict[str, Any]]:
    """JSON 최상위 배열과 row/wrapper 자료형을 검증한다."""

    if not isinstance(value, list):
        raise TypeError(
            f"{path}: top-level JSON value must be list, "
            f"got {type(value).__name__}"
        )

    for row_index, row in enumerate(value):
        if not isinstance(row, dict):
            raise TypeError(
                f"{path}: row {row_index} must be dict, "
                f"got {type(row).__name__}"
            )

        if wrapper_field is None:
            continue

        for required_field in ("contentid", wrapper_field):
            if required_field not in row:
                raise ValueError(
                    f"{path}: row {row_index} is missing required field "
                    f"'{required_field}'"
                )

        if not _normalize_content_id(row["contentid"]).strip():
            raise ValueError(
                f"{path}: row {row_index} has an empty required field 'contentid'"
            )

        details = row[wrapper_field]
        if not isinstance(details, list):
            raise TypeError(
                f"{path}: row {row_index} field '{wrapper_field}' must be list, "
                f"got {type(details).__name__}"
            )

        for detail_index, detail in enumerate(details):
            if not isinstance(detail, dict):
                raise TypeError(
                    f"{path}: row {row_index} {wrapper_field}[{detail_index}] "
                    f"must be dict, got {type(detail).__name__}"
                )

    return value


def _source_paths(base_dir: str | Path | None) -> tuple[Path, Path, Path]:
    if base_dir is None:
        return (
            Path(FESTIVAL_RAW_PATH),
            Path(FESTIVAL_INTRO_PATH),
            Path(FESTIVAL_INFO_PATH),
        )

    base_path = Path(base_dir)
    data_dir = base_path if base_path.name == "data" else base_path / "data"
    return (
        data_dir / "raw" / Path(FESTIVAL_RAW_PATH).name,
        data_dir / "extra" / Path(FESTIVAL_INTRO_PATH).name,
        data_dir / "extra" / Path(FESTIVAL_INFO_PATH).name,
    )


def load_festival_sources(base_dir: str | Path | None = None) -> FestivalSources:
    """세 원본 JSON을 검증하고 정규화된 후속 처리 입력을 반환한다.

    ``base_dir``를 생략하면 ``config.py``의 경로를 그대로 사용한다. 값을
    전달할 때는 프로젝트 루트 또는 ``data`` 디렉터리를 지정할 수 있다.
    """

    festival_path, intro_path, info_path = _source_paths(base_dir)

    festival_source = _validate_row_list(load_json(festival_path), festival_path)
    intro_source = _validate_row_list(
        load_json(intro_path), intro_path, wrapper_field="intro"
    )
    info_source = _validate_row_list(
        load_json(info_path), info_path, wrapper_field="info"
    )

    diagnostics = LoadDiagnostics()
    build_lookup(
        festival_source,
        missing_rows=diagnostics.festival_missing_rows,
        duplicate_ids=diagnostics.festival_duplicate_ids,
    )

    festival_rows = [normalize_festival(row) for row in festival_source]
    intro_lookup = build_intro_lookup(
        intro_source,
        skipped_rows=diagnostics.intro_skipped_rows,
        duplicate_ids=diagnostics.intro_duplicate_ids,
    )
    info_lookup = build_info_lookup(
        info_source,
        skipped_rows=diagnostics.info_skipped_rows,
    )

    return FestivalSources(
        festival_rows=festival_rows,
        intro_lookup=intro_lookup,
        info_lookup=dict(info_lookup),
        diagnostics=diagnostics,
    )
