"""
Terminal-Based Interactive Working Prototype for AdaptiveClass AI Student Tutor.

Allows students, evaluators, and faculty to interactively experience:
  1. Conversational AI tutoring with emotion-aware adaptations.
  2. Dynamic adaptive quizzes (beginner -> intermediate -> advanced).
  3. Real-time answer evaluation and explanations.
  4. Dynamic difficulty escalation and reinforcement.
  5. Comprehensive learner profiling (with historical data or clean new student).
  6. Clean, graceful terminal startup, navigation, and exit.

Run directly via:
    python -m app.student_ai.terminal_prototype
"""

import sys
import os
from typing import Optional, List

# Ensure UTF-8 output on Windows consoles to prevent charmap encoding errors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.student_ai.emotion_detector import detect_conversational_cue, EmotionCue
from app.student_ai.profiler import (
    LearnerProfile, create_new_student_profile, load_learner_profile_from_db, update_profile_with_quiz
)
from app.student_ai.quiz_generator import (
    AdaptiveQuizSession, find_question_for_session, evaluate_student_answer,
    generate_session_summary, get_available_topics, QuizQuestion
)
from app.student_ai.tutor import StudentTutor, is_quiz_trigger

# ANSI Color codes for clean terminal presentation
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

def print_banner():
    banner = f"""{CYAN}{BOLD}
========================================================================
   AdaptiveClass AI — Student AI Learning Assistant Prototype
   (Conversational Tutor, Adaptive Quizzes & Learner Profiling)
========================================================================{RESET}
{YELLOW}Philosophy: AI augments the teacher; empowers every student.{RESET}
"""
    print(banner)

def get_db_session(timeout: Optional[int] = None):
    """
    Attempts to establish a PostgreSQL database session with a fail-fast timeout.
    Returns None immediately if PostgreSQL is unavailable or unresponsive,
    allowing the terminal prototype to proceed in offline mode.
    Never exposes database credentials in logs.
    """
    if timeout is None:
        try:
            from app.config import DB_CONNECT_TIMEOUT
            timeout = DB_CONNECT_TIMEOUT
        except Exception:
            timeout = 3

    db = None
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        # Verify connection with a fast probe query
        db.execute(text("SELECT 1;"))
        return db
    except Exception:
        if db:
            try:
                db.close()
            except Exception:
                pass
        return None

def select_student_persona(db) -> LearnerProfile:
    """Lets the user pick a demo account or create a brand new student profile."""
    print(f"\n{BOLD}Choose a Student Persona to Begin:{RESET}")
    print(f"  {CYAN}[1]{RESET} Aarav Sharma (Demo: Struggling in Recursion at 28.0% mastery)")
    print(f"  {CYAN}[2]{RESET} Priya Patel (Demo: Advanced student at 92.0% mastery)")
    print(f"  {CYAN}[3]{RESET} Brand New Student (Zero prior records, test graceful baseline)")
    print(f"  {CYAN}[4]{RESET} Enter Custom Student Name")

    while True:
        choice = input(f"\n{BOLD}Select persona (1-4) [Default: 1]: {RESET}").strip()
        if choice in ["", "1"]:
            # Aarav Sharma
            if db:
                profile = load_learner_profile_from_db(student_id=1, db=db)
                if profile:
                    return profile
            # Fallback Aarav profile if DB not reachable
            aarav = create_new_student_profile("Aarav Sharma")
            aarav.student_id = 1
            aarav.email = "student@demo.com"
            aarav.overall_mastery = 61.0
            aarav.learning_level = "Intermediate"
            aarav.has_historical_data = True
            aarav.topic_mastery["Recursion"].mastery_percentage = 28.0
            aarav.topic_mastery["Recursion"].status_label = "Critical Gap"
            aarav.topic_mastery["Recursion"].attempt_count = 3
            aarav.topic_mastery["Arrays"].mastery_percentage = 91.0
            aarav.topic_mastery["Arrays"].status_label = "Strong"
            aarav.topic_mastery["Arrays"].attempt_count = 2
            aarav.strengths = ["Arrays"]
            aarav.weaknesses = ["Recursion"]
            aarav.areas_for_revision = ["Recursion (28.0%)"]
            return aarav

        elif choice == "2":
            # Priya Patel
            if db:
                profile = load_learner_profile_from_db(student_id=2, db=db)
                if profile:
                    return profile
            priya = create_new_student_profile("Priya Patel")
            priya.student_id = 2
            priya.email = "advanced@demo.com"
            priya.overall_mastery = 92.0
            priya.learning_level = "Advanced"
            priya.has_historical_data = True
            for t in priya.topic_mastery.values():
                t.mastery_percentage = 90.0
                t.status_label = "Strong"
                t.attempt_count = 2
            priya.strengths = ["Arrays", "Recursion", "Trees", "Linked Lists", "Graphs", "Sorting"]
            return priya

        elif choice == "3":
            # Brand New Student
            name = input("Enter new student's name [Default: New Student]: ").strip() or "New Student"
            return create_new_student_profile(student_name=name)

        elif choice == "4":
            name = input("Enter student name: ").strip() or "Learner"
            return create_new_student_profile(student_name=name)

        else:
            print(f"{RED}Invalid selection. Please choose 1, 2, 3, or 4.{RESET}")

