from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import (
    Teacher, Mentor, TeacherSubject, Mark, Class, Student, Concept, Question, QuizAttempt, QuizAttemptAnswer, ConceptPerformance
)
from app.security import hash_password

def get_calibrated_student_scores():
    """
    Deterministically computes calibrated concept scores for 80 students.
    Verified mathematical outputs:
      - Arrays avg: 82.00%
      - Linked Lists avg: 64.00%
      - Trees avg: 41.00%
      - Recursion avg: 35.00%
      - Graphs avg: 58.00%
      - Sorting avg: 75.00%
      - Recursion < 40%: EXACTLY 23 students
      - Global distribution (by overall student mastery):
          Advanced (>=85%): 12 students
          On Track (55%-84%): 45 students
          Needs Support (40%-54%): 18 students
          Needs Attention (<40%): 5 students
          Total: 80 students
    """
    scores = [{} for _ in range(80)]

    # 0: Aarav Sharma (Needs attention in Recursion: 28%)
    scores[0] = {'Arrays': 91, 'Linked Lists': 70, 'Trees': 40, 'Recursion': 28, 'Graphs': 45, 'Sorting': 48}
    # 1: Ananya Roy (Weak concept: Trees 35%)
    scores[1] = {'Arrays': 70, 'Linked Lists': 62, 'Trees': 35, 'Recursion': 40, 'Graphs': 48, 'Sorting': 55}
    # 2: Rahul Verma (Weak concept: Recursion 32%)
    scores[2] = {'Arrays': 72, 'Linked Lists': 60, 'Trees': 42, 'Recursion': 32, 'Graphs': 48, 'Sorting': 56}
    # 3: Priya Nair (Weak concept: Linked Lists 39%)
    scores[3] = {'Arrays': 70, 'Linked Lists': 39, 'Trees': 42, 'Recursion': 40, 'Graphs': 48, 'Sorting': 55}
    # 4: Priya Patel (Advanced learner, 92%)
    scores[4] = {'Arrays': 95, 'Linked Lists': 90, 'Trees': 88, 'Recursion': 94, 'Graphs': 92, 'Sorting': 93}

    # 11 more Advanced students (5..15) -> Total Advanced = 12
    for i in range(5, 16):
        scores[i] = {
            'Arrays': 98,
            'Linked Lists': 96,
            'Trees': 90,
            'Recursion': 40,
            'Graphs': 96,
            'Sorting': 98
        }

    # 5 Needs Attention students (75..79) -> Overall < 40% (All 5 have Recursion < 40%)
    for i in range(75, 80):
        scores[i] = {
            'Arrays': 42,
            'Linked Lists': 36,
            'Trees': 26,
            'Recursion': 16,
            'Graphs': 32,
            'Sorting': 42
        }

    # 14 more Needs Support students (16..29) -> Overall 40%-54% (All 14 have Recursion < 40%)
    for i in range(16, 30):
        scores[i] = {
            'Arrays': 72,
            'Linked Lists': 56,
            'Trees': 34,
            'Recursion': 20,
            'Graphs': 50,
            'Sorting': 68
        }

    # 45 On Track students (30..74) -> Overall 55%-84%
    for i in range(30, 75):
        rec = 23 if i in (30, 31) else 40
        scores[i] = {
            'Arrays': 86,
            'Linked Lists': 72,
            'Trees': 45,
            'Recursion': rec,
            'Graphs': 66,
            'Sorting': 86
        }

    target_averages = {
        'Arrays': 82.0,
        'Linked Lists': 64.0,
        'Trees': 41.0,
        'Recursion': 35.0,
        'Graphs': 58.0,
        'Sorting': 75.0
    }

    for c in ['Arrays', 'Linked Lists', 'Trees', 'Graphs', 'Sorting']:
        target_sum = int(round(target_averages[c] * 80))
        cur_sum = sum(s[c] for s in scores)
        diff = target_sum - cur_sum

        pool = list(range(32, 75))
        for step_i in range(abs(diff)):
            idx = pool[step_i % len(pool)]
            add = 1 if diff > 0 else -1
            scores[idx][c] += add

    return scores

