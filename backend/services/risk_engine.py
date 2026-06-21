from dataclasses import dataclass


@dataclass
class RiskResult:
    symptom_score: int
    adherence_score: int
    risk_score: int
    risk_level: str


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def compute_risk(symptom_score: int, adherence_score: int) -> RiskResult:
    """Reference scoring model.

    symptom_score: higher is worse (0-100)
    adherence_score: higher is better (0-100)
    """
    symptom_score = clamp(symptom_score, 0, 100)
    adherence_score = clamp(adherence_score, 0, 100)

    # Risk: symptom dominates; adherence reduces risk.
    risk_score = int(0.7 * symptom_score + 0.3 * (100 - adherence_score))

    if risk_score <= 19:
        level = "Stable"
    elif risk_score <= 39:
        level = "Moderate Risk"
    elif risk_score <= 69:
        level = "High Risk"
    else:
        level = "Critical"

    return RiskResult(
        symptom_score=symptom_score,
        adherence_score=adherence_score,
        risk_score=risk_score,
        risk_level=level,
    )

