# TODO

- [ ] Create real DB-backed implementations for missing backend endpoints:
  - [ ] `POST /api/patients` in `backend/api/patients.py`
  - [ ] `POST /api/adherence/update` in `backend/api/adherence.py`
  - [ ] `GET /api/reports/patient/{patient_id}` in `backend/api/reports.py`
- [ ] Verify frontend pages match backend route prefixes/payloads:
  - [ ] `frontend/provider/register_patient.html`
  - [ ] `frontend/patient/medication.html`
  - [ ] `frontend/nurse/reports.html`
- [ ] Run smoke tests by starting docker compose and calling endpoints.

