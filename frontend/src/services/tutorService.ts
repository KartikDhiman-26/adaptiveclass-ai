import { TutorMessage, QuickPromptType, QuickPromptOption, TutorConcept } from '../types/tutor';
import { StudentProfileResponse } from '../types';

/**
 * SIMULATED PEDAGOGICAL TUTOR SERVICE (MOCK LAYER)
 * ----------------------------------------------------
 * NOTE FOR BACKEND TEAM:
 * This module isolates all AI Tutor conversational interactions.
 * When the backend endpoint (e.g., `POST /api/tutor/chat`) is ready,
 * replace the simulated delay and response generators below with a live API call.
 */

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
    if (!profile || !profile.concept_performance) {
      return DEFAULT_TUTOR_CONCEPTS;
    }

    return profile.concept_performance.map((c) => {
      let status: 'Critical Gap' | 'Needs Attention' | 'Moderate' | 'Strong' = 'Moderate';
      if (c.mastery < 40) status = 'Critical Gap';
      else if (c.mastery < 60) status = 'Needs Attention';
      else if (c.mastery < 75) status = 'Moderate';
      else status = 'Strong';

      const foundDefault = DEFAULT_TUTOR_CONCEPTS.find(dc => dc.name.toLowerCase() === c.concept_name.toLowerCase());

      return {
        id: c.concept_id,
        name: c.concept_name,
        mastery: c.mastery,
        status,
        description: foundDefault ? foundDefault.description : `Core computational concept: ${c.concept_name}`,
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
    
    return [
      {
        id: 'msg_welcome_1',
        role: 'tutor',
        timestamp: 'Just now',
        content: `${greeting}! Welcome to your 1-on-1 study session for **${conceptName}**.\n\nYour current recorded mastery is **${mastery}%**${
          isGap ? ' — an identified priority gap from your recent class quiz.' : '.'
        }\n\nI am here to help you build solid conceptual intuition at your own pace without any pressure. How would you like to explore this topic today?`,
        followUpQuestions: [
          `Why do recursive functions crash if there is no base case?`,
          `How does the computer keep track of where to return in recursion?`,
          `What is the difference between head recursion and tail recursion?`
        ]
      }
    ];
  },

  /**
   * Generates a pedagogical response based on concept, prompt type, or custom query.
   * Includes simulated async delay (400-800ms) to mirror natural interaction.
   */
  sendMessage: async (
    conceptName: string,
    messageText: string,
    promptType: QuickPromptType = 'custom'
  ): Promise<TutorMessage> => {
    // Simulate real network latency
    await new Promise((resolve) => setTimeout(resolve, 600));

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. TEACH ME LIKE I'M FIVE (ELI5)
    if (promptType === 'eli5' || messageText.toLowerCase().includes('like i\'m five') || messageText.toLowerCase().includes('eli5')) {
      if (conceptName === 'Recursion') {
        return {
          id: `tutor_${Date.now()}`,
          role: 'tutor',
          timestamp,
          quickPromptType: 'eli5',
          content: `Think of **Recursion** like a set of **Russian Nesting Dolls (Matryoshka)** 🪆\n\n1. **The Recursive Step**: You open a big doll, and inside you find another doll that looks almost the same, just slightly smaller. You keep opening them one by one.\n\n2. **The Base Case**: Eventually, you open a doll and find a **solid tiny wooden baby** that does *not* open! This is your **Base Case** — the rule that tells you "Stop opening dolls!".\n\n3. **Returning Results**: Now that you've reached the tiny baby, you close the dolls back up, one inside the other, until the whole set is complete.\n\n**The Golden Rule**: Without that tiny baby doll (the Base Case), you'd be looking for more dolls forever until your table collapses. In programming, that collapse is called a **Stack Overflow**!`,
          followUpQuestions: [
            'Can a function have more than one base case?',
            'What happens if the doll gets bigger instead of smaller?'
          ],
          suggestedAction: {
            label: 'Test this mental model in Adaptive Practice',
            actionType: 'start_quiz',
            conceptId: 4
          }
        };
      } else if (conceptName === 'Trees') {
        return {
          id: `tutor_${Date.now()}`,
          role: 'tutor',
          timestamp,
          quickPromptType: 'eli5',
          content: `Imagine a **family tree** upside down! 🌱\n\nAt the very top sits the great-grandparent (the **Root**). From them branch out parents, and from parents branch out children.\n\nIn a **Binary Search Tree (BST)**, there is a strict house rule:\n- Anyone **younger/smaller** sits on the **Left** bench.\n- Anyone **older/larger** sits on the **Right** bench.\n\nBecause everyone follows this rule, if you are looking for age 15, you never have to search the whole room — you just compare at each person and turn Left or Right!`,
          followUpQuestions: [
            'What makes a tree "balanced"?',
            'What is a leaf node?'
          ]
        };
      }
    }

    // 2. EXPLAIN STEP BY STEP
    if (promptType === 'step_by_step' || messageText.toLowerCase().includes('step by step') || messageText.toLowerCase().includes('step-by-step')) {
      if (conceptName === 'Recursion') {
        return {
          id: `tutor_${Date.now()}`,
          role: 'tutor',
          timestamp,
          quickPromptType: 'step_by_step',
          content: `Let's trace how the computer executes a recursive function step-by-step using **factorial(3)**:\n\n**Phase 1: Pushing onto the Call Stack**\n- Step 1: Call \`factorial(3)\`. It needs \`3 * factorial(2)\`. Pauses execution and pushes frame onto stack.\n- Step 2: Call \`factorial(2)\`. It needs \`2 * factorial(1)\`. Pauses and pushes frame.\n- Step 3: Call \`factorial(1)\`. It hits the **Base Case** (\`n <= 1\`)! Returns \`1\` immediately.\n\n**Phase 2: Unwinding the Stack (Popping)**\n- Step 4: \`factorial(2)\` resumes: receives \`1\`, calculates \`2 * 1 = 2\`, and returns \`2\`.\n- Step 5: \`factorial(3)\` resumes: receives \`2\`, calculates \`3 * 2 = 6\`, and returns \`6\`.\n\nThe stack is now completely clear, and the final answer is **6**.`,
          codeSnippet: {
            language: 'python',
            code: `def factorial(n):\n    # 1. Base Case: stops recursion\n    if n <= 1:\n        return 1\n    # 2. Recursive Step: breaks problem into smaller subproblem\n    return n * factorial(n - 1)`,
            explanation: 'Notice how each call reduces n toward the terminating condition (n <= 1).'
          },
          followUpQuestions: [
            'What is the maximum call stack depth for factorial(n)?',
            'Why does tail-recursion save stack space?'
          ],
          suggestedAction: {
            label: 'Try a Call Stack Tracing Problem in Quiz',
            actionType: 'start_quiz',
            conceptId: 4
          }
        };
      }
    }

    // 3. REAL LIFE EXAMPLE
    if (promptType === 'real_world' || messageText.toLowerCase().includes('real life') || messageText.toLowerCase().includes('real world')) {
      if (conceptName === 'Recursion') {
        return {
          id: `tutor_${Date.now()}`,
          role: 'tutor',
          timestamp,
          quickPromptType: 'real_world',
          content: `Here is a real-world software engineering example you use every day: **Folder Directory Scanning** 📁\n\nWhen your computer searches for a file across your hard drive:\n\n1. It looks inside the current folder.\n2. For every file it finds, it checks if it's the target.\n3. For every **subfolder** it finds, it calls the exact same \`searchFolder()\` function recursively!\n4. The **Base Case** is an empty folder or a folder with only files and no subdirectories.\n\nOther massive real-world examples:\n- **JSON / XML Parsing**: Web APIs parse nested objects using recursive descent parsers.\n- **DOM Rendering**: Your web browser parses HTML tags like \`<div><span><p></p></span></div>\` as a recursive tree.`,
          followUpQuestions: [
            'How does Google Maps use recursion in pathfinding?',
            'Can recursion cause a server to run out of memory?'
          ]
        };
      }
    }

    // 4. QUIZ ME
    if (promptType === 'quiz_me' || messageText.toLowerCase().includes('quiz me') || messageText.toLowerCase().includes('quiz')) {
      return {
        id: `tutor_${Date.now()}`,
        role: 'tutor',
        timestamp,
        quickPromptType: 'quiz_me',
        content: `Here is a quick diagnostic check for **${conceptName}**:\n\n**Question**: Look at the following recursive code snippet:\n\`\`\`python\ndef mystery(n):\n    if n == 0:\n        return 0\n    return n + mystery(n - 2)\n\`\`\`\n\nWhat happens if someone calls \`mystery(5)\`?\n\n**A)** It returns 9.\n**B)** It terminates with a Stack Overflow Error.\n**C)** It returns 0.\n**D)** It returns an infinite loop without using stack memory.\n\nTake a moment to trace \`n = 5 -> 3 -> 1 -> -1 -> ...\`! Reply with your answer and reasoning.`,
        followUpQuestions: [
          'How can we fix the base case to handle odd numbers safely?',
          'What would mystery(4) return?'
        ],
        suggestedAction: {
          label: 'Launch Full 5-Question Adaptive Quiz',
          actionType: 'start_quiz',
          conceptId: 4
        }
      };
    }

    // 5. DEFAULT / CUSTOM CONVERSATIONAL RESPONSE
    return {
      id: `tutor_${Date.now()}`,
      role: 'tutor',
      timestamp,
      quickPromptType: 'custom',
      content: `That is a great question about **${conceptName}**!\n\nWhen addressing "${messageText.slice(0, 70)}...", keep the core invariant in mind: every operation must preserve the fundamental properties of the data structure while progressing closer toward termination.\n\nWould you like me to:\n1. Break this down with a visual diagram?\n2. Show a clean Python / C++ code snippet?\n3. Relate this directly to the questions on your class exam?`,
      followUpQuestions: [
        `Explain step-by-step with code`,
        `Give me a visual ASCII representation`,
        `Ready for practice quiz`
      ]
    };
  }
};

