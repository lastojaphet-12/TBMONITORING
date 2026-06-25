from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# NOTE: We import Base from backend.models.user to ensure a single declarative base.
from backend.models.user import Base, Role, User  # noqa: F401


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tb_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), index=True)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime)

    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    village: Mapped[str | None] = mapped_column(String(120), nullable=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True, index=True)
    provider_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    nurse_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id])
    provider: Mapped[User | None] = relationship("User", foreign_keys=[provider_id])
    nurse: Mapped[User | None] = relationship("User", foreign_keys=[nurse_id])

    symptom_reports: Mapped[list[SymptomReport]] = relationship(
        "SymptomReport", back_populates="patient", cascade="all, delete-orphan"
    )
    adherence_events: Mapped[list[MedicationAdherence]] = relationship(
        "MedicationAdherence", back_populates="patient", cascade="all, delete-orphan"
    )


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)

    medication_name: Mapped[str] = mapped_column(String(150), index=True)

    # Times per day, used to generate schedule slots.
    doses_per_day: Mapped[int] = mapped_column(Integer, default=1)

    # Example: 3 time/day => store default per-day dose times (24h clock) as strings.
    dose_time_1: Mapped[str | None] = mapped_column(String(5), nullable=True)
    dose_time_2: Mapped[str | None] = mapped_column(String(5), nullable=True)
    dose_time_3: Mapped[str | None] = mapped_column(String(5), nullable=True)

    instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Active window.
    start_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped[Patient] = relationship("Patient")
    schedules: Mapped[list[MedicationSchedule]] = relationship(
        "MedicationSchedule", back_populates="prescription", cascade="all, delete-orphan"
    )


class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), index=True)

    # One schedule row represents one dose time each day.
    # For example: time_slot='08:00', day_offset=0
    time_slot: Mapped[str] = mapped_column(String(5), index=True)
    day_offset: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prescription: Mapped[Prescription] = relationship("Prescription", back_populates="schedules")


class SymptomReport(Base):
    __tablename__ = "symptom_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)

    cough_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_in_sputum: Mapped[bool] = mapped_column(Boolean, default=False)
    chest_pain: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fever: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    night_sweats: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fatigue: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    weight_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    breathing_difficulty: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    oxygen_saturation: Mapped[float] = mapped_column(Float, default=98.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped[Patient] = relationship("Patient", back_populates="symptom_reports")


class MedicationAdherence(Base):
    __tablename__ = "medication_adherence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    prescription_id: Mapped[int | None] = mapped_column(ForeignKey("prescriptions.id"), nullable=True)

    taken: Mapped[bool] = mapped_column(Boolean, default=False)
    taken_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    remarks: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped[Patient] = relationship("Patient", back_populates="adherence_events")


class AlertStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class AlertType(str, enum.Enum):
    medication_alert = "medication_alert"
    followup_alert = "followup_alert"
    critical_tb_alert = "critical_tb_alert"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), index=True, nullable=True)

    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), index=True)
    severity: Mapped[str] = mapped_column(String(30), default="low")
    message: Mapped[str] = mapped_column(String(1000))

    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.open, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ChatRoomType(str, enum.Enum):
    patient_team = "patient_team"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_type: Mapped[ChatRoomType] = mapped_column(Enum(ChatRoomType), index=True)

    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True, index=True)

    provider_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    nurse_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Prevent duplicates for same team.
    __table_args__ = (
        UniqueConstraint("room_type", "patient_id", "provider_id", "nurse_id", name="uq_room_team"),
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id"), index=True)

    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(String(2000))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped[ChatRoom] = relationship("ChatRoom")


class ReminderCategory(str, enum.Enum):
    medication = "medication"
    symptoms_followup = "symptoms_followup"


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), index=True)

    category: Mapped[ReminderCategory] = mapped_column(Enum(ReminderCategory), index=True)
    message: Mapped[str] = mapped_column(String(1000))

    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    language: Mapped[str] = mapped_column(String(20), default="en")
    theme: Mapped[str] = mapped_column(String(20), default="light")

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

