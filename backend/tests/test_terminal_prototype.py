"""
Tests for Terminal Prototype components.
Verifies persona selection, clean startup, non-interactive quiz run, graceful exit,
and fail-fast database timeout / offline fallback handling.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import OperationalError
from app.student_ai.terminal_prototype import (
    select_student_persona, print_banner, run_adaptive_quiz, get_db_session, main
)
from app.student_ai.profiler import create_new_student_profile

@pytest.fixture(autouse=True)
def default_mock_gemini_key():
    """Ensures deterministic, fast unit tests without unmocked live network calls."""
    with patch("app.student_ai.tutor.GEMINI_API_KEY", ""):
        yield

def test_print_banner():
    # Should run without error
    print_banner()

def test_select_student_persona_aarav():
    with patch("builtins.input", side_effect=["1"]):
        profile = select_student_persona(db=None)
        assert profile.student_name == "Aarav Sharma"
        assert profile.learning_level == "Intermediate"
        assert profile.topic_mastery["Recursion"].mastery_percentage == 28.0

def test_select_student_persona_priya():
    with patch("builtins.input", side_effect=["2"]):
        profile = select_student_persona(db=None)
        assert profile.student_name == "Priya Patel"
        assert profile.learning_level == "Advanced"
        assert profile.overall_mastery == 92.0

def test_select_student_persona_new_student():
    with patch("builtins.input", side_effect=["3", "Vikram Patel"]):
        profile = select_student_persona(db=None)
        assert profile.student_name == "Vikram Patel"
        assert profile.has_historical_data is False
        assert profile.learning_level == "Beginner"

def test_run_adaptive_quiz_non_interactive():
    profile = create_new_student_profile("TestStudent")
    # Simulate answering: topic selection "1" (Recursion), then answers "B", "B", "B", "B", "B", then Enter to finish
    with patch("builtins.input", side_effect=["B", "B", "B", "B", "B", ""]):
        run_adaptive_quiz(profile, topic="Recursion", db=None)

    assert profile.has_historical_data is True
    assert profile.topic_mastery["Recursion"].attempt_count == 1
    assert len(profile.quiz_history) == 1

def test_terminal_prototype_clean_exit():
    """Simulate user selecting option 5 (Exit) on startup."""
    with patch("builtins.input", side_effect=["1", "5"]):
        # Choice 1 = Aarav, Choice 5 = Exit
        main()

def test_get_db_session_fail_fast_on_error():
    """Verifies that get_db_session returns None immediately without raising exception on DB error."""
    with patch("app.database.SessionLocal", side_effect=OperationalError("Connection timed out", None, None)):
        session = get_db_session(timeout=1)
        assert session is None

def test_terminal_prototype_reaches_menu_when_db_offline(capsys):
    """Verifies that main() prints startup check, offline notice, and reaches menu when DB is offline."""
    with patch("app.student_ai.terminal_prototype.get_db_session", return_value=None):
        with patch("builtins.input", side_effect=["1", "5"]):
            main()

    captured = capsys.readouterr().out
    assert "Checking database connectivity" in captured
    assert "Operating in resilient offline mode" in captured
    assert "Choose a Student Persona to Begin:" in captured
    assert "Active Persona:" in captured
    assert "Aarav Sharma" in captured
    assert "Main Menu" in captured
    assert "Thank you for using AdaptiveClass AI Student Tutor!" in captured

def test_terminal_prototype_safely_closes_db_on_exit():
    """Verifies that main() calls db.close() in the finally block upon exit."""
    mock_db = MagicMock()
    with patch("app.student_ai.terminal_prototype.get_db_session", return_value=mock_db):
        with patch("builtins.input", side_effect=["1", "5"]):
            main()

    assert mock_db.close.called

def test_run_chat_session_selecting_suggestion_3_starts_quiz():
    """Verifies that selecting option '3' (the displayed quiz action) launches the adaptive quiz."""
    from app.student_ai.terminal_prototype import run_chat_session
    from app.student_ai.tutor import StudentTutor

    profile = create_new_student_profile("TestStudent")
    tutor = StudentTutor("TestStudent", "Beginner", profile=profile)

    with patch("app.student_ai.terminal_prototype.run_adaptive_quiz") as mock_quiz:
        # User selects option "3" (which is the quiz trigger), then types "back"
        with patch("builtins.input", side_effect=["3", "back"]):
            run_chat_session(tutor, profile=profile, db=None)

        assert mock_quiz.called
        # Check that it called run_adaptive_quiz with topic='Recursion' and in_chat=True
        call_kwargs = mock_quiz.call_args.kwargs
        assert call_kwargs.get("topic") in ["Mathematics", "Recursion"]
        assert call_kwargs.get("in_chat") is True

def test_run_chat_session_natural_language_quiz_command():
    """Verifies that natural language requests like 'quiz me on recursion' start quiz directly."""
    from app.student_ai.terminal_prototype import run_chat_session
    from app.student_ai.tutor import StudentTutor

    profile = create_new_student_profile("TestStudent")
    tutor = StudentTutor("TestStudent", "Beginner", profile=profile)

    with patch("app.student_ai.terminal_prototype.run_adaptive_quiz") as mock_quiz:
        # User types "quiz me on recursion", then "back"
        with patch("builtins.input", side_effect=["quiz me on recursion", "back"]):
            run_chat_session(tutor, profile=profile, db=None)

        assert mock_quiz.called
        call_kwargs = mock_quiz.call_args.kwargs
        assert call_kwargs.get("topic") in ["Mathematics", "Recursion"]

def test_run_chat_session_numbered_concept_selection():
    """Verifies that selecting option '1' (a concept question) submits that question to tutor."""
    from app.student_ai.terminal_prototype import run_chat_session
    from app.student_ai.tutor import StudentTutor

    profile = create_new_student_profile("TestStudent")
    tutor = StudentTutor("TestStudent", "Beginner", profile=profile)

    # User inputs "1" (the first suggested question), then "back"
    with patch("builtins.input", side_effect=["1", "back"]):
        run_chat_session(tutor, profile=profile, db=None)

    # Verify conversation history recorded the question and an answer
    assert len(tutor.history) == 2
    assert tutor.history[0].role == "user"
    assert tutor.history[0].content != "1"  # Should be the expanded suggestion text, NOT raw "1"
    assert tutor.history[1].role == "assistant"

def test_run_chat_session_invalid_number_handling(capsys):
    """Verifies that typing an out-of-range number displays a polite hint without crashing."""
    from app.student_ai.terminal_prototype import run_chat_session
    from app.student_ai.tutor import StudentTutor

    profile = create_new_student_profile("TestStudent")
    tutor = StudentTutor("TestStudent", "Beginner", profile=profile)

    # User inputs "99", then "back"
    with patch("builtins.input", side_effect=["99", "back"]):
        run_chat_session(tutor, profile=profile, db=None)

    captured = capsys.readouterr().out
    assert "Invalid option. Please choose 1-" in captured
    # History should remain empty because "99" was not passed to tutor
    assert len(tutor.history) == 0

def test_quiz_answers_update_learner_profile_and_mastery():
    """Verifies that quiz answers dynamically update mastery, attempt count, and quiz history."""
    profile = create_new_student_profile("LearnerA")
    initial_mastery = profile.topic_mastery["Recursion"].mastery_percentage
    initial_attempts = profile.topic_mastery["Recursion"].attempt_count

    assert initial_attempts == 0
    assert initial_mastery == 0.0  # Initial baseline for new profile

    # Simulate answers: B, B, B, B, B, then Enter to finish
    with patch("builtins.input", side_effect=["B", "B", "B", "B", "B", ""]):
        run_adaptive_quiz(profile, topic="Recursion", db=None)

    # After quiz, attempt count should be 1, history recorded
    assert profile.topic_mastery["Recursion"].attempt_count == 1
    assert len(profile.quiz_history) == 1
    session_record = profile.quiz_history[0]
    assert session_record.topic == "Recursion"
    assert session_record.total_questions == 5
    assert session_record.score == 3
    assert profile.has_historical_data is True


