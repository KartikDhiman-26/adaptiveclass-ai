"""
Tests for lightweight text-based emotion cue detector.
Verifies pedagogical tone adaptation, confidence scoring, negation handling,
and ethical safeguarding.
"""

from app.student_ai.emotion_detector import (
    detect_conversational_cue, EmotionCue, ETHICAL_DISCLAIMER
)

def test_detect_confusion():
    text1 = "I don't understand how recursion works with the call stack."
    res1 = detect_conversational_cue(text1)
    assert res1.detected_cue == EmotionCue.CONFUSION
    assert res1.confidence >= 0.6
    assert "simplify" in res1.adaptation_strategy.lower()
    assert res1.ethical_disclaimer == ETHICAL_DISCLAIMER

    text2 = "I'm lost, what do you mean by base case?"
    res2 = detect_conversational_cue(text2)
    assert res2.detected_cue == EmotionCue.CONFUSION

def test_detect_frustration():
    text = "This is too hard, I give up. I've been stuck for hours and hate this!"
    res = detect_conversational_cue(text)
    assert res.detected_cue == EmotionCue.FRUSTRATION
    assert res.confidence >= 0.7
    assert "patience" in res1_strategy if False else "patience" in res.adaptation_strategy.lower()
    assert "step" in res.adaptation_strategy.lower()

def test_detect_nervousness():
    text = "I'm so worried about the upcoming exam, scared I will fail data structures."
    res = detect_conversational_cue(text)
    assert res.detected_cue == EmotionCue.NERVOUSNESS
    assert "reassuring" in res.adaptation_strategy.lower()

def test_detect_confidence():
    text = "That was easy! I get it now, bring on the next question."
    res = detect_conversational_cue(text)
    assert res.detected_cue == EmotionCue.CONFIDENCE
    assert "challenging" in res.adaptation_strategy.lower()

def test_detect_engagement():
    text = "That is fascinating, tell me more about how BST balances itself!"
    res = detect_conversational_cue(text)
    assert res.detected_cue == EmotionCue.ENGAGEMENT
    assert "curiosity" in res.adaptation_strategy.lower() or "enthusiasm" in res.adaptation_strategy.lower()

def test_neutral_and_empty():
    res_empty = detect_conversational_cue("")
    assert res_empty.detected_cue == EmotionCue.NEUTRAL

    res_normal = detect_conversational_cue("Can you show me the code for binary search?")
    assert res_normal.detected_cue == EmotionCue.NEUTRAL

def test_negation_handling():
    # Student states they are NOT confused
    text = "I am not confused, I just want the next problem."
    res = detect_conversational_cue(text)
    assert res.detected_cue != EmotionCue.CONFUSION
