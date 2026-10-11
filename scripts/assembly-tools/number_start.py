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

asm = load(os.path.join(here, name + "_asm.json"), {"steps": []})["steps"]
if not 1 <= k <= len(asm): sys.exit("❌ %s 에 %d번이 없다(번호 %d개). 먼저 01 번호 등록을 한다." % (name, k, len(asm)))
st = asm[k - 1]; note = st.get("note", "")
m = re.search(r"▣ 사용 부품:\s*(.*)", note); used = m.group(1).strip() if m else ""
def strip_paren(t):   # "리벳 2 (그림 옆 (2)), 축 1 (추정)" → "리벳 2, 축 1"
    prev = None
    while prev != t: prev, t = t, re.sub(r"\s*\([^()]*\)", "", t)
    return t
parts = "" if (not used or used.startswith("없음")) else ", ".join(x.strip() for x in strip_paren(used).split(",") if x.strip())

# ① 읽기 표 칸
rp = os.path.join(here, name + "_read.json"); rd = load(rp, {})
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
