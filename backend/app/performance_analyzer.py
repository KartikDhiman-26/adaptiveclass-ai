import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


REQUIRED_COLUMNS = {
    "rollno",
    "name",
    "subject",
    "class",
    "marks",
    "max_marks",
    "topic",
    "assessment",
    "date"
}


def parse_date_safely(date_val: Any) -> Optional[str]:
    """Parse date string across common formats and return ISO YYYY-MM-DD."""
    if not date_val:
        return None
    raw = str(date_val).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def validate_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate raw records against schema and value boundaries."""
    if not records:
        return {
            "valid": False,
            "errors": ["The uploaded dataset contains no records."],
            "valid_records": [],
            "total_rows": 0,
            "accepted_rows": 0,
            "rejected_rows": 0
        }

    errors = []
    valid_records = []

    for index, row in enumerate(records, start=2):
        missing = [
            col for col in REQUIRED_COLUMNS
            if col not in row or row[col] is None or str(row[col]).strip() == ""
        ]

        if missing:
            errors.append(f"Row {index}: Missing values in {', '.join(missing)}")
            continue

        try:
            marks = float(row["marks"])
            max_marks = float(row["max_marks"])

            if max_marks <= 0:
                raise ValueError("Maximum marks must be positive.")

            if marks < 0 or marks > max_marks:
                raise ValueError(f"Marks ({marks}) must be between 0 and maximum marks ({max_marks}).")

            std_date = parse_date_safely(row["date"])
            if not std_date:
                raise ValueError(f"Invalid date format '{row['date']}'. Expected YYYY-MM-DD or DD-MM-YYYY.")

            clean_row = dict(row)
            clean_row["marks"] = marks
            clean_row["max_marks"] = max_marks
            clean_row["percentage"] = round((marks / max_marks) * 100.0, 2)
            clean_row["date"] = std_date
            valid_records.append(clean_row)

        except (ValueError, TypeError) as error:
            errors.append(f"Row {index}: {error}")

    return {
        "valid": len(valid_records) > 0,
        "valid_records": valid_records,
        "errors": errors,
        "total_rows": len(records),
        "accepted_rows": len(valid_records),
        "rejected_rows": len(errors)
    }


def get_performance_level(percentage: float) -> str:
    """Classify performance using percentage according to established educational thresholds."""
    if percentage >= 85.0:
        return "Advanced"
    elif percentage >= 70.0:
        return "Proficient"
    elif percentage >= 50.0:
        return "Developing"
    else:
        return "Needs Support"


def compute_distribution(percentages: List[float]) -> Dict[str, Any]:
    """Calculate counts and percentages across performance tiers."""
    dist = {
        "advanced": 0,
        "proficient": 0,
        "developing": 0,
        "needs_support": 0,
        "total": len(percentages)
    }
    for p in percentages:
        level = get_performance_level(p)
        if level == "Advanced":
            dist["advanced"] += 1
        elif level == "Proficient":
            dist["proficient"] += 1
        elif level == "Developing":
            dist["developing"] += 1
        else:
            dist["needs_support"] += 1
    return dist


def analyze_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes classroom assessment records using pure deterministic Python math.
    Calculates class-level, student-level, subject-level, and topic-level metrics.
    """
    validation = validate_records(records)
    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
            "validation": validation
        }

    valid_rows = validation["valid_records"]

    student_data = defaultdict(
        lambda: {
            "name": "",
            "class": "",
            "marks": 0.0,
            "maximum": 0.0,
            "assessments": 0,
            "subject_scores": defaultdict(lambda: {"marks": 0.0, "max": 0.0}),
            "topic_scores": defaultdict(lambda: {"marks": 0.0, "max": 0.0}),
            "attempts": []
        }
    )

    subject_data = defaultdict(
        lambda: {
            "marks": 0.0,
            "maximum": 0.0,
            "assessments": 0,
            "students": set(),
            "percentages": [],
            "topics": defaultdict(lambda: {"marks": 0.0, "max": 0.0, "students": set()})
        }
    )

    topic_data = defaultdict(
        lambda: {
            "subject": "",
            "marks": 0.0,
            "maximum": 0.0,
            "assessments": 0,
            "students": set(),
            "student_percentages": {},
            "percentages": []
        }
    )

    all_percentages = []
    total_marks = 0.0
    total_maximum = 0.0

    for row in valid_rows:
        rollno = str(row["rollno"]).strip()
        student_name = str(row["name"]).strip()
        class_name = str(row.get("class", "")).strip()
        subject = str(row["subject"]).strip()
        topic = str(row["topic"]).strip()
        assessment = str(row.get("assessment", "Assessment")).strip()
        date_str = str(row.get("date", "")).strip()

        marks = float(row["marks"])
        maximum = float(row["max_marks"])
        pct = round((marks / maximum) * 100.0, 2)

        total_marks += marks
        total_maximum += maximum
        all_percentages.append(pct)

        # Student aggregations
        s = student_data[rollno]
        s["name"] = student_name
        s["class"] = class_name
        s["marks"] += marks
        s["maximum"] += maximum
        s["assessments"] += 1
        s["subject_scores"][subject]["marks"] += marks
        s["subject_scores"][subject]["max"] += maximum
        s["topic_scores"][topic]["marks"] += marks
        s["topic_scores"][topic]["max"] += maximum
        s["attempts"].append({
            "assessment": assessment,
            "topic": topic,
            "subject": subject,
            "marks": marks,
            "max_marks": maximum,
            "percentage": pct,
            "date": date_str
        })

        # Subject aggregations
        sub = subject_data[subject]
        sub["marks"] += marks
        sub["maximum"] += maximum
        sub["assessments"] += 1
        sub["students"].add(rollno)
        sub["percentages"].append(pct)
        sub["topics"][topic]["marks"] += marks
        sub["topics"][topic]["max"] += maximum
        sub["topics"][topic]["students"].add(rollno)

        # Topic aggregations
        top = topic_data[topic]
        top["subject"] = subject
        top["marks"] += marks
        top["maximum"] += maximum
        top["assessments"] += 1
        top["students"].add(rollno)
        top["percentages"].append(pct)
        # Record latest score per student for this topic
        top["student_percentages"][rollno] = pct

    # 1. Student Analysis
    students = []
    student_averages = []

    for rollno, s in student_data.items():
        avg_pct = round((s["marks"] / s["maximum"]) * 100.0, 2)
        student_averages.append(avg_pct)

        # Subject breakdown
        subj_breakdown = {}
        for sub_name, vals in s["subject_scores"].items():
            subj_breakdown[sub_name] = round((vals["marks"] / vals["max"]) * 100.0, 2)

        # Topic breakdown & strengths/weaknesses
        topic_breakdown = {}
        strengths = []
        weaknesses = []
        for top_name, vals in s["topic_scores"].items():
            top_pct = round((vals["marks"] / vals["max"]) * 100.0, 2)
            topic_breakdown[top_name] = top_pct
            if top_pct >= 75.0:
                strengths.append(top_name)
            elif top_pct < 50.0:
                weaknesses.append(top_name)

        # Chronological attempt trajectory
        sorted_attempts = sorted(s["attempts"], key=lambda a: a["date"])

        students.append({
            "rollno": rollno,
            "name": s["name"],
            "class": s["class"],
            "average_percentage": avg_pct,
            "learning_level": get_performance_level(avg_pct),
            "assessments_count": s["assessments"],
            "subject_performance": subj_breakdown,
            "topic_performance": topic_breakdown,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "attempts": sorted_attempts
        })

    # Sort students by average percentage descending
    students.sort(key=lambda x: x["average_percentage"], reverse=True)

    # 2. Subject Analysis
    subjects = []
    for sub_name, vals in subject_data.items():
        sub_pct = round((vals["marks"] / vals["maximum"]) * 100.0, 2)
        sub_dist = compute_distribution(vals["percentages"])

        topic_list = []
        for top_name, tvals in vals["topics"].items():
            tpct = round((tvals["marks"] / tvals["max"]) * 100.0, 2)
            topic_list.append({
                "topic": top_name,
                "percentage": tpct,
                "level": get_performance_level(tpct),
                "students_count": len(tvals["students"])
            })
        topic_list.sort(key=lambda t: t["percentage"], reverse=True)

        subjects.append({
            "name": sub_name,
            "percentage": sub_pct,
            "level": get_performance_level(sub_pct),
            "assessments": vals["assessments"],
            "students_count": len(vals["students"]),
            "distribution": sub_dist,
            "topics": topic_list,
            "strongest_topic": topic_list[0]["topic"] if topic_list else "",
            "weakest_topic": topic_list[-1]["topic"] if topic_list else "",
            "revision_needed": any(t["percentage"] < 50.0 for t in topic_list)
        })

    # 3. Topic Analysis
    topics = []
    weak_topics = []

    for top_name, vals in topic_data.items():
        top_pct = round((vals["marks"] / vals["maximum"]) * 100.0, 2)
        struggling_students = [
            r for r, p in vals["student_percentages"].items() if p < 50.0
        ]
        struggling_count = len(struggling_students)
        total_in_topic = len(vals["students"])
        struggling_pct = round((struggling_count / max(total_in_topic, 1)) * 100.0, 1)

        # Revision priority
        if top_pct < 40.0 or struggling_pct >= 40.0:
            revision_priority = "critical"
        elif top_pct < 50.0 or struggling_pct >= 25.0:
            revision_priority = "moderate"
        else:
            revision_priority = "low"

        topic_item = {
            "name": top_name,
            "subject": vals["subject"],
            "percentage": top_pct,
            "level": get_performance_level(top_pct),
            "assessments": vals["assessments"],
            "students_assessed": total_in_topic,
            "struggling_students_count": struggling_count,
            "struggling_students_percentage": struggling_pct,
            "distribution": compute_distribution(vals["percentages"]),
            "revision_priority": revision_priority
        }
        topics.append(topic_item)

        if top_pct < 50.0 or struggling_pct >= 30.0:
            weak_topics.append(topic_item)

    topics.sort(key=lambda t: t["percentage"])

    # 4. Class-Level Aggregations & Distribution
    class_avg = round((total_marks / max(total_maximum, 1.0)) * 100.0, 2)
    median_score = round(statistics.median(all_percentages), 2) if all_percentages else 0.0
    highest_score = max(all_percentages) if all_percentages else 0.0
    lowest_score = min(all_percentages) if all_percentages else 0.0

    global_distribution = compute_distribution(student_averages)
    students_needing_support = [s for s in students if s["average_percentage"] < 50.0]

    # Class-level critical learning gaps
    learning_gaps = [
        f"{t['name']} ({t['percentage']}%, {t['struggling_students_count']} students struggling)"
        for t in topics if t["revision_priority"] in ("critical", "moderate")
    ]

    return {
        "success": True,
        "data_summary": {
            "total_students": len(students),
            "total_assessments": len(valid_rows),
            "overall_percentage": class_avg,
            "median_percentage": median_score,
            "highest_percentage": highest_score,
            "lowest_percentage": lowest_score,
            "distribution": global_distribution
        },
        "student_analysis": students,
        "subject_analysis": subjects,
        "topic_analysis": topics,
        "weak_topics": weak_topics,
        "students_needing_support": students_needing_support,
        "learning_gaps": learning_gaps,
        "strongest_topic": topics[-1]["name"] if topics else "",
        "weakest_topic": topics[0]["name"] if topics else "",
        "validation": {
            "accepted_rows": validation["accepted_rows"],
            "rejected_rows": validation["rejected_rows"],
            "errors": validation["errors"]
        }
    }


