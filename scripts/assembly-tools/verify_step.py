# 번호 하나의 조립 결과를 한 번에 점검한다 — 번호마다 같은 검사를 손으로 돌려 빠뜨리지 않게 (2026-10-18 사용자 요청)
#   python verify_step.py <이름> <번호> [<번호>…]      (여러 번호 가능, 예: 5 6 7)
# 점검(✅ 통과 / ⚠ 확인 필요 / ❌ 실패):
#   1 홀라인   fits/NN_P.json 이 있고 도구·오차(px)가 기준 안인가 (blob-lattice·holefit 평균 ≤2.0px, 앵커 ≤2.0px 아니면 ⚠)
#   2 카메라   NN_axes.json 의 fit 오차 ≤2.0px, 모델에 실제로 들어간 theta·phi 가 axes 값과 같은가, 앞·뒤 번호와 같은 값(복사)이 아닌가
#   3 돌기↔구멍 _mates_table 결과에 ⚠ 가 없고 새 부품마다 맞물림 줄이 있는가
#   4 번호 대조 그림  책 링 ↔ 모델 구멍 번호를 적은 NN_4~ 그림(index.json idx≥3)이 있는가
#   5 읽기 표   면·링·부품·방향·부품방향·대조·판단과정이 다 차 있는가, 판단과정에 근거(칸·px·표)가 있는가
#   6 증거      record_check 증거가 지금 내용과 같은 지문인가(rulecheck 판정)
# 마지막에 번호별 요약 표. ❌ 가 있으면 종료 코드 1. 결과는 <이름>_verify.json 에 번호별로 저장(상태·항목·그때의 내용 지문) —
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
    def add(tag, ok, text): res.append((tag, ok)); msgs_[tag] = text; print("  %s %s — %s" % ({"ok": "✅", "warn": "⚠", "fail": "❌"}[ok], tag, text))
    # 1 홀라인
    f = jl(os.path.join(R, "fits", "%02d_P.json" % N))
    if not f: add("홀라인", "fail", "fits/%02d_P.json 없음" % N)
    else:
        tool = f.get("tool", "?"); err = f.get("err_px")
        if tool == "blob-lattice": add("홀라인", "ok" if (err is not None and err <= 2.0) else "warn", "구멍 흰 조각 격자 %s개 평균 %spx(기준 2.0)" % (f.get("found"), err))
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
    st = "실패" if any(o == "fail" for _, o in res) else ("주의" if any(o == "warn" for _, o in res) else "통과")
    vdb[str(N)] = {"상태": st, "항목": {t: o for t, o in res}, "지문": stepfp.fp(asm["steps"][N - 1]), "시각": time.strftime("%Y-%m-%d %H:%M"), "내용": msgs_by_step.get(N, {})}
json.dump(vdb, open(vf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 조립 보기의 "☑ 검증 체크" 모달이 읽는 사본: public/assembly-verify/<조립도 id>.json (지문은 뺀다)
try:
    _txt = open(os.path.join(here, "..", "..", "public", "design-assemblies.js"), encoding="utf-8").read()
    _pat = "cubo-[0-9]+-" + re.escape(name) + "(?![A-Za-z0-9_])"
    _m = re.search(_pat, _txt)
    if _m:
        _pd = os.path.join(here, "..", "..", "public", "assembly-verify"); os.makedirs(_pd, exist_ok=True)
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != "지문"} for k, v in vdb.items()}, open(os.path.join(_pd, _m.group(0) + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("모달용 사본:", "public/assembly-verify/" + _m.group(0) + ".json")
except Exception as _e: print("모달용 사본을 못 썼다:", _e)
print("═══ 요약 ═══"); tags = ["홀라인", "카메라", "돌기↔구멍", "번호 대조 그림", "읽기 표", "증거"]
print("%-5s" % "번호" + "".join("%-12s" % t for t in tags))
fails = 0
for N, res in summary.items():
    d = dict(res); print("%-5d" % N + "".join("%-12s" % {"ok": "✅", "warn": "⚠", "fail": "❌"}.get(d.get(t), "-") for t in tags)); fails += sum(1 for _, o in res if o == "fail")
sys.exit(1 if fails else 0)
