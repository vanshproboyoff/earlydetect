"""
Reaction Time Module
--------------------
Evaluates a list of reaction times (milliseconds) from the browser-based tap test.
Returns statistical features and risk indicators for neurological/sleep categories.
"""

import statistics


# Reference ranges (ms) based on general population data
NORMAL_MEAN_MS   = 250   # avg healthy adult
SLOW_THRESHOLD   = 350   # above this → elevated flag
VERY_SLOW        = 450   # above this → high flag
HIGH_VARIABILITY = 80    # std dev above this → inconsistency flag


def evaluate_reaction_time(times: list) -> dict:
    """
    Parameters
    ----------
    times : list of float
        Reaction times in milliseconds from each trial.

    Returns
    -------
    dict with stats, risk score (0–100), and interpretation flags.
    """
    if not times or len(times) < 3:
        return {"error": "Not enough trials (minimum 3 required)"}

    times = [float(t) for t in times if 50 < float(t) < 2000]  # filter outliers
    if len(times) < 3:
        return {"error": "Too many outlier values — please retry the test"}

    mean_rt   = statistics.mean(times)
    median_rt = statistics.median(times)
    std_rt    = statistics.stdev(times) if len(times) > 1 else 0
    best_rt   = min(times)
    worst_rt  = max(times)

    # ── Risk scoring ──────────────────────────────────────────────────────────
    score = 0

    # Slowness
    if mean_rt > VERY_SLOW:
        score += 50
    elif mean_rt > SLOW_THRESHOLD:
        score += 30
    elif mean_rt > NORMAL_MEAN_MS + 50:
        score += 15

    # High variability (inconsistency → neurological flag)
    if std_rt > HIGH_VARIABILITY:
        score += 25
    elif std_rt > 60:
        score += 10

    score = min(score, 100)

    # ── Interpretation ────────────────────────────────────────────────────────
    flags = []
    if mean_rt > SLOW_THRESHOLD:
        flags.append({
            "category": "neurological",
            "message":  f"Mean reaction time ({mean_rt:.0f} ms) is above normal range — may indicate slowed processing speed.",
        })
    if std_rt > HIGH_VARIABILITY:
        flags.append({
            "category": "neurological",
            "message":  f"High variability in responses (±{std_rt:.0f} ms) — may indicate inconsistent motor control.",
        })
    if mean_rt > SLOW_THRESHOLD:
        flags.append({
            "category": "sleep",
            "message":  "Slow reaction times can also be associated with sleep deprivation or fatigue.",
        })

    level = _risk_level(score)

    return {
        "stats": {
            "mean_ms":   round(mean_rt, 1),
            "median_ms": round(median_rt, 1),
            "std_ms":    round(std_rt, 1),
            "best_ms":   round(best_rt, 1),
            "worst_ms":  round(worst_rt, 1),
            "trials":    len(times),
        },
        "score":  score,
        "level":  level,
        "flags":  flags,
    }


def _risk_level(score: int) -> str:
    if score >= 75:
        return "high"
    elif score >= 45:
        return "moderate"
    return "low"
