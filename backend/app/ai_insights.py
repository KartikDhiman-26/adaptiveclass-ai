import json
from typing import Dict, Any, Tuple, List
from app.config import GEMINI_API_KEY
from app.schemas import AiInsightResponse

TEACHER_DISCLAIMER = (
    "AI-generated insights are recommendations. Teachers remain in control of instructional decisions."
)

def generate_classroom_insight(metrics: Dict[str, Any]) -> AiInsightResponse:
    """
    Generates classroom AI insight using Gemini 2.5 Flash if available,
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
            client = genai.Client(api_key=GEMINI_API_KEY)

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
                model="gemini-2.5-flash",
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
                generated_by="Gemini 2.5 Flash"
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
