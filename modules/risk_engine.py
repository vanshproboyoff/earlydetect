"""
Risk Engine
-----------
Combines scores from questionnaire, reaction time, and voice analysis
into a unified per-disease risk profile with actionable recommendations.
"""

DISEASES = {
    "mental_health": {
        "label": "Mental Health (Depression / Anxiety / Stress)",
        "categories": ["mental"],
        "modules": ["questionnaire", "voice"],
        "description": "Early signs of depression, anxiety, or chronic stress.",
    },

    "neurological": {
        "label": "Neurological (Parkinson's / Cognitive Decline)",
        "categories": ["neurological"],
        "modules": ["questionnaire", "reaction_time", "voice"],
        "description": "Possible early indicators of Parkinson's or cognitive decline.",
    },

    "metabolic": {
        "label": "Metabolic (Type 2 Diabetes Risk)",
        "categories": ["metabolic"],
        "modules": ["questionnaire"],
        "description": "Risk detection for Type 2 diabetes through behavioural patterns.",
    },

    "cardiovascular": {
        "label": "Cardiovascular (Hypertension Risk)",
        "categories": ["cardiovascular"],
        "modules": ["questionnaire", "voice"],
        "description": "Possible early hints of hypertension from stress markers.",
    },

    "sleep_disorder": {
        "label": "Sleep Disorder (Insomnia / Disrupted Sleep)",
        "categories": ["sleep"],
        "modules": ["questionnaire", "reaction_time"],
        "description": "Indicators of insomnia or disrupted sleep patterns.",
    },
}


RECOMMENDATIONS = {
    "low": (
        "No major concerns flagged for this category. "
        "Maintain healthy habits and schedule routine check-ups."
    ),

    "moderate": (
        "Some indicators present. Monitor these symptoms and "
        "consult a healthcare professional if they persist."
    ),

    "high": (
        "Multiple indicators detected. We strongly recommend "
        "consulting a doctor soon for proper evaluation."
    ),
}


def compute_risk_profile(data: dict) -> dict:

    q_scores = data.get("questionnaire_scores", {})
    rt_score = data.get("reaction_time_score", 0)
    v_score = data.get("voice_score", 0)

    all_flags = (
        data.get("questionnaire_flags", [])
        + data.get("reaction_time_flags", [])
        + data.get("voice_flags", [])
    )

    disease_risks = []

    for disease_id, disease in DISEASES.items():

        component_scores = []
        contributors = []

        # -------------------------
        # Questionnaire contribution
        # -------------------------

        for cat in disease["categories"]:

            if cat in q_scores:

                component_scores.append(q_scores[cat])

                contributors.append({
                    "source": "Questionnaire",
                    "score": q_scores[cat],
                    "reasons": [
                        f["message"]
                        for f in data.get("questionnaire_flags", [])
                        if f.get("category") == cat
                    ]
                })

        # -------------------------
        # Reaction time contribution
        # -------------------------

        if "reaction_time" in disease["modules"] and rt_score > 0:

            component_scores.append(rt_score)

            contributors.append({
                "source": "Reaction Time",
                "score": rt_score,
                "reasons": [
                    f["message"]
                    for f in data.get("reaction_time_flags", [])
                    if f.get("category") in disease["categories"]
                ]
            })

        # -------------------------
        # Voice contribution
        # -------------------------

        if "voice" in disease["modules"] and v_score > 0:

            component_scores.append(v_score)

            contributors.append({
                "source": "Voice Analysis",
                "score": v_score,
                "reasons": [
                    f["message"]
                    for f in data.get("voice_flags", [])
                    if f.get("category") in disease["categories"]
                ]
            })

        # -------------------------
        # Calculate final score
        # -------------------------

        if not component_scores:
            final_score = 0
        else:
            final_score = round(
                sum(component_scores) / len(component_scores)
            )

        # -------------------------
        # FIX: Calculate risk level
        # -------------------------

        level = _risk_level(final_score)

        # -------------------------
        # Relevant flags
        # -------------------------

        relevant_flags = [
            f for f in all_flags
            if f.get("category") in disease["categories"]
        ]

        # -------------------------
        # Store disease result
        # -------------------------

        disease_risks.append({
            "id": disease_id,
            "label": disease["label"],
            "description": disease["description"],
            "score": final_score,
            "level": level,
            "flags": relevant_flags,
            "contributors": contributors,
            "recommendation": RECOMMENDATIONS[level],
        })

    # -------------------------
    # Sort highest risk first
    # -------------------------

    disease_risks.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # -------------------------
    # Overall score
    # -------------------------

    overall_score = round(
        sum(d["score"] for d in disease_risks)
        / len(disease_risks)
    ) if disease_risks else 0

    overall_level = _risk_level(overall_score)

    high_count = sum(
        1 for d in disease_risks
        if d["level"] == "high"
    )

    moderate_count = sum(
        1 for d in disease_risks
        if d["level"] == "moderate"
    )

    # -------------------------
    # Final response
    # -------------------------

    return {
        "disease_risks": disease_risks,

        "overall_score": overall_score,

        "overall_level": overall_level,

        "high_count": high_count,

        "moderate_count": moderate_count,

        "disclaimer": (
            "IMPORTANT: This platform is a screening tool only and does NOT "
            "provide a medical diagnosis. Always consult a qualified "
            "healthcare professional for any health concerns. "
            "Results are informational only."
        ),
    }


def _risk_level(score: int) -> str:

    if score >= 70:
        return "high"

    elif score >= 40:
        return "moderate"

    return "low"