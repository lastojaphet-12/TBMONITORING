import os, sys
os.environ["DATABASE_URL"] = "sqlite:///./test6.db"
os.environ["JWT_SECRET_KEY"] = "test"
sys.path.insert(0, os.path.dirname(__file__))

try:
    from backend.app import app
    print("App imported OK")
    
    # Manually run startup
    from backend.database.postgres import init_db
    init_db()
    print("init_db OK")
    
    # Now serve via uvicorn
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8771, log_level="info", lifespan="on")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
