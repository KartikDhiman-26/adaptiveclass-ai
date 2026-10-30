import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_service import analyze_student_activity, generate_student_ai
from app.database import get_db
from app.dependencies import current_staff, current_student
from app.models import DatasetRow, Student, StudentAIAttempt, StudentAIInteraction, StudentAIReport
from app.schemas import (
    StudentAiAttemptRequest, StudentAiAttemptResponse, StudentAiChatRequest,
    StudentAiReportResponse, StudentAiResponse,
)

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
    interaction = StudentAIInteraction(
        student_id=claims["id"],
        interaction_type=response_type,
        message=request.message.strip(),
        topic=request.topic,
        difficulty=request.difficulty,
        response_json=json.dumps(content),
        model_name=model_name,
    )
    db.add(interaction)
    db.commit()
    return StudentAiResponse(
        response_type=response_type,
        content=content,
        model_name=model_name,
    )


@router.post("/attempts", response_model=StudentAiAttemptResponse)
def record_attempt(
    request: StudentAiAttemptRequest,
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    if request.total_questions <= 0 or request.score < 0 or request.score > request.total_questions:
        raise HTTPException(status_code=422, detail="Invalid quiz score or total_questions")
    if request.interaction_id:
        interaction = db.get(StudentAIInteraction, request.interaction_id)
        if not interaction or interaction.student_id != claims["id"]:
            raise HTTPException(status_code=404, detail="AI interaction not found")
    attempt = StudentAIAttempt(
        student_id=claims["id"],
        interaction_id=request.interaction_id,
        topic=request.topic,
        difficulty=request.difficulty,
        score=request.score,
        total_questions=request.total_questions,
        result_json=json.dumps(request.result),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _student_report(student_id: int, db: Session) -> StudentAiReportResponse:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    interactions = db.query(StudentAIInteraction).filter(
        StudentAIInteraction.student_id == student_id
    ).order_by(StudentAIInteraction.created_at.asc()).all()
    attempts = db.query(StudentAIAttempt).filter(
        StudentAIAttempt.student_id == student_id
    ).order_by(StudentAIAttempt.created_at.asc()).all()
    activity = [
        {
            "type": item.interaction_type,
            "message": item.message,
            "topic": item.topic,
            "difficulty": item.difficulty,
            "response": json.loads(item.response_json),
            "created_at": item.created_at.isoformat(),
        }
        for item in interactions
    ]
    attempt_data = [
        {
            "topic": item.topic,
            "difficulty": item.difficulty,
            "score": item.score,
            "total_questions": item.total_questions,
            "result": json.loads(item.result_json),
            "created_at": item.created_at.isoformat(),
        }
        for item in attempts
    ]
    try:
        report, model_name = analyze_student_activity(activity, attempt_data)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    saved = StudentAIReport(
        student_id=student_id,
        model_name=model_name,
        report_json=json.dumps(report),
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return StudentAiReportResponse(
        student_id=student.id,
        student_name=student.name,
        roll_number=student.roll_number,
        interaction_count=len(interactions),
        attempt_count=len(attempts),
        report=report,
        model_name=model_name,
        created_at=saved.created_at,
    )


@router.get("/report", response_model=StudentAiReportResponse)
def own_report(
    claims: Dict[str, Any] = Depends(current_student),
    db: Session = Depends(get_db),
):
    return _student_report(claims["id"], db)


@router.get("/reports/{student_id}", response_model=StudentAiReportResponse)
def teacher_report(
    student_id: int,
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if claims["role"] == "teacher" and (
        not student.class_group or student.class_group.teacher_id != claims["id"]
    ):
        raise HTTPException(status_code=403, detail="Teacher is not assigned to this student")
    return _student_report(student_id, db)


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