def analyze_historical_comparison(
    past_records: List[Dict[str, Any]],
    current_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compares two assessment datasets chronologically to detect:
    - Class average shifts (percentage-point delta)
    - Topic-level progression and persistent learning gaps
    - Individual student improvement or decline
    """
    if not past_records or not current_records:
        return {
            "has_historical_data": False,
            "message": "Insufficient historical data for longitudinal comparison. Requires at least two distinct assessments.",
            "class_average_change": 0.0,
            "topic_comparison": [],
            "student_progressions": [],
            "persistent_weak_topics": [],
            "improving_students": [],
            "declining_students": []
        }

    past_analysis = analyze_records(past_records)
    current_analysis = analyze_records(current_records)

    if not past_analysis.get("success") or not current_analysis.get("success"):
        return {
            "has_historical_data": False,
            "message": "Cannot perform historical comparison due to invalid assessment datasets.",
            "class_average_change": 0.0,
            "topic_comparison": [],
            "student_progressions": [],
            "persistent_weak_topics": [],
            "improving_students": [],
            "declining_students": []
        }

    past_avg = past_analysis["data_summary"]["overall_percentage"]
    curr_avg = current_analysis["data_summary"]["overall_percentage"]
    class_delta = round(curr_avg - past_avg, 2)

    # 1. Topic Comparison
    past_topics = {t["name"]: t["percentage"] for t in past_analysis["topic_analysis"]}
    curr_topics = {t["name"]: t["percentage"] for t in current_analysis["topic_analysis"]}

    topic_comparison = []
    persistent_weak = []

    all_topic_names = set(past_topics.keys()) | set(curr_topics.keys())
    for name in all_topic_names:
        p_score = past_topics.get(name)
        c_score = curr_topics.get(name)

        if p_score is not None and c_score is not None:
            delta = round(c_score - p_score, 2)
            status = "improved" if delta >= 3.0 else ("declined" if delta <= -3.0 else "steady")
            if p_score < 50.0 and c_score < 50.0:
                persistent_weak.append(name)
        elif p_score is None:
            delta = None
            status = "new_topic"
        else:
            delta = None
            status = "not_assessed_in_current"

        topic_comparison.append({
            "topic": name,
            "past_percentage": p_score,
            "current_percentage": c_score,
            "percentage_point_change": delta,
            "status": status
        })

    topic_comparison.sort(key=lambda t: t["percentage_point_change"] if t["percentage_point_change"] is not None else 0)

    # 2. Student-level progress comparison
    past_students = {s["rollno"]: s for s in past_analysis["student_analysis"]}
    curr_students = {s["rollno"]: s for s in current_analysis["student_analysis"]}

    improving = []
    declining = []
    student_progress = []

    for rollno, c_s in curr_students.items():
        if rollno in past_students:
            p_s = past_students[rollno]
            p_avg = p_s["average_percentage"]
            c_avg = c_s["average_percentage"]
            delta = round(c_avg - p_avg, 2)

            if delta >= 10.0:
                trajectory = "improving"
                improving.append({
                    "rollno": rollno,
                    "name": c_s["name"],
                    "past_average": p_avg,
                    "current_average": c_avg,
                    "change": delta
                })
            elif delta <= -10.0:
                trajectory = "declining"
                declining.append({
                    "rollno": rollno,
                    "name": c_s["name"],
                    "past_average": p_avg,
                    "current_average": c_avg,
                    "change": delta
                })
            else:
                trajectory = "steady"

            student_progress.append({
                "rollno": rollno,
                "name": c_s["name"],
                "past_average": p_avg,
                "current_average": c_avg,
                "change": delta,
                "trajectory": trajectory
            })

    student_progress.sort(key=lambda s: s["change"], reverse=True)

    return {
        "has_historical_data": True,
        "class_average_change": class_delta,
        "past_class_average": past_avg,
        "current_class_average": curr_avg,
        "topic_comparison": topic_comparison,
        "persistent_weak_topics": persistent_weak,
        "improving_students": improving,
        "declining_students": declining,
        "student_progressions": student_progress
    }