def print_suggestions_menu(suggestions: List[str]):
    """Renders contextual follow-up suggestions with clear instructions."""
    if not suggestions:
        return
    print(f"{CYAN}{BOLD}Suggested next steps:{RESET}")
    for i, s in enumerate(suggestions, 1):
        print(f"  {CYAN}[{i}]{RESET} {s}")
    print(f"\n{YELLOW}Choose an option ({BOLD}1-{len(suggestions)}{RESET}{YELLOW}) or type ANY custom question in plain English.{RESET}")
    print(f"{YELLOW}(Type {BOLD}'quiz'{RESET}{YELLOW} to practice, or {BOLD}'back'{RESET}{YELLOW} to return to main menu){RESET}\n")

def run_chat_session(
    tutor: StudentTutor,
    profile: Optional[LearnerProfile] = None,
    db = None
) -> Optional[str]:
    """
    Interactive conversational chat loop with dynamic follow-ups,
    numbered option handling, and unrestricted custom questions.
    """
    print(f"\n{CYAN}{BOLD}--- Starting Chat with AI Tutor ---{RESET}")
    print(f"{YELLOW}Ask any question about programming or DSA. Type {BOLD}'quiz'{RESET}{YELLOW} to practice, or {BOLD}'back'{RESET}{YELLOW} to return to main menu.{RESET}\n")

    print(f"{GREEN}{BOLD}AI Tutor:{RESET}\n{tutor.get_welcome()}\n")

    # Initial contextual starter suggestions
    if not tutor.last_suggestions:
        starter_followups = [
            "How does recursion work step by step?",
            "Can you explain HCF and LCM with an example?",
            "Start an adaptive quiz on Mathematics or DSA"
        ]
        tutor.last_suggestions = starter_followups
        tutor.seen_suggestions.update(starter_followups)

    print_suggestions_menu(tutor.last_suggestions)

    while True:
        try:
            user_msg = input(f"{BOLD}You ({tutor.student_name}): {RESET}").strip()
            if not user_msg:
                continue

            if user_msg.lower() in ["back", "exit", "quit", "menu"]:
                print(f"{YELLOW}Returning to main menu...{RESET}")
                break

            # 1. Check if user typed a number matching a displayed suggestion
            cleaned = user_msg.strip("[]").strip()
            if cleaned.isdigit():
                choice_idx = int(cleaned)
                if 1 <= choice_idx <= len(tutor.last_suggestions):
                    selected_text = tutor.last_suggestions[choice_idx - 1]
                    print(f"\n{CYAN}Selected: \"{selected_text}\"{RESET}\n")

                    # Check if selected option is a quiz action
                    is_quiz, q_topic = is_quiz_trigger(selected_text)
                    if is_quiz:
                        quiz_topic = q_topic or tutor.current_topic or "Recursion"
                        tutor.current_topic = quiz_topic
                        print(f"{GREEN}🎯 Starting Adaptive Quiz on {quiz_topic}!{RESET}\n")
                        if profile:
                            run_adaptive_quiz(profile, topic=quiz_topic, db=db, in_chat=True)
                            print(f"\n{CYAN}Resuming chat with your AI Tutor. What would you like to explore next?{RESET}\n")
                            fresh_followups = tutor.get_fresh_quiz_followups(quiz_topic)
                            tutor.last_suggestions = fresh_followups
                            print_suggestions_menu(fresh_followups)
                            continue
                        else:
                            return quiz_topic
                    else:
                        # Selected suggestion is a concept question -> submit as message
                        user_msg = selected_text
                else:
                    print(f"{YELLOW}Invalid option. Please choose 1-{len(tutor.last_suggestions)} or type your custom question in plain English.{RESET}\n")
                    continue

            # 2. Check if user entered a natural-language quiz request
            is_quiz, q_topic = is_quiz_trigger(user_msg)
            if is_quiz:
                quiz_topic = q_topic or tutor.current_topic or "Recursion"
                tutor.current_topic = quiz_topic
                print(f"\n{GREEN}🎯 Starting Adaptive Quiz on {quiz_topic}!{RESET}\n")
                if profile:
                    run_adaptive_quiz(profile, topic=quiz_topic, db=db, in_chat=True)
                    print(f"\n{CYAN}Resuming chat with your AI Tutor. What would you like to explore next?{RESET}\n")
                    fresh_followups = tutor.get_fresh_quiz_followups(quiz_topic)
                    tutor.last_suggestions = fresh_followups
                    print_suggestions_menu(fresh_followups)
                    continue
                else:
                    return quiz_topic

            # 3. Unrestricted custom question
            response = tutor.chat(user_msg)

            # Display emotion-adaptation indicator if detected
            if response.detected_cue != EmotionCue.NEUTRAL:
                print(f"\n{MAGENTA}[AI Adaptation: Detected {response.detected_cue.value} ({response.confidence * 100:.0f}% confidence) -> {response.adaptation_applied}]{RESET}")

            engine_label = "Gemini API" if response.engine_used == "gemini" else "Offline Pedagogical Engine"
            print(f"\n{GREEN}{BOLD}AI Tutor [{engine_label}]:{RESET}\n{response.message}\n")

            # Display newly generated, non-repeating contextual suggestions
            if response.suggested_followups:
                print_suggestions_menu(response.suggested_followups)

        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Chat session interrupted. Returning to main menu.{RESET}")
            break

    return None

