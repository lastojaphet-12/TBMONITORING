"""Initial schema - all core tables.

Revision ID: 0001
Revises:
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(150), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("provider", "nurse", "patient", name="role"), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(255), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("used", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("theme", sa.String(20), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tb_number", sa.String(64), nullable=True),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("gender", sa.Enum("male", "female", "other", name="gender"), nullable=True),
        sa.Column("date_of_birth", sa.DateTime(), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("district", sa.String(120), nullable=True),
        sa.Column("village", sa.String(120), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("nurse_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["nurse_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tb_number"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_patients_tb_number", "patients", ["tb_number"])
    op.create_index("ix_patients_full_name", "patients", ["full_name"])
    op.create_index("ix_patients_gender", "patients", ["gender"])

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("medication_name", sa.String(150), nullable=True),
        sa.Column("doses_per_day", sa.Integer(), nullable=True),
        sa.Column("dose_time_1", sa.String(5), nullable=True),
        sa.Column("dose_time_2", sa.String(5), nullable=True),
        sa.Column("dose_time_3", sa.String(5), nullable=True),
        sa.Column("instructions", sa.String(500), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"])
    op.create_index("ix_prescriptions_medication_name", "prescriptions", ["medication_name"])

    op.create_table(
        "medication_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prescription_id", sa.Integer(), nullable=True),
        sa.Column("time_slot", sa.String(5), nullable=True),
        sa.Column("day_offset", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medication_schedules_prescription_id", "medication_schedules", ["prescription_id"])
    op.create_index("ix_medication_schedules_time_slot", "medication_schedules", ["time_slot"])

    op.create_table(
        "symptom_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("cough_duration", sa.Integer(), nullable=True),
        sa.Column("blood_in_sputum", sa.Boolean(), nullable=True),
        sa.Column("chest_pain", sa.Boolean(), nullable=True),
        sa.Column("fever", sa.Boolean(), nullable=True),
        sa.Column("night_sweats", sa.Boolean(), nullable=True),
        sa.Column("fatigue", sa.Boolean(), nullable=True),
        sa.Column("weight_loss", sa.Float(), nullable=True),
        sa.Column("breathing_difficulty", sa.Boolean(), nullable=True),
        sa.Column("oxygen_saturation", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_symptom_reports_patient_id", "symptom_reports", ["patient_id"])

    op.create_table(
        "medication_adherence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("prescription_id", sa.Integer(), nullable=True),
        sa.Column("taken", sa.Boolean(), nullable=True),
        sa.Column("taken_time", sa.DateTime(), nullable=True),
        sa.Column("remarks", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_medication_adherence_patient_id", "medication_adherence", ["patient_id"])
    op.create_index("ix_medication_adherence_taken_time", "medication_adherence", ["taken_time"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("alert_type", sa.Enum("medication_alert", "followup_alert", "critical_tb_alert", name="alerttype"), nullable=True),
        sa.Column("severity", sa.String(30), nullable=True),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.Column("status", sa.Enum("open", "resolved", name="alertstatus"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_patient_id", "alerts", ["patient_id"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_status", "alerts", ["status"])

    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_type", sa.Enum("patient_team", name="chatroomtype"), nullable=True),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("nurse_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["nurse_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_type", "patient_id", "provider_id", "nurse_id", name="uq_room_team"),
    )
    op.create_index("ix_chat_rooms_room_type", "chat_rooms", ["room_type"])
    op.create_index("ix_chat_rooms_patient_id", "chat_rooms", ["patient_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=True),
        sa.Column("sender_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(2000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["chat_rooms.id"],),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["room_id"])
    op.create_index("ix_chat_messages_sender_id", "chat_messages", ["sender_id"])

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.Enum("medication", "symptoms_followup", name="remindercategory"), nullable=True),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminders_patient_id", "reminders", ["patient_id"])
    op.create_index("ix_reminders_category", "reminders", ["category"])
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"])


def downgrade() -> None:
    op.drop_table("reminders")
    op.drop_table("chat_messages")
    op.drop_table("chat_rooms")
    op.drop_table("alerts")
    op.drop_table("medication_adherence")
    op.drop_table("symptom_reports")
    op.drop_table("medication_schedules")
    op.drop_table("prescriptions")
    op.drop_table("patients")
    op.drop_table("user_settings")
    op.drop_table("password_reset_tokens")
    op.drop_table("users")

    sa.Enum("provider", "nurse", "patient", name="role").drop(op.get_bind(), checkfirst=True)
    sa.Enum("male", "female", "other", name="gender").drop(op.get_bind(), checkfirst=True)
    sa.Enum("medication_alert", "followup_alert", "critical_tb_alert", name="alerttype").drop(op.get_bind(), checkfirst=True)
    sa.Enum("open", "resolved", name="alertstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum("patient_team", name="chatroomtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum("medication", "symptoms_followup", name="remindercategory").drop(op.get_bind(), checkfirst=True)
