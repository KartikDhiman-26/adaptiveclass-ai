from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """Verify active PostgreSQL connectivity on startup."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print(f"[OK] Connected successfully to PostgreSQL database at: {DATABASE_URL}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to connect to PostgreSQL: {exc}")
        raise RuntimeError(
            f"Could not connect to PostgreSQL instance at {DATABASE_URL}. "
            "Please ensure the PostgreSQL server is running and the credentials in .env are correct."
        ) from exc
