import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Student, Concept, ConceptPerformance, Question

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "postgresql"

def test_auth_login():
    # Teacher login
    res = client.post("/api/auth/login", json={"email": "teacher@demo.com", "password": "password"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "teacher"
    assert "token" in data

    # Student login (Aarav)
    res_student = client.post("/api/auth/login", json={"email": "student@demo.com", "password": "password"})
    assert res_student.status_code == 200
    s_data = res_student.json()
    assert s_data["role"] == "student"
    assert s_data["name"] == "Aarav Sharma"

def test_class_analytics():
    # Fetch actual class id
    classes_res = client.get("/api/classes")
    assert classes_res.status_code == 200
    classes = classes_res.json()
    assert len(classes) > 0
    class_id = classes[0]["id"]

    res = client.get(f"/api/classes/{class_id}/analytics")
    assert res.status_code == 200
    data = res.json()
    assert data["student_count"] == 80
    assert data["weakest_concept"] == "Recursion"
    assert data["recursion_support_count"] == 23

    # Check concepts
    concepts = {c["concept_name"]: c["mastery_percentage"] for c in data["concept_mastery"]}
    assert abs(concepts["Arrays"] - 82.0) < 0.2
    assert abs(concepts["Recursion"] - 35.0) < 0.2
    assert abs(concepts["Trees"] - 41.0) < 0.2
    assert abs(concepts["Linked Lists"] - 64.0) < 0.2

    # Check AI insight structure
    insight = data["ai_insight"]
    assert "Recursion" in insight["what"]
    assert "23" in insight["why"]
    assert "base cases" in insight["suggested_action"].lower()
    assert insight["teacher_disclaimer"] is not None

def test_adaptive_quiz_and_mastery_feedback_loop():
    # 1. Reset demo data first to ensure clean state
    reset_res = client.post("/api/demo/reset")
    assert reset_res.status_code == 200

    classes_res = client.get("/api/classes")
    class_id = classes_res.json()[0]["id"]

    # 2. Start adaptive quiz for Aarav
    aarav_res = client.post("/api/auth/login", json={"email": "student@demo.com", "password": "password"})
    aarav_id = aarav_res.json()["user_id"]

    start_res = client.post("/api/quiz/adaptive/start", json={"student_id": aarav_id})
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["concept_name"] == "Recursion"
    assert start_data["difficulty"] == "beginner"
    first_q = start_data["current_question"]

    # 3. Answer correctly -> Check difficulty escalates to intermediate
    next_req = {
        "student_id": aarav_id,
        "concept_id": start_data["concept_id"],
        "current_question_id": first_q["question_id"],
        "selected_option": "B",  # correct base case answer in seed
        "current_difficulty": "beginner",
        "question_index": 1,
        "answered_question_ids": []
    }
    next_res = client.post("/api/quiz/adaptive/next-question", json=next_req)
    assert next_res.status_code == 200
    next_data = next_res.json()
    assert next_data["is_correct"] is True
    assert next_data["difficulty_change"] == "increased"
    assert next_data["next_question"]["difficulty"] == "intermediate"
    second_q = next_data["next_question"]

    # 4. Submit a completed practice quiz with 4/5 (80% accuracy)
    # Aarav's old mastery is 28.0%
    # Expected new mastery = round(28.0 * 0.35 + 80.0 * 0.65, 1) = round(9.8 + 52.0) = 61.8%
    db = SessionLocal()
    try:
        rec_questions = db.query(Question).filter(Question.concept_id == start_data["concept_id"]).all()
        q_ids = [q.id for q in rec_questions[:5]]
    finally:
        db.close()

    submit_req = {
        "student_id": aarav_id,
        "concept_id": start_data["concept_id"],
        "quiz_title": "Adaptive Recursion Practice - Session 1",
        "answers": [
            {"question_id": q_ids[0], "selected_answer": "B", "is_correct": True},
            {"question_id": q_ids[1], "selected_answer": "B", "is_correct": True},
            {"question_id": q_ids[2], "selected_answer": "A", "is_correct": True},
            {"question_id": q_ids[3], "selected_answer": "B", "is_correct": True},
            {"question_id": q_ids[4], "selected_answer": "B", "is_correct": False},
        ]
    }
    submit_res = client.post("/api/quiz/submit", json=submit_req)
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["score"] == 4
    assert sub_data["total_questions"] == 5
    assert sub_data["accuracy"] == 80.0
    assert sub_data["old_mastery"] == 28.0
    assert sub_data["new_mastery"] == 61.8
    assert sub_data["mastery_change"] == 33.8

    # 5. Verify database recomputed class analytics:
    # Since Aarav's mastery is now 61.8% (which is >= 40%), the count of students < 40% drops from 23 to 22!
    assert sub_data["new_recursion_support_count"] == 22
    assert sub_data["new_class_recursion_average"] > 35.0

    # Query class analytics API again to verify persistence in PostgreSQL
    analytics_after = client.get(f"/api/classes/{class_id}/analytics").json()
    assert analytics_after["recursion_support_count"] == 22
    assert analytics_after["overall_class_average"] >= 59.0

    # 6. Reset demo data again to restore baseline for further testing
    reset_after = client.post("/api/demo/reset")
    assert reset_after.status_code == 200
    new_class_id = client.get("/api/classes").json()[0]["id"]
    analytics_restored = client.get(f"/api/classes/{new_class_id}/analytics").json()
    assert analytics_restored["recursion_support_count"] == 23
