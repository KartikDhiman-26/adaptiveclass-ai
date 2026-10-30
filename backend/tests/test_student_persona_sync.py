import io
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Class, DatasetUpload

client = TestClient(app)

SAMPLE_CSV = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
201,Ishaan Gupta,Data Structures,CSE-B,9,20,Recursion,Quiz 1,2026-10-12
202,Anika Joshi,Data Structures,CSE-B,18,20,Recursion,Quiz 1,2026-10-12
203,Rishi Nair,Data Structures,CSE-B,14,20,Recursion,Quiz 1,2026-10-12
204,Tanvi Sen,Data Structures,CSE-B,7,20,Trees,Quiz 1,2026-10-12
"""


@pytest.fixture(autouse=True)
def cleanup_persona_test_data():
    yield
    db = SessionLocal()
    try:
        test_classes = db.query(Class).filter(Class.name == "CSE-B").all()
        for tc in test_classes:
            db.delete(tc)
        test_datasets = (
            db.query(DatasetUpload)
            .filter(DatasetUpload.filename == "sample_persona.csv")
            .all()
        )
        for td in test_datasets:
            db.delete(td)
        db.commit()
    finally:
        db.close()


def test_seed_cohort_students_list():
    classes_res = client.get("/api/classes")
    assert classes_res.status_code == 200
    classes = classes_res.json()
    demo_class = next((c for c in classes if c["student_count"] == 80), None)
    assert demo_class is not None, "Seeded demo class with 80 students must exist"

    students_res = client.get(f"/api/classes/{demo_class['id']}/students")
    assert students_res.status_code == 200
    students = students_res.json()
    assert len(students) == 80

    first_student = students[0]
    for key in ["id", "name", "roll_number", "email", "overall_mastery", "status_label", "weak_concept"]:
        assert key in first_student

    # Verify student profile endpoint
    prof_res = client.get(f"/api/students/{first_student['id']}/profile")
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert prof["student_name"] == first_student["name"]
    assert prof["overall_mastery"] == first_student["overall_mastery"]


def test_cohort_switch_and_student_persona_sync():
    # 1. Ingest imported cohort CSE-B
    files = {"file": ("sample_persona.csv", io.BytesIO(SAMPLE_CSV.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/datasets/upload", files=files)
    assert upload_res.status_code == 200
    up_data = upload_res.json()
    new_class_id = up_data["class_id"]
    assert new_class_id is not None
    assert up_data["class_name"] == "CSE-B"
    assert up_data["student_count"] == 4

    # 2. Verify students list for new cohort returns exactly its 4 students
    students_res = client.get(f"/api/classes/{new_class_id}/students")
    assert students_res.status_code == 200
    students = students_res.json()
    assert len(students) == 4

    student_names = [s["name"] for s in students]
    assert "Ishaan Gupta" in student_names
    assert "Anika Joshi" in student_names
    assert "Rishi Nair" in student_names
    assert "Tanvi Sen" in student_names

    # 3. Verify downstream requests for imported student
    ishaan = next(s for s in students if s["name"] == "Ishaan Gupta")
    
    # Profile
    p_res = client.get(f"/api/students/{ishaan['id']}/profile")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["student_name"] == "Ishaan Gupta"
    assert p_data["roll_number"] == "201"
    assert p_data["current_learning_gap"] == "Recursion"

    # Recommendations
    rec_res = client.get(f"/api/students/{ishaan['id']}/recommendations")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["weak_concept"] == "Recursion"

    # Adaptive Quiz Start
    quiz_res = client.post("/api/quiz/adaptive/start", json={"student_id": ishaan["id"]})
    assert quiz_res.status_code == 200
    q_data = quiz_res.json()
    assert q_data["concept_name"] == "Recursion"
    assert "current_question" in q_data

    # 4. Verify seed cohort remains isolated with 80 students
    classes = client.get("/api/classes").json()
    demo_class = next(c for c in classes if c["student_count"] == 80)
    demo_students = client.get(f"/api/classes/{demo_class['id']}/students").json()
    assert len(demo_students) == 80
    assert "Ishaan Gupta" not in [s["name"] for s in demo_students]

