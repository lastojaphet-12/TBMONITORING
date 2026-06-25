from fastapi import APIRouter, Depends

from backend.main_dependencies import require_role

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/patient/{patient_id}", dependencies=[Depends(require_role("nurse", "provider", "patient"))])
def patient_report(patient_id: int):
    from datetime import datetime

    from sqlalchemy import desc, select

    from backend.database.postgres import SessionLocal
    from backend.models.clinic_models import (
        Alert,
        AlertStatus,
        MedicationAdherence,
        Patient,
        SymptomReport,
    )
    from backend.services.risk_engine import compute_risk

    db = SessionLocal()
    try:
        patient = db.get(Patient, patient_id)
        if not patient:
            return {"patient_id": patient_id, "report": None, "error": "patient not found"}

        latest_symptoms = (
            db.scalars(
                select(SymptomReport).where(SymptomReport.patient_id == patient_id).order_by(desc(SymptomReport.created_at)).limit(1)
            ).first()
        )

        latest_adherence = (
            db.scalars(
                select(MedicationAdherence)
                .where(MedicationAdherence.patient_id == patient_id)
                .order_by(desc(MedicationAdherence.taken_time))
                .limit(1)
            ).first()
        )

        open_alerts = db.scalars(
            select(Alert)
            .where(Alert.patient_id == patient_id)
            .where(Alert.status == AlertStatus.open)
            .order_by(desc(Alert.created_at))
            .limit(50)
        ).all()

        # Compute a risk snapshot if we have latest symptoms.
        symptom_payload = None
        risk_snapshot = None
        if latest_symptoms:
            symptom_payload = {
                "cough_duration": latest_symptoms.cough_duration,
                "blood_in_sputum": latest_symptoms.blood_in_sputum,
                "chest_pain": latest_symptoms.chest_pain,
                "fever": latest_symptoms.fever,
                "night_sweats": latest_symptoms.night_sweats,
                "fatigue": latest_symptoms.fatigue,
                "weight_loss": latest_symptoms.weight_loss,
                "breathing_difficulty": latest_symptoms.breathing_difficulty,
                "oxygen_saturation": latest_symptoms.oxygen_saturation,
            }
            # mirror mapping used in symptoms.py
            from backend.api.symptoms import symptom_score_from_payload, SymptomReport as SymptomReportSchema

            # Build schema to reuse mapping
            schema = SymptomReportSchema(patient_id=patient_id, **symptom_payload)
            symptom_score = symptom_score_from_payload(schema)
            adherence_score = 100 if (latest_adherence and latest_adherence.taken) else 0
            risk = compute_risk(symptom_score=symptom_score, adherence_score=adherence_score)
            risk_snapshot = {
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
            }

        return {
            "patient_id": patient_id,
            "report": {
                "patient": {
                    "id": patient.id,
                    "tb_number": patient.tb_number,
                    "full_name": patient.full_name,
                    "gender": patient.gender.value if hasattr(patient.gender, "value") else str(patient.gender),
                    "date_of_birth": patient.date_of_birth.date().isoformat(),
                    "phone": patient.phone,
                    "district": patient.district,
                    "village": patient.village,
                    "provider_id": patient.provider_id,
                    "nurse_id": patient.nurse_id,
                },
                "latest_symptoms": (
                    {
                        "id": latest_symptoms.id,
                        "cough_duration": latest_symptoms.cough_duration,
                        "blood_in_sputum": latest_symptoms.blood_in_sputum,
                        "chest_pain": latest_symptoms.chest_pain,
                        "fever": latest_symptoms.fever,
                        "night_sweats": latest_symptoms.night_sweats,
                        "fatigue": latest_symptoms.fatigue,
                        "weight_loss": latest_symptoms.weight_loss,
                        "breathing_difficulty": latest_symptoms.breathing_difficulty,
                        "oxygen_saturation": latest_symptoms.oxygen_saturation,
                        "created_at": latest_symptoms.created_at.isoformat(),
                    }
                    if latest_symptoms
                    else None
                ),
                "latest_adherence": (
                    {
                        "id": latest_adherence.id,
                        "taken": latest_adherence.taken,
                        "taken_time": latest_adherence.taken_time.isoformat(),
                        "remarks": latest_adherence.remarks,
                    }
                    if latest_adherence
                    else None
                ),
                "risk_snapshot": risk_snapshot,
                "open_alerts": [
                    {
                        "id": a.id,
                        "alert_type": a.alert_type.value,
                        "severity": a.severity,
                        "message": a.message,
                        "status": a.status.value,
                        "created_at": (a.created_at.isoformat() if a.created_at else None),
                    }
                    for a in open_alerts
                ],
            },
        }
    finally:
        db.close()

