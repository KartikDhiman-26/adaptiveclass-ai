import json
from typing import Any, Dict

from app.config import GEMINI_API_KEY


def _fallback_analysis(rows: list[Dict[str, Any]]) -> Dict[str, Any]:
    subject_totals: Dict[str, list[float]] = {}
    topic_totals: Dict[str, list[float]] = {}
    student_totals: Dict[str, list[float]] = {}
    for row in rows:
        percentage = row["marks"] / row["max_marks"] * 100
        subject_totals.setdefault(row["subject"], []).append(percentage)
        if row.get("topic"):
            topic_totals.setdefault(row["topic"], []).append(percentage)
        student_totals.setdefault(row["roll_number"], []).append(percentage)

    def average(values: list[float]) -> float:
        return round(sum(values) / len(values), 2)

    topic_gaps = [
        {"topic": topic, "average_percentage": average(scores)}
        for topic, scores in topic_totals.items()
    ]
    topic_gaps.sort(key=lambda item: item["average_percentage"])
    at_risk = [
        {"roll_number": roll, "average_percentage": average(scores)}
        for roll, scores in student_totals.items()
        if average(scores) < 40
    ]
    return {
        "summary": {
            "row_count": len(rows),
            "student_count": len(student_totals),
            "subject_count": len(subject_totals),
            "class_average_percentage": average(
                [row["marks"] / row["max_marks"] * 100 for row in rows]
            ) if rows else 0,
        },
        "subject_averages": [
            {"subject": subject, "average_percentage": average(scores)}
            for subject, scores in subject_totals.items()
        ],
        "topic_gaps": topic_gaps,
        "at_risk_students": at_risk,
        "performance_trends": [],
        "recommendations": [
            "Prioritize the lowest-performing topics for targeted AI-generated practice."
        ] if topic_gaps else [],
    }


def analyze_dataset(rows: list[Dict[str, Any]]) -> tuple[Dict[str, Any], str]:
    statistical_summary = _fallback_analysis(rows)
    if not GEMINI_API_KEY:
        return statistical_summary, "Deterministic Dataset Analysis"

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "Analyze this normalized student performance dataset. Return valid JSON only "
            "with keys summary, subject_averages, topic_gaps, at_risk_students, "
            "performance_trends, recommendations. Use only the supplied data. "
            "Do not infer medical, psychological, or demographic claims. Dataset rows: "
            + json.dumps(statistical_summary, default=str)
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip()), "Gemini 2.5 Flash"
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini returned invalid analysis JSON: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Gemini analysis failed: {exc}") from exc


def generate_student_ai(
    request: Dict[str, Any], performance_context: list[Dict[str, Any]]
) -> tuple[Dict[str, Any], str]:
    if not GEMINI_API_KEY:
        return {
            "message": (
                f"Start with {request.get('topic') or 'your weakest topic'} at "
                f"{request.get('difficulty') or 'beginner'} difficulty. "
                "Ask for an explanation, example, or practice question."
            ),
            "context_rows": len(performance_context),
        }, "Deterministic Student AI"

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "You are a safe educational AI tutor. Respond as valid JSON with keys "
            "message, quiz, learning_plan, resources. Adapt to the requested topic "
            "and difficulty using only the performance context. Never claim to be a "
            "human teacher. Request: " + json.dumps(request) +
            " Performance context: " + json.dumps(performance_context, default=str)
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip()), "Gemini 2.5 Flash"
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini returned invalid student JSON: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Gemini student AI request failed: {exc}") from exc


def analyze_student_activity(
    interactions: list[Dict[str, Any]], attempts: list[Dict[str, Any]]
) -> tuple[Dict[str, Any], str]:
    if not GEMINI_API_KEY:
        topics = [item["topic"] for item in interactions if item.get("topic")]
        return {
            "summary": (
                f"The student completed {len(interactions)} AI interactions and "
                f"{len(attempts)} recorded quiz attempts."
            ),
            "topics_discussed": sorted(set(topics)),
            "quiz_performance": {
                "attempts": len(attempts),
                "average_score": round(
                    sum(item["score"] for item in attempts) / len(attempts), 2
                ) if attempts else None,
            },
            "learning_signals": [
                "Review repeated topics and quiz results before recommending the next activity."
            ],
            "teacher_actions": [
                "Use the uploaded performance data and this activity report together."
            ],
        }, "Deterministic Student Activity Analysis"

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "Analyze this student's AI learning activity for a teacher report. "
            "Return valid JSON only with keys summary, topics_discussed, "
            "quiz_performance, learning_signals, teacher_actions. Do not make "
            "medical or psychological claims. Activity: "
            + json.dumps({"interactions": interactions, "attempts": attempts}, default=str)
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip()), "Gemini 2.5 Flash"
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Gemini returned invalid activity report JSON: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Gemini activity analysis failed: {exc}") from exc
