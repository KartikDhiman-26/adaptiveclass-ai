import csv
import datetime
import io
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.ai_service import analyze_dataset
from app.database import get_db
from app.dependencies import current_staff
from app.models import (
    AnalysisResult,
    Class,
    Concept,
    ConceptPerformance,
    DatasetRow,
    DatasetUpload,
    Student,
    Teacher,
)
from app.schemas import (
    DatasetAnalysisResponse,
    DatasetRowResponse,
    DatasetUploadDetailResponse,
    DatasetUploadResponse,
    DatasetValidationResponse,
)
from app.security import hash_password

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

CANONICAL_ALIASES = {
    "roll_number": ["roll_number", "rollno", "roll_no", "roll", "student_id", "enrollment_no", "id"],
    "name": ["name", "student_name", "student", "full_name"],
    "subject": ["subject", "course", "subject_name"],
    "class": ["class", "class_name", "section", "grade", "cohort", "program"],
    "marks": ["marks", "marks_obtained", "score", "score_obtained"],
    "max_marks": ["max_marks", "max_marks_total", "total_marks", "out_of"],
    "topic": ["topic", "concept", "chapter", "module"],
    "assessment": ["assessment", "assessment_name", "quiz", "test", "exam"],
    "date": ["date", "assessment_date", "exam_date", "created_at"],
}


def _read_rows(filename: str, content: bytes) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "json":
        payload = json.loads(content.decode("utf-8"))
        rows = payload.get("rows") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("JSON must contain an array or an object with a rows array")
        return rows, None
    if suffix == "csv":
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        return [dict(r) for r in reader], None
    if suffix in {"xlsx", "xlsm"}:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet_candidates = ["student_marks", "marks", "assessments", "scores", "data", "sheet1"]
        target_sheet_name = None
        for cand in sheet_candidates:
            for sname in workbook.sheetnames:
                if sname.strip().lower() == cand:
                    target_sheet_name = sname
                    break
            if target_sheet_name:
                break
        if not target_sheet_name:
            for sname in workbook.sheetnames:
                if not any(k in sname.strip().lower() for k in ["readme", "instruction", "about", "note"]):
                    target_sheet_name = sname
                    break
        if not target_sheet_name:
            target_sheet_name = workbook.sheetnames[0]
        sheet = workbook[target_sheet_name]
        values = sheet.iter_rows(values_only=True)
        try:
            raw_headers = next(values)
            headers = [str(value).strip() if value is not None else "" for value in raw_headers]
        except StopIteration as exc:
            raise ValueError("Spreadsheet is empty") from exc
        rows = []
        for row in values:
            if not any(cell is not None and str(cell).strip() != "" for cell in row):
                continue
            row_dict = {}
            for h, cell in zip(headers, row):
                if not h:
                    continue
                if isinstance(cell, (datetime.date, datetime.datetime)):
                    cell = cell.isoformat()
                row_dict[h] = cell
            rows.append(row_dict)
        return rows, target_sheet_name
    raise ValueError("Only .xlsx, .xlsm, .csv, and .json files are supported")


def _normalize_row(raw: Dict[str, Any], row_number: int) -> Dict[str, Any]:
    values = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
    mapped: Dict[str, Any] = {}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            if alias in values and values[alias] is not None and str(values[alias]).strip() != "":
                mapped[canonical] = values[alias]
                break

    missing = [req for req in ["roll_number", "name", "marks", "max_marks"] if req not in mapped]
    if missing:
        raise ValueError(f"missing columns: {', '.join(sorted(missing))}")

    roll_number = str(mapped["roll_number"]).strip()
    name = str(mapped["name"]).strip()
    subject = str(mapped.get("subject", "Data Structures")).strip() or "Data Structures"
    class_name = str(mapped.get("class", "Class 10A")).strip() or "Class 10A"

    if not all((roll_number, name)):
        raise ValueError("roll_number and name are required")

    try:
        marks = float(mapped["marks"])
        max_marks = float(mapped["max_marks"])
    except (ValueError, TypeError):
        raise ValueError("marks and max_marks must be valid numeric values")

    if max_marks <= 0 or marks < 0 or marks > max_marks:
        raise ValueError("marks must be between 0 and max_marks")

    topic = str(mapped.get("topic", "General")).strip() if mapped.get("topic") is not None else "General"
    assessment = str(mapped.get("assessment", "Assessment 1")).strip() if mapped.get("assessment") is not None else "Assessment 1"
    raw_date = mapped.get("date")
    assessment_date = str(raw_date).strip() if raw_date is not None else None

    return {
        "roll_number": roll_number,
        "student_name": name,
        "subject": subject,
        "class_name": class_name,
        "marks": marks,
        "max_marks": max_marks,
        "topic": topic,
        "assessment": assessment,
        "assessment_date": assessment_date,
        "_row_number": row_number,
    }


