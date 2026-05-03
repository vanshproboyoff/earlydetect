"""
Questionnaire Module
--------------------
Evaluates lifestyle, sleep, and mood survey responses.
Returns scored risk indicators per disease category.
"""

QUESTIONS = [
    # Sleep
    {"id": "sleep_hours",    "text": "How many hours do you sleep per night on average?",     "type": "number", "category": "sleep"},
    {"id": "sleep_quality",  "text": "How would you rate your sleep quality? (1=Very poor, 5=Excellent)", "type": "scale", "category": "sleep"},
    {"id": "wake_often",     "text": "Do you wake up multiple times during the night?",       "type": "yesno",  "category": "sleep"},
    # Mood / Mental Health
    {"id": "mood_low",       "text": "Have you felt persistently sad or hopeless recently?",  "type": "yesno",  "category": "mental"},
    {"id": "anxiety_level",  "text": "How often do you feel anxious or overwhelmed? (1=Never, 5=Always)", "type": "scale", "category": "mental"},
    {"id": "concentration",  "text": "Do you have difficulty concentrating on tasks?",        "type": "yesno",  "category": "mental"},
    # Metabolic
    {"id": "thirst",         "text": "Do you experience excessive thirst or frequent urination?", "type": "yesno", "category": "metabolic"},
    {"id": "fatigue",        "text": "Do you feel unusually fatigued even after rest?",        "type": "yesno",  "category": "metabolic"},
    {"id": "family_diabetes","text": "Does anyone in your immediate family have diabetes?",    "type": "yesno",  "category": "metabolic"},
    # Cardiovascular
    {"id": "chest_discomfort","text": "Do you experience chest tightness or shortness of breath?", "type": "yesno", "category": "cardiovascular"},
    {"id": "stress_level",   "text": "How would you rate your daily stress level? (1=Low, 5=Very high)", "type": "scale", "category": "cardiovascular"},
    {"id": "exercise",       "text": "How many days per week do you exercise for 30+ minutes?", "type": "number", "category": "cardiovascular"},
    # Neurological
    {"id": "tremor",         "text": "Have you noticed any trembling in your hands or limbs?", "type": "yesno", "category": "neurological"},
    {"id": "memory_issues",  "text": "Do you frequently forget recent events or words?",       "type": "yesno",  "category": "neurological"},
    {"id": "coordination",   "text": "Do you sometimes feel unsteady or have balance issues?", "type": "yesno",  "category": "neurological"},
]


def evaluate_questionnaire(responses: dict) -> dict:
    """
    Scores questionnaire responses and returns risk scores (0–100)
    per disease category.
    """
    scores = {
        "mental":        0,
        "metabolic":     0,
        "cardiovascular":0,
        "neurological":  0,
        "sleep":         0,
    }
    max_scores = {k: 0 for k in scores}

    for q in QUESTIONS:
        qid = q["id"]
        cat = q["category"]
        val = responses.get(qid)
        if val is None:
            continue

        # ── Sleep scoring ──────────────────────────────────────────────────
        if qid == "sleep_hours":
            hours = float(val)
            if hours < 5:
                scores["sleep"] += 30
            elif hours < 6:
                scores["sleep"] += 15
            elif hours > 9:
                scores["sleep"] += 10
            max_scores["sleep"] += 30

        elif qid == "sleep_quality":
            score = (6 - int(val)) * 5   # invert: poor quality → higher risk
            scores["sleep"] += score
            max_scores["sleep"] += 25

        elif qid == "wake_often":
            if _yes(val):
                scores["sleep"] += 20
            max_scores["sleep"] += 20

        # ── Mental health ──────────────────────────────────────────────────
        elif qid == "mood_low":
            if _yes(val):
                scores["mental"] += 35
            max_scores["mental"] += 35

        elif qid == "anxiety_level":
            scores["mental"] += (int(val) - 1) * 8
            max_scores["mental"] += 32

        elif qid == "concentration":
            if _yes(val):
                scores["mental"] += 20
            max_scores["mental"] += 20

        # ── Metabolic ─────────────────────────────────────────────────────
        elif qid == "thirst":
            if _yes(val):
                scores["metabolic"] += 30
            max_scores["metabolic"] += 30

        elif qid == "fatigue":
            if _yes(val):
                scores["metabolic"] += 20
            max_scores["metabolic"] += 20

        elif qid == "family_diabetes":
            if _yes(val):
                scores["metabolic"] += 25
            max_scores["metabolic"] += 25

        # ── Cardiovascular ────────────────────────────────────────────────
        elif qid == "chest_discomfort":
            if _yes(val):
                scores["cardiovascular"] += 35
            max_scores["cardiovascular"] += 35

        elif qid == "stress_level":
            scores["cardiovascular"] += (int(val) - 1) * 7
            max_scores["cardiovascular"] += 28

        elif qid == "exercise":
            days = float(val)
            if days == 0:
                scores["cardiovascular"] += 20
            elif days < 3:
                scores["cardiovascular"] += 10
            max_scores["cardiovascular"] += 20

        # ── Neurological ──────────────────────────────────────────────────
        elif qid == "tremor":
            if _yes(val):
                scores["neurological"] += 35
            max_scores["neurological"] += 35

        elif qid == "memory_issues":
            if _yes(val):
                scores["neurological"] += 30
            max_scores["neurological"] += 30

        elif qid == "coordination":
            if _yes(val):
                scores["neurological"] += 25
            max_scores["neurological"] += 25

    # Normalize to 0–100
    normalized = {}
    for cat, raw in scores.items():
        maximum = max_scores.get(cat, 1) or 1
        normalized[cat] = min(100, round((raw / maximum) * 100))

    return {
        "scores": normalized,
        "flags":  _build_flags(normalized),
        "raw":    scores,
    }


def _yes(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("yes", "true", "1")


def _build_flags(scores: dict) -> list:
    flags = []
    thresholds = {
        "mental":         (40, "Possible early signs of stress, anxiety, or depression"),
        "metabolic":      (45, "Indicators consistent with metabolic risk (e.g. pre-diabetes)"),
        "cardiovascular": (40, "Elevated cardiovascular stress markers detected"),
        "neurological":   (35, "Possible early neurological indicators noted"),
        "sleep":          (40, "Signs of disrupted sleep patterns detected"),
    }
    for cat, (threshold, msg) in thresholds.items():
        if scores.get(cat, 0) >= threshold:
            flags.append({"category": cat, "message": msg, "score": scores[cat]})
    return flags


def get_questions() -> list:
    return QUESTIONS
