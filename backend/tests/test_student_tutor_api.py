"""
Tests for Student AI Tutor API Router functions.
Directly tests the route handler functions for chat, quiz start, quiz answer,
topic listing, and profile fetching.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.database import get_db
from app.routers.student_tutor import (
    list_available_topics, tutor_chat, start_tutor_quiz, answer_tutor_quiz,
    get_student_learner_profile, get_tutor_conversation, get_tutor_quiz_session,
    _restore_practice_session, router
)
from app.models import (
    Class, Concept, ConceptPerformance, QuizAttempt, Student, Teacher,
    TutorPracticeSession
)
from app.security import create_access_token, hash_password
from app.schemas import (
    TutorChatRequest, TutorQuizStartRequest, TutorQuizAnswerRequest
)

@pytest.fixture(autouse=True)
def default_mock_gemini_key():
    """Ensures deterministic, fast unit tests without unmocked live network calls."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        yield


@pytest.fixture
def tutor_student(db_session):
    teacher = Teacher(
        name="Tutor Test Teacher",
        email="tutor-teacher@example.test",
        hashed_password=hash_password("password")
    )
    db_session.add(teacher)
    db_session.flush()
    class_group = Class(
        name="Tutor Test Class",
        subject="Computer Science",
        semester="Fall",
        teacher_id=teacher.id
    )
    db_session.add(class_group)
    db_session.flush()
    student = Student(
        name="Aarav",
        email="aarav@example.test",
        roll_number="TUTOR-001",
        class_id=class_group.id,
        hashed_password=hash_password("password")
    )
    db_session.add(student)
    db_session.commit()
    return student


@pytest.fixture
def tutor_client(db_session, tutor_student):
    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        token = create_access_token({
            "sub": tutor_student.email,
            "role": "student",
            "id": tutor_student.id
        })
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client

def test_api_list_topics():
    topics = list_available_topics()
    assert isinstance(topics, list)
    assert "Recursion" in topics
    assert "Arrays" in topics

def test_api_tutor_chat(db_session, tutor_student):
    req = TutorChatRequest(
        student_id=tutor_student.id,
        message="Can you explain how recursion works step by step?"
    )
    res = tutor_chat(req=req, db=db_session, current_student=tutor_student)
    assert res.message is not None
    assert "Recursion" in res.message or "base case" in res.message.lower()
    assert len(res.suggested_followups) > 0

def test_api_tutor_chat_confusion_adaptation(db_session, tutor_student):
    req = TutorChatRequest(
        student_id=tutor_student.id,
        message="I don't understand this, I'm completely confused!"
    )
    res = tutor_chat(req=req, db=db_session, current_student=tutor_student)
    assert res.detected_cue == "CONFUSION"
    assert "analogy" in res.message.lower() or "simplify" in res.adaptation_applied.lower()

def test_api_quiz_workflow(db_session, tutor_student):

    # 1. Start quiz on Recursion
    start_req = TutorQuizStartRequest(
        topic="Recursion",
        student_id=tutor_student.id,
        starting_difficulty="beginner"
    )
    start_res = start_tutor_quiz(req=start_req, db=db_session, current_student=tutor_student)
    assert start_res.topic == "Recursion"
    assert start_res.current_difficulty == "beginner"
    assert start_res.first_question is not None
    session_id = start_res.session_id
    q_id = start_res.first_question.question_id
    restored = get_tutor_quiz_session(
        session_id=session_id, student_id=tutor_student.id,
        db=db_session, current_student=tutor_student
    )
    assert restored.current_question.question_id == q_id

    # 2. Answer question
    ans_req = TutorQuizAnswerRequest(
        session_id=session_id,
        student_id=tutor_student.id,
        topic="Recursion",
        question_id=q_id,
        selected_option="B",
        current_difficulty="beginner"
    )
    ans_res = answer_tutor_quiz(req=ans_req, db=db_session, current_student=tutor_student)
    assert ans_res.is_correct in [True, False]
    assert ans_res.explanation is not None
    assert ans_res.difficulty_change in ["increased", "maintained", "reinforced"]
    with pytest.raises(HTTPException) as exc_info:
        answer_tutor_quiz(req=ans_req, db=db_session, current_student=tutor_student)
    assert exc_info.value.status_code == 409

