from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_service import generate_student_ai
from app.database import get_db
from app.dependencies import current_student
from app.models import DatasetRow, Student
from app.schemas import StudentAiChatRequest, StudentAiResponse

router = APIRouter(prefix="/api/student-ai", tags=["Student AI"])


def _performance_context(claims: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    student = db.get(Student, claims.get("id"))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    rows = db.query(DatasetRow).filter(DatasetRow.roll_number == student.roll_number).all()
    return [
        {
            "subject": row.subject,
            "class": row.class_name,
            "topic": row.topic,
            "marks": row.marks,
            "max_marks": row.max_marks,
            "assessment": row.assessment,
            "date": row.assessment_date,
        }
        for row in rows
    ]


def _run_ai(
    response_type: str,
    request: StudentAiChatRequest,
    claims: Dict[str, Any],
    db: Session,
) -> StudentAiResponse:
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="message cannot be empty")
    payload = request.model_dump()
    payload["response_type"] = response_type
    try:
        content, model_name = generate_student_ai(payload, _performance_context(claims, db))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return StudentAiResponse(
        response_type=response_type,
        content=content,
        model_name=model_name,
    )


@router.post("/chat", response_model=StudentAiResponse)
def chat(
    request: StudentAiChatRequest,
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    return _run_ai("topic_chat", request, claims, db)


@router.post("/quiz", response_model=StudentAiResponse)
def quiz(
    request: StudentAiChatRequest,
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    return _run_ai("personalized_quiz", request, claims, db)


@router.post("/learning-plan", response_model=StudentAiResponse)
def learning_plan(
    request: StudentAiChatRequest,
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    return _run_ai("learning_plan", request, claims, db)


@router.get("/resources", response_model=StudentAiResponse)
def resources(
    topic: str,
    difficulty: str = "beginner",
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    request = StudentAiChatRequest(
        message=f"Recommend learning resources for {topic}.",
        topic=topic,
        difficulty=difficulty,
    )
    return _run_ai("video_resources", request, claims, db)
