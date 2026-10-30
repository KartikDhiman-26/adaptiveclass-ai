from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.seed_data import seed_database

router = APIRouter(prefix="/api/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    Resets the database to the initial calibrated state:
      - Aarav Sharma's Recursion mastery resets to 28.0%
      - Class Recursion average resets to 35.0%
      - Exactly 23 students below 40% threshold in Recursion
      - Clears new quiz attempts
    Allows judges and evaluators to repeat the live cycle at any time.
    """
    seed_database(db, force=True)
    return {
        "status": "success",
        "message": "Demo data successfully restored to original calibrated state.",
        "metrics": {
            "students": 80,
            "class_average": 59.2,
            "recursion_average": 35.0,
            "recursion_support_count": 23,
            "aarav_recursion_mastery": 28.0
        }
    }
