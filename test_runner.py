import os, sys, time, json, urllib.request, urllib.error, urllib.parse, subprocess

wd = os.path.dirname(os.path.abspath(__file__))
os.chdir(wd)

DB_FILE = f"test_{int(time.time())}.db"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", "8775", "--log-level", "warning"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env={**os.environ, "DATABASE_URL": f"sqlite:///./{DB_FILE}", "JWT_SECRET_KEY": "test"},
    cwd=wd
)

# Wait for server to be ready
for i in range(30):
    time.sleep(1)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8775/health", timeout=2)
        if r.status == 200:
            print("Server ready")
            break
    except:
        if i == 0:
            print("Waiting for server...")
else:
    print("Server failed to start")
    proc.terminate()
    out = proc.stdout.read(4096).decode(errors="replace")
    print("Output:", out[:2000])
    sys.exit(1)

BASE = "http://127.0.0.1:8775"
passed = 0
failed = 0

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
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, str(e)

def test(name, ok):
    global passed, failed
    if ok:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1

print("\n=== 1. Health ===")
s, d = req("GET", "/health")
test("health", s == 200 and d.get("status") == "ok")

print("\n=== 2. Register ===")
s, d = req("POST", "/api/auth/register", body={"username":"dr_provider","password":"pass123","role":"provider"})
test("register provider", s == 201 and d.get("id") == 1)
if s != 201:
    print(f"  Error: {d}")

s, d = req("POST", "/api/auth/register", body={"username":"nurse_anna","password":"pass123","role":"nurse"})
test("register nurse", s == 201)

s, d = req("POST", "/api/auth/register", body={"username":"patient_john","password":"pass123","role":"patient"})
test("register patient", s == 201)

print("\n=== 3. Login ===")
form = urllib.parse.urlencode({"username":"dr_provider","password":"pass123"}).encode()
r = urllib.request.Request(f"{BASE}/api/auth/login", data=form, headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
resp = urllib.request.urlopen(r)
ld = json.loads(resp.read())
TOKEN = ld.get("access_token","")
test("login provider", resp.status == 200 and bool(TOKEN))

print("\n=== 4. Me ===")
s, d = req("GET", "/api/auth/me", headers={"Authorization": f"Bearer {TOKEN}"})
test("/me", s == 200 and d.get("username") == "dr_provider")

print("\n=== 5. Create Patient ===")
s, d = req("POST", "/api/patients", headers={"Authorization": f"Bearer {TOKEN}"}, body={
    "tb_number": "TB-001", "full_name": "John Doe", "gender": "male",
    "date_of_birth": "1990-01-15", "phone": "+250700000000", "district": "Kigali", "village": "Kimironko",
})
test("create patient", s == 200 and d.get("created") is True and d.get("patient",{}).get("id") == 1)
if s == 200:
    print(f"  Patient: {d['patient']['full_name']} (TB#{d['patient']['tb_number']})")
else:
    print(f"  Error: {json.dumps(d, indent=2)[:300]}")

print("\n=== 6. Submit Symptoms (as patient) ===")
form_p = urllib.parse.urlencode({"username":"patient_john","password":"pass123"}).encode()
r_p = urllib.request.Request(f"{BASE}/api/auth/login", data=form_p, headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
TOKEN_SYM = json.loads(urllib.request.urlopen(r_p).read())["access_token"]

s, d = req("POST", "/api/symptoms/report", headers={"Authorization": f"Bearer {TOKEN_SYM}"}, body={
    "patient_id": 1, "cough_duration": 7, "blood_in_sputum": True,
    "chest_pain": True, "fever": True, "oxygen_saturation": 89.0,
})
test("submit symptoms", s == 200 and d.get("saved") is True)
if s != 200:
    print(f"  Error: {d}")
if s == 200:
    print(f"  Risk: {d['risk']['risk_level']} (score={d['risk']['risk_score']})")
    print(f"  Alerts created: {len(d['created_alerts'])}")

print("\n=== 7. Adherence Update ===")
form2 = urllib.parse.urlencode({"username":"patient_john","password":"pass123"}).encode()
r2 = urllib.request.Request(f"{BASE}/api/auth/login", data=form2, headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
resp2 = urllib.request.urlopen(r2)
TOKEN_P = json.loads(resp2.read())["access_token"]

s, d = req("POST", "/api/adherence/update", headers={"Authorization": f"Bearer {TOKEN_P}"}, body={
    "patient_id": 1, "taken": True, "taken_time": "2026-06-22T10:00:00Z", "remarks": "took with food",
})
test("adherence update", s == 200 and d.get("saved") is True)

print("\n=== 8. Alerts ===")
s, d = req("GET", "/api/alerts", headers={"Authorization": f"Bearer {TOKEN}"})
test("list alerts", s == 200 and len(d.get("alerts",[])) > 0)
if s == 200:
    print(f"  Alert count: {len(d['alerts'])}")

print("\n=== 9. Resolve Alert (as nurse) ===")
form_n = urllib.parse.urlencode({"username":"nurse_anna","password":"pass123"}).encode()
r_n = urllib.request.Request(f"{BASE}/api/auth/login", data=form_n, headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
TOKEN_N = json.loads(urllib.request.urlopen(r_n).read())["access_token"]
alert_id = d["alerts"][0]["id"]
s, d = req("POST", f"/api/alerts/{alert_id}/resolve", headers={"Authorization": f"Bearer {TOKEN_N}"})
test("resolve alert", s == 200 and d.get("resolved") is True)

print("\n=== 10. Patient Report ===")
s, d = req("GET", "/api/reports/patient/1", headers={"Authorization": f"Bearer {TOKEN}"})
test("patient report", s == 200 and d.get("report") is not None)

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed")

proc.terminate()
proc.wait()
sys.exit(0 if failed == 0 else 1)
