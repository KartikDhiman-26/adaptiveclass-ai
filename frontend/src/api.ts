import type {
  ClassAnalyticsResponse,
  StudentNeedingAttentionItem,
  StudentProfileResponse,
  AdaptiveStartResponse,
  AdaptiveNextQuestionResponse,
  QuizSubmitResponse,
  StudentRecommendation
} from './types.ts';

export interface ApiConfigDiagnostics {
  mode: string;
  isProduction: boolean;
  isConfigured: boolean;
  apiBase: string;
  sanitizedHost: string;
}

/**
 * In Vite production builds, `import.meta.env.PROD` is statically replaced with `true`,
 * which allows bundlers to dead-code eliminate development-only fallback URLs.
 */
const DEV_DEFAULT_FALLBACK = (typeof import.meta !== 'undefined' && import.meta.env?.PROD)
  ? '/api'
  : (typeof process !== 'undefined' && process.env?.NODE_ENV === 'production')
    ? '/api'
    : 'http://127.0.0.1:8000/api';

/**
 * Normalizes the API base URL with strict production isolation:
 * - In production: uses VITE_API_URL, strips trailing slashes, ensures single '/api' suffix.
 * - In production: NEVER falls back to localhost or 127.0.0.1; defaults to relative '/api'.
 * - In development: defaults to 'http://127.0.0.1:8000/api' if VITE_API_URL is unset.
 */
export function normalizeApiBaseUrl(rawInput?: string, isProduction: boolean = false): string {
  const trimmed = (rawInput || '').trim();

  if (trimmed) {
    if (isProduction && (trimmed.includes('localhost') || trimmed.includes('127.0.0.1'))) {
      console.error(
        `[AdaptiveClass AI] INVALID CONFIGURATION: VITE_API_URL is set to a localhost address (${trimmed}) in production! ` +
        `Browsers on deployed websites cannot reach localhost. Falling back to relative '/api'.`
      );
      return '/api';
    }

    const withoutTrailingSlash = trimmed.replace(/\/+$/, '');
    if (withoutTrailingSlash.endsWith('/api')) {
      return withoutTrailingSlash;
    }
    return `${withoutTrailingSlash}/api`;
  }

  if (isProduction) {
    return '/api';
  }

  return DEV_DEFAULT_FALLBACK;
}

/**
 * Returns safe environment and API base URL configuration diagnostics without exposing secrets.
 */
export function getApiConfigDiagnostics(): ApiConfigDiagnostics {
  // Read directly from import.meta.env for static compile-time Vite replacement
  const isProduction = typeof import.meta !== 'undefined' && import.meta.env
    ? Boolean(import.meta.env.PROD || import.meta.env.MODE === 'production')
    : (typeof process !== 'undefined' && process.env?.NODE_ENV === 'production');

  const mode = typeof import.meta !== 'undefined' && import.meta.env
    ? String(import.meta.env.MODE || (isProduction ? 'production' : 'development'))
    : (typeof process !== 'undefined' && process.env?.NODE_ENV ? process.env.NODE_ENV : 'development');

  const rawUrl = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL !== undefined
    ? String(import.meta.env.VITE_API_URL || '').trim()
    : (typeof process !== 'undefined' && process.env?.VITE_API_URL ? String(process.env.VITE_API_URL).trim() : '');

  const isConfigured = Boolean(rawUrl);
  const apiBase = normalizeApiBaseUrl(rawUrl, isProduction);

  let sanitizedHost = 'relative (/api)';
  if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
    try {
      const parsed = new URL(apiBase);
      sanitizedHost = parsed.host;
    } catch {
      sanitizedHost = 'unknown';
    }
  }

  return {
    mode,
    isProduction,
    isConfigured,
    apiBase,
    sanitizedHost
  };
}

export function resolveApiBase(): string {
  const diag = getApiConfigDiagnostics();
  return diag.apiBase;
}

export const API_BASE = resolveApiBase();

// Safe startup diagnostic (logged once on bundle load in browser)
if (typeof window !== 'undefined') {
  const diag = getApiConfigDiagnostics();
  if (diag.isProduction) {
    if (diag.isConfigured) {
      console.info(
        `%c[AdaptiveClass AI]%c Mode: ${diag.mode} | Target: %c${diag.sanitizedHost}%c (${diag.apiBase}) | VITE_API_URL: detected`,
        'background: #0f766e; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;',
        'color: inherit; font-weight: bold;',
        'color: #0f766e; font-weight: bold;',
        'color: #78716c;'
      );
    } else {
      console.warn(
        `%c[AdaptiveClass AI]%c Mode: ${diag.mode} | VITE_API_URL: not detected. Requests targeting relative '/api'. To connect to your external FastAPI backend, configure VITE_API_URL in your hosting provider dashboard (e.g. Vercel).`,
        'background: #dc2626; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;',
        'color: #dc2626; font-weight: bold;'
      );
    }
  } else {
    console.info(
      `%c[AdaptiveClass AI]%c Mode: ${diag.mode} | Local dev targeting: %c${diag.apiBase}%c`,
      'background: #d97706; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;',
      'color: inherit;',
      'color: #d97706; font-weight: bold;',
      'color: #78716c;'
    );
  }
}

export interface StudentTokenResponse {
  user_id: number;
  name: string;
  email: string;
  role: string;
  class_id?: number | null;
  token: string;
}

