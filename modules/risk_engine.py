# modules/risk_engine.py

"""
Risk Engine for EarlyDetect

IMPORTANT:
This is a heuristic screening system for a school/project application.
It is NOT a medical diagnosis system.
"""

# ---------------------------------------------------------
# Risk levels
# ---------------------------------------------------------

def _risk_level(score):
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Moderate"
    else:
        return "Low"


# ---------------------------------------------------------
# Safe number conversion
# ---------------------------------------------------------

def _number(value, default=0):
    try:
        return float(value)
    except:
        return default


# ---------------------------------------------------------
# Get category score from a dictionary
# ---------------------------------------------------------

def _get_category_score(data, category):
    if not isinstance(data, dict):
        return 0

    # Normal category name
    if category in data:
        return _number(data[category])

    # Common alternative names
    alternatives = {
        "mental": [
            "mental_score",
            "mental_health",
            "mental_health_score"
        ],
        "neurological": [
            "neurological_score",
            "neuro",
            "neuro_score"
        ],
        "metabolic": [
            "metabolic_score"
        ],
        "cardiovascular": [
            "cardiovascular_score",
            "cardio",
            "cardio_score"
        ],
        "sleep": [
            "sleep_score",
            "sleep_disorder"
        ]
    }

    for key in alternatives.get(category, []):
        if key in data:
            return _number(data[key])

    return 0


# ---------------------------------------------------------
# Get category score from facial analysis
# ---------------------------------------------------------

def _get_facial_score(facial_data, category):
    if not isinstance(facial_data, dict):
        return 0

    # New structure:
    # {
    #     "mental": 40,
    #     "cardiovascular": 20
    # }
    if "category_scores" in facial_data:
        return _get_category_score(
            facial_data["category_scores"],
            category
        )

    # Current facial_analysis.py structure
    if category == "mental":
        return _number(
            facial_data.get("mental_score", 0)
        )

    if category == "cardiovascular":
        return _number(
            facial_data.get("cardiovascular_score", 0)
        )

    return 0


# ---------------------------------------------------------
# Get category score from voice analysis
# ---------------------------------------------------------

def _get_voice_score(voice_data, category):
    if not isinstance(voice_data, dict):
        return 0

    # Preferred new structure
    if "category_scores" in voice_data:
        return _get_category_score(
            voice_data["category_scores"],
            category
        )

    # If old voice module only returns one global score,
    # DO NOT use that score for every disease.
    #
    # Instead use its flags to determine which category
    # the voice result actually relates to.

    flags = voice_data.get("flags", [])

    if not isinstance(flags, list):
        return 0

    score = 0

    for flag in flags:
        text = str(flag).lower()

        if category == "mental":
            if "low pitch" in text:
                score += 20
            elif "high speech rate" in text:
                score += 10
            elif "low energy" in text:
                score += 20
            elif "negative sentiment" in text:
                score += 15

        elif category == "neurological":
            if "slow speech" in text:
                score += 20
            elif "pause" in text:
                score += 15

        elif category == "cardiovascular":
            if "high pitch" in text:
                score += 15
            elif "high energy" in text:
                score += 10

    return min(score, 100)


# ---------------------------------------------------------
# Get category score from reaction-time analysis
# ---------------------------------------------------------

def _get_reaction_score(rt_data, category):
    if not isinstance(rt_data, dict):
        return 0

    # Preferred new structure
    if "category_scores" in rt_data:
        return _get_category_score(
            rt_data["category_scores"],
            category
        )

    flags = rt_data.get("flags", [])

    if not isinstance(flags, list):
        flags = []

    score = _number(
        rt_data.get("score", 0)
    )

    # Old reaction-time module has one global score.
    # Only use it where the corresponding flag exists.

    relevant = False

    for flag in flags:
        text = str(flag).lower()

        if category == "neurological":
            if "neurological" in text or "reaction" in text:
                relevant = True

        elif category == "sleep":
            if "sleep" in text:
                relevant = True

    if relevant:
        return min(score, 100)

    return 0


# ---------------------------------------------------------
# Combine scores
# ---------------------------------------------------------

def _combine_scores(scores, weights=None):

    valid_scores = []

    for value in scores:
        if value is not None:
            value = _number(value)

            if value > 0:
                valid_scores.append(value)

    if not valid_scores:
        return 0

    if weights is None:
        return round(
            sum(valid_scores) / len(valid_scores),
            2
        )

    weighted_total = 0
    weight_total = 0

    for value, weight in zip(scores, weights):

        if value is not None:
            value = _number(value)

            if value > 0:
                weighted_total += value * weight
                weight_total += weight

    if weight_total == 0:
        return 0

    return round(
        weighted_total / weight_total,
        2
    )


# ---------------------------------------------------------
# Main risk calculation
# ---------------------------------------------------------

