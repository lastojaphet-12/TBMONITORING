from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.main_dependencies import require_role

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    tb_number: str
    full_name: str
    gender: str
    date_of_birth: str
    phone: str | None = None
    district: str | None = None
    village: str | None = None
    provider_id: int | None = None
    nurse_id: int | None = None


@router.post("", dependencies=[Depends(require_role("provider"))])
def create_patient(payload: PatientCreate):
    from datetime import datetime
    from sqlalchemy import select

    from backend.database.postgres import SessionLocal
    from backend.models.clinic_models import Patient
    from backend.models.user import User

    db = SessionLocal()
    try:
        provider = None
        nurse = None

        if payload.provider_id is not None:
            provider = db.get(User, payload.provider_id)
            if not provider or provider.role != provider.role.__class__("provider"):
                # role check conservative; if stored role matches string enum values this is still OK
                if not provider:
                    return {"created": False, "error": "provider not found"}
                if getattr(provider, "role", None).value != "provider":
                    return {"created": False, "error": "provider_id must belong to a provider user"}

        if payload.nurse_id is not None:
            nurse = db.get(User, payload.nurse_id)
            if not nurse:
                return {"created": False, "error": "nurse not found"}
            if getattr(nurse, "role", None).value != "nurse":
                return {"created": False, "error": "nurse_id must belong to a nurse user"}

        existing = db.execute(select(Patient).where(Patient.tb_number == payload.tb_number)).scalar_one_or_none()
        if existing:
            return {"created": False, "error": "tb_number already exists"}

        dt = datetime.fromisoformat(payload.date_of_birth)
        patient = Patient(
            tb_number=payload.tb_number,
            full_name=payload.full_name,
            gender=payload.gender,
            date_of_birth=dt,
            phone=payload.phone,
            district=payload.district,
            village=payload.village,
            provider_id=payload.provider_id,
            nurse_id=payload.nurse_id,
            created_at=datetime.utcnow(),
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        return {
            "created": True,
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
        }
    finally:
        db.close()

