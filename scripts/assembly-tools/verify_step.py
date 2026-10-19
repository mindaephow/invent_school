# 번호 하나의 조립 결과를 한 번에 점검한다 — 번호마다 같은 검사를 손으로 돌려 빠뜨리지 않게 (2026-10-18 사용자 요청)
#   python verify_step.py <이름> <번호> [<번호>…]      (여러 번호 가능, 예: 5 6 7)
# 점검(✅ 통과 / ⚠ 확인 필요 / ❌ 실패):
#   1 홀라인   fits/NN_P.json 이 있고 도구·오차(px)가 기준 안인가 (blob-lattice·holefit 평균 ≤2.0px, 앵커 ≤2.0px 아니면 ⚠)
#   2 카메라   NN_axes.json 의 fit 오차 ≤2.0px, 모델에 실제로 들어간 theta·phi 가 axes 값과 같은가, 앞·뒤 번호와 같은 값(복사)이 아닌가
#   3 돌기↔구멍 _mates_table 결과에 ⚠ 가 없고 새 부품마다 맞물림 줄이 있는가
#   4 번호 대조 그림  책 링 ↔ 모델 구멍 번호를 적은 NN_4~ 그림(index.json idx≥3)이 있는가
#   5 읽기 표   면·링·부품·방향·부품방향·대조·판단과정이 다 차 있는가, 판단과정에 근거(칸·px·표)가 있는가
#   6 증거      record_check 증거가 지금 내용과 같은 지문인가(rulecheck 판정)
# [2026-10-19 사용자 수정] 18번부터 넘어가는 기준 = ① 책 비교 증거(record_check) ✅ + ② 다음 책 대조(<이름>_via.json — 다음 책에서 이 조립이 적용된 모양을 비교, 모델이 아직 없으면 "book_only": true) ✅. 아래 규칙·도구 항목은 안 맞을 때 원인을 찾는 점검(결과에 '원인 점검'으로 표시)이다.
# (옛 기준, 17번까지) 넘어가는 기준: 홀라인 ✅ + 번호 대조 그림 ✅ 이면 그 번호는 '통과'(번호판 파랑). 카메라·돌기↔구멍·읽기 표·증거는 참고 항목으로 ⚠·❌ 를 보고하되 막지 않는다.
# 마지막에 번호별 요약 표. 홀라인·번호 대조 ❌ 가 있으면 종료 코드 1. 결과는 <이름>_verify.json 에 번호별로 저장(상태·항목·그때의 내용 지문) —
#   python verify_step.py <이름> --표   → 통과 / 주의 / 실패 / 낡음(점검 뒤 내용이 바뀜) / 미검증 으로 55개 번호를 나눠 보여 준다.
import sys, os, re, json, subprocess
sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))
def run(*a):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, *a], cwd=here, capture_output=True, text=True, encoding="utf-8", env=env).stdout
if len(sys.argv) < 3: sys.exit(__doc__)
name = sys.argv[1]
if sys.argv[2] == "--표":   # 저장된 결과를 번호 전체로 보여 준다(점검 안 한 번호는 '미검증', 내용이 바뀐 번호는 '낡음')
    import stepfp
    db = json.load(open(os.path.join(here, name + "_verify.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_verify.json")) else {}
    a = json.load(open(os.path.join(here, name + "_asm.json"), encoding="utf-8"))["steps"]
    cnt = {}
    for i in range(1, len(a) + 1):
        e = db.get(str(i))
        if not e: t = "미검증"
        elif e.get("지문") != stepfp.fp(a[i - 1]): t = "낡음(내용 바뀜)"
        else: t = e["상태"]
        cnt.setdefault(t, []).append(i)
    for t in ("통과", "주의", "실패", "낡음(내용 바뀜)", "미검증"): print("%-14s %2d개  %s" % (t, len(cnt.get(t, [])), (" ".join(map(str, cnt[t])) if t in cnt and len(cnt[t]) <= 30 else "")))
    sys.exit(0)
steps = [int(v) for v in sys.argv[2:]]
R = os.path.join(here, "refs", name)
def jl(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None
asm = jl(os.path.join(here, name + "_asm.json")); read = jl(os.path.join(here, name + "_read.json")) or {}; index = jl(os.path.join(R, "index.json")) or []
def cam_of(n):
    try: c = asm["steps"][n - 1]["cam"]; return float(c["theta"]), float(c["phi"]), asm["steps"][n - 1].get("camSrc")
    except Exception: return None
summary = {}; msgs_by_step = {}
for N in steps:
    print("═══ %s %d번 점검 ═══" % (name, N)); res = []; msgs_ = {}
    def add(tag, ok, text):   # 확인한 것 / 안 한 것 말투로 바꿔 저장한다 — 이 도구의 목적은 "책과 맞는지 확인"이고, 확인이 안 되면 무엇을 안 해서인지 남기는 것
        _what = {"홀라인": ("책 그림의 구멍 줄(홀라인)을 맞춰 모델을 책 위에 겹쳐 비교할 수 있게 함", "책 그림의 구멍 줄(홀라인)을 정확히 맞추지 않아 모델과 책을 겹쳐 비교하지 못함"),
                 "양쪽 홀라인": ("결합하는 부품과 결합되는 부품 양쪽의 구멍 격자를 모두 그려 책 링 칸을 각각 셈", "받는 쪽·끼우는 쪽 중 한쪽 구멍 격자만 있음(fits/NN_*.json 이 2개 미만)"),
                 "카메라": ("책과 같은 각도의 카메라를 풀어 모델을 책과 같은 각도로 봄", "책과 같은 각도의 카메라를 정확히 못 풀어 모델과 책의 각도 비교가 부정확함"),
                 "돌기↔구멍": ("모델에서 새 부품의 돌기가 구멍에 들어가는지 숫자로 봄", "모델에서 돌기↔구멍이 맞는지 숫자로 못 봄/안 맞음"),
                 "번호 대조 그림": ("책 링 번호와 모델 결합 구멍 번호가 같은지 그림으로 대조함", "책 링 번호와 모델 결합 구멍 번호를 그림으로 대조하지 않음"),
                 "읽기 표": ("책에서 읽은 근거(링·방향·판단과정)를 읽기 표에 남김", "책에서 읽은 근거를 읽기 표에 다 남기지 않음"),
                 "증거": ("3D 화면과 책을 나란히 본 기록을 남김", "3D 화면과 책을 나란히 본 기록이 없거나, 고친 뒤 다시 안 봄")}.get(tag, ("", ""))
        text = ("확인함: " + _what[0] + " — " + text) if ok == "ok" else ("안 한 것: " + _what[1] + " (" + text + ")")
        res.append((tag, ok)); msgs_[tag] = text; print("  %s %s — %s" % ({"ok": "✅", "warn": "⚠", "fail": "❌"}[ok], tag, text))
    # 1 홀라인
    f = jl(os.path.join(R, "fits", "%02d_P.json" % N))
    if not f: add("홀라인", "fail", "fits/%02d_P.json 없음" % N)
    else:
        tool = f.get("tool", "?"); err = f.get("err_px")
        if tool == "via-later":   # 판이 없는 번호: 이 번호의 부품이 다시 보이는 뒤 번호의 홀라인·번호 대조가 통과하면 결합이 확인된 것으로 본다(사용자 2026-10-18)
            _vv = (jl(os.path.join(here, name + "_verify.json")) or {}).get(str(f.get("via")), {})
            add("홀라인", "ok" if _vv.get("상태") == "통과" else "warn", "뒤 번호 %s번 점검 %s 로 대신 확인(블록만 있는 번호)" % (f.get("via"), _vv.get("상태", "안 돌림")))
            tool = None
        if tool is None: pass
        elif tool == "blob-lattice": add("홀라인", "ok" if (err is not None and err <= 2.0) else "warn", "구멍 흰 조각 격자 %s개 평균 %spx(기준 2.0)" % (f.get("found"), err))
        elif tool == "anchor-pnp": add("홀라인", "warn", "격자 아님 — 앵커 점으로 푼 값(⚠ 구멍 중심 검출 아님)")
        elif tool in ("manual", None, "?"): add("홀라인", "fail", "손으로 읽은 점 — 홀라인을 다시 맞춘다")
        else: add("홀라인", "ok", "도구 %s" % tool)
    # 2 카메라
    ax = jl(os.path.join(R, "%02d_axes.json" % N)); c = cam_of(N)
    if not ax or "fit" not in ax: add("카메라", "fail", "axes 에 fit(오차)이 없음 — 손으로 쓴 값")
    else:
        e = ax["fit"].get("err_px"); msgs = []; st = "ok"
        if e is None or e > 2.0: st = "warn"; msgs.append("오차 %spx > 2.0" % e)
        else: msgs.append("오차 %.2fpx" % e)
        if c:
            if abs(c[0] - ax["fit"].get("theta", 99)) > 0.011 or abs(c[1] - ax["fit"].get("phi", 99)) > 0.011: st = "fail"; msgs.append("모델 cam(%.2f,%.2f) ≠ axes fit(%.2f,%.2f) — 풀이값이 모델에 안 들어감" % (c[0], c[1], ax["fit"].get("theta"), ax["fit"].get("phi")))
            if c[2] == "guess": st = "fail" if st != "fail" else st; msgs.append("camSrc=guess")
            for m in (N - 1, N + 1):
                o = cam_of(m)
                if o and abs(o[0] - c[0]) < 0.005 and abs(o[1] - c[1]) < 0.005: st = "fail"; msgs.append("%d번과 같은 값(복사?)" % m)
        add("카메라", st, ", ".join(msgs))
    # 3 돌기↔구멍
    _st = [N]
    try: _st += sorted({int(k.split(":")[0]) for k in (asm["steps"][N - 1].get("moveMade") or {})} - {N})   # 합치는·옮기는 번호는 옮겨진 부품의 맞물림도 본다
    except Exception: pass
    out = run("_mates_table.py", name, *[str(v) for v in _st]); lines = [l for l in out.splitlines() if "옆" in l]; bad = []
    for l in lines:
        if "⚠" not in l: continue
        m = re.search(r"깊이 (-?[\d.]+)", l)
        if m and abs(float(m.group(1))) > 8: continue   # 구멍에서 8mm 넘게 떨어진 우연한 근접(결합 아님)은 세지 않는다
        bad.append(l)
    if not lines: add("돌기↔구멍", "warn", "맞물림 줄 없음(합치는 번호거나 맞물림 안 찾음) — 눈으로 확인")
    elif bad: add("돌기↔구멍", "fail", "%d줄 ⚠: %s" % (len(bad), bad[0].strip()[:70]))
    else: add("돌기↔구멍", "ok", "%d줄 전부 ✅" % len(lines))
    # 3-1 양쪽 홀라인(사용자 2026-10-19): 결합하는 부품·결합되는 부품 구멍 격자를 모두 그린다 — fits/NN_<라벨>.json 이 2개 이상
    _fl = [x for x in os.listdir(os.path.join(R, "fits")) if re.match(r"%02d_[A-Za-z0-9]+\.json$" % N, x)] if os.path.isdir(os.path.join(R, "fits")) else []
    add("양쪽 홀라인", "ok" if len(_fl) >= 2 else "warn", ("격자 %s" % sorted(_fl)) if len(_fl) >= 2 else "격자 %d개뿐(%s) — 받는 쪽과 끼우는 쪽 둘 다 필요" % (len(_fl), ",".join(_fl)))
    # 4 번호 대조 그림
    imgs = [x for x in index if x.get("step") == N and x.get("idx", 0) >= 3 and ("번호" in x.get("note", "") or "대조" in x.get("note", "") or "M" in x.get("note", ""))]
    add("번호 대조 그림", "ok" if imgs else "warn", ("idx %s" % [x["idx"] for x in imgs]) if imgs else "책 링↔모델 구멍 번호 대조 그림 없음(_cellcmp.py 또는 번호판 그림)")
    # 5 읽기 표
    r = read.get(str(N)) or {}; need = ("면", "링", "부품", "방향", "부품방향", "대조", "판단과정"); miss = [k for k in need if not str(r.get(k, "")).strip()]
    if miss: add("읽기 표", "fail", "빈 칸: " + ", ".join(miss))
    else:
        w = str(r["판단과정"]); evid = bool(re.search(r"px|칸|표|mm|✅", w))
        add("읽기 표", "ok" if evid else "warn", "전부 참" + ("" if evid else " — 판단과정에 칸·px·표 같은 근거가 없음"))
    # 6 증거
    rc = run("rulecheck.py", name, str(N)); ev = [l for l in rc.splitlines() if "증거" in l]
    if any("✅증거" in l for l in rc.splitlines()): add("증거", "ok", "record_check 지문 일치")
    else: add("증거", "fail", ev[0].strip()[:80] if ev else "증거 확인 불가")
    summary[N] = res; msgs_by_step[N] = msgs_; print()
import time, stepfp
vf = os.path.join(here, name + "_verify.json"); vdb = jl(vf) or {}
for N, res in summary.items():
    _d = dict(res); _must = [_d.get("증거")] if N >= 18 else [_d.get("홀라인"), _d.get("번호 대조 그림")]   # 18번부터(사용자 2026-10-19): 통과 = 책 비교 증거 + 다음 책 대조. 홀라인·양쪽 홀라인·카메라·돌기↔구멍·번호 대조·읽기 표는 안 맞을 때 원인을 찾는 점검 항목이라 통과를 막지 않는다
    st = "통과" if all(o == "ok" for o in _must) else ("실패" if any(o == "fail" for o in _must) else "주의")
    vdb[str(N)] = {"상태": st, "항목": {t: o for t, o in res}, "지문": stepfp.fp(asm["steps"][N - 1]), "시각": time.strftime("%Y-%m-%d %H:%M"), "내용": msgs_by_step.get(N, {})}
json.dump(vdb, open(vf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 뒤 번호로 확인(사용자 2026-10-18, 같은 날 정정): "다음 번호가 진행됐다"는 것만으로는 증명이 아니다(내가 억지로 진행시켰을 수 있다).
#   이 번호의 부품이 나오는 뒤 번호 책에서 **그 부품을 책과 실제로 비교한 그림**이 있어야 한다 — 그 기록을 <이름>_via.json 에 적는다:
#     {"4": [{"step": 7, "image": "07_4.jpg", "what": "블록 셋 돌기 8개를 7번 책 돌기에 찍어 일치"}]}
#   인정 조건: ① 기록한 그림 파일이 있고 ② 그 뒤 번호가 스스로 통과(홀라인·번호 대조)이고 ③ 그 번호 화면에 이 번호 부품이 실제로 보임. 기록이 없으면 '안 한 것'으로 남긴다.
_steps = asm["steps"]; _NS = len(_steps)
_via = jl(os.path.join(here, name + "_via.json")) or {}
def _shows(n, m):
    if str(n) in ((_steps[m - 1].get("hideMade")) or {}): return False
    if _steps[m - 1].get("slot") == _steps[n - 1].get("slot"): return True
    return any(str(k).split(":")[0] == str(n) for k in (_steps[m - 1].get("moveMade") or {}))
def _own_pass(m):
    e = vdb.get(str(m), {}); return e.get("상태") == "통과" and not e.get("확인")
for _sk in sorted(vdb, key=int):
    _n = int(_sk); _e = vdb[_sk]; _e.pop("확인", None); (_e.get("항목") or {}).pop("뒤 번호 확인", None)
    if _n < 18 and _own_pass(_n): continue
    _recs = _via.get(str(_n)) or []; _good = [r for r in _recs if os.path.exists(os.path.join(R, r.get("image", "_없음_"))) and (r.get("book_only") or (_own_pass(r.get("step", 0)) and _shows(_n, r.get("step", 0))))]   # book_only = 다음 번호 모델은 아직 없고 그 책 그림에서 이 번호 조립이 적용된 모양을 비교한 기록(사용자 2026-10-19)
    if _n >= 18 and _e.get("상태") == "통과" and not _good: _e["상태"] = "주의"   # 18번부터: 책 비교 증거만으로는 통과가 아니다 — 다음 책 대조도 필요
    if _n >= 18 and _e.get("상태") != "통과":   # 안 맞을 때만 규칙 점검: 어느 규칙·도구 항목이 ⚠·❌ 인지 원인 후보로 적어 둔다
        _e.setdefault("내용", {})["원인 점검"] = "규칙 점검 항목 중 ⚠·❌: " + (", ".join(t for t, o in (_e.get("항목") or {}).items() if o != "ok" and t not in ("뒤 번호 확인", "증거")) or "없음")
    if _good:
        _e["확인"] = "뒤 번호 " + ", ".join("%s번(%s)" % (r["step"], r["image"]) for r in _good) + " 책에서 이 번호 부품을 비교해 확인"
        if _n < 18 or (_e.get("항목") or {}).get("증거") == "ok": _e["상태"] = "통과"
        _e.setdefault("항목", {})["뒤 번호 확인"] = "ok"; _e.setdefault("내용", {})["뒤 번호 확인"] = "확인함: " + _e["확인"] + " — " + "; ".join(r.get("what", "") for r in _good)
    else:
        _conf = [m for m in range(_n + 1, _NS + 1) if _shows(_n, m)][:6]
        _e.setdefault("항목", {})["뒤 번호 확인"] = "warn"
        _e.setdefault("내용", {})["뒤 번호 확인"] = "안 한 것: 이 번호 부품이 나오는 뒤 번호(%s번) 책에서 이 부품을 책과 비교한 그림을 남기지 않음(<이름>_via.json 에 기록)" % (", ".join(str(v) for v in _conf) if _conf else "없음/안 찾음")
        if _recs: _e["내용"]["뒤 번호 확인"] += " — 기록은 있으나 그림 없음·뒤 번호 미통과·화면에 안 보임 중 하나"
json.dump(vdb, open(vf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 조립 보기의 "☑ 검증 체크" 모달(관리자만)이 읽도록 ivs_assembly_checks 에 저장한다: issue_key = 'auto:<항목>', verdict = ok(통과) / fix(주의·실패), note = '상태|문장'.
#   public 폴더에는 아무것도 쓰지 않는다 — 관리자만 보이게(사용자 지시 2026-10-18). 서비스 키는 .env.local.
try:
    import urllib.request
    _env = dict(l.strip().split("=", 1) for l in open(os.path.join(here, "..", "..", ".env.local"), encoding="utf-8") if "=" in l and not l.startswith("#"))
    _u = _env["SUPABASE_URL"].strip('"'); _k = _env["SUPABASE_SERVICE_ROLE_KEY"].strip('"')
    _txt = open(os.path.join(here, "..", "..", "public", "design-assemblies.js"), encoding="utf-8").read()
    _m = re.search("cubo-[0-9]+-" + re.escape(name) + "(?![A-Za-z0-9_])", _txt)
    if _m:
        _rows = []
        for _sk2, _e in vdb.items():
            for _t, _o in (_e.get("항목") or {}).items():
                _rows.append({"assembly_id": _m.group(0), "step": int(_sk2), "issue_key": "auto:" + _t, "verdict": "ok" if _o == "ok" else "fix", "note": _o + "|" + ((_e.get("내용") or {}).get(_t, "")), "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S+09:00")})
        _rq = urllib.request.Request(_u + "/rest/v1/ivs_assembly_checks?on_conflict=assembly_id,step,issue_key", data=json.dumps(_rows).encode("utf-8"), method="POST",
                                     headers={"apikey": _k, "Authorization": "Bearer " + _k, "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"})
        urllib.request.urlopen(_rq); print("검증 결과를 DB(관리자 표)에 저장:", len(_rows), "줄")
except Exception as _e: print("검증 결과를 DB 에 못 썼다:", _e)
print("═══ 요약 ═══"); tags = ["홀라인", "양쪽 홀라인", "카메라", "돌기↔구멍", "번호 대조 그림", "읽기 표", "증거"]
print("%-5s" % "번호" + "".join("%-12s" % t for t in tags))
fails = 0
for N, res in summary.items():
    d = dict(res); print("%-5d" % N + "".join("%-12s" % {"ok": "✅", "warn": "⚠", "fail": "❌"}.get(d.get(t), "-") for t in tags)); fails += sum(1 for t, o in res if o == "fail" and t in ("홀라인", "번호 대조 그림"))
sys.exit(1 if fails else 0)
