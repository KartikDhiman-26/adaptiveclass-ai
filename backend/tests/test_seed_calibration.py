import pytest
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Student, Concept, Question, ConceptPerformance, QuizAttempt

def test_postgresql_seed_mathematical_calibration():
    db = SessionLocal()
    try:
        # 1. Verify student count
        total_students = db.query(Student).count()
        assert total_students == 80, f"Expected 80 students, found {total_students}"

        # 2. Verify concept count
        total_concepts = db.query(Concept).count()
        assert total_concepts == 6, f"Expected 6 concepts, found {total_concepts}"

        # 3. Verify question count
        total_questions = db.query(Question).count()
        assert total_questions == 30, f"Expected 30 questions, found {total_questions}"

        # 4. Verify Concept Averages
        target_averages = {
            "Arrays": 82.0,
            "Linked Lists": 64.0,
            "Trees": 41.0,
            "Recursion": 35.0,
            "Graphs": 58.0,
            "Sorting": 75.0,
        }

        concepts = db.query(Concept).all()
        for concept in concepts:
            avg_score = db.query(func.avg(ConceptPerformance.mastery_score))\
                .filter(ConceptPerformance.concept_id == concept.id)\
                .scalar()
            expected_avg = target_averages[concept.name]
            assert abs(avg_score - expected_avg) < 0.1, (
                f"Concept '{concept.name}' average mismatch: got {avg_score:.2f}%, expected {expected_avg}%"
            )

        # 5. Verify Recursion Support Count (EXACTLY 23 students below 40%)
        rec_concept = db.query(Concept).filter(Concept.name == "Recursion").first()
        rec_below_40_count = db.query(ConceptPerformance)\
            .filter(ConceptPerformance.concept_id == rec_concept.id, ConceptPerformance.mastery_score < 40.0)\
            .count()
        assert rec_below_40_count == 23, (
            f"Expected exactly 23 students with Recursion < 40%, found {rec_below_40_count}"
        )

        # 6. Verify Global Distribution (Across all 80 students)
        # Thresholds: Advanced >= 85, On Track: 55 - 84, Needs Support: 40 - 54, Needs Attention: < 40
        students = db.query(Student).all()
        tiers = {"Advanced": 0, "On Track": 0, "Needs Support": 0, "Needs Attention": 0}
        for s in students:
            overall = db.query(func.avg(ConceptPerformance.mastery_score))\
                .filter(ConceptPerformance.student_id == s.id)\
                .scalar()
            if overall >= 85.0:
                tiers["Advanced"] += 1
            elif overall >= 55.0:
                tiers["On Track"] += 1
            elif overall >= 40.0:
                tiers["Needs Support"] += 1
            else:
                tiers["Needs Attention"] += 1

        assert tiers["Advanced"] == 12, f"Advanced tier count mismatch: {tiers['Advanced']}"
        assert tiers["On Track"] == 45, f"On Track tier count mismatch: {tiers['On Track']}"
        assert tiers["Needs Support"] == 18, f"Needs Support tier count mismatch: {tiers['Needs Support']}"
        assert tiers["Needs Attention"] == 5, f"Needs Attention tier count mismatch: {tiers['Needs Attention']}"

        # 7. Verify Aarav Sharma (student@demo.com)
        aarav = db.query(Student).filter(Student.email == "student@demo.com").first()
        assert aarav is not None
        assert aarav.name == "Aarav Sharma"
        aarav_rec = db.query(ConceptPerformance)\
            .filter(ConceptPerformance.student_id == aarav.id, ConceptPerformance.concept_id == rec_concept.id)\
            .first()
        assert aarav_rec.mastery_score == 28.0, f"Aarav Recursion expected 28.0%, got {aarav_rec.mastery_score}%"

        aarav_arr = db.query(ConceptPerformance)\
            .join(Concept)\
            .filter(ConceptPerformance.student_id == aarav.id, Concept.name == "Arrays")\
            .first()
        assert aarav_arr.mastery_score == 91.0, f"Aarav Arrays expected 91.0%, got {aarav_arr.mastery_score}%"

        # Verify Aarav's recent quizzes
        quizzes = db.query(QuizAttempt).filter(QuizAttempt.student_id == aarav.id).order_by(QuizAttempt.timestamp.asc()).all()
        assert len(quizzes) == 3
        assert quizzes[0].accuracy == 72.0
        assert quizzes[1].accuracy == 64.0
        assert quizzes[2].accuracy == 48.0

        print("\n[TEST PASSED] All PostgreSQL database calibration assertions verified 100%!")
    finally:
        db.close()
