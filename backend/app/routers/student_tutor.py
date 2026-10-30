"""
FastAPI Router for Student AI Tutor and Adaptive Practice.
Exposes endpoints for chat, adaptive quiz generation, answer evaluation,
and learner profiling for direct frontend integration.
"""

import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import get_authenticated_student
from app.models import (
    Student, TutorConversation, TutorConversationMessage, TutorPracticeSession
)
from app.schemas import (
    TutorChatRequest, TutorChatResponse,
    TutorConversationResponse, TutorConversationMessageResponse,
    TutorQuizStartRequest, TutorQuizStartResponse, TutorQuizResumeResponse,
    TutorQuizQuestionItem,
    TutorQuizAnswerRequest, TutorQuizAnswerResponse
)
from app.student_ai.tutor import StudentTutor, ChatMessage
from app.student_ai.profiler import (
    load_learner_profile_from_db, create_new_student_profile,
    update_profile_with_quiz, calculate_learning_level
)
from app.student_ai.quiz_generator import (
    AdaptiveQuizSession, QuizQuestion, find_question_for_session,
    evaluate_student_answer, get_available_topics
)
from app.config import get_gemini_status
from app.student_ai.emotion_detector import ETHICAL_DISCLAIMER

router = APIRouter(prefix="/api/student-tutor", tags=["Student AI Tutor"])

@router.get("/status")
def tutor_status():
    """Returns safe runtime status of Gemini / Offline engine configuration without exposing credentials."""
    status = get_gemini_status()
    return {
        "gemini_configured": status["configured"],
        "model": status["model"],
        "mode": status["mode"],
        "active_engine": "gemini" if status["configured"] else "offline_fallback"
    }


@router.get("/topics", response_model=List[str])
def list_available_topics():
    """Returns available topics for adaptive practice."""
    return get_available_topics()