def _can_access(dataset: DatasetUpload, claims: Dict[str, Any]) -> bool:
    return (
        claims.get("role") in {"mentor", "teacher"}
        or claims.get("id") == dataset.uploaded_by_id
    )


def _upload_response(dataset: DatasetUpload) -> DatasetUploadResponse:
    return DatasetUploadResponse(
        id=dataset.id,
        filename=dataset.filename,
        file_type=dataset.file_type,
        status=dataset.status,
        row_count=dataset.row_count,
        error_count=dataset.error_count,
        uploaded_at=dataset.uploaded_at,
    )


@router.post("/validate", response_model=DatasetValidationResponse)
async def validate_dataset(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A dataset file is required")
    try:
        content = await file.read()
        raw_rows, sheet_name = _read_rows(file.filename, content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"File parse error: {str(exc)}") from exc

    if not raw_rows:
        raise HTTPException(status_code=422, detail="No rows found in uploaded file")

    first_row = raw_rows[0]
    detected_columns = [str(k) for k in first_row.keys() if k]

    normalized_sample: List[Dict[str, Any]] = []
    sample_errors: List[Dict[str, Any]] = []
    check_limit = min(len(raw_rows), 100)
    valid_count = 0
    for idx in range(check_limit):
        row_num = idx + 2
        try:
            norm = _normalize_row(raw_rows[idx], row_num)
            valid_count += 1
            if len(normalized_sample) < 5:
                normalized_sample.append(norm)
        except Exception as exc:
            if len(sample_errors) < 5:
                sample_errors.append({"row": row_num, "error": str(exc)})

    sample_class = normalized_sample[0]["class_name"] if normalized_sample else None
    sample_subject = normalized_sample[0]["subject"] if normalized_sample else None

    is_valid = valid_count > 0 and len(sample_errors) < (check_limit // 2)

    return DatasetValidationResponse(
        valid=is_valid,
        row_count=len(raw_rows),
        detected_columns=detected_columns,
        class_name=sample_class,
        subject=sample_subject,
        sample_errors=sample_errors,
    )


@router.post("/upload", response_model=DatasetUploadDetailResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A dataset file is required")
    try:
        content = await file.read()
        raw_rows, sheet_name = _read_rows(file.filename, content)
        normalized: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        for row_number, raw in enumerate(raw_rows, start=2):
            try:
                normalized.append(_normalize_row(dict(raw), row_number))
            except (TypeError, ValueError) as exc:
                if len(errors) < 50:
                    errors.append({"row": row_number, "error": str(exc)})
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not normalized:
        raise HTTPException(
            status_code=422,
            detail={"message": "No valid dataset rows found", "errors": errors},
        )

    # Resolve a valid teacher_id for foreign keys
    teacher = db.query(Teacher).filter(Teacher.id == claims.get("id")).first()
    if not teacher:
        teacher = db.query(Teacher).first()
    if not teacher:
        teacher = Teacher(
            name="Prof. Vikram Sen",
            email="teacher@demo.com",
            department="Computer Science & Engineering",
            hashed_password=hash_password("password"),
        )
        db.add(teacher)
        db.flush()
    teacher_id = teacher.id

    suffix = file.filename.lower().rsplit(".", 1)[-1]
    dataset = DatasetUpload(
        filename=file.filename,
        file_type=suffix,
        uploaded_by_id=teacher_id,
        uploaded_by_role=claims.get("role", "teacher"),
        status="processed_with_errors" if errors else "processed",
        row_count=len(normalized),
        error_count=len(errors),
    )
    db.add(dataset)
    db.flush()

    # 1. Bulk insert DatasetRow mappings in chunks of 1000
    chunk_size = 1000
    for i in range(0, len(normalized), chunk_size):
        chunk = normalized[i : i + chunk_size]
        records = [
            {
                "dataset_id": dataset.id,
                "roll_number": r["roll_number"],
                "student_name": r["student_name"],
                "subject": r["subject"],
                "class_name": r["class_name"],
                "marks": r["marks"],
                "max_marks": r["max_marks"],
                "topic": r["topic"],
                "assessment": r["assessment"],
                "assessment_date": r["assessment_date"],
            }
            for r in chunk
        ]
        db.bulk_insert_mappings(DatasetRow, records)

    # 2. Sync to Relational Entities (Class, Student, Concept, ConceptPerformance)
    class_counter: Dict[str, int] = {}
    for r in normalized:
        c_name = r["class_name"]
        class_counter[c_name] = class_counter.get(c_name, 0) + 1
    primary_class_name = max(class_counter, key=class_counter.get)

    subject_counter: Dict[str, int] = {}
    for r in normalized:
        if r["class_name"] == primary_class_name:
            s_name = r["subject"]
            subject_counter[s_name] = subject_counter.get(s_name, 0) + 1
    primary_subject = max(subject_counter, key=subject_counter.get) if subject_counter else "Data Structures"

    existing_classes = {c.name.strip().lower(): c for c in db.query(Class).all()}
    target_class = existing_classes.get(primary_class_name.strip().lower())
    if not target_class:
        target_class = Class(
            name=primary_class_name,
            subject=primary_subject,
            semester="Semester 1",
            teacher_id=teacher_id,
        )
        db.add(target_class)
        db.flush()
        existing_classes[primary_class_name.strip().lower()] = target_class

    primary_rows = [r for r in normalized if r["class_name"] == primary_class_name]
    student_records_map: Dict[str, str] = {}
    for r in primary_rows:
        student_records_map[r["roll_number"]] = r["student_name"]

    all_rolls = list(student_records_map.keys())
    existing_students = {
        s.roll_number: s
        for s in db.query(Student).filter(Student.roll_number.in_(all_rolls)).all()
    }

    student_obj_map: Dict[str, Student] = {}
    default_pwd_hash = hash_password("password123")
    for roll, s_name in student_records_map.items():
        if roll in existing_students:
            s_obj = existing_students[roll]
            s_obj.class_id = target_class.id
            s_obj.name = s_name
            student_obj_map[roll] = s_obj
        else:
            clean_roll = "".join(ch for ch in roll.lower() if ch.isalnum())
            email = f"{clean_roll}@adaptiveclass.ai"
            s_obj = Student(
                name=s_name,
                email=email,
                roll_number=roll,
                class_id=target_class.id,
                hashed_password=default_pwd_hash,
            )
            db.add(s_obj)
            student_obj_map[roll] = s_obj

    db.flush()

    all_topics = {r["topic"] for r in primary_rows if r.get("topic")}
    existing_concepts = {c.name.strip().lower(): c for c in db.query(Concept).all()}
    concept_obj_map: Dict[str, Concept] = {}
    for topic_name in all_topics:
        t_key = topic_name.strip().lower()
        if t_key in existing_concepts:
            concept_obj_map[t_key] = existing_concepts[t_key]
        else:
            c_obj = Concept(
                name=topic_name.strip(),
                subject=primary_subject,
                description=f"Core concept: {topic_name.strip()}",
                order_index=len(existing_concepts) + 1,
            )
            db.add(c_obj)
            db.flush()
            existing_concepts[t_key] = c_obj
            concept_obj_map[t_key] = c_obj

    perf_agg: Dict[Tuple[int, int], Dict[str, float]] = {}
    for r in primary_rows:
        roll = r["roll_number"]
        t_key = r["topic"].strip().lower() if r.get("topic") else ""
        if roll not in student_obj_map or t_key not in concept_obj_map:
            continue
        s_id = student_obj_map[roll].id
        c_id = concept_obj_map[t_key].id
        key = (s_id, c_id)
        if key not in perf_agg:
            perf_agg[key] = {"marks": 0.0, "max_marks": 0.0, "attempts": 0}
        perf_agg[key]["marks"] += r["marks"]
        perf_agg[key]["max_marks"] += r["max_marks"]
        perf_agg[key]["attempts"] += 1

    student_ids = [s.id for s in student_obj_map.values()]
    existing_perfs = {
        (cp.student_id, cp.concept_id): cp
        for cp in db.query(ConceptPerformance)
        .filter(ConceptPerformance.student_id.in_(student_ids))
        .all()
    }

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    for (s_id, c_id), stats in perf_agg.items():
        mastery = (
            round((stats["marks"] / stats["max_marks"]) * 100.0, 1)
            if stats["max_marks"] > 0
            else 0.0
        )
        mastery = max(0.0, min(100.0, mastery))
        attempts = int(stats["attempts"])
        corrects = int(round(attempts * (mastery / 100.0)))
        if (s_id, c_id) in existing_perfs:
            cp = existing_perfs[(s_id, c_id)]
            cp.mastery_score = mastery
            cp.attempt_count = attempts
            cp.correct_count = corrects
            cp.last_updated = now_utc
        else:
            cp = ConceptPerformance(
                student_id=s_id,
                concept_id=c_id,
                mastery_score=mastery,
                attempt_count=attempts,
                correct_count=corrects,
                last_updated=now_utc,
            )
            db.add(cp)

    db.commit()
    db.refresh(dataset)

    return DatasetUploadDetailResponse(
        id=dataset.id,
        filename=dataset.filename,
        file_type=dataset.file_type,
        status=dataset.status,
        row_count=dataset.row_count,
        error_count=dataset.error_count,
        uploaded_at=dataset.uploaded_at,
        class_id=target_class.id,
        class_name=target_class.name,
        subject=target_class.subject,
        student_count=len(student_records_map),
        errors=errors[:20],
    )


@router.get("", response_model=List[DatasetUploadResponse])
def list_datasets(
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    query = db.query(DatasetUpload)
    if claims.get("role") != "mentor":
        query = query.filter(
            DatasetUpload.uploaded_by_id == claims.get("id", 1),
            DatasetUpload.uploaded_by_role == claims.get("role", "teacher"),
        )
    return [_upload_response(dataset) for dataset in query.order_by(DatasetUpload.uploaded_at.desc()).all()]


@router.get("/{dataset_id}", response_model=DatasetUploadResponse)
def get_dataset(
    dataset_id: int,
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    dataset = db.get(DatasetUpload, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not _can_access(dataset, claims):
        raise HTTPException(status_code=403, detail="You cannot access this dataset")
    return _upload_response(dataset)


@router.get("/{dataset_id}/rows", response_model=List[DatasetRowResponse])
def get_dataset_rows(
    dataset_id: int,
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    dataset = db.get(DatasetUpload, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not _can_access(dataset, claims):
        raise HTTPException(status_code=403, detail="You cannot access this dataset")
    return [
        DatasetRowResponse(
            id=row.id, roll_number=row.roll_number, name=row.student_name,
            subject=row.subject, class_name=row.class_name, marks=row.marks,
            max_marks=row.max_marks, topic=row.topic, assessment=row.assessment,
            date=row.assessment_date,
        )
        for row in dataset.rows[:500]
    ]


@router.post("/{dataset_id}/analysis", response_model=DatasetAnalysisResponse)
def analyze_uploaded_dataset(
    dataset_id: int,
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    dataset = db.get(DatasetUpload, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not _can_access(dataset, claims):
        raise HTTPException(status_code=403, detail="You cannot analyze this dataset")
    rows = [
        {
            "roll_number": row.roll_number, "name": row.student_name,
            "subject": row.subject, "class": row.class_name, "marks": row.marks,
            "max_marks": row.max_marks, "topic": row.topic,
            "assessment": row.assessment, "date": row.assessment_date,
        }
        for row in dataset.rows
    ]
    try:
        result, model_name = analyze_dataset(rows)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    analysis = AnalysisResult(
        dataset_id=dataset.id,
        analysis_type="teacher_dashboard",
        model_name=model_name,
        result_json=json.dumps(result),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return DatasetAnalysisResponse(
        dataset_id=dataset.id, analysis_type=analysis.analysis_type,
        model_name=analysis.model_name, result=result, created_at=analysis.created_at,
    )


@router.get("/{dataset_id}/analysis", response_model=List[DatasetAnalysisResponse])
def list_dataset_analysis(
    dataset_id: int,
    claims: Dict[str, Any] = Depends(current_staff),
    db: Session = Depends(get_db),
):
    dataset = db.get(DatasetUpload, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not _can_access(dataset, claims):
        raise HTTPException(status_code=403, detail="You cannot access this dataset")
    return [
        DatasetAnalysisResponse(
            dataset_id=item.dataset_id, analysis_type=item.analysis_type,
            model_name=item.model_name, result=json.loads(item.result_json),
            created_at=item.created_at,
        )
        for item in dataset.analyses
    ]
