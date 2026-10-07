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
# ───── 단계 계약 검사(계획이 조용히 사라지지 않게) ─────
# <이름>_contract.json = 단계마다 부품 이름별 개수 + 부품 없는 단계 표시. 스크립트를 고친 뒤 이 값과 다르면 종료한다(30·31번 코드가 다른 수정에 지워졌는데 검사 0건이던 사고).
# 일부러 바꾼 것이면 --accept-contract 로 새 값을 받아들인다. 설명에 "(채우는 중)"이 남은 단계도 막는다.
_asm0 = json.load(open(files[0], encoding="utf-8"))["steps"]
cur_contract = {}
for _k, _st in enumerate(_asm0, 1):
    _cnt = {}
    for _pt in _st.get("parts", []): _cnt[_pt.get("n")] = _cnt.get(_pt.get("n"), 0) + 1
    cur_contract[str(_k)] = {"parts": _cnt, "noPart": bool(_st.get("noPart"))}
# 작업 공간(창고) 규칙: 창고 칸(slot)을 쓰는 조립도는 모든 단계에 slot 이 있어야 하고, 앞 단계와 자리가 바뀌면 history(불러온 곳·보관한 곳 글자)가 있어야 한다(안내서 6-5).
_slots = [_st.get("slot") for _st in _asm0]
_bad_slot = []
if any(v is not None for v in _slots):
    for _k, _st in enumerate(_asm0, 1):
        if _st.get("slot") is None: _bad_slot.append("단계 %d: slot(작업 창고 번호)이 없음" % _k)
        elif _k > 1 and _slots[_k - 2] is not None and _st["slot"] != _slots[_k - 2] and not _st.get("history"): _bad_slot.append("단계 %d: 작업 자리가 %s → %s 로 바뀌는데 history(불러온/보관한 곳)가 없음" % (_k, _slots[_k - 2], _st["slot"]))
_cf = name + "_contract.json"
_bad2 = _bad_slot + ["단계 %d 설명에 '(채우는 중)'이 남음 — 채우지 않은 뼈대 단계" % (_k) for _k, _st in enumerate(_asm0, 1) if "(채우는 중)" in (_st.get("note") or "")]
if os.path.exists(_cf) and "--accept-contract" not in sys.argv:
    _old = json.load(open(_cf, encoding="utf-8"))
    for _k in sorted(set(_old) | set(cur_contract), key=int):
        if _old.get(_k) != cur_contract.get(_k): _bad2.append("단계 %s 계약 불일치: 기대 %s / 지금 %s" % (_k, _old.get(_k), cur_contract.get(_k)))
if _bad2:
    print(chr(10) + "❌ 단계 계약 위반 — 계획한 단계가 사라졌거나 바뀌었다:"); [print("  ", b) for b in _bad2]
    print("   (일부러 바꿨다면 --accept-contract 를 붙여 다시 돌린다)")
    sys.exit(1)
