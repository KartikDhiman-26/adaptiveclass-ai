from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session

from app.csv_processor import parse_and_validate_csv
from app.assessment_repository import (
    save_assessment_dataset,
    get_dataset_by_id,
    get_assessment_records,
    records_to_dict_list,
    list_teacher_datasets
)
from app.performance_analyzer import analyze_records, analyze_historical_comparison
from app.pattern_detector import PatternDetector
from app.ai_insights import generate_assessment_pipeline_insights, TEACHER_DISCLAIMER


def format_structured_pipeline_output(
    dataset_metadata: Dict[str, Any],
    validation_report: Dict[str, Any],
    analytics: Dict[str, Any],
    patterns: List[Dict[str, Any]],
    historical: Dict[str, Any],
    ai_insights: Dict[str, Any],
    status: str = "success",
    message: str = "Assessment data processed and analyzed successfully."
) -> Dict[str, Any]:
    """
    Constructs the standardized, stable structured output contract for backend integration.
    """
    return {
        "status": status,
        "message": message,
        "dataset_metadata": dataset_metadata,
        "validation_results": {
            "total_rows": validation_report.get("total_uploaded_rows", 0),
            "accepted_rows": validation_report.get("accepted_rows", 0),
            "rejected_rows": validation_report.get("rejected_rows", 0),
            "duplicate_rows": validation_report.get("duplicate_rows", 0),
            "row_errors": validation_report.get("row_errors", []),
            "column_mapping": validation_report.get("detected_columns", {})
        },
        "class_analytics": {
            "overall_average": analytics.get("data_summary", {}).get("overall_percentage", 0.0),
            "median_average": analytics.get("data_summary", {}).get("median_percentage", 0.0),
            "highest_score": analytics.get("data_summary", {}).get("highest_percentage", 0.0),
            "lowest_score": analytics.get("data_summary", {}).get("lowest_percentage", 0.0),
            "student_count": analytics.get("data_summary", {}).get("total_students", 0),
            "assessment_records_count": analytics.get("data_summary", {}).get("total_assessments", 0),
            "performance_distribution": analytics.get("data_summary", {}).get("distribution", {}),
            "students_needing_support": [
                {
                    "rollno": s["rollno"],
                    "name": s["name"],
                    "average": s["average_percentage"],
                    "weaknesses": s.get("weaknesses", [])
                }
                for s in analytics.get("students_needing_support", [])
            ],
            "learning_gaps": analytics.get("learning_gaps", []),
            "strongest_topic": analytics.get("strongest_topic", ""),
            "weakest_topic": analytics.get("weakest_topic", "")
        },
        "student_analytics": analytics.get("student_analysis", []),
        "subject_analytics": analytics.get("subject_analysis", []),
        "topic_analytics": analytics.get("topic_analysis", []),
        "pattern_detection": patterns,
        "historical_comparison": historical,
        "ai_insights": ai_insights,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }


