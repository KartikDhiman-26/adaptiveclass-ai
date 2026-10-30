import csv
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.performance_analyzer import analyze_records


# Standard column names and their accepted alternatives
COLUMN_ALIASES = {
    "rollno": [
        "rollno", "roll_no", "roll_number", "student_id",
        "roll", "reg_no", "registration_no", "enrollment_no"
    ],
    "name": [
        "name", "student_name", "student", "full_name", "candidate_name"
    ],
    "subject": [
        "subject", "course", "subject_name", "course_name"
    ],
    "class": [
        "class", "class_name", "grade", "section", "class_grade", "cohort"
    ],
    "marks": [
        "marks", "score", "obtained_marks", "marks_obtained", "obtained", "scored_marks"
    ],
    "max_marks": [
        "max_marks", "total_marks", "maximum_marks", "out_of", "max_score", "total_score"
    ],
    "topic": [
        "topic", "chapter", "unit", "concept", "subtopic", "lesson"
    ],
    "assessment": [
        "assessment", "test", "exam", "exam_name", "assessment_name", "test_name", "quiz"
    ],
    "date": [
        "date", "assessment_date", "exam_date", "test_date", "attempt_date"
    ]
}


def normalize_header(header: str) -> str:
    """Normalize CSV column names by trimming, converting to lower case and replacing symbols."""
    header = str(header).strip().lower()
    header = re.sub(r"[^a-z0-9]+", "_", header)
    return header.strip("_")


