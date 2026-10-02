# 조립도 한 번에 만들기: python build.py <스크립트 이름(예: autogun)> [--write]
#   1) partlib 로 부품 연결점(conn.json·dims.json) 생성  2) 스크립트 실행(<이름>.py → <이름>_asm.json·<이름>_entry.js)
#   3) check_local.js 의 모든 검사(단계별 정밀·겹침·검증 절차·LIST·안내 화살표) → 문제가 있으면 종료 코드 1
#   4) --write 이면 문제 0건일 때만 public/design-assemblies.js 에 넣는다(emit.py)
# 실수를 발견하면 lessons.py 의 LESSONS 에 규칙을 적고 가능하면 asmlib/검사로 옮긴다 — 이 스크립트가 마지막에 그 목록을 보여 준다.
import subprocess, sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1]; write = "--write" in sys.argv
env = dict(os.environ, PYTHONIOENCODING="utf-8")
def run(cmd, show=True):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    if show and out.strip(): print(out.rstrip())
    return p.returncode, out
run([sys.executable, "partlib.py"], show=False)
rc, out0 = run([sys.executable, name + ".py"])
if rc: sys.exit("스크립트 실행 실패")
files = [name + "_asm.json"]
list_f, def_f = name + "_list.json", name + "_def.json"
args = ["node", "check_local.js", files[0]] + ([list_f] + ([def_f] if os.path.exists(def_f) else []) if os.path.exists(list_f) else [])
rc, out = run(args)
bad = []
for line in (out0 + chr(10) + out).splitlines():
    s = line.strip()
    if s.startswith("단계별 정밀 검사 문제:") and not s.endswith(" 0"): bad.append(s)
    if s.startswith("단계별 검증 절차 문제:") and not s.endswith(" 0"): bad.append(s)
    if s.startswith("안내 화살표 없는 부품:") and not s.endswith(" 0"): bad.append(s)
    if s.startswith("[경고]") or "[경고]" in s: bad.append(s)
    if s.startswith("LIST") and "불일치" in s: bad.append(s)
if bad:
    print("\n❌ 문제 있음 — 고친 뒤 다시 돌릴 것:"); [print("  ", b) for b in bad]
    sys.exit(1)
print("\n✅ 문제 0건 (겹침 경고는 위 목록에서 오탐인지 직접 확인)")
# ───── 규칙 준수 확인(가이드 6-1 체크리스트) ─────
# 자동 검사로는 안 보이는 것을 단계별로 기록한다: <이름>_rules.json = {"view":[화면 확대로 본 단계], "count":[교재와 칸 수 대조한 단계], "camera":[교재와 카메라 확인한 단계]}
# 눈으로 확인할 때마다 해당 단계 번호를 이 파일에 적는다. --write 는 모든 단계가 세 목록에 있어야 한다(아니면 --unverified 로 미확인임을 알고 넣는다).
asm = json.load(open(files[0], encoding="utf-8"))["steps"]
n_steps = len(asm)
rf = name + "_rules.json"
rules = json.load(open(rf, encoding="utf-8")) if os.path.exists(rf) else {}
srcs = {}
for k, st in enumerate(asm, 1): srcs.setdefault(st.get("camSrc") or "없음", []).append(k)
print("\n── 규칙 준수 확인 (가이드 6-1) ──")
print("자동 검사: 통과 (위)")
print("카메라 출처:", ", ".join(f"{v} {len(ks)}개" for v, ks in srcs.items()), "| 짐작/없음 단계:", sorted(srcs.get("guess", []) + srcs.get("없음", [])))
# 기준선(바닥 방향선) 점검: 원점에서 150mm 넘게 떨어진 자리에서 만드는 단계는 cam.axes 가 있어야 한다(가이드 6-1 11번)
far = []
for k, st in enumerate(asm, 1):
    pts = []
    for pt_ in st.get("parts", []):
        pp = (pt_.get("side") or {}).get("p") or pt_.get("p")
        if pp and not (pt_.get("move") and pt_["move"].get("at") == k): pts.append(pp)
    if pts and max(max(abs(q[0]), abs(q[2])) for q in pts) > 150 and not (st.get("cam") or {}).get("axes"): far.append(k)
print("기준선(cam.axes) 없는데 원점에서 먼 단계:", far if far else "없음")
if far: print("⚠ 가이드 6-1 11번: 이 단계들은 기준선이 안 보일 수 있다.")
unver = False
for key, label in (("view", "화면 확대 확인"), ("count", "교재와 칸 수 대조"), ("camera", "교재와 카메라 확인")):
    done = set(rules.get(key, [])); miss = [k for k in range(1, n_steps + 1) if k not in done]
    unver = unver or bool(miss)
    print(f"{label}: {n_steps - len(miss)}/{n_steps} 단계" + (f" — 안 한 단계 {miss}" if miss else ""))
if unver: print("⚠ 위 '안 한 단계'는 보고할 때 안 했다고 말해야 한다.")
if write and unver and "--unverified" not in sys.argv:
    sys.exit("❌ 규칙 확인이 끝나지 않아 --write 를 하지 않는다. 확인하고 " + rf + " 에 적거나, 미확인을 알고 넣으려면 --unverified 를 붙인다.")
if write:  # (규칙 확인은 위에서 이미 검사)
    rc, out = run([sys.executable, "emit.py", name + "_entry.js", "cubo-1-" + name]); print(out.strip())
