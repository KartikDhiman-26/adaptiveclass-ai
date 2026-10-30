export interface ConceptMasteryItem {
  concept_id: number;
  concept_name: string;
  mastery_percentage: number;
  status_label: 'Strong' | 'Moderate' | 'Needs Attention' | 'Critical Gap' | string;
  status_color: 'green' | 'blue' | 'amber' | 'red' | string;
}

export interface StudentStatusDistribution {
  advanced: number;
  on_track: number;
  needs_support: number;
  needs_attention: number;
  total: number;
}

export interface AiInsightResponse {
  learning_gap: string;
  class_mastery: number;
  students_below_threshold: number;
  what: string;
  why: string;
  suggested_action: string;
  enrichment_action: string;
  teacher_disclaimer: string;
  generated_by: string;
}

export interface ClassAnalyticsResponse {
  class_id: number;
  class_name: string;
  subject: string;
  semester: string;
  student_count: number;
  overall_class_average: number;
  concept_mastery: ConceptMasteryItem[];
  weakest_concept: string;
  strongest_concept: string;
  recursion_support_count: number;
  recursion_support_threshold: number;
  global_distribution: StudentStatusDistribution;
  ai_insight: AiInsightResponse;
}

export interface StudentNeedingAttentionItem {
  student_id: number;
  student_name: string;
  roll_number: string;
  email: string;
  weak_concept: string;
  mastery: number;
  recommended_action: string;
}

export interface StudentConceptScore {
  concept_id: number;
  concept_name: string;
  mastery: number;
  status_label: string;
  status_color: string;
}

export interface RecentQuizItem {
  quiz_id: number;
  quiz_title: string;
  score: number;
  total_questions: number;
  accuracy: number;
  timestamp: string;
}

export interface StudentProfileResponse {
  student_id: number;
  student_name: string;
  roll_number: string;
  email: string;
  overall_mastery: number;
  status_label: string;
  concept_performance: StudentConceptScore[];
  current_learning_gap: string;
  recent_performance: RecentQuizItem[];
  ai_insight: string;
  suggested_steps: string[];
}

export interface QuestionOut {
  question_id: number;
  concept_id: number;
  concept_name: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

export interface AdaptiveStartResponse {
  session_id: string;
  concept_id: number;
  concept_name: string;
  current_question: QuestionOut;
  question_index: number;
  total_questions: number;
  difficulty: string;
}

export interface AdaptiveNextQuestionResponse {
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  difficulty_change: 'increased' | 'maintained' | 'reinforced';
  next_question: QuestionOut | null;
  is_quiz_complete: boolean;
  current_score: number;
  total_answered: number;
}

export interface QuizSubmitResponse {
  quiz_attempt_id: number;
  score: number;
  total_questions: number;
  accuracy: number;
  old_mastery: number;
  new_mastery: number;
  mastery_change: number;
  concept_name: string;
  new_class_recursion_average: number;
  new_recursion_support_count: number;
  impact_message: string;
}

export interface StudentRecommendation {
  student_id: number;
  student_name: string;
  weak_concept: string;
  current_mastery: number;
  recommendation_title: string;
  reason: string;
  topics: string[];
  estimated_minutes: number;
  difficulty_entry: string;
}
