# 번호 시작 도우미 — 05 조립 과정에서 번호 하나를 시작할 때 매번 손으로 하던 준비를 대신한다.
#   python number_start.py <이름> <번호>
# 하는 일: ① 읽기 표(<이름>_read.json)에 그 번호 칸을 만들고 '부품'을 03 에서 적은 "▣ 사용 부품" 으로 채운다(이미 있으면 건드리지 않는다)
#          ② <이름>_rules.json 의 strict·orient_check·placecheck 를 켠다 ③ 그 번호의 파일 상태와 창고·✓ 상태를 보여 주고 다음에 할 일을 순서대로 적는다.
# 하지 않는 일: 방향·격자·자세 같은 판단은 하지 않는다(그림을 읽는 사람이 한다). axes 파일은 만들지 않는다(0 값이 진짜로 오해되는 것을 막으려고).
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))
name, k = sys.argv[1], int(sys.argv[2]); NN = "%02d" % k
def load(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 세션 시작 체크(사용자 지시 2026-10-13 "다시 시작하면 개발서버와 로그인을 체크해서 먼저 요청") — 번호 작업·계산에 들어가기 전에 이 블록을 읽고, ❌ 는 사용자에게 먼저 요청한다.
def _session_check():
    import urllib.request
    up = None
    for port in (3178, 3177, 3179):
        try: urllib.request.urlopen("http://localhost:%d/design.html" % port, timeout=4).read(1); up = port; break
        except Exception: pass
    root = os.path.abspath(os.path.join(here, "..", ".."))
    env = os.path.join(root, ".env.local"); envtxt = open(env, encoding="utf-8").read() if os.path.exists(env) else ""
    keys = all(k_ in envtxt for k_ in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"))
    db = None
    if keys:
        try:
            import userdone; _m = re.search(r'Asm\("([^"]+)"', open(os.path.join(here, name + ".py"), encoding="utf-8").read())
            db = sorted(userdone.user_done(_m.group(1)) or ())
        except (SystemExit, Exception): db = None
    print("═══ 세션 시작 체크 (번호 작업 전에 읽는다) ═══")
    print("  %s 개발 서버: %s" % ("✅" if up else "❌", ("localhost:%d 응답" % up) if up else "응답 없음 → 서버를 켠다(preview_start invent-school-dev2), 다른 채팅 서버가 이미 있으면 그 포트를 쓴다"))
    print("  %s .env.local(SUPABASE 키): %s" % ("✅" if keys else "❌", "있음" if keys else "없음 → 사용자에게 달라고 한다(CLAUDE.md)"))
    print("  %s DB 읽기(사용자 ✓): %s" % ("✅" if db is not None else "❌", ("읽음 — ✓ 번호 %s" % db) if db is not None else "못 읽음 → 멈춘다(통과시키지 않는다)"))
    print("  ⚠ 로그인: 스크립트가 확인할 수 없다. 화면 비교(05 5-5)·❄/📷 확인에는 선생님 계정 로그인이 필요하므로 **새로 시작하거나 새 세션이면 사용자에게 먼저 요청한다**(비밀번호는 대신 입력하지 않는다). 브라우저 pane 에서 로그인 화면이 보이면 아직이다.")
    print("  ⚠ 읽을 것: SKILL.md 처음부터 → process/05_조립.md 체크리스트 → HANDOFF_<이름>.md → user_diffs/요청차이.md (이번 번호에서 지킬 규칙 3개를 첫 보고 한 줄에)")
    return up
_SERVER = _session_check()

# ── 알고 있는 정보 리마인드(사용자 지시 2026-10-13 "새 번호에 들어가면 이미지 작업부터 하지 말고, 이미 알고 있는 정보를 먼저 파악하자" — 드롭체커 28번) ──
# 이미지 작업(격자·모서리·홀라인) 전에 앞 번호까지 만든 것·쓴 부품·남은 부품·사용자가 바로잡은 것을 먼저 보여 준다. 읽기만 하고 아무것도 쓰지 않는다. 못 읽어도 번호 시작은 막지 않는다.
def _remind():
    try:
        print("═══ 이미 알고 있는 정보 — 이미지 작업 전에 읽는다 (%s %d번) ═══" % (name, k))
        a_ = load(os.path.join(here, name + "_asm.json"), {"steps": []})["steps"]; lst = load(os.path.join(here, name + "_list.json"), {})
        # ① 쓴 부품 / 남은 부품 (LIST 대비, 앞 번호까지)
        used = {}
        for st_ in a_[:k - 1]:
            for pt_ in st_.get("parts", []): used[pt_.get("n")] = used.get(pt_.get("n"), 0) + 1
        left = {n_: c_ - used.get(n_, 0) for n_, c_ in lst.items() if n_ != "리모컨" and c_ - used.get(n_, 0) > 0}   # 리모컨은 조립도에 넣지 않는다(사용자 지시 2026-10-14)
        print("  ① 앞 번호(%d번)까지 쓴 부품 %d개 / 남은 부품(LIST 대비): %s" % (k - 1, sum(used.values()), ", ".join("%s %d" % (n_, c_) for n_, c_ in left.items()) or "없음"))
        # ② 앞 번호 읽기 표 — 놓은 방법·열린 사항(정정·확인 대기)
        rd = load(os.path.join(here, name + "_read.json"), {})
        for j_ in (k - 1, k - 2):
            e_ = rd.get(str(j_)) or {}
            if e_: print("  ② %d번 읽기 표 — 부품방향: %s" % (j_, str(e_.get("부품방향", ""))[:260].replace(chr(10), " "))); print("       열린 사항·정정: %s" % (" / ".join(x_ for x_ in str(e_.get("판단과정", "")).split("★") [1:])[:260] or "없음"))
        # ③ 앞 번호 코드가 정한 짝·창고 (history·slot)
        prev = a_[k - 2] if 1 < k <= len(a_) else {}
        print("  ③ 앞 번호 창고 %s · 이번 번호 창고 %s | 앞 번호 history: %s" % (prev.get("slot"), (a_[k - 1].get("slot") if k <= len(a_) else "?"), str(prev.get("history", ""))[:120] or "-"))
        # ④ 사용자가 바로잡은 최근 항목(같은 실수 반복 금지)
        dif = os.path.join(here, "user_diffs", "요청차이.md")
        if os.path.exists(dif):
            heads = [l_.strip() for l_ in open(dif, encoding="utf-8").read().splitlines() if l_.startswith("## ")][-4:]
            print("  ④ 사용자가 최근 바로잡은 것(user_diffs/요청차이.md 끝 4개):"); [print("       " + h_[:110]) for h_ in heads]
        print("  ⑤ 놓을 자리는 모델로 먼저 좁힌다: python pegprobe.py %s 빈구멍 <칸> <줄> · 위돌기 · 빈돌기 <부품> — 그다음에 책 그림으로 후보 중 어느 것인지 가린다(이미지 격자는 카메라·화면 비교용)." % name)
        _pf = os.path.join(here, "refs", name, "fits", "%02d_P.json" % (k - 1))
        if os.path.exists(_pf):   # 29번에서 배운 것: 판이 가려져 holefit 가 안 되면 앞 번호 책 그림과 판 무늬를 맞춘다(눈으로 안 된다고 건너뛰지 말고 도구를 먼저 돌린다)
            print('  ⑥ 판이 이번 번호에서 가려졌으면(앞 번호 %d 판 격자 있음): holefit → python plate_match.py %s %d %d P --검증 "c,r,h,x,y;…" (앞 번호에서 놓아 3D 가 확정된 리벳 끝·블록 돌기·판 모서리 5개 이상의 칸·높이·픽셀) → infer_grid --anchor. 05_조립.md 0-2 절. 유추 격자는 규칙 점검이 사용자 ✓ 를 요구한다.' % (k - 1, name, k - 1, k))
        print("  ⑦ 진행 상태 문서: process/HANDOFF_%s.md (앞 번호 절) — 번호 하나로 안 풀리면 05_조립.md 0-1 절." % name)
    except Exception as ex_:
        print("  (리마인드를 읽지 못했다: %s — 번호 시작은 계속한다)" % ex_)
_remind()
asm = load(os.path.join(here, name + "_asm.json"), {"steps": []})["steps"]
if not 1 <= k <= len(asm): sys.exit("❌ %s 에 %d번이 없다(번호 %d개). 먼저 01 번호 등록을 한다." % (name, k, len(asm)))
st = asm[k - 1]; note = st.get("note", "")
m = re.search(r"▣ 사용 부품:\s*(.*)", note); used = m.group(1).strip() if m else ""
def strip_paren(t):   # "리벳 2 (그림 옆 (2)), 축 1 (추정)" → "리벳 2, 축 1"
    prev = None
    while prev != t: prev, t = t, re.sub(r"\s*\([^()]*\)", "", t)
    return t
parts = "" if (not used or used.startswith("없음")) else ", ".join(x.strip() for x in strip_paren(used).split(",") if x.strip())

# ⓪ 앞 과정 점검(사용자 지시 2026-10-12 "앞순서에 안한게 있으면 하고 넘어가야 하게끔") — 02·03·04 와 앞 번호 확인이 끝나지 않았으면 여기서 멈춘다.
#    읽기 표·규칙 파일도 만들지 않고, 격자·구멍 점 같은 번호 작업은 시작할 수 없다. 끝낸 뒤 다시 돌린다.
_gate = []
_R0 = os.path.join(here, "refs", name)
_miss_img = [i for i in range(0, len(asm) + 1) if i and not os.path.exists(os.path.join(_R0, "%02d.jpg" % i))]
if not os.path.exists(os.path.join(_R0, "00.jpg")): _miss_img.insert(0, 0)
if _miss_img: _gate.append(("02 이미지 자르기", "책 그림이 없는 번호: %s" % _miss_img[:12], "refs_make.py 로 만든다(02)"))
if not os.path.exists(os.path.join(_R0, "00_1.jpg")): _gate.append(("02 완성품 방향선 그림", "완성 사진과 한 세트인 방향선 그림(refs/%s/00_1.jpg)이 없다" % name, "02_이미지_자르기.md 3-2 로 만들어 올린다(앞 +Z · 뒤 −Z · 위 +Y · 왼쪽 +X · 오른쪽 −X, 사용자 확인) — 00_개선규칙 9번"))
_miss_used = [i for i, s in enumerate(asm, 1) if "▣ 사용 부품:" not in (s.get("note") or "")]
if _miss_used: _gate.append(("03 부품 체크", "▣ 사용 부품이 없는 번호: %s" % _miss_used[:15], "번호별 사용 부품을 적고 LIST 와 대조한다(03 B)"))
_miss_slot = [i for i, s in enumerate(asm, 1) if s.get("slot") is None]
_miss_hist = [i for i in range(2, len(asm) + 1) if asm[i - 1].get("slot") is not None and asm[i - 2].get("slot") is not None and asm[i - 1]["slot"] != asm[i - 2]["slot"] and not asm[i - 1].get("history")]
if _miss_slot: _gate.append(("04 창고 정리", "창고(slot)가 없는 번호: %s" % _miss_slot[:15], "번호마다 slot·history 를 적는다(04) — 스크립트를 고쳤으면 python %s.py 로 asm 을 다시 만든다" % name))
if _miss_hist: _gate.append(("04 창고 정리", "창고가 바뀌는데 history 가 없는 번호: %s" % _miss_hist[:15], "history 글을 적는다(04)"))
if k > 1:   # 앞 번호: 사용자 ✓ 또는 지금 내용과 같은 지문의 비교 증거(record_check)가 있어야 다음 번호를 시작한다
    _prev = asm[k - 2]
    if _prev.get("noPart") or not (_prev.get("parts") or _prev.get("moveMade")): _gate.append(("앞 번호 %d" % (k - 1), "아직 작성 전(부품 없음)", "앞 번호부터 끝낸다 — 번호는 순서대로"))
    else:   # 부품이 있는 번호, 또는 앞 번호 부품을 옮기기만 하는(합치는) 번호
        _ok = False
        try:
            import stepfp; _ev = load(os.path.join(here, name + "_evidence.json"), {}).get(str(k - 1))
            _ok = bool(_ev and _ev.get("fp") == stepfp.fp(_prev))
        except Exception: pass
        if not _ok:
            try:
                import userdone; _mid0 = re.search(r'Asm\("([^"]+)"', open(os.path.join(here, name + ".py"), encoding="utf-8").read())
                _ok = k - 1 in (userdone.user_done(_mid0.group(1)) or ())
            except (SystemExit, Exception): pass
        if not _ok: _gate.append(("앞 번호 %d" % (k - 1), "사용자 ✓ 도, 지금 내용과 같은 비교 증거(record_check)도 없음", "화면에서 책과 나란히 비교하고 record_check.py 로 증거를 남긴다(05 5-5)"))
if not _SERVER: _gate.append(("세션 시작 체크", "개발 서버가 응답하지 않음(3177·3178·3179 모두)", "서버를 켜고(preview_start invent-school-dev2 — 다른 채팅이 쓰는 중이면 그 포트를 그대로 쓴다) 사용자에게 로그인을 요청한다"))
try:   # 규칙 점검(rulecheck.py) — 앞 번호에 규칙 미달(❌)이 있으면 그것부터 해결해야 다음 번호를 시작한다(사용자 지시 2026-10-12: 도망가지 않고 스스로 문제를 찾아 해결)
    import rulecheck; _fb = rulecheck.first_bad(name)
    if _fb and _fb[0] < k:
        for _t, _why in _fb[1]:
            _gate.append(("규칙 점검 %d번" % _fb[0], "%s — %s" % (_t, _why), "python rulecheck.py %s %d 로 해결 방법을 보고 먼저 끝낸다(%s)" % (name, _fb[0], rulecheck.FIX.get(_t.split()[0], "05_조립.md"))))
except Exception as _e:
    _gate.append(("규칙 점검", "rulecheck 를 실행하지 못함: %s" % str(_e)[:80], "python rulecheck.py %s 를 돌려 오류를 본다" % name))
if _gate:
    print("═══ %s %d번 — ❌ 앞 과정이 끝나지 않았다: 이것부터 하고 넘어간다 ═══" % (name, k))
    for i, (p, why, how) in enumerate(_gate, 1): print("  %d. [%s] %s\n       → %s" % (i, p, why, how))
    sys.exit("(읽기 표·규칙 파일은 만들지 않았다. 위를 끝낸 뒤 다시 돌린다)")

# ① 읽기 표 칸
rp =os.path.join(here, name + "_read.json"); rd = load(rp, {})
if str(k) not in rd:
    rd[str(k)] = {"면": "", "링": "", "부품": parts, "대조": "", "방향": "", "부품방향": "", "판단과정": ""}; save(rp, rd); made = "새로 만듦(부품은 03 의 사용 부품으로 채움)"
else: made = "이미 있음(건드리지 않음)"
ent = rd[str(k)]

# ② 규칙 켜기
rlp = os.path.join(here, name + "_rules.json"); rl = load(rlp, {}); ch = False
for f in ("strict", "orient_check", "placecheck"):
    if rl.get(f) is not True: rl[f] = True; ch = True
if ch: save(rlp, rl)
script = os.path.join(here, name + ".py"); has_sc = os.path.exists(script) and "stepchecks.apply" in open(script, encoding="utf-8").read()

# ③ 상태
R = os.path.join(here, "refs", name); fits = os.path.join(R, "fits")
ax = load(os.path.join(R, NN + "_axes.json"), None)
state = [
    ("책 그림 크롭", os.path.exists(os.path.join(R, NN + ".jpg")), "refs/%s/%s.jpg" % (name, NN)),
    ("가위·회전값(_lv.json)", os.path.exists(os.path.join(R, NN + "_lv.json")), "refs/%s/%s_lv.json (crop·angle)" % (name, NN)),
    ("구멍 점(fits)", os.path.isdir(fits) and any(f.startswith(NN + "_") and f.endswith(".json") for f in os.listdir(fits)), "blobfit / fit_corners / fit_row → fits/%s_<라벨>.json" % NN),
    ("방향(_axes.json, fit 포함)", bool(ax and ax.get("fit")), "python axes_fit.py %s %d <라벨> <칸수> <줄수> <칸방향> <줄방향>" % (name, k)),
    ("격자 그림(NN_2)", os.path.exists(os.path.join(R, NN + "_2.jpg")), "python refs_rect.py %s %d" % (name, k)),
]
print("═══ %s %d번 시작 ═══   (SKILL.md 를 처음부터 다시 읽고, 이번 번호에서 지킬 규칙 3개를 첫 보고에 적는다)" % (name, k))
print("교재:", note.split("\n")[0][:80]); print("사용 부품(03):", used or "(적혀 있지 않음 — 03 을 먼저 한다)")
print("읽기 표 %d번 칸: %s" % (k, made)); print("스크립트에 stepchecks.apply:", "있음" if has_sc else "❌ 없음 — 넣지 않으면 --write 가 거부된다")
slot = st.get("slot"); pslot = asm[k - 2].get("slot") if k > 1 else None
print("창고: " + ("아직 정하지 않음 — 04 로 먼저 정한다" if slot is None else "이번 %s / 앞 번호 %s" % (slot, pslot) + ("  → 창고가 바뀌므로 history 글이 필요하다(04)" if k > 1 and slot != pslot else "")))
mid = re.search(r'Asm\("([^"]+)"', open(script, encoding="utf-8").read()) if os.path.exists(script) else None
try:
    import userdone; done = userdone.user_done(mid.group(1)) if mid else None
except SystemExit as e: done = None; print("(사용자 ✓ 목록을 읽지 못함 — 이 번호가 ✓ 인지 화면에서 먼저 본다)")
if done and k in done: print("✅ 이 번호는 사용자가 ✓ 완료로 표시했다 — 내용을 바꾸지 않는다")
# 사용자가 이 번호에 남긴 기록(❄ 모습 기록·📷 카메라)을 먼저 읽는다 — 사용자가 이미 고친 부품은 코드 값보다 사용자 값이 기준이다(사용자 기록 분석 2026-10-12: 자세를 고친 부품은 부시·메인보드·판 묶음에 몰려 있었다).
def _rest(path):
    import urllib.request, userdone
    env = userdone._env(); url = (env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")).rstrip("/"); key = env["SUPABASE_SERVICE_ROLE_KEY"]
    return json.loads(urllib.request.urlopen(urllib.request.Request(url + "/rest/v1/" + path, headers={"apikey": key, "Authorization": "Bearer " + key}), timeout=20).read().decode("utf-8"))
def _R(r):
    import numpy as np
    a, b, c = np.radians(r); Rx = np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]]); Ry = np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]]); Rz = np.array([[np.cos(c),-np.sin(c),0],[np.sin(c),np.cos(c),0],[0,0,1]])
    return Rz @ Ry @ Rx
