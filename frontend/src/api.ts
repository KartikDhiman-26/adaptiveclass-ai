import {
  ClassAnalyticsResponse,
  StudentNeedingAttentionItem,
  StudentProfileResponse,
  AdaptiveStartResponse,
  AdaptiveNextQuestionResponse,
  QuizSubmitResponse,
  StudentRecommendation
} from './types';

const API_BASE = 'http://127.0.0.1:8000/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP Error ${res.status}`);
    }
    return res.json();
  } catch (error: any) {
    console.error(`API request error on ${url}:`, error);
    throw error;
  }
}

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    return request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  getDemoUsers: async () => {
    return request<any[]>('/auth/demo-users');
  },

  // Classes & Analytics
  getClasses: async () => {
    return request<any[]>('/classes');
  },

  getClassAnalytics: async (classId: number): Promise<ClassAnalyticsResponse> => {
    return request<ClassAnalyticsResponse>(`/classes/${classId}/analytics`);
  },

  getStudentsNeedingAttention: async (classId: number): Promise<StudentNeedingAttentionItem[]> => {
    return request<StudentNeedingAttentionItem[]>(`/classes/${classId}/students-needing-attention`);
  },

  getClassStudents: async (classId: number): Promise<any[]> => {
    return request<any[]>(`/classes/${classId}/students`);
  },

  // Student Profiles & Recommendations
  getStudentProfile: async (studentId: number): Promise<StudentProfileResponse> => {
    return request<StudentProfileResponse>(`/students/${studentId}/profile`);
  },

  getStudentRecommendations: async (studentId: number): Promise<StudentRecommendation> => {
    return request<StudentRecommendation>(`/students/${studentId}/recommendations`);
  },

  // Adaptive Quiz
  startAdaptiveQuiz: async (studentId: number, conceptId?: number): Promise<AdaptiveStartResponse> => {
    return request<AdaptiveStartResponse>('/quiz/adaptive/start', {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId, concept_id: conceptId })
    });
  },

  getNextAdaptiveQuestion: async (payload: {
    student_id: number;
    concept_id: number;
    current_question_id: number;
    selected_option: string;
    current_difficulty: string;
    question_index: number;
    answered_question_ids: number[];
  }): Promise<AdaptiveNextQuestionResponse> => {
    return request<AdaptiveNextQuestionResponse>('/quiz/adaptive/next-question', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  submitQuiz: async (payload: {
    student_id: number;
    concept_id: number;
    quiz_title: string;
    answers: Array<{ question_id: number; selected_answer: string; is_correct: boolean }>;
  }): Promise<QuizSubmitResponse> => {
    return request<QuizSubmitResponse>('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Demo Reset
  resetDemoData: async (): Promise<any> => {
    return request<any>('/demo/reset', {
      method: 'POST'
    });
  }
};
