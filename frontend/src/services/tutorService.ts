import { TutorMessage, QuickPromptType, QuickPromptOption, TutorConcept } from '../types/tutor';
import { StudentProfileResponse } from '../types';
import { api, TutorChatResponsePayload } from '../api';

export const QUICK_PROMPTS: QuickPromptOption[] = [
  {
    id: 'eli5',
    label: "Teach me like I'm five",
    description: 'Intuitive analogies and simple mental models',
    queryTemplate: (concept) => `Can you explain ${concept} in simple everyday terms, like I'm five years old?`
  },
  {
    id: 'step_by_step',
    label: 'Explain step by step',
    description: 'Detailed trace of execution and algorithmic mechanics',
    queryTemplate: (concept) => `Walk me step-by-step through how ${concept} works under the hood with a concrete walkthrough.`
  },
  {
    id: 'real_world',
    label: 'Give me a real-life example',
    description: 'Practical industry and physical engineering analogies',
    queryTemplate: (concept) => `Where is ${concept} used in real-world software engineering or daily life?`
  },
  {
    id: 'quiz_me',
    label: 'Quiz me on this concept',
    description: 'A quick conceptual question to test your understanding',
    queryTemplate: (concept) => `Ask me a diagnostic challenge question on ${concept} to see if I truly understand it.`
  }
];

export const DEFAULT_TUTOR_CONCEPTS: TutorConcept[] = [
  {
    id: 4,
    name: 'Recursion',
    mastery: 28.0,
    status: 'Critical Gap',
    description: 'Self-referential functions, call stack frames, and terminating base conditions.',
    recommendedTopics: ['Base Case Formulation', 'Call Stack Tracing (LIFO)', 'Recurrence Relations']
  },
  {
    id: 3,
    name: 'Trees',
    mastery: 40.0,
    status: 'Needs Attention',
    description: 'Hierarchical node structures, binary search tree invariants, and depth/breadth traversals.',
    recommendedTopics: ['BST Invariants', 'In-Order Traversal', 'Tree Height & Balancing']
  },
  {
    id: 2,
    name: 'Linked Lists',
    mastery: 70.0,
    status: 'Moderate',
    description: 'Non-contiguous memory nodes connected via pointer addresses.',
    recommendedTopics: ['Two-Pointer Fast/Slow', 'Cycle Detection', 'Pointer Manipulation']
  },
  {
    id: 5,
    name: 'Graphs',
    mastery: 45.0,
    status: 'Needs Attention',
    description: 'Vertices and edges modeling arbitrary networks and reachability.',
    recommendedTopics: ['Adjacency Lists', 'BFS Shortest Paths', 'DFS Exploration']
  },
  {
    id: 1,
    name: 'Arrays',
    mastery: 91.0,
    status: 'Strong',
    description: 'Contiguous memory allocations supporting O(1) indexed lookups.',
    recommendedTopics: ['Boundary Checks', 'Kadane Subarrays', 'Two-Pointer Sliding Window']
  },
  {
    id: 6,
    name: 'Sorting',
    mastery: 48.0,
    status: 'Needs Attention',
    description: 'Algorithmic ordering paradigms including divide-and-conquer.',
    recommendedTopics: ['Merge Sort Partitioning', 'Quick Sort Pivot Selection']
  }
];

