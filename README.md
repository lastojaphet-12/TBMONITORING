# Digital Chronic TB Remote Monitoring System

This repository contains a reference implementation skeleton for a web-based Digital Chronic Tuberculosis (TB) Remote Monitoring System.

## Tech
- Frontend: HTML/CSS/JS, Bootstrap 5
- Backend: Python 3.12+, FastAPI
- DB: PostgreSQL (SQLAlchemy + Alembic)
- Time-series: InfluxDB (client stub included)
- Auth: JWT
- Realtime: WebSocket (chat stub)
- Deployment: Docker + docker-compose

## Development
### Prerequisites
- Docker & docker-compose

### Run
```bash
docker compose up --build
```

Backend should become available at:
- `http://localhost:8000/health`

## Project structure
See `/backend` and `/frontend` directories.

