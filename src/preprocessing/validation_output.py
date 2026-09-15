"""담당 5. Document 검증·분리·저장·통계 가이드

이 파일은 최종 단계의 책임을 모은다. 검증 함수, reject log 생성,
JSONL 저장, 결과 통계를 구현한다. 원본 텍스트를 다시 정제하지 않는다.
"""
import json
from pathlib import Path

from config import (
    PROCESSED_DOCUMENTS_PATH,
    REJECT_LOG_PATH,
    PREPROCESSING_REPORT_PATH,
)

MIN_TEXT_LENGTH = 50

# TODO 1. validate_document(document) -> list[str]를 구현한다.
#
# required = ["doc_id", "title", "text", "metadata"]를 for field in required로
# 순회한다. document.get(field)가 비어 있으면 missing_<field>를 errors에 추가한다.
# text 길이가 MIN_TEXT_LENGTH보다 짧으면 short_text를 추가한다.
# metadata의 event_start/event_end 형식과 좌표 숫자 여부도 별도 오류 코드로 기록한다.
# 오류가 없으면 빈 list를 반환한다. bool 하나가 아니라 여러 오류를 반환해야
# reject 원인을 한 번에 확인할 수 있다.

# TODO 6. MIN_TEXT_LENGTH, 날짜 형식, 좌표 범위 등 검증 기준을 정의한다.
#
# MIN_TEXT_LENGTH는 config.py 또는 이 파일의 상수로 한 곳에서 관리한다.
# event_start와 event_end는 값이 있을 때 숫자 8자리 YYYYMMDD인지 확인한다.
# longitude는 -180 이상 180 이하, latitude는 -90 이상 90 이하인지 확인한다.
# 각 규칙을 위반하면 하나의 오류만 반환하지 말고 오류 목록에 모두 추가한다.

def validate_document(document) -> list[str]:
    errors = []
    required = ["doc_id", "title", "text", "metadata"]

    for field in required: # 필수 필드 검사
        if not document.get(field):
            errors.append(f"missing_{field}")

    text = document.get("text") or "" # text 길이 검사

    if not str(text).strip():
        errors.append("short_text")
    elif len(text) < MIN_TEXT_LENGTH:
        errors.append("short_text")

    metadata = document.get("metadata", {})

    if isinstance(metadata, dict):
        for field in ["event_start", "event_end"]: # 날짜 형식: YYYYMMDD 숫자 8자리
            value = metadata.get(field)

            if value:
                value = str(value)

                if not (len(value) == 8 and value.isdigit()):
                    errors.append(f"invalid_{field}")

        longitude = metadata.get("longitude") # longitude 범위 검사

        if longitude is not None:
            try:
                longitude = float(longitude)

                if not -180 <= longitude <= 180:
                    errors.append("invalid_longitude")

            except (ValueError, TypeError):
                errors.append("invalid_longitude")

        latitude = metadata.get("latitude") # latitude 범위 검사

        if latitude is not None:
            try:
                latitude = float(latitude)

                if not -90 <= latitude <= 90:
                    errors.append("invalid_latitude")

            except (ValueError, TypeError):
                errors.append("invalid_latitude")

    return errors



# TODO 2. make_reject_log(document, errors) -> dict를 구현한다.
#
# doc_id, title, reject_reason, text_length를 포함한다.
# reject_reason은 errors를 list로 보존하거나 ","로 join한다.
# 원문 전체 text를 reject log에 복사하지 않아 로그가 불필요하게 커지지 않게 한다.

def make_reject_log(document, errors) -> dict:
    return {
        "doc_id": document.get("doc_id"),
        "title": document.get("title"),
        "reject_reason": errors,
        "text_length": len(document.get("text") or ""),
    }

# TODO 3. save_jsonl(path, rows)와 save_json(path, value)를 구현한다.
#
# Path(path).parent.mkdir(parents=True, exist_ok=True)로 디렉터리를 만든다.
# open(path, "w", encoding="utf-8")을 사용한다.
# JSONL은 for row in rows 반복문에서 json.dumps(row, ensure_ascii=False) 뒤
# 개행을 붙여 한 줄씩 저장한다. 저장 후 다시 읽어 json.loads()가 되는지 확인한다.

# TODO 7. 재실행 시 출력 파일을 overwrite하는 정책을 정의한다.
#
# save_jsonl은 파일을 "w" 모드로 열어 이전 실행 결과를 먼저 지운다.
# 저장 전 부모 디렉터리가 없으면 mkdir(parents=True, exist_ok=True)로 만든다.
# 그래야 같은 명령을 여러 번 실행해도 문서가 중복으로 쌓이지 않는다.

def save_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f: # "w" 모드이므로 재실행 시 기존 결과를 덮어씀
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with open(path, "r", encoding="utf-8") as f: # 저장 후 JSONL 파싱 확인
        for line in f:
            if line.strip():
                json.loads(line)