export const tutorService = {
  /**
   * Derives concepts and individual student mastery levels from student profile
   */
  getConceptsForStudent: (profile?: StudentProfileResponse | null): TutorConcept[] => {
    if (!profile || !profile.concept_performance || profile.concept_performance.length === 0) {
      return DEFAULT_TUTOR_CONCEPTS;
    }

    return profile.concept_performance.map((c) => {
      let status: 'Critical Gap' | 'Needs Attention' | 'Moderate' | 'Strong' = 'Moderate';
      if (c.mastery < 40) status = 'Critical Gap';
      else if (c.mastery < 60) status = 'Needs Attention';
      else if (c.mastery < 75) status = 'Moderate';
      else status = 'Strong';

      const foundDefault = DEFAULT_TUTOR_CONCEPTS.find(
        (dc) => dc.name.toLowerCase() === c.concept_name.toLowerCase()
      );

      return {
        id: c.concept_id,
        name: c.concept_name,
        mastery: c.mastery,
        status,
        description: foundDefault ? foundDefault.description : `Core curricular concept: ${c.concept_name}`,
        recommendedTopics: foundDefault ? foundDefault.recommendedTopics : ['Core Fundamentals', 'Practice Problems']
      };
    });
  },

  /**
   * Provides initial welcoming message when entering the AI Tutor workspace
   */
  getInitialWorkspaceMessages: (conceptName: string, studentName: string, mastery: number): TutorMessage[] => {
    const isGap = mastery < 40;
    const greeting = studentName ? `Hello ${studentName.split(' ')[0]}` : 'Hello';

    const initialFollowups: Record<string, string[]> = {
      recursion: [
        'How does recursion work step-by-step under the hood?',
        'Can you explain the base case with a simple analogy?',
        'Show me the difference between recursion and an iterative loop'
      ],
      trees: [
        'How does binary search tree lookup work?',
        'What is the difference between in-order and pre-order traversal?',
        'Why do balanced trees guarantee O(log N) operations?'
      ],
      arrays: [
        'Why are array lookups O(1) in memory?',
        'How does two-pointer technique work on arrays?',
        'What are the trade-offs between arrays and linked lists?'
      ],
      'linked lists': [
        'How do pointers connect nodes in memory?',
        'How does fast and slow pointer detect cycles?',
        'Why is inserting at head O(1) for linked lists?'
      ],
      sorting: [
        'How does merge sort use divide and conquer?',
        'Why is quicksort O(N log N) on average?',
        'Which sorting algorithm is best for nearly sorted data?'
      ],
      graphs: [
        'What is the difference between BFS and DFS?',
        'How do adjacency lists represent connections?',
        'When would you use Dijkstra algorithm?'
      ],
      mathematics: [
        'Explain HCF and LCM with a real-world example',
        'How does the Euclidean algorithm find GCD?',
        'Why is HCF(a, b) * LCM(a, b) = a * b?'
      ]
    };

    const key = conceptName.toLowerCase();
    const followUps =
      initialFollowups[key] || [
        `Can you explain ${conceptName} step by step?`,
        `Give me a real-world everyday example of ${conceptName}`,
        `Quiz me on ${conceptName} fundamentals`
      ];

    return [
      {
        id: 'msg_welcome_1',
        role: 'tutor',
        timestamp: 'Just now',
        content: `${greeting}! Welcome to your 1-on-1 Socratic study session for **${conceptName}**.\n\nYour current recorded mastery is **${mastery}%**${
          isGap ? ' — an identified priority gap from your recent class quiz.' : '.'
        }\n\nI am here to help you build solid conceptual intuition at your own pace without any pressure. How would you like to explore this topic today?`,
        followUpQuestions: followUps
      }
    ];
  },

  /**
   * Connects to the real backend `POST /api/student-tutor/chat` endpoint.
   * Passes real student identity, bearer token, session persistence, and requested format.
   */
  sendMessage: async (
    conceptName: string,
    messageText: string,
    promptType: QuickPromptType = 'custom',
    studentId: number,
    studentName?: string,
    token?: string,
    sessionId?: string | null,
    conceptId?: number
  ): Promise<TutorMessage> => {
    if (!studentId) {
      throw new Error('Please select an active student persona before starting a tutor chat session.');
    }

    // Resolve bearer token if not directly passed
    let authToken = token;
    if (!authToken) {
      const tokenRes = await api.getStudentToken(studentId);
      authToken = tokenRes.token;
    }

    let requestedFormat: 'explanation' | 'pseudocode' | 'algorithm' | 'code' | 'diagram' | null = null;
    if (promptType === 'step_by_step') {
      requestedFormat = 'algorithm';
    } else if (promptType === 'eli5' || promptType === 'real_world' || promptType === 'quiz_me') {
      requestedFormat = 'explanation';
    }

    const payload = {
      student_id: studentId,
      student_name: studentName || 'Student',
      session_id: sessionId || null,
      message: messageText,
      topic: conceptName,
      requested_format: requestedFormat
    };

    const res: TutorChatResponsePayload = await api.sendTutorChat(payload, authToken);
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    return {
      id: `tutor_${Date.now()}`,
      role: 'tutor',
      timestamp,
      quickPromptType: promptType,
      content: res.message,
      followUpQuestions: res.suggested_followups,
      engineUsed: res.engine_used,
      adaptationApplied: res.adaptation_applied,
      topicDetected: res.topic_detected || conceptName,
      suggestQuiz: res.suggest_quiz,
      suggestedQuizTopic: res.suggested_quiz_topic || undefined,
      sessionId: res.session_id,
      suggestedAction: res.suggest_quiz
        ? {
            label: `Launch Adaptive Quiz on ${res.suggested_quiz_topic || conceptName}`,
            actionType: 'start_quiz',
            conceptId: conceptId,
            topicName: res.suggested_quiz_topic || conceptName
          }
        : undefined
    };
  }
};
