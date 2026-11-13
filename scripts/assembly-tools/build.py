# 조립도 한 번에 만들기: python build.py <스크립트 이름(예: autogun)> [--write]
#   1) partlib 로 부품 연결점(conn.json·dims.json) 생성  2) 스크립트 실행(<이름>.py → <이름>_asm.json·<이름>_entry.js)
#   3) check_local.js 의 모든 검사(단계별 정밀·겹침·검증 절차·LIST·안내 화살표) → 문제가 있으면 종료 코드 1
#   4) --write 이면 문제 0건일 때만 public/design-assemblies.js 에 넣는다(emit.py)
# 실수를 발견하면 lessons.py 의 LESSONS 에 규칙을 적고 가능하면 asmlib/검사로 옮긴다 — 이 스크립트가 마지막에 그 목록을 보여 준다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import re, subprocess, sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1]; write = "--write" in sys.argv
# 우회 옵션 전부 삭제(관리자 지시 2026-10-11): 쓸 수 있는 옵션은 --write 하나뿐이다. --unverified·--wip·--accept-contract·--allow-steps·--sync-approved·--iron-later·--grid-skip 등
# 번호별 확인을 건너뛰게 하던 옵션을 Claude 가 말없이 써서 7~15번을 몰아 만든 일이 있었다. 확인의 근거는 사용자가 화면에서 누른 ✓ 완료(DB)뿐이다(userdone.py).
_bad_opts = [a_ for a_ in sys.argv[2:] if a_ != "--write"]
if _bad_opts: sys.exit("❌ 쓸 수 없는 옵션: " + " ".join(_bad_opts) + " — 우회 옵션은 모두 삭제됐다. 쓸 수 있는 옵션은 --write 하나뿐이다. 막히면 막힌 이유를 고치거나, 사용자에게 보고한다.")
env = dict(os.environ, PYTHONIOENCODING="utf-8")
def run(cmd, show=True):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    if show and out.strip(): print(out.rstrip())
    return p.returncode, out
# 기본 환경 자동 세팅(사용자 지시 2026-11-09): 이 조립도의 _rules.json 에 빠진 기본 검사 항목을 빌드할 때 자동으로 채운다 — 나중에 손으로 챙기지 않아도 검사가 켜져 있다(새 조립도 new_assembly.py 와 같은 목록, 규칙 00절). 이미 적힌 값은 건드리지 않는다.
_DEFAULT_FLAGS = {"parts_sum": True, "mate_marks": True, "strict": True, "orient_check": True, "placecheck": True, "img_db": True, "rulecheck": True}
try:
    _rf = asmpath.resolve(name + "_rules.json"); _rj = json.load(open(_rf, encoding="utf-8")); _miss = [k for k in _DEFAULT_FLAGS if k not in _rj]
    if _miss:
        _rj.update({k: _DEFAULT_FLAGS[k] for k in _miss}); open(_rf, "w", encoding="utf-8").write(json.dumps(_rj, ensure_ascii=False, indent=1))
        print("기본 검사 항목 자동 추가:", ", ".join(_miss))
except Exception as _e:
    print("⚠ 기본 검사 항목 자동 추가를 못 함:", str(_e)[:100])
run([sys.executable, "partlib.py"], show=False)
rc, out0 = run([sys.executable, asmpath.ap(name, ".py")])
if rc: sys.exit("스크립트 실행 실패")
import userdone
_m0 = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(name + "_entry.js", encoding="utf-8").read())
_aid = _m0.group(1) if _m0 else "cubo-1-" + name
_USER_DONE = userdone.user_done(_aid)   # 사용자가 화면에서 직접 누른 ✓ 완료 단계 — 읽지 못하면 여기서 멈춘다
print("사용자 ✓ 완료 단계(DB):", sorted(_USER_DONE) if _USER_DONE else "없음")
files = [name + "_asm.json"]
list_f, def_f = name + "_list.json", name + "_def.json"
args = ["node", "check_local.js", asmpath.resolve(files[0])] + ([asmpath.resolve(list_f)] + ([asmpath.resolve(def_f)] if os.path.exists(def_f) else []) if os.path.exists(list_f) else [])
rc, out = run(args)
try: _MATE_MARKS = bool(json.load(open(name + "_rules.json", encoding="utf-8")).get("mate_marks"))
except Exception: _MATE_MARKS = False
bad = []
# 아직 시작하지 않은 번호(격자 그림 1·2 또는 읽기 표가 없는 뒤 번호)의 문제는 세지 않는다 — 번호를 순서대로 만드는 규칙(A1)과 같다
def _worked_upto():
    try: ix = json.load(open(os.path.join("refs", name, "index.json"), encoding="utf-8"))
    except Exception: ix = []
    hv = {}
    for r in ix: hv.setdefault(r["step"], set()).add(r["idx"])
    try: rd = json.load(open(name + "_read.json", encoding="utf-8"))
    except Exception: rd = {}
    w = [k for k in range(1, 200) if {1, 2} <= hv.get(k, set()) or any(str((rd.get(str(k)) or {}).get(f, "")).strip() for f in ("면", "링"))]
    return max(w) if w else 0
