export type TutorRole = 'student' | 'tutor' | 'system';

export type QuickPromptType = 'eli5' | 'step_by_step' | 'real_world' | 'quiz_me' | 'custom';

export interface CodeSnippet {
  language: string;
  code: string;
  explanation?: string;
}

export interface TutorMessage {
  id: string;
  role: TutorRole;
  content: string;
  timestamp: string;
  quickPromptType?: QuickPromptType;
  codeSnippet?: CodeSnippet;
  followUpQuestions?: string[];
  suggestedAction?: {
    label: string;
    actionType: 'start_quiz' | 'next_topic';
    conceptId?: number;
    topicName?: string;
  };
  engineUsed?: 'gemini' | 'offline_fallback' | string;
  adaptationApplied?: string;
  topicDetected?: string;
  suggestQuiz?: boolean;
  suggestedQuizTopic?: string;
  sessionId?: string;
  isError?: boolean;
}

export interface TutorConcept {
  id: number;
  name: string;
  mastery: number;
  status: 'Critical Gap' | 'Needs Attention' | 'Moderate' | 'Strong';
  description: string;
  recommendedTopics: string[];
}

export interface QuickPromptOption {
  id: QuickPromptType;
  label: string;
  description: string;
  queryTemplate: (concept: string) => string;
}