QUESTIONS_SEED = [
    # Recursion (5 questions)
    {
        "concept": "Recursion",
        "difficulty": "beginner",
        "question": "What is the primary purpose of a base case in a recursive function?",
        "a": "To allocate more heap memory for recursive calls",
        "b": "To terminate the recursion and prevent infinite call stack overflow",
        "c": "To convert recursion into an iterative while loop",
        "d": "To speed up the processor clock cycle",
        "correct": "B",
        "explanation": "A base case provides the termination condition where the function returns directly without making further recursive calls, preventing a stack overflow."
    },
    {
        "concept": "Recursion",
        "difficulty": "beginner",
        "question": "Which data structure is intrinsically used by the system call stack during recursive execution?",
        "a": "Queue (FIFO)",
        "b": "Stack (LIFO)",
        "c": "Binary Search Tree",
        "d": "Hash Table",
        "correct": "B",
        "explanation": "Function call frames are pushed onto the call stack and popped in Last-In-First-Out (LIFO) order as each recursive invocation completes."
    },
    {
        "concept": "Recursion",
        "difficulty": "intermediate",
        "question": "What is the recurrence relation for the standard Tower of Hanoi problem with n disks?",
        "a": "T(n) = 2T(n-1) + 1",
        "b": "T(n) = T(n-1) + n",
        "c": "T(n) = 2T(n/2) + O(1)",
        "d": "T(n) = T(n-2) + 2",
        "correct": "A",
        "explanation": "Moving n disks requires moving n-1 disks to auxiliary peg, 1 disk to target peg, and n-1 disks onto target peg: T(n) = 2T(n-1) + 1 = 2^n - 1."
    },
    {
        "concept": "Recursion",
        "difficulty": "intermediate",
        "question": "Why is a tail-recursive function considered more memory-efficient when optimized by a compiler?",
        "a": "It uses dynamic programming lookup tables",
        "b": "The compiler can reuse the current stack frame instead of creating a new one",
        "c": "It automatically converts recursive variables into global static memory",
        "d": "It runs the recursive steps on multiple CPU threads simultaneously",
        "correct": "B",
        "explanation": "With tail-call elimination, the final operation is the recursive call itself, so the compiler reuses the existing stack frame in O(1) auxiliary space."
    },
    {
        "concept": "Recursion",
        "difficulty": "advanced",
        "question": "In tree recursion like generating all subsets, what is the call stack depth and total function invocations for n elements?",
        "a": "Depth: O(n), Total Calls: O(2^n)",
        "b": "Depth: O(2^n), Total Calls: O(n)",
        "c": "Depth: O(log n), Total Calls: O(n^2)",
        "d": "Depth: O(n^2), Total Calls: O(n!)",
        "correct": "A",
        "explanation": "The maximum stack depth is proportional to the recursion tree height O(n), while the total number of subset decisions creates 2^(n+1) - 1 = O(2^n) total calls."
    },

    # Arrays (5 questions)
    {
        "concept": "Arrays",
        "difficulty": "beginner",
        "question": "What is the time complexity of accessing an element at a given index in a contiguous array?",
        "a": "O(1)",
        "b": "O(n)",
        "c": "O(log n)",
        "d": "O(n log n)",
        "correct": "A",
        "explanation": "Arrays are stored in contiguous memory locations, allowing direct memory address calculation: Base_Address + (Index * Element_Size) in O(1)."
    },
    {
        "concept": "Arrays",
        "difficulty": "beginner",
        "question": "What is the worst-case time complexity of inserting an element at the beginning of an unsorted array of size n?",
        "a": "O(1)",
        "b": "O(n)",
        "c": "O(log n)",
        "d": "O(n^2)",
        "correct": "B",
        "explanation": "Inserting at index 0 requires shifting all n existing elements one position to the right, which takes O(n) operations."
    },
    {
        "concept": "Arrays",
        "difficulty": "intermediate",
        "question": "Kadane's algorithm is used to solve which classic array problem in O(n) time?",
        "a": "Finding the longest increasing subsequence",
        "b": "Maximum contiguous subarray sum",
        "c": "Median of two sorted arrays",
        "d": "Matrix multiplication",
        "correct": "B",
        "explanation": "Kadane's algorithm computes the maximum subarray sum in a single linear pass O(n) by maintaining max_so_far and current_max."
    },
    {
        "concept": "Arrays",
        "difficulty": "intermediate",
        "question": "In a dynamic array (like std::vector or Python list), what is the amortized time complexity of appending an element?",
        "a": "O(n)",
        "b": "O(1)",
        "c": "O(log n)",
        "d": "O(n^2)",
        "correct": "B",
        "explanation": "Although occasional resizing takes O(n), doubling the capacity ensures the amortized cost per append operation is O(1)."
    },
    {
        "concept": "Arrays",
        "difficulty": "advanced",
        "question": "To rotate an array of size n to the right by k steps in O(n) time and O(1) extra space, which strategy is optimal?",
        "a": "Three reversals: reverse entire array, then reverse first k, then remaining n-k",
        "b": "Copy elements into a temporary hash table",
        "c": "Bubble sort each element k times",
        "d": "Binary search on rotated indices",
        "correct": "A",
        "explanation": "The 3-step reversal algorithm reverses the whole array, then the first k elements, then the remaining elements in O(n) time with O(1) space."
    },

    # Linked Lists (5 questions)
    {
        "concept": "Linked Lists",
        "difficulty": "beginner",
        "question": "What is the primary structural difference between an array and a singly linked list?",
        "a": "Arrays store pointers; linked lists store integers only",
        "b": "Arrays have contiguous memory; linked list nodes are linked via pointers",
        "c": "Linked lists provide O(1) random index access",
        "d": "Arrays can grow indefinitely without memory limits",
        "correct": "B",
        "explanation": "Linked list nodes can be stored anywhere in heap memory and are chained together using next pointers, avoiding fixed contiguous blocks."
    },
    {
        "concept": "Linked Lists",
        "difficulty": "beginner",
        "question": "What is the time complexity of deleting the head node of a singly linked list when given the head pointer?",
        "a": "O(1)",
        "b": "O(n)",
        "c": "O(log n)",
        "d": "O(n^2)",
        "correct": "A",
        "explanation": "Deleting head only requires updating head = head->next, taking O(1) constant time."
    },
    {
        "concept": "Linked Lists",
        "difficulty": "intermediate",
        "question": "Floyd's Cycle-Finding Algorithm detects a loop in a linked list using which pointer technique?",
        "a": "Divide and conquer pointers",
        "b": "Fast and slow (tortoise and hare) pointers",
        "c": "Two backward pointers from tail",
        "d": "Bitwise XOR pointer traversal",
        "correct": "B",
        "explanation": "A slow pointer moves 1 step and a fast pointer moves 2 steps; if a loop exists, they are guaranteed to meet inside the cycle."
    },
    {
        "concept": "Linked Lists",
        "difficulty": "intermediate",
        "question": "To find the middle element of a singly linked list in a single pass without knowing length, we use:",
        "a": "Binary search on pointer addresses",
        "b": "Slow pointer moving 1 step, fast pointer moving 2 steps",
        "c": "Recursively reversing the list twice",
        "d": "Storing all nodes in a min-heap",
        "correct": "B",
        "explanation": "When the fast pointer reaches the end of the list, the slow pointer will be positioned exactly at the middle node."
    },
    {
        "concept": "Linked Lists",
        "difficulty": "advanced",
        "question": "In a Doubly Linked List with sentinel head and tail nodes, what is the benefit of LRU Cache implementation?",
        "a": "O(1) removal and O(1) insertion to front/tail combined with a hash map",
        "b": "Automatic sorting of cached keys by numerical value",
        "c": "Reduces hash collision probability to zero",
        "d": "Allows thread-safe execution without mutex locks",
        "correct": "A",
        "explanation": "A doubly linked list allows removing any node in O(1) once its pointer is found via hash map and inserting it at the front in O(1)."
    },

    # Trees (5 questions)
    {
        "concept": "Trees",
        "difficulty": "beginner",
        "question": "In a Binary Search Tree (BST), what invariant must hold for every node X?",
        "a": "Left child <= X <= Right child",
        "b": "Both children must be strictly greater than X",
        "c": "All leaves must reside at the same depth",
        "d": "The root must contain the maximum value",
        "correct": "A",
        "explanation": "For any node in a BST, all keys in its left subtree are less than or equal to the node key, and all keys in the right subtree are greater."
    },
    {
        "concept": "Trees",
        "difficulty": "beginner",
        "question": "Which tree traversal visited nodes in non-decreasing order for a Binary Search Tree?",
        "a": "Pre-order (Root, Left, Right)",
        "b": "In-order (Left, Root, Right)",
        "c": "Post-order (Left, Right, Root)",
        "d": "Level-order (Breadth First)",
        "correct": "B",
        "explanation": "In-order traversal visits Left subtree, then current Node, then Right subtree, producing keys in strictly sorted order."
    },
    {
        "concept": "Trees",
        "difficulty": "intermediate",
        "question": "What is the maximum number of nodes in a full binary tree of height h (where a root-only tree has height 0)?",
        "a": "2^(h+1) - 1",
        "b": "2^h",
        "c": "2h + 1",
        "d": "h^2",
        "correct": "A",
        "explanation": "Sum of nodes at levels 0 to h: 1 + 2 + 4 + ... + 2^h = 2^(h+1) - 1."
    },
    {
        "concept": "Trees",
        "difficulty": "intermediate",
        "question": "What is the balance factor of a node in an AVL Tree?",
        "a": "Height(Left Subtree) - Height(Right Subtree)",
        "b": "Number of left children / Number of right children",
        "c": "Depth of node * Height of tree",
        "d": "Difference in node keys",
        "correct": "A",
        "explanation": "AVL balance factor is Height(left) - Height(right), strictly maintained in {-1, 0, +1} via rotations."
    },
    {
        "concept": "Trees",
        "difficulty": "advanced",
        "question": "What is the worst-case search time in an un-balanced degenerate BST with n elements?",
        "a": "O(log n)",
        "b": "O(n)",
        "c": "O(1)",
        "d": "O(n log n)",
        "correct": "B",
        "explanation": "If elements are inserted in sorted order, the BST degenerates into a linked list of height n, giving O(n) search time."
    },

    # Graphs (5 questions)
    {
        "concept": "Graphs",
        "difficulty": "beginner",
        "question": "Which graph representation is more memory-efficient for a sparse graph with V vertices and E edges?",
        "a": "Adjacency Matrix (V x V)",
        "b": "Adjacency List (V + E)",
        "c": "Complete Bipartite Matrix",
        "d": "Full Permutation Array",
        "correct": "B",
        "explanation": "Adjacency list uses O(V + E) space, whereas an adjacency matrix always consumes O(V^2) regardless of the number of edges."
    },
    {
        "concept": "Graphs",
        "difficulty": "beginner",
        "question": "Breadth-First Search (BFS) on an unweighted graph naturally discovers what kind of path?",
        "a": "Longest simple path",
        "b": "Shortest path in terms of number of edges",
        "c": "Eulerian circuit",
        "d": "Minimum vertex cover",
        "correct": "B",
        "explanation": "Because BFS explores vertices layer by layer in increasing distance from the source, it finds the shortest path in unweighted graphs."
    },
    {
        "concept": "Graphs",
        "difficulty": "intermediate",
        "question": "Dijkstra's shortest path algorithm fails or produces incorrect results when:",
        "a": "The graph contains cycles",
        "b": "The graph contains negative weight edges",
        "c": "The graph has more than 1000 vertices",
        "d": "The graph is directed",
        "correct": "B",
        "explanation": "Dijkstra assumes that adding an edge cannot decrease the path distance (greedy choice); negative edges violate this premise."
    },
    {
        "concept": "Graphs",
        "difficulty": "intermediate",
        "question": "Kruskal's algorithm finds a Minimum Spanning Tree using which greedy strategy and helper data structure?",
        "a": "Sorting edges by weight and Disjoint Set Union (DSU / Union-Find)",
        "b": "Priority queue on vertices and DFS stack",
        "c": "Topological sort and dynamic programming table",
        "d": "Bellman-Ford matrix relaxation",
        "correct": "A",
        "explanation": "Kruskal sorts all edges by ascending weight and adds an edge if it connects two disconnected components, checked via DSU."
    },
    {
        "concept": "Graphs",
        "difficulty": "advanced",
        "question": "Topological sorting can only be performed on which class of graphs?",
        "a": "Undirected graphs with positive weights",
        "b": "Directed Acyclic Graphs (DAGs)",
        "c": "Complete Bipartite graphs",
        "d": "Self-looping multigraphs",
        "correct": "B",
        "explanation": "A topological sort requires a dependency ordering where every directed edge u -> v has u preceding v, which is impossible if any cycle exists."
    },

    # Sorting (5 questions)
    {
        "concept": "Sorting",
        "difficulty": "beginner",
        "question": "What is the best-case time complexity of standard Bubble Sort when an early-exit swapped flag is used on an already sorted array?",
        "a": "O(1)",
        "b": "O(n)",
        "c": "O(n log n)",
        "d": "O(n^2)",
        "correct": "B",
        "explanation": "With an early-exit check, a single O(n) pass detects that zero swaps occurred and terminates."
    },
    {
        "concept": "Sorting",
        "difficulty": "beginner",
        "question": "Which sorting algorithm is guaranteed to run in O(n log n) time in all cases (worst, average, best) and is stable?",
        "a": "Quick Sort",
        "b": "Merge Sort",
        "c": "Selection Sort",
        "d": "Heap Sort",
        "correct": "B",
        "explanation": "Merge sort divides the list in half and merges sorted sub-lists, maintaining O(n log n) in all cases while preserving relative order of equal keys."
    },
    {
        "concept": "Sorting",
        "difficulty": "intermediate",
        "question": "What is the worst-case time complexity of Quick Sort, and when does it occur with standard first-element pivot selection?",
        "a": "O(n^2) when the array is already sorted or reverse sorted",
        "b": "O(n log n) always",
        "c": "O(n) on random arrays",
        "d": "O(2^n) on duplicate keys",
        "correct": "A",
        "explanation": "If pivot selection consistently yields 1 and n-1 partitions (as with sorted arrays using first-element pivot), the recurrence is T(n) = T(n-1) + O(n) = O(n^2)."
    },
    {
        "concept": "Sorting",
        "difficulty": "intermediate",
        "question": "Why is Counting Sort able to sort n integers in O(n + k) linear time?",
        "a": "It uses comparison trees faster than O(n log n)",
        "b": "It is a non-comparison sort that uses keys as array indices",
        "c": "It parallelizes quick sort across multiple CPU cores",
        "d": "It divides arrays into log n blocks",
        "correct": "B",
        "explanation": "Counting sort does not compare elements directly; it tallies occurrences of distinct key values within range k and constructs the output in O(n + k)."
    },
    {
        "concept": "Sorting",
        "difficulty": "advanced",
        "question": "Heap Sort uses a binary heap to sort in O(n log n) time. What is its auxiliary space complexity?",
        "a": "O(1) in-place",
        "b": "O(n)",
        "c": "O(log n)",
        "d": "O(n^2)",
        "correct": "A",
        "explanation": "Heap Sort builds the max-heap directly within the input array and swaps max elements to the end in-place with O(1) auxiliary space."
    }
]