def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            value,
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(path, "r", encoding="utf-8") as f: # 저장 후 다시 읽어서 JSON 파싱 확인
        json.load(f)

# TODO 4. build_preprocessing_report(processed, rejects, source_count)를 구현한다.
#
# success_count, reject_count, missing_text_count, short_text_count,
# duplicate_doc_id_count를 계산한다.
# text_lengths = [len(doc["text"]) for doc in processed]로 길이를 모으고
# 최소·최대·평균을 계산한다. 0건일 때 min/max에서 예외가 나지 않게 처리한다.

# TODO 9. 제거 사유별 전처리 통계를 report에 기록한다.
#
# 단순히 reject_count 하나만 세지 말고, 왜 문서가 최종 결과에서 제외되었는지
# 사유별로 나누어 집계한다.
#
# report에는 최소한 다음 항목을 포함한다.
# - source_count: 전처리 대상이었던 원본 문서 수
# - duplicate_removed_count: 중복으로 제거된 문서 수
# - short_text_removed_count: 기준 길이보다 짧아 제거된 문서 수
# - missing_text_count: 본문이 없어 제거된 문서 수
# - final_document_count: 최종 저장된 문서 수
# - reject_count: 최종적으로 reject log에 기록된 전체 문서 수
#
# final_document_count는 processed 문서의 실제 개수와 같아야 한다.
# 각 사유별 제거 건수의 합계가 reject_count와 일치하는지 검증한다.

# TODO 10. 중복 문서 제거와 중복 문서 통계를 구분한다.
#
# duplicate_doc_id_count는 처리 후 중복 ID가 발견된 개수이고,
# duplicate_removed_count는 중복 문서를 실제로 제외한 개수이다.
# 두 값은 의미가 다르므로 report에서 별도 필드로 관리한다.
#
# 중복 판단 기준은 contentid에서 만든 doc_id로 한다.
# 이미 처리한 doc_id가 다시 나오면 해당 문서는 processed 목록에 넣지 않고,
# reject log에 duplicate_doc_id 사유로 기록한다.

def build_preprocessing_report(
    processed,
    rejects,
    source_count,
    duplicate_removed_count,
):
    final_document_count = len(processed)
    reject_count = len(rejects)

    doc_ids = [doc.get("doc_id") for doc in processed] # 최종 processed 안에 중복 doc_id가 남아 있는지 확인

    duplicate_doc_id_count = (
        len(doc_ids) - len(set(doc_ids))
    )

    missing_text_count = 0
    short_text_removed_count = 0
    other_removed_count = 0

    # reject 문서의 대표 제거 사유 집계
    # 우선순위:
    # duplicate > missing_text > short_text
    # 한 문서를 여러 번 세지 않도록 함
    reason_count = 0

    for row in rejects:
        reasons = row.get("reject_reason", [])

        if isinstance(reasons, str):
            reasons = reasons.split(",")

        if "missing_text" in reasons:
            missing_text_count += 1

        elif "short_text" in reasons:
            short_text_removed_count += 1

        elif "duplicate_doc_id" not in reasons:
            other_removed_count += 1 # 날짜, 좌표 등 기타 검증 오류도 reject이므로 포함

    # TODO 9: 제거 사유 총계 검증
    reason_count = (
        duplicate_removed_count
        + missing_text_count
        + short_text_removed_count
        + other_removed_count
    )

    if reason_count != reject_count:
        raise ValueError(
            "reject reason count mismatch: "
            f"{reason_count} != {reject_count}"
        )

    text_lengths = [ # 텍스트 길이 통계
        len(doc["text"])
        for doc in processed
    ]

    if text_lengths:
        min_text_length = min(text_lengths)
        max_text_length = max(text_lengths)
        avg_text_length = (
            sum(text_lengths) / len(text_lengths)
        )
    else:
        min_text_length = 0
        max_text_length = 0
        avg_text_length = 0

    return {
        "source_count": source_count,

        # TODO 10
        # 처리 후 남아 있는 중복 ID 수
        "duplicate_doc_id_count":
            duplicate_doc_id_count,

        # 실제 제거한 중복 문서 수
        "duplicate_removed_count":
            duplicate_removed_count,

        # TODO 9
        "short_text_removed_count":
            short_text_removed_count,

        "missing_text_count":
            missing_text_count,

        "other_removed_count":
            other_removed_count,

        "final_document_count":
            final_document_count,

        "reject_count":
            reject_count,

        # TODO 4
        "min_text_length":
            min_text_length,

        "max_text_length":
            max_text_length,

        "avg_text_length":
            avg_text_length,
    }

# TODO 5. 출력 파일을 정의한다.
#
# config.py의 PROCESSED_DOCUMENTS_PATH
# config.py의 REJECT_LOG_PATH
# config.py의 PREPROCESSING_REPORT_PATH