export interface TutorChatRequestPayload {
  student_id: number;
  student_name?: string;
  session_id?: string | null;
  message: string;
  topic?: string | null;
  requested_format?: 'explanation' | 'pseudocode' | 'algorithm' | 'code' | 'diagram' | null;
}

export interface TutorChatResponsePayload {
  session_id: string;
  message: string;
  topic_detected?: string | null;
  detected_cue: string;
  confidence: number;
  adaptation_applied: string;
  suggested_followups: string[];
  suggest_quiz: boolean;
  suggested_quiz_topic?: string | null;
  engine_used: string;
  response_format: string;
  ethical_disclaimer: string;
}

export type ClassIdentifier =
  | number
  | string
  | { id?: number | string; class_id?: number | string; classId?: number | string; [key: string]: any };

/**
 * Normalizes any class reference (numeric ID, numeric string, or class object)
 * into a valid integer class ID.
 * Rejects DOM/React events, empty objects, invalid strings, and non-positive numbers.
 */
export function normalizeClassId(classRef: unknown): number {
  if (typeof classRef === 'number') {
    if (Number.isFinite(classRef) && !Number.isNaN(classRef) && classRef > 0) {
      return Math.floor(classRef);
    }
    throw new Error(`Invalid numeric class ID: ${classRef}`);
  }

  if (typeof classRef === 'string') {
    const trimmed = classRef.trim();
    if (/^\d+$/.test(trimmed)) {
      const parsed = parseInt(trimmed, 10);
      if (Number.isFinite(parsed) && parsed > 0) {
        return parsed;
      }
    }
    throw new Error(`Invalid string class ID: "${classRef}"`);
  }

  if (classRef && typeof classRef === 'object') {
    // Defend against DOM/React synthetic events mistakenly passed as arguments
    if ('nativeEvent' in classRef || 'target' in classRef || 'preventDefault' in classRef) {
      throw new Error(`Received DOM/React Event object instead of class ID. Check event handlers to avoid passing events directly.`);
    }

    const obj = classRef as Record<string, any>;
    const rawId = obj.id ?? obj.class_id ?? obj.classId;
    if (rawId !== undefined && rawId !== null) {
      return normalizeClassId(rawId);
    }
    throw new Error(`Class object does not contain a valid ID property ('id', 'class_id', or 'classId'): ${JSON.stringify(classRef)}`);
  }

  throw new Error(`Invalid class identifier provided: ${String(classRef)}`);
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // Prevent malformed endpoints containing serialized objects from ever being requested
  if (endpoint.includes('[object Object]') || endpoint.includes('[object%20Object]')) {
    const errorMsg = `Attempted to make API request with invalid URL containing serialized object: ${endpoint}`;
    console.error(errorMsg);
    throw new Error(errorMsg);
  }

  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${API_BASE}${normalizedEndpoint}`;
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
      let detailMsg: string;
      if (typeof err.detail === 'string') {
        detailMsg = err.detail;
      } else if (Array.isArray(err.detail)) {
        detailMsg = err.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      } else if (err.detail && typeof err.detail === 'object') {
        detailMsg = JSON.stringify(err.detail);
      } else {
        detailMsg = `HTTP Error ${res.status}`;
      }
      throw new Error(detailMsg);
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

  getStudentToken: async (studentId: number): Promise<StudentTokenResponse> => {
    return request<StudentTokenResponse>('/auth/student-token', {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId })
    });
  },

  getDemoUsers: async () => {
    return request<any[]>('/auth/demo-users');
  },

  // Classes & Analytics
  getClasses: async () => {
    return request<any[]>('/classes');
  },

  getClassAnalytics: async (classRef: ClassIdentifier): Promise<ClassAnalyticsResponse> => {
    const classId = normalizeClassId(classRef);
    return request<ClassAnalyticsResponse>(`/classes/${classId}/analytics`);
  },

  getStudentsNeedingAttention: async (classRef: ClassIdentifier): Promise<StudentNeedingAttentionItem[]> => {
    const classId = normalizeClassId(classRef);
    return request<StudentNeedingAttentionItem[]>(`/classes/${classId}/students-needing-attention`);
  },

  getClassStudents: async (classRef: ClassIdentifier): Promise<any[]> => {
    const classId = normalizeClassId(classRef);
    return request<any[]>(`/classes/${classId}/students`);
  },

  // Student Profiles & Recommendations
  getStudentProfile: async (studentId: number): Promise<StudentProfileResponse> => {
    return request<StudentProfileResponse>(`/students/${studentId}/profile`);
  },

  getStudentRecommendations: async (studentId: number): Promise<StudentRecommendation> => {
    return request<StudentRecommendation>(`/students/${studentId}/recommendations`);
  },

  // Student AI Tutor
  getTutorStatus: async () => {
    return request<{
      gemini_configured: boolean;
      model: string;
      mode: string;
      active_engine: string;
    }>('/student-tutor/status');
  },

  sendTutorChat: async (payload: TutorChatRequestPayload, token: string): Promise<TutorChatResponsePayload> => {
    return request<TutorChatResponsePayload>('/student-tutor/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
  },

  getTutorConversation: async (sessionId: string, studentId: number, token: string) => {
    return request<any>(`/student-tutor/sessions/${sessionId}?student_id=${studentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
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
  },

  // Dataset Ingestion & Validation
  validateDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/validate`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail) || `Validation failed (${res.status})`);
    }
    return res.json();
  },

  uploadDataset: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail) || `Upload failed (${res.status})`);
    }
    return res.json();
  }
};
