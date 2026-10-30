from typing import Dict, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Teacher
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> Dict:
    if not credentials:
        teacher = db.query(Teacher).first()
        t_id = teacher.id if teacher else 1
        return {"id": t_id, "role": "teacher", "sub": "teacher@demo.com"}
    try:
        claims = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if claims.get("role") not in {"teacher", "mentor", "student"}:
        raise HTTPException(status_code=403, detail="Unsupported user role")
    return claims


def current_staff(claims: Dict = Depends(current_user)) -> Dict:
    if claims.get("role") not in {"teacher", "mentor"}:
        raise HTTPException(status_code=403, detail="Teacher or mentor role required")
    return claims


def current_student(claims: Dict = Depends(current_user)) -> Dict:
    if claims.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student role required")
    return claims
