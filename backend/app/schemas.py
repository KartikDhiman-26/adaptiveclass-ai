from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str  # "teacher" or "student"
    class_id: Optional[int] = None
    token: str

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
    generated_by: str  # Configured Gemini model or the deterministic fallback

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


# --- Student AI Tutor Schemas ---

class TutorChatRequest(BaseModel):
    student_id: Optional[int] = None
    student_name: Optional[str] = "Student"
    session_id: Optional[str] = None
    message: str
    topic: Optional[str] = None
    requested_format: Optional[Literal["explanation", "pseudocode", "algorithm", "code", "diagram"]] = None

class TutorChatResponse(BaseModel):
    session_id: str
    message: str
    topic_detected: Optional[str] = None
    detected_cue: str
    confidence: float
    adaptation_applied: str
    suggested_followups: List[str]
    suggest_quiz: bool
    suggested_quiz_topic: Optional[str] = None
    engine_used: str = "offline_fallback"
    response_format: str = "explanation"
    ethical_disclaimer: str

class TutorConversationMessageResponse(BaseModel):
    role: str
    content: str
    created_at: str

class TutorConversationResponse(BaseModel):
    session_id: str
    current_topic: Optional[str] = None
    messages: List[TutorConversationMessageResponse]

class TutorQuizStartRequest(BaseModel):
    student_id: Optional[int] = None
    student_name: Optional[str] = "Student"
    topic: Optional[str] = None
    chat_session_id: Optional[str] = None
    starting_difficulty: Optional[Literal["beginner", "intermediate", "advanced"]] = None

class TutorQuizQuestionItem(BaseModel):
    question_id: str
    topic: str
    difficulty: str
    question_text: str
    options: Dict[str, str]
    concept_focus: str

class TutorQuizStartResponse(BaseModel):
    session_id: str
    topic: str
    current_difficulty: str
    first_question: TutorQuizQuestionItem
    total_questions: int

class TutorQuizResumeResponse(BaseModel):
    session_id: str
    topic: str
    current_difficulty: str
    total_questions: int
    current_question: Optional[TutorQuizQuestionItem] = None
    answered_count: int
    current_score: int
    is_complete: bool

class TutorQuizAnswerRequest(BaseModel):
    session_id: str
    student_id: Optional[int] = None
    student_name: Optional[str] = "Student"
    topic: str
    question_id: str
    selected_option: str
    current_difficulty: str

class TutorQuizAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    difficulty_change: str
    new_difficulty: str
    next_question: Optional[TutorQuizQuestionItem] = None
    current_score: int
    is_complete: bool
