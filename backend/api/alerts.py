from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgres import SessionLocal
from backend.main_dependencies import get_current_user_payload, require_role
from backend.models.clinic_models import Alert, AlertStatus, Patient


router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", dependencies=[Depends(require_role("nurse", "provider", "patient"))])
def list_alerts(payload=Depends(get_current_user_payload), db: Session = Depends(get_db)):
    role = payload.get("role")
    stmt = select(Alert).where(Alert.status == AlertStatus.open)

    if role == "patient":
        user_id = int(payload.get("sub"))
        patient = db.execute(select(Patient).where(Patient.user_id == user_id)).scalar_one_or_none()
        if patient:
            stmt = stmt.where(Alert.patient_id == patient.id)
        else:
            return {"alerts": []}

    stmt = stmt.order_by(Alert.created_at.desc()).limit(200)
    alerts = list(db.scalars(stmt).all())

    return {
        "alerts": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "alert_type": a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
                "severity": a.severity,
                "message": a.message,
                "status": a.status.value if hasattr(a.status, "value") else str(a.status),
                "created_at": (a.created_at.isoformat() if a.created_at is not None else None),

            }
            for a in alerts
        ]
    }


@router.post("/{alert_id}/resolve", dependencies=[Depends(require_role("nurse"))])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status != AlertStatus.resolved:
        alert.status = AlertStatus.resolved
        alert.resolved_at = datetime.utcnow()
        db.add(alert)
        db.commit()

    return {"resolved": True, "alert_id": alert_id}


