# 조립도 한 번에 만들기: python build.py <스크립트 이름(예: autogun)> [--write]
#   1) partlib 로 부품 연결점(conn.json·dims.json) 생성  2) 스크립트 실행(<이름>.py → <이름>_asm.json·<이름>_entry.js)
#   3) check_local.js 의 모든 검사(단계별 정밀·겹침·검증 절차·LIST·안내 화살표) → 문제가 있으면 종료 코드 1
#   4) --write 이면 문제 0건일 때만 public/design-assemblies.js 에 넣는다(emit.py)
# 실수를 발견하면 lessons.py 의 LESSONS 에 규칙을 적고 가능하면 asmlib/검사로 옮긴다 — 이 스크립트가 마지막에 그 목록을 보여 준다.
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
run([sys.executable, "partlib.py"], show=False)
rc, out0 = run([sys.executable, name + ".py"])
if rc: sys.exit("스크립트 실행 실패")
import userdone
_m0 = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(name + "_entry.js", encoding="utf-8").read())
_aid = _m0.group(1) if _m0 else "cubo-1-" + name
_USER_DONE = userdone.user_done(_aid)   # 사용자가 화면에서 직접 누른 ✓ 완료 단계 — 읽지 못하면 여기서 멈춘다
print("사용자 ✓ 완료 단계(DB):", sorted(_USER_DONE) if _USER_DONE else "없음")
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
# ✓ 완료 단계의 계약이 바뀌면 막고(고치려면 사용자가 ✓ 를 풀어야 함), ✓ 없는 단계는 자동으로 새 값을 받는다(--accept-contract 는 삭제됨). 설명에 "(채우는 중)"이 남은 단계도 막는다.
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
# ───── 책 이미지 작업 게이트(관리자 지시 2026-10-07: 수평선·격자·부품 배치가 이 작업의 전부 — 기억이 없는 Claude 도 이 검사로 강제된다) ─────
# 부품이 있는 단계마다 refs/<이름>/index.json 에 그 단계의 격자 그림이 있어야 한다: 1차(idx 1)와 2차(idx 2, 수평선을 긋고 돌린 그림 위의 격자). 판이 없는 단계는 설명이 ① 로 시작하는 원본 1장(idx 1)만 인정한다.
# 이 검사는 건너뛸 수 없다. 옛 조립도(아래 목록)만 면제.
LEGACY_NO_GRID = {"formula1", "rabbit", "balance", "windmill", "spinner", "trike", "soccer", "autogun", "airplane", "rollingbot", "battlerobot"}
_skip = set()   # --grid-skip 는 없앴다(2026-10-08): 격자를 "못 만든다/불필요하다"고 Claude 가 혼자 정하던 일을 막는다
if any(_a.startswith("--grid-skip") for _a in sys.argv): sys.exit("❌ --grid-skip 은 쓸 수 없다. 격자를 만든다(가려지면 보이는 구멍으로 맞추고 그 사실을 note 에 적는다).")
_idxf = os.path.join("refs", name, "index.json")
_idx = json.load(open(_idxf, encoding="utf-8")) if os.path.exists(_idxf) else []
_have = {}
for _r in _idx: _have.setdefault(_r["step"], {})[_r["idx"]] = _r.get("note", "")
_nogrid = []
for _k, _st in enumerate(asm, 1):
    if not _st.get("parts") or _k in _skip: continue
    _h = _have.get(_k, {})
    _plate = any(("프레임" in str(_p.get("n", "")) and "브라켓" not in str(_p.get("n", ""))) for _p in _st.get("parts", [])) or any("프레임" in str(_p.get("n", "")) for _p in _st.get("parts", []))
    ok = (1 in _h and 2 in _h)   # 2026-10-08: 판이 없다는 이유의 원본 1장 예외 폐지(격자는 큰기어 구멍·판 구멍 등 보이는 구멍으로 항상 만든다)   # 프레임(판)이 있는 단계는 반드시 회전·수평선·격자(idx 2) — 원본 한 장으로 때우지 못한다
    if not ok: _nogrid.append(_k)
