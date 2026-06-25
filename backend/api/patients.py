from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.database.postgres import SessionLocal
from backend.main_dependencies import get_current_user_payload, require_role
from backend.models.clinic_models import Patient
from backend.models.user import User

router = APIRouter(prefix="/patients", tags=["patients"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _patient_to_dict(patient: Patient) -> dict:
    return {
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
        "user_id": patient.user_id,
        "created_at": patient.created_at.isoformat(),
    }


@router.get("/my-patient", dependencies=[Depends(require_role("patient"))])
def get_my_patient(payload=Depends(get_current_user_payload), db=Depends(get_db)):
    user_id = int(payload.get("sub"))
    patient = db.execute(select(Patient).where(Patient.user_id == user_id)).scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="No patient record linked to this user")
    return {"patient": _patient_to_dict(patient)}


@router.get("", dependencies=[Depends(require_role("provider", "nurse", "patient"))])
def list_patients(
    payload=Depends(get_current_user_payload),
    db=Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    role = payload.get("role")
    user_id = int(payload.get("sub"))

    base_filter = (Patient.user_id == user_id) if role == "patient" else None

    count_stmt = select(Patient.id)
    if base_filter is not None:
        count_stmt = count_stmt.where(base_filter)
    total = len(db.execute(count_stmt).scalars().all())

    stmt = select(Patient)
    if base_filter is not None:
        stmt = stmt.where(base_filter)
    patients = db.execute(stmt.offset(offset).limit(limit)).scalars().all()

    return {
        "patients": [_patient_to_dict(p) for p in patients],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{patient_id}", dependencies=[Depends(require_role("provider", "nurse", "patient"))])
def get_patient(patient_id: int, payload=Depends(get_current_user_payload), db=Depends(get_db)):
    role = payload.get("role")
    user_id = int(payload.get("sub"))
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if role == "patient" and patient.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"patient": _patient_to_dict(patient)}


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
    user_id: int | None = None


@router.post("", dependencies=[Depends(require_role("provider"))])
def create_patient(payload: PatientCreate):
    from datetime import datetime
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
            user_id=payload.user_id,
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
                "user_id": patient.user_id,
            },
        }
    finally:
        db.close()

