# 조립도 작업을 시작할 때 📷 카메라·❄ 모습 기록·✓ 완료 표시를 백업하고 모두 푼다(규칙 00-1, 사용자 지시 2026-11-13).
#   python release_start.py <이름>            → DB(ivs_assembly_cams·poses·status)의 그 조립도 행을 refs/<이름>/_release_backup/<시각>.json 에 저장한 뒤 삭제
#   python release_start.py <이름> --보기     → 지울 개수만 보여 준다(삭제 안 함)
# handoff.py <이름> --아이디 <계정> --시작 이 자동으로 부른다 — 작업을 시작할 때 한 번만 돈다(번호 작업 도중에는 돌리지 않는다: 새로 저장한 값이 지워진다).
import asmpath  # 조립도 파일 자리 연결
import json, os, re, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import userdone
if len(sys.argv) < 2 or sys.argv[1].startswith("--"): sys.exit(__doc__)
name = sys.argv[1]; view = "--보기" in sys.argv
env = userdone._env(); url = (env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")).rstrip("/"); key = env["SUPABASE_SERVICE_ROLE_KEY"]
H = {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=representation"}
def req(method, path):
    r = urllib.request.Request(url + "/rest/v1/" + path, headers=H, method=method)
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode("utf-8") or "[]")
mid = re.search(r'id: "(cubo-[^"]+)"', open(asmpath.ap(name, "_entry.js"), encoding="utf-8").read()).group(1)
TABLES = (("ivs_assembly_cams", "📷 카메라"), ("ivs_assembly_poses", "❄ 모습 기록"), ("ivs_assembly_status", "✓ 완료 표시"))
rows = {t: req("GET", "%s?assembly_id=eq.%s&select=*" % (t, mid)) for t, _ in TABLES}
for t, label in TABLES: print("%s: %d개 (번호 %s)" % (label, len(rows[t]), sorted(r.get("step") for r in rows[t])))
if view: sys.exit(0)
if any(rows.values()):
    bdir = os.path.join(HERE, "refs", name, "_release_backup"); os.makedirs(bdir, exist_ok=True)
    bf = os.path.join(bdir, time.strftime("%Y%m%d_%H%M%S") + ".json"); json.dump({"assembly_id": mid, "rows": rows}, open(bf, "w", encoding="utf-8"), ensure_ascii=False)
    print("백업:", os.path.relpath(bf, HERE))
    for t, label in TABLES:
        if rows[t]: req("DELETE", "%s?assembly_id=eq.%s" % (t, mid)); print("풀었다 —", label, len(rows[t]), "개")
else: print("풀 것이 없다.")

# 손 좌표(규칙 1번·C6·00-1 ③): 조립 스크립트의 손 좌표를 백업하고 지운다(strip_hand.py) — 부품 위치는 원점 미배치로 돌아가고 번호 작업에서 attach/recv 규칙 좌표로 다시 놓는다
import subprocess
subprocess.run([sys.executable, os.path.join(HERE, "strip_hand.py"), name], env=dict(os.environ, PYTHONIOENCODING="utf-8"))

try:   # 작업 범위 되돌림: build 는 number_start 로 시작한 번호까지만 막는다(규칙 A1)
    json.dump({"upto": 0}, open(os.path.join(HERE, "refs", name, "_worked_upto.json"), "w", encoding="utf-8")); print("작업 범위: 0 (number_start 로 번호를 시작할 때마다 늘어난다)")
except Exception as e_: print("작업 범위 기록 실패:", e_)
