from typing import Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import (
    Class, Student, Concept, ConceptPerformance, QuizAttempt, QuizAttemptAnswer, Question
)
from app.schemas import (
    ClassAnalyticsResponse, ConceptMasteryItem, StudentStatusDistribution,
    StudentNeedingAttentionItem, StudentProfileResponse, StudentConceptScore,
    RecentQuizItem, QuizSubmitResponse, AiInsightResponse
)
from app.ai_insights import generate_classroom_insight, generate_student_insight

def get_concept_status(mastery: float) -> tuple[str, str]:
    """Returns (status_label, status_color) based on mastery score."""
    if mastery >= 75.0:
        return ("Strong", "green")
    elif mastery >= 60.0:
        return ("Moderate", "blue")
    elif mastery >= 40.0:
        return ("Needs Attention", "amber")
    else:
        return ("Critical Gap", "red")

def get_student_status_label(overall_mastery: float) -> str:
    if overall_mastery >= 85.0:
        return "Advanced"
    elif overall_mastery >= 55.0:
        return "On Track"
    elif overall_mastery >= 40.0:
        return "Needs Support"
    else:
        return "Needs Attention"

def get_class_analytics(class_id: int, db: Session) -> ClassAnalyticsResponse:
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class:
        raise ValueError(f"Class with id {class_id} not found")

    student_count = db.query(Student).filter(Student.class_id == class_id).count()

    # Query concept averages (prioritize concepts belonging to this class's performances)
    concepts = db.query(Concept).join(ConceptPerformance, ConceptPerformance.concept_id == Concept.id)\
        .join(Student, Student.id == ConceptPerformance.student_id)\
        .filter(Student.class_id == class_id).distinct().order_by(Concept.order_index.asc()).all()
    if not concepts and target_class.subject:
        concepts = db.query(Concept).filter(Concept.subject == target_class.subject).order_by(Concept.order_index.asc()).all()
    if not concepts:
        concepts = []
    concept_items: List[ConceptMasteryItem] = []
    
    total_class_mastery_sum = 0.0
    weakest_concept_name = ""
    weakest_concept_score = 999.0
    weakest_concept_id = None
    strongest_concept_name = ""
    strongest_concept_score = -1.0

    recursion_concept_id = None
    recursion_avg = 35.0

    for concept in concepts:
        avg_score = db.query(func.avg(ConceptPerformance.mastery_score))\
            .join(Student, ConceptPerformance.student_id == Student.id)\
            .filter(Student.class_id == class_id, ConceptPerformance.concept_id == concept.id)\
            .scalar() or 0.0

        rounded_avg = round(float(avg_score), 1)
        total_class_mastery_sum += rounded_avg

        if concept.name == "Recursion":
            recursion_concept_id = concept.id
            recursion_avg = rounded_avg

        if rounded_avg < weakest_concept_score:
            weakest_concept_score = rounded_avg
            weakest_concept_name = concept.name
            weakest_concept_id = concept.id

        if rounded_avg > strongest_concept_score:
            strongest_concept_score = rounded_avg
            strongest_concept_name = concept.name

        label, color = get_concept_status(rounded_avg)
        concept_items.append(ConceptMasteryItem(
            concept_id=concept.id,
            concept_name=concept.name,
            mastery_percentage=rounded_avg,
            status_label=label,
            status_color=color
        ))

    if weakest_concept_score == 999.0:
        weakest_concept_score = 0.0
    if strongest_concept_score == -1.0:
        strongest_concept_score = 0.0

    overall_class_average = round(total_class_mastery_sum / max(len(concepts), 1), 1) if concepts else 0.0

    # Calculate support count (< 40.0%) for the critical bottleneck of this class
    target_gap_id = recursion_concept_id if recursion_concept_id else weakest_concept_id
    recursion_support_count = 0
    if target_gap_id:
        recursion_support_count = db.query(ConceptPerformance)\
            .join(Student, ConceptPerformance.student_id == Student.id)\
            .filter(
                Student.class_id == class_id,
                ConceptPerformance.concept_id == target_gap_id,
                ConceptPerformance.mastery_score < 40.0
            ).count()
    elif not target_gap_id and weakest_concept_name:
        weakest_c = db.query(Concept).filter(Concept.name == weakest_concept_name).first()
        if weakest_c:
            recursion_support_count = db.query(ConceptPerformance)\
                .join(Student, ConceptPerformance.student_id == Student.id)\
                .filter(
                    Student.class_id == class_id,
                    ConceptPerformance.concept_id == weakest_c.id,
                    ConceptPerformance.mastery_score < 40.0
                ).count()

    # Calculate Global Student Distribution across all concepts
    students = db.query(Student).filter(Student.class_id == class_id).all()
    adv_count = 0
    on_track_count = 0
    needs_support_count = 0
    needs_attention_count = 0

    for s in students:
        overall = db.query(func.avg(ConceptPerformance.mastery_score))\
            .filter(ConceptPerformance.student_id == s.id)\
            .scalar() or 0.0
        overall_val = float(overall)
        if overall_val >= 85.0:
            adv_count += 1
        elif overall_val >= 55.0:
            on_track_count += 1
        elif overall_val >= 40.0:
            needs_support_count += 1
        else:
            needs_attention_count += 1

    distribution = StudentStatusDistribution(
        advanced=adv_count,
        on_track=on_track_count,
        needs_support=needs_support_count,
        needs_attention=needs_attention_count,
        total=student_count
    )

    # Generate AI / Autonomous Insight
    raw_metrics = {
        "class_name": target_class.name,
        "subject": target_class.subject,
        "student_count": student_count,
        "overall_average": overall_class_average,
        "weakest_concept": weakest_concept_name,
        "weakest_mastery": weakest_concept_score,
        "strongest_concept": strongest_concept_name,
        "strongest_mastery": strongest_concept_score,
        "recursion_support_count": recursion_support_count,
        "recursion_support_pct": round((recursion_support_count / max(student_count, 1)) * 100.0, 1),
        "advanced_count": adv_count,
        "concept_items": [c.model_dump() for c in concept_items]
    }
    insight = generate_classroom_insight(raw_metrics)

    return ClassAnalyticsResponse(
        class_id=target_class.id,
        class_name=target_class.name,
        subject=target_class.subject,
        semester=target_class.semester,
        student_count=student_count,
        overall_class_average=overall_class_average,
        concept_mastery=concept_items,
        weakest_concept=weakest_concept_name,
        strongest_concept=strongest_concept_name,
        recursion_support_count=recursion_support_count,
        recursion_support_threshold=40.0,
        global_distribution=distribution,
        ai_insight=insight
    )

