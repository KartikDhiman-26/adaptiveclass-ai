import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Teacher, DatasetUpload, AssessmentRecord
from app.csv_processor import (
    parse_and_validate_csv,
    process_csv,
    normalize_header,
    parse_date_safely
)
from app.assessment_repository import (
    save_assessment_dataset,
    get_dataset_by_id,
    list_teacher_datasets,
    get_assessment_records,
    records_to_dict_list,
    delete_dataset
)
from app.performance_analyzer import (
    analyze_records,
    analyze_historical_comparison,
    get_performance_level,
    compute_distribution
)
from app.pattern_detector import PatternDetector
from app.ai_insights import (
    generate_assessment_pipeline_insights,
    TEACHER_DISCLAIMER
)
from app.ai_pipeline import (
    process_assessment_csv,
    analyze_existing_dataset,
    retrieve_historical_analysis
)


@pytest.fixture
def in_memory_db():
    """Provides an isolated in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Pre-seed a test teacher
    teacher = Teacher(
        name="Prof. Vikram Sen",
        email="vikram.sen@university.edu",
        department="Computer Science",
        hashed_password="mock_hashed_secret"
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    yield session, teacher
    session.close()


@pytest.fixture(autouse=True)
def use_deterministic_ai_insights():
    with patch("app.ai_insights.GEMINI_API_KEY", ""):
        yield


# ==============================================================================
# 1. CSV INGESTION & VALIDATION TESTS
# ==============================================================================

def test_header_normalization():
    assert normalize_header(" Roll Number ") == "roll_number"
    assert normalize_header("Marks_Obtained (Out of 100)") == "marks_obtained_out_of_100"
    assert normalize_header("TEST-NAME") == "test_name"


def test_date_parsing_variations():
    assert parse_date_safely("2026-10-20") == "2026-10-20"
    assert parse_date_safely("20-10-2026") == "2026-10-20"
    assert parse_date_safely("10/20/2026") == "2026-10-20"
    assert parse_date_safely("20/10/2026") == "2026-10-20"
    assert parse_date_safely("invalid-date-string") is None
    assert parse_date_safely("") is None


def test_csv_alias_recognition():
    csv_text = """Roll Number,Student Name,Subject Name,Class,Score,Total Marks,Topic,Test Name,Assessment Date
101,Aarav Sharma,Data Structures,CSE-A,18,20,Recursion,Quiz 1,2026-10-20
102,Diya Patel,Data Structures,CSE-A,16,20,Recursion,Quiz 1,2026-10-20
"""
    result = parse_and_validate_csv(csv_text)
    assert result["success"] is True
    assert result["accepted_rows"] == 2
    assert result["detected_columns"]["rollno"] == "Roll Number"
    assert result["detected_columns"]["marks"] == "Score"
    assert result["detected_columns"]["max_marks"] == "Total Marks"


def test_csv_explicit_column_mapping():
    csv_text = """RegID,FullName,Branch,Discipline,Points,OutOf,Concept,ExamType,DateDone
201,Priya Rao,Section B,Mathematics,45,50,Calculus,Exam 1,2026-11-01
"""
    mapping = {
        "rollno": "RegID",
        "name": "FullName",
        "class": "Branch",
        "subject": "Discipline",
        "marks": "Points",
        "max_marks": "OutOf",
        "topic": "Concept",
        "assessment": "ExamType",
        "date": "DateDone"
    }
    result = parse_and_validate_csv(csv_text, column_mapping=mapping)
    assert result["success"] is True
    assert result["accepted_rows"] == 1
    assert result["valid_records"][0]["rollno"] == "201"
    assert result["valid_records"][0]["percentage"] == 90.0


def test_csv_missing_required_columns():
    csv_text = "rollno,name,marks\n101,Aarav,18\n"
    result = parse_and_validate_csv(csv_text)
    assert result["success"] is False
    assert "Required columns are missing" in result["message"]
    assert "max_marks" in result["missing_columns"]
    assert "subject" in result["missing_columns"]


def test_csv_empty_content():
    assert parse_and_validate_csv("")["success"] is False
    assert parse_and_validate_csv("   \n  \n")["success"] is False


def test_csv_invalid_marks_boundary():
    # Negative marks and marks > max_marks
    csv_text = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
101,Aarav,Math,CSE-A,-5,20,Algebra,Quiz 1,2026-10-20
102,Diya,Math,CSE-A,25,20,Algebra,Quiz 1,2026-10-20
103,Rohan,Math,CSE-A,15,0,Algebra,Quiz 1,2026-10-20
"""
    result = parse_and_validate_csv(csv_text)
    assert result["success"] is False
    assert result["rejected_rows"] == 3
    errors = " ".join(result["row_errors"])
    assert "cannot be negative" in errors
    assert "cannot exceed maximum marks" in errors
    assert "greater than zero" in errors


def test_csv_duplicate_record_handling():
    csv_text = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
