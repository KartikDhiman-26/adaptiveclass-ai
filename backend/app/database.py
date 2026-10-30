from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import DATABASE_URL, DB_CONNECT_TIMEOUT
from sqlalchemy.engine import make_url

# Mask sensitive credentials so passwords are never exposed in console or log outputs
SAFE_DATABASE_URL = make_url(DATABASE_URL).render_as_string(hide_password=True)

connect_args = {}
if 'postgresql' in DATABASE_URL or 'psycopg' in DATABASE_URL:
    connect_args['connect_timeout'] = DB_CONNECT_TIMEOUT

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    connect_args=connect_args,
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
        print(f"[OK] Connected successfully to PostgreSQL database at: {SAFE_DATABASE_URL}")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to connect to PostgreSQL: {exc}")
        raise RuntimeError(
            f"Could not connect to PostgreSQL instance at {SAFE_DATABASE_URL}. "
            "Please ensure the PostgreSQL server is running and the credentials in .env are correct."
        ) from exc
