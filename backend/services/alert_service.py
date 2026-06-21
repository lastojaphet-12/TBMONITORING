from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AlertDraft:
    alert_type: str
    severity: str
    message: str


def medication_alert_if_missing(last_med_time: datetime | None) -> AlertDraft | None:
    if last_med_time is None:
        return AlertDraft(
            alert_type="medication_alert",
            severity="medium",
            message="No medication recorded within the last 24 hours.",
        )

    if datetime.utcnow() - last_med_time > timedelta(hours=24):
        return AlertDraft(
            alert_type="medication_alert",
            severity="medium",
            message="No medication recorded within 24 hours.",
        )
    return None


def followup_alert_if_missing(last_symptom_report_time: datetime | None) -> AlertDraft | None:
    if last_symptom_report_time is None:
        return AlertDraft(
            alert_type="followup_alert",
            severity="low",
            message="No symptom report for 3 days. Please submit an update.",
        )

    if datetime.utcnow() - last_symptom_report_time > timedelta(days=3):
        return AlertDraft(
            alert_type="followup_alert",
            severity="low",
            message="No symptom report for 3 days. Please submit an update.",
        )
    return None


def critical_tb_alert(*, blood_in_sputum: bool, oxygen_saturation: float) -> AlertDraft | None:
    if blood_in_sputum and oxygen_saturation < 92.0:
        return AlertDraft(
            alert_type="critical_tb_alert",
            severity="critical",
            message="Critical TB alert: blood in sputum with oxygen saturation below 92%. Immediate nurse intervention required.",
        )
    return None

