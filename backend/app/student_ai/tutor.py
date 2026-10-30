"""
Student-Facing AI Tutor Engine for AdaptiveClass AI.

Provides conversational tutoring, step-by-step explanations, line-by-line code tracing,
multi-turn context retention, emotion-aware teaching adaptation, and dynamic
contextual follow-up suggestions with zero repetition.
Works with Gemini API (e.g. gemini-2.5-flash / gemini-3.8-flash) when API key is provided,
with an intelligent offline pedagogical engine fallback for guaranteed zero-downtime operation.
"""

import json
import re
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set
from pydantic import BaseModel, Field

from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_REQUEST_TIMEOUT_MS, get_gemini_status
from app.student_ai.emotion_detector import detect_conversational_cue, EmotionCue, EmotionCueResult
from app.student_ai.prompts import (
    TUTOR_SYSTEM_PROMPT, EMOTION_ADAPTATION_DIRECTIVES, LINE_BY_LINE_EXPLANATION_PROMPT,
    CONTEXTUAL_SUGGESTIONS_PROMPT, REPRESENTATION_FORMAT_INSTRUCTIONS
)
from app.student_ai.profiler import (
    LearnerProfile, TopicMastery, calculate_learning_level,
    create_new_student_profile
)

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    detected_cue: Optional[str] = None

class TutorResponse(BaseModel):
    message: str
    detected_cue: EmotionCue
    confidence: float
    adaptation_applied: str
    suggested_followups: List[str] = Field(default_factory=list)
    suggest_quiz: bool = False
    suggested_quiz_topic: Optional[str] = None
    engine_used: str = "offline_fallback"
    topic_detected: Optional[str] = None
    response_format: str = "explanation"


def detect_requested_format(text: str) -> Optional[str]:
    lower = text.lower()
    if re.search(r"\b(pseudo[\s-]?code|language[- ]neutral steps)\b", lower):
        return "pseudocode"
    if re.search(r"\b(flowchart|diagram|visuali[sz]e|picture|pictorial|draw it)\b", lower):
        return "diagram"
    if re.search(
        r"\b(?:give|show|write|provide|outline|list)\s+(?:me\s+)?(?:the\s+)?(?:steps|algorithm)\b"
        r"|\bsteps of (?:the )?algorithm\b|\bnumbered steps\b|\bas an algorithm\b",
        lower
    ):
        return "algorithm"
    if re.search(r"\b(show|write|give|provide|convert to|implement)\b.{0,30}\b(code|program|implementation)\b", lower):
        return "code"
    return None


OFFLINE_PSEUDOCODE = {
    "mathematics": "INPUT a, b\nWHILE b is not 0:\n    remainder = a MOD b\n    a = b\n    b = remainder\nOUTPUT a  // greatest common divisor",
    "recursion": "FUNCTION factorial(n)\n    IF n <= 1:\n        RETURN 1\n    RETURN n * factorial(n - 1)\nEND FUNCTION",
    "linked lists": "SET current = head\nWHILE current is not null:\n    PROCESS current.data\n    SET current = current.next\nEND WHILE",
    "trees": "FUNCTION inorder(node)\n    IF node is null: RETURN\n    inorder(node.left)\n    VISIT node.value\n    inorder(node.right)\nEND FUNCTION",
    "arrays": "INPUT array and target index\nIF index is within array bounds:\n    OUTPUT array[index]\nELSE:\n    REPORT index out of bounds",
    "sorting": "IF input has at most one item: RETURN input\nSPLIT input into left and right halves\nSORT each half recursively\nMERGE both sorted halves\nRETURN merged result",
    "graphs": "ADD start vertex to queue and mark visited\nWHILE queue is not empty:\n    REMOVE next vertex\n    PROCESS it\n    ADD each unvisited neighbor to queue and mark visited",
}

OFFLINE_DIAGRAMS = {
    "mathematics": "48 --remainder 12--> 18 --remainder 6--> 12 --remainder 0--> 6\n                                                        GCD = 6",
    "recursion": "factorial(3)\n    | waits for 3 * factorial(2)\n    v\nfactorial(2)\n    | waits for 2 * factorial(1)\n    v\nfactorial(1) -> 1 (base case)\n    ^ returns 2, then 6",
    "linked lists": "head -> [10 | next] -> [20 | next] -> [30 | null]",
    "trees": "        8\n       / \\\n      3   10\n     / \\    \\\n    1   6    14",
    "arrays": "index:  0    1    2    3\n       +----+----+----+----+\nvalue: | 10 | 20 | 30 | 40 |\n       +----+----+----+----+",
    "sorting": "       [8, 3, 5, 1]\n        /        \\\n    [8, 3]      [5, 1]\n      /            \\\n   [3, 8]          [1, 5]\n        \\          /\n        [1, 3, 5, 8]",
    "graphs": "A ---- B\n|      |\nC ---- D\n\nBFS from A: A -> B -> C -> D (one possible order)",
}

WELCOME_MESSAGE = (
    "👋 Hello {name}! I am your **AdaptiveClass AI Personal Learning Tutor**.\n\n"
    "I'm here to help you truly master computer science and mathematics concepts at your own pace. "
    "Here is what we can do together:\n\n"
    "1. 💡 **Step-by-Step Explanations**: Ask me about Mathematics fundamentals (e.g. *'Explain HCF and LCM'*, *'Euclidean algorithm'*), or Data Structures & Algorithms (*'How does recursion work?'*, *'Explain binary search'*).\n"
    "2. 🔍 **Line-by-Line Code Breakdowns**: Paste any code snippet and ask me to explain how each line executes and changes memory.\n"
    "3. 🧠 **Adaptive Practice Quizzes**: Type *'quiz'* or ask for practice on any topic (HCF & LCM, Recursion, Linked Lists, Trees, etc.) and I'll adapt the questions to your skill level!\n"
    "4. 🔄 **Re-explaining When Confused**: If something doesn't make sense, just tell me! I will try an easier everyday analogy.\n\n"
    "What topic or concept would you like to explore today?"
)