def get_students_needing_attention(class_id: int, db: Session) -> List[StudentNeedingAttentionItem]:
    """
    Returns students with acute concept gaps (< 40%), prioritizing prominent demo students.
    """
    students = db.query(Student).filter(Student.class_id == class_id).all()
    attention_list = []

    action_map = {
        "Recursion": "Beginner practice on base cases",
        "Trees": "Concept revision on BST invariants",
        "Linked Lists": "Pointer manipulation practice",
        "Graphs": "BFS traversal tracing",
        "Arrays": "Array boundary revision",
        "Sorting": "Divide & conquer review"
    }

    for s in students:
        # Find lowest concept performance
        lowest_perf = db.query(ConceptPerformance)\
            .join(Concept)\
            .filter(ConceptPerformance.student_id == s.id)\
            .order_by(ConceptPerformance.mastery_score.asc())\
            .first()

        if lowest_perf and lowest_perf.mastery_score < 40.0:
            c_name = lowest_perf.concept.name
            action = action_map.get(c_name, "Targeted practice")
            attention_list.append(StudentNeedingAttentionItem(
                student_id=s.id,
                student_name=s.name,
                roll_number=s.roll_number,
                email=s.email,
                weak_concept=c_name,
                mastery=round(lowest_perf.mastery_score, 1),
                recommended_action=action
            ))

    # Sort so Aarav Sharma, Ananya, Rahul, Priya appear at top for demo clarity
    priority_emails = ["student@demo.com", "rahul@demo.com", "ananya@demo.com", "priyan@demo.com"]
    attention_list.sort(key=lambda x: (0 if x.email in priority_emails else 1, x.mastery))
    return attention_list

def get_student_profile(student_id: int, db: Session) -> StudentProfileResponse:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student with id {student_id} not found")

    performances = db.query(ConceptPerformance)\
        .join(Concept)\
        .filter(ConceptPerformance.student_id == student_id)\
        .order_by(Concept.order_index.asc())\
        .all()

    concept_scores: List[StudentConceptScore] = []
    total_score = 0.0
    weakest_c_name = ""
    weakest_c_score = 999.0

    for p in performances:
        m = round(p.mastery_score, 1)
        total_score += m
        label, color = get_concept_status(m)
        if m < weakest_c_score:
            weakest_c_score = m
            weakest_c_name = p.concept.name

        concept_scores.append(StudentConceptScore(
            concept_id=p.concept_id,
            concept_name=p.concept.name,
            mastery=m,
            status_label=label,
            status_color=color
        ))

    overall_mastery = round(total_score / max(len(performances), 1), 1)
    status_label = get_student_status_label(overall_mastery)

    # Recent quizzes
    quizzes = db.query(QuizAttempt)\
        .filter(QuizAttempt.student_id == student_id)\
        .order_by(QuizAttempt.timestamp.desc())\
        .limit(5)\
        .all()

    recent_quiz_items: List[RecentQuizItem] = []
    for q in quizzes:
        recent_quiz_items.append(RecentQuizItem(
            quiz_id=q.id,
            quiz_title=q.quiz_title,
            score=q.score,
            total_questions=q.total_questions,
            accuracy=round(q.accuracy, 1),
            timestamp=q.timestamp.strftime("%b %d, %Y")
        ))

    # Generate student AI insight
    safe_weakest = weakest_c_name or "General Fundamentals"
    safe_score = weakest_c_score if weakest_c_score != 999.0 else 0.0

    student_metric = {
        "name": student.name,
        "overall_mastery": overall_mastery,
        "weakest_concept": safe_weakest,
        "weakest_score": safe_score,
        "concepts": [c.model_dump() for c in concept_scores]
    }
    ai_insight_text, suggested_steps = generate_student_insight(student_metric)

    return StudentProfileResponse(
        student_id=student.id,
        student_name=student.name,
        roll_number=student.roll_number,
        email=student.email,
        overall_mastery=overall_mastery,
        status_label=status_label,
        concept_performance=concept_scores,
        current_learning_gap=safe_weakest,
        recent_performance=recent_quiz_items,
        ai_insight=ai_insight_text,
        suggested_steps=suggested_steps
    )

