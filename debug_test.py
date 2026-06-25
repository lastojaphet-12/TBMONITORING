import os, sys, time, json, urllib.request, urllib.error, threading
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test2.db"
os.environ["JWT_SECRET_KEY"] = "test"

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from backend.app import app

def run():
    uvicorn.run(app, host="127.0.0.1", port=8768, log_level="info")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(3)

BASE = "http://127.0.0.1:8768"

def req(method, path, headers=None, body=None):
    data = json.dumps(body).encode() if body else None
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.headers.get("Content-Type","").startswith("application/json") else e.read().decode()

s, d = req("GET", "/health")
print(f"health: {s} {d}")

s, d = req("POST", "/api/auth/register", body={"username":"dr_provider","password":"pass123","role":"provider"})
print(f"register: {s}")
if s != 201:
    print(f"  error body: {d}")
else:
    print(f"  id={d.get('id')}")
    print(f"  success={d}")

# Try login
form = urllib.parse.urlencode({"username":"dr_provider","password":"pass123"}).encode()
r = urllib.request.Request(f"{BASE}/api/auth/login", data=form, headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
resp = urllib.request.urlopen(r)
ld = json.loads(resp.read())
print(f"login: {resp.status}, token={bool(ld.get('access_token'))}")
TOKEN = ld["access_token"]

# Create patient
s, d = req("POST", "/api/patients", headers={"Authorization": f"Bearer {TOKEN}"}, body={
    "tb_number": "TB-001", "full_name": "John Doe", "gender": "male",
    "date_of_birth": "1990-01-15", "phone": "+250700000000", "district": "Kigali", "village": "Kimironko",
})
print(f"create patient: {s} {json.dumps(d, indent=2)[:200]}")
