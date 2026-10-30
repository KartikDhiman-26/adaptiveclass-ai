"""
Regression tests for:
1. Active cohort analytics isolation (ensuring imported school classes do not leak demo Recursion/Data Structures values).
2. Missing-data handling (empty cohorts return clean empty state without crashing or demo leakage).
3. Student tutor runtime status endpoint and mocked Gemini SDK integration.
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Class, Student, Concept, ConceptPerformance, Teacher
from app.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture
def school_cohort_db():
    db = SessionLocal()
    teacher = db.query(Teacher).first()
    teacher_id = teacher.id if teacher else 1

    # 1. Create a dedicated School Class (e.g. Class 9A - Mathematics)
    school_class = Class(
        name="Class 9A - Secondary",
        subject="Mathematics",
        semester="Academic Year 2026-2027",
        teacher_id=teacher_id
    )
    db.add(school_class)
    db.flush()

    # 2. Add 3 school students
    students = []
    for i, name in enumerate(["Aarush Gupta", "Bhavna Joshi", "Chetan Rao"], start=1):
        s = Student(
            name=name,
            email=f"school_student_{i}_{school_class.id}@school.edu",
            roll_number=f"SCH_{school_class.id}_{i}",
            class_id=school_class.id,
            hashed_password=hash_password("password123")
        )
        db.add(s)
        students.append(s)
    db.flush()

    # 3. Add school-specific concepts (NOT Data Structures / Recursion)
    num_systems = Concept(
        name="Number Systems",
        subject="Mathematics",
        description="Real numbers, irrationality proofs, and decimal expansions.",
        order_index=1
    )
    polynomials = Concept(
        name="Polynomials",
        subject="Mathematics",
        description="Degree, zeros, and remainder theorem.",
        order_index=2
    )
    db.add_all([num_systems, polynomials])
    db.flush()

    # 4. Add concept performance:
    # Number Systems: 35% (weakest, 2 students below 40%)
    # Polynomials: 78% (strongest)
    db.add(ConceptPerformance(student_id=students[0].id, concept_id=num_systems.id, mastery_score=30.0, attempt_count=2, correct_count=1))
    db.add(ConceptPerformance(student_id=students[1].id, concept_id=num_systems.id, mastery_score=35.0, attempt_count=2, correct_count=1))
    db.add(ConceptPerformance(student_id=students[2].id, concept_id=num_systems.id, mastery_score=40.0, attempt_count=2, correct_count=1))

    db.add(ConceptPerformance(student_id=students[0].id, concept_id=polynomials.id, mastery_score=75.0, attempt_count=2, correct_count=2))
    db.add(ConceptPerformance(student_id=students[1].id, concept_id=polynomials.id, mastery_score=80.0, attempt_count=2, correct_count=2))
    db.add(ConceptPerformance(student_id=students[2].id, concept_id=polynomials.id, mastery_score=80.0, attempt_count=2, correct_count=2))

    # 5. Empty class with no students or concepts
    empty_class = Class(
        name="Class 11C - Physics (Unassigned)",
        subject="Physics",
        semester="Academic Year 2026-2027",
        teacher_id=teacher_id
    )
    db.add(empty_class)
    db.commit()

    cohort_info = {
        "school_class_id": school_class.id,
        "empty_class_id": empty_class.id,
        "first_student_id": students[0].id,
        "first_student_email": students[0].email
    }

    try:
        yield cohort_info
    finally:
        # Cleanup isolated test cohort
        db.query(ConceptPerformance).filter(ConceptPerformance.student_id.in_([s.id for s in students])).delete(synchronize_session=False)
        db.query(Student).filter(Student.class_id == school_class.id).delete(synchronize_session=False)
        db.query(Concept).filter(Concept.id.in_([num_systems.id, polynomials.id])).delete(synchronize_session=False)
        db.query(Class).filter(Class.id.in_([school_class.id, empty_class.id])).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_school_cohort_analytics_isolation(school_cohort_db):
    """
    Verifies that querying analytics for a School cohort returns strictly
    its own concepts and statistics, without leaking demo engineering records.
    """
    class_id = school_cohort_db["school_class_id"]
    res = client.get(f"/api/classes/{class_id}/analytics")
    assert res.status_code == 200, res.text
    data = res.json()

    # 1. Total student count is strictly 3, NOT 80
    assert data["student_count"] == 3
    assert data["subject"] == "Mathematics"
    assert data["class_name"] == "Class 9A - Secondary"

    # 2. Concept names are strictly Mathematics concepts
    concept_names = [c["concept_name"] for c in data["concept_mastery"]]
    assert "Number Systems" in concept_names
    assert "Polynomials" in concept_names
    assert "Recursion" not in concept_names
    assert "Arrays" not in concept_names
    assert "Data Structures" not in concept_names

    # 3. Weakest concept is Number Systems (not Recursion)
    assert data["weakest_concept"] == "Number Systems"
    assert data["strongest_concept"] == "Polynomials"

    # 4. Bottleneck support count is exactly 2 students (< 40% in Number Systems), NOT 23
    assert data["recursion_support_count"] == 2

    # 5. AI Insight references Mathematics and Number Systems
    insight = data["ai_insight"]
    assert "Number Systems" in insight["what"]
    assert "Recursion" not in insight["what"]


def test_empty_cohort_analytics_graceful_handling(school_cohort_db):
    """
    Verifies that an empty cohort returns a valid 0-metric payload without crashing
    or substituting demo values.
    """
    empty_id = school_cohort_db["empty_class_id"]
    res = client.get(f"/api/classes/{empty_id}/analytics")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["student_count"] == 0
    assert data["overall_class_average"] == 0.0
    assert data["concept_mastery"] == []
    assert data["weakest_concept"] == ""
    assert data["strongest_concept"] == ""
    assert data["recursion_support_count"] == 0
    assert data["global_distribution"]["total"] == 0


def test_tutor_status_endpoint():
    """Verifies the GET /api/student-tutor/status endpoint returns safe config info."""
    res = client.get("/api/student-tutor/status")
    assert res.status_code == 200
    data = res.json()
    assert "gemini_configured" in data
    assert "model" in data
    assert "mode" in data
    assert "active_engine" in data
    assert isinstance(data["gemini_configured"], bool)


def test_tutor_mocked_gemini_integration(school_cohort_db):
    """
    Verifies that when Gemini is available, the tutor endpoint utilizes Gemini,
    returns engine_used == 'gemini', and preserves student identity.
    """
    student_id = school_cohort_db["first_student_id"]
    token = create_access_token({"sub": school_cohort_db["first_student_email"], "role": "student", "id": student_id})

    # Mock genai.Client
    mock_response = MagicMock()
    mock_response.text = "This is a real-time Socratic explanation of Number Systems generated by Gemini."

    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = mock_response

    with patch("app.student_ai.tutor.GEMINI_API_KEY", "mock_key_for_test"), \
         patch("google.genai.Client", return_value=mock_client_instance):
        payload = {
            "student_id": student_id,
            "student_name": "Aarush Gupta",
            "message": "Can you explain Number Systems to me?",
            "topic": "Number Systems"
        }
        res = client.post(
            "/api/student-tutor/chat",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["engine_used"] == "gemini"
        assert "Gemini" in data["message"] or "Number Systems" in data["message"]


def test_tutor_offline_fallback_does_not_fabricate_recursion(school_cohort_db):
    """
    Verifies that when offline, asking about a school topic like Number Systems
    explains offline mode rather than substituting Recursion.
    """
    student_id = school_cohort_db["first_student_id"]
    token = create_access_token({"sub": school_cohort_db["first_student_email"], "role": "student", "id": student_id})

    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        payload = {
            "student_id": student_id,
            "student_name": "Aarush Gupta",
            "message": "Can you explain Number Systems to me?",
            "topic": "Number Systems"
        }
        res = client.post(
            "/api/student-tutor/chat",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["engine_used"] == "offline_fallback"
        # Must not fabricate Russian dolls or factorial recursion
        assert "Russian nesting dolls" not in data["message"]
        assert "factorial" not in data["message"]
        assert "Offline Pedagogical Mode" in data["message"]