def test_api_learner_profile_fallback(db_session, tutor_student):
    profile_dict = get_student_learner_profile(
        student_id=tutor_student.id, db=db_session, current_student=tutor_student
    )
    assert profile_dict["student_name"] == tutor_student.name
    assert profile_dict["has_historical_data"] is False
    assert profile_dict["learning_level"] == "Beginner"


def test_chat_context_is_saved_and_restored_per_session(db_session, tutor_student):
    first = tutor_chat(
        TutorChatRequest(
            student_id=tutor_student.id,
            message="Explain recursion"
        ),
        db=db_session, current_student=tutor_student
    )
    second = tutor_chat(
        TutorChatRequest(
            student_id=tutor_student.id,
            session_id=first.session_id,
            message="Show me pseudocode"
        ),
        db=db_session, current_student=tutor_student
    )

    conversation = get_tutor_conversation(
        session_id=first.session_id,
        student_id=tutor_student.id,
        db=db_session, current_student=tutor_student
    )
    assert second.session_id == first.session_id
    assert second.response_format == "pseudocode"
    assert "FUNCTION factorial" in second.message
    assert conversation.current_topic == "Recursion"
    assert [message.role for message in conversation.messages] == [
        "user", "assistant", "user", "assistant"
    ]


def test_chat_session_cannot_be_loaded_by_another_student(db_session, tutor_student):
    first = tutor_chat(
        TutorChatRequest(student_id=tutor_student.id, message="Explain arrays"),
        db=db_session, current_student=tutor_student
    )

    second_student = Student(
        name="Priya",
        email="priya@example.test",
        roll_number="TUTOR-002",
        class_id=tutor_student.class_id,
        hashed_password=hash_password("password")
    )
    db_session.add(second_student)
    db_session.flush()
    with pytest.raises(HTTPException) as exc_info:
        get_tutor_conversation(
            session_id=first.session_id,
            student_id=second_student.id,
            db=db_session, current_student=second_student
        )
    assert exc_info.value.status_code == 404


def test_chat_can_start_quiz_from_current_conversation_topic(db_session, tutor_student):
    chat = tutor_chat(
        TutorChatRequest(student_id=tutor_student.id, message="Explain arrays"),
        db=db_session, current_student=tutor_student
    )

    quiz = start_tutor_quiz(
        TutorQuizStartRequest(
            chat_session_id=chat.session_id,
            student_id=tutor_student.id
        ),
        db=db_session, current_student=tutor_student
    )
    assert quiz.topic == "Arrays"
    assert quiz.first_question.topic == "Arrays"


def test_http_learning_flow_restores_chat_and_active_quiz(tutor_client, tutor_student):
    chat_response = tutor_client.post(
        "/api/student-tutor/chat",
        json={"student_id": tutor_student.id, "message": "Explain recursion"}
    )
    assert chat_response.status_code == 200
    chat_data = chat_response.json()

    followup_response = tutor_client.post(
        "/api/student-tutor/chat",
        json={
            "student_id": tutor_student.id,
            "session_id": chat_data["session_id"],
            "message": "Show pseudocode"
        }
    )
    assert followup_response.status_code == 200
    assert followup_response.json()["response_format"] == "pseudocode"

    history_response = tutor_client.get(
        f"/api/student-tutor/sessions/{chat_data['session_id']}?student_id={tutor_student.id}"
    )
    assert history_response.status_code == 200
    assert len(history_response.json()["messages"]) == 4

    quiz_response = tutor_client.post(
        "/api/student-tutor/quiz/start",
        json={
            "student_id": tutor_student.id,
            "chat_session_id": chat_data["session_id"]
        }
    )
    assert quiz_response.status_code == 200
    quiz_data = quiz_response.json()
    assert quiz_data["topic"] == "Recursion"

    resume_response = tutor_client.get(
        f"/api/student-tutor/quiz/{quiz_data['session_id']}?student_id={tutor_student.id}"
    )
    assert resume_response.status_code == 200
    assert resume_response.json()["current_question"]["question_id"] == (
        quiz_data["first_question"]["question_id"]
    )


