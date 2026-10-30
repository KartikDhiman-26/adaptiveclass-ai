from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class LoginRequest(BaseModel):
    email: Optional[str] = None
    login_id: Optional[str] = None
    password: str
    captcha_id: Optional[str] = None
    captcha_answer: Optional[str] = None

class LoginResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str  # "teacher" or "student"
    class_id: Optional[int] = None
    token: str


class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str
    expires_at: datetime


class DatasetUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    row_count: int
    error_count: int
    uploaded_at: datetime


class DatasetRowResponse(BaseModel):
    id: int
    roll_number: str
    name: str
    subject: str
    class_name: str
    marks: float
    max_marks: float
    topic: Optional[str] = None
    assessment: Optional[str] = None
    date: Optional[str] = None


class DatasetUploadDetailResponse(DatasetUploadResponse):
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class DatasetAnalysisResponse(BaseModel):
    dataset_id: int
    analysis_type: str
    model_name: str
    result: Dict[str, Any]
    created_at: datetime


class StudentAiChatRequest(BaseModel):
    message: str
    topic: Optional[str] = None
    difficulty: Optional[str] = None


class StudentAiResponse(BaseModel):
    response_type: str
    content: Dict[str, Any]
    model_name: str


class StudentAiAttemptRequest(BaseModel):
    interaction_id: Optional[int] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    score: float
    total_questions: int
    result: Dict[str, Any] = Field(default_factory=dict)


class StudentAiAttemptResponse(BaseModel):
    id: int
    student_id: int
    topic: Optional[str]
    difficulty: Optional[str]
    score: float
    total_questions: int
    created_at: datetime


class StudentAiReportResponse(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    interaction_count: int
    attempt_count: int
    report: Dict[str, Any]
    model_name: str
    created_at: datetime

class ConceptMasteryItem(BaseModel):
    concept_id: int
    concept_name: str
    mastery_percentage: float
    status_label: str  # "Strong", "Moderate", "Needs Attention", "Critical Gap"
    status_color: str  # "green", "blue", "amber", "red"

class StudentStatusDistribution(BaseModel):
    advanced: int       # >= 85%
    on_track: int       # 55% - 84%
    needs_support: int  # 40% - 54%
    needs_attention: int # < 40%
    total: int

class AiInsightResponse(BaseModel):
    learning_gap: str
    class_mastery: float
    students_below_threshold: int
    what: str
    why: str
    suggested_action: str
    enrichment_action: str
    teacher_disclaimer: str
    generated_by: str  # "Gemini 2.5 Flash" or "Autonomous Rule-Based Engine"

class ClassAnalyticsResponse(BaseModel):
    class_id: int
    class_name: str
    subject: str
    semester: str
    student_count: int
    overall_class_average: float
    concept_mastery: List[ConceptMasteryItem]
    weakest_concept: str
    strongest_concept: str
    recursion_support_count: int
    recursion_support_threshold: float
    global_distribution: StudentStatusDistribution
    ai_insight: AiInsightResponse

class StudentNeedingAttentionItem(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    email: str
    weak_concept: str
    mastery: float
    recommended_action: str

class StudentConceptScore(BaseModel):
    concept_id: int
    concept_name: str
    mastery: float
    status_label: str
    status_color: str

class RecentQuizItem(BaseModel):
    quiz_id: int
    quiz_title: str
    score: int
    total_questions: int
    accuracy: float
    timestamp: str

class StudentProfileResponse(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    email: str
    overall_mastery: float
    status_label: str
    concept_performance: List[StudentConceptScore]
    current_learning_gap: str
    recent_performance: List[RecentQuizItem]
    ai_insight: str
    suggested_steps: List[str]

class QuestionOut(BaseModel):
    question_id: int
    concept_id: int
    concept_name: str
    difficulty: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

class AdaptiveStartRequest(BaseModel):
    student_id: int
    concept_id: Optional[int] = None  # None defaults to student's weakest concept (Recursion)

class AdaptiveStartResponse(BaseModel):
    session_id: str
    concept_id: int
    concept_name: str
    current_question: QuestionOut
    question_index: int
    total_questions: int
    difficulty: str

class AdaptiveNextQuestionRequest(BaseModel):
    student_id: int
    concept_id: int
    current_question_id: int
    selected_option: str  # "A", "B", "C", "D"
    current_difficulty: str
    question_index: int
    answered_question_ids: List[int]

class AdaptiveNextQuestionResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    difficulty_change: str  # "increased", "maintained", "reinforced"
    next_question: Optional[QuestionOut]
    is_quiz_complete: bool
    current_score: int
    total_answered: int

class QuizAnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str
    is_correct: bool

class QuizSubmitRequest(BaseModel):
    student_id: int
    concept_id: int
    quiz_title: str
    answers: List[QuizAnswerSubmission]

class QuizSubmitResponse(BaseModel):
    quiz_attempt_id: int
    score: int
    total_questions: int
    accuracy: float
    old_mastery: float
    new_mastery: float
    mastery_change: float
    concept_name: str
    new_class_recursion_average: float
    new_recursion_support_count: int
    impact_message: str
