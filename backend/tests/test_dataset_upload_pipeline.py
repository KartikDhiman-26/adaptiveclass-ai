import io
import os
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Class, DatasetUpload

client = TestClient(app)

SAMPLE_CSV = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
101,Aarav Sharma,Data Structures,CSE-A,8,20,Recursion,Quiz 1,2026-10-10
102,Diya Patel,Data Structures,CSE-A,18,20,Recursion,Quiz 1,2026-10-10
103,Rohan Verma,Data Structures,CSE-A,14,20,Recursion,Quiz 1,2026-10-10
104,Meera Singh,Data Structures,CSE-A,6,20,Trees,Quiz 1,2026-10-10
105,Kabir Kumar,Data Structures,CSE-A,17,20,Trees,Quiz 1,2026-10-10
"""


@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    db = SessionLocal()
    try:
        test_classes = db.query(Class).filter(Class.name == "CSE-A").all()
        for tc in test_classes:
            db.delete(tc)
        test_datasets = (
            db.query(DatasetUpload)
            .filter(
                DatasetUpload.filename.in_(
                    ["sample.csv", "sample_assessment.csv"]
                )
            )
            .all()
        )
        for td in test_datasets:
            db.delete(td)
        db.commit()
    finally:
        db.close()


def test_dataset_validate_endpoint():
    files = {"file": ("sample.csv", io.BytesIO(SAMPLE_CSV.encode("utf-8")), "text/csv")}
    res = client.post("/api/datasets/validate", files=files)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["valid"] is True
    assert data["row_count"] == 5
    assert "rollno" in data["detected_columns"]
    assert data["class_name"] == "CSE-A"
    assert data["subject"] == "Data Structures"


def test_dataset_upload_end_to_end():
    # 1. Upload sample CSV
    files = {"file": ("sample_assessment.csv", io.BytesIO(SAMPLE_CSV.encode("utf-8")), "text/csv")}
    res = client.post("/api/datasets/upload", files=files)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["row_count"] == 5
    assert data["class_name"] == "CSE-A"
    assert data["subject"] == "Data Structures"
    assert data["student_count"] == 5
    new_class_id = data["class_id"]
    assert new_class_id is not None

    # 2. Verify classes list reflects new class
    classes_res = client.get("/api/classes")
    assert classes_res.status_code == 200
    classes = classes_res.json()
    found_class = next((c for c in classes if c["id"] == new_class_id), None)
    assert found_class is not None
    assert found_class["name"] == "CSE-A"
    assert found_class["student_count"] == 5

    # 3. Verify analytics for imported class
    analytics_res = client.get(f"/api/classes/{new_class_id}/analytics")
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert analytics["student_count"] == 5
    assert len(analytics["concept_mastery"]) >= 2
    concept_names = [c["concept_name"] for c in analytics["concept_mastery"]]
    assert "Recursion" in concept_names
    assert "Trees" in concept_names

    # 4. Verify seed class with 80 students remains untouched
    demo_class = next((c for c in classes if c["student_count"] == 80), None)
    assert demo_class is not None
    demo_analytics = client.get(f"/api/classes/{demo_class['id']}/analytics").json()
    assert demo_analytics["student_count"] == 80
    assert demo_analytics["weakest_concept"] == "Recursion"
    assert demo_analytics["recursion_support_count"] == 23


def test_dataset_validate_multi_sheet_excel():
    excel_path = os.path.join(os.path.dirname(__file__), "..", "..", "Datasets", "COLLEGE 1.xlsx")
    if not os.path.exists(excel_path):
        pytest.skip("COLLEGE 1.xlsx not found")

    with open(excel_path, "rb") as f:
        files = {"file": ("COLLEGE 1.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res = client.post("/api/datasets/validate", files=files)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["valid"] is True
        assert data["row_count"] > 30000
        assert "roll_number" in data["detected_columns"]
        assert data["class_name"] is not None
