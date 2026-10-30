"""
Tests for Student AI Tutor conversational engine.
Verifies welcome messaging, step-by-step guidance, line-by-line walkthroughs,
emotion adaptation, conversation memory, and mocked Gemini behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.student_ai.tutor import (
    StudentTutor, TutorResponse, is_quiz_trigger, OFFLINE_SUGGESTION_POOLS
)
from app.student_ai.emotion_detector import EmotionCue
from app.student_ai.profiler import create_new_student_profile

@pytest.fixture(autouse=True)
def default_mock_gemini_key():
    """Ensures deterministic, fast unit tests without unmocked live network calls."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        yield

def test_tutor_welcome_message():
    tutor = StudentTutor(student_name="Aarav Sharma", student_level="Intermediate")
    welcome = tutor.get_welcome()
    assert "Aarav Sharma" in welcome
    assert "Personal Learning Tutor" in welcome
    assert "Step-by-Step" in welcome
    assert "Line-by-Line" in welcome
    assert "Adaptive Practice" in welcome

def test_tutor_step_by_step_concept_explanation():
    tutor = StudentTutor(student_name="Aarav Sharma", student_level="Intermediate")
    res = tutor.chat("How does recursion work?")
    assert isinstance(res, TutorResponse)
    assert len(tutor.history) == 2  # 1 user + 1 assistant
    assert "Recursion" in res.message
    assert "Base Case" in res.message or "base case" in res.message.lower()
    assert len(res.suggested_followups) > 0

def test_tutor_line_by_line_code_explanation():
    tutor = StudentTutor(student_name="Priya", student_level="Beginner")
    res = tutor.chat("Can you explain this code line by line: def f(n): if n <= 1: return 1")
    assert "Line" in res.message or "Line-by-Line" in res.message
    assert "Walkthrough" in res.message or "breakdown" in res.message.lower()

def test_tutor_confusion_adaptation():
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
    res = tutor.chat("I don't understand this at all, it's totally confusing.")
    assert res.detected_cue == EmotionCue.CONFUSION
    assert "Analogy" in res.message or "analogy" in res.message.lower() or "simplify" in res.message.lower()

def test_tutor_quiz_intent_detection():
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
    res = tutor.chat("Can we take an adaptive quiz on Recursion?")
    assert res.suggest_quiz is True
    assert res.suggested_quiz_topic == "Recursion"
    assert "Adaptive Quiz" in res.message

def test_tutor_conversation_memory():
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
    tutor.chat("What is a linked list?")
    tutor.chat("How is it different from an array?")
    assert len(tutor.history) == 4
    assert tutor.history[0].role == "user"
    assert tutor.history[1].role == "assistant"
    assert tutor.history[2].role == "user"
    assert tutor.history[3].role == "assistant"

