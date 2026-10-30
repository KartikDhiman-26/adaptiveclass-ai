"""
Lightweight text-based emotion cue detector for adaptive teaching.

ETHICAL SAFEGUARD & PEDAGOGICAL BOUNDARY:
This detector is strictly a conversational heuristic to help the AI tutor calibrate
its pedagogical tone and explanation granularity.
It is NOT a psychological, psychiatric, or medical diagnostic tool.
It treats conversational cues as uncertain text-based signals.
Sensitive emotional labels are NEVER persisted to the student's permanent profile.
"""

import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

ETHICAL_DISCLAIMER = (
    "Pedagogical Notice: Conversational cues are uncertain text signals used solely "
    "for real-time teaching adaptation (tone & pacing). They do not represent psychological "
    "evaluations and are never saved to permanent student records."
)

class EmotionCue(str, Enum):
    CONFUSION = "CONFUSION"
    FRUSTRATION = "FRUSTRATION"
    NERVOUSNESS = "NERVOUSNESS"
    CONFIDENCE = "CONFIDENCE"
    ENGAGEMENT = "ENGAGEMENT"
    NEUTRAL = "NEUTRAL"

class EmotionCueResult(BaseModel):
    detected_cue: EmotionCue
    confidence: float  # 0.0 to 1.0
    trigger_phrases: List[str]
    adaptation_strategy: str
    suggested_tone: str
    ethical_disclaimer: str = ETHICAL_DISCLAIMER

# Pattern definitions for conversational cues
CONFUSION_PATTERNS = [
    r"\b(i\s+don'?t\s+understand|don'?t\s+get\s+it|not\s+getting\s+this|confus(ed|ing)|lost|huh|what\s+do\s+you\s+mean|can\s+you\s+re-?explain|doesn'?t\s+make\s+sense|makes?\s+no\s+sense|unclear|what\s+is\s+happening|having\s+trouble\s+understanding)\b",
    r"\b(explain\s+again|explain\s+differently|i'?m\s+mixed\s+up|wait\s+what)\b"
]

FRUSTRATION_PATTERNS = [
    r"\b(this\s+is\s+too\s+hard|i\s+give\s+up|hate\s+this|so\s+annoy(ing|ed)|stuck\s+for\s+hours|doesn'?t\s+work\s+at\s+all|ugh|argh|impossible|so\s+frustrat(ing|ed)|waste\s+of\s+time|tired\s+of\s+this)\b",
    r"\b(why\s+won'?t\s+this\s+work|never\s+gonna\s+get\s+this|never\s+going\s+to\s+understand)\b"
]

NERVOUSNESS_PATTERNS = [
    r"\b(worried(\s+\w+){0,3}\s+exam|scared(\s+\w+){0,2}\s+fail|afraid(\s+of)?|am\s+i\s+dumb|not\s+smart\s+enough|fear|anxious|nervous|stress(ed)?|what\s+if\s+i\s+mess\s+up|imposter)\b",
    r"\b(bad\s+at\s+coding|can\s+never\s+do\s+dsa|panic|hopeless|worried)\b"
]

CONFIDENCE_PATTERNS = [
    r"\b(that\s+was\s+easy|i\s+get\s+it\s+now|got\s+it\s+completely|understood|piece\s+of\s+cake|solved\s+it|makes\s+total\s+sense|super\s+clear|crystal\s+clear)\b",
    r"\b(bring\s+on\s+the\s+next|give\s+me\s+harder|ready\s+for\s+advanced|easy\s+peasy)\b"
]

ENGAGEMENT_PATTERNS = [
    r"\b(fascinating|tell\s+me\s+more|what\s+if\s+we|curious\s+about|how\s+does\s+that\s+relate\s+to|interesting|love\s+this|can\s+we\s+try|deep\s+dive|cool)\b",
    r"\b(wondering\s+how|would\s+it\s+be\s+faster\s+if|could\s+we\s+optimize)\b"
]