def run_adaptive_quiz(
    profile: LearnerProfile,
    topic: Optional[str] = None,
    db = None,
    in_chat: bool = False
):
    """Runs a full adaptive quiz session with difficulty adjustments and scoring."""
    topics = get_available_topics()
    print(f"\n{CYAN}{BOLD}--- Adaptive AI Quiz Generator ---{RESET}")

    # Select topic if not provided
    if not topic:
        print(f"\n{BOLD}Select a Topic for Practice:{RESET}")
        for i, t in enumerate(topics, 1):
            flag = ""
            if t in profile.weaknesses:
                flag = f" {RED}(Area Needing Practice!){RESET}"
            elif t in profile.strengths:
                flag = f" {GREEN}(Known Strength){RESET}"
            print(f"  {CYAN}[{i}]{RESET} {t}{flag}")

        while True:
            sel = input(f"\n{BOLD}Choose topic (1-{len(topics)}) [Default: 1 - Recursion]: {RESET}").strip()
            if sel == "":
                topic = "Recursion"
                break
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(topics):
                    topic = topics[idx]
                    break
            except ValueError:
                pass
            print(f"{RED}Invalid selection. Please choose a valid number.{RESET}")

    # Determine starting difficulty based on profile mastery in this topic
    starting_difficulty = "beginner"
    if topic in profile.topic_mastery:
        score = profile.topic_mastery[topic].mastery_percentage
        if score >= 75.0:
            starting_difficulty = "intermediate"

    total_q = 5
    session = AdaptiveQuizSession(
        topic=topic,
        starting_difficulty=starting_difficulty,
        total_questions=total_q,
        student_id=profile.student_id
    )

    print(f"\n{GREEN}{BOLD}Starting Adaptive Quiz on {topic}!{RESET}")
    print(f"Total Questions: {total_q} | Starting Difficulty: {starting_difficulty.upper()}\n")

    question_idx = 1
    while not session.is_complete and question_idx <= total_q:
        q: Optional[QuizQuestion] = find_question_for_session(session)
        if not q:
            print(f"{YELLOW}No more questions available for {topic}. Concluding quiz.{RESET}")
            break

        print(f"------------------------------------------------------------------------")
        print(f"{BOLD}Question {question_idx} of {total_q} [{CYAN}{q.difficulty.upper()}{RESET}{BOLD}]{RESET}")
        print(f"Topic Concept: {q.concept_focus}")
        print(f"\n{q.question_text}\n")

        for opt_key, opt_text in q.options.items():
            print(f"  {BOLD}{opt_key}){RESET} {opt_text}")

        # Get answer
        while True:
            selected = input(f"\n{BOLD}Your Answer (A, B, C, or D): {RESET}").strip().upper()
            if selected in ["A", "B", "C", "D"]:
                break
            print(f"{RED}Please enter A, B, C, or D.{RESET}")

        # Evaluate
        eval_result = evaluate_student_answer(session, q, selected)

        if eval_result.is_correct:
            print(f"\n{GREEN}{BOLD}✓ Correct!{RESET}")
        else:
            print(f"\n{RED}{BOLD}✗ Incorrect.{RESET} Correct answer is: {BOLD}{eval_result.correct_answer}{RESET}")

        print(f"\n{BOLD}Explanation:{RESET} {eval_result.explanation}")

        # Difficulty progression notification
        if eval_result.difficulty_change == "increased":
            print(f"{GREEN}▲ Excellent! Increasing difficulty to: {BOLD}{eval_result.new_difficulty.upper()}{RESET}")
        elif eval_result.difficulty_change == "reinforced":
            print(f"{YELLOW}▼ Adjusting difficulty to reinforce foundations: {BOLD}{eval_result.new_difficulty.upper()}{RESET}")
        else:
            print(f"{CYAN}■ Maintaining challenge level at: {BOLD}{eval_result.new_difficulty.upper()}{RESET}")

        question_idx += 1

    # Generate and display summary
    summary = generate_session_summary(session)
    print(f"\n========================================================================")
    print(f"{GREEN}{BOLD}🎯 Quiz Completed! Final Diagnostic Summary:{RESET}")
    print(f"========================================================================")
    print(f"Topic: {summary.topic}")
    print(f"Final Score: {summary.score} / {summary.total_questions} ({summary.accuracy:.1f}%)")
    print(f"Difficulty Trajectory: {' ➔ '.join(d.capitalize() for d in summary.difficulty_trajectory)}")
    print(f"Final Challenge Level Reached: {summary.final_difficulty.upper()}")

    if summary.weak_concepts:
        print(f"\n{YELLOW}Concepts Needing Practice:{RESET}")
        for wc in summary.weak_concepts:
            print(f"  - {wc}")

    print(f"\n{CYAN}Recommended Next Steps:{RESET}")
    for rec in summary.recommendations:
        print(f"  ✓ {rec}")

    # Update profile with results
    update_profile_with_quiz(
        profile=profile,
        topic=topic,
        score=summary.score,
        total_questions=summary.total_questions,
        final_difficulty=summary.final_difficulty,
        db=db
    )
    print(f"\n{GREEN}Learner Profile successfully updated with your latest quiz results!{RESET}")
    prompt_msg = "Press Enter to resume chat..." if in_chat else "Press Enter to return to main menu..."
    input(f"\n{BOLD}{prompt_msg}{RESET}")