@patch("app.student_ai.tutor.GEMINI_API_KEY", "mock-test-key-12345")
def test_tutor_mocked_gemini_api_call():
    """Verifies that when GEMINI_API_KEY is present, genai.Client is invoked properly."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = "Hello! Recursion is like nesting Russian dolls. Step 1: Base Case. Step 2: Recursive Call."
        mock_instance.models.generate_content.return_value = mock_response

        tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
        res = tutor.chat("Explain recursion to me")

        assert mock_instance.models.generate_content.called
        assert mock_client_cls.call_args.kwargs["http_options"] == {"timeout": 10_000}
        assert "Russian dolls" in res.message

def test_dynamic_suggestions_evolve_by_context():
    """Verifies that follow-up suggestions adapt dynamically based on user context."""
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")

    # Turn 1: General concept question
    res1 = tutor.chat("What is recursion?")
    assert len(res1.suggested_followups) >= 2
    # Option 3 is a quiz trigger
    assert any(is_quiz_trigger(s)[0] for s in res1.suggested_followups)

    # Turn 2: Line by line code question
    res2 = tutor.chat("Can you explain the recursion code line by line?")
    # Suggestions should adapt and be distinct from Turn 1
    assert res2.suggested_followups != res1.suggested_followups

    # Turn 3: Switch topic to Trees
    res3 = tutor.chat("Now explain Binary Search Trees")
    assert "Tree" in res3.message or "BST" in res3.message
    # Suggestions should now relate to trees or quiz on trees
    assert any("tree" in s.lower() for s in res3.suggested_followups)

def test_suggestions_zero_repetition_across_turns():
    """Verifies that suggestions are never repeatedly shown in subsequent turns."""
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
    turn1_suggestions = tutor.chat("Tell me about recursion").suggested_followups
    turn2_suggestions = tutor.chat("How does the call stack unwind?").suggested_followups
    turn3_suggestions = tutor.chat("What is the time complexity?").suggested_followups

    # Verify no overlap between turn 1 and turn 2
    overlap_1_2 = set(turn1_suggestions).intersection(set(turn2_suggestions))
    assert len(overlap_1_2) == 0, f"Found repeating suggestions between turns 1 and 2: {overlap_1_2}"

    # Verify no overlap between turn 2 and turn 3
    overlap_2_3 = set(turn2_suggestions).intersection(set(turn3_suggestions))
    assert len(overlap_2_3) == 0, f"Found repeating suggestions between turns 2 and 3: {overlap_2_3}"

def test_natural_language_quiz_triggers():
    """Verifies regex and keyword detection for starting quizzes naturally."""
    triggers = [
        ("quiz me", True, None),
        ("test my knowledge", True, None),
        ("quiz me on recursion", True, "Recursion"),
        ("give me questions on recursion", True, "Recursion"),
        ("Start an adaptive quiz on Linked Lists", True, "Linked Lists"),
        ("can we do a practice quiz on trees?", True, "Trees"),
        ("test me on sorting", True, "Sorting"),
        ("I want to practice arrays", True, "Arrays"),
        ("How does a linked list work?", False, None),
        ("Explain binary search", False, None),
    ]
    for text, expected_match, expected_topic in triggers:
        matched, topic = is_quiz_trigger(text)
        assert matched is expected_match, f"Failed for text: '{text}'"
        if expected_topic:
            assert topic == expected_topic, f"Expected topic '{expected_topic}', got '{topic}' for '{text}'"

def test_custom_questions_accepted_at_any_point():
    """Verifies that arbitrary, unconstrained custom questions are processed accurately."""
    tutor = StudentTutor(student_name="Aarav", student_level="Intermediate")

    # Ask about call stack unwinding
    res_stack = tutor.chat("How does the call stack unwind in recursion?")
    assert "Call Stack" in res_stack.message or "frame" in res_stack.message.lower()

    # Ask about complexity
    res_complexity = tutor.chat("What is the time complexity of recursion?")
    assert "O(N)" in res_complexity.message or "Complexity" in res_complexity.message

    # Ask about iterative loop equivalent
    res_iterative = tutor.chat("Can you show an iterative loop version?")
    assert "iterative" in res_iterative.message.lower() or "loop" in res_iterative.message.lower()

@patch("app.student_ai.tutor.GEMINI_API_KEY", "mock-test-key-12345")
def test_gemini_dynamic_suggestions_generation():
    """Verifies that when Gemini is available, suggestions are parsed from JSON and deduplicated."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = '["How do we avoid stack overflow?", "Can you trace n=5?", "Start an adaptive quiz on Recursion"]'
        mock_instance.models.generate_content.return_value = mock_response

        tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
        suggestions = tutor.generate_contextual_suggestions(
            user_input="How does recursion work?",
            response_text="Recursion breaks problems down into smaller instances.",
            topic="Recursion",
            cue=EmotionCue.NEUTRAL
        )
        assert len(suggestions) == 3
        assert "How do we avoid stack overflow?" in suggestions
        assert "Start an adaptive quiz on Recursion" in suggestions
        assert "How do we avoid stack overflow?" in tutor.seen_suggestions
        assert mock_client_cls.call_args.kwargs["http_options"] == {"timeout": 10_000}

def test_hcf_lcm_first_question_returns_math_not_recursion():
    """Verifies that asking about HCF/LCM as the first question returns Mathematics, not Recursion."""
    tutor = StudentTutor(student_name="Aarav", student_level="Intermediate")
    res = tutor.chat("explain hcf and lcm")

    assert res.engine_used == "offline_fallback"
    assert res.topic_detected == "Mathematics"
    # Must contain HCF, LCM, and Euclidean algorithm
    assert "hcf" in res.message.lower()
    assert "lcm" in res.message.lower()
    assert "euclidean" in res.message.lower()
    assert "12" in res.message and "18" in res.message  # Worked example present
    # Must NOT return recursion
    assert "recursion" not in res.message.lower()
    assert "factorial" not in res.message.lower()

def test_recursion_then_topic_change_to_hcf_lcm():
    """Verifies that asking about Recursion and then changing to HCF/LCM switches topic cleanly."""
    tutor = StudentTutor(student_name="Aarav", student_level="Intermediate")

    # Turn 1: Recursion
    res1 = tutor.chat("How does recursion work?")
    assert "Recursion" in res1.message
    assert tutor.current_topic == "Recursion"

    # Turn 2: Topic change to HCF and LCM
    res2 = tutor.chat("explain hcf and lcm")
    assert "hcf" in res2.message.lower()
    assert "lcm" in res2.message.lower()
    assert tutor.current_topic == "Mathematics"
    # Previous topic MUST NOT override the new question!
    assert "recursion" not in res2.message.lower()
    assert "factorial" not in res2.message.lower()