_UP0 = _worked_upto()
try:   # number_start 가 적은 "지금까지 작업한 번호"(손 좌표 삭제로 뒤 번호가 다시 만들 일이 된 조립도) — 그 뒤 번호의 문제는 세지 않는다
    _wf0 = os.path.join("refs", name, "_worked_upto.json")
    if os.path.exists(_wf0): _UP0 = min(_UP0, int(json.load(open(_wf0, encoding="utf-8")).get("upto", 0)) + 1)   # +1 = 지금 하는 번호 바로 다음까지 미리 본다
except Exception: pass
_cnt = {}; _cur = None
for line in (out0 + chr(10) + out).splitlines():
    s = line.strip()
    _h = next((h for h in ("단계별 정밀 검사 문제:", "단계별 검증 절차 문제:", "안내 화살표 없는 부품:") if s.startswith(h)), None)
    if _h: _cur = _h; _cnt.setdefault(_h, [s, 0]); continue
    _m = re.match(r"(\d+)단계", s)
    if _cur and _m:
        if int(_m.group(1)) <= _UP0: _cnt[_cur][1] += 1
    elif s and not _m: _cur = None
for _h, (_s, _n) in _cnt.items():
    if _n: bad.append("%s %d (1~%d번)" % (_h.rstrip(":"), _n, _UP0))
for line in (out0 + chr(10) + out).splitlines():
    s = line.strip()
    if s.startswith("안내점 맞물림 없는 부품:") and not s.endswith(" 0"):   # 안내점(marks)이 가리키는 구멍에 돌기가 제자리에서 안 들어가 있으면 화살표가 안 나온다(드롭체커 27번). <이름>_rules.json 에 "mate_marks": true 인 조립도만 막고, 나머지는 경고로 보여 준다(옛 조립도 ✓ 번호는 못 고친다)
        if _MATE_MARKS:   # 시작하지 않은 뒤 번호(1~_UP0 밖)의 맞물림 문제는 세지 않는다 — 위 단계별 검사와 같은 규칙(A1)
            _mm = [int(m_.group(1)) for m_ in (re.match(r"(\d+)단계 .*맞물려 있지 않음", l_.strip()) for l_ in (out0 + chr(10) + out).splitlines()) if m_]
            if any(k_ <= _UP0 for k_ in _mm) or not _mm: bad.append(s)
            else: print("⚠ " + s + " (뒤 번호 %s단계 — 아직 시작하지 않아 막지 않음)" % ",".join(str(k_) for k_ in sorted(set(_mm))))
        else: print("⚠ " + s + " (참고 — <이름>_rules.json 에 \"mate_marks\": true 를 넣으면 이 조립도는 막는다)")
    if s.startswith("[경고]") or "[경고]" in s:
        _wm = re.search(r"(\d+)단계", s)
        if _wm and int(_wm.group(1)) > _UP0: print("⚠ " + s + " (뒤 번호 %s단계 — 아직 시작하지 않아 막지 않음)" % _wm.group(1))
        else: bad.append(s)
    if s.startswith("LIST") and "불일치" in s: bad.append(s)
if bad:
    print("\n❌ 문제 있음 — 고친 뒤 다시 돌릴 것:"); [print("  ", b) for b in bad]
    sys.exit(1)
_ov = [int(m_.group(1)) for m_ in (re.search(r"몸통 겹침:\s*(\d+)", l_) for l_ in (out0 + chr(10) + out).splitlines()) if m_ and int(m_.group(1)) > 0]
if _ov: print("\n⚠⚠ 몸통 겹침 %d건 — 부품이 서로 뚫고 들어가 있다. 위 '겹침' 줄을 하나씩 보고 진짜(물리적으로 불가능)면 자리를 고치고, 기어 상자 근사 오탐이면 읽기 표 판단과정에 이유를 적는다(2026-11-08 로봇팽이 15번: 큰기어가 판을 뚫었는데 ✅ 로 지나감)" % _ov[0])
print("\n✅ 문제 0건 (겹침 경고는 위 목록에서 오탐인지 직접 확인)" if not _ov else "\n⚠ 문제 0건이지만 몸통 겹침 확인 전")
# ───── 단계 계약 검사(계획이 조용히 사라지지 않게) ─────
# <이름>_contract.json = 단계마다 부품 이름별 개수 + 부품 없는 단계 표시. 스크립트를 고친 뒤 이 값과 다르면 종료한다(30·31번 코드가 다른 수정에 지워졌는데 검사 0건이던 사고).
# ✓ 완료 단계의 계약이 바뀌면 막고(고치려면 사용자가 ✓ 를 풀어야 함), ✓ 없는 단계는 자동으로 새 값을 받는다(--accept-contract 는 삭제됨). 설명에 "(채우는 중)"이 남은 단계도 막는다.
_asm0 = json.load(open(files[0], encoding="utf-8"))["steps"]
cur_contract = {}
for _k, _st in enumerate(_asm0, 1):
    _cnt = {}
    for _pt in _st.get("parts", []): _cnt[_pt.get("n")] = _cnt.get(_pt.get("n"), 0) + 1
    cur_contract[str(_k)] = {"parts": _cnt, "noPart": bool(_st.get("noPart"))}
