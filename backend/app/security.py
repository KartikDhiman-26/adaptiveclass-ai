import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Optional
from jose import jwt

SECRET_KEY = "adaptiveclass-ai-secure-demo-secret-key-2026"
ALGORITHM = "HS256"
SALT = "adaptive_edu_salt_"

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


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