# Negation prefixes to avoid false matches (e.g. "I am not confused at all")
NEGATION_PREFIXES = r"\b(not|never|no\s+longer|isn'?t|aren'?t|wasn'?t|don'?t\s+feel)\s+"

def detect_conversational_cue(text: str) -> EmotionCueResult:
    """
    Analyzes student message text for conversational teaching cues.
    Returns detected cue, confidence score, and pedagogical strategy.
    """
    if not text or not text.strip():
        return _build_neutral_result()

    lower_text = text.lower().strip()

    # Check for direct negations of confusion (e.g., "I'm not confused")
    if re.search(NEGATION_PREFIXES + r"(confused|lost|having\s+trouble)", lower_text):
        # Student explicitly states they are not confused
        pass
    else:
        # Check Frustration first (high pedagogical priority to de-escalate)
        frustration_matches = _find_matches(FRUSTRATION_PATTERNS, lower_text)
        if frustration_matches:
            return EmotionCueResult(
                detected_cue=EmotionCue.FRUSTRATION,
                confidence=min(0.6 + 0.15 * len(frustration_matches), 0.95),
                trigger_phrases=frustration_matches,
                adaptation_strategy="Respond with deep patience, validate the difficulty, and break into a single tiny step.",
                suggested_tone="Calm, patient, empathetic, step-by-step"
            )

        # Check Nervousness
        nervous_matches = _find_matches(NERVOUSNESS_PATTERNS, lower_text)
        if nervous_matches:
            return EmotionCueResult(
                detected_cue=EmotionCue.NERVOUSNESS,
                confidence=min(0.6 + 0.15 * len(nervous_matches), 0.95),
                trigger_phrases=nervous_matches,
                adaptation_strategy="Use a warm, reassuring, and supportive tone to rebuild confidence.",
                suggested_tone="Reassuring, encouraging, low-pressure"
            )

        # Check Confusion
        confusion_matches = _find_matches(CONFUSION_PATTERNS, lower_text)
        if confusion_matches:
            return EmotionCueResult(
                detected_cue=EmotionCue.CONFUSION,
                confidence=min(0.65 + 0.15 * len(confusion_matches), 0.95),
                trigger_phrases=confusion_matches,
                adaptation_strategy="Simplify explanation, use an alternative everyday analogy, and avoid technical jargon.",
                suggested_tone="Clear, simplified, gentle, analogy-driven"
            )

    # Check Confidence
    confidence_matches = _find_matches(CONFIDENCE_PATTERNS, lower_text)
    if confidence_matches:
        return EmotionCueResult(
            detected_cue=EmotionCue.CONFIDENCE,
            confidence=min(0.6 + 0.15 * len(confidence_matches), 0.95),
            trigger_phrases=confidence_matches,
            adaptation_strategy="Warmly acknowledge mastery, then offer a slightly more challenging question or edge case.",
            suggested_tone="Affirming, stimulating, slightly challenging"
        )

    # Check Engagement
    engagement_matches = _find_matches(ENGAGEMENT_PATTERNS, lower_text)
    if engagement_matches:
        return EmotionCueResult(
            detected_cue=EmotionCue.ENGAGEMENT,
            confidence=min(0.6 + 0.15 * len(engagement_matches), 0.95),
            trigger_phrases=engagement_matches,
            adaptation_strategy="Match curiosity with enthusiasm and explore deeper connections or practical applications.",
            suggested_tone="Enthusiastic, intellectually stimulating, exploratory"
        )

    return _build_neutral_result()

def _find_matches(patterns: List[str], text: str) -> List[str]:
    matches = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matches.append(m.group(0))
    return matches

def _build_neutral_result() -> EmotionCueResult:
    return EmotionCueResult(
        detected_cue=EmotionCue.NEUTRAL,
        confidence=0.5,
        trigger_phrases=[],
        adaptation_strategy="Maintain friendly, clear, and structured conversational tutoring.",
        suggested_tone="Friendly, structured, approachable"
    )
