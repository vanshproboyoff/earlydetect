"""
Voice Analysis Module
---------------------
Accepts voice feature data extracted in the browser via the Web Audio API.
Features: pitch (Hz), energy (RMS), speech rate (words/min), pause ratio.

In production: replace with a real speech API such as:
  - AssemblyAI  → speaker diarization + sentiment
  - Azure Speech → emotion + pitch analysis
  - Hume AI     → prosodic emotion analysis
"""


# ── Threshold constants ───────────────────────────────────────────────────────
PITCH_LOW_HZ          = 85    # below normal range → possible fatigue / depression
PITCH_HIGH_HZ         = 255   # above normal → possible anxiety / stress
ENERGY_LOW            = 0.02  # very low energy → fatigue / low mood
ENERGY_HIGH           = 0.85  # high energy with high pitch → stress
SPEECH_RATE_SLOW      = 100   # wpm below this → possible depression / cognitive slowing
SPEECH_RATE_FAST      = 200   # wpm above this → possible anxiety
PAUSE_RATIO_HIGH      = 0.35  # more than 35 % silence → hesitation / cognitive load


def analyze_voice_features(data: dict) -> dict:
    """
    Parameters (all optional but at least 2 required for meaningful analysis)
    ----------
    data keys:
      pitch_mean_hz    : float  – mean fundamental frequency
      pitch_std_hz     : float  – pitch variability
      energy_mean      : float  – normalised RMS energy (0–1)
      speech_rate_wpm  : float  – estimated words per minute
      pause_ratio      : float  – fraction of audio that is silence
      sentiment_score  : float  – optional (−1 to +1, from speech-to-text API)
      transcript       : str    – optional transcript text

    Returns
    -------
    dict with score (0–100), flags, and feature summary.
    """
    received = {k: v for k, v in data.items() if v is not None}
    if len(received) < 2:
        return {"error": "Insufficient voice features provided"}

    score  = 0
    flags  = []
    detail = {}

    pitch    = data.get("pitch_mean_hz")
    pitch_sd = data.get("pitch_std_hz")
    energy   = data.get("energy_mean")
    wpm      = data.get("speech_rate_wpm")
    pauses   = data.get("pause_ratio")
    sentiment= data.get("sentiment_score")  # -1 (negative) to +1 (positive)

    # ── Pitch analysis ────────────────────────────────────────────────────────
    if pitch is not None:
        if pitch < PITCH_LOW_HZ:
            score += 20
            flags.append({
                "category": "mental",
                "message":  f"Low pitch ({pitch:.0f} Hz) may indicate low mood or fatigue.",
            })
        elif pitch > PITCH_HIGH_HZ:
            score += 15
            flags.append({
                "category": "cardiovascular",
                "message":  f"Elevated pitch ({pitch:.0f} Hz) associated with stress or anxiety.",
            })
        detail["pitch_hz"] = pitch

    if pitch_sd is not None and pitch_sd < 15:
        score += 10
        flags.append({
            "category": "mental",
            "message":  "Monotone speech (low pitch variability) can be an indicator of depression.",
        })

    # ── Energy analysis ───────────────────────────────────────────────────────
    if energy is not None:
        if energy < ENERGY_LOW:
            score += 20
            flags.append({
                "category": "mental",
                "message":  "Very low vocal energy detected — possible fatigue or low mood.",
            })
        elif energy > ENERGY_HIGH:
            score += 10
            flags.append({
                "category": "cardiovascular",
                "message":  "High vocal energy combined with elevated pitch may indicate stress.",
            })
        detail["energy"] = energy

    # ── Speech rate ───────────────────────────────────────────────────────────
    if wpm is not None:
        if wpm < SPEECH_RATE_SLOW:
            score += 20
            flags.append({
                "category": "neurological",
                "message":  f"Slow speech rate ({wpm:.0f} wpm) may indicate cognitive slowing or depression.",
            })
        elif wpm > SPEECH_RATE_FAST:
            score += 10
            flags.append({
                "category": "mental",
                "message":  f"Rapid speech rate ({wpm:.0f} wpm) may indicate anxiety.",
            })
        detail["speech_rate_wpm"] = wpm

    # ── Pause / hesitation analysis ───────────────────────────────────────────
    if pauses is not None:
        if pauses > PAUSE_RATIO_HIGH:
            score += 15
            flags.append({
                "category": "neurological",
                "message":  f"High pause ratio ({pauses*100:.0f}%) may suggest word-finding difficulty or cognitive load.",
            })
        detail["pause_ratio"] = pauses

    # ── Sentiment from transcript ─────────────────────────────────────────────
    if sentiment is not None:
        if sentiment < -0.4:
            score += 15
            flags.append({
                "category": "mental",
                "message":  "Negative sentiment detected in speech content.",
            })
        detail["sentiment"] = sentiment

    score = min(score, 100)

    return {
        "score":   score,
        "level":   _risk_level(score),
        "flags":   flags,
        "details": detail,
    }


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    elif score >= 40:
        return "moderate"
    return "low"