def process_assessment_csv(
    file_content: Union[bytes, str],
    teacher_id: int,
    db: Optional[Session] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    filename: str = "uploaded_assessment.csv",
    class_name: Optional[str] = None,
    subject: Optional[str] = None,
    assessment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Primary Public API Entry Point for Assessment Ingestion & Intelligence.

    End-to-End Workflow:
      1. Parse & validate CSV content with configurable column aliases and mappings.
      2. Detect duplicates and value boundary violations without fabricating missing data.
      3. If a database session is provided, persist the dataset and records atomically with teacher ownership.
      4. Retrieve preceding assessment records for this teacher/subject to compute longitudinal comparisons.
      5. Calculate deterministic classroom, student, subject, and topic analytics.
      6. Detect empirical learning patterns and pedagogical anomalies.
      7. Generate teacher-facing Gemini / fallback instructional recommendations.
      8. Return the complete, structured output contract.
    """
    # 1. Parse and validate CSV
    parsed = parse_and_validate_csv(file_content, column_mapping=column_mapping)
    if not parsed["success"]:
        return {
            "status": "error",
            "message": parsed.get("message", "CSV parsing and validation failed."),
            "validation_results": {
                "total_rows": parsed.get("total_uploaded_rows", 0),
                "accepted_rows": 0,
                "rejected_rows": parsed.get("rejected_rows", 0),
                "duplicate_rows": parsed.get("duplicate_rows", 0),
                "row_errors": parsed.get("row_errors", []),
                "column_mapping": parsed.get("detected_columns", {})
            },
            "class_analytics": None,
            "student_analytics": [],
            "subject_analytics": [],
            "topic_analytics": [],
            "pattern_detection": [],
            "historical_comparison": {"has_historical_data": False},
            "ai_insights": {
                "class_summary": "Unable to generate insights due to CSV validation errors.",
                "student_support_recommendations": [],
                "topic_recommendations": [],
                "actionable_teaching_recommendations": [],
                "teacher_disclaimer": TEACHER_DISCLAIMER
            },
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

    valid_records = parsed["valid_records"]

    # 2. Database Storage & Historical Retrieval (if DB session provided)
    dataset_id = None
    historical_records: List[Dict[str, Any]] = []

    if db is not None:
        # Determine subject/class filter for historical comparison
        rec_subjects = list({r["subject"] for r in valid_records})
        primary_subject = subject or (rec_subjects[0] if rec_subjects else None)
        rec_classes = list({r["class"] for r in valid_records})
        primary_class = class_name or (rec_classes[0] if rec_classes else None)

        # Retrieve prior records for this teacher before saving the current one
        prior_records = get_assessment_records(
            db=db,
            teacher_id=teacher_id,
            subject=primary_subject,
            class_name=primary_class
        )
        if prior_records:
            historical_records = records_to_dict_list(prior_records)

        # Save current dataset
        upload = save_assessment_dataset(
            db=db,
            teacher_id=teacher_id,
            filename=filename,
            valid_records=valid_records,
            class_name=primary_class,
            subject=primary_subject,
            assessment_name=assessment_name,
            column_mapping=column_mapping,
            total_uploaded_rows=parsed["total_uploaded_rows"],
            duplicate_rows=parsed["duplicate_rows"]
        )
        dataset_id = upload.id

    # 3. Deterministic Performance Analytics
    analytics = analyze_records(valid_records)

    # 4. Historical Comparison
    historical = analyze_historical_comparison(historical_records, valid_records)

    # 5. Intelligent Pattern Detection
    patterns = PatternDetector.detect_patterns(analytics, historical)

    # 6. Gemini / Fallback Teacher Insights
    ai_insights = generate_assessment_pipeline_insights(analytics, patterns, historical)

    # 7. Construct Metadata
    dataset_metadata = {
        "dataset_id": dataset_id,
        "filename": filename,
        "teacher_id": teacher_id,
        "class_name": class_name or (valid_records[0]["class"] if valid_records else "N/A"),
        "subject": subject or (valid_records[0]["subject"] if valid_records else "N/A"),
        "assessment_name": assessment_name or (valid_records[0]["assessment"] if valid_records else "N/A"),
        "total_records": parsed["total_uploaded_rows"],
        "valid_records": len(valid_records),
        "duplicate_records": parsed["duplicate_rows"],
        "upload_timestamp": datetime.now(timezone.utc).isoformat()
    }

    # 8. Return standardized structured contract
    return format_structured_pipeline_output(
        dataset_metadata=dataset_metadata,
        validation_report=parsed,
        analytics=analytics,
        patterns=patterns,
        historical=historical,
        ai_insights=ai_insights
    )


def analyze_existing_dataset(
    dataset_id: int,
    teacher_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Re-analyzes an existing, previously uploaded dataset from PostgreSQL
    without requiring CSV re-upload.
    """
    upload = get_dataset_by_id(db, dataset_id, teacher_id)
    if not upload:
        return {
            "status": "error",
            "message": f"Dataset #{dataset_id} not found or access is unauthorized for teacher #{teacher_id}."
        }

    records = get_assessment_records(db, teacher_id=teacher_id, dataset_id=dataset_id)
    if not records:
        return {
            "status": "error",
            "message": f"No assessment records associated with dataset #{dataset_id}."
        }

    dict_records = records_to_dict_list(records)

    # Historical retrieval (records before this dataset)
    prior_records = db.query(upload.__class__)\
        .filter(upload.__class__.teacher_id == teacher_id, upload.__class__.id < dataset_id)\
        .order_by(upload.__class__.id.desc()).first()

    historical_records = []
    if prior_records:
        h_records = get_assessment_records(db, teacher_id=teacher_id, dataset_id=prior_records.id)
        historical_records = records_to_dict_list(h_records)

    analytics = analyze_records(dict_records)
    historical = analyze_historical_comparison(historical_records, dict_records)
    patterns = PatternDetector.detect_patterns(analytics, historical)
    ai_insights = generate_assessment_pipeline_insights(analytics, patterns, historical)

    dataset_metadata = {
        "dataset_id": upload.id,
        "filename": upload.filename,
        "teacher_id": upload.teacher_id,
        "class_name": upload.class_name,
        "subject": upload.subject,
        "assessment_name": upload.assessment_name,
        "total_records": upload.total_records,
        "valid_records": upload.valid_records,
        "duplicate_records": upload.duplicate_records,
        "upload_timestamp": upload.upload_timestamp.isoformat() if upload.upload_timestamp else None
    }

    dummy_validation = {
        "total_uploaded_rows": upload.total_records,
        "accepted_rows": upload.valid_records,
        "rejected_rows": max(upload.total_records - upload.valid_records, 0),
        "duplicate_rows": upload.duplicate_records,
        "row_errors": [],
        "detected_columns": {}
    }

    return format_structured_pipeline_output(
        dataset_metadata=dataset_metadata,
        validation_report=dummy_validation,
        analytics=analytics,
        patterns=patterns,
        historical=historical,
        ai_insights=ai_insights
    )


def retrieve_historical_analysis(
    teacher_id: int,
    db: Session,
    class_name: Optional[str] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Performs longitudinal assessment analysis across all stored datasets for a teacher.
    Identifies multi-assessment trajectories, persistent weak topics, and student progress.
    """
    datasets = list_teacher_datasets(db, teacher_id)
    if len(datasets) < 2:
        return {
            "has_historical_data": False,
            "message": f"Historical analysis requires at least two uploaded assessment datasets. Currently found {len(datasets)} dataset(s).",
            "datasets_found": len(datasets),
            "timeline": []
        }

    # Chronologically sort datasets (oldest first)
    sorted_datasets = sorted(datasets, key=lambda d: d.upload_timestamp or datetime.min)

    dataset_analyses = []
    for d in sorted_datasets:
        recs = get_assessment_records(
            db=db,
            teacher_id=teacher_id,
            dataset_id=d.id,
            class_name=class_name,
            subject=subject
        )
        if recs:
            d_dict = records_to_dict_list(recs)
            d_analysis = analyze_records(d_dict)
            dataset_analyses.append({
                "dataset_id": d.id,
                "filename": d.filename,
                "assessment_name": d.assessment_name,
                "class_name": d.class_name,
                "subject": d.subject,
                "upload_timestamp": d.upload_timestamp.isoformat() if d.upload_timestamp else None,
                "average": d_analysis.get("data_summary", {}).get("overall_percentage", 0.0),
                "records": d_dict
            })

    if len(dataset_analyses) < 2:
        return {
            "has_historical_data": False,
            "message": "Insufficient matching records across datasets for the specified class/subject filters.",
            "datasets_found": len(dataset_analyses),
            "timeline": []
        }

    # Compare oldest with latest for overarching trend
    oldest = dataset_analyses[0]
    latest = dataset_analyses[-1]
    comparison = analyze_historical_comparison(oldest["records"], latest["records"])

    return {
        "has_historical_data": True,
        "total_datasets_compared": len(dataset_analyses),
        "timeline": [
            {
                "dataset_id": item["dataset_id"],
                "assessment_name": item["assessment_name"],
                "average": item["average"],
                "timestamp": item["upload_timestamp"]
            }
            for item in dataset_analyses
        ],
        "overall_shift": comparison.get("class_average_change", 0.0),
        "persistent_weak_topics": comparison.get("persistent_weak_topics", []),
        "improving_students": comparison.get("improving_students", []),
        "declining_students": comparison.get("declining_students", []),
        "topic_comparison": comparison.get("topic_comparison", [])
    }