def test_hcf_lcm_follow_up_line_by_line_explanation():
    """Verifies that following up on HCF/LCM with line-by-line request explains Euclidean code, not recursion."""
    tutor = StudentTutor(student_name="Aarav", student_level="Intermediate")
    tutor.chat("explain hcf and lcm")

    res_line = tutor.chat("Can you explain the Euclidean algorithm line by line?")
    assert tutor.current_topic == "Mathematics"
    assert "Line-by-Line" in res_line.message or "Walkthrough" in res_line.message
    assert "compute_hcf" in res_line.message or "euclidean" in res_line.message.lower()
    assert "factorial" not in res_line.message.lower()

def test_topic_change_after_hcf_lcm_to_different_topic():
    """Verifies topic change after HCF/LCM to Binary Search Trees."""
    tutor = StudentTutor(student_name="Aarav", student_level="Intermediate")
    tutor.chat("explain hcf and lcm")

    res_tree = tutor.chat("Now explain binary search trees")
    assert tutor.current_topic == "Trees"
    assert "Tree" in res_tree.message or "BST" in res_tree.message
    assert "hcf" not in res_tree.message.lower()
    assert "lcm" not in res_tree.message.lower()

def test_gemini_unavailable_fallback_answers_correct_topic():
    """Verifies fallback answers the correct topic when Gemini is unconfigured."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
        res = tutor.chat("Explain HCF and LCM with an example")
        assert res.engine_used == "offline_fallback"
        assert "hcf" in res.message.lower() and "lcm" in res.message.lower()
        assert "12" in res.message and "18" in res.message

def test_gemini_available_actual_custom_question_sent_to_api():
    """Verifies that when Gemini is available, the exact user question is sent to the API."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", "mock-test-key-valid"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_instance = MagicMock()
            mock_client_cls.return_value = mock_instance
            resp1 = MagicMock()
            resp1.text = "Gemini answer: HCF is Highest Common Factor and LCM is Lowest Common Multiple."
            resp2 = MagicMock()
            resp2.text = '["How does Euclidean algorithm work?", "Can you trace 12 and 18?", "Start an adaptive quiz on Mathematics"]'
            mock_instance.models.generate_content.side_effect = [resp1, resp2]

            tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
            user_question = "Explain HCF and LCM with an example."
            res = tutor.chat(user_question)

            assert mock_instance.models.generate_content.called
            call_args_list = mock_instance.models.generate_content.call_args_list
            first_call_prompt = call_args_list[0].kwargs.get("contents", "")

            # Ensure the EXACT student query reached the prompt sent to Gemini
            assert f"STUDENT: {user_question}" in first_call_prompt
            assert res.engine_used == "gemini"
            assert "Gemini answer" in res.message

def test_gemini_api_error_handled_without_returning_unrelated_content():
    """Verifies that API errors activate fallback cleanly and still answer the correct topic."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", "mock-test-key-error"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_instance = MagicMock()
            mock_client_cls.return_value = mock_instance
            mock_instance.models.generate_content.side_effect = RuntimeError("API rate limit exceeded")

            tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
            res = tutor.chat("explain hcf and lcm")

            # Must fallback cleanly to offline engine
            assert res.engine_used == "offline_fallback"
            assert res.topic_detected == "Mathematics"
            # Must answer HCF and LCM, NOT recursion!
            assert "hcf" in res.message.lower() and "lcm" in res.message.lower()
            assert "understanding recursion" not in res.message.lower()
            assert mock_instance.models.generate_content.call_count == 1

def test_unsupported_topic_returns_clarification_not_recursion():
    """Verifies that an unsupported offline question returns clarification rather than dumping recursion."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
        res = tutor.chat("Explain quantum computing and qubit superposition")

        assert "understanding recursion" not in res.message.lower()
        assert "factorial" not in res.message.lower()
        assert "built-in curriculum" in res.message or "offline mode" in res.message.lower()
        assert "quantum computing" in res.message.lower()


@pytest.mark.parametrize(
    ("input_text", "response_format", "expected"),
    [
        ("Show recursion pseudocode", "pseudocode", "FUNCTION factorial"),
        ("Give me the algorithm for recursion", "algorithm", "RETURN n * factorial"),
        ("Show code for recursion", "code", "def factorial"),
        ("Draw a diagram for recursion", "diagram", "factorial(3)")
    ]
)
def test_offline_tutor_supports_requested_representations(input_text, response_format, expected):
    tutor = StudentTutor(student_name="Aarav", student_level="Beginner")
    response = tutor.chat(input_text)

    assert response.response_format == response_format
    assert expected in response.message
    assert "```" in response.message


def test_topic_mastery_adapts_tutor_level():
    profile = create_new_student_profile("Aarav")
    profile.learning_level = "Beginner"
    profile.topic_mastery["Recursion"].mastery_percentage = 82.0
    profile.topic_mastery["Recursion"].attempt_count = 3
    tutor = StudentTutor(student_name="Aarav", profile=profile)

    tutor.chat("Explain recursion")

    assert tutor.student_level == "Advanced"