def is_quiz_trigger(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detects if a user input or selected suggestion triggers an adaptive quiz.
    Returns (is_quiz_trigger, detected_topic).
    """
    if not text:
        return False, None
    lower = text.strip().lower()

    # Exact standalone keywords
    if lower in ["quiz", "test", "practice", "start quiz", "take quiz", "quiz please", "adaptive quiz"]:
        return True, None

    # Natural language quiz patterns
    patterns = [
        r"\b(start|take|launch|begin|do|want|try|give\s+me)\b(\s+\w+){0,3}\s+\b(quiz|test|practice)\b",
        r"\b(quiz\s+me|test\s+(me|my\s+knowledge))\b",
        r"\b(give\s+me|show\s+me|practice)\s+(some\s+)?questions\b",
        r"\b(adaptive\s+quiz|practice\s+quiz|beginner\s+quiz|intermediate\s+quiz|advanced\s+quiz)\b"
    ]
    for p in patterns:
        if re.search(p, lower):
            # Check for mathematics keywords first
            if any(k in lower for k in ["hcf", "lcm", "gcd", "math"]):
                return True, "Mathematics"
            # Extract topic if present in query
            for t in ["recursion", "linked lists", "trees", "arrays", "graphs", "sorting", "stack", "queue"]:
                if t in lower:
                    return True, t.title()
            return True, None

    return False, None


# Rich topic knowledge base for offline explanation
OFFLINE_TOPIC_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "mathematics": {
        "title": "Mathematics: HCF (GCD) & LCM",
        "analogy": (
            "• **HCF (Highest Common Factor)**: Imagine you have two ribbons—one 12 cm long and another 18 cm long. "
            "You want to cut both ribbons into equal pieces with zero leftover ribbon. The longest piece you can cut is 6 cm (the HCF)!\n"
            "• **LCM (Lowest Common Multiple)**: Imagine two runners on a circular track. Runner A completes a lap in 4 minutes, "
            "and Runner B in 6 minutes. Starting together, when will they first cross the start line at the same time? After 12 minutes (the LCM)!"
        ),
        "steps": [
            "1. **HCF / GCD Definition**: The largest positive integer that divides both numbers evenly without leaving any remainder.",
            "2. **LCM Definition**: The smallest positive integer that is divisible by both numbers.",
            "3. **Golden Mathematical Rule**: For any two positive integers $a$ and $b$:\n"
            "   $$\\text{HCF}(a, b) \\times \\text{LCM}(a, b) = a \\times b$$\n"
            "   Therefore: $$\\text{LCM}(a, b) = \\frac{a \\times b}{\\text{HCF}(a, b)}$$",
            "4. **Worked Step-by-Step Example (Numbers: 12 and 18)**:\n"
            "   - **Prime Factorization of 12**: $12 = 2 \\times 2 \\times 3 = 2^2 \\times 3^1$\n"
            "   - **Prime Factorization of 18**: $18 = 2 \\times 3 \\times 3 = 2^1 \\times 3^2$\n"
            "   - **Find HCF**: Take common prime factors with lowest powers: $2^1 \\times 3^1 = 6$.\n"
            "   - **Find LCM**: Take all prime factors with highest powers: $2^2 \\times 3^2 = 4 \\times 9 = 36$.\n"
            "   - **Verification**: $12 \\times 18 = 216$, and $\\text{HCF} \\times \\text{LCM} = 6 \\times 36 = 216$ (Matches!)."
        ],
        "example_code": (
            "def compute_hcf(a, b):\n"
            "    # Euclidean Algorithm: gcd(a, b) = gcd(b, a % b)\n"
            "    while b != 0:\n"
            "        a, b = b, a % b\n"
            "    return a\n\n"
            "def compute_lcm(a, b):\n"
            "    # Property: LCM(a, b) = (|a * b|) // HCF(a, b)\n"
            "    if a == 0 or b == 0:\n"
            "        return 0\n"
            "    return abs(a * b) // compute_hcf(a, b)\n\n"
            "# Example execution\n"
            "num1, num2 = 12, 18\n"
            "print('HCF of 12 and 18:', compute_hcf(num1, num2))  # 6\n"
            "print('LCM of 12 and 18:', compute_lcm(num1, num2))  # 36\n"
        ),
        "code_walkthrough": [
            "Line 1 (`def compute_hcf(a, b):`): Defines the function implementing the Euclidean algorithm.",
            "Line 3 (`while b != 0:`): Loops as long as the remainder `b` is non-zero.",
            "Line 4 (`a, b = b, a % b`): Simultaneously updates `a` to divisor `b`, and `b` to remainder `a % b`.",
            "Line 5 (`return a`): When `b` reaches 0, `a` holds the Greatest Common Divisor.",
            "Line 7-11 (`def compute_lcm(a, b):`): Computes LCM in O(1) extra time using `abs(a * b) // compute_hcf(a, b)`."
        ],
        "trace_example": (
            "Tracing `compute_hcf(12, 18)`:\n"
            "1. Step 1: `a = 12, b = 18` -> `a % b = 12 % 18 = 12`. Next `(a, b) = (18, 12)`\n"
            "2. Step 2: `a = 18, b = 12` -> `a % b = 18 % 12 = 6`. Next `(a, b) = (12, 6)`\n"
            "3. Step 3: `a = 12, b = 6` -> `a % b = 12 % 6 = 0`. Next `(a, b) = (6, 0)`\n"
            "4. Step 4: `b == 0` -> Loop terminates. Returns `a = 6`!"
        ),
        "complexity": (
            "- **Time Complexity**: **O(log(min(a, b)))** via the Euclidean algorithm (by Lamé's Theorem, at most 5 * decimal digits of smaller number).\n"
            "- **Space Complexity**: **O(1)** auxiliary memory since the iterative loop runs in-place."
        ),
        "alternative_implementation": (
            "```python\n"
            "# Recursive Euclidean Algorithm\n"
            "def gcd_recursive(a, b):\n"
            "    if b == 0:\n"
            "        return a\n"
            "    return gcd_recursive(b, a % b)\n"
            "```\n\n"
            "- **Space**: O(log(min(a, b))) call stack frames for the recursive version vs O(1) for the iterative loop."
        )
    },
    "recursion": {
        "title": "Recursion",
        "analogy": "Imagine standing between two mirrors, or opening a Russian Matryoshka doll until you reach the solid tiny doll inside.",
        "steps": [
            "1. **Base Case**: The stop condition that halts the recursion and prevents infinite loops.",
            "2. **Recursive Call**: The function calling itself with a strictly smaller or simpler input.",
            "3. **Call Stack**: Each call is stacked on top of previous calls. When the base case is hit, calls return and unwind from top to bottom."
        ],
        "example_code": (
            "def factorial(n):\n"
            "    # Base Case: Stop when n reaches 1 or 0\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    # Recursive Step: n * factorial of (n - 1)\n"
            "    return n * factorial(n - 1)\n"
        ),
        "code_walkthrough": [
            "Line 1 (`def factorial(n):`): Defines the function accepting an integer `n`.",
            "Line 2-3 (`if n <= 1: return 1`): Base case. When `n` reaches 1, returns 1 without further calls.",
            "Line 4-5 (`return n * factorial(n - 1)`): Recursive call. Pauses current execution and calls `factorial(n - 1)`."
        ],
        "trace_example": (
            "Tracing `factorial(3)`:\n"
            "1. `factorial(3)` pauses, calls `factorial(2)`\n"
            "2. `factorial(2)` pauses, calls `factorial(1)`\n"
            "3. `factorial(1)` hits base case and returns `1` immediately\n"
            "4. `factorial(2)` computes `2 * 1 = 2` and returns\n"
            "5. `factorial(3)` computes `3 * 2 = 6` and returns final answer: **6**"
        ),
        "complexity": (
            "- **Time Complexity**: **O(N)** because there are N recursive calls, each doing O(1) work.\n"
            "- **Space Complexity**: **O(N)** auxiliary space on the Call Stack to hold active frames."
        ),
        "alternative_implementation": (
            "```python\n"
            "# Iterative factorial loop: O(1) space\n"
            "def factorial_iterative(n):\n"
            "    result = 1\n"
            "    for i in range(2, n + 1):\n"
            "        result *= i\n"
            "    return result\n"
            "```\n\n"
            "- **Advantage**: Saves memory by eliminating call stack frames (O(1) vs O(N))."
        )
    },
    "linked lists": {
        "title": "Linked Lists",
        "analogy": "Think of a treasure hunt where each clue contains a message and directions to where the next clue is hidden.",
        "steps": [
            "1. **Node**: A container holding two things: your data, and a pointer (reference) to the next node.",
            "2. **Head**: The starting node of the list.",
            "3. **Traversal**: Unlike arrays where you jump directly via index `arr[i]`, here you must follow pointers one-by-one from the Head."
        ],
        "example_code": (
            "class Node:\n"
            "    def __init__(self, data):\n"
            "        self.data = data\n"
            "        self.next = None  # Pointer to next node\n"
        ),
        "code_walkthrough": [
            "Line 1 (`class Node:`): Creates a blueprint for list nodes.",
            "Line 2-3 (`self.data = data`): Stores the actual value in this node.",
            "Line 4 (`self.next = None`): Initially, this node doesn't point to anything (end of list)."
        ],
        "trace_example": (
            "Traversing `Node(10) -> Node(20) -> Node(30) -> None`:\n"
            "1. Start at `head` (10)\n"
            "2. Follow `current.next` to reach 20\n"
            "3. Follow `current.next` to reach 30\n"
            "4. `current.next` is `None` -> Reached the end of the list!"
        ),
        "complexity": (
            "- **Prepend (Insert at Head)**: **O(1)** instant time.\n"
            "- **Search / Access by Index**: **O(N)** linear time (must traverse from Head).\n"
            "- **Space**: **O(N)** for storing N nodes and pointers."
        ),
        "alternative_implementation": (
            "```python\n"
            "# Inserting at the head of a linked list\n"
            "def insert_head(head, val):\n"
            "    new_node = Node(val)\n"
            "    new_node.next = head\n"
            "    return new_node  # new_node is now the head\n"
            "```"
        )
    },
    "trees": {
        "title": "Binary Search Trees (BST)",
        "analogy": "Think of an inverted tree or an organized family tree where for every parent, smaller numbers go to the left branch and bigger numbers go to the right branch.",
        "steps": [
            "1. **Root**: The topmost node of the tree.",
            "2. **BST Invariant**: For every node: all values in Left Subtree < Node Value < all values in Right Subtree.",
            "3. **In-Order Traversal**: Visiting Left -> Root -> Right yields keys in sorted order!"
        ],
        "example_code": (
            "class TreeNode:\n"
            "    def __init__(self, val):\n"
            "        self.val = val\n"
            "        self.left = None\n"
            "        self.right = None\n"
        ),
        "code_walkthrough": [
            "Line 1-2 (`class TreeNode`): Node definition holding value `val`.",
            "Line 3 (`self.left = None`): Pointer to left child subtree (strictly smaller values).",
            "Line 4 (`self.right = None`): Pointer to right child subtree (strictly larger values)."
        ],
        "trace_example": (
            "Searching for key 15 in BST with root 10:\n"
            "1. Compare 15 with root (10): Since 15 > 10, go right!\n"
            "2. Compare 15 with right child (20): Since 15 < 20, go left!\n"
            "3. Left child is 15: Key found in O(log N) comparisons!"
        ),
        "complexity": (
            "- **Balanced BST Search/Insert/Delete**: **O(log N)** time.\n"
            "- **Unbalanced Worst-Case**: **O(N)** if tree degrades into a straight linked list.\n"
            "- **Space Complexity**: **O(N)** for N tree nodes."
        ),
        "alternative_implementation": (
            "```python\n"
            "# Recursive in-order traversal: Left -> Root -> Right\n"
            "def inorder(root):\n"
            "    if root:\n"
            "        inorder(root.left)\n"
            "        print(root.val, end=' ')\n"
            "        inorder(root.right)\n"
            "```"
        )
    },
    "arrays": {
        "title": "Arrays & Dynamic Arrays",
        "analogy": "Think of a row of consecutively numbered apartment mailboxes right next to each other.",
        "steps": [
            "1. **Contiguous Memory**: Every element sits in sequential memory, enabling O(1) instant random access via index.",
            "2. **Fixed vs Dynamic**: Fixed arrays have set size; dynamic arrays automatically double capacity when full.",
            "3. **Tradeoffs**: Fast lookups by index, but slow insertions/deletions in the middle (O(N) shifts required)."
        ],
        "example_code": (
            "# Creating and accessing an array in Python\n"
            "numbers = [10, 20, 30, 40, 50]\n"
            "first_element = numbers[0]  # O(1) Instant Access\n"
            "numbers.append(60)          # O(1) Amortized Append\n"
        ),
        "code_walkthrough": [
            "Line 2: Allocates contiguous array containing 5 integers.",
            "Line 3: Computes address as base + 0 * size, returning 10 instantly in O(1) time.",
            "Line 4: Adds 60 to the end in amortized O(1) time."
        ],
        "complexity": (
            "- **Index Access**: **O(1)** constant time.\n"
            "- **Append**: **O(1)** amortized time.\n"
            "- **Insertion/Deletion in middle**: **O(N)** time due to shifting elements."
        )
    },
    "sorting": {
        "title": "Sorting Algorithms",
        "analogy": "Arranging a messy hand of playing cards from lowest to highest card.",
        "steps": [
            "1. **Comparison Sorts**: Algorithms like Merge Sort and Quick Sort compare elements pairwise.",
            "2. **Divide and Conquer**: Break array into halves, sort halves recursively, then merge them back together in O(N log N) time.",
            "3. **Lower Bound**: No comparison-based sort can beat O(N log N) in the worst case."
        ],
        "example_code": (
            "def merge_sort(arr):\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    mid = len(arr) // 2\n"
            "    left = merge_sort(arr[:mid])\n"
            "    right = merge_sort(arr[mid:])\n"
            "    return merge(left, right)\n"
        ),
        "code_walkthrough": [
            "Line 2-3: Base case: arrays of length 0 or 1 are already sorted.",
            "Line 4: Finds middle index to split array in halves.",
            "Line 5-6: Recursively sorts left and right halves.",
            "Line 7: Merges the two sorted halves in O(N) linear time."
        ],
        "complexity": (
            "- **Merge Sort Time**: **O(N log N)** guaranteed across best, average, and worst cases.\n"
            "- **Quick Sort Time**: **O(N log N)** average, **O(N^2)** worst case.\n"
            "- **Merge Sort Space**: **O(N)** auxiliary memory for merging."
        )
    },
    "graphs": {
        "title": "Graph Data Structures",
        "analogy": "Think of an airline route network connecting cities (vertices) via direct flights (edges).",
        "steps": [
            "1. **Vertices & Edges**: Nodes represent entities; edges represent connections between them.",
            "2. **Adjacency List**: Hash map or list of lists storing neighbors for each node (memory efficient for sparse graphs).",
            "3. **Traversals**: BFS explores layer-by-layer (shortest path); DFS explores deep into paths first."
        ],
        "example_code": (
            "# Representing a graph using an Adjacency List in Python\n"
            "graph = {\n"
            "    'A': ['B', 'C'],\n"
            "    'B': ['A', 'D', 'E'],\n"
            "    'C': ['A', 'F'],\n"
            "    'D': ['B'],\n"
            "    'E': ['B', 'F'],\n"
            "    'F': ['C', 'E']\n"
            "}\n"
        ),
        "code_walkthrough": [
            "Line 2: Node 'A' is connected to 'B' and 'C'.",
            "Line 3: Node 'B' connects to 'A', 'D', and 'E'.",
            "This adjacency list takes O(V + E) space where V is vertices and E is edges."
        ],
        "complexity": (
            "- **BFS / DFS Traversal Time**: **O(V + E)** with Adjacency List.\n"
            "- **Space Complexity**: **O(V + E)** to store the graph and visited set."
        )
    }
}

# Offline dynamic suggestion candidate pools
OFFLINE_SUGGESTION_POOLS: Dict[str, Dict[str, List[str]]] = {
    "mathematics": {
        "clarification": [
            "How does the Euclidean algorithm find GCD so quickly?",
            "Why does HCF(a, b) * LCM(a, b) = a * b?",
            "What is the difference between prime factorization and Euclidean division?",
            "What happens if one of the numbers is 0 or negative?"
        ],
        "code_trace": [
            "Can you explain the Euclidean algorithm line by line?",
            "Can we trace compute_hcf(48, 18) step by step?",
            "How do you find the HCF and LCM of 3 numbers in Python?",
            "Can you show the recursive version of GCD?"
        ],
        "complexity": [
            "What is the time complexity of the Euclidean algorithm (Lamé's theorem)?",
            "Why is Euclidean algorithm faster than prime factorization for large numbers?",
            "How does the Extended Euclidean Algorithm find modular inverses?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Mathematics (HCF & LCM)",
            "Test my knowledge on HCF and LCM with a quiz",
            "Challenge me with practice questions on HCF and LCM"
        ]
    },
    "recursion": {
        "clarification": [
            "Why is a base case strictly required in recursive functions?",
            "How does the call stack unwind after hitting the base case?",
            "What is the difference between direct and indirect recursion?",
            "What is a recursion tree and how do we draw one?"
        ],
        "code_trace": [
            "Can you explain this code line by line?",
            "What happens if input n is 0 or negative?",
            "Can you show an iterative version of this algorithm?",
            "Can we trace this with input n=4 step by step?"
        ],
        "complexity": [
            "What is the time and space complexity of this recursion?",
            "What is tail recursion and how does it optimize memory?",
            "How does memoization prevent stack overflow?",
            "What are common beginner bugs when writing recursion?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Recursion",
            "Test my knowledge on Recursion with a quiz",
            "Challenge me with practice questions on Recursion"
        ]
    },
    "linked lists": {
        "clarification": [
            "Why is insertion at the head O(1) in a linked list?",
            "What is the key difference between an Array and a Linked List?",
            "How does pointer reference work in Python or C++?",
            "What is a doubly linked list?"
        ],
        "code_trace": [
            "Can you explain this node code line by line?",
            "How do you detect a cycle using fast and slow pointers?",
            "How do you reverse a singly linked list?",
            "How do you find the middle node in one pass?"
        ],
        "complexity": [
            "Why is searching a linked list O(N) instead of O(1)?",
            "How do CPU cache misses affect linked list traversal?",
            "How do we prevent memory leaks when deleting nodes?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Linked Lists",
            "Test my knowledge on Linked Lists with a quiz",
            "Challenge me with practice questions on Linked Lists"
        ]
    },
    "trees": {
        "clarification": [
            "What is the BST invariant rule for left and right subtrees?",
            "Why is in-order traversal of a BST always sorted?",
            "What is the difference between a tree and a graph?",
            "What makes a binary tree 'balanced'?"
        ],
        "code_trace": [
            "Can you explain tree node insertion line by line?",
            "How do pre-order and post-order traversals work?",
            "How do we calculate the maximum height of a binary tree?",
            "Can we trace searching for a key in a BST?"
        ],
        "complexity": [
            "Why can an unbalanced BST degrade to O(N) linear time?",
            "How do AVL tree rotations restore height balance?",
            "What is the space complexity of tree recursion on the call stack?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Trees",
            "Test my knowledge on Trees with a quiz",
            "Challenge me with practice questions on Trees"
        ]
    },
    "arrays": {
        "clarification": [
            "Why is index access O(1) in an array?",
            "What is the difference between fixed and dynamic arrays?",
            "How does contiguous memory allocation work in RAM?",
            "Why are insertions in the middle of an array O(N)?"
        ],
        "code_trace": [
            "Can you explain this array traversal line by line?",
            "How does Kadane's algorithm find the maximum subarray sum?",
            "How do two-pointer techniques work for reversing an array?",
            "Can you trace finding duplicates in an array?"
        ],
        "complexity": [
            "Why does dynamic array append have O(1) amortized cost?",
            "How do CPU cache lines improve array iteration speed?",
            "When should an array be used instead of a hash table?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Arrays",
            "Test my knowledge on Arrays with a quiz",
            "Challenge me with practice questions on Arrays"
        ]
    },
    "sorting": {
        "clarification": [
            "What is the difference between Merge Sort and Quick Sort?",
            "What does it mean for a sorting algorithm to be 'stable'?",
            "Why can't comparison-based sorts beat O(N log N) in the worst case?",
            "When is Insertion Sort faster than Quick Sort?"
        ],
        "code_trace": [
            "Can you explain the Merge Sort partition step line by line?",
            "How does Quick Sort choose a pivot element?",
            "Can we trace sorting [5, 2, 8, 1, 9] step by step?",
            "How does binary search work on an already sorted array?"
        ],
        "complexity": [
            "Why is Quick Sort O(N^2) in the worst-case scenario?",
            "How does TimSort combine Merge Sort and Insertion Sort?",
            "What is the auxiliary space complexity of Merge Sort?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Sorting",
            "Test my knowledge on Sorting with a quiz",
            "Challenge me with practice questions on Sorting"
        ]
    },
    "graphs": {
        "clarification": [
            "When should I use Breadth-First Search vs Depth-First Search?",
            "What is the difference between an Adjacency List and an Adjacency Matrix?",
            "What is the difference between directed and undirected graphs?",
            "What is a weighted graph?"
        ],
        "code_trace": [
            "Can you explain BFS queue traversal line by line?",
            "How do we detect a cycle in a directed graph using DFS?",
            "How do we find the shortest unweighted path with BFS?",
            "Can we trace Dijkstra's algorithm on a small graph?"
        ],
        "complexity": [
            "Why does Dijkstra's algorithm fail on negative edge weights?",
            "What is the time complexity of BFS with an Adjacency List?",
            "How does Bellman-Ford handle negative weight cycles?"
        ],
        "quizzes": [
            "Start an adaptive quiz on Graphs",
            "Test my knowledge on Graphs with a quiz",
            "Challenge me with practice questions on Graphs"
        ]
    }
}


class StudentTutor:
    """Manages an active conversational tutoring session for a student."""

    def __init__(
        self,
        student_name: str = "Student",
        student_level: str = "Beginner",
        profile: Optional[LearnerProfile] = None
    ):
        self.session_id = str(uuid.uuid4())
        self.student_name = student_name
        self.student_level = student_level
        self.profile = profile or create_new_student_profile(student_name)
        self.history: List[ChatMessage] = []
        self.current_topic: Optional[str] = None
        self.seen_suggestions: Set[str] = set()
        self.last_suggestions: List[str] = []
        self.last_engine_used: str = "offline_fallback"
        self.last_detected_cue: EmotionCueResult = EmotionCueResult(
            detected_cue=EmotionCue.NEUTRAL,
            confidence=0.5,
            trigger_phrases=[],
            adaptation_strategy="Standard tutoring",
            suggested_tone="Friendly & structured"
        )

    def get_welcome(self) -> str:
        """Returns personalized introductory greeting."""
        return WELCOME_MESSAGE.format(name=self.student_name)

    def chat(self, user_text: str, requested_format: Optional[str] = None) -> TutorResponse:
        """
        Processes a user message:
        1. Detects emotion cues.
        2. Applies pedagogical adaptation.
        3. Formulates response via Gemini or offline engine.
        4. Generates dynamic, non-repeating contextual follow-up suggestions.
        5. Maintains conversation context.
        """
        user_input = user_text.strip()
        if not user_input:
            initial_followups = [
                "How does recursion work step by step?",
                "Can you explain HCF and LCM with an example?",
                "Start an adaptive quiz on Mathematics or DSA"
            ]
            self.last_suggestions = initial_followups
            self.seen_suggestions.update(initial_followups)
            return TutorResponse(
                message="Feel free to ask any question about programming, data structures, or mathematics!",
                detected_cue=EmotionCue.NEUTRAL,
                confidence=0.5,
                adaptation_applied="Prompted for input",
                suggested_followups=initial_followups,
                engine_used="offline_fallback"
            )

        # 1. Detect conversational emotion cue
        cue_result = detect_conversational_cue(user_input)
        self.last_detected_cue = cue_result

        # 2. Check if student expresses quiz intent
        quiz_intent, quiz_topic = is_quiz_trigger(user_input)
        if quiz_intent:
            topic_to_use = quiz_topic or self.current_topic or "Recursion"
            self.current_topic = topic_to_use
            msg = (
                f"🎯 **Adaptive Quiz Ready!**\n\n"
                f"I've set up an adaptive quiz on **{topic_to_use}** for you! "
                f"We'll start at your current level (**{self.student_level}**) and dynamically adjust "
                f"the difficulty based on how you answer.\n\n"
                f"You can choose **Option 2** in the main menu or click start to begin right now!"
            )
            quiz_followups = [
                f"Start adaptive quiz on {topic_to_use} now",
                f"Review {topic_to_use} fundamentals first",
                "Explore another data structure"
            ]
            self.history.extend([
                ChatMessage(role="user", content=user_input, detected_cue=cue_result.detected_cue.value),
                ChatMessage(role="assistant", content=msg)
            ])
            self.last_suggestions = quiz_followups
            self.seen_suggestions.update(quiz_followups)
            return TutorResponse(
                message=msg,
                detected_cue=cue_result.detected_cue,
                confidence=cue_result.confidence,
                adaptation_applied="Detected quiz request",
                suggest_quiz=True,
                suggested_quiz_topic=topic_to_use,
                suggested_followups=quiz_followups,
                engine_used="offline_fallback",
                topic_detected=topic_to_use,
                response_format="explanation"
            )

        # 3. Check for line-by-line explanation request
        line_by_line_request = self._check_line_by_line_intent(user_input)
        response_format = requested_format or detect_requested_format(user_input) or "explanation"

        # 4. Detect topic from the actual student question
        detected_topic = self._detect_topic(user_input)
        if detected_topic:
            self.current_topic = detected_topic
        topic_mastery = self._find_topic_mastery(self.current_topic)
        self.student_level = (
            calculate_learning_level(topic_mastery.mastery_percentage)
            if topic_mastery and topic_mastery.attempt_count > 0
            else self.profile.learning_level
        )

        # Record user message in history
        self.history.append(ChatMessage(
            role="user",
            content=user_input,
            detected_cue=cue_result.detected_cue.value
        ))

        # 5. Generate Response via Gemini or Fallback
        response_text = self._generate_response_text(
            user_input=user_input,
            cue_result=cue_result,
            is_line_by_line=line_by_line_request,
            topic=self.current_topic,
            requested_format=response_format
        )

        # Record assistant response in history
        self.history.append(ChatMessage(
            role="assistant",
            content=response_text
        ))

        # 6. Generate Dynamic Non-Repeating Follow-Up Suggestions
        topic_for_suggestions = self.current_topic or "Recursion"
        followups = self.generate_contextual_suggestions(
            user_input=user_input,
            response_text=response_text,
            topic=topic_for_suggestions,
            cue=cue_result.detected_cue,
            allow_gemini=self.last_engine_used == "gemini"
        )
        self.last_suggestions = followups

        return TutorResponse(
            message=response_text,
            detected_cue=cue_result.detected_cue,
            confidence=cue_result.confidence,
            adaptation_applied=cue_result.adaptation_strategy,
            suggested_followups=followups,
            suggest_quiz=False,
            engine_used=self.last_engine_used,
            topic_detected=self.current_topic,
            response_format=response_format
        )

    def _generate_response_text(
        self,
        user_input: str,
        cue_result: EmotionCueResult,
        is_line_by_line: bool,
        topic: Optional[str],
        requested_format: str = "explanation"
    ) -> str:
        """Tries Gemini first; falls back seamlessly to deterministic pedagogical engine."""
        if GEMINI_API_KEY:
            try:
                print(f"[STUDENT TUTOR] Attempting Gemini API call (model: '{GEMINI_MODEL}')...")
                from google import genai
                client = genai.Client(
                    api_key=GEMINI_API_KEY,
                    http_options={"timeout": GEMINI_REQUEST_TIMEOUT_MS}
                )

                emotion_guidance = EMOTION_ADAPTATION_DIRECTIVES.get(
                    cue_result.detected_cue.value,
                    EMOTION_ADAPTATION_DIRECTIVES["NEUTRAL"]
                )
                system_content = TUTOR_SYSTEM_PROMPT.format(
                    student_name=self.student_name,
                    student_level=self.student_level,
                    strengths=", ".join(self.profile.strengths) if self.profile.strengths else "Foundational concepts",
                    weak_areas=", ".join(self.profile.weaknesses) if self.profile.weaknesses else "New student assessment",
                    emotion_guidance=emotion_guidance,
                    topic_mastery_context=self._topic_mastery_context(topic)
                )
                format_instruction = REPRESENTATION_FORMAT_INSTRUCTIONS.get(requested_format)

                recent_history = self.history[-6:]
                context_str = ""
                for msg in recent_history[:-1]:
                    context_str += f"{msg.role.upper()}: {msg.content}\n"

                prompt = (
                    f"{system_content}\n\n"
                    f"Requested response format: {format_instruction or 'Use a clear explanation and include relevant examples.'}\n"
                    f"Conversation Context:\n{context_str}\n"
                    f"STUDENT: {user_input}\n\n"
                    f"TUTOR (Respond in friendly markdown, step-by-step, beginner accessible):"
                )

                res = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
                if res and res.text:
                    print(f"[STUDENT TUTOR] Gemini API call successful (model: '{GEMINI_MODEL}'). Response generated.")
                    self.last_engine_used = "gemini"
                    return res.text.strip()
            except Exception as exc:
                print(f"[STUDENT TUTOR] Gemini API call failed ({type(exc).__name__}: {exc}). Activating offline pedagogical engine fallback.")
        else:
            print("[STUDENT TUTOR] GEMINI_API_KEY not configured. Using offline pedagogical engine fallback.")

        # Deterministic Offline Pedagogical Response
        self.last_engine_used = "offline_fallback"
        return self._generate_offline_pedagogical_response(
            user_input, cue_result, is_line_by_line, topic, requested_format
        )

    def _topic_mastery_context(self, topic: Optional[str]) -> str:
        if not topic:
            return f"Overall demonstrated mastery: {self.profile.overall_mastery}%"
        mastery = self._find_topic_mastery(topic)
        if not mastery or mastery.attempt_count == 0:
            return f"No recorded quiz performance yet for {topic}; begin with a foundational explanation."
        return (
            f"{topic}: {mastery.mastery_percentage}% mastery from "
            f"{mastery.attempt_count} quiz attempt(s), {mastery.correct_count} correct answers."
        )

    def _find_topic_mastery(self, topic: Optional[str]) -> Optional[TopicMastery]:
        if not topic:
            return None
        normalized = topic.casefold()
        return next(
            (
                mastery for name, mastery in self.profile.topic_mastery.items()
                if normalized == name.casefold()
                or normalized in name.casefold()
                or name.casefold() in normalized
            ),
            None
        )

    def _generate_offline_pedagogical_response(
        self,
        user_input: str,
        cue_result: EmotionCueResult,
        is_line_by_line: bool,
        topic: Optional[str],
        requested_format: str = "explanation"
    ) -> str:
        """
        Generates rich, step-by-step pedagogical responses offline.
        Matches the actual user question rather than defaulting to Recursion.
        If unsupported, asks for clarification rather than returning an unrelated explanation.
        """
        lower_input = user_input.lower()

        # Step 1: Check if user_input directly mentions a recognized topic
        direct_key = self._match_offline_topic_key(user_input)
        if direct_key:
            matched_key = direct_key
            self.current_topic = self._key_to_topic_name(direct_key)
        # Step 2: If code or line-by-line is requested on input:
        elif is_line_by_line or self._check_line_by_line_intent(user_input):
            if any(k in lower_input for k in ["hcf", "lcm", "gcd", "%"]):
                matched_key = "mathematics"
            elif any(k in lower_input for k in ["n - 1", "factorial", "f(", "return 1", "recursion"]):
                matched_key = "recursion"
            elif self.current_topic:
                matched_key = self._topic_name_to_key(self.current_topic) or "recursion"
            else:
                matched_key = "recursion"
            self.current_topic = self._key_to_topic_name(matched_key)
        # Step 3: If student expresses confusion with no prior topic set:
        elif cue_result.detected_cue == EmotionCue.CONFUSION and not self.current_topic:
            matched_key = "recursion"
            self.current_topic = "Recursion"
        # Step 4: If no direct match, check if this is a follow-up to the current active topic
        elif topic and self._is_followup_to_current_topic(user_input):
            matched_key = self._topic_name_to_key(topic)
            if not matched_key:
                return self._generate_unsupported_topic_clarification(user_input, topic)
        # Step 5: Neither direct match nor active follow-up -> return clarification
        else:
            return self._generate_unsupported_topic_clarification(user_input, topic)

        if not matched_key or matched_key not in OFFLINE_TOPIC_KNOWLEDGE:
            return self._generate_unsupported_topic_clarification(user_input, topic)

        kb = OFFLINE_TOPIC_KNOWLEDGE[matched_key]

        if requested_format in REPRESENTATION_FORMAT_INSTRUCTIONS:
            return self._format_offline_representation(
                matched_key, kb, requested_format, cue_result.detected_cue
            )

        # 1. Confusion Handling
        if cue_result.detected_cue == EmotionCue.CONFUSION:
            return (
                f"💡 **Let's take a step back and simplify!**\n\n"
                f"It is completely normal to feel confused by {kb['title']} at first—almost every student does! "
                f"Let's look at it using a simple everyday analogy instead:\n\n"
                f"> 🏷️ **Analogy**: {kb['analogy']}\n\n"
                f"Let's focus on just **one core idea**:\n"
                f"{kb['steps'][0]}\n\n"
                f"Does that comparison make sense so far? If yes, we can look at a tiny example together!"
            )

        # 2. Frustration Handling
        if cue_result.detected_cue == EmotionCue.FRUSTRATION:
            return (
                f"🤝 **Take a deep breath—I'm right here with you.**\n\n"
                f"{kb['title']} can be really tricky, and getting stuck does NOT mean you can't learn it. "
                f"Let's slow things down and break it into a single tiny step:\n\n"
                f"Forget the complex syntax for a moment. Just remember:\n"
                f"{kb['steps'][0]}\n\n"
                f"That's all you need right now. Would you like me to walk you through a simple code example line by line?"
            )

        # 3. Nervousness Handling
        if cue_result.detected_cue == EmotionCue.NERVOUSNESS:
            return (
                f"🌱 **You've got this!**\n\n"
                f"Feeling anxious about exams or problem solving is very common. The great thing about Computer Science is that "
                f"it's a skill built step by step, not something you have to master overnight.\n\n"
                f"Let's master **{kb['title']}** together with simple principles:\n\n"
                + "\n\n".join(kb["steps"][:3]) + "\n\n"
                f"Whenever you're ready, we can run a low-stakes beginner practice quiz where you can test your knowledge with zero pressure!"
            )

        # 4. Line-by-Line Code Request
        if is_line_by_line or "line by line" in lower_input or "walkthrough" in lower_input:
            walkthrough_items = kb.get("code_walkthrough", [])
            trace_section = kb.get("trace_example", "")
            trace_md = f"\n\n💡 **Execution Trace Example:**\n{trace_section}" if trace_section else ""
            return (
                f"🔍 **Line-by-Line Walkthrough: {kb['title']}**\n\n"
                f"Here is our standard implementation:\n\n"
                f"```python\n{kb['example_code']}```\n\n"
                f"**Step-by-step breakdown:**\n"
                + "\n".join(f"- {step}" for step in walkthrough_items)
                + trace_md + "\n\n"
                f"Would you like to try tracing this with custom inputs, or take an adaptive practice quiz?"
            )

        # 5. Confidence Handling
        if cue_result.detected_cue == EmotionCue.CONFIDENCE:
            return (
                f"🎉 **Awesome job! You're picking up {kb['title']} fast.**\n\n"
                f"Since you're feeling confident, let's test your understanding with a slightly deeper challenge:\n\n"
                f"```python\n{kb['example_code']}```\n\n"
                f"**Challenge**: How could we optimize this algorithm or handle unusual edge cases?\n\n"
                f"Or if you prefer, we can jump straight into an **Adaptive Practice Quiz**!"
            )

        # 6. Specific follow-up requests in multi-turn conversation
        if "call stack" in lower_input or "unwind" in lower_input:
            if matched_key == "recursion":
                return (
                    f"📦 **How the Call Stack Unwinds in Recursion**\n\n"
                    f"Every time a recursive function calls itself, the computer saves the current state (local variables and where it left off) "
                    f"in an execution frame on the **Call Stack**.\n\n"
                    f"1. **Pushing Phase**: `factorial(3)` calls `factorial(2)` calls `factorial(1)`. Three frames sit stacked in memory.\n"
                    f"2. **Base Case Reached**: `factorial(1)` returns `1` directly without making new calls.\n"
                    f"3. **Popping (Unwinding) Phase**: The top frame is popped from the stack. `factorial(2)` multiplies `2 * 1 = 2` and pops. "
                    f"Finally `factorial(3)` multiplies `3 * 2 = 6` and returns the final answer.\n\n"
                    f"Would you like to see how to prevent a stack overflow error, or test your understanding?"
                )
            elif matched_key == "mathematics":
                return (
                    f"📦 **Recursive Euclidean Algorithm & Call Stack**\n\n"
                    f"When written recursively: `def gcd(a, b): return a if b == 0 else gcd(b, a % b)`:\n"
                    f"1. `gcd(12, 18)` calls `gcd(18, 12)` (push frame 1)\n"
                    f"2. `gcd(18, 12)` calls `gcd(12, 6)` (push frame 2)\n"
                    f"3. `gcd(12, 6)` calls `gcd(6, 0)` (push frame 3)\n"
                    f"4. `b == 0`: returns `6` directly. Call stack unwinds with final answer **6**!\n\n"
                    f"Would you like to try this with another pair of numbers or take a quiz?"
                )

        if "complexity" in lower_input or "big o" in lower_input or "time complexity" in lower_input or "space complexity" in lower_input:
            complexity_info = kb.get("complexity", (
                f"- **Time Complexity**: Standard operations typically range from O(1) to O(N log N).\n"
                f"- **Space Complexity**: Depends on memory allocations and call stack depth."
            ))
            return (
                f"⏱️ **Time & Space Complexity: {kb['title']}**\n\n"
                f"{complexity_info}\n\n"
                f"💡 *Would you like to explore optimization techniques or test your knowledge with a quiz?*"
            )

        if "iterative" in lower_input or "loop" in lower_input or "recursive version" in lower_input:
            alt_code = kb.get("alternative_implementation", "")
            if alt_code:
                return (
                    f"🔄 **Implementation Comparison: {kb['title']}**\n\n"
                    f"{alt_code}\n\n"
                    f"Would you like to trace how this executes or see another approach?"
                )

        # 7. General / Neutral Step-by-Step Response for the matched topic
        return (
            f"📚 **Understanding {kb['title']} Step-by-Step**\n\n"
            f"> 💡 **Analogy**: {kb['analogy']}\n\n"
            f"Here are the essential building blocks:\n\n"
            + "\n\n".join(kb["steps"]) + "\n\n"
            f"Here is the foundational code structure in Python:\n\n"
            f"```python\n{kb['example_code']}```\n\n"
            f"Would you like me to walk through this line by line, or would you like to test your understanding with an adaptive quiz?"
        )

    def _format_offline_representation(
        self,
        topic_key: str,
        knowledge: Dict[str, Any],
        requested_format: str,
        cue: EmotionCue
    ) -> str:
        if requested_format == "pseudocode":
            body = OFFLINE_PSEUDOCODE.get(topic_key)
            title = "Pseudocode"
            language = "text"
        elif requested_format == "algorithm":
            pseudo_steps = OFFLINE_PSEUDOCODE.get(topic_key)
            body = "\n".join(
                f"{index}. {step.strip()}"
                for index, step in enumerate(pseudo_steps.splitlines(), 1)
            ) if pseudo_steps else "\n".join(knowledge["steps"])
            title = "Algorithm"
            language = "text"
        elif requested_format == "code":
            body = knowledge.get("example_code")
            title = "Example Code (Python)"
            language = "python"
        else:
            body = OFFLINE_DIAGRAMS.get(topic_key)
            title = "Concept Diagram"
            language = "text"

        if not body:
            return (
                f"I don't have an offline {requested_format} template for {knowledge['title']} yet. "
                "I can still explain the concept step by step, or you can try again when the live tutor is available."
            )

        reassurance = ""
        if cue == EmotionCue.CONFUSION:
            reassurance = "No problem—let's make the idea concrete and easier to follow.\n\n"
        elif cue == EmotionCue.FRUSTRATION:
            reassurance = "We can take this one small step at a time.\n\n"
        elif cue == EmotionCue.NERVOUSNESS:
            reassurance = "It is normal to need practice; take this at your own pace.\n\n"

        return (
            f"{reassurance}"
            f"**{title}: {knowledge['title']}**\n\n"
            f"```{language}\n{body}\n```\n\n"
            f"{knowledge['steps'][0]}"
        )

    def _generate_unsupported_topic_clarification(self, user_input: str, topic: Optional[str] = None) -> str:
        """Generates an honest, helpful clarification when an unsupported topic is asked offline."""
        return (
            f"🤔 **Offline Pedagogical Mode Active**\n\n"
            f"You asked: *\"{user_input}\"*\n\n"
            f"In **offline mode**, my built-in curriculum specifically covers:\n"
            f"1. 🔢 **Mathematics & Number Theory**: HCF (GCD), LCM, Prime Factorization, Euclidean Algorithm\n"
            f"2. 🔄 **Recursion & Backtracking**: Base cases, call stacks, unwinding, recursion trees\n"
            f"3. 📦 **Core Data Structures**: Arrays, Singly & Doubly Linked Lists, Binary Search Trees, Graphs\n"
            f"4. ⚡ **Sorting Algorithms**: Merge Sort, Quick Sort, Bubble Sort, Complexity Analysis\n\n"
            f"💡 **To enable live AI answers for {topic or 'custom school topics'}**:\n"
            f"Set a valid `GEMINI_API_KEY` in `backend/.env` for real-time AI reasoning.\n\n"
            f"Which of the core topics above would you like to explore together?"
        )

    def _match_offline_topic_key(self, text: str) -> Optional[str]:
        """Matches explicit topic keywords in text to an offline knowledge base key."""
        lower = text.lower()
        if any(k in lower for k in [
            "hcf", "lcm", "gcd", "greatest common divisor", "highest common factor",
            "lowest common multiple", "least common multiple", "euclidean algorithm",
            "prime factorization", "common factor", "common multiple"
        ]):
            return "mathematics"
        if any(k in lower for k in ["recursion", "recursive", "base case", "call stack", "factorial"]):
            return "recursion"
        if any(k in lower for k in ["linked list", "linked lists", "singly linked", "doubly linked"]):
            return "linked lists"
        if any(k in lower for k in ["binary search tree", "binary tree", "bst", "trees", "tree traversal"]):
            return "trees"
        if any(k in lower for k in ["array", "arrays", "dynamic array", "contiguous memory"]):
            return "arrays"
        if any(k in lower for k in ["sorting", "merge sort", "quicksort", "quick sort", "bubble sort"]):
            return "sorting"
        if any(k in lower for k in ["graph", "graphs", "bfs", "dfs", "dijkstra"]):
            return "graphs"
        return None

    def _detect_topic(self, text: str) -> Optional[str]:
        """Detects topic name for conversation state tracking."""
        key = self._match_offline_topic_key(text)
        return self._key_to_topic_name(key) if key else None

    def _key_to_topic_name(self, key: str) -> str:
        mapping = {
            "mathematics": "Mathematics",
            "recursion": "Recursion",
            "linked lists": "Linked Lists",
            "trees": "Trees",
            "arrays": "Arrays",
            "sorting": "Sorting",
            "graphs": "Graphs"
        }
        return mapping.get(key, key.title())

    def _topic_name_to_key(self, topic: Optional[str]) -> Optional[str]:
        if not topic:
            return None
        lower = topic.lower()
        if "math" in lower or "hcf" in lower or "lcm" in lower or "gcd" in lower:
            return "mathematics"
        for k in OFFLINE_TOPIC_KNOWLEDGE:
            if k in lower:
                return k
        return None

    def _is_followup_to_current_topic(self, user_input: str) -> bool:
        """
        Checks if a user input is a continuation/follow-up question to the currently active topic.
        Returns False if the user appears to be asking a new, unrelated concept question.
        """
        if not self.current_topic:
            return False
        lower = user_input.lower().strip()

        if detect_requested_format(user_input):
            return True

        # Generic follow-up inquiries that refer to the previous answer
        generic_followup_patterns = [
            r"\b(line\s+by\s+line|walk\s*through|step\s+by\s+step\s+code|trace\s+code|explain\s+this\s+code)\b",
            r"\b(time\s+complexity|space\s+complexity|big\s*o|complexity)\b",
            r"\b(iterative|loop|recursive\s+version|recursive\s+way)\b",
            r"\b(call\s+stack|unwind|stack\s+overflow)\b",
            r"\b(edge\s+case|what\s+if\s+n|negative|zero)\b",
            r"\b(another\s+example|more\s+examples|simpler\s+example|show\s+example|real[- ]world|real[- ]life|analogy|analogies)\b",
            r"\b(why|how\s+does\s+that\s+work|what\s+do\s+you\s+mean|can\s+you\s+simplify|i\s+don't\s+understand|confused)\b"
        ]
        for pattern in generic_followup_patterns:
            if re.search(pattern, lower):
                return True

        # Check if user explicitly mentioned keywords of the current topic
        current_key = self._topic_name_to_key(self.current_topic)
        if current_key and current_key in lower:
            return True

        # If it is a short question under 4 words without an explicit new subject, treat as follow-up
        tokens = lower.split()
        if len(tokens) <= 3 and not any(verb in lower for verb in ["explain", "teach", "what is", "define"]):
            return True

        return False

    def generate_contextual_suggestions(
        self,
        user_input: str,
        response_text: str,
        topic: str,
        cue: EmotionCue,
        allow_gemini: bool = True
    ) -> List[str]:
        """
        Dynamically generates 2-3 contextual follow-up suggestions.
        Avoids repeating suggestions that were already displayed or answered in this session.
        Uses Gemini when available, with a rich offline candidate engine fallback.
        """
        # Try Gemini dynamic suggestions if online
        if GEMINI_API_KEY and allow_gemini:
            try:
                from google import genai
                client = genai.Client(
                    api_key=GEMINI_API_KEY,
                    http_options={"timeout": GEMINI_REQUEST_TIMEOUT_MS}
                )
                prompt = CONTEXTUAL_SUGGESTIONS_PROMPT.format(
                    topic=topic,
                    student_level=self.student_level,
                    student_query=user_input,
                    tutor_summary=response_text[:250],
                    previous_suggestions="\n".join(f"- {s}" for s in self.seen_suggestions) if self.seen_suggestions else "None yet"
                )
                res = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
                if res and res.text:
                    raw = res.text.strip()
                    if raw.startswith("```json"):
                        raw = raw[7:]
                    if raw.startswith("```"):
                        raw = raw[3:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    items = json.loads(raw.strip())
                    if isinstance(items, list) and len(items) >= 2:
                        valid_items = [
                            s.strip() for s in items
                            if isinstance(s, str) and s.strip() and s.strip() not in self.seen_suggestions
                        ]
                        if len(valid_items) >= 2:
                            # Ensure last option is a quiz trigger
                            if not any(is_quiz_trigger(s)[0] for s in valid_items):
                                valid_items.append(f"Start an adaptive quiz on {topic}")
                            chosen = valid_items[:3]
                            self.seen_suggestions.update(chosen)
                            return chosen
            except Exception as exc:
                print(f"[STUDENT TUTOR] Gemini suggestions call failed ({exc}). Using offline suggestions engine.")

        # Deterministic offline suggestion generator
        return self._generate_offline_contextual_suggestions(user_input, response_text, topic, cue)

    def _generate_offline_contextual_suggestions(
        self,
        user_input: str,
        response_text: str,
        topic: str,
        cue: EmotionCue
    ) -> List[str]:
        """
        Selects 3 fresh, contextual suggestions from the offline pool.
        Strictly filters out any candidate in `self.seen_suggestions` to prevent repetition.
        """
        norm_topic = self._topic_name_to_key(topic) or "recursion"

        pool = OFFLINE_SUGGESTION_POOLS.get(norm_topic, OFFLINE_SUGGESTION_POOLS["recursion"])
        lower_input = user_input.lower()
        selected: List[str] = []

        # Category 1: Concept / Code Question based on turn context
        if "line by line" in lower_input or "code" in lower_input:
            cat1 = "code_trace"
            cat2 = "complexity"
        elif cue == EmotionCue.CONFUSION:
            cat1 = "clarification"
            cat2 = "code_trace"
        elif cue == EmotionCue.CONFIDENCE:
            cat1 = "complexity"
            cat2 = "clarification"
        else:
            cat1 = "clarification"
            cat2 = "code_trace"

        # Helper to pick first unseen item from a category
        def pick_unseen(category: str) -> Optional[str]:
            for cand in pool.get(category, []):
                if cand not in self.seen_suggestions and cand not in selected:
                    return cand
            return None

        # Pick Option 1
        opt1 = pick_unseen(cat1) or pick_unseen("clarification")
        if opt1:
            selected.append(opt1)

        # Pick Option 2
        opt2 = pick_unseen(cat2) or pick_unseen("code_trace") or pick_unseen("complexity")
        if opt2:
            selected.append(opt2)

        # Pick Option 3: Adaptive Quiz Trigger
        opt3 = pick_unseen("quizzes")
        if not opt3:
            opt3 = f"Start an adaptive quiz on {topic}"
        selected.append(opt3)

        # Fallback if any slot is missing: construct dynamic contextual questions
        while len(selected) < 3:
            dynamic_cand = f"What are common edge cases in {topic}?"
            if dynamic_cand not in self.seen_suggestions and dynamic_cand not in selected:
                selected.insert(len(selected) - 1, dynamic_cand)
            else:
                dynamic_cand2 = f"How does {topic} compare to other concepts?"
                selected.insert(len(selected) - 1, dynamic_cand2)
                break

        # Record in seen_suggestions
        self.seen_suggestions.update(selected)
        return selected

    def get_fresh_quiz_followups(self, topic: str) -> List[str]:
        """Returns fresh suggestions following the completion of a quiz."""
        norm_topic = self._topic_name_to_key(topic) or "recursion"
        pool = OFFLINE_SUGGESTION_POOLS.get(norm_topic, OFFLINE_SUGGESTION_POOLS["recursion"])
        followups = []
        for cat in ["complexity", "clarification", "code_trace"]:
            for cand in pool.get(cat, []):
                if cand not in self.seen_suggestions and cand not in followups:
                    followups.append(cand)
                    break
            if len(followups) == 2:
                break

        followups.append(f"Take another practice quiz on {topic}")
        self.seen_suggestions.update(followups)
        return followups

    def _check_line_by_line_intent(self, text: str) -> bool:
        lower = text.lower()
        return bool(re.search(r"\b(line\s+by\s+line|walk\s*through|step\s+by\s+step\s+code|trace\s+code|explain\s+this\s+code)\b", lower))
