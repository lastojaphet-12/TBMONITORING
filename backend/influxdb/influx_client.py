from influxdb_client import InfluxDBClient, Point

from backend.config import settings


class InfluxClient:
    def __init__(self):
        self.client = InfluxDBClient(
            url=settings.influx_url,
            token=settings.influx_token,
            org=settings.influx_org,
        )
        self.bucket = settings.influx_bucket

    def write_monitoring_point(
        self,
        *,
        patient_id: str,
        nurse_id: str | None,
        district: str | None,
        village: str | None,
        weight: float | None = None,
        temperature: float | None = None,
        oxygen_level: float | None = None,
        heart_rate: int | None = None,
        respiratory_rate: int | None = None,
        symptom_score: int | None = None,
        risk_score: int | None = None,
        adherence_score: int | None = None,
    ) -> None:
        p = Point("patient_monitoring")
        p = p.tag("patient_id", patient_id)
        if nurse_id:
            p = p.tag("nurse_id", nurse_id)
        if district:
            p = p.tag("district", district)
        if village:
            p = p.tag("village", village)

        if weight is not None:
            p = p.field("weight", float(weight))
        if temperature is not None:
            p = p.field("temperature", float(temperature))
        if oxygen_level is not None:
            p = p.field("oxygen_level", float(oxygen_level))
        if heart_rate is not None:
            p = p.field("heart_rate", int(heart_rate))
        if respiratory_rate is not None:
            p = p.field("respiratory_rate", int(respiratory_rate))
        if symptom_score is not None:
            p = p.field("symptom_score", int(symptom_score))
        if risk_score is not None:
            p = p.field("risk_score", int(risk_score))
        if adherence_score is not None:
            p = p.field("adherence_score", int(adherence_score))

        write_api = self.client.write_api()
        write_api.write(bucket=self.bucket, org=settings.influx_org, record=p)