# TODO 8. 저장 후 JSONL 파싱, 건수 합계, doc_id 중복, report 통계를 재검증한다.
#
# 저장된 JSONL을 다시 한 줄씩 읽고 json.loads가 성공하는지 확인한다.
# processed_count + reject_count가 source_count와 같은지 확인한다.
# 성공 문서의 doc_id가 중복되지 않는지 확인한다.
# report의 각 count가 실제 processed/reject 파일의 행 수와 같은지 확인한다.
# 검증 실패 시 성공으로 종료하지 말고 오류를 발생시킨다.

def verify_outputs(
    processed_path,
    reject_path,
    report,
    source_count,
):
    # 저장된 processed JSONL 다시 읽기
    processed_rows = []

    with open(
        processed_path,
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            if line.strip():
                processed_rows.append(
                    json.loads(line)
                )

    # 저장된 reject JSONL 다시 읽기
    reject_rows = []

    with open(
        reject_path,
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            if line.strip():
                reject_rows.append(
                    json.loads(line)
                )

    processed_count = len(processed_rows)
    reject_count = len(reject_rows)

    # 전체 건수 확인
    if processed_count + reject_count != source_count:
        raise ValueError(
            "count mismatch: "
            f"processed({processed_count}) "
            f"+ reject({reject_count}) "
            f"!= source_count({source_count})"
        )

    # 성공 문서 doc_id 중복 검사
    doc_ids = [
        row.get("doc_id")
        for row in processed_rows
    ]

    if len(doc_ids) != len(set(doc_ids)):
        raise ValueError(
            "duplicate doc_id found "
            "in processed documents"
        )

    # report 통계 확인
    if report["source_count"] != source_count:
        raise ValueError(
            "report source_count mismatch"
        )

    if (
        report["final_document_count"]
        != processed_count
    ):
        raise ValueError(
            "report final_document_count mismatch"
        )

    if (
        report["reject_count"]
        != reject_count
    ):
        raise ValueError(
            "report reject_count mismatch"
        )

    # 처리 후 중복은 반드시 0이어야 정상
    if report["duplicate_doc_id_count"] != 0:
        raise ValueError(
            "duplicate_doc_id_count "
            "must be 0 after preprocessing"
        )

    duplicate_reject_count = 0

    for row in reject_rows:
        reasons = row.get("reject_reason", [])

        if isinstance(reasons, str):
            reasons = reasons.split(",")

        if "duplicate_doc_id" in reasons:
            duplicate_reject_count += 1

    if duplicate_reject_count != report["duplicate_removed_count"]:
        raise ValueError(
            "report duplicate_removed_count mismatch"
        )

    return True



# TODO 10. 중복 문서 제거와 중복 문서 통계를 구분한다.
#
# duplicate_doc_id_count는 처리 후 중복 ID가 발견된 개수이고,
# duplicate_removed_count는 중복 문서를 실제로 제외한 개수이다.
# 두 값은 의미가 다르므로 report에서 별도 필드로 관리한다.
#
# 중복 판단 기준은 contentid에서 만든 doc_id로 한다.
# 이미 처리한 doc_id가 다시 나오면 해당 문서는 processed 목록에 넣지 않고,
# reject log에 duplicate_doc_id 사유로 기록한다.

def preprocess_documents(documents):
    processed = []
    rejects = []

    seen_doc_ids = set()
    duplicate_removed_count = 0

    for document in documents:
        doc_id = document.get("doc_id")

        # TODO 10:
        # 이미 나온 doc_id면 processed에 넣지 않고 reject
        if doc_id and doc_id in seen_doc_ids:
            rejects.append(
                make_reject_log(
                    document,
                    ["duplicate_doc_id"],
                )
            )

            duplicate_removed_count += 1
            continue

        # 일반 검증
        errors = validate_document(document)

        if errors:
            rejects.append(
                make_reject_log(
                    document,
                    errors,
                )
            )
            continue

        # 처음 나온 doc_id 기록
        seen_doc_ids.add(doc_id)

        processed.append(document)

    return (
        processed,
        rejects,
        duplicate_removed_count,
    )


#최종 실행 코드

def run_preprocessing(documents):
    source_count = len(documents)

    # 전처리
    (
        processed,
        rejects,
        duplicate_removed_count,
    ) = preprocess_documents(documents)

    # report 생성
    report = build_preprocessing_report(
        processed,
        rejects,
        source_count,
        duplicate_removed_count,
    )

    # TODO 5: config.py의 경로 사용
    save_jsonl(
        PROCESSED_DOCUMENTS_PATH,
        processed,
    )

    save_jsonl(
        REJECT_LOG_PATH,
        rejects,
    )

    save_json(
        PREPROCESSING_REPORT_PATH,
        report,
    )

    # TODO 8: 저장 후 재검증
    verify_outputs(
        PROCESSED_DOCUMENTS_PATH,
        REJECT_LOG_PATH,
        report,
        source_count,
    )

    print("전처리 및 검증 완료")

    return processed, rejects, report
