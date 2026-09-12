"""프로젝트에서 사용하는 공통 경로와 파일명을 관리한다."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
EXTRA_DIR = DATA_DIR / "extra"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLES_DIR = DATA_DIR / "samples"

FESTIVAL_RAW_PATH = RAW_DIR / "festival_raw.json"
EXPERIENCE_RAW_PATH = RAW_DIR / "experience_raw.json"
FESTIVAL_FULL_SAMPLE_PATH = SAMPLES_DIR / "festivals_2026_full.json"
FESTIVAL_INTRO_PATH = EXTRA_DIR / "festival_intro_2026.json"
FESTIVAL_INFO_PATH = EXTRA_DIR / "festival_info_2026.json"
FESTIVAL_NEARBY_PATH = EXTRA_DIR / "festival_nearby_5km.json"
STAYS_PATH = EXTRA_DIR / "stays_all.json"
CLASSIFICATION_CODES_PATH = EXTRA_DIR / "classification_codes.json"

PROCESSED_DOCUMENTS_PATH = PROCESSED_DIR / "festivals_documents.jsonl"
REJECT_LOG_PATH = PROCESSED_DIR / "preprocessing_reject_log.jsonl"
PREPROCESSING_REPORT_PATH = PROCESSED_DIR / "preprocessing_report.json"
