import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Question, Concept, Student, ConceptPerformance
from app.schemas import (
    AdaptiveStartRequest, AdaptiveStartResponse,
    AdaptiveNextQuestionRequest, AdaptiveNextQuestionResponse,
    QuestionOut, QuizSubmitRequest, QuizSubmitResponse
)
from app.analytics_engine import record_quiz_and_update_mastery

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

TOTAL_ADAPTIVE_QUESTIONS = 5

@router.post("/adaptive/start", response_model=AdaptiveStartResponse)
def start_adaptive_quiz(req: AdaptiveStartRequest, db: Session = Depends(get_db)):
    concept_id = req.concept_id
    if not concept_id:
        # Default to student's weakest concept
        lowest = db.query(ConceptPerformance)\
            .filter(ConceptPerformance.student_id == req.student_id)\
            .order_by(ConceptPerformance.mastery_score.asc())\
            .first()
        if lowest:
            concept_id = lowest.concept_id
        else:
            rec_c = db.query(Concept).filter(Concept.name == "Recursion").first()
            concept_id = rec_c.id if rec_c else 1

    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Start with a beginner question from PostgreSQL
    q = db.query(Question)\
        .filter(Question.concept_id == concept_id, Question.difficulty == "beginner")\
        .first()

    if not q:
        q = db.query(Question).filter(Question.concept_id == concept_id).first()

    if not q:
        raise HTTPException(status_code=404, detail="No questions available for this concept")

    q_out = QuestionOut(
        question_id=q.id,
        concept_id=concept.id,
        concept_name=concept.name,
        difficulty=q.difficulty,
        question_text=q.question_text,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d
    )

    return AdaptiveStartResponse(
        session_id=str(uuid.uuid4()),
        concept_id=concept.id,
        concept_name=concept.name,
        current_question=q_out,
        question_index=1,
        total_questions=TOTAL_ADAPTIVE_QUESTIONS,
        difficulty=q.difficulty
    )

@router.post("/adaptive/next-question", response_model=AdaptiveNextQuestionResponse)
def get_next_adaptive_question(req: AdaptiveNextQuestionRequest, db: Session = Depends(get_db)):
    current_q = db.query(Question).filter(Question.id == req.current_question_id).first()
    if not current_q:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = (req.selected_option.strip().upper() == current_q.correct_answer.strip().upper())
    curr_diff = req.current_difficulty.lower()

    # True functional adaptive difficulty progression:
    # Correct beginner -> Intermediate
    # Correct intermediate -> Advanced
    # Incorrect advanced -> Intermediate
    # Incorrect intermediate -> Beginner
    # Incorrect beginner -> Beginner (reinforce)
    if is_correct:
        if curr_diff == "beginner":
            next_target_diff = "intermediate"
            diff_change = "increased"
        elif curr_diff == "intermediate":
            next_target_diff = "advanced"
            diff_change = "increased"
        else:
            next_target_diff = "advanced"
            diff_change = "maintained"
    else:
        if curr_diff == "advanced":
            next_target_diff = "intermediate"
            diff_change = "reinforced"
        elif curr_diff == "intermediate":
            next_target_diff = "beginner"
            diff_change = "reinforced"
        else:
            next_target_diff = "beginner"
            diff_change = "reinforced"

    all_used = list(set(req.answered_question_ids + [req.current_question_id]))
    is_complete = (req.question_index >= TOTAL_ADAPTIVE_QUESTIONS)

    next_q_out = None
    if not is_complete:
        # Query PostgreSQL for next question with matching difficulty
        candidate = db.query(Question)\
            .filter(
                Question.concept_id == req.concept_id,
                Question.difficulty == next_target_diff,
                ~Question.id.in_(all_used)
            ).first()

        # Fallback to any unused question in the concept
        if not candidate:
            candidate = db.query(Question)\
                .filter(
                    Question.concept_id == req.concept_id,
                    ~Question.id.in_(all_used)
                ).first()

        if candidate:
            c_obj = candidate.concept
            c_name = c_obj.name if c_obj else "Data Structures"
            next_q_out = QuestionOut(
                question_id=candidate.id,
                concept_id=candidate.concept_id,
                concept_name=c_name,
                difficulty=candidate.difficulty,
                question_text=candidate.question_text,
                option_a=candidate.option_a,
                option_b=candidate.option_b,
                option_c=candidate.option_c,
                option_d=candidate.option_d
            )
        else:
            is_complete = True

    return AdaptiveNextQuestionResponse(
        is_correct=is_correct,
        correct_answer=current_q.correct_answer,
        explanation=current_q.explanation or "No explanation provided.",
        difficulty_change=diff_change,
        next_question=next_q_out,
        is_quiz_complete=is_complete,
        current_score=0,  # calculated on final submit
        total_answered=req.question_index
    )

@router.post("/submit", response_model=QuizSubmitResponse)
def submit_quiz(sub: QuizSubmitRequest, db: Session = Depends(get_db)):
    answers_dicts = [a.model_dump() for a in sub.answers]
    return record_quiz_and_update_mastery(
        student_id=sub.student_id,
        concept_id=sub.concept_id,
        quiz_title=sub.quiz_title,
        answers=answers_dicts,
        db=db
    )