def calculate_risk(
    questionnaire_scores=None,
    questionnaire_flags=None,
    reaction_time_score=0,
    reaction_time_flags=None,
    voice_score=0,
    voice_flags=None,
    facial_scores=None,
    facial_flags=None,
    reaction_time_data=None,
    voice_data=None,
    facial_data=None
):

    # -----------------------------------------------------
    # Prepare data
    # -----------------------------------------------------

    questionnaire_scores = questionnaire_scores or {}
    questionnaire_flags = questionnaire_flags or []

    reaction_time_flags = reaction_time_flags or []
    voice_flags = voice_flags or []
    facial_flags = facial_flags or []

    # -----------------------------------------------------
    # Convert old-style inputs into dictionaries
    # -----------------------------------------------------

    if reaction_time_data is None:
        reaction_time_data = {
            "score": reaction_time_score,
            "flags": reaction_time_flags
        }

    if voice_data is None:
        voice_data = {
            "score": voice_score,
            "flags": voice_flags
        }

    if facial_data is None:
        facial_data = facial_scores or {}

        if isinstance(facial_data, dict):
            facial_data = dict(facial_data)
            facial_data["flags"] = facial_flags

    # -----------------------------------------------------
    # Disease/category definitions
    # -----------------------------------------------------

    diseases = {

        "mental_health": {
            "name": "Mental Health",
            "category": "mental",
            "components": [
                "questionnaire",
                "voice",
                "facial"
            ]
        },

        "neurological": {
            "name": "Neurological",
            "category": "neurological",
            "components": [
                "questionnaire",
                "reaction_time",
                "voice"
            ]
        },

        "metabolic": {
            "name": "Metabolic",
            "category": "metabolic",
            "components": [
                "questionnaire"
            ]
        },

        "cardiovascular": {
            "name": "Cardiovascular",
            "category": "cardiovascular",
            "components": [
                "questionnaire",
                "voice",
                "facial"
            ]
        },

        "sleep_disorder": {
            "name": "Sleep",
            "category": "sleep",
            "components": [
                "questionnaire",
                "reaction_time"
            ]
        }
    }

    results = []

    # -----------------------------------------------------
    # Calculate each category independently
    # -----------------------------------------------------

    for disease_key, disease in diseases.items():

        category = disease["category"]

        component_scores = []
        component_names = []

        # ---------------------------------------------
        # Questionnaire
        # ---------------------------------------------

        if "questionnaire" in disease["components"]:

            q_score = _get_category_score(
                questionnaire_scores,
                category
            )

            if q_score > 0:
                component_scores.append(q_score)
                component_names.append("Questionnaire")

        # ---------------------------------------------
        # Reaction time
        # ---------------------------------------------

        if "reaction_time" in disease["components"]:

            rt_score = _get_reaction_score(
                reaction_time_data,
                category
            )

            if rt_score > 0:
                component_scores.append(rt_score)
                component_names.append("Reaction Time")

        # ---------------------------------------------
        # Voice
        # ---------------------------------------------

        if "voice" in disease["components"]:

            v_score = _get_voice_score(
                voice_data,
                category
            )

            if v_score > 0:
                component_scores.append(v_score)
                component_names.append("Voice Analysis")

        # ---------------------------------------------
        # Facial
        # ---------------------------------------------

        if "facial" in disease["components"]:

            f_score = _get_facial_score(
                facial_data,
                category
            )

            if f_score > 0:
                component_scores.append(f_score)
                component_names.append("Facial Analysis")

        # ---------------------------------------------
        # Final score
        # ---------------------------------------------

        if component_scores:

            # Questionnaire is the main screening signal.
            # Other modules provide supporting evidence.
            #
            # If questionnaire exists:
            # 60% questionnaire
            # 20% other module(s)
            #
            # If questionnaire does not exist:
            # average available supporting signals.

            q_score = 0

            if "questionnaire" in disease["components"]:
                q_score = _get_category_score(
                    questionnaire_scores,
                    category
                )

            other_scores = []

            for score, name in zip(
                component_scores,
                component_names
            ):
                if name != "Questionnaire":
                    other_scores.append(score)

            if q_score > 0 and other_scores:

                supporting_average = (
                    sum(other_scores) /
                    len(other_scores)
                )

                final_score = (
                    q_score * 0.70 +
                    supporting_average * 0.30
                )

            elif q_score > 0:

                final_score = q_score

            else:

                final_score = (
                    sum(component_scores) /
                    len(component_scores)
                )

        else:
            final_score = 0

        final_score = round(
            min(max(final_score, 0), 100),
            2
        )

        level = _risk_level(final_score)

        # -------------------------------------------------
        # Get relevant flags
        # -------------------------------------------------

        relevant_flags = []

        for flag in questionnaire_flags:
            if isinstance(flag, dict):

                flag_category = str(
                    flag.get("category", "")
                ).lower()

                if (
                    category in flag_category or
                    flag_category in category
                ):
                    relevant_flags.append(flag)

            else:
                text = str(flag).lower()

                if category in text:
                    relevant_flags.append(flag)

        # Add module flags only to relevant diseases

        if category in ["neurological", "sleep"]:

            for flag in reaction_time_flags:
                relevant_flags.append(flag)

        if category in [
            "mental",
            "neurological",
            "cardiovascular"
        ]:

            for flag in voice_flags:
                relevant_flags.append(flag)

        if category in [
            "mental",
            "cardiovascular"
        ]:

            for flag in facial_flags:
                relevant_flags.append(flag)

        # -------------------------------------------------
        # Result
        # -------------------------------------------------

        result = {
            "key": disease_key,
            "name": disease["name"],
            "score": final_score,
            "level": level,
            "flags": relevant_flags,
            "components": {
                name: score
                for name, score in zip(
                    component_names,
                    component_scores
                )
            }
        }

        results.append(result)

    # ---------------------------------------------------------
    # Sort highest risk first
    # ---------------------------------------------------------

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # Overall score
    #
    # IMPORTANT:
    # Do not simply average all five diseases.
    # Use the strongest relevant risks instead.
    # ---------------------------------------------------------

    non_zero_scores = [
        result["score"]
        for result in results
        if result["score"] > 0
    ]

    if non_zero_scores:

        highest_score = max(non_zero_scores)

        # Overall score is mostly influenced by the
        # highest category, while still considering
        # other elevated categories.

        elevated_scores = [
            score
            for score in non_zero_scores
            if score >= 40
        ]

        if elevated_scores:

            average_elevated = (
                sum(elevated_scores) /
                len(elevated_scores)
            )

            overall_score = (
                highest_score * 0.70 +
                average_elevated * 0.30
            )

        else:

            overall_score = highest_score

    else:

        overall_score = 0

    overall_score = round(
        min(max(overall_score, 0), 100),
        2
    )

    overall_level = _risk_level(
        overall_score
    )

    # ---------------------------------------------------------
    # Count levels
    # ---------------------------------------------------------

    high_count = sum(
        1
        for result in results
        if result["level"] == "High"
    )

    moderate_count = sum(
        1
        for result in results
        if result["level"] == "Moderate"
    )

    # ---------------------------------------------------------
    # Recommendations
    # ---------------------------------------------------------

    recommendations = []

    if high_count > 0:

        recommendations.append(
            "Some screening results are elevated. "
            "Consider discussing the results with a "
            "qualified healthcare professional."
        )

    elif moderate_count > 0:

        recommendations.append(
            "Some screening indicators are moderately "
            "elevated. Consider monitoring symptoms and "
            "discussing persistent concerns with a "
            "qualified healthcare professional."
        )

    else:

        recommendations.append(
            "No major elevated indicators were detected "
            "by this screening system."
        )

    recommendations.append(
        "This screening result is an indication based "
        "on the information provided and is not a medical diagnosis."
    )

    # ---------------------------------------------------------
    # Final output
    # ---------------------------------------------------------

    return {
        "overall_score": overall_score,
        "overall_level": overall_level,
        "high_count": high_count,
        "moderate_count": moderate_count,
        "results": results,
        "recommendations": recommendations
    }


