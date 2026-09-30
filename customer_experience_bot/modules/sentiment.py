"""
Sentiment & Urgency Analysis Module for Enterprise Customer Experience (CX) Suite.
Performs real-time sentiment scoring (-100 to +100), emotion detection,
and urgency classification (LOW, MEDIUM, HIGH, CRITICAL).
"""

import re
from typing import Dict, Any

EMOTIONS = [
    "Frustrated",
    "Angry",
    "Disappointed",
    "Confused",
    "Satisfied",
    "Happy",
    "Neutral",
    "Anxious",
    "Urgent"
]

SENTIMENTS = [
    "Very Positive",
    "Positive",
    "Neutral",
    "Negative",
    "Very Negative"
]

URGENCIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL"
]

# Lexicons and weights for fallback sentiment scoring
VERY_NEGATIVE_TRIGGERS = [
    "terrible", "worst", "horrible", "furious", "disaster", "cheated", "fraud",
    "lawyer", "legal notice", "consumer court", "sue", "unacceptable", "pathetic",
    "hopeless", "fire", "smoke", "spark", "shock", "burst", "explosion", "injury",
    "stolen", "loss of business", "nobody is responding", "no response for", "10 days", "unresolved"
]

NEGATIVE_TRIGGERS = [
    "bad", "poor", "complaint", "stopped working", "broken", "delay", "delayed",
    "not happy", "frustrated", "disappointed", "annoyed", "issue", "problem",
    "failing", "fail", "not working", "useless", "headache", "waiting", "defect"
]

POSITIVE_TRIGGERS = [
    "good", "great", "nice", "helpful", "thanks", "thank you", "resolved",
    "working fine", "satisfied", "appreciate", "quick", "prompt", "smooth"
]

VERY_POSITIVE_TRIGGERS = [
    "excellent", "outstanding", "amazing", "wonderful", "delighted", "superb",
    "fantastic", "best service", "extremely satisfied", "kudos", "brilliant"
]

CRITICAL_SAFETY_KEYWORDS = [
    "fire", "smoke", "spark", "sparking", "shock", "electrocuted", "electrocution",
    "burning", "hazard", "explosion", "physical injury", "threat", "police", "legal"
]

HIGH_URGENCY_KEYWORDS = [
    "days without", "nobody responded", "escalate", "manager", "unresolved",
    "urgent", "asap", "emergency", "immediately", "shut down", "plant stopped",
    "dealer loss", "repeated", "again and again"
]

def analyze_sentiment_fallback(text: str) -> Dict[str, Any]:
    """
    High-precision deterministic rule-based sentiment, emotion, and urgency analyzer.
    Used when API key is unavailable or offline.
    """
    text_lower = text.lower()

    # 1. Critical & Urgency Detection
    is_critical = any(re.search(rf"\b{k}\b", text_lower) for k in CRITICAL_SAFETY_KEYWORDS)
    is_high = any(re.search(rf"\b{k}\b", text_lower) for k in HIGH_URGENCY_KEYWORDS)

    if is_critical:
        urgency = "CRITICAL"
    elif is_high:
        urgency = "HIGH"
    elif any(k in text_lower for k in ["not working", "broken", "issue", "delay", "service"]):
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    # 2. Sentiment Scoring
    score = 0
    for word in VERY_NEGATIVE_TRIGGERS:
        if word in text_lower:
            score -= 40
    for word in NEGATIVE_TRIGGERS:
        if word in text_lower:
            score -= 15
    for word in POSITIVE_TRIGGERS:
        if word in text_lower:
            score += 20
    for word in VERY_POSITIVE_TRIGGERS:
        if word in text_lower:
            score += 45

    # Check for intense delay expressions (e.g., "10 days", "has not visited for 5 days")
    delay_match = re.search(r"(\d+)\s+days?", text_lower)
    if delay_match:
        days = int(delay_match.group(1))
        if days >= 3:
            score -= min(50, days * 7)
            if urgency not in ["CRITICAL", "HIGH"]:
                urgency = "HIGH"

    # Clamp score to [-100, 100]
    score = max(-100, min(100, score))

    # Map to discrete sentiment
    if score <= -60:
        sentiment = "Very Negative"
    elif score <= -15:
        sentiment = "Negative"
    elif score < 20:
        sentiment = "Neutral"
    elif score <= 60:
        sentiment = "Positive"
    else:
        sentiment = "Very Positive"

    # 3. Emotion Detection
    if is_critical or "fire" in text_lower or "smoke" in text_lower:
        emotion = "Urgent"
    elif any(k in text_lower for k in ["furious", "angry", "terrible", "worst", "cheated", "legal", "sue"]):
        emotion = "Angry"
    elif any(k in text_lower for k in ["frustrated", "waiting", "nobody", "unresolved", "not visited", "hasn't visited", "has not visited", "stopped working", "again and again", "days"]):
        emotion = "Frustrated"
    elif any(k in text_lower for k in ["disappointed", "poor", "expected better", "bad"]):
        emotion = "Disappointed"
    elif any(k in text_lower for k in ["worried", "concerned", "anxious", "scared", "fear"]):
        emotion = "Anxious"
    elif any(k in text_lower for k in ["confused", "how to", "what does", "error code", "don't understand"]):
        emotion = "Confused"
    elif sentiment == "Very Positive":
        emotion = "Happy"
    elif sentiment == "Positive":
        emotion = "Satisfied"
    else:
        emotion = "Neutral"

    return {
        "sentiment": sentiment,
        "sentiment_score": score,
        "emotion": emotion,
        "urgency": urgency
    }
