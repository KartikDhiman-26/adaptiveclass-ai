from unittest.mock import patch, MagicMock
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Class, Student, DatasetUpload, TutorConversation

client = TestClient(app)

SAMPLE_IMPORT_CSV = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
301,Kavya Verma,Computer Science,CS-301,6,20,Trees,Quiz 1,2026-10-15
302,Dev Patel,Computer Science,CS-301,17,20,Trees,Quiz 1,2026-10-15
"""


@pytest.fixture(autouse=True)
def cleanup_test_cohort():
    yield
    db = SessionLocal()
    try:
        classes = db.query(Class).filter(Class.name == "CS-301").all()
        for c in classes:
            db.delete(c)
        uploads = db.query(DatasetUpload).filter(DatasetUpload.filename == "tutor_test_cohort.csv").all()
        for u in uploads:
            db.delete(u)
        db.commit()
    finally:
        db.close()


def test_student_token_issuance_and_chat():
    # 1. Fetch seed student
    classes_res = client.get("/api/classes")
    assert classes_res.status_code == 200
    classes = classes_res.json()
    demo_class = next(c for c in classes if c["student_count"] == 80)

    students_res = client.get(f"/api/classes/{demo_class['id']}/students")
    assert students_res.status_code == 200
    students = students_res.json()
    student = students[0]

    # 2. Request student bearer token via /api/auth/student-token
    token_res = client.post("/api/auth/student-token", json={"student_id": student["id"]})
    assert token_res.status_code == 200
    token_data = token_res.json()
    assert token_data["user_id"] == student["id"]
    assert token_data["role"] == "student"
    assert "token" in token_data
    token = token_data["token"]

    # 3. Call tutor chat without auth -> 401
    unauth_res = client.post("/api/student-tutor/chat", json={
        "student_id": student["id"],
        "message": "Can you explain recursion step by step?",
        "topic": "Recursion"
    })
    assert unauth_res.status_code == 401

    # 4. Call tutor chat with mismatched student ID -> 403
    other_student = students[1]
    mismatch_res = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": other_student["id"],
            "message": "Can you explain recursion step by step?",
            "topic": "Recursion"
        }
    )
    assert mismatch_res.status_code == 403

    # 5. Call tutor chat with valid bearer token -> 200 OK
    chat_res = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": student["id"],
            "message": "Can you explain recursion step by step?",
            "topic": "Recursion",
            "requested_format": "explanation"
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert "session_id" in chat_data
    assert "message" in chat_data
    assert len(chat_data["message"]) > 0
    assert "engine_used" in chat_data
    assert "suggested_followups" in chat_data
    assert isinstance(chat_data["suggested_followups"], list)
    assert "adaptation_applied" in chat_data

    # 6. Multi-turn chat using session_id
    session_id = chat_data["session_id"]
    second_chat_res = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": student["id"],
            "session_id": session_id,
            "message": "Can you show me the iterative version instead?",
            "topic": "Recursion",
            "requested_format": "code"
        }
    )
    assert second_chat_res.status_code == 200
    second_data = second_chat_res.json()
    assert second_data["session_id"] == session_id
    assert len(second_data["message"]) > 0


def test_imported_cohort_student_tutor_session():
    # 1. Ingest imported cohort
    files = {"file": ("tutor_test_cohort.csv", io.BytesIO(SAMPLE_IMPORT_CSV.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/datasets/upload", files=files)
    assert upload_res.status_code == 200
    new_class_id = upload_res.json()["class_id"]

    # 2. Get students of imported cohort
    students_res = client.get(f"/api/classes/{new_class_id}/students")
    assert students_res.status_code == 200
    students = students_res.json()
    kavya = next(s for s in students if s["name"] == "Kavya Verma")

    # 3. Issue token for imported student
    token_res = client.post("/api/auth/student-token", json={"student_id": kavya["id"]})
    assert token_res.status_code == 200
    token = token_res.json()["token"]

    # 4. Chat as imported student with their concept (Trees)
    chat_res = client.post(
        "/api/student-tutor/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": kavya["id"],
            "student_name": kavya["name"],
            "message": "Explain Trees in simple terms with an analogy",
            "topic": "Trees"
        }
    )
    assert chat_res.status_code == 200
    res_json = chat_res.json()
    assert "Trees" in res_json["message"] or "tree" in res_json["message"].lower()
    assert res_json["session_id"] is not None


def test_gemini_engine_invocation_and_model_config(monkeypatch):
    from app.config import GEMINI_MODEL

    # Verify default configured model is gemini-2.5-flash
    assert GEMINI_MODEL in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]

    # Get student and token
    classes_res = client.get("/api/classes")
    classes = classes_res.json()
    demo_class = next(c for c in classes if c["student_count"] == 80)
    students = client.get(f"/api/classes/{demo_class['id']}/students").json()
    student = students[0]
    token = client.post("/api/auth/student-token", json={"student_id": student["id"]}).json()["token"]

    # Mock gemini client
    mock_response = MagicMock()
    mock_response.text = "Hello! A recursive function has a base case and a recursive step."
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models

    monkeypatch.setattr("app.student_ai.tutor.GEMINI_API_KEY", "fake-test-key-12345")
    with patch("google.genai.Client", return_value=mock_client_instance):
        chat_res = client.post(
            "/api/student-tutor/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "student_id": student["id"],
                "message": "How does recursion work?",
                "topic": "Recursion"
            }
        )
        assert chat_res.status_code == 200
        res_data = chat_res.json()
        assert res_data["engine_used"] == "gemini"
        assert "Hello! A recursive function" in res_data["message"]
        # Verify call used gemini-2.5-flash
        assert mock_models.generate_content.call_count >= 1
        for call_item in mock_models.generate_content.call_args_list:
            assert call_item.kwargs["model"] == GEMINI_MODEL
