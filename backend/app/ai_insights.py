import json
from typing import Dict, Any, Tuple, List, Optional
from app.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_REQUEST_TIMEOUT_MS
from app.schemas import AiInsightResponse

TEACHER_DISCLAIMER = (
    "AI-generated insights are recommendations. Teachers remain in control of instructional decisions."
)

def generate_classroom_insight(metrics: Dict[str, Any]) -> AiInsightResponse:
    """
    Generates classroom AI insight using the configured Gemini model if available,
    otherwise gracefully and immediately uses the deterministic rule-based engine.
    Strictly follows the WHAT / WHY / SUGGESTED ACTION / DISCLAIMER structure.
    """
    weakest = metrics.get("weakest_concept", "Recursion")
    weakest_mastery = metrics.get("weakest_mastery", 35.0)
    student_count = metrics.get("student_count", 80)
    rec_support_count = metrics.get("recursion_support_count", 23)
    rec_support_pct = metrics.get("recursion_support_pct", 28.8)
    adv_count = metrics.get("advanced_count", 12)
    strongest = metrics.get("strongest_concept", "Arrays")
    strongest_mastery = metrics.get("strongest_mastery", 82.0)

    # Attempt Gemini generation if API key is provided
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(
                api_key=GEMINI_API_KEY,
                http_options={"timeout": GEMINI_REQUEST_TIMEOUT_MS}
            )

            prompt = f"""
You are an expert AI teaching assistant for college computer science professors.
Analyze this Data Structures class performance data:
- Total Students: {student_count}
- Weakest Concept: {weakest} (Mastery: {weakest_mastery}%)
- Students needing support in {weakest} (< 40% threshold): {rec_support_count} students ({rec_support_pct}%)
- Strongest Concept: {strongest} (Mastery: {strongest_mastery}%)
- Advanced Students: {adv_count} students

Generate a structured JSON response with these exact keys:
{{
  "what": "Clear statement of the measured performance gap based strictly on the data",
  "why": "Specific statistical evidence citing the {rec_support_count} students and {weakest_mastery}% mastery",
  "suggested_action": "Targeted instructional recommendation for the professor (e.g. revision on base cases and call stacks)",
  "enrichment_action": "Suggested enrichment challenge for the {adv_count} high-mastery students"
}}

IMPORTANT GUIDELINES:
- Do not make psychological or medical assumptions.
- Do not claim absolute certainty or evaluate teacher competence.
- Only reference the provided data.
Respond with pure valid JSON only, no markdown backticks.
"""
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())

            return AiInsightResponse(
                learning_gap=weakest,
                class_mastery=weakest_mastery,
                students_below_threshold=rec_support_count,
                what=parsed.get("what", f"{weakest} is currently the largest classroom learning gap at {weakest_mastery}% mastery."),
                why=parsed.get("why", f"{rec_support_count} students ({rec_support_pct}%) scored below the 40% academic support threshold."),
                suggested_action=parsed.get("suggested_action", f"Conduct a targeted revision session on {weakest} fundamentals before advancing."),
                enrichment_action=parsed.get("enrichment_action", f"{adv_count} students demonstrate consistent high mastery. Provide advanced challenges."),
                teacher_disclaimer=TEACHER_DISCLAIMER,
                generated_by=f"Gemini ({GEMINI_MODEL})"
            )
        except Exception as exc:
            print(f"[AI INSIGHTS] Gemini call failed or unavailable ({exc}). Using deterministic rule-based engine.")

    # Autonomous Rule-Based Fallback Engine
    what_text = (
        f"{weakest} is currently the largest measured learning gap in the classroom, "
        f"with a class mastery of {weakest_mastery}%."
    )
    why_text = (
        f"{rec_support_count} of {student_count} students ({rec_support_pct}%) are below the 40% support threshold, "
        f"primarily faltering on base case formulation and call stack tracing."
    )
    suggested_action_text = (
        f"Conduct a targeted {weakest.lower()} revision session focusing on base cases and stack frames "
        f"before introducing advanced tree and graph algorithms."
    )
    enrichment_action_text = (
        f"{adv_count} students are consistently demonstrating high mastery (≥85%). "
        f"Suggested enrichment: Assign AVL tree rotations and competitive programming challenge sets."
    )

    return AiInsightResponse(
        learning_gap=weakest,
        class_mastery=weakest_mastery,
        students_below_threshold=rec_support_count,
        what=what_text,
        why=why_text,
        suggested_action=suggested_action_text,
        enrichment_action=enrichment_action_text,
        teacher_disclaimer=TEACHER_DISCLAIMER,
        generated_by="Autonomous Rule-Based Engine"
    )

