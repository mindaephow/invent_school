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
if write:
    rc, out = run([sys.executable, "emit.py", name + "_entry.js", "cubo-1-" + name]); print(out.strip())
