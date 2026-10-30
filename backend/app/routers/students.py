from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Concept, ConceptPerformance
from app.schemas import StudentProfileResponse
from app.analytics_engine import get_student_profile

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("/{student_id}/profile", response_model=StudentProfileResponse)
def get_profile(student_id: int, db: Session = Depends(get_db)):
    try:
        return get_student_profile(student_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{student_id}/recommendations")
def get_recommendations(student_id: int, db: Session = Depends(get_db)):
    profile = get_student_profile(student_id, db)

    weak_concept = profile.current_learning_gap
    weak_score = next((c.mastery for c in profile.concept_performance if c.concept_name == weak_concept), 30.0)

    # Concept specific topics
    topic_map = {
        "Recursion": {
            "title": "Recursion Fundamentals & Stack Tracing",
            "topics": [
                "1. Identifying proper base cases to avoid infinite recursion",
                "2. Tracking execution frames on the call stack (LIFO)",
                "3. Formulation of recurrence relations",
                "4. Basic recursion problems (Factorial, Fibonacci, Array Reversal)"
            ],
            "estimated_minutes": 15,
            "difficulty_entry": "Beginner"
        },
        "Trees": {
            "title": "Binary Tree Structures & In-order Traversal",
            "topics": [
                "1. BST Invariant: Left <= Root <= Right",
                "2. Recursive tree traversal algorithms",
                "3. Calculating height and depth of full binary trees"
            ],
            "estimated_minutes": 20,
            "difficulty_entry": "Beginner"
        },
        "Linked Lists": {
            "title": "Linked List Pointer Operations",
            "topics": [
                "1. Pointer manipulation without memory leaks",
                "2. Two-pointer technique (fast and slow pointers)",
                "3. Cycle detection and middle node discovery"
            ],
            "estimated_minutes": 15,
            "difficulty_entry": "Beginner"
        },
        "Graphs": {
            "title": "Graph Traversal & Representations",
            "topics": [
                "1. Adjacency list vs adjacency matrix space tradeoffs",
                "2. BFS queue exploration and shortest unweighted paths"
            ],
            "estimated_minutes": 20,
            "difficulty_entry": "Intermediate"
        },
        "Arrays": {
            "title": "Array Manipulations & Subarrays",
            "topics": [
                "1. Amortized append operations in dynamic arrays",
                "2. Kadane's maximum subarray sum algorithm"
            ],
            "estimated_minutes": 15,
            "difficulty_entry": "Intermediate"
        },
        "Sorting": {
            "title": "Divide and Conquer Sorts",
            "topics": [
                "1. Merge Sort tree partitioning",
                "2. Quick Sort pivot selection pitfalls"
            ],
            "estimated_minutes": 15,
            "difficulty_entry": "Intermediate"
        }
    }

    concept_rec = topic_map.get(weak_concept, topic_map["Recursion"])

    return {
        "student_id": student_id,
        "student_name": profile.student_name,
        "weak_concept": weak_concept,
        "current_mastery": weak_score,
        "recommendation_title": concept_rec["title"],
        "reason": f"Your recent quiz performance shows lower accuracy in {weak_concept} ({weak_score}% mastery). Targeted practice will reinforce core concepts.",
        "topics": concept_rec["topics"],
        "estimated_minutes": concept_rec["estimated_minutes"],
        "difficulty_entry": concept_rec["difficulty_entry"]
    }