@router.post("/chat", response_model=TutorChatResponse)
def tutor_chat(
    req: TutorChatRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """
    Conversational AI tutor endpoint with emotion-aware adaptation,
    scaffolding, and line-by-line code explanation.
    """
    if req.student_id is not None and req.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    profile = load_learner_profile_from_db(current_student.id, db)
    if not profile:
        profile = create_new_student_profile(current_student.name)
        profile.student_id = current_student.id

    conversation = None
    if req.session_id:
        conversation = db.query(TutorConversation).filter(
            TutorConversation.id == req.session_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Tutor conversation not found")
        if conversation.student_id != current_student.id:
            raise HTTPException(status_code=404, detail="Tutor conversation not found")
    else:
        conversation = TutorConversation(
            id=str(uuid.uuid4()),
            student_id=current_student.id,
            student_name=current_student.name
        )
        db.add(conversation)
        db.flush()

    tutor = StudentTutor(
        student_name=conversation.student_name,
        student_level=profile.learning_level,
        profile=profile
    )
    tutor.session_id = conversation.id
    tutor.current_topic = conversation.current_topic
    tutor.history = [
        ChatMessage(role=message.role, content=message.content)
        for message in conversation.messages
    ]
    tutor.seen_suggestions = set(json.loads(conversation.seen_suggestions or "[]"))
    if req.topic:
        tutor.current_topic = req.topic

    history_start = len(tutor.history)
    res = tutor.chat(req.message, requested_format=req.requested_format)

    conversation.current_topic = tutor.current_topic
    conversation.seen_suggestions = json.dumps(sorted(tutor.seen_suggestions))
    for message in tutor.history[history_start:]:
        db.add(TutorConversationMessage(
            conversation_id=conversation.id,
            role=message.role,
            content=message.content
        ))
    db.commit()

    return TutorChatResponse(
        session_id=conversation.id,
        message=res.message,
        topic_detected=res.topic_detected,
        detected_cue=res.detected_cue.value,
        confidence=res.confidence,
        adaptation_applied=res.adaptation_applied,
        suggested_followups=res.suggested_followups,
        suggest_quiz=res.suggest_quiz,
        suggested_quiz_topic=res.suggested_quiz_topic,
        engine_used=res.engine_used,
        response_format=res.response_format,
        ethical_disclaimer=ETHICAL_DISCLAIMER
    )

@router.get("/sessions/{session_id}", response_model=TutorConversationResponse)
def get_tutor_conversation(
    session_id: str,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """Loads a conversation only for the student identity that owns it."""
    if student_id is not None and student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    conversation = db.query(TutorConversation).filter(
        TutorConversation.id == session_id
    ).first()
    if not conversation or conversation.student_id != current_student.id:
        raise HTTPException(status_code=404, detail="Tutor conversation not found")

    return TutorConversationResponse(
        session_id=conversation.id,
        current_topic=conversation.current_topic,
        messages=[
            TutorConversationMessageResponse(
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat()
            )
            for message in conversation.messages
        ]
    )


def _serialize_practice_session(session: AdaptiveQuizSession) -> str:
    return json.dumps({
        "current_difficulty": session.current_difficulty,
        "total_target_questions": session.total_target_questions,
        "questions_asked": [question.model_dump() for question in session.questions_asked],
        "answers_given": session.answers_given,
        "score": session.score,
        "difficulty_progression": session.difficulty_progression,
        "consecutive_correct": session.consecutive_correct,
        "consecutive_incorrect": session.consecutive_incorrect,
        "weak_concepts": session.weak_concepts,
        "is_complete": session.is_complete,
        "pending_question": (
            session.pending_question.model_dump() if session.pending_question else None
        )
    })


def _restore_practice_session(record: TutorPracticeSession) -> AdaptiveQuizSession:
    state = json.loads(record.state_json)
    session = AdaptiveQuizSession(
        topic=record.topic,
        starting_difficulty=state["current_difficulty"],
        total_questions=state["total_target_questions"],
        student_id=record.student_id
    )
    session.session_id = record.id
    session.questions_asked = [
        QuizQuestion.model_validate(question)
        for question in state["questions_asked"]
    ]
    session.answers_given = state["answers_given"]
    session.score = state["score"]
    session.difficulty_progression = state["difficulty_progression"]
    session.consecutive_correct = state["consecutive_correct"]
    session.consecutive_incorrect = state["consecutive_incorrect"]
    session.weak_concepts = state["weak_concepts"]
    session.is_complete = state["is_complete"]
    session.pending_question = (
        QuizQuestion.model_validate(state["pending_question"])
        if state["pending_question"] else None
    )
    return session


@router.get("/quiz/{session_id}", response_model=TutorQuizResumeResponse)
def get_tutor_quiz_session(
    session_id: str,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """Restores an active quiz for its student after a reload or process restart."""
    if student_id is not None and student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    record = db.query(TutorPracticeSession).filter(
        TutorPracticeSession.id == session_id
    ).first()
    if not record or record.student_id != current_student.id:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    session = _restore_practice_session(record)
    question = session.pending_question
    return TutorQuizResumeResponse(
        session_id=session.session_id,
        topic=session.topic,
        current_difficulty=session.current_difficulty,
        total_questions=session.total_target_questions,
        current_question=TutorQuizQuestionItem(
            question_id=question.question_id,
            topic=question.topic,
            difficulty=question.difficulty,
            question_text=question.question_text,
            options=question.options,
            concept_focus=question.concept_focus
        ) if question else None,
        answered_count=len(session.questions_asked),
        current_score=session.score,
        is_complete=session.is_complete
    )


@router.post("/quiz/start", response_model=TutorQuizStartResponse)
def start_tutor_quiz(
    req: TutorQuizStartRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """Initializes an adaptive quiz session on the chosen topic."""
    if req.student_id is not None and req.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    conversation = None
    if req.chat_session_id:
        conversation = db.query(TutorConversation).filter(
            TutorConversation.id == req.chat_session_id
        ).first()
        if not conversation or conversation.student_id != current_student.id:
            raise HTTPException(status_code=404, detail="Tutor conversation not found")
    topic = req.topic or (conversation.current_topic if conversation else None) or "Recursion"

    profile = load_learner_profile_from_db(current_student.id, db)
    if not profile:
        profile = create_new_student_profile(current_student.name)
        profile.student_id = current_student.id

    topic_mastery = profile.topic_mastery.get(topic)
    if req.starting_difficulty:
        starting_diff = req.starting_difficulty
    elif topic_mastery and topic_mastery.attempt_count > 0:
        starting_diff = calculate_learning_level(topic_mastery.mastery_percentage).lower()
    else:
        starting_diff = profile.learning_level.lower()

    session = AdaptiveQuizSession(
        topic=topic,
        starting_difficulty=starting_diff,
        total_questions=5,
        student_id=current_student.id
    )

    q = find_question_for_session(session)
    if not q:
        raise HTTPException(status_code=404, detail=f"No questions available for {topic}")
    session.pending_question = q

    db.add(TutorPracticeSession(
        id=session.session_id,
        student_id=current_student.id,
        student_name=profile.student_name,
        topic=session.topic,
        state_json=_serialize_practice_session(session)
    ))
    db.commit()

    item = TutorQuizQuestionItem(
        question_id=q.question_id,
        topic=q.topic,
        difficulty=q.difficulty,
        question_text=q.question_text,
        options=q.options,
        concept_focus=q.concept_focus
    )

    return TutorQuizStartResponse(
        session_id=session.session_id,
        topic=session.topic,
        current_difficulty=session.current_difficulty,
        first_question=item,
        total_questions=session.total_target_questions
    )

@router.post("/quiz/answer", response_model=TutorQuizAnswerResponse)
def answer_tutor_quiz(
    req: TutorQuizAnswerRequest,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """Evaluates answer, adapts difficulty, and serves next question."""
    if req.student_id is not None and req.student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    record = db.query(TutorPracticeSession).filter(
        TutorPracticeSession.id == req.session_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Quiz session not found or expired")
    if record.student_id != current_student.id:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    session = _restore_practice_session(record)
    if not session.pending_question or session.pending_question.question_id != req.question_id:
        raise HTTPException(status_code=409, detail="Question is not the current unanswered question")

    eval_res = evaluate_student_answer(session, session.pending_question, req.selected_option)

    next_item = None
    if not eval_res.is_quiz_complete:
        next_q = find_question_for_session(session)
        if next_q:
            next_item = TutorQuizQuestionItem(
                question_id=next_q.question_id,
                topic=next_q.topic,
                difficulty=next_q.difficulty,
                question_text=next_q.question_text,
                options=next_q.options,
                concept_focus=next_q.concept_focus
            )
            session.pending_question = next_q
        else:
            eval_res.is_quiz_complete = True
            session.is_complete = True
    if eval_res.is_quiz_complete:
        session.pending_question = None
        profile = load_learner_profile_from_db(current_student.id, db)
        if not profile:
            profile = create_new_student_profile(current_student.name)
            profile.student_id = current_student.id
        update_profile_with_quiz(
            profile=profile,
            topic=session.topic,
            score=session.score,
            total_questions=len(session.questions_asked),
            final_difficulty=session.current_difficulty,
            db=db
        )
    record.state_json = _serialize_practice_session(session)
    db.commit()

    return TutorQuizAnswerResponse(
        is_correct=eval_res.is_correct,
        correct_answer=eval_res.correct_answer,
        explanation=eval_res.explanation,
        difficulty_change=eval_res.difficulty_change,
        new_difficulty=eval_res.new_difficulty,
        next_question=next_item,
        current_score=eval_res.current_score,
        is_complete=eval_res.is_quiz_complete
    )

@router.get("/profile/{student_id}")
def get_student_learner_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_authenticated_student)
):
    """Fetches full learner profile for a student."""
    if student_id != current_student.id:
        raise HTTPException(status_code=403, detail="Cannot access another student's tutor data")
    profile = load_learner_profile_from_db(student_id, db)
    if not profile:
        # Fallback to new student baseline
        profile = create_new_student_profile(f"Student #{student_id}")
        profile.student_id = student_id
    return profile.model_dump()
