"""
Tests for Adaptive AI Quiz Generator.
Verifies difficulty tiers (beginner, intermediate, advanced), dynamic escalation,
answer evaluation, explanation delivery, weak-concept tracking, and no duplicate questions.
"""

from unittest.mock import MagicMock, patch

from app.student_ai.quiz_generator import (
    AdaptiveQuizSession, find_question_for_session, evaluate_student_answer,
    generate_session_summary, get_available_topics, OFFLINE_QUESTION_BANK,
    _generate_question_with_gemini
)

def test_available_topics_and_bank_coverage():
    topics = get_available_topics()
    assert "Recursion" in topics
    assert "Arrays" in topics
    assert "Linked Lists" in topics
    assert "Trees" in topics

    # Check each difficulty tier exists in bank
    difficulties = set(q["difficulty"] for q in OFFLINE_QUESTION_BANK)
    assert "beginner" in difficulties
    assert "intermediate" in difficulties
    assert "advanced" in difficulties

def test_adaptive_difficulty_escalation():
    """Correct answers should escalate: beginner -> intermediate -> advanced."""
    session = AdaptiveQuizSession(topic="Recursion", starting_difficulty="beginner", total_questions=3)
    assert session.current_difficulty == "beginner"

    # 1. First question
    q1 = find_question_for_session(session)
    assert q1 is not None
    assert q1.difficulty == "beginner"

    # Answer correctly
    eval1 = evaluate_student_answer(session, q1, q1.correct_answer)
    assert eval1.is_correct is True
    assert eval1.difficulty_change == "increased"
    assert eval1.new_difficulty == "intermediate"
    assert session.score == 1

    # 2. Second question should be intermediate
    q2 = find_question_for_session(session)
    assert q2 is not None
    assert q2.difficulty == "intermediate"
    assert q2.question_id != q1.question_id  # No duplicate!

    # Answer correctly again
    eval2 = evaluate_student_answer(session, q2, q2.correct_answer)
    assert eval2.is_correct is True
    assert eval2.difficulty_change == "increased"
    assert eval2.new_difficulty == "advanced"
    assert session.score == 2

    # 3. Third question should be advanced
    q3 = find_question_for_session(session)
    assert q3 is not None
    assert q3.difficulty == "advanced"
    assert q3.question_id not in [q1.question_id, q2.question_id]

def test_adaptive_difficulty_reduction_and_weak_concept_flagging():
    """Incorrect answers should decrease/reinforce difficulty and flag weak concepts."""
    session = AdaptiveQuizSession(topic="Recursion", starting_difficulty="intermediate", total_questions=3)

    q1 = find_question_for_session(session)
    assert q1 is not None
    assert q1.difficulty == "intermediate"

    # Choose a deliberately wrong answer
    wrong_opt = "A" if q1.correct_answer != "A" else "B"
    eval1 = evaluate_student_answer(session, q1, wrong_opt)

    assert eval1.is_correct is False
    assert eval1.difficulty_change == "reinforced"
    assert eval1.new_difficulty == "beginner"
    assert session.score == 0
    assert q1.concept_focus in session.weak_concepts

    # Next question should be beginner
    q2 = find_question_for_session(session)
    assert q2 is not None
    assert q2.difficulty == "beginner"

def test_no_duplicate_questions_in_session():
    session = AdaptiveQuizSession(topic="Recursion", starting_difficulty="beginner", total_questions=5)
    served_ids = []

    for _ in range(3):
        q = find_question_for_session(session)
        if q:
            assert q.question_id not in served_ids, f"Duplicate question served: {q.question_id}"
            served_ids.append(q.question_id)
            evaluate_student_answer(session, q, q.correct_answer)

    assert len(served_ids) == len(set(served_ids))


def test_unknown_quiz_topic_does_not_serve_an_unrelated_topic():
    session = AdaptiveQuizSession(topic="Quantum Mechanics", starting_difficulty="beginner")

    assert find_question_for_session(session) is None


@patch("app.student_ai.quiz_generator.GEMINI_API_KEY", "mock-test-key")
def test_gemini_quiz_generator_rejects_missing_correct_answer():
    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.models.generate_content.return_value.text = (
            '{"question_text":"What is a base case?",'
            '"option_a":"A stopping condition","option_b":"A recursive call",'
            '"option_c":"A variable","option_d":"A loop","explanation":"It stops recursion."}'
        )

        assert _generate_question_with_gemini("Recursion", "beginner") is None

def test_quiz_session_summary_and_recommendations():
    session = AdaptiveQuizSession(topic="Recursion", starting_difficulty="beginner", total_questions=2)

    q1 = find_question_for_session(session)
    evaluate_student_answer(session, q1, q1.correct_answer)

    q2 = find_question_for_session(session)
    wrong_opt = "A" if q2.correct_answer != "A" else "B"
    evaluate_student_answer(session, q2, wrong_opt)

    summary = generate_session_summary(session)
    assert summary.topic == "Recursion"
    assert summary.score == 1
    assert summary.total_questions == 2
    assert summary.accuracy == 50.0
    assert len(summary.recommendations) >= 2
    assert len(summary.weak_concepts) >= 1


@patch("app.student_ai.quiz_generator.GEMINI_API_KEY", "mock-test-key")
def test_gemini_quiz_generation_uses_millisecond_timeout():
    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_instance.models.generate_content.return_value.text = (
            '{"question_text":"What is a base case?",'
            '"option_a":"A stopping condition","option_b":"A recursive call",'
            '"option_c":"A variable","option_d":"A loop",'
            '"correct_answer":"A","explanation":"It stops recursion.",'
            '"concept_tag":"Base Case"}'
        )

        question = _generate_question_with_gemini("Recursion", "beginner")

    assert question is not None
    assert question.question_text == "What is a base case?"
    assert mock_client_cls.call_args.kwargs["http_options"] == {"timeout": 10_000}
