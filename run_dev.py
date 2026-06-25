"""Development server: serves both backend API and frontend static files."""
import os, sys, uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="TB Monitoring Dev Server")

from backend.api import auth, patients, symptoms, adherence, alerts, reports
from backend.database.postgres import init_db
from backend.database.seed_data import seed_default_users
from backend.websocket.chat import router as chat_router

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    init_db()
    seed_default_users()

app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(symptoms.router, prefix="/api")
app.include_router(adherence.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# Serve frontend static files from /frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(os.path.dirname(__file__), 'dev.db').replace(os.sep, '/')}"
    os.environ.setdefault("DATABASE_URL", db_url)
    os.environ.setdefault("JWT_SECRET_KEY", "dev_secret_key_change_in_prod")
    print(f"Starting dev server with DB: {db_url}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
