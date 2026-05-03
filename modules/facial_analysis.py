"""
Facial Analysis Module
----------------------
Analyses an uploaded photo using DeepFace to detect:
- Emotions (happy, sad, angry, fearful, surprised, disgusted, neutral)
- Estimated age
- Gender
- Dominant race

Maps emotion scores to health risk indicators for mental health
and cardiovascular (stress) categories.
"""

import base64
import io
import numpy as np

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False


# ── Emotion → Risk Mapping ────────────────────────────────────────────────────
# How much each emotion contributes to each disease category (0–100 weight)
EMOTION_RISK_MAP = {
    "sad":       {"mental": 40, "cardiovascular": 10},
    "angry":     {"mental": 20, "cardiovascular": 35},
    "fearful":   {"mental": 35, "cardiovascular": 25},
    "disgusted": {"mental": 15, "cardiovascular": 10},
    "neutral":   {"mental":  5, "cardiovascular":  5},
    "surprised": {"mental":  5, "cardiovascular": 10},
    "happy":     {"mental":  0, "cardiovascular":  0},
}

STRESS_EMOTIONS = {"angry", "fearful", "disgusted"}
LOW_MOOD_EMOTIONS = {"sad", "fearful", "disgusted"}


def analyze_face(image_data: str) -> dict:
    """
    Parameters
    ----------
    image_data : str
        Base64-encoded image string (with or without data URI prefix).

    Returns
    -------
    dict with emotion scores, age, gender, risk scores, and flags.
    """
    if not DEEPFACE_AVAILABLE:
        return {"error": "DeepFace is not installed. Run: pip install deepface tf-keras"}

    try:
        # Decode base64 image
        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image_array = _bytes_to_array(image_bytes)

        # Run DeepFace analysis
        results = DeepFace.analyze(
            img_path      = image_array,
            actions       = ["emotion", "age", "gender"],
            enforce_detection = False,
            silent        = True,
        )

        # DeepFace returns a list if multiple faces detected — use first face
        if isinstance(results, list):
            result = results[0]
        else:
            result = results

        emotions    = result.get("emotion", {})
        dominant    = result.get("dominant_emotion", "neutral")
        age         = result.get("age", "Unknown")
        gender_data = result.get("gender", {})

        # Get dominant gender
        if isinstance(gender_data, dict):
            gender = max(gender_data, key=gender_data.get)
            gender_confidence = round(max(gender_data.values()), 1)
        else:
            gender = str(gender_data)
            gender_confidence = None

        # Round emotion percentages
        emotions_rounded = {k: round(v, 1) for k, v in emotions.items()}

        # ── Risk Scoring ──────────────────────────────────────────────────
        mental_score = 0
        cardio_score = 0

        for emotion, percentage in emotions.items():
            weight = percentage / 100
            mapping = EMOTION_RISK_MAP.get(emotion, {})
            mental_score += mapping.get("mental", 0) * weight
            cardio_score += mapping.get("cardiovascular", 0) * weight

        mental_score = min(100, round(mental_score))
        cardio_score = min(100, round(cardio_score))

        # ── Flags ─────────────────────────────────────────────────────────
        flags = []

        if dominant in LOW_MOOD_EMOTIONS:
            flags.append({
                "category": "mental",
                "message":  f"Dominant facial expression '{dominant}' may indicate low mood or emotional distress.",
            })

        if dominant in STRESS_EMOTIONS:
            flags.append({
                "category": "cardiovascular",
                "message":  f"Facial stress markers detected ('{dominant}') — may indicate elevated stress or anxiety.",
            })

        # Check if happy emotion is very low (possible masked emotion)
        happy_pct = emotions.get("happy", 0)
        if happy_pct < 10 and dominant not in ("happy", "surprised"):
            flags.append({
                "category": "mental",
                "message":  f"Low positive affect detected ({happy_pct:.0f}% happy) — may suggest suppressed mood.",
            })

        return {
            "emotions":           emotions_rounded,
            "dominant_emotion":   dominant,
            "age":                age,
            "gender":             gender,
            "gender_confidence":  gender_confidence,
            "mental_score":       mental_score,
            "cardiovascular_score": cardio_score,
            "mental_level":       _risk_level(mental_score),
            "cardiovascular_level": _risk_level(cardio_score),
            "flags":              flags,
            "faces_detected":     len(results) if isinstance(results, list) else 1,
        }

    except Exception as e:
        return {"error": f"Face analysis failed: {str(e)}. Please try a clearer photo."}


def _bytes_to_array(image_bytes: bytes):
    """Convert raw image bytes to numpy array for DeepFace."""
    import cv2
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image. Please upload a valid JPG or PNG.")
    return img


def _risk_level(score: int) -> str:
    if score >= 55:
        return "high"
    elif score >= 25:
        return "moderate"
    return "low"    