def parse_date_safely(date_val: Any) -> Optional[str]:
    """Parse date string across common formats and return ISO YYYY-MM-DD."""
    if not date_val:
        return None
    raw = str(date_val).strip()
    # Try common date formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_and_validate_csv(
    file_content: Union[bytes, str],
    column_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Parses and validates CSV content.
    Supports automatic header recognition, explicit column mappings,
    strict validation against missing/invalid values, and duplicate detection.

    Returns a detailed validation report along with validated records.
    """
    try:
        # Decode bytes with fallback encoding support
        if isinstance(file_content, bytes):
            try:
                text = file_content.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")
        else:
            text = str(file_content)

        if not text.strip():
            return {
                "success": False,
                "message": "The uploaded CSV file is empty.",
                "total_uploaded_rows": 0,
                "accepted_rows": 0,
                "rejected_rows": 0,
                "duplicate_rows": 0,
                "valid_records": [],
                "rejected_records": [],
                "row_errors": ["The uploaded CSV file is empty."],
                "missing_columns": list(COLUMN_ALIASES.keys()),
                "detected_columns": {}
            }

        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            return {
                "success": False,
                "message": "CSV headers are missing or file is improperly formatted.",
                "total_uploaded_rows": 0,
                "accepted_rows": 0,
                "rejected_rows": 0,
                "duplicate_rows": 0,
                "valid_records": [],
                "rejected_records": [],
                "row_errors": ["CSV headers are missing."],
                "missing_columns": list(COLUMN_ALIASES.keys()),
                "detected_columns": {}
            }

        # Build mapping of original headers to normalized versions
        original_headers = list(reader.fieldnames)
        normalized_headers = {
            h: normalize_header(h) for h in original_headers if h
        }

        detected_columns: Dict[str, str] = {}
        applied_mapping = column_mapping.copy() if column_mapping else {}

        # 1. Apply explicit mappings first if provided
        for standard_name in COLUMN_ALIASES.keys():
            if standard_name in applied_mapping:
                target_col = applied_mapping[standard_name]
                if target_col in original_headers:
                    detected_columns[standard_name] = target_col
                else:
                    # Check case-insensitive / normalized match
                    norm_target = normalize_header(target_col)
                    for orig, norm in normalized_headers.items():
                        if norm == norm_target:
                            detected_columns[standard_name] = orig
                            break

        # 2. Detect remaining columns via aliases
        for standard_name, aliases in COLUMN_ALIASES.items():
            if standard_name in detected_columns:
                continue
            for orig, norm in normalized_headers.items():
                if norm in aliases:
                    detected_columns[standard_name] = orig
                    break

        # 3. Check for missing required columns
        missing_columns = [
            col for col in COLUMN_ALIASES.keys()
            if col not in detected_columns
        ]

        if missing_columns:
            return {
                "success": False,
                "message": f"Required columns are missing: {', '.join(missing_columns)}",
                "total_uploaded_rows": 0,
                "accepted_rows": 0,
                "rejected_rows": 0,
                "duplicate_rows": 0,
                "valid_records": [],
                "rejected_records": [],
                "row_errors": [f"Missing required column: {col}" for col in missing_columns],
                "missing_columns": missing_columns,
                "detected_columns": detected_columns
            }

        # 4. Process and validate each row
        valid_records: List[Dict[str, Any]] = []
        rejected_records: List[Dict[str, Any]] = []
        row_errors: List[str] = []
        seen_keys = set()
        duplicate_count = 0
        total_rows = 0

        for row_idx, row in enumerate(reader, start=2):
            total_rows += 1
            row_issues = []

            clean_record: Dict[str, Any] = {}
            for std_col, orig_col in detected_columns.items():
                val = row.get(orig_col)
                clean_record[std_col] = str(val).strip() if val is not None else ""

            # Check missing / empty values
            missing_vals = [
                std_col for std_col, val in clean_record.items()
                if not val
            ]
            if missing_vals:
                row_issues.append(f"Missing required value(s) in: {', '.join(missing_vals)}")

            # Validate numeric marks
            marks_val = None
            max_marks_val = None

            if "marks" not in missing_vals:
                try:
                    marks_val = float(clean_record["marks"])
                except (ValueError, TypeError):
                    row_issues.append(f"Invalid marks value '{clean_record['marks']}' - must be numeric.")

            if "max_marks" not in missing_vals:
                try:
                    max_marks_val = float(clean_record["max_marks"])
                    if max_marks_val <= 0:
                        row_issues.append("Maximum marks must be greater than zero.")
                except (ValueError, TypeError):
                    row_issues.append(f"Invalid maximum marks value '{clean_record['max_marks']}' - must be numeric.")

            if marks_val is not None and max_marks_val is not None and max_marks_val > 0:
                if marks_val < 0:
                    row_issues.append(f"Marks cannot be negative ({marks_val}).")
                elif marks_val > max_marks_val:
                    row_issues.append(f"Marks ({marks_val}) cannot exceed maximum marks ({max_marks_val}).")

            # Validate date format
            standardized_date = None
            if "date" not in missing_vals:
                standardized_date = parse_date_safely(clean_record["date"])
                if not standardized_date:
                    row_issues.append(f"Invalid date format '{clean_record['date']}'. Expected YYYY-MM-DD or DD-MM-YYYY.")

            if row_issues:
                err_msg = f"Row {row_idx}: " + "; ".join(row_issues)
                row_errors.append(err_msg)
                rejected_records.append({
                    "row_number": row_idx,
                    "data": clean_record,
                    "errors": row_issues
                })
                continue

            # Duplicate check
            dup_key = (
                clean_record["rollno"],
                clean_record["subject"],
                clean_record["topic"],
                clean_record["assessment"],
                standardized_date
            )

            if dup_key in seen_keys:
                duplicate_count += 1
                row_errors.append(
                    f"Row {row_idx}: Duplicate record detected for student {clean_record['rollno']} "
                    f"in {clean_record['subject']} - {clean_record['topic']} ({clean_record['assessment']})."
                )
                rejected_records.append({
                    "row_number": row_idx,
                    "data": clean_record,
                    "errors": ["Duplicate record in assessment dataset."]
                })
                continue

            seen_keys.add(dup_key)

            # Record is valid
            percentage = round((marks_val / max_marks_val) * 100.0, 2)
            validated_record = {
                "rollno": clean_record["rollno"],
                "name": clean_record["name"],
                "class": clean_record["class"],
                "subject": clean_record["subject"],
                "topic": clean_record["topic"],
                "assessment": clean_record["assessment"],
                "marks": marks_val,
                "max_marks": max_marks_val,
                "percentage": percentage,
                "date": standardized_date
            }
            valid_records.append(validated_record)

        return {
            "success": len(valid_records) > 0,
            "message": "CSV processed successfully." if valid_records else "No valid records found.",
            "total_uploaded_rows": total_rows,
            "accepted_rows": len(valid_records),
            "rejected_rows": len(rejected_records),
            "duplicate_rows": duplicate_count,
            "valid_records": valid_records,
            "rejected_records": rejected_records,
            "row_errors": row_errors,
            "missing_columns": [],
            "detected_columns": detected_columns
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "message": "Unable to decode file encoding. Please upload a UTF-8 or Latin-1 CSV.",
            "total_uploaded_rows": 0,
            "accepted_rows": 0,
            "rejected_rows": 0,
            "duplicate_rows": 0,
            "valid_records": [],
            "rejected_records": [],
            "row_errors": ["Encoding error."],
            "missing_columns": [],
            "detected_columns": {}
        }
    except csv.Error as error:
        return {
            "success": False,
            "message": f"CSV reading error: {error}",
            "total_uploaded_rows": 0,
            "accepted_rows": 0,
            "rejected_rows": 0,
            "duplicate_rows": 0,
            "valid_records": [],
            "rejected_records": [],
            "row_errors": [str(error)],
            "missing_columns": [],
            "detected_columns": {}
        }
    except Exception as error:
        return {
            "success": False,
            "message": f"Processing failed: {error}",
            "total_uploaded_rows": 0,
            "accepted_rows": 0,
            "rejected_rows": 0,
            "duplicate_rows": 0,
            "valid_records": [],
            "rejected_records": [],
            "row_errors": [str(error)],
            "missing_columns": [],
            "detected_columns": {}
        }


def process_csv(
    file_content: Union[bytes, str],
    column_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Legacy and direct entry point:
    Read CSV content, detect columns, validate records,
    and generate performance analytics.
    """
    parsed = parse_and_validate_csv(file_content, column_mapping=column_mapping)

    if not parsed["success"]:
        return {
            "success": False,
            "message": parsed.get("message", "Validation failed."),
            "missing_columns": parsed.get("missing_columns", []),
            "detected_columns": parsed.get("detected_columns", {}),
            "validation_report": parsed
        }

    # Run performance analyzer on validated unique records
    analysis = analyze_records(parsed["valid_records"])

    return {
        "success": analysis.get("success", False),
        "detected_columns": parsed["detected_columns"],
        "total_uploaded_rows": parsed["total_uploaded_rows"],
        "duplicate_rows": parsed["duplicate_rows"],
        "rejected_rows": parsed["rejected_rows"],
        "analysis": analysis,
        "validation_report": parsed
    }
