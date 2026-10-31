from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from the backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

raw_database_url = os.getenv("DATABASE_URL")

if not raw_database_url:
    raise RuntimeError(
        "CRITICAL ERROR: DATABASE_URL environment variable is missing. "
        "PostgreSQL is required for AdaptiveClass AI. "
        "Please specify a valid PostgreSQL connection URL in backend/.env"
    )

# Normalize database URL to strictly use the psycopg 3 driver (postgresql+psycopg://)
# Cloud platforms like Render inject DATABASE_URL as 'postgres://' or 'postgresql://',
# which causes SQLAlchemy to default to psycopg2 (resulting in ModuleNotFoundError: No module named 'psycopg2').
if raw_database_url.startswith("postgres://"):
    DATABASE_URL = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_database_url.startswith("postgresql+psycopg2://"):
    DATABASE_URL = raw_database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
elif raw_database_url.startswith("postgresql://"):
    DATABASE_URL = raw_database_url.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = raw_database_url

if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError(
        f"CRITICAL ERROR: Invalid database scheme in DATABASE_URL: {DATABASE_URL}. "
        "AdaptiveClass AI strictly requires PostgreSQL with the psycopg 3 driver (postgresql+psycopg://)."
    )

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
GEMINI_REQUEST_TIMEOUT_MS = int(os.getenv("GEMINI_REQUEST_TIMEOUT_MS", "10000"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "3"))
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://adaptiveclass-ai.vercel.app",
]

# Allow adding origins dynamically via ADDITIONAL_CORS_ORIGINS or CORS_ORIGINS
raw_additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS") or os.getenv("CORS_ORIGINS")
if raw_additional_origins:
    for origin in raw_additional_origins.split(","):
        origin_clean = origin.strip().rstrip("/")
        if origin_clean and origin_clean not in CORS_ORIGINS:
            CORS_ORIGINS.append(origin_clean)


def get_gemini_status() -> Dict[str, Any]:
    has_key = bool(GEMINI_API_KEY)
    key_length = len(GEMINI_API_KEY) if has_key else 0
    return {
        "configured": has_key,
        "key_length": key_length,
        "model": GEMINI_MODEL,
        "mode": "online (Gemini API)" if has_key else "offline (pedagogical engine fallback)"
    }