# 작업 공간(창고) 규칙: 창고 칸(slot)을 쓰는 조립도는 모든 단계에 slot 이 있어야 하고, 앞 단계와 자리가 바뀌면 history(불러온 곳·보관한 곳 글자)가 있어야 한다(규칙 파일 A3·A3a).
_slots = [_st.get("slot") for _st in _asm0]
_bad_slot = []
if any(v is not None for v in _slots):
    for _k, _st in enumerate(_asm0, 1):
        if _st.get("slot") is None: _bad_slot.append("단계 %d: slot(작업 창고 번호)이 없음" % _k)
        elif _k > 1 and _slots[_k - 2] is not None and _st["slot"] != _slots[_k - 2] and not _st.get("history"): _bad_slot.append("단계 %d: 작업 자리가 %s → %s 로 바뀌는데 history(불러온/보관한 곳)가 없음" % (_k, _slots[_k - 2], _st["slot"]))
_cf = name + "_contract.json"
_bad2 = _bad_slot + ["단계 %d 설명에 '(채우는 중)'이 남음 — 채우지 않은 뼈대 단계" % (_k) for _k, _st in enumerate(_asm0, 1) if "(채우는 중)" in (_st.get("note") or "")]
if os.path.exists(_cf):
    _old = json.load(open(_cf, encoding="utf-8"))
    for _k in sorted(set(_old) | set(cur_contract), key=int):
        if _old.get(_k) != cur_contract.get(_k):
            if int(_k) in _USER_DONE: _bad2.append("단계 %s 는 사용자가 ✓ 완료한 단계인데 계약이 바뀜: 기대 %s / 지금 %s — 고치려면 사용자가 그 단계의 ✓ 를 먼저 풀어야 한다" % (_k, _old.get(_k), cur_contract.get(_k)))
            else: print("   (단계 %s: 아직 사용자 ✓ 가 없는 단계라 계약 값을 새로 받는다)" % _k)
if _bad2:
    print(chr(10) + "❌ 단계 계약 위반 — 계획한 단계가 사라졌거나 바뀌었다:"); [print("  ", b) for b in _bad2]
    sys.exit(1)
