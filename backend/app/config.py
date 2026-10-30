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
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
