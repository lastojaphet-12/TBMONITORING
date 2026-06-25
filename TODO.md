# TODO

- [x] Create real DB-backed implementations for missing backend endpoints:
  - [x] `POST /api/patients` in `backend/api/patients.py`
  - [x] `POST /api/adherence/update` in `backend/api/adherence.py`
  - [x] `GET /api/reports/patient/{patient_id}` in `backend/api/reports.py`
- [x] Verify frontend pages match backend route prefixes/payloads:
  - [x] `frontend/provider/register_patient.html` → `POST /api/patients`
  - [x] `frontend/patient/medication.html` → `POST /api/adherence/update`
  - [x] `frontend/nurse/reports.html` → `GET /api/reports/patient/{patient_id}`
- [x] Run smoke tests by starting docker compose and calling endpoints.
  - All 12 endpoint tests pass (health, register, login, me, create patient, symptoms, adherence, alerts, resolve, patient report)

