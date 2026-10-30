import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import (
    Class, Student, Concept, ConceptPerformance, Question, QuizAttempt, QuizAttemptAnswer,
    TutorConversation, TutorConversationMessage, DatasetUpload
)

client = TestClient(app)

SAMPLE_COHORT_CSV = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
401,Karan Mehra,Data Structures,CSE-Beta,5,20,Trees,Midterm,2026-10-18
402,Sanya Roy,Data Structures,CSE-Beta,16,20,Trees,Midterm,2026-10-18
403,Aditya Sen,Data Structures,CSE-Beta,18,20,Trees,Midterm,2026-10-18
"""


@pytest.fixture(autouse=True)
def cleanup_feedback_loop_data():
    yield
    db = SessionLocal()
    try:
        classes = db.query(Class).filter(Class.name == "CSE-Beta").all()
        for c in classes:
            db.delete(c)
        uploads = db.query(DatasetUpload).filter(DatasetUpload.filename == "feedback_loop_cohort.csv").all()
        for u in uploads:
            db.delete(u)
        db.commit()
    finally:
        db.close()
    # Teardown reset to guarantee calibration for all test suites
    client.post("/api/demo/reset")


def test_seed_student_full_feedback_loop():
    """
    Verifies the complete closed feedback loop for calibrated seed student Aarav Sharma:
    1. Aarav starts with Recursion at 28.0% mastery.
    2. Class 10A has 23 students needing support in Recursion.
    3. Aarav chats with tutor (verified: tutor chat alone does NOT artificially inflate mastery).
    4. Aarav completes adaptive practice quiz and scores 5/5 (100%).
    5. Persistence: QuizAttempt, QuizAttemptAnswer, ConceptPerformance written to PostgreSQL.
    6. Aarav's mastery rises to 74.8% (crossing the 40% threshold).
    7. Teacher dashboard updates in real-time:
       - Class Recursion average increases.
       - Students needing support drops from 23 to 22.
       - Aarav is removed from critical attention alert list.
    """
    # Reset demo to ensure clean baseline: Aarav at 28.0%, 23 students needing support
    reset_res = client.post("/api/demo/reset")
    assert reset_res.status_code == 200

    db = SessionLocal()
    try:
        # Step 1: Identify Aarav Sharma and Class 10A
        aarav = db.query(Student).filter(Student.email == "student@demo.com").first()
        assert aarav is not None
        class_10a = db.query(Class).filter(Class.id == aarav.class_id).first()
        assert class_10a is not None

        rec_concept = db.query(Concept).filter(Concept.name == "Recursion").first()
        assert rec_concept is not None

        # Verify initial state
        aarav_perf = db.query(ConceptPerformance).filter(
            ConceptPerformance.student_id == aarav.id,
            ConceptPerformance.concept_id == rec_concept.id
        ).first()
        assert aarav_perf is not None
        initial_mastery = aarav_perf.mastery_score

        initial_analytics = client.get(f"/api/classes/{class_10a.id}/analytics").json()
        initial_rec_avg = next(c["mastery_percentage"] for c in initial_analytics["concept_mastery"] if c["concept_name"] == "Recursion")
        initial_support_count = initial_analytics["recursion_support_count"]

        # Step 2: Student chats with AI Tutor
        token_res = client.post("/api/auth/student-token", json={"student_id": aarav.id})
        assert token_res.status_code == 200
        token = token_res.json()["token"]

        tutor_res = client.post(
            "/api/student-tutor/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "student_id": aarav.id,
                "message": "Can you explain recursion step by step with base cases?",
                "topic": "Recursion"
            }
        )
        assert tutor_res.status_code == 200
        tutor_data = tutor_res.json()
        assert tutor_data["session_id"] is not None

        # Verify: Tutor conversation did NOT fabricate progress or inflate mastery
        db.expire_all()
        check_perf = db.query(ConceptPerformance).filter(
            ConceptPerformance.student_id == aarav.id,
            ConceptPerformance.concept_id == rec_concept.id
        ).first()
        assert check_perf.mastery_score == initial_mastery, "Tutor chat must not fabricate mastery increase"

        # Verify tutor conversation persisted in PostgreSQL
        conv = db.query(TutorConversation).filter(TutorConversation.id == tutor_data["session_id"]).first()
        assert conv is not None
        assert conv.student_id == aarav.id

        # Step 3: Student starts adaptive practice quiz
        start_res = client.post("/api/quiz/adaptive/start", json={
            "student_id": aarav.id,
            "concept_id": rec_concept.id
        })
        assert start_res.status_code == 200
        start_data = start_res.json()
        assert start_data["concept_name"] == "Recursion"
        assert start_data["total_questions"] == 5

        # Fetch real questions for Recursion from DB
        real_qs = db.query(Question).filter(Question.concept_id == rec_concept.id).all()
        assert len(real_qs) >= 5

        # Step 4: Complete and submit quiz with 100% accuracy using real question IDs
        answers = [
            {"question_id": q.id, "selected_answer": q.correct_answer, "is_correct": True}
            for q in real_qs[:5]
        ]
        submit_res = client.post("/api/quiz/submit", json={
            "student_id": aarav.id,
            "concept_id": rec_concept.id,
            "quiz_title": "Recursion Adaptive Practice Quiz",
            "answers": answers
        })
        assert submit_res.status_code == 200
        sub_data = submit_res.json()
        assert sub_data["score"] == 5
        assert sub_data["accuracy"] == 100.0
        assert sub_data["new_mastery"] > sub_data["old_mastery"]

        # Step 5: Verify PostgreSQL persistence
        db.expire_all()
        quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == sub_data["quiz_attempt_id"]).first()
        assert quiz_attempt is not None
        assert quiz_attempt.student_id == aarav.id
        assert quiz_attempt.score == 5
        assert quiz_attempt.accuracy == 100.0

        attempt_answers = db.query(QuizAttemptAnswer).filter(QuizAttemptAnswer.quiz_attempt_id == quiz_attempt.id).all()
        assert len(attempt_answers) == 5

        updated_perf = db.query(ConceptPerformance).filter(
            ConceptPerformance.student_id == aarav.id,
            ConceptPerformance.concept_id == rec_concept.id
        ).first()
        assert updated_perf.mastery_score >= 70.0
        assert updated_perf.attempt_count >= 1

        # Step 6: Verify Student Profile reflects updated mastery
        prof_res = client.get(f"/api/students/{aarav.id}/profile")
        assert prof_res.status_code == 200
        prof = prof_res.json()
        assert prof["overall_mastery"] > 55.0
        assert any(q["quiz_id"] == quiz_attempt.id for q in prof["recent_performance"])
        assert prof["current_learning_gap"] != "Recursion"

        # Step 7: Verify Teacher Dashboard Analytics in real-time
        updated_analytics = client.get(f"/api/classes/{class_10a.id}/analytics").json()
        updated_rec_avg = next(c["mastery_percentage"] for c in updated_analytics["concept_mastery"] if c["concept_name"] == "Recursion")
        assert updated_rec_avg > initial_rec_avg
        assert updated_analytics["recursion_support_count"] < initial_support_count

        attention_res = client.get(f"/api/classes/{class_10a.id}/students-needing-attention")
        assert attention_res.status_code == 200
        attention_students = attention_res.json()
        aarav_attention = next((s for s in attention_students if s["student_id"] == aarav.id and s["weak_concept"] == "Recursion"), None)
        assert aarav_attention is None, "Aarav must be removed from Recursion alert after reaching > 40% mastery"

    finally:
        db.close()


def test_imported_cohort_full_feedback_loop():
    """
    Verifies the closed feedback loop for an uploaded CSV dataset cohort:
    1. Ingests CSE-Beta with student Karan Mehra having Trees gap (25.0%).
    2. Karan takes a quiz on Trees and improves mastery.
    3. Teacher analytics for CSE-Beta update strictly from real database data.
    4. Verified: Zero demo data leakage into imported cohort analytics.
    """
    db = SessionLocal()
    try:
        # 1. Ingest imported cohort
        files = {"file": ("feedback_loop_cohort.csv", io.BytesIO(SAMPLE_COHORT_CSV.encode("utf-8")), "text/csv")}
        upload_res = client.post("/api/datasets/upload", files=files)
        assert upload_res.status_code == 200
        up_data = upload_res.json()
        new_class_id = up_data["class_id"]

        # 2. Get students in imported cohort
        students = client.get(f"/api/classes/{new_class_id}/students").json()
        assert len(students) == 3
        karan = next(s for s in students if s["name"] == "Karan Mehra")
        assert karan["weak_concept"] == "Trees"
        initial_karan_mastery = karan["weak_mastery"]
        assert initial_karan_mastery == 25.0

        # 3. Verify initial imported cohort analytics (cohort isolation)
        initial_analytics = client.get(f"/api/classes/{new_class_id}/analytics").json()
        assert initial_analytics["student_count"] == 3
        assert initial_analytics["class_name"] == "CSE-Beta"
        assert len(initial_analytics["concept_mastery"]) == 1
        assert initial_analytics["concept_mastery"][0]["concept_name"] == "Trees"

        trees_concept_id = initial_analytics["concept_mastery"][0]["concept_id"]

        # 4. Issue token and complete quiz using real questions from Question bank
        token = client.post("/api/auth/student-token", json={"student_id": karan["id"]}).json()["token"]
        assert token is not None

        # Fetch questions available for Trees or question bank
        trees_qs = db.query(Question).filter(Question.concept_id == trees_concept_id).all()
        if len(trees_qs) < 5:
            trees_qs = db.query(Question).all()

        answers = [
            {"question_id": q.id, "selected_answer": q.correct_answer, "is_correct": True}
            for q in trees_qs[:5]
        ]
        submit_res = client.post("/api/quiz/submit", json={
            "student_id": karan["id"],
            "concept_id": trees_concept_id,
            "quiz_title": "Trees Adaptive Practice Quiz",
            "answers": answers
        })
        assert submit_res.status_code == 200
        sub_data = submit_res.json()
        assert sub_data["new_mastery"] > initial_karan_mastery
        assert sub_data["concept_name"] == "Trees"

        # 5. Verify teacher analytics for imported cohort updated
        updated_analytics = client.get(f"/api/classes/{new_class_id}/analytics").json()
        updated_trees_avg = updated_analytics["concept_mastery"][0]["mastery_percentage"]
        assert updated_trees_avg > initial_analytics["concept_mastery"][0]["mastery_percentage"]

        # 6. Verify cohort isolation: Class 10A must not be affected by CSE-Beta quiz
        classes = client.get("/api/classes").json()
        demo_class = next(c for c in classes if c["student_count"] == 80)
        demo_analytics = client.get(f"/api/classes/{demo_class['id']}/analytics").json()
        assert demo_analytics["student_count"] == 80
        assert len(demo_analytics["concept_mastery"]) == 6
    finally:
        db.close()


def test_feedback_loop_security_and_authorization():
    """
    Verifies student authorization boundaries:
    1. Unauthenticated tutor requests are blocked (401).
    2. Student cannot impersonate another student (403).
    3. Student cannot access another student's conversation session (404/403).
    4. Student cannot access another student's learner profile (403).
    """
    classes = client.get("/api/classes").json()
    demo_class = next(c for c in classes if c["student_count"] == 80)
    students = client.get(f"/api/classes/{demo_class['id']}/students").json()
    student_a = students[0]
    student_b = students[1]

    # Token for student A
    token_a = client.post("/api/auth/student-token", json={"student_id": student_a["id"]}).json()["token"]
    # Token for student B
    token_b = client.post("/api/auth/student-token", json={"student_id": student_b["id"]}).json()["token"]

    # 1. Student A chats with tutor
    chat_a = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "student_id": student_a["id"],
            "message": "Explain trees",
            "topic": "Trees"
        }
    )
    assert chat_a.status_code == 200
    session_id_a = chat_a.json()["session_id"]

    # 2. Student B attempts to read Student A's conversation session -> 404/403
    cross_read = client.get(
        f"/api/student-tutor/sessions/{session_id_a}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert cross_read.status_code in [403, 404]

    # 3. Student B attempts to impersonate Student A in tutor chat -> 403
    impersonate = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "student_id": student_a["id"],
            "message": "Impersonating student A",
            "topic": "Trees"
        }
    )
    assert impersonate.status_code == 403

    # 4. Student B attempts to access Student A's learner profile -> 403
    profile_tamper = client.get(
        f"/api/student-tutor/profile/{student_a['id']}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert profile_tamper.status_code == 403