try:
    import numpy as np, math
    if not mid: raise ValueError("조립도 id 를 스크립트에서 못 찾음")
    prow = _rest("ivs_assembly_poses?select=poses&assembly_id=eq.%s&step=eq.%d" % (mid.group(1), k)); crow = _rest("ivs_assembly_cams?select=cam&assembly_id=eq.%s&step=eq.%d" % (mid.group(1), k))
    dfn = load(os.path.join(here, name + "_def.json"), {}); xf = dfn.get("xform"); M = np.array(xf["m"], float) if (xf and k >= xf.get("at", 10**9)) else np.eye(3)
    cnt, code = {}, {}
    for si, st2 in enumerate(asm, 1):
        for q in st2.get("parts", []):
            cnt[q["n"]] = cnt.get(q["n"], 0) + 1
            if si == k: code["%s %d번" % (q["n"], cnt[q["n"]])] = q
    diff = []
    for lab, o in (prow[0]["poses"] if prow else {}).items():
        q = code.get(lab)
        if q and o.get("r") and not q.get("noFreeze") and not (q.get("side") and k < q["side"].get("until", 0)):
            rel = (M @ _R(q.get("r") or [0, 0, 0])).T @ _R(o["r"]); ang = math.degrees(math.acos(max(-1, min(1, (np.trace(rel) - 1) / 2))))
            if ang > 3: diff.append("%s(%d°)" % (lab, round(ang)))
    # 위치(p)도 비교한다(드롭체커 29번: 코드 hover 를 고쳐도 사용자 ❄ 기록의 위치가 화면을 덮어서 안 바뀌어 보였다 — 사용자 지정이 무조건 우선)
    posd = []
    for lab, o in (prow[0]["poses"] if prow else {}).items():
        q = code.get(lab)
        if q and o.get("p") and not q.get("noFreeze") and not (q.get("side") and k < q["side"].get("until", 0)):
            fin = np.array(q["p"], float); dr = np.array(q.get("dir") or [0, 0, 0], float); hv = (q.get("hover") or 0)
            cand = [fin] + ([fin + dr * hv] if hv and dr.any() else [])
            if min(float(np.linalg.norm((M @ c) - np.array(o["p"], float))) for c in cand) > 1.5: posd.append("%s" % lab)
    if posd: print("사용자 ❄ 기록 위치가 코드(제자리·띄운 자리)와 다른 부품(사용자 값이 기준이라 화면은 기록 위치로 보인다): " + ", ".join(posd[:12]) + (" …" if len(posd) > 12 else "") + " — 고치라는 지시면 pose_edit.py 로 기록을 고친다(백업 자동)")
    print("사용자 ❄ 모습 기록:", "없음" if not prow else "%d개 부품" % len(prow[0]["poses"]) + (" — 코드와 자세가 다른 부품(사용자 값이 기준): " + ", ".join(diff) if diff else " (코드와 자세가 모두 같음)"))
    cam = crow[0]["cam"] if crow else None; print("사용자 📷 카메라:", "없음" if not cam else "theta %s phi %s (이 값이 코드 cam 보다 기준)" % (cam.get("theta"), cam.get("phi")))