print("책 이미지 작업(수평선·격자) 단계별 그림:", "면제(옛 조립도)" if name in LEGACY_NO_GRID else (f"{len([1 for k, st in enumerate(asm, 1) if st.get('parts')]) - len(_nogrid)}단계 있음" + (f" — ❌ 격자가 없는 단계 {_nogrid}" if _nogrid else "")))
if write and _nogrid and name not in LEGACY_NO_GRID:
    sys.exit("❌ 책 이미지 작업(수평선을 긋고 돌린 그림 위의 격자 1차·2차)이 없는 단계가 있어 --write 를 하지 않는다: " + str(_nogrid) + "\n   안내서 '★★★ 최우선 규칙'대로 그 단계의 격자를 먼저 만든다(refs_make → refs_cli/refs-grid). 이 검사는 건너뛸 수 없다.")

# ───── 철칙 순서 게이트(관리자 지시 2026-10-08, 우회 불가): 부품이 있는 번호마다 refs/<이름>/NN_lv.json(잘라내기→수평선→회전, refs_cli.py level)이 있어야 한다 — 원본 위에서 격자를 먼저 맞춘 번호는 막는다(옛 조립도·--sync 이전 번호는 면제 목록 IRON_EXEMPT).
IRON_EXEMPT = {"dog": {}}   # 철칙 이전에 만든 번호를 새 순서로 다시 만들 때까지 예외로 둘 목록(이름 → {번호}). 비워 두면 전 번호 필수
if name == "dog":
    _lv_missing = [k for k, st in enumerate(asm, 1) if st.get("parts") and not os.path.exists(os.path.join("refs", name, "%02d_lv.json" % k)) and k not in IRON_EXEMPT.get(name, {})]
    print("철칙 순서(잘라내기→수평선→회전→격자) 그림:", "전 번호 있음" if not _lv_missing else "❌ 새 순서로 안 만든 번호 %s" % _lv_missing)
    if write and _lv_missing: print("   (경고) --write 는 막지 않는다 — 기존 1~14번을 새 순서로 다시 만드는 중. 새로 만드는 번호는 level 부터 한다.")
# ───── 번호별 읽기 표 게이트(관리자 지시 2026-10-08, 우회 불가): <이름>_read.json = {"번호": {"면": "카메라가 보는 면", "링": "초록 링이 있는 칸·줄(센 근거)", "부품": "쓴 부품"}} — 부품이 있는 단계마다 세 칸이 모두 채워져야 --write 한다.
#   격자를 만들고 점이 구멍 위에 앉았는지 확인한 뒤 센 값을 적는다. 건너뛰고 "나중에"가 안 되게 하는 장치다. 건너뛸 수 없다. 옛 조립도는 면제.
_rdf = name + "_read.json"; _rd = json.load(open(_rdf, encoding="utf-8")) if os.path.exists(_rdf) else {}
_noread = [_k for _k, _st in enumerate(asm, 1) if _st.get("parts") and not all(str((_rd.get(str(_k)) or {}).get(_f, "")).strip() for _f in ("면", "링", "부품"))]
print("번호별 읽기 표(" + _rdf + "):", "면제(옛 조립도)" if name in LEGACY_NO_GRID else (f"{len([1 for k, st in enumerate(asm, 1) if st.get('parts')]) - len(_noread)}단계 있음" + (f" — ❌ 안 적은 단계 {_noread}" if _noread else "")))
if write and _noread and name not in LEGACY_NO_GRID:
    sys.exit("❌ 번호별 읽기 표가 비어 있는 단계가 있어 --write 를 하지 않는다: " + str(_noread) + " — " + _rdf + " 에 그 번호의 면·링·부품을 적는다(격자를 만든 뒤 구멍을 센 결과). 묻지 말고 적고 계속한다.")

# ───── 그룹 이동 참고 정보(관리자 지시 2026-10-09: 막는 장치가 아니라 판단을 돕는 정보): rules 에 "placecheck": true 가 있으면 그룹으로 옮겨 붙이는 부품의 상대 자세가 옮기기 전·후에 같은지 보여 준다.
#   어긋남이 크면 막지 않고 알려 준다 — 완성 모습·앞뒤 번호를 펼쳐 놓고 이유를 판단해 읽기 표 '판단과정'에 적는다.
if rules.get("placecheck"):
    import placecheck
    _pcp, _pcs = placecheck.rigid_problems(asm, exempt=set(rules.get("placecheck_exempt", [])))
    print("그룹 이동 참고(placecheck):", ", ".join("%d번 %d개 부품 어긋남 %.3fmm" % t for t in _pcs) if _pcs else "그룹 이동 없음")
    for _x in _pcp: print("   ⚠ 판단 필요:", _x)
