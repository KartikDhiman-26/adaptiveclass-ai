import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import DatasetUpload, AssessmentRecord


def save_assessment_dataset(
    db: Session,
    teacher_id: int,
    filename: str,
    valid_records: List[Dict[str, Any]],
    class_name: Optional[str] = None,
    subject: Optional[str] = None,
    assessment_name: Optional[str] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    total_uploaded_rows: int = 0,
    duplicate_rows: int = 0
) -> DatasetUpload:
    """
    Stores a validated assessment dataset and its individual assessment records
    within a single atomic database transaction.
    Enforces teacher ownership and dataset isolation.
    """
    if not valid_records:
        raise ValueError("Cannot persist an empty assessment dataset.")

    # Infer metadata from records if not explicitly passed
    classes = {r["class"] for r in valid_records if "class" in r}
    subjects = {r["subject"] for r in valid_records if "subject" in r}
    assessments = {r["assessment"] for r in valid_records if "assessment" in r}

    resolved_class = class_name or (list(classes)[0] if len(classes) == 1 else "Multiple Classes")
    resolved_subject = subject or (list(subjects)[0] if len(subjects) == 1 else "Multiple Subjects")
    resolved_assessment = assessment_name or (list(assessments)[0] if len(assessments) == 1 else "Multiple Assessments")

    try:
        # Create dataset upload metadata record
        upload = DatasetUpload(
            teacher_id=teacher_id,
            filename=filename,
            class_name=resolved_class,
            subject=resolved_subject,
            assessment_name=resolved_assessment,
            total_records=total_uploaded_rows or len(valid_records),
            valid_records=len(valid_records),
            duplicate_records=duplicate_rows,
            status="completed",
            upload_timestamp=datetime.now(timezone.utc),
            column_mapping=json.dumps(column_mapping) if column_mapping else None
        )
        db.add(upload)
        db.flush()  # Generates upload.id for foreign key assignment

        # Bulk create assessment records
        records_to_create = []
        for r in valid_records:
            marks = float(r["marks"])
            max_marks = float(r["max_marks"])
            percentage = round((marks / max_marks) * 100.0, 2)

            rec = AssessmentRecord(
                dataset_upload_id=upload.id,
                teacher_id=teacher_id,
                roll_number=str(r["rollno"]).strip(),
                student_name=str(r["name"]).strip(),
                class_name=str(r["class"]).strip(),
                subject=str(r["subject"]).strip(),
                topic=str(r["topic"]).strip(),
                assessment_name=str(r["assessment"]).strip(),
                marks_obtained=marks,
                max_marks=max_marks,
                percentage=percentage,
                assessment_date=str(r["date"]).strip()
            )
            records_to_create.append(rec)

        db.add_all(records_to_create)
        db.commit()
        db.refresh(upload)
        return upload

    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Failed to persist assessment dataset: {exc}") from exc


def get_dataset_by_id(
    db: Session,
    dataset_id: int,
    teacher_id: int
) -> Optional[DatasetUpload]:
    """
    Retrieve a specific dataset by ID strictly enforcing teacher ownership.
    Returns None if the dataset does not exist or belongs to another teacher.
    """
    return db.query(DatasetUpload).filter(
        DatasetUpload.id == dataset_id,
        DatasetUpload.teacher_id == teacher_id
    ).first()


def list_teacher_datasets(
    db: Session,
    teacher_id: int
) -> List[DatasetUpload]:
    """Retrieve all uploaded datasets belonging to a specific teacher."""
    return db.query(DatasetUpload).filter(
        DatasetUpload.teacher_id == teacher_id
    ).order_by(DatasetUpload.upload_timestamp.desc()).all()


def get_assessment_records(
    db: Session,
    teacher_id: int,
    dataset_id: Optional[int] = None,
    class_name: Optional[str] = None,
    student_roll: Optional[str] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    assessment_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[AssessmentRecord]:
    """
    Retrieves filtered assessment records strictly scoped to the authenticated teacher.
    Supports historical analysis by allowing querying across multiple datasets.
    """
    query = db.query(AssessmentRecord).filter(
        AssessmentRecord.teacher_id == teacher_id
    )

    if dataset_id is not None:
        query = query.filter(AssessmentRecord.dataset_upload_id == dataset_id)
    if class_name:
        query = query.filter(AssessmentRecord.class_name == class_name)
    if student_roll:
        query = query.filter(AssessmentRecord.roll_number == student_roll)
    if subject:
        query = query.filter(AssessmentRecord.subject == subject)
    if topic:
        query = query.filter(AssessmentRecord.topic == topic)
    if assessment_name:
        query = query.filter(AssessmentRecord.assessment_name == assessment_name)
    if start_date:
        query = query.filter(AssessmentRecord.assessment_date >= start_date)
    if end_date:
        query = query.filter(AssessmentRecord.assessment_date <= end_date)

    return query.order_by(
        AssessmentRecord.assessment_date.asc(),
        AssessmentRecord.roll_number.asc()
    ).all()


def records_to_dict_list(records: List[AssessmentRecord]) -> List[Dict[str, Any]]:
    """Convert a list of AssessmentRecord ORM instances to a clean dictionary list."""
    return [
        {
            "id": r.id,
            "dataset_upload_id": r.dataset_upload_id,
            "teacher_id": r.teacher_id,
            "rollno": r.roll_number,
            "name": r.student_name,
            "class": r.class_name,
            "subject": r.subject,
            "topic": r.topic,
            "assessment": r.assessment_name,
            "marks": r.marks_obtained,
            "max_marks": r.max_marks,
            "percentage": r.percentage,
            "date": r.assessment_date
        }
        for r in records
    ]


def delete_dataset(
    db: Session,
    dataset_id: int,
    teacher_id: int
) -> bool:
    """
    Deletes a dataset and all associated assessment records (via cascade).
    Enforces teacher isolation.
    """
    upload = get_dataset_by_id(db, dataset_id, teacher_id)
    if not upload:
        return False
    db.delete(upload)
    db.commit()
    return True