except Exception as e: print("(사용자 ❄·📷 기록을 읽지 못함: %s — 화면에서 먼저 확인한다)" % str(e)[:60])
star =[p for p in ("DC모터", "메인보드", "작은기어", "큰기어") if p in parts]
if star: print("⚠ 방향 기준 부품 있음: %s → 읽기 표에 방향 카드(measure_part·get_part_connectors + 책 증거)를 먼저 쓴다" % ", ".join(star))
print("─ 파일 상태 ─")
for t, ok, hint in state: print("  %s %s%s" % ("☑" if ok else "☐", t, "" if ok else "   ← " + hint))
filled = [f for f in ("면", "링", "부품", "방향", "부품방향", "대조") if str(ent.get(f, "")).strip()]
print("  %s 읽기 표 채움: %s (빈 칸: %s)" % ("☑" if len(filled) == 6 else "☐", ", ".join(filled) or "없음", ", ".join(f for f in ("면", "링", "부품", "방향", "부품방향", "대조") if f not in filled) or "없음"))
print("─ 다음에 할 일 (05 순서) ─")
todo = [t for t, ok, h in state if not ok]
order = ["책 그림 크롭", "가위·회전값(_lv.json)", "구멍 점(fits)", "방향(_axes.json, fit 포함)", "격자 그림(NN_2)"]
for i, t in enumerate([o for o in order if o in todo], 1): print("  %d. %s" % (i, t))
print("  → 읽기 표 빈 칸 → 놓기(attach·recv) → python build.py %s --write → 화면 비교 → python record_check.py %s %d <캡처.png> \"<비교 결과>\"" % (name, name, k))