STUDENT_NAMES = [
    # Prominent Demo Students
    ("Aarav Sharma", "student@demo.com", "CSE2024-001"),
    ("Ananya Roy", "ananya@demo.com", "CSE2024-002"),
    ("Rahul Verma", "rahul@demo.com", "CSE2024-003"),
    ("Priya Nair", "priyan@demo.com", "CSE2024-004"),
    ("Priya Patel", "advanced@demo.com", "CSE2024-005"),
    # Additional students to reach 80
    ("Rohan Mehta", "rohan.m@demo.com", "CSE2024-006"),
    ("Sneha Iyer", "sneha.i@demo.com", "CSE2024-007"),
    ("Aditya Kulkarni", "aditya.k@demo.com", "CSE2024-008"),
    ("Neha Gupta", "neha.g@demo.com", "CSE2024-009"),
    ("Vikram Malhotra", "vikram.m@demo.com", "CSE2024-010"),
    ("Divya Deshmukh", "divya.d@demo.com", "CSE2024-011"),
    ("Kabir Joshi", "kabir.j@demo.com", "CSE2024-012"),
    ("Tanvi Saxena", "tanvi.s@demo.com", "CSE2024-013"),
    ("Ishaan Reddy", "ishaan.r@demo.com", "CSE2024-014"),
    ("Kavya Pillai", "kavya.p@demo.com", "CSE2024-015"),
    ("Arjun Nambiar", "arjun.n@demo.com", "CSE2024-016"),
    ("Riya Banerjee", "riya.b@demo.com", "CSE2024-017"),
    ("Siddharth Rao", "siddharth.r@demo.com", "CSE2024-018"),
    ("Anika Menon", "anika.m@demo.com", "CSE2024-019"),
    ("Manish Tiwari", "manish.t@demo.com", "CSE2024-020"),
    ("Pooja Bhat", "pooja.b@demo.com", "CSE2024-021"),
    ("Varun Hegde", "varun.h@demo.com", "CSE2024-022"),
    ("Meera Nair", "meera.n@demo.com", "CSE2024-023"),
    ("Akash Shinde", "akash.s@demo.com", "CSE2024-024"),
    ("Shreya Kadam", "shreya.k@demo.com", "CSE2024-025"),
    ("Gaurav Chavan", "gaurav.c@demo.com", "CSE2024-026"),
    ("Ritika Sethi", "ritika.s@demo.com", "CSE2024-027"),
    ("Kunal Mathur", "kunal.m@demo.com", "CSE2024-028"),
    ("Swati Mishra", "swati.m@demo.com", "CSE2024-029"),
    ("Harsh Vardhan", "harsh.v@demo.com", "CSE2024-030"),
    ("Preeti Kapoor", "preeti.k@demo.com", "CSE2024-031"),
    ("Naveen Chopra", "naveen.c@demo.com", "CSE2024-032"),
    ("Kriti Aggarwal", "kriti.a@demo.com", "CSE2024-033"),
    ("Sameer Jain", "sameer.j@demo.com", "CSE2024-034"),
    ("Tanya Mittal", "tanya.m@demo.com", "CSE2024-035"),
    ("Abhishek Pandey", "abhishek.p@demo.com", "CSE2024-036"),
    ("Sanya Goel", "sanya.g@demo.com", "CSE2024-037"),
    ("Ayush Singhal", "ayush.s@demo.com", "CSE2024-038"),
    ("Pallavi Shah", "pallavi.s@demo.com", "CSE2024-039"),
    ("Deepak Meena", "deepak.m@demo.com", "CSE2024-040"),
    ("Simran Gill", "simran.g@demo.com", "CSE2024-041"),
    ("Yash Rathore", "yash.r@demo.com", "CSE2024-042"),
    ("Komal Yadav", "komal.y@demo.com", "CSE2024-043"),
    ("Pranav Dixit", "pranav.d@demo.com", "CSE2024-044"),
    ("Monika Soni", "monika.s@demo.com", "CSE2024-045"),
    ("Suraj Kumar", "suraj.k@demo.com", "CSE2024-046"),
    ("Natasha Kaul", "natasha.k@demo.com", "CSE2024-047"),
    ("Mohit Rawat", "mohit.r@demo.com", "CSE2024-048"),
    ("Bhavna Das", "bhavna.d@demo.com", "CSE2024-049"),
    ("Ashwin Varma", "ashwin.v@demo.com", "CSE2024-050"),
    ("Payal Roy", "payal.r@demo.com", "CSE2024-051"),
    ("Rajesh Murthy", "rajesh.m@demo.com", "CSE2024-052"),
    ("Geeta Swaminathan", "geeta.s@demo.com", "CSE2024-053"),
    ("Dinesh Balan", "dinesh.b@demo.com", "CSE2024-054"),
    ("Lakshmi Narayanan", "lakshmi.n@demo.com", "CSE2024-055"),
    ("Suresh Prabhu", "suresh.p@demo.com", "CSE2024-056"),
    ("Vidya Krishnan", "vidya.k@demo.com", "CSE2024-057"),
    ("Manoj Subramanian", "manoj.s@demo.com", "CSE2024-058"),
    ("Radha Chandran", "radha.c@demo.com", "CSE2024-059"),
    ("Vijay Raghavan", "vijay.r@demo.com", "CSE2024-060"),
    ("Deepa Sridhar", "deepa.s@demo.com", "CSE2024-061"),
    ("Balaji Sundaram", "balaji.s@demo.com", "CSE2024-062"),
    ("Anuradha Chetty", "anuradha.c@demo.com", "CSE2024-063"),
    ("Karthik Natarajan", "karthik.n@demo.com", "CSE2024-064"),
    ("Revathi Padmanabhan", "revathi.p@demo.com", "CSE2024-065"),
    ("Senthil Kumaran", "senthil.k@demo.com", "CSE2024-066"),
    ("Usha Gopinath", "usha.g@demo.com", "CSE2024-067"),
    ("Ganesh Venkatesh", "ganesh.v@demo.com", "CSE2024-068"),
    ("Sandhya Raman", "sandhya.r@demo.com", "CSE2024-069"),
    ("Raghavan Natesan", "raghavan.n@demo.com", "CSE2024-070"),
    ("Padma Srinivasan", "padma.s@demo.com", "CSE2024-071"),
    ("Madhavan Kannan", "madhavan.k@demo.com", "CSE2024-072"),
    ("Lalitha Thiagarajan", "lalitha.t@demo.com", "CSE2024-073"),
    ("Gautam Sengupta", "gautam.s@demo.com", "CSE2024-074"),
    ("Aparna Mukherjee", "aparna.m@demo.com", "CSE2024-075"),
    ("Subhashis Bose", "subhashis.b@demo.com", "CSE2024-076"),
    ("Debolina Ghosh", "debolina.g@demo.com", "CSE2024-077"),
    ("Amitava Roychowdhury", "amitava.r@demo.com", "CSE2024-078"),
    ("Mousumi Dutta", "mousumi.d@demo.com", "CSE2024-079"),
    ("Somnath Chakraborty", "somnath.c@demo.com", "CSE2024-080"),
]

