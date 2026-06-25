from datetime import datetime, timedelta

from sqlalchemy import select

from backend.api.auth import hash_password
from backend.database.postgres import SessionLocal
from backend.models.clinic_models import (
    Alert,
    AlertStatus,
    AlertType,
    Gender,
    MedicationAdherence,
    Patient,
    Prescription,
    SymptomReport,
)
from backend.models.user import User, Role


import logging

logger = logging.getLogger(__name__)


def _upsert_user(db, username, password, role):
    existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _upsert_patient(db, tb_number, **kwargs):
    existing = db.execute(select(Patient).where(Patient.tb_number == tb_number)).scalar_one_or_none()
    if existing:
        return existing
    patient = Patient(tb_number=tb_number, **kwargs)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def seed_default_users() -> None:
    db = SessionLocal()
    try:
        created_users = 0
        created_patients = 0

        # ── Providers ──
        provider1 = _upsert_user(db, "provider1", "provider123", Role.provider)
        created_users += 1
        provider2 = _upsert_user(db, "drmwangi", "provider123", Role.provider)
        created_users += 1
        provider3 = _upsert_user(db, "drkisaka", "provider123", Role.provider)
        created_users += 1

        # ── Nurses ──
        nurse1 = _upsert_user(db, "nurse1", "nurse123", Role.nurse)
        created_users += 1
        nurse2 = _upsert_user(db, "neema", "nurse123", Role.nurse)
        created_users += 1
        nurse3 = _upsert_user(db, "asha", "nurse123", Role.nurse)
        created_users += 1

        # ── Patient Users ──
        patient_users = {}
        for uname, pw in [
            ("patient1", "patient123"),
            ("pascal", "patient123"),
            ("juma", "patient123"),
            ("rehema", "patient123"),
            ("baraka", "patient123"),
            ("zainabu", "patient123"),
            ("abdullah", "patient123"),
            ("esther", "patient123"),
        ]:
            u = _upsert_user(db, uname, pw, Role.patient)
            created_users += 1
            patient_users[uname] = u

        logger.info("Seeded %d user(s)", created_users)

        # ── Patients ──
        patients_data = [
            dict(
                tb_number="TB-001",
                full_name="Pascal Jumanne",
                gender=Gender.male,
                date_of_birth=datetime(1985, 3, 12),
                phone="+255712100001",
                district="Arusha",
                village="Sokoni",
                user_id=patient_users["pascal"].id,
                provider_id=provider1.id,
                nurse_id=nurse1.id,
            ),
            dict(
                tb_number="TB-002",
                full_name="Neema Mushi",
                gender=Gender.female,
                date_of_birth=datetime(1992, 7, 25),
                phone="+255712100002",
                district="Mwanza",
                village="Mkuyuni",
                user_id=patient_users["patient1"].id,
                provider_id=provider1.id,
                nurse_id=nurse2.id,
            ),
            dict(
                tb_number="TB-003",
                full_name="Juma Hassan",
                gender=Gender.male,
                date_of_birth=datetime(1978, 11, 3),
                phone="+255712100003",
                district="Dar es Salaam",
                village="Kariakoo",
                user_id=patient_users["juma"].id,
                provider_id=provider2.id,
                nurse_id=nurse2.id,
            ),
            dict(
                tb_number="TB-004",
                full_name="Rehema Maganga",
                gender=Gender.female,
                date_of_birth=datetime(1995, 1, 18),
                phone="+255712100004",
                district="Mbeya",
                village="Iyela",
                user_id=patient_users["rehema"].id,
                provider_id=provider2.id,
                nurse_id=nurse3.id,
            ),
            dict(
                tb_number="TB-005",
                full_name="Baraka Charles",
                gender=Gender.male,
                date_of_birth=datetime(1988, 9, 30),
                phone="+255712100005",
                district="Dodoma",
                village="Majengo",
                user_id=patient_users["baraka"].id,
                provider_id=provider3.id,
                nurse_id=nurse1.id,
            ),
            dict(
                tb_number="TB-006",
                full_name="Zainabu Salum",
                gender=Gender.female,
                date_of_birth=datetime(1990, 5, 14),
                phone="+255712100006",
                district="Tanga",
                village="Ngamiani",
                user_id=patient_users["zainabu"].id,
                provider_id=provider3.id,
                nurse_id=nurse3.id,
            ),
            dict(
                tb_number="TB-007",
                full_name="Abdullah Omari",
                gender=Gender.male,
                date_of_birth=datetime(1982, 12, 7),
                phone="+255712100007",
                district="Zanzibar",
                village="Mkunazini",
                user_id=patient_users["abdullah"].id,
                provider_id=provider1.id,
                nurse_id=nurse2.id,
            ),
            dict(
                tb_number="TB-008",
                full_name="Esther Lema",
                gender=Gender.female,
                date_of_birth=datetime(1997, 8, 22),
                phone="+255712100008",
                district="Kilimanjaro",
                village="Mwika",
                user_id=patient_users["esther"].id,
                provider_id=provider2.id,
                nurse_id=nurse3.id,
            ),
        ]

        for pdata in patients_data:
            _upsert_patient(db, **pdata)
            created_patients += 1

        logger.info("Seeded %d patient(s)", created_patients)

        # ── Fetch patients back for related data ──
        patients = {p.full_name: p for p in db.execute(select(Patient)).scalars().all()}

        # ── Symptoms ──
        for patient_name, symptoms in [
            ("Pascal Jumanne", [
                dict(cough_duration=14, blood_in_sputum=True, chest_pain=True, fever=True, oxygen_saturation=88.0),
                dict(cough_duration=10, blood_in_sputum=False, chest_pain=True, fever=False, oxygen_saturation=94.0),
            ]),
            ("Neema Mushi", [
                dict(cough_duration=7, blood_in_sputum=False, chest_pain=False, fever=True, oxygen_saturation=96.0),
            ]),
            ("Juma Hassan", [
                dict(cough_duration=21, blood_in_sputum=True, chest_pain=True, fever=True, night_sweats=True, weight_loss=3.5, oxygen_saturation=85.0),
                dict(cough_duration=18, blood_in_sputum=True, chest_pain=True, fever=True, night_sweats=True, oxygen_saturation=87.0),
                dict(cough_duration=15, blood_in_sputum=False, chest_pain=False, fever=False, oxygen_saturation=92.0),
            ]),
            ("Rehema Maganga", [
                dict(cough_duration=5, blood_in_sputum=False, chest_pain=False, fever=False, oxygen_saturation=98.0),
            ]),
            ("Baraka Charles", [
                dict(cough_duration=10, blood_in_sputum=False, chest_pain=True, fever=True, fatigue=True, oxygen_saturation=91.0),
            ]),
            ("Zainabu Salum", [
                dict(cough_duration=3, blood_in_sputum=False, chest_pain=False, fever=True, oxygen_saturation=97.0),
            ]),
            ("Abdullah Omari", [
                dict(cough_duration=12, blood_in_sputum=True, chest_pain=True, fever=True, night_sweats=True, weight_loss=2.0, oxygen_saturation=86.0),
                dict(cough_duration=9, blood_in_sputum=False, chest_pain=True, fever=False, oxygen_saturation=93.0),
            ]),
            ("Esther Lema", [
                dict(cough_duration=4, blood_in_sputum=False, chest_pain=False, fever=True, fatigue=True, oxygen_saturation=95.0),
            ]),
        ]:
            pt = patients.get(patient_name)
            if not pt:
                continue
            for i, sym in enumerate(symptoms):
                existing = db.execute(
                    select(SymptomReport).where(
                        SymptomReport.patient_id == pt.id,
                        SymptomReport.cough_duration == sym.get("cough_duration"),
                    )
                ).scalar_one_or_none()
                if existing:
                    continue
                db.add(SymptomReport(patient_id=pt.id, **sym))
        db.commit()

        # ── Prescriptions ──
        prescriptions_data = [
            ("Pascal Jumanne", "Rifampin + Isoniazid", 1, "08:00", None, None),
            ("Neema Mushi", "Rifampin + Isoniazid", 1, "08:00", None, None),
            ("Juma Hassan", "Rifampin + Isoniazid + Pyrazinamide", 3, "08:00", "14:00", "20:00"),
            ("Rehema Maganga", "Rifampin + Isoniazid", 1, "08:00", None, None),
            ("Baraka Charles", "Rifampin + Isoniazid", 2, "08:00", "20:00", None),
            ("Zainabu Salum", "Rifampin + Isoniazid", 1, "08:00", None, None),
            ("Abdullah Omari", "Rifampin + Isoniazid + Pyrazinamide", 3, "08:00", "14:00", "20:00"),
            ("Esther Lema", "Rifampin + Isoniazid", 1, "08:00", None, None),
        ]
        for pname, med, doses, t1, t2, t3 in prescriptions_data:
            pt = patients.get(pname)
            if not pt:
                continue
            existing = db.execute(
                select(Prescription).where(
                    Prescription.patient_id == pt.id,
                    Prescription.medication_name == med,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(Prescription(
                patient_id=pt.id,
                medication_name=med,
                doses_per_day=doses,
                dose_time_1=t1,
                dose_time_2=t2,
                dose_time_3=t3,
                start_at=datetime.utcnow() - timedelta(days=30),
            ))
        db.commit()

        # ── Adherence ──
        for pname in patients:
            pt = patients[pname]
            existing = db.execute(
                select(MedicationAdherence).where(MedicationAdherence.patient_id == pt.id)
            ).first()
            if existing:
                continue
            for day in range(7):
                taken = day < 5
                db.add(MedicationAdherence(
                    patient_id=pt.id,
                    taken=taken,
                    taken_time=datetime.utcnow() - timedelta(days=6 - day, hours=8),
                ))
        db.commit()

        # ── Alerts ──
        alerts_data = [
            ("Juma Hassan", AlertType.critical_tb_alert, "high", "Critical TB symptoms detected: prolonged cough with blood, chest pain, fever, night sweats, and weight loss."),
            ("Abdullah Omari", AlertType.critical_tb_alert, "high", "Critical TB symptoms detected: cough with blood, chest pain, fever, night sweats."),
            ("Pascal Jumanne", AlertType.critical_tb_alert, "medium", "Moderate TB symptoms: cough with blood, chest pain, fever. Low oxygen saturation (88%)."),
            ("Baraka Charles", AlertType.followup_alert, "medium", "Follow-up needed: persistent cough and chest pain. Schedule a clinic visit."),
            ("Zainabu Salum", AlertType.followup_alert, "low", "Mild fever reported. Routine follow-up recommended."),
        ]
        for pname, atype, severity, msg in alerts_data:
            pt = patients.get(pname)
            if not pt:
                continue
            existing = db.execute(
                select(Alert).where(
                    Alert.patient_id == pt.id,
                    Alert.alert_type == atype,
                    Alert.message == msg,
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(Alert(
                patient_id=pt.id,
                alert_type=atype,
                severity=severity,
                message=msg,
                status=AlertStatus.open,
            ))
        db.commit()

        logger.info("Seeded related clinical data (symptoms, prescriptions, adherence, alerts)")

    except Exception:
        logger.exception("Failed to seed data")
        raise
    finally:
        db.close()
