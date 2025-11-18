from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

# Build the path to the .env file (one directory up from 'server/')
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Loads all settings from the .env file."""

    # --- API Keys ---
    GOOGLE_API_KEY: str

    # --- Database ---
    MONGODB_URI: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "scifusion"

    # --- NEW: Auth Settings ---
    SECRET_KEY: str = "a-very-secret-key-that-you-must-change"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # --- Job Artifacts ---
    RESULTS_DIR: str = str((BASE_DIR / "results").resolve())
    RESULTS_SAMPLE_DIR: str = str((BASE_DIR / "resultsSample").resolve())
    CORS_ALLOWED_ORIGINS: Optional[str] = None
    CORS_ALLOW_ORIGIN_REGEX: Optional[str] = None

    class Config:
        env_file = env_path
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore other env vars not defined here


# Create a single, importable settings object
# We will import this 'settings' object in other files
settings = Settings()
