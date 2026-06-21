from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, select

from backend.database.postgres import SessionLocal
from backend.main_dependencies import require_role
from backend.models.clinic_models import (
    Alert,
    AlertStatus,
    AlertType,
    MedicationAdherence,
    Patient,
    SymptomReport as SymptomReportModel,
)
from backend.services.alert_service import critical_tb_alert
from backend.services.risk_engine import compute_risk

router = APIRouter(prefix="/symptoms", tags=["symptoms"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SymptomReport(BaseModel):
    patient_id: int
    cough_duration: int | None = None
    blood_in_sputum: bool = False
    chest_pain: bool | None = None
    fever: bool | None = None
    night_sweats: bool | None = None
    fatigue: bool | None = None
    weight_loss: float | None = None  # percent
    breathing_difficulty: bool | None = None
    oxygen_saturation: float = 98.0


def symptom_score_from_payload(payload: SymptomReport) -> int:
    """Simple deterministic symptom score mapping to 0-100 (higher = worse)."""
    score = 0

    if payload.blood_in_sputum:
        score += 45

    if payload.chest_pain:
        score += 10
    if payload.fever:
        score += 10
    if payload.night_sweats:
        score += 8
    if payload.fatigue:
        score += 7
    if payload.breathing_difficulty:
        score += 15

    if payload.weight_loss is not None:
        # weight_loss is percent; cap at 10% => +20 points
        score += int(max(0.0, min(10.0, payload.weight_loss)) * 2)

    if payload.cough_duration is not None:
        # cough_duration in days; cap at 30 => +20 points
        score += int(max(0, min(30, payload.cough_duration)) * (20 / 30))

    # oxygen saturation: lower oxygen => worse
    osat = payload.oxygen_saturation
    if osat < 92:
        score += 40
    elif osat < 95:
        score += 25
    elif osat < 97:
        score += 10
    else:
        score += 0

    return max(0, min(100, int(score)))


def adherence_score_latest(db: Session, patient_id: int) -> int:
    """0/100 based on latest adherence event."""
    stmt = (
        select(MedicationAdherence)
        .where(MedicationAdherence.patient_id == patient_id)
        .order_by(desc(MedicationAdherence.taken_time))
        .limit(1)
    )

    row = db.scalars(stmt).first()
    if not row:
        return 50  # neutral default
    return 100 if row.taken else 0


@router.post("/report", dependencies=[Depends(require_role("patient", "nurse"))])
def submit_symptoms(payload: SymptomReport, db: Session = Depends(get_db)):
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        return {"saved": False, "error": "patient not found"}

    # Persist symptom report
    report = SymptomReportModel(
        patient_id=payload.patient_id,
        cough_duration=payload.cough_duration,
        blood_in_sputum=payload.blood_in_sputum,
        chest_pain=payload.chest_pain,
        fever=payload.fever,
        night_sweats=payload.night_sweats,
        fatigue=payload.fatigue,
        weight_loss=payload.weight_loss,
        breathing_difficulty=payload.breathing_difficulty,
        oxygen_saturation=payload.oxygen_saturation,
        created_at=datetime.utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    symptom_score = symptom_score_from_payload(payload)
    adherence_score = adherence_score_latest(db, payload.patient_id)
    risk = compute_risk(symptom_score=symptom_score, adherence_score=adherence_score)

    created_alerts: list[Alert] = []

    # Critical TB alert first (highest priority)
    crit = critical_tb_alert(
        blood_in_sputum=payload.blood_in_sputum,
        oxygen_saturation=payload.oxygen_saturation,
    )
    if crit:
        alert = Alert(
            patient_id=payload.patient_id,
            alert_type=AlertType(crit.alert_type),
            severity=crit.severity,
            message=crit.message,
            status=AlertStatus.open,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created_alerts.append(alert)

    # Risk-driven followup alert
    if not created_alerts and risk.risk_level in {"High Risk", "Critical"}:
        message = f"Risk alert: computed TB symptom risk level is '{risk.risk_level}' (risk_score={risk.risk_score}). Please review and follow up."
        alert = Alert(
            patient_id=payload.patient_id,
            alert_type=AlertType.followup_alert,
            severity="high" if risk.risk_level == "High Risk" else "critical",
            message=message,
            status=AlertStatus.open,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created_alerts.append(alert)

    return {
        "saved": True,
        "symptom_score": symptom_score,
        "adherence_score": adherence_score,
        "risk": {
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
        },
        "created_alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type.value,
                "severity": a.severity,
                "message": a.message,
                "status": a.status.value,
            }
            for a in created_alerts
        ],
    }


