"""
Tests for Learner Profiler.
Verifies new-student baseline handling (zero prior assumptions),
mastery updates via weighted formula, learning level calibration,
and strengths/weaknesses detection.
"""

from app.student_ai.profiler import (
    create_new_student_profile, update_profile_with_quiz,
    calculate_learning_level, get_concept_status_label
)

def test_new_student_profile_creation_no_assumptions():
    profile = create_new_student_profile("Rohan Mehta")
    assert profile.student_name == "Rohan Mehta"
    assert profile.has_historical_data is False
    assert profile.overall_mastery == 0.0
    assert profile.learning_level == "Beginner"
    assert len(profile.quiz_history) == 0
    assert len(profile.strengths) == 0
    assert len(profile.weaknesses) == 0
    assert "Recursion" in profile.topic_mastery
    assert profile.topic_mastery["Recursion"].attempt_count == 0

def test_update_profile_for_new_student_after_quiz():
    profile = create_new_student_profile("Rohan Mehta")

    # Rohan scores 4 out of 5 (80%) on Recursion
    update_profile_with_quiz(
        profile=profile,
        topic="Recursion",
        score=4,
        total_questions=5,
        final_difficulty="intermediate"
    )

    assert profile.has_historical_data is True
    rec_mastery = profile.topic_mastery["Recursion"].mastery_percentage
    assert rec_mastery == 80.0
    assert profile.topic_mastery["Recursion"].status_label == "Strong"
    assert "Recursion" in profile.strengths
    assert len(profile.quiz_history) == 1
    assert profile.quiz_history[0].accuracy == 80.0

def test_weighted_mastery_formula_with_existing_data():
    profile = create_new_student_profile("Aarav Sharma")
    profile.has_historical_data = True
    profile.topic_mastery["Recursion"].mastery_percentage = 28.0  # initial gap
    profile.topic_mastery["Recursion"].attempt_count = 1

    # Aarav scores 4 out of 5 (80%) on Recursion
    # Expected: round(28.0 * 0.35 + 80.0 * 0.65, 1) = round(9.8 + 52.0) = 61.8%
    update_profile_with_quiz(
        profile=profile,
        topic="Recursion",
        score=4,
        total_questions=5,
        final_difficulty="intermediate"
    )

    new_score = profile.topic_mastery["Recursion"].mastery_percentage
    assert abs(new_score - 61.8) < 0.1
    assert profile.topic_mastery["Recursion"].status_label == "Moderate"

def test_learning_level_calibration():
    assert calculate_learning_level(88.0) == "Advanced"
    assert calculate_learning_level(65.0) == "Intermediate"
    assert calculate_learning_level(35.0) == "Beginner"

def test_profile_summary_output():
    profile = create_new_student_profile("Tanvi")
    summary = profile.get_summary()
    assert "Tanvi" in summary
    assert "New Student (No prior records)" in summary