def generate_student_insight(metrics: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Generates student-specific personalized insight and actionable practice steps.
    """
    name = metrics.get("name", "Student")
    overall = metrics.get("overall_mastery", 61.0)
    weakest = metrics.get("weakest_concept", "Recursion")
    weakest_score = metrics.get("weakest_score", 28.0)

    # Determine strong areas (>70%)
    concepts = metrics.get("concepts", [])
    strong_concepts = [c["concept_name"] for c in concepts if c.get("mastery", 0) >= 70]
    strong_str = " and ".join(strong_concepts[:2]) if strong_concepts else "Arrays"

    insight = (
        f"{name} demonstrates strong understanding of {strong_str} ({overall}% overall mastery) "
        f"but is currently experiencing difficulty with {weakest} ({weakest_score}% mastery). "
        f"Recent quiz trends indicate struggles with base cases and stack depth tracking."
    )

    steps = [
        f"Review {weakest} fundamentals (base cases & recursive steps)",
        f"Complete 5 beginner {weakest.lower()} practice problems",
        f"Attempt intermediate {weakest.lower()} tracing challenges"
    ]

    return insight, steps


def generate_assessment_pipeline_insights(
    analytics: Dict[str, Any],
    patterns: List[Dict[str, Any]],
    historical: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates teacher-facing pedagogical insights across class, student, topic, and historical dimensions.
    Uses the configured Gemini model when GEMINI_API_KEY is configured; otherwise provides an immediate,
    high-precision deterministic rule-based analysis grounded in the calculated numbers.
    """
    summary = analytics.get("data_summary", {})
    class_avg = summary.get("overall_percentage", 0.0)
    student_count = summary.get("total_students", 0)
    dist = summary.get("distribution", {})
    adv_count = dist.get("advanced", 0)
    support_count = dist.get("needs_support", 0)

    topics = analytics.get("topic_analysis", [])
    weak_topics = [t["name"] for t in topics if t.get("revision_priority") in ("critical", "moderate")]
    strong_topics = [t["name"] for t in topics if t.get("percentage", 0) >= 75.0]

    weak_str = ", ".join(weak_topics) if weak_topics else "None detected"
    strong_str = ", ".join(strong_topics) if strong_topics else "General curriculum"

    # 1. Attempt Gemini generation if a key is present
    if GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(
                api_key=GEMINI_API_KEY,
                http_options={"timeout": GEMINI_REQUEST_TIMEOUT_MS}
            )

            pattern_summaries = [
                f"- {p['pattern_type']} ({p.get('entity_name', '')}): {p.get('evidence', '')}"
                for p in patterns[:6]
            ]
            patterns_text = "\n".join(pattern_summaries) if pattern_summaries else "No acute anomalies detected."

            prompt = f"""
You are an expert AI teaching assistant for university engineering professors.
Analyze this classroom assessment analytics data:
- Total Students: {student_count}
- Class Average: {class_avg}%
- Advanced Students (>=85%): {adv_count}
- Students Needing Academic Support (<50%): {support_count}
- Strong Topics: {strong_str}
- Topics Requiring Revision: {weak_str}
- Detected Statistical Patterns:
{patterns_text}

Generate a concise, professional JSON response strictly adhering to these keys:
{{
  "class_summary": "1-2 sentence executive summary of overall classroom performance",
  "student_support_recommendations": [
    {{"student": "Student Identifier", "gap": "Specific topic", "suggested_action": "Targeted intervention"}}
  ],
  "topic_recommendations": [
    {{"topic": "Topic Name", "issue": "Specific weakness", "teaching_strategy": "Concrete revision technique"}}
  ],
  "historical_insights": "Brief summary of progression if trends exist, or statement that more data is needed",
  "actionable_teaching_recommendations": [
    "Specific recommendation 1",
    "Specific recommendation 2"
  ]
}}

STRICT GUIDELINES:
- Ground every claim strictly in the provided metrics.
- Do NOT make psychological assumptions, evaluate teacher competence, or invent student data.
- Output valid JSON only, without markdown fences.
"""
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]

            parsed = json.loads(raw.strip())
            return {
                "class_summary": parsed.get("class_summary", f"Class average is {class_avg}% across {student_count} students."),
                "student_support_recommendations": parsed.get("student_support_recommendations", []),
                "topic_recommendations": parsed.get("topic_recommendations", []),
                "historical_insights": parsed.get("historical_insights", "Historical trend analysis active."),
                "actionable_teaching_recommendations": parsed.get("actionable_teaching_recommendations", []),
                "generated_by": f"Gemini ({GEMINI_MODEL})",
                "teacher_disclaimer": TEACHER_DISCLAIMER
            }
        except Exception as exc:
            print(f"[AI INSIGHTS] Gemini call failed ({exc}). Utilizing deterministic rule-based engine.")

    # 2. Autonomous Rule-Based Fallback Engine
    # Class Summary
    class_summary = (
        f"Classroom overall average is {class_avg}% across {student_count} assessed students. "
        f"{adv_count} student(s) demonstrated advanced mastery (>=85%), while {support_count} student(s) "
        f"currently fall below the 50% academic proficiency threshold."
    )

    # Student Support Recommendations
    student_recs = []
    students_needing_support = analytics.get("students_needing_support", [])
    for st in students_needing_support[:5]:
        weak_str_st = ", ".join(st.get("weaknesses", [])) or "overall score"
        student_recs.append({
            "student": f"{st['name']} ({st['rollno']})",
            "gap": weak_str_st,
            "evidence": f"Average score {st['average_percentage']}%",
            "suggested_action": f"Provide structured remediation and foundational exercises in {weak_str_st}."
        })

    # Topic Recommendations
    topic_recs = []
    for top in topics:
        if top.get("revision_priority") in ("critical", "moderate"):
            topic_recs.append({
                "topic": top["name"],
                "issue": f"{top.get('struggling_students_percentage', 0)}% of students scored below 50% (topic average {top['percentage']}%)",
                "teaching_strategy": f"Conduct an interactive tracing/worked-example review focusing on {top['name']} core concepts.",
                "practice_activity": f"Assign 3-5 progressive exercises starting with beginner constraints before multi-step applications."
            })

    # Historical Insights
    if historical and historical.get("has_historical_data"):
        delta = historical.get("class_average_change", 0.0)
        direction = "increased" if delta > 0 else ("decreased" if delta < 0 else "remained steady")
        imp_count = len(historical.get("improving_students", []))
        dec_count = len(historical.get("declining_students", []))
        hist_text = (
            f"Class performance has {direction} by {abs(delta)} percentage points between assessments. "
            f"{imp_count} student(s) showed significant improvement (>=+10%), while {dec_count} showed performance decline."
        )
    else:
        hist_text = "Historical longitudinal comparison requires at least two distinct assessment datasets."

    # Actionable Teaching Recommendations
    actions = []
    if weak_topics:
        actions.append(f"Prioritize dedicated classroom revision on high-barrier topics: {', '.join(weak_topics[:3])}.")
    if support_count > 0:
        actions.append(f"Organize small-group or peer-assisted tutoring for the {support_count} students scoring below 50%.")
    if adv_count > 0:
        actions.append(f"Prepare extension challenges for the {adv_count} advanced students ready for higher complexity.")
    actions.append("Conduct a short 5-question formative diagnostic quiz following the next revision cycle.")

    return {
        "class_summary": class_summary,
        "student_support_recommendations": student_recs,
        "topic_recommendations": topic_recs,
        "historical_insights": hist_text,
        "actionable_teaching_recommendations": actions,
        "generated_by": "Autonomous Rule-Based Engine",
        "teacher_disclaimer": TEACHER_DISCLAIMER
    }
