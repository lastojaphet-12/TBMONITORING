import subprocess, time, sys, os, json, urllib.request, urllib.parse, socket

BASE = "http://127.0.0.1:8765"
PORT = 8765

CWD = os.getcwd()
DB_FILE = os.path.join(CWD, f"smoke_{os.getpid()}.db")
DB_URL = f"sqlite:///{DB_FILE.replace(os.sep, '/')}"
os.environ["DATABASE_URL"] = DB_URL
os.environ["JWT_SECRET_KEY"] = "test"
print(f"[test] Using DB: {DB_FILE}", flush=True)

def kill_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex(("127.0.0.1", port)) == 0:
        print(f"[test] Port {port} in use, freeing...", flush=True)
        if sys.platform == "win32":
            subprocess.run(
                ['powershell', '-Command',
                 f'Get-NetTCPConnection -LocalPort {port} | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}'],
                capture_output=True, timeout=5,
            )
        else:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=5)
        time.sleep(2)
    sock.close()

kill_port(PORT)

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app:app",
     "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    env={**os.environ, "DATABASE_URL": DB_URL, "JWT_SECRET_KEY": "test"},
)

for _attempt in range(30):
    time.sleep(1)
    try:
        r = urllib.request.urlopen(f"{BASE}/health", timeout=3)
        if r.status == 200:
            break
    except Exception:
        continue
else:
    print("[test] FAIL: Server did not start in time", flush=True)
    proc.terminate(); proc.wait()
    sys.exit(1)

print(f"[test] DB exists: {os.path.exists(DB_FILE)}", flush=True)

def req(method, path, headers=None, body=None):
    data = json.dumps(body).encode() if body else None
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body.decode()
    except Exception as e:
        return 0, str(e)

passed = 0
failed = 0

def check(name, status, expected_status, predicate=None):
    global passed, failed
    ok = status == expected_status and (predicate is None or predicate())
    if ok:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}  (status={status})")
        failed += 1

# 1. Health
print("\n=== Health ===")
s, d = req("GET", "/health")
check("/health", s, 200, lambda: d.get("status") == "ok")

# 2. Register
print("\n=== Register ===")
s, d = req("POST", "/api/auth/register", body={"username":"dr_provider","password":"pass123","role":"provider"})
check("register provider", s, 201, lambda: d.get("id") is not None)
PROVIDER_ID = d.get("id")

s, d = req("POST", "/api/auth/register", body={"username":"nurse_anna","password":"pass123","role":"nurse"})
check("register nurse", s, 201, lambda: d.get("id") is not None)
NURSE_ID = d.get("id")

s, d = req("POST", "/api/auth/register", body={"username":"patient_john","password":"pass123","role":"patient"})
check("register patient_user", s, 201, lambda: d.get("id") is not None)
PATIENT_USER_ID = d.get("id")

# 3. Login
print("\n=== Login ===")
form = urllib.parse.urlencode({"username":"dr_provider","password":"pass123"}).encode()
r = urllib.request.Request(f"{BASE}/api/auth/login", data=form,
    headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
resp = urllib.request.urlopen(r, timeout=10)
login_data = json.loads(resp.read())
TOKEN = login_data.get("access_token","")
check("login provider", resp.status, 200, lambda: bool(TOKEN))

# 4. /me
print("\n=== Me ===")
s, d = req("GET", "/api/auth/me", headers={"Authorization": f"Bearer {TOKEN}"})
check("/me", s, 200, lambda: d.get("username") == "dr_provider")

# 5. Create patient
print("\n=== Create Patient ===")
s, d = req("POST", "/api/patients", headers={"Authorization": f"Bearer {TOKEN}"}, body={
    "tb_number": "TB-001",
    "full_name": "John Doe",
    "gender": "male",
    "date_of_birth": "1990-01-15",
    "phone": "+250700000000",
    "district": "Kigali",
    "village": "Kimironko",
    "provider_id": PROVIDER_ID,
    "user_id": PATIENT_USER_ID,
})
check("create patient", s, 200, lambda: d.get("created") is True and d.get("patient",{}).get("id") is not None)
PATIENT_ID = d.get("patient",{}).get("id")

# 6. Submit symptoms
print("\n=== Submit Symptoms ===")
s, d = req("POST", "/api/symptoms/report", headers={"Authorization": f"Bearer {TOKEN}"}, body={
    "patient_id": PATIENT_ID,
    "cough_duration": 7,
    "blood_in_sputum": True,
    "chest_pain": True,
    "fever": True,
    "oxygen_saturation": 89.0,
})
check("submit symptoms", s, 200, lambda: d.get("saved") is True)
if s == 200:
    print(f"    risk: {d.get('risk',{}).get('risk_level')} (score={d.get('risk',{}).get('risk_score')})")
    print(f"    alerts: {len(d.get('created_alerts',[]))}")

# 7. Adherence update
print("\n=== Adherence Update ===")
form2 = urllib.parse.urlencode({"username":"patient_john","password":"pass123"}).encode()
r2 = urllib.request.Request(f"{BASE}/api/auth/login", data=form2,
    headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
resp2 = urllib.request.urlopen(r2, timeout=10)
TOKEN_PATIENT = json.loads(resp2.read())["access_token"]

s, d = req("POST", "/api/adherence/update", headers={"Authorization": f"Bearer {TOKEN_PATIENT}"}, body={
    "patient_id": PATIENT_ID,
    "taken": True,
    "taken_time": "2026-06-22T10:00:00Z",
    "remarks": "took with food",
})
check("adherence update", s, 200, lambda: d.get("saved") is True)

# 8. List alerts
print("\n=== Alerts ===")
s, d = req("GET", "/api/alerts", headers={"Authorization": f"Bearer {TOKEN}"})
check("list alerts", s, 200, lambda: len(d.get("alerts",[])) > 0)
if s == 200:
    print(f"    alert count: {len(d.get('alerts',[]))}")

# 9. Patient report
print("\n=== Patient Report ===")
s, d = req("GET", f"/api/reports/patient/{PATIENT_ID}", headers={"Authorization": f"Bearer {TOKEN}"})
check("patient report", s, 200, lambda: d.get("report") is not None)

print(f"\n{'='*40}")
print(f"Passed: {passed}, Failed: {failed}")

proc.terminate()
proc.wait()

try:
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
except Exception:
    pass

sys.exit(0 if failed == 0 else 1)