def test_http_tutor_requires_a_student_token(tutor_client, tutor_student):
    response = tutor_client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": "Bearer invalid"},
        json={"student_id": tutor_student.id, "message": "Explain recursion"}
    )
    assert response.status_code == 401


def test_http_tutor_rejects_student_id_spoofing(tutor_client, db_session, tutor_student):
    other_student = Student(
        name="Priya",
        email="priya@example.test",
        roll_number="TUTOR-002",
        class_id=tutor_student.class_id,
        hashed_password=hash_password("password")
    )
    db_session.add(other_student)
    db_session.flush()
    token = create_access_token({
        "sub": other_student.email,
        "role": "student",
        "id": other_student.id
    })
    response = tutor_client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"student_id": tutor_student.id, "message": "Explain recursion"}
    )
    assert response.status_code == 403


@patch("app.student_ai.quiz_generator.GEMINI_API_KEY", "")
def test_unknown_quiz_topic_does_not_fall_back_to_unrelated_question(db_session, tutor_student):
    with pytest.raises(HTTPException) as exc_info:
        start_tutor_quiz(
            TutorQuizStartRequest(student_id=tutor_student.id, topic="Quantum Mechanics"),
            db=db_session, current_student=tutor_student
        )
    assert exc_info.value.status_code == 404


def test_completed_tutor_quiz_updates_persistent_student_mastery(db_session):
    teacher = Teacher(
        name="Teacher",
        email="teacher@example.test",
        hashed_password="not-a-real-password"
    )
    db_session.add(teacher)
    db_session.flush()
    class_group = Class(
        name="Test Class",
        subject="Computer Science",
        semester="Fall",
        teacher_id=teacher.id
    )
    db_session.add(class_group)
    db_session.flush()
    student = Student(
        name="Aarav",
        email="aarav@example.test",
        roll_number="TEST-001",
        class_id=class_group.id,
        hashed_password="not-a-real-password"
    )
    concept = Concept(name="Recursion")
    db_session.add_all([student, concept])
    db_session.flush()
    db_session.add(ConceptPerformance(
        student_id=student.id,
        concept_id=concept.id,
        mastery_score=40.0,
        attempt_count=2,
        correct_count=3
    ))
    db_session.commit()
    student_id = student.id
    concept_id = concept.id

    start = start_tutor_quiz(
        TutorQuizStartRequest(
            student_id=student_id,
            topic="Recursion",
            starting_difficulty="beginner"
        ),
        db=db_session, current_student=student
    )

    final_answer = None
    for _ in range(start.total_questions):
        record = db_session.query(TutorPracticeSession).filter(
            TutorPracticeSession.id == start.session_id
        ).one()
        db_session.expunge_all()
        session = _restore_practice_session(record)
        current_student = db_session.query(Student).filter(
            Student.id == student_id
        ).one()
        question = session.pending_question
        assert question is not None
        final_answer = answer_tutor_quiz(
            TutorQuizAnswerRequest(
                session_id=start.session_id,
                student_id=student_id,
                topic="Recursion",
                question_id=question.question_id,
                selected_option=question.correct_answer,
                current_difficulty=session.current_difficulty
            ),
            db=db_session, current_student=current_student
        )

    assert final_answer is not None and final_answer.is_complete
    updated = db_session.query(ConceptPerformance).filter(
        ConceptPerformance.student_id == student_id,
        ConceptPerformance.concept_id == concept_id
    ).one()
    attempt = db_session.query(QuizAttempt).filter(
        QuizAttempt.student_id == student_id
    ).one()
    assert updated.mastery_score == 79.0
    assert updated.attempt_count == 3
    assert updated.correct_count == 8
    assert attempt.score == 5
    assert attempt.accuracy == 100.0
