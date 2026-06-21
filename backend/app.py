from fastapi import FastAPI

from backend.api import auth, patients, symptoms, adherence, alerts, reports
from backend.database.postgres import init_db
from backend.websocket.chat import router as chat_router

app = FastAPI(title="Digital Chronic TB Remote Monitoring System")



@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(symptoms.router, prefix="/api")
app.include_router(adherence.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# WebSocket Routers
app.include_router(chat_router, prefix="/api")



