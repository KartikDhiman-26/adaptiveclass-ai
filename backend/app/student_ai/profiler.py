"""
Learner Profiling Engine for AdaptiveClass AI Student Tutor.

Tracks subject-wise mastery, topic strengths/weaknesses, quiz performance history,
estimated learning level, and revision priorities.
Supports database-backed loading (via existing models) or graceful new-student creation
with zero prior records.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Re-use existing status thresholds
def calculate_learning_level(overall_mastery: float) -> str:
    """Returns Beginner, Intermediate, or Advanced based on mastery."""
    if overall_mastery >= 75.0:
        return "Advanced"
    elif overall_mastery >= 50.0:
        return "Intermediate"
    else:
        return "Beginner"

class TopicMastery(BaseModel):
    concept_id: Optional[int] = None
    concept_name: str
    mastery_percentage: float = 0.0
    status_label: str = "Not Started"
    attempt_count: int = 0
    correct_count: int = 0

class QuizHistoryRecord(BaseModel):
    quiz_id: Optional[int] = None
    quiz_title: str
    topic: str
    score: int
    total_questions: int
    accuracy: float
    difficulty_reached: str
    date_str: str

class LearnerProfile(BaseModel):
    student_id: Optional[int] = None
    student_name: str
    email: Optional[str] = None
    subject: str = "Data Structures & Algorithms"
    overall_mastery: float = 0.0
    learning_level: str = "Beginner"
    topic_mastery: Dict[str, TopicMastery] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    areas_for_revision: List[str] = Field(default_factory=list)
    quiz_history: List[QuizHistoryRecord] = Field(default_factory=list)
    has_historical_data: bool = False

    def get_summary(self) -> str:
        """Human-readable multi-line summary of learner profile."""
        lines = [
            f"=== Learner Profile: {self.student_name} ===",
            f"Subject: {self.subject}",
            f"Learning Level: {self.learning_level} ({self.overall_mastery}% overall mastery)",
            f"Historical Data: {'Available' if self.has_historical_data else 'New Student (No prior records)'}"
        ]
        if self.strengths:
            lines.append(f"Strengths: {', '.join(self.strengths)}")
        else:
            lines.append("Strengths: None identified yet")

        if self.weaknesses:
            lines.append(f"Areas Needing Attention: {', '.join(self.weaknesses)}")
        else:
            lines.append("Areas Needing Attention: None currently flagged")

        if self.areas_for_revision:
            lines.append(f"Recommended Revision: {', '.join(self.areas_for_revision)}")

        if self.topic_mastery:
            lines.append("\nTopic Breakdown:")
            for name, tm in self.topic_mastery.items():
                lines.append(f"  - {name}: {tm.mastery_percentage:.1f}% ({tm.status_label})")

        return "\n".join(lines)


def get_concept_status_label(mastery: float) -> str:
    if mastery >= 75.0:
        return "Strong"
    elif mastery >= 60.0:
        return "Moderate"
    elif mastery >= 40.0:
        return "Needs Attention"
    else:
        return "Critical Gap"


def create_new_student_profile(student_name: str = "Student", subject: str = "Data Structures & Algorithms") -> LearnerProfile:
    """
    Creates a clean baseline profile for a new student with zero past records.
    Never invents data or makes assumptions.
    """
    default_topics = ["Recursion", "Arrays", "Linked Lists", "Trees", "Graphs", "Sorting"]
    topic_map = {}
    for t in default_topics:
        topic_map[t] = TopicMastery(
            concept_name=t,
            mastery_percentage=0.0,
            status_label="Not Started",
            attempt_count=0,
            correct_count=0
        )

    return LearnerProfile(
        student_id=None,
        student_name=student_name,
        email=None,
        subject=subject,
        overall_mastery=0.0,
        learning_level="Beginner",
        topic_mastery=topic_map,
        strengths=[],
        weaknesses=[],
        areas_for_revision=["Foundational Programming & DSA Basics"],
        quiz_history=[],
        has_historical_data=False
    )


def load_learner_profile_from_db(student_id: int, db: Session) -> Optional[LearnerProfile]:
    """
    Loads learner profile from PostgreSQL database using existing models.
    Reuses existing ConceptPerformance and QuizAttempt structures.
    """
    try:
        from app.models import Student, ConceptPerformance, Concept, QuizAttempt
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None

        # Fetch concept performance
        performances = db.query(ConceptPerformance)\
            .join(Concept)\
            .filter(ConceptPerformance.student_id == student_id)\
            .order_by(Concept.order_index.asc())\
            .all()

        topic_map = {}
        total_score = 0.0
        strengths = []
        weaknesses = []
        revision_areas = []

        for p in performances:
            c_name = p.concept.name
            score = round(float(p.mastery_score), 1)
            label = get_concept_status_label(score)
            total_score += score

            topic_map[c_name] = TopicMastery(
                concept_id=p.concept_id,
                concept_name=c_name,
                mastery_percentage=score,
                status_label=label,
                attempt_count=p.attempt_count or 1,
                correct_count=p.correct_count or 0
            )

            if score >= 75.0:
                strengths.append(c_name)
            elif score < 45.0:
                weaknesses.append(c_name)
                revision_areas.append(f"{c_name} ({score}%)")

        overall = round(total_score / max(len(performances), 1), 1) if performances else 0.0
        learning_level = calculate_learning_level(overall)

        # Fetch past quizzes
        quizzes = db.query(QuizAttempt)\
            .filter(QuizAttempt.student_id == student_id)\
            .order_by(QuizAttempt.timestamp.desc())\
            .limit(10)\
            .all()

        quiz_records = []
        for q in quizzes:
            quiz_records.append(QuizHistoryRecord(
                quiz_id=q.id,
                quiz_title=q.quiz_title,
                topic=q.quiz_title.replace("Adaptive Practice: ", ""),
                score=q.score,
                total_questions=q.total_questions,
                accuracy=round(q.accuracy, 1),
                difficulty_reached="adaptive",
                date_str=q.timestamp.strftime("%Y-%m-%d %H:%M") if q.timestamp else "Recently"
            ))

        return LearnerProfile(
            student_id=student.id,
            student_name=student.name,
            email=student.email,
            subject=(student.class_group.subject if student.class_group and student.class_group.subject else "Data Structures & Algorithms"),
            overall_mastery=overall,
            learning_level=learning_level,
            topic_mastery=topic_map,
            strengths=strengths,
            weaknesses=weaknesses,
            areas_for_revision=revision_areas or (["Beginner practice sets"] if weaknesses else []),
            quiz_history=quiz_records,
            has_historical_data=bool(performances or quizzes)
        )
    except Exception as exc:
        print(f"[PROFILER] Error loading profile from database ({exc}).")
        return None


def update_profile_with_quiz(
    profile: LearnerProfile,
    topic: str,
    score: int,
    total_questions: int,
    final_difficulty: str = "intermediate",
    db: Optional[Session] = None
) -> LearnerProfile:
    """
    Updates the learner profile in-memory (and optionally in DB) following a quiz attempt.
    Uses the project's data-driven weighted formula:
      New_Mastery = round(Old_Mastery * 0.35 + Quiz_Accuracy * 0.65, 1)
    """
    accuracy = round((score / max(total_questions, 1)) * 100.0, 1)
    old_mastery = 0.0

    if topic in profile.topic_mastery:
        existing = profile.topic_mastery[topic]
        old_mastery = existing.mastery_percentage if profile.has_historical_data else accuracy
        if profile.has_historical_data:
            new_mastery = round(old_mastery * 0.35 + accuracy * 0.65, 1)
        else:
            new_mastery = accuracy
        existing.mastery_percentage = new_mastery
        existing.status_label = get_concept_status_label(new_mastery)
        existing.attempt_count += 1
        existing.correct_count += score
    else:
        new_mastery = accuracy
        profile.topic_mastery[topic] = TopicMastery(
            concept_name=topic,
            mastery_percentage=new_mastery,
            status_label=get_concept_status_label(new_mastery),
            attempt_count=1,
            correct_count=score
        )

    # Recompute overall mastery across all active topics
    scored_topics = [t.mastery_percentage for t in profile.topic_mastery.values() if t.attempt_count > 0]
    if scored_topics:
        profile.overall_mastery = round(sum(scored_topics) / len(scored_topics), 1)
    else:
        profile.overall_mastery = accuracy

    profile.learning_level = calculate_learning_level(profile.overall_mastery)
    profile.has_historical_data = True

    # Recompute strengths and weaknesses
    profile.strengths = [
        t.concept_name for t in profile.topic_mastery.values()
        if t.attempt_count > 0 and t.mastery_percentage >= 70.0
    ]
    profile.weaknesses = [
        t.concept_name for t in profile.topic_mastery.values()
        if t.attempt_count > 0 and t.mastery_percentage < 50.0
    ]
    profile.areas_for_revision = [
        f"{t.concept_name} ({t.mastery_percentage:.1f}%)"
        for t in profile.topic_mastery.values()
        if t.attempt_count > 0 and t.mastery_percentage < 55.0
    ]

    # Add to quiz history
    from datetime import datetime, timezone
    profile.quiz_history.insert(0, QuizHistoryRecord(
        quiz_title=f"Practice: {topic}",
        topic=topic,
        score=score,
        total_questions=total_questions,
        accuracy=accuracy,
        difficulty_reached=final_difficulty,
        date_str=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    ))

    # If DB session and student_id exist, persist update
    if db is not None and profile.student_id:
        from app.models import ConceptPerformance, Concept, QuizAttempt
        concept_obj = db.query(Concept).filter(Concept.name.ilike(topic)).first()
        if not concept_obj:
            last_order = db.query(Concept.order_index).order_by(Concept.order_index.desc()).first()
            concept_obj = Concept(
                name=topic,
                subject="Data Structures & Mathematics",
                order_index=(last_order[0] or 0) + 1 if last_order else 0
            )
            db.add(concept_obj)
            db.flush()

        perf = db.query(ConceptPerformance).filter(
            ConceptPerformance.student_id == profile.student_id,
            ConceptPerformance.concept_id == concept_obj.id
        ).first()
        if perf:
            perf.mastery_score = new_mastery
            perf.attempt_count += 1
            perf.correct_count += score
        else:
            db.add(ConceptPerformance(
                student_id=profile.student_id,
                concept_id=concept_obj.id,
                mastery_score=new_mastery,
                attempt_count=1,
                correct_count=score
            ))

        db.add(QuizAttempt(
            student_id=profile.student_id,
            concept_id=concept_obj.id,
            quiz_title=f"Adaptive Practice: {topic}",
            score=score,
            total_questions=total_questions,
            accuracy=accuracy
        ))
        db.commit()

    return profile
