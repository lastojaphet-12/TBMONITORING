from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.main_dependencies import require_role

router = APIRouter(prefix="/adherence", tags=["adherence"])


class AdherenceUpdate(BaseModel):
    patient_id: int
    taken: bool
    taken_time: str  # ISO string
    remarks: str | None = None


@router.post("/update", dependencies=[Depends(require_role("patient"))])
def update_adherence(payload: AdherenceUpdate):
    from datetime import datetime

    from backend.database.postgres import SessionLocal
    from backend.models.clinic_models import MedicationAdherence, Patient

    db = SessionLocal()
    try:
        patient = db.get(Patient, payload.patient_id)
        if not patient:
            return {"saved": False, "error": "patient not found"}

        try:
            taken_time = datetime.fromisoformat(payload.taken_time.replace("Z", "+00:00"))
        except ValueError:
            return {"saved": False, "error": "taken_time must be ISO 8601"}

        event = MedicationAdherence(
            patient_id=payload.patient_id,
            taken=payload.taken,
            taken_time=taken_time,
            remarks=payload.remarks,
            created_at=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        return {
            "saved": True,
            "adherence": {
                "id": event.id,
                "patient_id": event.patient_id,
                "taken": event.taken,
                "taken_time": event.taken_time.isoformat(),
                "remarks": event.remarks,
            },
        }
    finally:
        db.close()

