import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """App configuration"""

    # App info
    APP_NAME = "Pocket"
    APP_VERSION = "0.1.0"

    # API Settings
    API_BASE_URL = os.getenv("API_URL", "http://localhost:8000/api")
    API_TIMEOUT = 30

    # Security
    TOKEN_EXPIRY_DAYS = 7

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    STORAGE_DIR = BASE_DIR / "storage"

    # Colors (for theming)
    PRIMARY_COLOR = (0.2, 0.6, 0.8, 1)  # Blue
    SUCCESS_COLOR = (0.2, 0.8, 0.4, 1)  # Green
    WARNING_COLOR = (0.9, 0.6, 0.1, 1)  # Orange
    DANGER_COLOR = (0.8, 0.2, 0.2, 1)  # Red

    # Create storage directory if not exists
    STORAGE_DIR.mkdir(exist_ok=True)