def seed_database(db: Session, force: bool = False):
    """
    Idempotent database seeder. If data is already present, skips unless force=True.
    """
    existing_students_count = db.query(Student).count()
    if existing_students_count >= 80 and not force:
        print("[SEED] Database already contains 80+ students. Skipping seeding (Idempotent).")
        return

    if force:
        print("[SEED] Force flag enabled: resetting existing records...")
        db.query(QuizAttemptAnswer).delete()
        db.query(QuizAttempt).delete()
        db.query(Mark).delete()
        db.query(ConceptPerformance).delete()
        db.query(Question).delete()
        db.query(Student).delete()
        db.query(Concept).delete()
        db.query(Class).delete()
        db.query(TeacherSubject).delete()
        db.query(Teacher).delete()
        db.query(Mentor).delete()
        db.commit()

    print("[SEED] Seeding database for AdaptiveClass AI...")

    # 1. Create Teacher
    default_password_hash = hash_password("password")
    teacher = Teacher(
        name="Prof. Vikram Sen",
        email="teacher@demo.com",
        department="Computer Science & Engineering",
        hashed_password=default_password_hash
    )
    db.add(teacher)
    db.flush()
    db.add(TeacherSubject(teacher_id=teacher.id, subject="Data Structures"))
    db.add(Mentor(
        name="Dr. Demo Mentor",
        email="mentor@demo.com",
        hashed_password=default_password_hash,
    ))
    db.flush()

    # 2. Create Class
    course_class = Class(
        name="B.E. CSE — Data Structures",
        subject="Data Structures",
        semester="Semester 3",
        teacher_id=teacher.id
    )
    db.add(course_class)
    db.flush()

    # 3. Create Concepts
    concept_names = ["Arrays", "Linked Lists", "Trees", "Recursion", "Graphs", "Sorting"]
    concept_map = {}
    for idx, c_name in enumerate(concept_names, start=1):
        concept = Concept(
            name=c_name,
            subject="Data Structures",
            description=f"Core computational concept: {c_name}",
            order_index=idx
        )
        db.add(concept)
        db.flush()
        concept_map[c_name] = concept

    # 4. Create Questions
    for q_data in QUESTIONS_SEED:
        c_obj = concept_map[q_data["concept"]]
        q = Question(
            concept_id=c_obj.id,
            difficulty=q_data["difficulty"],
            question_text=q_data["question"],
            option_a=q_data["a"],
            option_b=q_data["b"],
            option_c=q_data["c"],
            option_d=q_data["d"],
            correct_answer=q_data["correct"],
            explanation=q_data["explanation"]
        )
        db.add(q)
    db.flush()

    # 5. Create 80 Students and ConceptPerformances
    calibrated_scores = get_calibrated_student_scores()
    now = datetime.now(timezone.utc)

    for i, (name, email, roll) in enumerate(STUDENT_NAMES):
        student = Student(
            name=name,
            email=email,
            roll_number=roll,
            class_id=course_class.id,
            hashed_password=default_password_hash
        )
        db.add(student)
        db.flush()

        student_scores = calibrated_scores[i]
        attempts_num = 3 if i == 0 else 2
        for c_name, score in student_scores.items():
            perf = ConceptPerformance(
                student_id=student.id,
                concept_id=concept_map[c_name].id,
                mastery_score=float(score),
                attempt_count=attempts_num,
                correct_count=int(round(score / 100.0 * 10)),
                last_updated=now - timedelta(days=(i % 5))
            )
            db.add(perf)

        # Seed recent quizzes for Aarav Sharma (student 0)
        if i == 0:
            rec_id = concept_map["Recursion"].id
            arr_id = concept_map["Arrays"].id
            ll_id = concept_map["Linked Lists"].id

            # Quiz 1 (Arrays): 72%
            db.add(QuizAttempt(
                student_id=student.id,
                concept_id=arr_id,
                quiz_title="Quiz 1: Array Traversals & Bounds",
                score=72,
                total_questions=100,
                accuracy=72.0,
                timestamp=now - timedelta(days=14)
            ))
            # Quiz 2 (Linked Lists): 64%
            db.add(QuizAttempt(
                student_id=student.id,
                concept_id=ll_id,
                quiz_title="Quiz 2: Singly & Doubly Linked Chains",
                score=64,
                total_questions=100,
                accuracy=64.0,
                timestamp=now - timedelta(days=7)
            ))
            # Quiz 3 (Recursion Assessment): 48%
            db.add(QuizAttempt(
                student_id=student.id,
                concept_id=rec_id,
                quiz_title="Quiz 3: Recursive Stack Formulation",
                score=48,
                total_questions=100,
                accuracy=48.0,
                timestamp=now - timedelta(days=2)
            ))

    db.commit()
    print("[SEED] Successfully seeded 80 students, 6 concepts, and 30 questions into PostgreSQL!")

if __name__ == "__main__":
    from app.database import SessionLocal, Base, engine
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    try:
        seed_database(db_session, force=True)
    finally:
        db_session.close()
