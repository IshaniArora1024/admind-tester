import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
ADMIND_MASTER_KEY: str = os.getenv("ADMIND_MASTER_KEY", "admind_test_key_123")
LOG_IMPRESSIONS: bool = os.getenv("LOG_IMPRESSIONS", "true").lower() == "true"
LOG_CLICKS: bool = os.getenv("LOG_CLICKS", "true").lower() == "true"
CAMPAIGNS_DIR: str = os.getenv("CAMPAIGNS_DIR", "campaigns")
LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")

Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

IMPRESSIONS_PATH = Path(LOGS_DIR) / "impressions.jsonl"
CLICKS_PATH = Path(LOGS_DIR) / "clicks.jsonl"

if not IMPRESSIONS_PATH.exists():
    IMPRESSIONS_PATH.touch()

if not CLICKS_PATH.exists():
    CLICKS_PATH.touch()
