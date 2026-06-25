import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, select

from backend.database.postgres import SessionLocal
from backend.influxdb.influx_client import InfluxClient
from backend.main_dependencies import require_role
from backend.models.clinic_models import MedicationAdherence, Patient

logger = logging.getLogger(__name__)
influx = InfluxClient()

router = APIRouter(prefix="/adherence", tags=["adherence"])


class AdherenceUpdate(BaseModel):
    patient_id: int
    taken: bool
    taken_time: str  # ISO string
    remarks: str | None = None


@router.get("/history/{patient_id}", dependencies=[Depends(require_role("patient", "nurse", "provider"))])
def adherence_history(patient_id: int):
    db = SessionLocal()
    try:
        events = db.scalars(
            select(MedicationAdherence)
            .where(MedicationAdherence.patient_id == patient_id)
            .order_by(desc(MedicationAdherence.taken_time))
            .limit(50)
        ).all()
        return {
            "adherence": [
                {
                    "id": e.id,
                    "taken": e.taken,
                    "taken_time": e.taken_time.isoformat(),
                    "remarks": e.remarks,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ]
        }
    finally:
        db.close()


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

        # Write monitoring data to InfluxDB (fire-and-forget, ignore errors)
        try:
            influx.write_monitoring_point(
                patient_id=str(payload.patient_id),
                nurse_id=str(patient.nurse_id) if patient.nurse_id else None,
                district=patient.district,
                village=patient.village,
            )
        except Exception:
            logger.warning("InfluxDB write failed", exc_info=True)

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