def display_profile(profile: LearnerProfile):
    """Displays the student's complete learner profile."""
    print(f"\n{CYAN}{BOLD}--- Current Learner Profile ---{RESET}\n")
    print(profile.get_summary())

    if profile.quiz_history:
        print(f"\n{BOLD}Recent Quiz Attempts:{RESET}")
        for q in profile.quiz_history[:5]:
            print(f"  - [{q.date_str}] {q.quiz_title}: {q.score}/{q.total_questions} ({q.accuracy}%) [Level: {q.difficulty_reached}]")

    input(f"\n{BOLD}Press Enter to return to main menu...{RESET}")

def main():
    """Main terminal prototype entry point."""
    print_banner()

    # Step 1: Print clear startup message before attempting database connection
    try:
        from app.config import DB_CONNECT_TIMEOUT
        timeout_val = DB_CONNECT_TIMEOUT
    except Exception:
        timeout_val = 3

    print(f"{CYAN}Checking database connectivity (timeout: {timeout_val}s)...{RESET}")
    db = get_db_session(timeout=timeout_val)
    if db:
        print(f"{GREEN}[OK] PostgreSQL connected. Profile changes can be persisted.{RESET}\n")
    else:
        print(f"{YELLOW}[NOTICE] Database is offline or unreachable.{RESET}")
        print(f"{YELLOW}[OFFLINE MODE] Operating in resilient offline mode with in-memory learner profiles.{RESET}\n")

    try:
        # Select student persona
        profile = select_student_persona(db)
        tutor = StudentTutor(
            student_name=profile.student_name,
            student_level=profile.learning_level,
            profile=profile
        )

        print(f"\n{GREEN}Active Persona: {BOLD}{profile.student_name}{RESET} ({profile.learning_level} Level)")

        # Main menu loop
        while True:
            print(f"\n{CYAN}{BOLD}==================== Main Menu ===================={RESET}")
            print(f"  {CYAN}[1]{RESET} 💬 Chat with AI Tutor (Conversational learning & code explanation)")
            print(f"  {CYAN}[2]{RESET} 📝 Take Adaptive AI Quiz (Dynamic difficulty scaling)")
            print(f"  {CYAN}[3]{RESET} 📊 View Learner Profile (Mastery, strengths, and weaknesses)")
            print(f"  {CYAN}[4]{RESET} 👤 Switch Student Persona")
            print(f"  {CYAN}[5]{RESET} 🚪 Exit Prototype")
            print(f"{CYAN}==================================================={RESET}")

            try:
                choice = input(f"{BOLD}Select an option (1-5): {RESET}").strip()
                if choice == "1":
                    topic_from_chat = run_chat_session(tutor, profile=profile, db=db)
                    if topic_from_chat:
                        run_adaptive_quiz(profile, topic=topic_from_chat, db=db)
                elif choice == "2":
                    run_adaptive_quiz(profile, db=db)
                elif choice == "3":
                    display_profile(profile)
                elif choice == "4":
                    profile = select_student_persona(db)
                    tutor = StudentTutor(
                        student_name=profile.student_name,
                        student_level=profile.learning_level,
                        profile=profile
                    )
                    print(f"{GREEN}Switched to: {profile.student_name}{RESET}")
                elif choice in ["5", "exit", "quit", "q"]:
                    print(f"\n{CYAN}Thank you for using AdaptiveClass AI Student Tutor! Keep learning! 🎓{RESET}\n")
                    break
                else:
                    print(f"{RED}Invalid option. Please choose 1 to 5.{RESET}")
            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{CYAN}Exiting AdaptiveClass AI Prototype cleanly. Goodbye! 🎓{RESET}\n")
                break
    finally:
        # Ensure database session is closed safely on any exit path
        if db:
            try:
                db.close()
            except Exception:
                pass

if __name__ == "__main__":
    main()