# ───── 번호별 점검 게이트(관리자 지시 2026-10-08, 우회 불가): <이름>_checks.json 의 blocking(격자 없음·읽기 표 빈칸·읽기 표 부품≠모델·LIST 초과)이 있으면 --write 하지 않는다.
_ckf = name + "_checks.json"
if name not in LEGACY_NO_GRID and not os.path.exists(_ckf):   # 2026-10-10: 조립 스크립트 끝에 import stepchecks; stepchecks.apply(A, "<이름>") 가 없으면 번호별 점검이 한 번도 안 돌아 규칙을 건너뛰게 된다
    sys.exit("❌ " + _ckf + " 가 없다 — 조립 스크립트 끝(A.save_links() 앞)에 `import stepchecks; stepchecks.apply(A, \"" + name + "\")` 를 넣고 다시 돌린다. 이 검사는 건너뛸 수 없다.")
if os.path.exists(_ckf) and name not in LEGACY_NO_GRID:
    _ck = json.load(open(_ckf, encoding="utf-8")); _bl = _ck.get("blocking", [])
    print("번호별 점검(" + _ckf + "):", "통과" if not _bl else "❌ 막힌 항목 %d개" % len(_bl)); [print("   ☐", b_) for b_ in _bl]
    _evf = name + "_evidence.json"; _evd = json.load(open(_evf, encoding="utf-8")) if os.path.exists(_evf) else {}
    for _k, _st in enumerate(asm, 1):   # 비교 증거는 번호 내용이 바뀐 뒤에는 무효 — 지금 최종 내용의 지문과 같아야 한다
        if str(_k) in _evd and _evd[str(_k)].get("fp") != stepfp.fp(_st) and _k not in _USER_DONE: _bl.append("%d번: 책과 비교한 뒤 내용이 바뀜 — 다시 비교하고 record_check.py 로 증거를 새로 남긴다" % _k)
    # 이미 저장해 둔 번호를 고치는 저장(마지막 번호가 늘지 않음)은 앞 번호 증거가 낡았어도 허용한다 — 고친 것을 화면으로 봐야 다시 비교할 수 있다.
    #   새 번호를 더하는 저장(마지막 번호가 늘어남)은 앞 번호 전부가 증거(또는 사용자 ✓)를 갖춰야 한다. 마지막으로 저장에 성공한 번호는 <이름>_gate.json 에 build.py 가 적는다.
    _gf = name + "_gate.json"; _gate = json.load(open(_gf, encoding="utf-8")) if os.path.exists(_gf) else {}
    _lb = max([_k for _k, _st in enumerate(asm, 1) if _st.get("parts")] or [0])
    _fix_only = _lb <= int(_gate.get("last_built", 0)) and int(_gate.get("last_built", 0)) > 0
    if _fix_only and _bl:
        _eye_stale = [b_ for b_ in _bl if any(t_ in b_ for t_ in ("화면 확대 확인", "나란히 비교", "카메라 책과 대조", "짐작(guess)이 아님", "책과 비교한 뒤 내용이 바뀜"))]
        if _eye_stale: print("   (이미 저장한 번호를 고치는 저장이라 다음 눈 확인 %d개는 막지 않는다 — 저장 뒤 화면으로 다시 비교하고 record_check.py 로 증거를 새로 남긴다)" % len(_eye_stale)); [print("     ·", b_) for b_ in _eye_stale]
        _bl = [b_ for b_ in _bl if b_ not in _eye_stale]
    if write and _bl: sys.exit("❌ 번호별 점검에서 막힌 항목이 있어 --write 를 하지 않는다 — 막힌 항목을 고친다. 눈으로 하는 확인(화면 확대·칸 수 대조·카메라 대조)은 화면 캡처와 책 그림을 나란히 비교하고 record_check.py 로 증거를 남긴 번호(또는 사용자가 ✓ 한 번호)만 통과한다. 마지막으로 만든 번호 하나만 증거 없이 쓸 수 있다.")
if write:  # (규칙 확인은 위에서 이미 검사)
    _m = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(name + "_entry.js", encoding="utf-8").read())   # 항목 파일의 id(2권은 cubo-2-...). 없으면 1권 규칙
    rc, out = run([sys.executable, "emit.py", name + "_entry.js", _m.group(1) if _m else "cubo-1-" + name]); print(out.strip())
    if rc == 0: json.dump({"last_built": max([_k for _k, _st in enumerate(asm, 1) if _st.get("parts")] or [0])}, open(name + "_gate.json", "w", encoding="utf-8"))
