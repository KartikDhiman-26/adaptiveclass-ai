import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CaptchaChallenge, Mentor, Teacher, Student
from app.schemas import CaptchaResponse, LoginRequest, LoginResponse
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/captcha", response_model=CaptchaResponse)
def create_captcha(db: Session = Depends(get_db)):
    left = secrets.randbelow(20) + 1
    right = secrets.randbelow(20) + 1
    challenge = CaptchaChallenge(
        id=secrets.token_urlsafe(24),
        question=f"What is {left} + {right}?",
        answer_hash=hash_password(str(left + right)),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(challenge)
    db.commit()
    return CaptchaResponse(
        captcha_id=challenge.id,
        question=challenge.question,
        expires_at=challenge.expires_at,
    )

@router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    identifier = (creds.login_id or creds.email or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=422, detail="login_id or email is required")
    if creds.login_id and (not creds.captcha_id or not creds.captcha_answer):
        raise HTTPException(status_code=422, detail="captcha_id and captcha_answer are required")
    if creds.captcha_id or creds.captcha_answer:
        challenge = db.get(CaptchaChallenge, creds.captcha_id)
        if (not challenge or challenge.used or
                challenge.expires_at < datetime.now(timezone.utc) or
                not creds.captcha_answer or
                not verify_password(creds.captcha_answer.strip(), challenge.answer_hash)):
            raise HTTPException(status_code=401, detail="Invalid or expired captcha")
        challenge.used = True
        db.commit()

    # 1. Check Teacher
    teacher = db.query(Teacher).filter(Teacher.email == identifier).first()
    if teacher and verify_password(creds.password, teacher.hashed_password):
        class_obj = teacher.classes[0] if teacher.classes else None
        class_id = class_obj.id if class_obj else 1
        token = create_access_token({"sub": teacher.email, "role": "teacher", "id": teacher.id})
        return LoginResponse(
            user_id=teacher.id,
            name=teacher.name,
            email=teacher.email,
            role="teacher",
            class_id=class_id,
            token=token
        )

    # 2. Check Mentor
    mentor = db.query(Mentor).filter(Mentor.email == identifier).first()
    if mentor and verify_password(creds.password, mentor.hashed_password):
        token = create_access_token({"sub": mentor.email, "role": "mentor", "id": mentor.id})
        return LoginResponse(
            user_id=mentor.id, name=mentor.name, email=mentor.email,
            role="mentor", token=token
        )

    # 3. Check Student
    student = db.query(Student).filter(Student.email == identifier).first()
    if student and verify_password(creds.password, student.hashed_password):
        token = create_access_token({"sub": student.email, "role": "student", "id": student.id})
        return LoginResponse(
            user_id=student.id,
            name=student.name,
            email=student.email,
            role="student",
            class_id=student.class_id,
            token=token
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials. For demo: teacher@demo.com or student@demo.com with password 'password'"
    )

@router.get("/demo-users")
def get_demo_users():
    """Returns quick switcher accounts for live evaluator demonstration."""
    return [
        {
            "role": "teacher",
            "name": "Prof. Vikram Sen",
            "email": "teacher@demo.com",
            "password": "password",
            "description": "Instructor view: Classroom analytics, critical gap alerts, and teaching interventions"
        },
        {
            "role": "student",
            "name": "Aarav Sharma",
            "email": "student@demo.com",
            "password": "password",
            "description": "Student view: Needs practice on Recursion (28%), personalized recommendations"
        },
        {
            "role": "student",
            "name": "Priya Patel",
            "email": "advanced@demo.com",
            "password": "password",
            "description": "Advanced learner: High mastery across all concepts (92%), enrichment challenges"
        },
        {
            "role": "mentor",
            "name": "Dr. Demo Mentor",
            "email": "mentor@demo.com",
            "password": "password",
            "description": "Mentor view: access to analytics and marks across all subjects"
        }
    ]