101,Aarav,Math,CSE-A,18,20,Algebra,Quiz 1,2026-10-20
101,Aarav,Math,CSE-A,18,20,Algebra,Quiz 1,2026-10-20
102,Diya,Math,CSE-A,15,20,Algebra,Quiz 1,2026-10-20
"""
    result = parse_and_validate_csv(csv_text)
    assert result["success"] is True
    assert result["accepted_rows"] == 2
    assert result["duplicate_rows"] == 1


# ==============================================================================
# 2. DATABASE REPOSITORY & ISOLATION TESTS
# ==============================================================================

def test_database_persistence_and_teacher_isolation(in_memory_db):
    session, teacher = in_memory_db

    # Create a second teacher
    teacher_2 = Teacher(name="Prof. Anita Roy", email="anita@test.edu", hashed_password="pw")
    session.add(teacher_2)
    session.commit()

    records = [
        {
            "rollno": "101", "name": "Aarav", "class": "CSE-A", "subject": "Data Structures",
            "topic": "Recursion", "assessment": "Quiz 1", "marks": 16.0, "max_marks": 20.0,
            "percentage": 80.0, "date": "2026-10-20"
        }
    ]

    upload = save_assessment_dataset(
        db=session,
        teacher_id=teacher.id,
        filename="ds_q1.csv",
        valid_records=records
    )

    assert upload.id is not None
    assert upload.teacher_id == teacher.id

    # Teacher 1 can access dataset
    fetched_1 = get_dataset_by_id(session, upload.id, teacher.id)
    assert fetched_1 is not None

    # Teacher 2 cannot access Teacher 1's dataset
    fetched_2 = get_dataset_by_id(session, upload.id, teacher_2.id)
    assert fetched_2 is None

    # Records retrieval isolation
    t1_records = get_assessment_records(session, teacher_id=teacher.id)
    assert len(t1_records) == 1

    t2_records = get_assessment_records(session, teacher_id=teacher_2.id)
    assert len(t2_records) == 0

    # Cascade delete
    deleted = delete_dataset(session, upload.id, teacher.id)
    assert deleted is True
    assert len(get_assessment_records(session, teacher_id=teacher.id)) == 0


# ==============================================================================
# 3. DETERMINISTIC PERFORMANCE ANALYZER TESTS
# ==============================================================================

def test_performance_classification():
    assert get_performance_level(92.0) == "Advanced"
    assert get_performance_level(75.0) == "Proficient"
    assert get_performance_level(55.0) == "Developing"
    assert get_performance_level(42.0) == "Needs Support"


def test_deterministic_analytics_calculations():
    records = [
        {"rollno": "101", "name": "Aarav", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q1", "marks": 8.0, "max_marks": 20.0, "date": "2026-10-20"},
        {"rollno": "102", "name": "Diya", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q1", "marks": 18.0, "max_marks": 20.0, "date": "2026-10-20"},
        {"rollno": "103", "name": "Rohan", "class": "CSE-A", "subject": "Math", "topic": "Algebra", "assessment": "Q1", "marks": 16.0, "max_marks": 20.0, "date": "2026-10-20"}
    ]
    # Total marks = 42, Total max = 60. Overall = 70.0%
    result = analyze_records(records)
    assert result["success"] is True
    summary = result["data_summary"]
    assert summary["overall_percentage"] == 70.0
    assert summary["total_students"] == 3
    assert summary["total_assessments"] == 3

    # Student needing support (Aarav: 8/20 = 40.0% < 50%)
    needing_support = result["students_needing_support"]
    assert len(needing_support) == 1
    assert needing_support[0]["rollno"] == "101"


def test_historical_assessment_comparison():
    past_records = [
        {"rollno": "101", "name": "Aarav", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q1", "marks": 8.0, "max_marks": 20.0, "date": "2026-10-10"},
        {"rollno": "102", "name": "Diya", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q1", "marks": 14.0, "max_marks": 20.0, "date": "2026-10-10"}
    ]
    current_records = [
        {"rollno": "101", "name": "Aarav", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q2", "marks": 16.0, "max_marks": 20.0, "date": "2026-10-24"},
        {"rollno": "102", "name": "Diya", "class": "CSE-A", "subject": "Math", "topic": "Calculus", "assessment": "Q2", "marks": 15.0, "max_marks": 20.0, "date": "2026-10-24"}
    ]

    hist = analyze_historical_comparison(past_records, current_records)
    assert hist["has_historical_data"] is True
    assert hist["class_average_change"] == 22.5  # 55.0% -> 77.5% (+22.5%)
    assert len(hist["improving_students"]) == 1
    assert hist["improving_students"][0]["rollno"] == "101"
    assert hist["improving_students"][0]["change"] == 40.0


# ==============================================================================
# 4. PATTERN DETECTION TESTS
# ==============================================================================

def test_pattern_detection_rules():
    analytics = {
        "success": True,
        "data_summary": {"overall_percentage": 65.0},
        "topic_analysis": [
            {
                "name": "Recursion",
                "subject": "Data Structures",
                "percentage": 34.0,
                "struggling_students_percentage": 45.0,
                "struggling_students_count": 10,
                "students_assessed": 22
            }
        ],
        "subject_analysis": [],
        "student_analysis": [
            {
                "rollno": "101",
                "name": "Aarav Sharma",
                "average_percentage": 38.0,
                "weaknesses": ["Recursion"],
                "assessments_count": 2
            }
        ]
    }
    historical = {
        "has_historical_data": True,
        "persistent_weak_topics": ["Recursion"],
        "improving_students": [{"rollno": "102", "name": "Diya", "past_average": 60.0, "current_average": 78.0, "change": 18.0}],
        "declining_students": [{"rollno": "103", "name": "Rohan", "past_average": 82.0, "current_average": 64.0, "change": -18.0}],
        "student_progressions": [{"rollno": "102", "name": "Diya", "past_average": 60.0, "current_average": 90.0, "change": 30.0}]
    }

    patterns = PatternDetector.detect_patterns(analytics, historical)
    types = [p["pattern_type"] for p in patterns]

    assert "CRITICAL_LEARNING_GAP" in types
    assert "CONSISTENTLY_WEAK_STUDENT" in types
    assert "REPEATEDLY_WEAK_TOPIC" in types
    assert "IMPROVING_STUDENT" in types
    assert "DECLINING_STUDENT" in types
    assert "UNUSUAL_PERFORMANCE_CHANGE" in types

    # Verify transparent evidence format
    for p in patterns:
        assert p["evidence"] != ""
        assert p["rule"] != ""
        assert p["recommended_action"] != ""


# ==============================================================================
# 5. AI INSIGHTS & DETERMINISTIC FALLBACK TESTS
# ==============================================================================

@patch("app.ai_insights.GEMINI_API_KEY", "")
def test_ai_insights_rule_based_fallback():
    analytics = {
        "success": True,
        "data_summary": {
            "overall_percentage": 68.5,
            "total_students": 30,
            "distribution": {"advanced": 5, "needs_support": 4}
        },
        "topic_analysis": [
            {"name": "Trees", "percentage": 39.0, "revision_priority": "critical", "struggling_students_percentage": 40.0}
        ],
        "students_needing_support": [
            {"name": "Aarav", "rollno": "101", "average_percentage": 42.0, "weaknesses": ["Trees"]}
        ]
    }
    patterns = [
        {"pattern_type": "CRITICAL_LEARNING_GAP", "entity_name": "Trees", "evidence": "Class topic avg 39%"}
    ]

    insights = generate_assessment_pipeline_insights(analytics, patterns)
    assert insights["generated_by"] == "Autonomous Rule-Based Engine"
    assert "68.5%" in insights["class_summary"]
    assert len(insights["student_support_recommendations"]) >= 1
    assert len(insights["actionable_teaching_recommendations"]) >= 2
    assert insights["teacher_disclaimer"] == TEACHER_DISCLAIMER


# ==============================================================================
# 6. END-TO-END PIPELINE INTEGRATION TESTS
# ==============================================================================

def test_end_to_end_pipeline_workflow(in_memory_db):
    session, teacher = in_memory_db

    csv_data = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
101,Aarav Sharma,Data Structures,CSE-A,8,20,Recursion,Quiz 1,2026-10-10
102,Diya Patel,Data Structures,CSE-A,14,20,Recursion,Quiz 1,2026-10-10
103,Rohan Verma,Data Structures,CSE-A,18,20,Recursion,Quiz 1,2026-10-10
"""

    # 1. First Upload
    result_1 = process_assessment_csv(
        file_content=csv_data,
        teacher_id=teacher.id,
        db=session,
        filename="quiz_1.csv"
    )

    assert result_1["status"] == "success"
    assert result_1["class_analytics"]["overall_average"] == 66.67
    assert result_1["class_analytics"]["student_count"] == 3
    ds_id_1 = result_1["dataset_metadata"]["dataset_id"]
    assert ds_id_1 is not None

    # 2. Second Upload for Longitudinal Comparison
    csv_data_2 = """rollno,name,subject,class,marks,max_marks,topic,assessment,date
101,Aarav Sharma,Data Structures,CSE-A,16,20,Recursion,Quiz 2,2026-10-24
102,Diya Patel,Data Structures,CSE-A,15,20,Recursion,Quiz 2,2026-10-24
103,Rohan Verma,Data Structures,CSE-A,19,20,Recursion,Quiz 2,2026-10-24
"""
    result_2 = process_assessment_csv(
        file_content=csv_data_2,
        teacher_id=teacher.id,
        db=session,
        filename="quiz_2.csv"
    )

    assert result_2["status"] == "success"
    hist = result_2["historical_comparison"]
    assert hist["has_historical_data"] is True
    assert hist["class_average_change"] > 0
    assert len(hist["improving_students"]) == 1
    assert hist["improving_students"][0]["rollno"] == "101"

    # 3. Test analyze_existing_dataset
    stored_analysis = analyze_existing_dataset(ds_id_1, teacher.id, session)
    assert stored_analysis["status"] == "success"
    assert stored_analysis["dataset_metadata"]["dataset_id"] == ds_id_1

    # 4. Test retrieve_historical_analysis
    longitudinal = retrieve_historical_analysis(teacher.id, session)
    assert longitudinal["has_historical_data"] is True
    assert longitudinal["total_datasets_compared"] == 2
