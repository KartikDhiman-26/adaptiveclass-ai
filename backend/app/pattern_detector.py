from typing import Any, Dict, List, Optional


class PatternDetector:
    """
    Transparent, explainable educational pattern detector.
    Derives deterministic patterns strictly from calculated analytics and empirical thresholds.
    Never speculates on student motivation, personal traits, or clinical causes.
    """

    SUPPORT_THRESHOLD = 50.0
    CRITICAL_TOPIC_THRESHOLD = 40.0
    CLASS_STRUGGLE_PERCENTAGE_THRESHOLD = 30.0
    SIGNIFICANT_IMPROVEMENT_THRESHOLD = 10.0
    SIGNIFICANT_DECLINE_THRESHOLD = -10.0
    LARGE_SWING_THRESHOLD = 25.0

    @classmethod
    def detect_patterns(
        cls,
        analytics: Dict[str, Any],
        historical: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans analytics and optional historical progression to isolate actionable pedagogical patterns.
        Returns a structured list of pattern items with supporting numerical evidence.
        """
        patterns: List[Dict[str, Any]] = []

        if not analytics.get("success"):
            return patterns

        # 1. Detect Class-Level Learning Gaps & Revision Priorities
        topic_analysis = analytics.get("topic_analysis", [])
        for topic in topic_analysis:
            name = topic["name"]
            subject = topic.get("subject", "General")
            avg_pct = topic["percentage"]
            struggling_pct = topic.get("struggling_students_percentage", 0.0)
            struggling_cnt = topic.get("struggling_students_count", 0)
            assessed_cnt = topic.get("students_assessed", 0)

            # Critical Learning Gap rule
            if avg_pct < cls.CRITICAL_TOPIC_THRESHOLD or struggling_pct >= cls.CLASS_STRUGGLE_PERCENTAGE_THRESHOLD:
                patterns.append({
                    "pattern_type": "CRITICAL_LEARNING_GAP",
                    "entity_type": "topic",
                    "entity_name": name,
                    "subject": subject,
                    "priority": "high",
                    "evidence": (
                        f"Topic average is {avg_pct}%. {struggling_cnt} of {assessed_cnt} students "
                        f"({struggling_pct}%) scored below the {cls.SUPPORT_THRESHOLD}% proficiency threshold."
                    ),
                    "rule": f"Topic average < {cls.CRITICAL_TOPIC_THRESHOLD}% or struggling students >= {cls.CLASS_STRUGGLE_PERCENTAGE_THRESHOLD}%",
                    "recommended_action": f"Schedule an immediate revision session for '{name}' focusing on fundamental mechanics before introducing new topics."
                })
            elif avg_pct < cls.SUPPORT_THRESHOLD:
                patterns.append({
                    "pattern_type": "TARGETED_REVISION_PRIORITY",
                    "entity_type": "topic",
                    "entity_name": name,
                    "subject": subject,
                    "priority": "medium",
                    "evidence": f"Topic average is {avg_pct}%, falling below the {cls.SUPPORT_THRESHOLD}% support threshold.",
                    "rule": f"Topic average < {cls.SUPPORT_THRESHOLD}%",
                    "recommended_action": f"Provide supplementary worked examples and formative practice problems on '{name}'."
                })

        # 2. Detect Subject-Specific Performance Gaps
        class_overall = analytics.get("data_summary", {}).get("overall_percentage", 0.0)
        subject_analysis = analytics.get("subject_analysis", [])
        if len(subject_analysis) > 1:
            for sub in subject_analysis:
                sub_name = sub["name"]
                sub_avg = sub["percentage"]
                delta = round(class_overall - sub_avg, 2)
                if delta >= 15.0:
                    patterns.append({
                        "pattern_type": "SUBJECT_PERFORMANCE_GAP",
                        "entity_type": "subject",
                        "entity_name": sub_name,
                        "subject": sub_name,
                        "priority": "medium",
                        "evidence": f"Subject average is {sub_avg}%, which is {delta}% lower than the overall classroom average ({class_overall}%).",
                        "rule": "Subject average is 15% or more below the class overall percentage",
                        "recommended_action": f"Examine syllabus pacing and problem set difficulty alignment in '{sub_name}'."
                    })

        # 3. Detect Consistently Weak Students & Individual Support Needs
        student_analysis = analytics.get("student_analysis", [])
        for st in student_analysis:
            roll = st["rollno"]
            name = st["name"]
            avg = st["average_percentage"]
            weak_topics = st.get("weaknesses", [])
            assessments = st.get("assessments_count", 1)

            if avg < cls.SUPPORT_THRESHOLD:
                weak_topics_str = ", ".join(weak_topics) if weak_topics else "General curriculum"
                patterns.append({
                    "pattern_type": "CONSISTENTLY_WEAK_STUDENT" if assessments > 1 else "STUDENT_NEEDS_SUPPORT",
                    "entity_type": "student",
                    "entity_name": f"{name} ({roll})",
                    "subject": "All",
                    "priority": "high",
                    "evidence": f"Overall average is {avg}% across {assessments} assessment(s). Weak areas: {weak_topics_str}.",
                    "rule": f"Student average < {cls.SUPPORT_THRESHOLD}%",
                    "recommended_action": f"Assign foundational remedial exercises in {weak_topics_str} and offer guided office-hour review."
                })

        # 4. Detect Historical Patterns (Progression, Decline, Swings, Persistent Gaps)
        if historical and historical.get("has_historical_data"):
            # Persistent weak topics
            persistent = historical.get("persistent_weak_topics", [])
            for p_top in persistent:
                patterns.append({
                    "pattern_type": "REPEATEDLY_WEAK_TOPIC",
                    "entity_type": "topic",
                    "entity_name": p_top,
                    "subject": "Multiple",
                    "priority": "high",
                    "evidence": f"Topic '{p_top}' maintained an average below {cls.SUPPORT_THRESHOLD}% across consecutive assessments.",
                    "rule": "Topic average remains below threshold in consecutive assessments",
                    "recommended_action": f"Re-anchor instructional strategies for '{p_top}', using visual step-by-step traces or laboratory exercises."
                })

            # Improving students
            for imp in historical.get("improving_students", []):
                patterns.append({
                    "pattern_type": "IMPROVING_STUDENT",
                    "entity_type": "student",
                    "entity_name": f"{imp['name']} ({imp['rollno']})",
                    "subject": "General",
                    "priority": "low",
                    "evidence": f"Score progressed from {imp['past_average']}% to {imp['current_average']}% (+{imp['change']}% gain).",
                    "rule": f"Score increase >= +{cls.SIGNIFICANT_IMPROVEMENT_THRESHOLD}% between assessments",
                    "recommended_action": "Recognize improvement and provide enrichment challenge tasks."
                })

            # Declining students
            for dec in historical.get("declining_students", []):
                patterns.append({
                    "pattern_type": "DECLINING_STUDENT",
                    "entity_type": "student",
                    "entity_name": f"{dec['name']} ({dec['rollno']})",
                    "subject": "General",
                    "priority": "high",
                    "evidence": f"Score dropped from {dec['past_average']}% to {dec['current_average']}% ({dec['change']}% decline).",
                    "rule": f"Score decrease <= {cls.SIGNIFICANT_DECLINE_THRESHOLD}% between assessments",
                    "recommended_action": "Check recent assessment topic comprehension and review foundational concepts."
                })

            # Unusual swings (> 25% change)
            for prog in historical.get("student_progressions", []):
                abs_change = abs(prog["change"])
                if abs_change >= cls.LARGE_SWING_THRESHOLD:
                    patterns.append({
                        "pattern_type": "UNUSUAL_PERFORMANCE_CHANGE",
                        "entity_type": "student",
                        "entity_name": f"{prog['name']} ({prog['rollno']})",
                        "subject": "General",
                        "priority": "medium",
                        "evidence": f"Large performance swing of {prog['change']}% ({prog['past_average']}% -> {prog['current_average']}%).",
                        "rule": f"Absolute score swing >= {cls.LARGE_SWING_THRESHOLD}%",
                        "recommended_action": "Investigate whether the swing stems from topic-specific variance or assessment format differences."
                    })

        return patterns
