"""
Adaptive AI Quiz Generator.

Generates and manages multi-tier adaptive quizzes (beginner, intermediate, advanced).
Adjusts difficulty dynamically based on real-time student performance.
Evaluates answers with detailed explanations, detects weak concepts,
and recommends targeted next steps.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_REQUEST_TIMEOUT_MS
from app.student_ai.prompts import QUIZ_QUESTION_GENERATION_PROMPT, LEARNING_RECOMMENDATIONS_PROMPT

DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

class QuizQuestion(BaseModel):
    question_id: str
    topic: str
    difficulty: str  # beginner, intermediate, advanced
    question_text: str
    options: Dict[str, str]  # "A": "...", "B": "...", "C": "...", "D": "..."
    correct_answer: str      # "A", "B", "C", or "D"
    explanation: str
    concept_focus: str

class AnswerEvaluation(BaseModel):
    is_correct: bool
    selected_answer: str
    correct_answer: str
    explanation: str
    previous_difficulty: str
    new_difficulty: str
    difficulty_change: str  # "increased", "maintained", "reinforced"
    current_score: int
    total_answered: int
    is_quiz_complete: bool

class QuizSessionSummary(BaseModel):
    topic: str
    score: int
    total_questions: int
    accuracy: float
    difficulty_trajectory: List[str]
    final_difficulty: str
    weak_concepts: List[str]
    recommendations: List[str]


# Curated question repository for core topics across all 3 difficulties.
# Ensures 100% offline reliability, zero latency, and comprehensive coverage.
OFFLINE_QUESTION_BANK: List[Dict[str, Any]] = [
    # --- MATHEMATICS (HCF & LCM) ---
    {
        "id": "math-beg-1",
        "topic": "Mathematics",
        "difficulty": "beginner",
        "question_text": "What is the Highest Common Factor (HCF / GCD) of 12 and 18?",
        "options": {
            "A": "3",
            "B": "6",
            "C": "12",
            "D": "36"
        },
        "correct_answer": "B",
        "explanation": "Factors of 12 are {1, 2, 3, 4, 6, 12} and factors of 18 are {1, 2, 3, 6, 9, 18}. The common factors are {1, 2, 3, 6}, and the highest is 6.",
        "concept_focus": "HCF Definition & Factoring"
    },
    {
        "id": "math-beg-2",
        "topic": "Mathematics",
        "difficulty": "beginner",
        "question_text": "What is the Lowest Common Multiple (LCM) of 4 and 6?",
        "options": {
            "A": "12",
            "B": "24",
            "C": "2",
            "D": "8"
        },
        "correct_answer": "A",
        "explanation": "Multiples of 4 are {4, 8, 12, 16...} and multiples of 6 are {6, 12, 18...}. The smallest positive common multiple is 12.",
        "concept_focus": "LCM Definition & Common Multiples"
    },
    {
        "id": "math-int-1",
        "topic": "Mathematics",
        "difficulty": "intermediate",
        "question_text": "Given two positive integers with HCF = 6 and product = 216, what is their LCM?",
        "options": {
            "A": "18",
            "B": "36",
            "C": "72",
            "D": "1296"
        },
        "correct_answer": "B",
        "explanation": "Using the fundamental relation HCF(a, b) * LCM(a, b) = a * b: 6 * LCM = 216, therefore LCM = 216 / 6 = 36.",
        "concept_focus": "Fundamental Property: HCF * LCM = Product"
    },
    {
        "id": "math-int-2",
        "topic": "Mathematics",
        "difficulty": "intermediate",
        "question_text": "In the Euclidean algorithm for computing GCD(a, b): 'while b != 0: a, b = b, a % b', which mathematical property makes it correct?",
        "options": {
            "A": "GCD(a, b) = GCD(b, a % b)",
            "B": "GCD(a, b) = GCD(a - b, b - a)",
            "C": "GCD(a, b) = GCD(a * b, a / b)",
            "D": "GCD(a, b) = GCD(a + b, a - b)"
        },
        "correct_answer": "A",
        "explanation": "The Euclidean algorithm relies on the theorem that any common divisor of a and b also divides their remainder (a % b), so GCD(a, b) = GCD(b, a % b).",
        "concept_focus": "Euclidean Algorithm Remainder Theorem"
    },
    {
        "id": "math-adv-1",
        "topic": "Mathematics",
        "difficulty": "advanced",
        "question_text": "According to Lamé's Theorem, what is the tight asymptotic bound on the number of division steps taken by the Euclidean algorithm to compute GCD(a, b) where a > b?",
        "options": {
            "A": "O(b)",
            "B": "At most 5 times the number of decimal digits in b (O(log b))",
            "C": "O(sqrt(b))",
            "D": "O(b^2)"
        },
        "correct_answer": "B",
        "explanation": "Lamé's theorem proves that the worst case occurs for consecutive Fibonacci numbers, bounding the number of division steps to at most 5 * (number of decimal digits of b), establishing O(log b) logarithmic time complexity.",
        "concept_focus": "Asymptotic Complexity & Lamé's Theorem"
    },
    # --- RECURSION ---
    {
        "id": "rec-beg-1",
        "topic": "Recursion",
        "difficulty": "beginner",
        "question_text": "What is the primary purpose of a 'base case' in a recursive function?",
        "options": {
            "A": "To accelerate function execution speed",
            "B": "To prevent infinite recursion and terminate the recursive calls",
            "C": "To allocate dynamic heap memory",
            "D": "To return multiple data types"
        },
        "correct_answer": "B",
        "explanation": "A base case specifies the terminating condition for recursion. Without it, the function calls itself indefinitely until the call stack overflows.",
        "concept_focus": "Base Case Purpose"
    },
    {
        "id": "rec-beg-2",
        "topic": "Recursion",
        "difficulty": "beginner",
        "question_text": "Which fundamental data structure does the system runtime implicitly use to track recursive function calls?",
        "options": {
            "A": "Queue (FIFO)",
            "B": "Call Stack (LIFO)",
            "C": "Hash Map",
            "D": "Min-Heap"
        },
        "correct_answer": "B",
        "explanation": "Every recursive call pushes an execution frame onto the system Call Stack (Last-In, First-Out). When a call returns, its frame is popped.",
        "concept_focus": "Call Stack Mechanics"
    },
    {
        "id": "rec-int-1",
        "topic": "Recursion",
        "difficulty": "intermediate",
        "question_text": "Consider the following recursive code:\n\ndef f(n):\n    if n <= 1:\n        return 1\n    return f(n - 1) + f(n - 2)\n\nWhat is the approximate time complexity of this unmemoized Fibonacci function?",
        "options": {
            "A": "O(N)",
            "B": "O(N log N)",
            "C": "O(2^N)",
            "D": "O(N^2)"
        },
        "correct_answer": "C",
        "explanation": "Because each call branches into two sub-calls without caching (memoization), the recursion tree has a branching factor of 2 with depth N, yielding O(2^N) exponential time.",
        "concept_focus": "Recursive Time Complexity & Overlapping Subproblems"
    },
    {
        "id": "rec-int-2",
        "topic": "Recursion",
        "difficulty": "intermediate",
        "question_text": "What is 'tail recursion'?",
        "options": {
            "A": "Recursion where the recursive call is the very last operation performed before returning",
            "B": "Recursion that only runs on linked list tails",
            "C": "A recursive function with two or more base cases",
            "D": "Recursion that requires exponential auxiliary memory"
        },
        "correct_answer": "A",
        "explanation": "In tail recursion, the recursive call is the final operation in the function. Tail-call optimization allows compilers to reuse the current stack frame instead of creating a new one.",
        "concept_focus": "Tail Recursion Optimization"
    },
    {
        "id": "rec-adv-1",
        "topic": "Recursion",
        "difficulty": "advanced",
        "question_text": "According to the Master Theorem, what is the tight asymptotic bound for T(N) = 2T(N/2) + O(N)?",
        "options": {
            "A": "O(N)",
            "B": "O(N log N)",
            "C": "O(N^2)",
            "D": "O(log N)"
        },
        "correct_answer": "B",
        "explanation": "Here a = 2, b = 2, and f(N) = O(N). Since log_b(a) = log_2(2) = 1, and f(N) = Theta(N^1), Case 2 of the Master Theorem applies, giving Theta(N log N). This is the exact recurrence for Merge Sort.",
        "concept_focus": "Master Theorem Recurrence Solving"
    },

    # --- ARRAYS ---
    {
        "id": "arr-beg-1",
        "topic": "Arrays",
        "difficulty": "beginner",
        "question_text": "What is the time complexity of accessing an element at a known index in a standard array?",
        "options": {
            "A": "O(1)",
            "B": "O(N)",
            "C": "O(log N)",
            "D": "O(N^2)"
        },
        "correct_answer": "A",
        "explanation": "Arrays store elements in contiguous memory locations, allowing the memory address of any index i to be calculated directly as Base_Address + i * element_size in O(1) constant time.",
        "concept_focus": "Random Access & Contiguous Memory"
    },
    {
        "id": "arr-int-1",
        "topic": "Arrays",
        "difficulty": "intermediate",
        "question_text": "Which algorithmic technique solves the 'Maximum Subarray Sum' problem in O(N) linear time and O(1) auxiliary space?",
        "options": {
            "A": "Kadane's Algorithm",
            "B": "Floyd-Warshall Algorithm",
            "C": "Dijkstra's Algorithm",
            "D": "Binary Search"
        },
        "correct_answer": "A",
        "explanation": "Kadane's algorithm keeps a running current_sum and updates max_sum dynamically in a single pass, resetting current_sum to 0 whenever it drops below zero.",
        "concept_focus": "Kadane's Dynamic Programming Algorithm"
    },
    {
        "id": "arr-adv-1",
        "topic": "Arrays",
        "difficulty": "advanced",
        "question_text": "When a dynamic array (such as Python list or C++ std::vector) doubles its capacity upon filling up, what is the amortized cost per append operation?",
        "options": {
            "A": "O(N)",
            "B": "O(1) amortized",
            "C": "O(log N)",
            "D": "O(N log N)"
        },
        "correct_answer": "B",
        "explanation": "Although copying elements takes O(N) time when doubling occurs, doubling happens exponentially less frequently. Spread across all insertions, the amortized cost per append is O(1).",
        "concept_focus": "Amortized Complexity Analysis"
    },

    # --- LINKED LISTS ---
    {
        "id": "ll-beg-1",
        "topic": "Linked Lists",
        "difficulty": "beginner",
        "question_text": "In a singly linked list, what does each node store besides its data value?",
        "options": {
            "A": "An array index",
            "B": "A reference / pointer to the next node",
            "C": "A pointer to the parent node",
            "D": "The total length of the list"
        },
        "correct_answer": "B",
        "explanation": "A singly linked list node contains two components: data value and a pointer (or reference) to the subsequent node in sequence.",
        "concept_focus": "Node Pointer Anatomy"
    },
    {
        "id": "ll-int-1",
        "topic": "Linked Lists",
        "difficulty": "intermediate",
        "question_text": "Which pointer strategy detects a cycle in a linked list using O(1) auxiliary space?",
        "options": {
            "A": "Depth-First Search",
            "B": "Floyd's Tortoise and Hare (Slow & Fast Pointers)",
            "C": "Hash Set of visited node references",
            "D": "Binary Search"
        },
        "correct_answer": "B",
        "explanation": "Floyd's cycle-finding algorithm moves a slow pointer by 1 step and a fast pointer by 2 steps. If a cycle exists, they will inevitably meet inside the loop in O(N) time and O(1) space.",
        "concept_focus": "Two-Pointer Floyd Cycle Detection"
    },
    {
        "id": "ll-adv-1",
        "topic": "Linked Lists",
        "difficulty": "advanced",
        "question_text": "What is the primary cache-locality advantage of an Array over a Linked List during sequential iteration?",
        "options": {
            "A": "Arrays use less code",
            "B": "Contiguous array elements leverage CPU cache line pre-fetching, whereas linked list nodes scattered across heap cause cache misses",
            "C": "Linked lists cannot store primitive integers",
            "D": "Linked lists require garbage collection on every step"
        },
        "correct_answer": "B",
        "explanation": "CPUs fetch entire cache lines into L1/L2 caches. Contiguous array memory ensures subsequent elements are already in high-speed cache, drastically outperforming pointer chasing across fragmented heap memory.",
        "concept_focus": "Hardware Cache Locality & Spatial Locality"
    },

    # --- TREES ---
    {
        "id": "tree-beg-1",
        "topic": "Trees",
        "difficulty": "beginner",
        "question_text": "In a Binary Search Tree (BST), where are keys smaller than the root always located?",
        "options": {
            "A": "In the right subtree",
            "B": "In the left subtree",
            "C": "At the leaves only",
            "D": "In random order"
        },
        "correct_answer": "B",
        "explanation": "The fundamental BST invariant states that all keys in the left subtree are strictly less than the root node, and all keys in the right subtree are greater than or equal to the root.",
        "concept_focus": "BST Invariant Property"
    },
    {
        "id": "tree-int-1",
        "topic": "Trees",
        "difficulty": "intermediate",
        "question_text": "Which tree traversal of a valid Binary Search Tree produces the node values in strictly sorted ascending order?",
        "options": {
            "A": "Pre-order Traversal (Root, Left, Right)",
            "B": "Post-order Traversal (Left, Right, Root)",
            "C": "In-order Traversal (Left, Root, Right)",
            "D": "Level-order Traversal (BFS)"
        },
        "correct_answer": "C",
        "explanation": "In-order traversal visits Left -> Root -> Right. Because Left < Root < Right in a BST, in-order traversal naturally yields sorted keys in O(N) time.",
        "concept_focus": "In-Order Tree Traversal"
    },
    {
        "id": "tree-adv-1",
        "topic": "Trees",
        "difficulty": "advanced",
        "question_text": "In an AVL tree, what is the maximum permissible difference between the heights of the left and right subtrees for any node?",
        "options": {
            "A": "0",
            "B": "1",
            "C": "2",
            "D": "log N"
        },
        "correct_answer": "B",
        "explanation": "The AVL balance factor condition requires that |height(left) - height(right)| <= 1 for every node. When this is violated by an insertion or deletion, tree rotations restore balance in O(1) time.",
        "concept_focus": "AVL Tree Height Balance Factor"
    },

    # --- GRAPHS ---
    {
        "id": "graph-beg-1",
        "topic": "Graphs",
        "difficulty": "beginner",
        "question_text": "What data structure is standardly used to implement Breadth-First Search (BFS) in a graph?",
        "options": {
            "A": "Queue (FIFO)",
            "B": "Stack (LIFO)",
            "C": "Priority Queue",
            "D": "Hash Set only"
        },
        "correct_answer": "A",
        "explanation": "BFS explores nodes level-by-level in concentric rings, requiring a Queue to process nodes in the order they were first discovered.",
        "concept_focus": "BFS Queue Mechanics"
    },
    {
        "id": "graph-int-1",
        "topic": "Graphs",
        "difficulty": "intermediate",
        "question_text": "For a sparse graph with V vertices and E edges, which representation is more space-efficient?",
        "options": {
            "A": "Adjacency Matrix (O(V^2))",
            "B": "Adjacency List (O(V + E))",
            "C": "Incidence Matrix (O(V * E))",
            "D": "Complete Edge Matrix"
        },
        "correct_answer": "B",
        "explanation": "For sparse graphs where E << V^2, an Adjacency List consumes only O(V + E) space, avoiding the O(V^2) memory footprint of an Adjacency Matrix.",
        "concept_focus": "Graph Representation Tradeoffs"
    },
    {
        "id": "graph-adv-1",
        "topic": "Graphs",
        "difficulty": "advanced",
        "question_text": "Why does Dijkstra's shortest path algorithm fail or produce incorrect results on graphs with negative edge weights?",
        "options": {
            "A": "It crashes with a recursion error",
            "B": "It greedily assumes that once a vertex is finalized (popped from min-heap), its shortest path cannot decrease, which is violated by negative edges",
            "C": "It cannot handle directed graphs",
            "D": "It requires all vertices to have degree 2"
        },
        "correct_answer": "B",
        "explanation": "Dijkstra's greedy invariant assumes paths only get longer as edge weights are added. A negative edge can retroactively provide a cheaper path to an already finalized node. Bellman-Ford must be used instead.",
        "concept_focus": "Dijkstra Greedy Invariant & Negative Edges"
    },

    # --- SORTING ---
    {
        "id": "sort-beg-1",
        "topic": "Sorting",
        "difficulty": "beginner",
        "question_text": "Which sorting algorithm repeatedly finds the minimum element from the unsorted part and places it at the beginning?",
        "options": {
            "A": "Bubble Sort",
            "B": "Selection Sort",
            "C": "Merge Sort",
            "D": "Quick Sort"
        },
        "correct_answer": "B",
        "explanation": "Selection Sort divides the array into sorted and unsorted regions, repeatedly selecting the minimum element from the unsorted region and swapping it into place.",
        "concept_focus": "Selection Sort Mechanics"
    },
    {
        "id": "sort-int-1",
        "topic": "Sorting",
        "difficulty": "intermediate",
        "question_text": "What is the worst-case time complexity of standard Quick Sort when pivot selection is poor (e.g. always picking the largest or smallest element on a sorted array)?",
        "options": {
            "A": "O(N log N)",
            "B": "O(N^2)",
            "C": "O(N)",
            "D": "O(log N)"
        },
        "correct_answer": "B",
        "explanation": "If the pivot splits the array into sizes 0 and N-1 at every step, the recursion depth is N and work per level is O(N), degenerating to O(N^2) quadratic time.",
        "concept_focus": "Quick Sort Worst-Case Partition Degeneracy"
    },
    {
        "id": "sort-adv-1",
        "topic": "Sorting",
        "difficulty": "advanced",
        "question_text": "Why cannot any comparison-based sorting algorithm achieve a worst-case time complexity better than Omega(N log N)?",
        "options": {
            "A": "Because CPU instructions have a limit of N operations",
            "B": "Because a comparison decision tree requires at least N! leaves, giving height >= log2(N!) = Omega(N log N)",
            "C": "Because memory bus bandwidth limits comparisons",
            "D": "Because arrays cannot be partitioned smaller than size 1"
        },
        "correct_answer": "B",
        "explanation": "There are N! possible permutations of N distinct elements. Any comparison-based algorithm corresponds to a binary decision tree. With N! possible outcomes, the height of the decision tree must be at least log2(N!) = Omega(N log N).",
        "concept_focus": "Information-Theoretic Comparison Sort Lower Bound"
    }
]


class AdaptiveQuizSession:
    """Manages the live state of an adaptive quiz session for a student."""

    def __init__(
        self,
        topic: str = "Recursion",
        starting_difficulty: str = "beginner",
        total_questions: int = 5,
        student_id: Optional[int] = None
    ):
        self.session_id = str(uuid.uuid4())
        self.topic = topic
        self.current_difficulty = starting_difficulty.lower()
        self.total_target_questions = total_questions
        self.student_id = student_id
        self.questions_asked: List[QuizQuestion] = []
        self.answers_given: List[Dict[str, Any]] = []
        self.score = 0
        self.difficulty_progression: List[str] = [self.current_difficulty]
        self.consecutive_correct = 0
        self.consecutive_incorrect = 0
        self.weak_concepts: List[str] = []
        self.is_complete = False
        self.pending_question: Optional[QuizQuestion] = None

    def next_difficulty(self, is_correct: bool) -> Tuple[str, str]:
        """
        Calculates the next difficulty according to adaptive pedagogy:
        - Correct on beginner -> intermediate (increased)
        - Correct on intermediate -> advanced (increased)
        - Correct on advanced -> advanced (maintained)
        - Incorrect on advanced -> intermediate (reinforced)
        - Incorrect on intermediate -> beginner (reinforced)
        - Incorrect on beginner -> beginner (reinforced)
        """
        curr = self.current_difficulty
        if is_correct:
            self.consecutive_correct += 1
            self.consecutive_incorrect = 0
            if curr == "beginner":
                next_diff = "intermediate"
                change = "increased"
            elif curr == "intermediate":
                next_diff = "advanced"
                change = "increased"
            else:
                next_diff = "advanced"
                change = "maintained"
        else:
            self.consecutive_incorrect += 1
            self.consecutive_correct = 0
            if curr == "advanced":
                next_diff = "intermediate"
                change = "reinforced"
            elif curr == "intermediate":
                next_diff = "beginner"
                change = "reinforced"
            else:
                next_diff = "beginner"
                change = "reinforced"

        self.current_difficulty = next_diff
        self.difficulty_progression.append(next_diff)
        return next_diff, change


def get_available_topics() -> List[str]:
    """Returns all supported topic categories."""
    topics = set(q["topic"] for q in OFFLINE_QUESTION_BANK)
    return sorted(list(topics))


def find_question_for_session(
    session: AdaptiveQuizSession,
    used_ids: Optional[List[str]] = None
) -> Optional[QuizQuestion]:
    """
    Selects the best matching question for the session's topic and difficulty,
    guaranteeing no duplicate questions are shown.
    Falls back gracefully if the exact difficulty tier is exhausted.
    """
    if used_ids is None:
        used_ids = [q.question_id for q in session.questions_asked]

    # Normalize topic matching (case-insensitive substring)
    target_topic = session.topic.lower()
    target_diff = session.current_difficulty.lower()

    # 1. Exact match on topic and difficulty
    candidates = [
        q for q in OFFLINE_QUESTION_BANK
        if target_topic in q["topic"].lower()
        and q["difficulty"].lower() == target_diff
        and q["id"] not in used_ids
    ]

    # 2. Relaxed match on topic (any unused question for this topic)
    if not candidates:
        candidates = [
            q for q in OFFLINE_QUESTION_BANK
            if target_topic in q["topic"].lower()
            and q["id"] not in used_ids
        ]

    # 3. Dynamic generation with Gemini if available and topic not found
    if not candidates and GEMINI_API_KEY:
        gemini_q = _generate_question_with_gemini(session.topic, session.current_difficulty)
        if gemini_q and gemini_q.question_id not in used_ids:
            return gemini_q

    if not candidates:
        return None

    raw = candidates[0]
    return QuizQuestion(
        question_id=raw["id"],
        topic=raw["topic"],
        difficulty=raw["difficulty"],
        question_text=raw["question_text"],
        options=raw["options"],
        correct_answer=raw["correct_answer"],
        explanation=raw["explanation"],
        concept_focus=raw["concept_focus"]
    )


def evaluate_student_answer(
    session: AdaptiveQuizSession,
    question: QuizQuestion,
    selected_option: str
) -> AnswerEvaluation:
    """
    Evaluates the student's answer, adjusts difficulty dynamically,
    records performance, and returns immediate instructional feedback.
    """
    cleaned_selection = selected_option.strip().upper()
    is_correct = (cleaned_selection == question.correct_answer.strip().upper())

    if is_correct:
        session.score += 1
    else:
        # Flag weak concept focus
        if question.concept_focus not in session.weak_concepts:
            session.weak_concepts.append(question.concept_focus)

    prev_diff = session.current_difficulty
    new_diff, diff_change = session.next_difficulty(is_correct)

    session.questions_asked.append(question)
    session.answers_given.append({
        "question_id": question.question_id,
        "selected": cleaned_selection,
        "correct": question.correct_answer,
        "is_correct": is_correct,
        "difficulty": question.difficulty
    })

    if len(session.questions_asked) >= session.total_target_questions:
        session.is_complete = True

    return AnswerEvaluation(
        is_correct=is_correct,
        selected_answer=cleaned_selection,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        previous_difficulty=prev_diff,
        new_difficulty=new_diff,
        difficulty_change=diff_change,
        current_score=session.score,
        total_answered=len(session.questions_asked),
        is_quiz_complete=session.is_complete
    )


def generate_session_summary(session: AdaptiveQuizSession) -> QuizSessionSummary:
    """Produces the final diagnostic summary and actionable study roadmap."""
    total = len(session.questions_asked)
    accuracy = round((session.score / max(total, 1)) * 100.0, 1)

    # Generate personalized recommendations
    recs = []
    if accuracy >= 80.0:
        recs.append(f"Mastery in {session.topic} is strong ({accuracy}%). Ready to advance to competitive challenges.")
        recs.append("Review advanced time/space complexity proofs and edge cases.")
        recs.append("Apply this topic to complex compound structures (e.g. trees & graph algorithms).")
    elif accuracy >= 50.0:
        recs.append(f"Solid grasp of {session.topic} fundamentals, with minor difficulty on intermediate questions.")
        if session.weak_concepts:
            recs.append(f"Focus targeted revision on: {', '.join(session.weak_concepts[:2])}.")
        recs.append("Practice 3-5 intermediate tracing problems before testing again.")
    else:
        recs.append(f"Foundational concepts in {session.topic} need reinforcement ({accuracy}% accuracy).")
        if session.weak_concepts:
            recs.append(f"Review core principles of: {', '.join(session.weak_concepts)}.")
        recs.append("Work through beginner code traces line-by-line with simple test inputs.")

    return QuizSessionSummary(
        topic=session.topic,
        score=session.score,
        total_questions=total,
        accuracy=accuracy,
        difficulty_trajectory=session.difficulty_progression,
        final_difficulty=session.current_difficulty,
        weak_concepts=session.weak_concepts,
        recommendations=recs
    )


def _generate_question_with_gemini(topic: str, difficulty: str) -> Optional[QuizQuestion]:
    """Generates a dynamic question using Gemini API if configured."""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options={"timeout": GEMINI_REQUEST_TIMEOUT_MS}
        )
        prompt = QUIZ_QUESTION_GENERATION_PROMPT.format(
            topic=topic,
            difficulty=difficulty,
            focus=f"Key concepts in {topic}"
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        data = json.loads(raw_text.strip())
        required_fields = (
            "question_text", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation"
        )
        if not isinstance(data, dict) or any(
            not isinstance(data.get(field), str) or not data[field].strip()
            for field in required_fields
        ):
            print("[QUIZ GENERATOR] Gemini returned an incomplete question. Using offline bank.")
            return None

        correct_answer = data["correct_answer"].strip().upper()
        if correct_answer not in {"A", "B", "C", "D"}:
            print("[QUIZ GENERATOR] Gemini returned an invalid answer key. Using offline bank.")
            return None

        return QuizQuestion(
            question_id=f"gemini-{uuid.uuid4().hex[:6]}",
            topic=topic,
            difficulty=difficulty,
            question_text=data["question_text"].strip(),
            options={
                "A": data["option_a"].strip(),
                "B": data["option_b"].strip(),
                "C": data["option_c"].strip(),
                "D": data["option_d"].strip()
            },
            correct_answer=correct_answer,
            explanation=data["explanation"].strip(),
            concept_focus=data.get("concept_tag") or topic
        )
    except Exception as exc:
        print(f"[QUIZ GENERATOR] Gemini generation failed ({exc}). Using offline bank.")
        return None