def record_quiz_and_update_mastery(
    student_id: int,
    concept_id: int,
    quiz_title: str,
    answers: List[Dict[str, Any]],
    db: Session
) -> QuizSubmitResponse:
    """
    Calculates student's new mastery score from actual quiz performance using the formula:
      New_Mastery = round(Old_Mastery * 0.35 + Quiz_Accuracy * 0.65, 1)
    Persists results to PostgreSQL, recomputes class averages and support count, and returns before/after comparisons.
    """
    total_q = len(answers)
    score = sum(1 for a in answers if a.get("is_correct", False))
    accuracy = round((score / max(total_q, 1)) * 100.0, 1)

    # 1. Create QuizAttempt
    attempt = QuizAttempt(
        student_id=student_id,
        concept_id=concept_id,
        quiz_title=quiz_title,
        score=score,
        total_questions=total_q,
        accuracy=accuracy
    )
    db.add(attempt)
    db.flush()

    # 2. Add QuizAttemptAnswers
    for ans in answers:
        db.add(QuizAttemptAnswer(
            quiz_attempt_id=attempt.id,
            question_id=ans["question_id"],
            selected_answer=ans["selected_answer"],
            is_correct=ans.get("is_correct", False)
        ))

    # 3. Fetch ConceptPerformance record
    perf = db.query(ConceptPerformance)\
        .filter(ConceptPerformance.student_id == student_id, ConceptPerformance.concept_id == concept_id)\
        .first()

    concept_obj = db.query(Concept).filter(Concept.id == concept_id).first()
    concept_name = concept_obj.name if concept_obj else "Recursion"

    old_mastery = perf.mastery_score if perf else 28.0

    # Apply data-driven mastery formula:
    # New_Mastery = round(Old_Mastery * 0.35 + Quiz_Accuracy * 0.65, 1)
    new_mastery = round(old_mastery * 0.35 + accuracy * 0.65, 1)
    mastery_change = round(new_mastery - old_mastery, 1)

    if perf:
        perf.mastery_score = new_mastery
        perf.attempt_count += 1
        perf.correct_count += score
    else:
        perf = ConceptPerformance(
            student_id=student_id,
            concept_id=concept_id,
            mastery_score=new_mastery,
            attempt_count=1,
            correct_count=score
        )
        db.add(perf)

    db.commit()

    # 4. Recompute Class Averages and Support Count directly from PostgreSQL
    student = db.query(Student).filter(Student.id == student_id).first()
    class_id = student.class_id if student else 1

    # Check for this concept's class average and support count
    target_concept_id = concept_id
    avg_query = db.query(func.avg(ConceptPerformance.mastery_score))\
        .join(Student, ConceptPerformance.student_id == Student.id)\
        .filter(Student.class_id == class_id, ConceptPerformance.concept_id == target_concept_id)\
        .scalar()
    new_concept_avg = round(float(avg_query), 1) if avg_query is not None else new_mastery

    support_count_query = db.query(ConceptPerformance)\
        .join(Student, ConceptPerformance.student_id == Student.id)\
        .filter(
            Student.class_id == class_id,
            ConceptPerformance.concept_id == target_concept_id,
            ConceptPerformance.mastery_score < 40.0
        ).count()

    sign = "+" if mastery_change >= 0 else ""
    impact_msg = (
        f"Mastery in {concept_name} updated from {old_mastery}% to {new_mastery}% ({sign}{mastery_change}%). "
        f"Classroom average for {concept_name} is now {new_concept_avg}%, with {support_count_query} student(s) needing support."
    )

    return QuizSubmitResponse(
        quiz_attempt_id=attempt.id,
        score=score,
        total_questions=total_q,
        accuracy=accuracy,
        old_mastery=old_mastery,
        new_mastery=new_mastery,
        mastery_change=mastery_change,
        concept_name=concept_name,
        new_class_recursion_average=new_concept_avg,
        new_recursion_support_count=support_count_query,
        impact_message=impact_msg
    )
