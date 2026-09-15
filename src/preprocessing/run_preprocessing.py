"""축제 전처리 파이프라인을 실행하고 검증된 결과를 저장한다."""
from .document_builder import build_festival_document
from .load_data import load_festival_sources
from .validation_output import build_preprocessing_report, preprocess_documents, save_json, save_jsonl, verify_outputs
from config import PREPROCESSING_REPORT_PATH, PROCESSED_DOCUMENTS_PATH, REJECT_LOG_PATH


def build_documents_from_sources(sources):
    return [build_festival_document(f, sources.intro_lookup.get(f["contentid"]), sources.info_lookup.get(f["contentid"], [])) for f in sources.festival_rows]


def run_preprocessing():
    sources = load_festival_sources()
    documents = build_documents_from_sources(sources)
    processed, rejects, duplicate_count = preprocess_documents(documents)
    report = build_preprocessing_report(processed, rejects, len(documents), duplicate_count)
    report.update({
        "intro_missing_count": sum(f["contentid"] not in sources.intro_lookup for f in sources.festival_rows),
        "info_missing_count": sum(f["contentid"] not in sources.info_lookup for f in sources.festival_rows),
        "intro_skipped_count": len(sources.diagnostics.intro_skipped_rows),
        "info_skipped_count": len(sources.diagnostics.info_skipped_rows),
    })
    save_jsonl(PROCESSED_DOCUMENTS_PATH, processed)
    save_jsonl(REJECT_LOG_PATH, rejects)
    save_json(PREPROCESSING_REPORT_PATH, report)
    verify_outputs(PROCESSED_DOCUMENTS_PATH, REJECT_LOG_PATH, report, len(documents))
    return processed, rejects, report


if __name__ == "__main__":
    run_preprocessing()