json.dump(cur_contract, open(_cf, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("단계 계약: 통과 (%d단계)" % len(cur_contract))
# ───── 승인(✅ 완료) 단계 보호 ─────
# <이름>_approved.json = {"steps": {단계: 내용 해시}} — 사용자가 ✅ 완료로 체크한 단계의 내용 지문. 그 단계 내용이 바뀌면 빌드를 막는다(사용자 승인 단계를 Claude 가 멋대로 고치는 사고 방지).
# 매 빌드마다 DB(ivs_assembly_status)의 사용자 ✓ 목록과 이 파일을 자동으로 맞춘다. 고쳐야 하는 ✓ 단계는 사용자가 ✓ 를 풀어 줄 때만 열린다.
import hashlib
_af = name + "_approved.json"
import stepfp
_fp = stepfp.fp
# ✓ 완료 단계의 내용 지문은 매 빌드에서 DB 의 ✓ 와 자동으로 맞춘다: ✓ 가 풀린 단계는 지문을 지우고(사용자가 고치라고 풀어 준 것), 처음 보는 ✓ 단계는 지금 내용을 지문으로 저장한다.
#   그 외 ✓ 단계의 내용이 바뀌면 빌드를 막는다. 풀 수 있는 사람은 사용자(화면의 ✓ 버튼)뿐이다.
_ap = json.load(open(_af, encoding="utf-8")).get("steps", {}) if os.path.exists(_af) else {}
_ap = {k: h for k, h in _ap.items() if int(k) in _USER_DONE}
_chg = [int(k) for k, h in _ap.items() if int(k) <= len(_asm0) and _fp(_asm0[int(k) - 1]) != h]
if _chg:
    print(chr(10) + "❌ 사용자가 ✅ 완료로 체크한 단계의 내용이 바뀜: " + str(sorted(_chg)))
    print("   되돌릴 것. 고쳐야 하는 단계라면 사용자에게 그 단계의 ✓ 를 풀어 달라고 보고한다(다른 방법은 없다).")
    sys.exit(1)
for _k in sorted(_USER_DONE):
    if str(_k) not in _ap and _k <= len(_asm0): _ap[str(_k)] = _fp(_asm0[_k - 1])
json.dump({"steps": _ap}, open(_af, "w", encoding="utf-8"), indent=0)
print("승인 단계 보호: 통과 (%d단계 변경 없음)" % len(_ap))
# ───── 규칙 준수 확인(가이드 6-1 체크리스트) ─────
# 자동 검사로는 안 보이는 것을 단계별로 기록한다: <이름>_rules.json = {"view":[화면 확대로 본 단계], "count":[교재와 칸 수 대조한 단계], "camera":[교재와 카메라 확인한 단계]}
# 눈으로 확인할 때마다 해당 단계 번호를 이 파일에 적는다. (참고용 기록 — 확인의 근거는 사용자 ✓ 완료뿐이다)
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
print("(위 rules.json 목록은 참고용이다 — 눈으로 하는 확인의 근거는 화면↔책 비교 증거(record_check.py)나 사용자 ✓ 이고, Claude 가 이 목록에 적어서 막힘을 풀 수 없다)")
# ───── 책 이미지 작업 게이트(관리자 지시 2026-10-07: 방향 표시·격자·부품 배치가 이 작업의 전부 — 기억이 없는 Claude 도 이 검사로 강제된다) ─────
# 부품이 있는 단계마다 refs/<이름>/index.json 에 그 단계의 격자 그림이 있어야 한다: 1차(idx 1)와 2차(idx 2, 방향에 맞춰 돌린 그림 위의 격자). 판이 없는 단계는 설명이 ① 로 시작하는 원본 1장(idx 1)만 인정한다.
# 이 검사는 건너뛸 수 없다.
_skip = set()   # --grid-skip 는 없앴다(2026-10-08): 격자를 "못 만든다/불필요하다"고 Claude 가 혼자 정하던 일을 막는다
if any(_a.startswith("--grid-skip") for _a in sys.argv): sys.exit("❌ --grid-skip 은 쓸 수 없다. 격자를 만든다(가려지면 보이는 구멍으로 맞추고 그 사실을 note 에 적는다).")
_idxf = os.path.join("refs", name, "index.json")
_idx = json.load(open(_idxf, encoding="utf-8")) if os.path.exists(_idxf) else []
_have = {}
for _r in _idx: _have.setdefault(_r["step"], {})[_r["idx"]] = _r.get("note", "")
_nogrid = []
_rdf0 = name + "_read.json"
_rd0 = json.load(open(_rdf0, encoding="utf-8")) if os.path.exists(_rdf0) else {}
# 아직 시작하지 않은 번호는 검사하지 않는다: 격자 그림(1·2)이나 읽기 표가 있는 가장 뒤 번호까지만 본다(그 앞 번호가 비면 막는다). 번호를 순서대로 만드는 규칙(A1)과 같다.
_worked = [k for k in range(1, len(asm) + 1) if (1 in _have.get(k, {}) and 2 in _have.get(k, {})) or any(str((_rd0.get(str(k)) or {}).get(f, "")).strip() for f in ("면", "링"))]
_upto = max(_worked) if _worked else 0
for _k, _st in enumerate(asm, 1):
    if _k > _upto: continue
    if not _st.get("parts") or _k in _skip: continue
    _h = _have.get(_k, {})
    _plate = any(("프레임" in str(_p.get("n", "")) and "브라켓" not in str(_p.get("n", ""))) for _p in _st.get("parts", [])) or any("프레임" in str(_p.get("n", "")) for _p in _st.get("parts", []))
    ok = (1 in _h and 2 in _h)   # 2026-10-08: 판이 없다는 이유의 원본 1장 예외 폐지(격자는 큰기어 구멍·판 구멍 등 보이는 구멍으로 항상 만든다)   # 프레임(판)이 있는 단계는 반드시 회전·방향 표시·격자(idx 2) — 원본 한 장으로 때우지 못한다
    if not ok: _nogrid.append(_k)
print("책 이미지 작업(방향 표시·격자) 단계별 그림:", (f"{len([1 for k, st in enumerate(asm, 1) if st.get('parts')]) - len(_nogrid)}단계 있음" + (f" — ❌ 격자가 없는 단계 {_nogrid}" if _nogrid else "")))
_lb_saved = int((json.load(open(name + "_gate.json", encoding="utf-8")) if os.path.exists(name + "_gate.json") else {}).get("last_built", 0))
try:   # 저장된 조립도에서 새 부품 없이 합치는 번호(moveMade·madeNoPart)도 '이미 저장한 번호'다 — stepchecks 의 마지막 번호 정의와 같게(부품만 세면 27번 같은 합치기 번호가 늘 새 번호로 취급돼 막힌다)
    _sv = json.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"]
    _lb_saved = max([_lb_saved] + [i_ for i_, s_ in enumerate(_sv, 1) if s_.get("parts") or s_.get("moveMade") or s_.get("madeNoPart")])
except Exception: pass   # 이미 저장한 번호(<= last_built)를 고치는 저장은 격자·읽기 표 게이트로 막지 않는다(사용자 지시 2026-11-10: 앞 번호 격자가 비었다고 26번 수정 저장이 막히면 안 된다). 새로 더하는 번호(> last_built)는 그대로 막는다.
_nogrid_all = list(_nogrid); _nogrid = [k_ for k_ in _nogrid if k_ > _lb_saved]
if _nogrid_all and not _nogrid: print("   (이미 저장한 번호 %s 는 격자가 없지만 고치는 저장이라 막지 않는다 — 격자는 따로 만들어야 한다)" % _nogrid_all)
if write and _nogrid:
    sys.exit("❌ 책 이미지 작업(방향에 맞춰 돌린 그림 위의 격자 1차·2차)이 없는 단계가 있어 --write 를 하지 않는다: " + str(_nogrid) + "\n   큐보 부품결합규칙.md 규칙(1번 규칙·D 절)대로 그 단계의 격자를 먼저 만든다(refs_make → refs_rect). 이 검사는 건너뛸 수 없다.")

# ───── 철칙 순서 게이트(관리자 지시 2026-10-08, 우회 불가): 부품이 있는 번호마다 refs/<이름>/NN_lv.json(잘라내기→방향 표시→회전)이 있어야 한다 — 원본 위에서 격자를 먼저 맞춘 번호는 막는다(옛 조립도·--sync 이전 번호는 면제 목록 IRON_EXEMPT).
IRON_EXEMPT = {"dog": {}}   # 철칙 이전에 만든 번호를 새 순서로 다시 만들 때까지 예외로 둘 목록(이름 → {번호}). 비워 두면 전 번호 필수
if name == "dog":
    _lv_missing = [k for k, st in enumerate(asm, 1) if st.get("parts") and not os.path.exists(os.path.join("refs", name, "%02d_lv.json" % k)) and k not in IRON_EXEMPT.get(name, {})]
    print("철칙 순서(잘라내기→방향 표시→회전→격자) 그림:", "전 번호 있음" if not _lv_missing else "❌ 새 순서로 안 만든 번호 %s" % _lv_missing)
    if write and _lv_missing: print("   (경고) --write 는 막지 않는다 — 기존 1~14번을 새 순서로 다시 만드는 중. 새로 만드는 번호는 level 부터 한다.")
# ───── 번호별 읽기 표 게이트(관리자 지시 2026-10-08, 우회 불가): <이름>_read.json = {"번호": {"면": "카메라가 보는 면", "링": "초록 링이 있는 칸·줄(센 근거)", "부품": "쓴 부품"}} — 부품이 있는 단계마다 세 칸이 모두 채워져야 --write 한다.
#   격자를 만들고 점이 구멍 위에 앉았는지 확인한 뒤 센 값을 적는다. 건너뛰고 "나중에"가 안 되게 하는 장치다. 건너뛸 수 없다.
_rdf = name + "_read.json"; _rd = json.load(open(_rdf, encoding="utf-8")) if os.path.exists(_rdf) else {}
_noread = [_k for _k, _st in enumerate(asm, 1) if _k <= _upto and _st.get("parts") and not all(str((_rd.get(str(_k)) or {}).get(_f, "")).strip() for _f in ("면", "링", "부품"))]
print("번호별 읽기 표(" + _rdf + "):", (f"{len([1 for k, st in enumerate(asm, 1) if st.get('parts')]) - len(_noread)}단계 있음" + (f" — ❌ 안 적은 단계 {_noread}" if _noread else "")))
_noread_all = list(_noread); _noread = [k_ for k_ in _noread if k_ > _lb_saved]
if _noread_all and not _noread: print("   (이미 저장한 번호 %s 는 읽기 표가 비었지만 고치는 저장이라 막지 않는다 — 읽기 표는 따로 적어야 한다)" % _noread_all)
if write and _noread:
    sys.exit("❌ 번호별 읽기 표가 비어 있는 단계가 있어 --write 를 하지 않는다: " + str(_noread) + " — " + _rdf + " 에 그 번호의 면·링·부품을 적는다(격자를 만든 뒤 구멍을 센 결과). 묻지 말고 적고 계속한다.")

# 연결점(초록 점)은 무조건 부품 DB 의 돌기·구멍 점을 그대로 쓴다 = guideMode "mates" (사용자 지시 2026-11-09, 규칙 G26). 따로 재거나 적은 안내점·허용치 방식은 쓰지 않는다.
_ef = asmpath.resolve(name + "_entry.js")
if os.path.exists(_ef) and 'guideMode: "mates"' not in open(_ef, encoding="utf-8").read():
    print("❌ 연결점 방식이 mates 가 아니다(DB 연결점 그대로 쓰지 않음) — Asm(..., guideMode=\"mates\") 와 항목 파일에 guideMode: \"mates\" 가 있어야 한다(G26)")
    if write: sys.exit("❌ guideMode mates 가 아니어서 --write 를 하지 않는다 — 조립도 스크립트의 Asm(...) 에 guideMode=\"mates\" 를 넣는다.")

# ───── 그룹 이동 참고 정보(관리자 지시 2026-10-09: 막는 장치가 아니라 판단을 돕는 정보): rules 에 "placecheck": true 가 있으면 그룹으로 옮겨 붙이는 부품의 상대 자세가 옮기기 전·후에 같은지 보여 준다.
#   어긋남이 크면 막지 않고 알려 준다 — 완성 모습·앞뒤 번호를 펼쳐 놓고 이유를 판단해 읽기 표 '판단과정'에 적는다.
if rules.get("placecheck"):
    import placecheck
    _pcp, _pcs = placecheck.rigid_problems(asm, exempt=set(rules.get("placecheck_exempt", [])))
    print("그룹 이동 참고(placecheck):", ", ".join("%d번 %d개 부품 어긋남 %.3fmm" % t for t in _pcs) if _pcs else "그룹 이동 없음")
    for _x in _pcp: print("   ⚠ 판단 필요:", _x)
# ───── 번호별 점검 게이트(관리자 지시 2026-10-08, 우회 불가): <이름>_checks.json 의 blocking(격자 없음·읽기 표 빈칸·읽기 표 부품≠모델·LIST 초과)이 있으면 --write 하지 않는다.
_ckf = name + "_checks.json"
if not os.path.exists(_ckf):   # 2026-10-10: 조립 스크립트 끝에 import stepchecks; stepchecks.apply(A, "<이름>") 가 없으면 번호별 점검이 한 번도 안 돌아 규칙을 건너뛰게 된다
    sys.exit("❌ " + _ckf + " 가 없다 — 조립 스크립트 끝(A.save_links() 앞)에 `import stepchecks; stepchecks.apply(A, \"" + name + "\")` 를 넣고 다시 돌린다. 이 검사는 건너뛸 수 없다.")
if os.path.exists(_ckf):
    _ck = json.load(open(_ckf, encoding="utf-8")); _bl = _ck.get("blocking", [])
    _bl = [b_ for b_ in _bl if not (re.match(r"(\d+)번", b_) and int(re.match(r"(\d+)번", b_).group(1)) > _upto)]   # 아직 시작하지 않은 뒤 번호는 막지 않는다(번호를 순서대로 만드는 규칙 A1)
    print("번호별 점검(" + _ckf + "):", "통과" if not _bl else "❌ 막힌 항목 %d개" % len(_bl)); [print("   ☐", b_) for b_ in _bl]
    _evf = name + "_evidence.json"; _evd = json.load(open(_evf, encoding="utf-8")) if os.path.exists(_evf) else {}
    for _k, _st in enumerate(asm, 1):   # 비교 증거는 번호 내용이 바뀐 뒤에는 무효 — 지금 최종 내용의 지문과 같아야 한다
        if str(_k) in _evd and not stepfp.same(_evd[str(_k)], _st, asm) and _k not in _USER_DONE: _bl.append("%d번: 책과 비교한 뒤 내용이 바뀜 — 다시 비교하고 record_check.py 로 증거를 새로 남긴다" % _k)
    # 이미 저장해 둔 번호를 고치는 저장(마지막 번호가 늘지 않음)은 앞 번호 증거가 낡았어도 허용한다 — 고친 것을 화면으로 봐야 다시 비교할 수 있다.
    #   새 번호를 더하는 저장(마지막 번호가 늘어남)은 앞 번호 전부가 증거(또는 사용자 ✓)를 갖춰야 한다. 마지막으로 저장에 성공한 번호는 <이름>_gate.json 에 build.py 가 적는다.
    _gf = name + "_gate.json"; _gate = json.load(open(_gf, encoding="utf-8")) if os.path.exists(_gf) else {}
    _lb = max([_k for _k, _st in enumerate(asm, 1) if _st.get("parts")] or [0])
    _fix_only = _lb <= int(_gate.get("last_built", 0)) and int(_gate.get("last_built", 0)) > 0
    if _fix_only and _bl:
        _eye_stale = [b_ for b_ in _bl if any(t_ in b_ for t_ in ("화면 확대 확인", "나란히 비교", "카메라 책과 대조", "짐작(guess)이 아님", "책과 비교한 뒤 내용이 바뀜"))]
        if _eye_stale: print("   (이미 저장한 번호를 고치는 저장이라 다음 눈 확인 %d개는 막지 않는다 — 저장 뒤 화면으로 다시 비교하고 record_check.py 로 증거를 새로 남긴다)" % len(_eye_stale)); [print("     ·", b_) for b_ in _eye_stale]
        _bl = [b_ for b_ in _bl if b_ not in _eye_stale]
    # 이미 저장한 번호(<= last_built)의 막힘 항목은 저장을 막지 않는다(사용자 지시 2026-11-10: 앞 번호 읽기 표·눈 확인이 비었다고 고치는 저장이 막히면 안 된다). 새로 더하는 번호(> last_built)의 항목만 막는다. 건너뛴 항목은 출력에 남긴다.
    _saved_bl = [b_ for b_ in _bl if re.match(r"(\d+)번", b_) and int(re.match(r"(\d+)번", b_).group(1)) <= _lb_saved]
    if _saved_bl and write:
        print("   (이미 저장한 번호의 미완 항목 %d개는 저장을 막지 않는다 — 나중에 채워야 한다)" % len(_saved_bl)); _bl = [b_ for b_ in _bl if b_ not in _saved_bl]
    if write and _bl: [print("   ☐(막힘)", b_) for b_ in _bl]
    if write and _bl: sys.exit("❌ 번호별 점검에서 막힌 항목이 있어 --write 를 하지 않는다 — 막힌 항목을 고친다. 눈으로 하는 확인(화면 확대·칸 수 대조·카메라 대조)은 화면 캡처와 책 그림을 나란히 비교하고 record_check.py 로 증거를 남긴 번호(또는 사용자가 ✓ 한 번호)만 통과한다. 마지막으로 만든 번호 하나만 증거 없이 쓸 수 있다.")
# 규칙 점검(rulecheck.py): 번호마다 격자 출처·카메라 오차·증거·읽기 표를 판정해 요약을 보여 준다. 저장은 막지 않고(경고) 다음 번호 시작은 number_start 가 막는다.
try:
    import rulecheck as _rc
    _res, _strict = _rc.check(name)
    _badn = [k_ for k_, it_ in _res.items() if any(s_ == "❌" for s_, _, _ in it_)]
    print("규칙 점검(rulecheck): ❌ %d번 %s — 자세한 해결 방법: python rulecheck.py %s" % (len(_badn), _badn[:20], name) if _badn else "규칙 점검(rulecheck): ❌ 없음")
except Exception as _e_:
    print("규칙 점검(rulecheck) 을 실행하지 못함:", str(_e_)[:100])
# 도는 부품(축·T축·바퀴·기어·서보혼·DC모터)이 있는데 DB 에 관절이 하나도 없으면 경고 — 번호를 만들 때 바로 등록하는 규칙(사용자 지적 2026-11-01 조향자동차: 완성 직전까지 0개)
try:
    import _jq as _jqq
    _rot = sorted({_n for _st in asm for _p in _st.get("parts", []) for _n in [_p.get("n", "")] if _n in ("축", "T축", "중간바퀴", "작은바퀴", "큰기어", "작은기어", "서보혼", "스프라켓")})
    _aid = re.search(r'id: "(cubo-[^"]+)"', open(name + "_entry.js", encoding="utf-8").read())
    if _rot and _aid and not _jqq.get("ivs_assembly_joints", "assembly_id=eq.%s&select=joint_id&limit=1" % _aid.group(1)):
        print("[경고] 도는 부품(%s)이 있는데 관절이 0개 — 번호를 만들 때 바로 관절·움직이는 묶음을 등록한다(큐보/규칙/05_조립.md, CLAUDE.md '회전하는 곳은 항상 관절')" % ", ".join(_rot))
except Exception as _e_:
    print("관절 점검을 실행하지 못함:", str(_e_)[:100])
# 화면 "부품정리·창고정리" 표시(관리자 지시 2026-11-02): 평소 미완, 1차(모든 번호 기록)가 끝났을 때만 완료. 손으로 완료로 적지 않는다. parts_sum 을 켠 조립도만 표시한다.
try:
    _rl = json.load(open(name + "_rules.json", encoding="utf-8")) if os.path.exists(name + "_rules.json") else {}
    _ef = name + "_entry.js"; _es = re.sub(r"      prepDone: .*\n", "", open(_ef, encoding="utf-8").read())
    if _rl.get("parts_sum") and os.path.exists(list_f):
        import collections as _co2
        _lst = asmpath.list_counts(name); _tot = _co2.Counter(); _all_used = True   # LIST + 관리자 확정 수량(qtyOverride, 사용자 2026-11-13 — 배틀로봇 부품정리가 영영 미완이던 원인)
        for _st in _asm0:
            _mu = re.search(r"▣ 사용 부품:\s*(.*)", _st.get("note") or "")
            if not _mu: _all_used = False; continue
            _txt = re.sub(r"\([^)]*\)", "", _mu.group(1))
            for _pp in _txt.split(","):
                _mm = re.match(r"\s*(.+?)\s+(\d+)\s*$", _pp)
                if _mm: _tot[_mm.group(1).strip()] += int(_mm.group(2))
        _parts_ok = bool(_all_used and all(_tot.get(_n, 0) == _c for _n, _c in _lst.items() if _n != "리모컨") and all(_n in _lst for _n in _tot))   # 1차 완료 = 모든 번호에 ▣ 사용 부품이 있고 합계 = LIST (큐보 부품결합규칙.md A2a)
        if not _parts_ok: print("   부품정리: 미완 — ▣ 사용 부품이 없는 번호가 있거나 합계가 LIST 와 다름")
        _slots_ok = any(v is not None for v in _slots) and not _bad_slot   # 1차 완료 = 모든 번호에 slot, 창고가 바뀌는 번호마다 history (큐보 부품결합규칙.md A3a)
        if not _slots_ok: print("   창고정리: 미완 — slot 이 없는 번호나 history 가 없는 번호가 있음")
        _es = _es.replace("      steps: [", "      prepDone: %s,\n      steps: [" % json.dumps({"parts": bool(_parts_ok), "slots": bool(_slots_ok)}), 1)
        print("부품정리 %s · 창고정리 %s (화면 표시)" % ("완료" if _parts_ok else "미완", "완료" if _slots_ok else "미완"))
    open(_ef, "w", encoding="utf-8").write(_es)
except Exception as _e_:
    print("부품정리·창고정리 표시를 만들지 못함:", str(_e_)[:100])
# 규칙 위반 화면 표시(사용자 지시 2026-11-08): 번호별 위반을 모아 항목 파일에 def.violations 로 넣는다 — 화면이 종류마다 다른 색·기호로 칠한다(violations.py). 번호 지문(✓ 보호)에는 들어가지 않는다.
try:
    import violations as _vi
    _n_, _ts_, _ = _vi.write_entry(name)
    print("규칙 위반 표시: %d번 (%s)" % (_n_, ", ".join(_ts_) or "없음"))
except Exception as _e_:
    print("규칙 위반 표시를 만들지 못함:", str(_e_)[:120])
# ✓ 완료(잠금)한 번호에 규칙 위반이 있으면 사용자가 원해도 막는다(사용자 지시 2026-11-08: 위반이 있는 조립도는 잠글 수 없다). ✓ 를 풀고 위반을 고쳐야 한다.
try:
    _lockbad = {int(_k): len(_v) for _k, _v in _vi.collect(name).items() if int(_k) in _USER_DONE}
except Exception as _e_:
    _lockbad = {}; print("완료 번호의 위반 검사를 못 했다:", str(_e_)[:100])
if _lockbad:
    sys.exit("❌ ✓ 완료로 잠긴 번호에 규칙 위반이 있다(번호: 건수) " + str(_lockbad) + " — 위반이 있으면 잠글 수 없다. 사용자에게 ✓ 를 풀어도 되는지 묻고, 풀고 고친 뒤 위반 0 을 확인하고 다시 잠근다.")
if write:  # (규칙 확인은 위에서 이미 검사)
    _m = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(name + "_entry.js", encoding="utf-8").read())   # 항목 파일의 id(2권은 cubo-2-...). 없으면 1권 규칙
    rc, out = run([sys.executable, "emit.py", name + "_entry.js", _m.group(1) if _m else "cubo-1-" + name]); print(out.strip())
    if rc == 0: json.dump({"last_built": max([_k for _k, _st in enumerate(asm, 1) if _st.get("parts") or _st.get("moveMade") or _st.get("madeNoPart")] or [0])}, open(name + "_gate.json", "w", encoding="utf-8"))
# 검사 파일 감시(CCTV, gate_watch.py): 규칙을 지키는 검사 도구가 사용자가 마지막으로 확인한 상태에서 바뀌었으면 매번 여기서 한 줄로 보인다(막지는 않는다).
try: print(subprocess.run([sys.executable, "gate_watch.py", "--brief"], capture_output=True, text=True, encoding="utf-8").stdout.strip())
except Exception as _e3: print("검사 파일 감시를 실행하지 못함:", str(_e3)[:80])
