from pathlib import Path
import os, re, sys

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False): return Path(sys.executable).parent
    return Path(os.path.abspath(__file__)).parent.parent
BASE_DIR = _get_base_dir()

LIB_FILE_NAME = "历史价格库.xlsx"
BACKUP_PREFIX = "历史价格库_备份_"
IMPORT_REQUIRED_COLS = ("material_name", "spec_feature")
BATCH_FUZZ_THRESHOLD = 50
SINGLE_RESULT_LIMIT = 50
UI_THROTTLE_SEC = 0.1
PDF_MAX_PAGES = 30
PDF_TEXT_CHUNK_CHARS = 9000
PDF_TEXT_CHUNK_OVERLAP = 500
PBKDF2_ITERATIONS = 600_000
API_TIMEOUT = (8, 90)

COL_PROJECT, COL_MATERIAL, COL_SPEC = "project_name", "material_name", "spec_feature"
COL_UNIT, COL_PRICE, COL_CONTRACT = "unit", "price_tax", "contract_no"
COL_SUPPLIER, COL_DATE = "supply_company", "record_date"

DEFAULT_AI_URL_CN = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_TEXT_MODEL, DEFAULT_VL_MODEL = "qwen-max", "qwen-vl-max"

APP_FONT, NUM_FONT = "Microsoft YaHei UI", "Segoe UI"

COLOR_BG = ("#F8F9FA", "#111111")
COLOR_CARD = ("#FFFFFF", "#1C1C1E")
COLOR_TEXT_MAIN = ("#1A1A1A", "#F3F4F6")
COLOR_TEXT_SUB = ("#6B7280", "#9CA3AF")
COLOR_BRAND = ("#0067C0", "#4CC2FF")
COLOR_BRAND_LIGHT = ("#E5F1FB", "#1A3348")
COLOR_SIDEBAR_BG = ("#FFFFFF", "#111111")
COLOR_NAV_HOVER = ("#F3F4F6", "#2D2D2D")
COLOR_SEARCH = ("#0F7B6C", "#26B39D")
COLOR_DANGER = ("#C42B1C", "#FF99A4")
COLOR_PLACEHOLDER = ("#8B98A9", "#6B7280")
COLOR_INPUT_BG = ("#FFFFFF", "#2D2D2D")
COLOR_TABLE_ODD = ("#F9FAFB", "#242424")
COLOR_BORDER = ("#E5E7EB", "#333333")

_BACKUP_TIME_RE = re.compile(r"(\d{8}_\d{6})")
_JSON_ARRAY_RE = re.compile(r'\[[\s\S]*\]')