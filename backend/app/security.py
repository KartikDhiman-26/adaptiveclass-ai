import hashlib
import hmac
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import jwt
from jose.exceptions import JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student

_configured_secret = os.getenv("JWT_SECRET_KEY")
if os.getenv("APP_ENV", "development").lower() == "production" and (
    not _configured_secret or len(_configured_secret) < 32
):
    raise RuntimeError("Production requires a JWT_SECRET_KEY of at least 32 characters")
SECRET_KEY = _configured_secret or "adaptiveclass-ai-development-only-key"
ALGORITHM = "HS256"
SALT = "adaptive_edu_salt_"
bearer_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salted = f"{SALT}{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_authenticated_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Student:
    """Validates a bearer token and resolves its student identity from the database."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid student authentication is required",
        headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthorized

    try:
        claims = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise unauthorized

    student_id = claims.get("id")
    email = claims.get("sub")
    if claims.get("role") != "student" or not isinstance(student_id, int) or not email:
        raise unauthorized
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.email == email
    ).first()
    if student is None:
        raise unauthorized
    return student
