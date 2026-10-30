from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS
from app.database import engine, Base, SessionLocal, check_db_connection
from app.seed_data import seed_database
from app.routers import auth, classes, students, quiz, demo, student_tutor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Check PostgreSQL connectivity
    print("[STARTUP] Checking PostgreSQL connectivity...")
    check_db_connection()

    # 2. Ensure schema tables exist
    print("[STARTUP] Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    # 3. Idempotent seed check
    print("[STARTUP] Checking seed data...")
    db = SessionLocal()
    try:
        seed_database(db, force=False)
    finally:
        db.close()

    print("[STARTUP] AdaptiveClass AI Backend is ready!")
    yield
    print("[SHUTDOWN] Shutting down AdaptiveClass AI Backend...")

app = FastAPI(
    title="AdaptiveClass AI API",
    description="Adaptive Learning Intelligence Platform for College Classrooms",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(students.router)
app.include_router(quiz.router)
app.include_router(demo.router)
app.include_router(student_tutor.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to AdaptiveClass AI API",
        "philosophy": "AI augments the teacher; it does not replace the teacher.",
        "docs_url": "/docs",
        "database": "PostgreSQL 17",
        "status": "online"
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "postgresql",
        "version": "1.0.0"
    }
