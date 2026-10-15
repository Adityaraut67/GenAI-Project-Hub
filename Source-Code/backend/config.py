import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATASET_PATH = BASE_DIR / "scheme_data.json"
TEMP_UPLOAD_DIR = BASE_DIR / "temp_uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf"}
DEFAULT_LANGUAGE = os.getenv("CIVICLENS_DEFAULT_LANGUAGE", "en")
CORS_ORIGIN = os.getenv("CIVICLENS_CORS_ORIGIN", "http://localhost:5173")


def get_llm_settings():
    return {
        "api_key": os.getenv("CIVICLENS_LLM_API_KEY", ""),
        "endpoint": os.getenv("CIVICLENS_LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
        "model": os.getenv("CIVICLENS_LLM_MODEL", "gpt-4o-mini"),
    }