# ---------------------------------------------------------
# Compatibility wrapper
#
# Some versions of app.py may call compute_risk()
# instead of calculate_risk().
# ---------------------------------------------------------

def compute_risk(
    questionnaire_scores=None,
    questionnaire_flags=None,
    reaction_time_score=0,
    reaction_time_flags=None,
    voice_score=0,
    voice_flags=None,
    facial_scores=None,
    facial_flags=None,
    reaction_time_data=None,
    voice_data=None,
    facial_data=None
):

    return calculate_risk(
        questionnaire_scores=questionnaire_scores,
        questionnaire_flags=questionnaire_flags,
        reaction_time_score=reaction_time_score,
        reaction_time_flags=reaction_time_flags,
        voice_score=voice_score,
        voice_flags=voice_flags,
        facial_scores=facial_scores,
        facial_flags=facial_flags,
        reaction_time_data=reaction_time_data,
        voice_data=voice_data,
        facial_data=facial_data
    )
def compute_risk_profile(
    questionnaire_scores=None,
    questionnaire_flags=None,
    reaction_time_score=0,
    reaction_time_flags=None,
    voice_score=0,
    voice_flags=None,
    facial_scores=None,
    facial_data=None,
    face_mental_score=0,
    face_cardio_score=0,
    face_flags=None
):
    return calculate_risk(
        questionnaire_scores=questionnaire_scores,
        questionnaire_flags=questionnaire_flags,
        reaction_time_score=reaction_time_score,
        reaction_time_flags=reaction_time_flags,
        voice_score=voice_score,
        voice_flags=voice_flags,
        facial_scores=facial_scores,
        facial_data=facial_data,
        face_mental_score=face_mental_score,
        face_cardio_score=face_cardio_score,
        face_flags=face_flags
    )