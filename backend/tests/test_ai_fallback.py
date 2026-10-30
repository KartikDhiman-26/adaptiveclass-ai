from app.ai_insights import generate_classroom_insight, generate_student_insight, TEACHER_DISCLAIMER

def test_ai_autonomous_fallback():
    metrics = {
        "class_name": "B.E. CSE — Data Structures",
        "subject": "Data Structures",
        "student_count": 80,
        "overall_average": 59.2,
        "weakest_concept": "Recursion",
        "weakest_mastery": 35.0,
        "strongest_concept": "Arrays",
        "strongest_mastery": 82.0,
        "recursion_support_count": 23,
        "recursion_support_pct": 28.8,
        "advanced_count": 12,
        "concept_items": []
    }

    insight = generate_classroom_insight(metrics)
    assert insight.learning_gap == "Recursion"
    assert insight.class_mastery == 35.0
    assert insight.students_below_threshold == 23
    assert "Recursion" in insight.what
    assert "23 of 80 students" in insight.why
    assert "base cases" in insight.suggested_action.lower()
    assert insight.teacher_disclaimer == TEACHER_DISCLAIMER
    assert insight.generated_by in ["Gemini 2.5 Flash", "Autonomous Rule-Based Engine"]

def test_student_personalized_insight():
    student_metric = {
        "name": "Aarav Sharma",
        "overall_mastery": 61.0,
        "weakest_concept": "Recursion",
        "weakest_score": 28.0,
        "concepts": [
            {"concept_name": "Arrays", "mastery": 91.0},
            {"concept_name": "Linked Lists", "mastery": 78.0},
            {"concept_name": "Trees", "mastery": 52.0},
            {"concept_name": "Recursion", "mastery": 28.0},
            {"concept_name": "Graphs", "mastery": 65.0},
            {"concept_name": "Sorting", "mastery": 80.0}
        ]
    }
    insight_text, steps = generate_student_insight(student_metric)
    assert "Aarav Sharma" in insight_text
    assert "Recursion" in insight_text
    assert "28" in insight_text
    assert len(steps) >= 3