json.dump(cur_contract, open(_cf, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("단계 계약: 통과 (%d단계)" % len(cur_contract))
# ───── 승인(✅ 완료) 단계 보호 ─────
# <이름>_approved.json = {"steps": {단계: 내용 해시}} — 사용자가 ✅ 완료로 체크한 단계의 내용 지문. 그 단계 내용이 바뀌면 빌드를 막는다(사용자 승인 단계를 Claude 가 멋대로 고치는 사고 방지).
# 작업 시작 전에 DB(ivs_assembly_status)에서 완료 단계 목록을 읽어 이 파일을 맞춘다. 사용자가 고치라고 한 단계만 --allow-steps 30,31 처럼 열어 준다.
import hashlib
_af = name + "_approved.json"
def _fp(st): return hashlib.sha1(json.dumps(st, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
_allow = set()
for _a in sys.argv:
    if _a.startswith("--allow-steps="): _allow = {int(x) for x in _a.split("=", 1)[1].split(",") if x.strip()}
if "--sync-approved" in sys.argv:
    _steps_ok = [int(x) for x in sys.argv[sys.argv.index("--sync-approved") + 1].split(",")]
    json.dump({"steps": {str(k): _fp(_asm0[k - 1]) for k in _steps_ok}}, open(_af, "w", encoding="utf-8"), indent=0)
    print("승인 단계 지문 저장:", _steps_ok)
if os.path.exists(_af):
    _ap = json.load(open(_af, encoding="utf-8")).get("steps", {})
    _chg = [int(k) for k, h in _ap.items() if int(k) <= len(_asm0) and _fp(_asm0[int(k) - 1]) != h and int(k) not in _allow]
    if _chg:
        print(chr(10) + "❌ 사용자가 ✅ 완료로 체크한 단계의 내용이 바뀜: " + str(sorted(_chg)))
        print("   사용자가 고치라고 한 단계가 아니면 되돌릴 것. 고치라고 했다면 --allow-steps=" + ",".join(map(str, sorted(_chg))) + " 로 다시 돌린 뒤 --sync-approved 로 지문을 갱신한다.")
        sys.exit(1)
    print("승인 단계 보호: 통과 (%d단계 변경 없음)" % len(_ap))
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
# ───── 책 이미지 작업 게이트(관리자 지시 2026-10-07: 수평선·격자·부품 배치가 이 작업의 전부 — 기억이 없는 Claude 도 이 검사로 강제된다) ─────
# 부품이 있는 단계마다 refs/<이름>/index.json 에 그 단계의 격자 그림이 있어야 한다: 1차(idx 1)와 2차(idx 2, 수평선을 긋고 돌린 그림 위의 격자). 판이 없는 단계는 설명이 ① 로 시작하는 원본 1장(idx 1)만 인정한다.
# 이 검사는 --unverified 로 건너뛸 수 없다. 옛 조립도(아래 목록)만 면제. 정말 못 만드는 단계는 --grid-skip=3,5 로 이유를 보고하고 관리자 확인을 받은 뒤에만 쓴다.
LEGACY_NO_GRID = {"rabbit", "balance", "windmill", "spinner", "trike", "soccer", "autogun", "airplane", "rollingbot", "battlerobot"}
_skip = set()
for _a in sys.argv:
    if _a.startswith("--grid-skip="): _skip = {int(x) for x in _a.split("=", 1)[1].split(",") if x.strip()}
_idxf = os.path.join("refs", name, "index.json")
_idx = json.load(open(_idxf, encoding="utf-8")) if os.path.exists(_idxf) else []
_have = {}
for _r in _idx: _have.setdefault(_r["step"], {})[_r["idx"]] = _r.get("note", "")
_nogrid = []
for _k, _st in enumerate(asm, 1):
    if not _st.get("parts") or _k in _skip: continue
    _h = _have.get(_k, {})
    ok = (1 in _h and 2 in _h) or (1 in _h and str(_h[1]).lstrip().startswith("①"))
    if not ok: _nogrid.append(_k)
print("책 이미지 작업(수평선·격자) 단계별 그림:", "면제(옛 조립도)" if name in LEGACY_NO_GRID else (f"{len([1 for k, st in enumerate(asm, 1) if st.get('parts')]) - len(_nogrid)}단계 있음" + (f" — ❌ 격자가 없는 단계 {_nogrid}" if _nogrid else "")))
if write and _nogrid and name not in LEGACY_NO_GRID:
    sys.exit("❌ 책 이미지 작업(수평선을 긋고 돌린 그림 위의 격자 1차·2차)이 없는 단계가 있어 --write 를 하지 않는다: " + str(_nogrid) + "\n   안내서 '★★★ 최우선 규칙'대로 그 단계의 격자를 먼저 만든다(refs_make → refs_cli/refs-grid). 이 검사는 --unverified 로 건너뛸 수 없다.")
if write and unver and "--unverified" not in sys.argv:
    sys.exit("❌ 규칙 확인이 끝나지 않아 --write 를 하지 않는다. 확인하고 " + rf + " 에 적거나, 미확인을 알고 넣으려면 --unverified 를 붙인다.")
if write:  # (규칙 확인은 위에서 이미 검사)
    rc, out = run([sys.executable, "emit.py", name + "_entry.js", "cubo-1-" + name]); print(out.strip())
