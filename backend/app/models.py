from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship, synonym
from app.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    department = Column(String(100), default="Computer Science & Engineering")
    hashed_password = Column(String(255), nullable=False)

    classes = relationship("Class", back_populates="teacher", cascade="all, delete-orphan")
    subjects = relationship("TeacherSubject", back_populates="teacher", cascade="all, delete-orphan")
    dataset_uploads = relationship("DatasetUpload", back_populates="teacher", cascade="all, delete-orphan")
    assessment_records = relationship("AssessmentRecord", back_populates="teacher", cascade="all, delete-orphan")


class Mentor(Base):
    __tablename__ = "mentors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


class CaptchaChallenge(Base):
    __tablename__ = "captcha_challenges"

    id = Column(String(64), primary_key=True)
    question = Column(String(255), nullable=False)
    answer_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class TeacherSubject(Base):
    __tablename__ = "teacher_subjects"
    __table_args__ = (UniqueConstraint("teacher_id", "subject", name="uq_teacher_subject"),)

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject = Column(String(100), nullable=False)

    teacher = relationship("Teacher", back_populates="subjects")


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    subject = Column(String(100), nullable=False)
    semester = Column(String(50), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="class_group", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    class_group = relationship("Class", back_populates="students")
    performances = relationship("ConceptPerformance", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    ai_interactions = relationship("StudentAIInteraction", back_populates="student", cascade="all, delete-orphan")
    ai_attempts = relationship("StudentAIAttempt", back_populates="student", cascade="all, delete-orphan")
    ai_reports = relationship("StudentAIReport", back_populates="student", cascade="all, delete-orphan")


class StudentAIInteraction(Base):
    __tablename__ = "student_ai_interactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    topic = Column(String(150), nullable=True)
    difficulty = Column(String(50), nullable=True)
    response_json = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="ai_interactions")


class StudentAIAttempt(Base):
    __tablename__ = "student_ai_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    interaction_id = Column(Integer, ForeignKey("student_ai_interactions.id"), nullable=True)
    topic = Column(String(150), nullable=True)
    difficulty = Column(String(50), nullable=True)
    score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="ai_attempts")


class StudentAIReport(Base):
    __tablename__ = "student_ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("Student", back_populates="ai_reports")


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    subject = Column(String(100), default="Data Structures")
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    questions = relationship("Question", back_populates="concept", cascade="all, delete-orphan")
    performances = relationship("ConceptPerformance", back_populates="concept", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    difficulty = Column(String(20), nullable=False)  # "beginner", "intermediate", "advanced"
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_answer = Column(String(5), nullable=False)  # "A", "B", "C", "D"
    explanation = Column(Text, nullable=True)

    concept = relationship("Concept", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    quiz_title = Column(String(150), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)  # percentage, e.g. 80.0
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    student = relationship("Student", back_populates="quiz_attempts")
    answers = relationship("QuizAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"

    id = Column(Integer, primary_key=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(String(5), nullable=False)
    is_correct = Column(Boolean, nullable=False)

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")


class TutorConversation(Base):
    __tablename__ = "tutor_conversations"

    id = Column(String(36), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    student_name = Column(String(100), nullable=False, default="Student")
    current_topic = Column(String(100), nullable=True)
    seen_suggestions = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    messages = relationship(
        "TutorConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="TutorConversationMessage.id"
    )


class TutorConversationMessage(Base):
    __tablename__ = "tutor_conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        String(36),
        ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("TutorConversation", back_populates="messages")


class TutorPracticeSession(Base):
    __tablename__ = "tutor_practice_sessions"

    id = Column(String(36), primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    student_name = Column(String(100), nullable=False, default="Student")
    topic = Column(String(100), nullable=False)
    state_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class ConceptPerformance(Base):
    __tablename__ = "concept_performance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    mastery_score = Column(Float, nullable=False)  # 0.0 - 100.0
    attempt_count = Column(Integer, default=1)
    correct_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    student = relationship("Student", back_populates="performances")
    concept = relationship("Concept", back_populates="performances")


class DatasetUpload(Base):
    __tablename__ = "dataset_uploads"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=True, default="csv")
    uploaded_by_id = Column(Integer, nullable=True, index=True)
    uploaded_by_role = Column(String(20), nullable=True, default="teacher")
    class_name = Column(String(100), nullable=True)
    subject = Column(String(100), nullable=True)
    assessment_name = Column(String(150), nullable=True)
    total_records = Column(Integer, default=0, nullable=False)
    valid_records = Column(Integer, default=0, nullable=False)
    duplicate_records = Column(Integer, default=0, nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # "processing", "completed", "failed", "processed"
    upload_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    column_mapping = Column(Text, nullable=True)

    # Synonym for cross-compatibility between datasets router and assessment repository
    uploaded_at = synonym("upload_timestamp")

    teacher = relationship("Teacher", back_populates="dataset_uploads")
    records = relationship("AssessmentRecord", back_populates="dataset", cascade="all, delete-orphan")
    rows = relationship("DatasetRow", back_populates="dataset", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="dataset", cascade="all, delete-orphan")


class DatasetRow(Base):
    __tablename__ = "dataset_rows"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    roll_number = Column(String(50), nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    class_name = Column(String(150), nullable=False, index=True)
    marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    topic = Column(String(150), nullable=True, index=True)
    assessment = Column(String(150), nullable=True)
    assessment_date = Column(String(50), nullable=True)

    dataset = relationship("DatasetUpload", back_populates="rows")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("dataset_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("DatasetUpload", back_populates="analyses")


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_upload_id = Column(Integer, ForeignKey("dataset_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)

    roll_number = Column(String(50), nullable=False, index=True)
    student_name = Column(String(120), nullable=False)
    class_name = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    assessment_name = Column(String(150), nullable=False)
    marks_obtained = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    assessment_date = Column(String(50), nullable=False)

    # Column synonyms for flexibility across CSV representations
    rollno = synonym("roll_number")
    name = synonym("student_name")
    marks = synonym("marks_obtained")
    assessment = synonym("assessment_name")
    date = synonym("assessment_date")

    dataset = relationship("DatasetUpload", back_populates="records")
    teacher = relationship("Teacher", back_populates="assessment_records")
