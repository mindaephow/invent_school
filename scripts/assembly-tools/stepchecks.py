# 번호마다 한 일을 체크박스로 보여 준다(관리자 지시 2026-10-08) — 허락을 받는 장치가 아니라 "뭐뭐를 했다"를 화면(개발서버 단계 설명)에 ☑/☐ 로 적어 두고 넘어가게 하는 장치다.
# 사용: 조립 스크립트 끝(save_links 앞)에서  import stepchecks; stepchecks.apply(A, "dog")
#   - 번호마다 점검 항목을 계산해 그 번호 설명(note) 끝에 "━ 작업 점검 ━" 블록으로 붙인다(빌드할 때마다 새로 계산).
#   - 막는 항목(blocking)은 <이름>_checks.json 에 적고, build.py 가 --write 때 막는다: 격자 그림 없음, 읽기 표 빈칸, 읽기 표 부품 ≠ 모델 부품, 쓴 부품 합계가 LIST 를 넘음.
#   - 사람이 눈으로 하는 항목(화면 확인·책과 나란히 비교·카메라)은 <이름>_rules.json 의 view/count/camera 목록에 번호가 있으면 ☑.
import json, os, re, collections
import numpy as np
import userdone, stepfp
MARK = "\n━ 작업 점검 ━"

def _counts(parts):
    c = collections.Counter(p.n for p in parts if "copyOf" not in p.extra); return c   # copyOf: 복사해서 다른 창고에 보관한 부품(asmlib copy_to_slot)은 읽기 표 부품 수에 넣지 않는다

def _parse(txt):   # "315프레임 1, 3단블록 1" → Counter (이름에 숫자가 있어도 마지막 숫자가 개수)
    c = collections.Counter()
    for part in re.split(r"[,，]", str(txt)):
        m = re.match(r"\s*(.+?)\s+(\d+)\s*$", part)
        if m: c[m.group(1).strip()] += int(m.group(2))
    return c

_DIMS = None
def _dims():
    global _DIMS
    if _DIMS is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dims.json")
        _DIMS = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    return _DIMS

def _pose(pt, k):   # k번에서의 자세: 옆자리에서 만드는 중이면 옆자리 자세, 아니면 그룹으로 옮겨지기 전(_base)이 있으면 그것
    from asmlib import euler_to_R
    sd = pt.extra.get("side")
    if sd and k < sd.get("until", 0): return np.array(sd["p"], float), np.array(euler_to_R(sd["r"]), float)
    b = getattr(pt, "_base", None)
    return (np.array(b[0], float), np.array(b[1], float)) if b else (np.array(pt.p, float), np.array(pt.R, float))

def bush_wrong(A, k):
    """k번의 부시 중 넓은 쪽(모델 −y)이 닿은 판 쪽을 향한 것(규칙: 좁은 쪽 +y 가 판 쪽)의 번호(0부터)를 돌려준다.
    판정 못 하는 것(닿는 부품 없음·양쪽 다 닿음)은 통과로 친다 — 틀린 것만 막는다."""
    dims = _dims(); bad = []
    others = [(q, *_pose(q, k)) for k2, st2 in enumerate(A.steps, 1) if k2 <= k for q in st2.parts if q.n not in ("부시", "축", "T축") and q.n in dims]
    def inside(pt, q, p, R):
        loc = R.T @ (pt - p); return bool(np.all(np.abs(loc) <= np.array(dims[q.n]) / 2 + 0.3))
    for i, b in enumerate(A.steps[k - 1].parts):
        if b.n != "부시": continue
        p, R = _pose(b, k); u = R @ np.array([0, 1, 0.])
        hn = any(inside(p + u * 3.4, q, qp, qR) for q, qp, qR in others)
        hw = any(inside(p - u * 3.4, q, qp, qR) for q, qp, qR in others)
        if hw and not hn: bad.append(i)
    return bad

def fastener_protrusion(A, k):
    """k번에서 새로 꽂은 볼트·너트의 가장 큰 부분(머리·너트 몸)이 프레임 면 밖으로 나온 만큼(mm)을 돌려준다 — 기본 규칙(사용자 지시 2026-10-24):
    볼트·너트의 가장 큰 부분은 프레임 구멍(홀라인) 안으로 들어가 프레임 외곽선 밖으로 안 나온다. 반환: [(부품, 받는 프레임, 나온 mm)] — 0.3 넘은 것만."""
    from asmlib import euler_to_R
    dims = _dims(); bad = []
    hide = A.steps[k - 1].kw.get("hideMade") or {}
    def pose_k(q):
        key = "%d:%d" % (q.step.index, q.step.parts.index(q))
        for j in range(k, 0, -1):
            e = (A.steps[j - 1].kw.get("moveMade") or {}).get(key)
            if e: return np.array(e["p"], float), np.array(euler_to_R(e["r"]), float)
        return _pose(q, k)
    pool = [(q, *pose_k(q)) for k2, st2 in enumerate(A.steps, 1) if k2 <= k and str(k2) not in hide for q in st2.parts if q.n in dims and "프레임" in q.n]
    for b in A.steps[k - 1].parts:
        if b.n not in ("8볼트", "12볼트", "너트") or not b.conn["pegs"]: continue
        bp, bR = pose_k(b); c = b.conn["pegs"][0]
        ld = np.array(c["dir"], float); dw = bR @ ld; ax = int(np.argmax(np.abs(ld))); half = np.array(dims[b.n], float)[ax] / 2
        base = bp + bR @ (np.array(c["pos"], float) - ld * c["len"] / 2)    # 돌기 밑동(구멍 입구 쪽 끝)
        back_t = float(np.dot(bp, dw) + (-half))                              # 부품 상자의 바깥쪽 끝(돌기 방향의 반대쪽) 좌표
        for q, p, R in pool:
            d = np.array(dims[q.n]) / 2; e = np.abs(R) @ d; lo, hi = p - e, p + e
            if np.all(base + dw * 1.0 >= lo - 0.3) and np.all(base + dw * 1.0 <= hi + 0.3):   # 밑동에서 구멍 쪽으로 1 들어간 점이 든 프레임 = 받는 프레임
                cs = [float(np.dot(np.array([x, y, z]), dw)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
                face_t = min(cs)   # 돌기가 들어가는 입구 면(돌기 방향 쪽으로 가장 안쪽이 아닌 바깥 면)
                prot = face_t - back_t
                if prot > 0.3: bad.append((b.n, q.n, round(prot, 1)))
                break
    return bad

def rivet_gaps(A, k):
    """k번에서 새로 꽂은 리벳마다, 리벳이 잇는 두 프레임(양끝이 든 부품) 사이의 틈(mm, +는 떠 있음, −는 겹침)을 돌려준다 — 기본 규칙(사용자 지시 2026-10-24):
    리벳으로 프레임과 프레임을 이으면 두 프레임은 딱 붙는다(틈 0, 겹침 0). 두 부품을 못 찾으면(한쪽만 꽂힌 결합 전 모습 등) 건너뛴다.
    반환: [(리벳 이름, 부품1 이름, 부품2 이름, 틈)] — 틈이 0.3 넘게 떠 있거나(6 이하) 1.0 넘게 겹친 것만."""
    from asmlib import euler_to_R
    dims = _dims(); bad = []
    hide = A.steps[k - 1].kw.get("hideMade") or {}
    def pose_k(q):   # k번 시점 자세: k번까지 옮겨진(moveMade) 마지막 자세, 없으면 놓은 자세
        key = "%d:%d" % (q.step.index, q.step.parts.index(q))
        for j in range(k, 0, -1):
            e = (A.steps[j - 1].kw.get("moveMade") or {}).get(key)
            if e: return np.array(e["p"], float), np.array(euler_to_R(e["r"]), float)
        return _pose(q, k)
    pool = [(q, *pose_k(q)) for k2, st2 in enumerate(A.steps, 1) if k2 <= k and str(k2) not in hide for q in st2.parts if q.n in dims and q.n != "리벳"]
    def box_of(q, p, R):
        d = np.array(dims[q.n]) / 2.0; e = np.abs(R) @ d; return p - e, p + e
    def host(pt, skip=None):
        for q, p, R in pool:
            if q is skip: continue
            lo, hi = box_of(q, p, R)
            if np.all(pt >= lo - 0.01) and np.all(pt <= hi + 0.01): return q, p, R
        return None
    for r in A.steps[k - 1].parts:
        if r.n != "리벳" or r.extra.get("copyOf"): continue   # 복사본(둘째 벌)은 원본 번호에서 이미 점검했다 — 복사 번호에서는 건너뜀
        rp, rR = pose_k(r)
        loc = {c["id"]: np.array(c["pos"], float) for c in r.conn["pegs"]}
        if "p1" not in loc or "p2" not in loc: continue
        t1, t2 = rp + rR @ loc["p1"], rp + rR @ loc["p2"]; ax = (t2 - t1) / np.linalg.norm(t2 - t1)
        h1 = host(t1 - ax * 1.0)
        if not h1: continue
        h2 = host(t2 + ax * 1.0, h1[0])
        if not h2 or any(x[0].n in ("1열브라켓", "2열브라켓") for x in (h1, h2)): continue   # 브라켓은 L 자 모양이라 상자로는 면 위치를 못 잰다 — 건너뜀
        def span(h):
            lo, hi = box_of(h[0], h[1], h[2]); cs = [float(np.dot(np.array([x, y, z]), ax)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]; return min(cs), max(cs)
        a, b = span(h1), span(h2); gap = max(b[0] - a[1], a[0] - b[1])
        if 0.3 < gap <= 6.0 or gap < -1.0: bad.append((r.n, h1[0].n, h2[0].n, round(gap, 1)))
    return bad


_AX = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
def mainboard_dir(A, k, txt):
    """메인보드 방향 검사(사용자 지시 2026-10-26, 볼링머신 36번 거꾸로 결합 재발): 모델에서 버튼 쪽(모델 +z)이 월드 어느 쪽인지 계산해,
    읽기 표 '부품방향' 에 적은 "버튼쪽=±X/Y/Z"(책 사진에서 읽은 쪽)와 다르면, 또는 안 적었으면 막는다. 돌려주는 값 = 문제 문구 목록."""
    import re
    bad = []
    bd = [b for b in A.steps[k - 1].parts if b.n == "메인보드"]
    if not bd: return bad
    m = re.search(r"버튼\s*쪽\s*=\s*([+\-−])\s*([XYZxyz])", txt or "")
    if not m: return ["읽기 표 '부품방향'에 책에서 읽은 \"버튼쪽=±X(또는 Y·Z)\" 가 없다(책 사진의 노란 버튼이 월드 어느 쪽인지 먼저 적는다)"]
    want = ("-" if m.group(1) in "-−" else "+") + m.group(2).upper()
    for i, b in enumerate(bd):
        p, R = _pose(b, k); u = R @ np.array([0, 0, 1.0])
        got = max(_AX, key=lambda a: float(np.dot(u, _AX[a])))
        if got != want: bad.append("메인보드 %d번째: 모델 버튼 쪽(+z)이 %s 인데 책에서 읽은 버튼쪽은 %s" % (i + 1, got, want))
    return bad

def apply(A, name):
    here = os.path.dirname(os.path.abspath(__file__))
    lst = json.load(open(os.path.join(here, name + "_list.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_list.json")) else {}
    lst.pop("리모컨", None)   # 리모컨은 조립도에 넣지 않는다(사용자 지시 2026-10-14) — LIST 대조에서 뺀다
    rd = json.load(open(os.path.join(here, name + "_read.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_read.json")) else {}
    rl = json.load(open(os.path.join(here, name + "_rules.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_rules.json")) else {}
    ip = os.path.join(here, "refs", name, "index.json")
    idx = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else []
    have = collections.defaultdict(dict)
    for r in idx: have[r["step"]][r["idx"]] = r.get("note", "")
    cum = collections.Counter(); blocking = []; rows = {}
    _done = userdone.user_done(A.id)   # 사용자가 화면에서 직접 누른 ✓ 완료 단계(DB) — 눈으로 하는 확인(화면 확대·책과 나란히 비교·카메라)의 유일한 근거(2026-10-11: rules.json 에 Claude 가 적어서 푸는 길 삭제)
    _last_built = max([i for i, st2 in enumerate(A.steps, 1) if st2.parts or st2.kw.get("moveMade") or st2.kw.get("madeNoPart")] or [0])   # 새 부품 없이 앞 번호 부품을 옮겨 합치는 번호(오토타깃 32번)도 '가장 마지막에 만든 번호'다(사용자 승인 2026-10-20)
    _evf = os.path.join(here, name + "_evidence.json"); _evid = json.load(open(_evf, encoding="utf-8")) if os.path.exists(_evf) else {}
    for k, st in enumerate(A.steps, 1):
        if not st.parts and not st.kw.get("moveMade") and not st.kw.get("madeNoPart"):   # 새 부품이 없어도 앞 번호 부품을 옮겨 합치는 번호(18번 등)는 작업 점검을 붙인다(사용자 지시 2026-10-17: "18번에 작업점검은 어디 갔어?")
            continue
        cnt = _counts(st.parts); cum.update(cnt)
        items = []   # (필수 여부, 통과, 문구)
        h = have.get(k, {})
        plate = any("프레임" in p.n for p in st.parts)
        _fd = os.path.join(here, "refs", name, "fits")   # 격자 점 파일(fits/NN_<라벨>.json)이 있어야 격자를 만든 것이다 — 점 없이 선만 그은 그림을 격자로 세지 않는다(관리자 지적 2026-10-09: 43번에 격자 점이 없는데 ☑ 로 찍혔다)
        _has_fit = (not os.path.isdir(_fd)) or any(f_.startswith("%02d_" % k) and f_.endswith(".json") for f_ in os.listdir(_fd))
        grid_ok = (1 in h and 2 in h) and _has_fit
        items.append((True, grid_ok, ("책 그림 격자(수평선·회전·격자 점) 만듦" if _has_fit else "책 그림 격자 점이 없음(이미지만 있음)") if 2 in h else "책 그림 원본 확인(판이 없는 번호)"))
        r = rd.get(str(k)) or {}
        items.append((True, all(str(r.get(f, "")).strip() for f in ("면", "링", "부품")), "읽기 표(면·링·부품) 적음"))
        rp = _parse(r.get("부품", "")) if r.get("부품") else None
        same = rp is not None and dict(rp) == dict(cnt)
        items.append((True, same, "읽기 표의 부품 = 모델의 부품 (%s)" % ", ".join("%s %d" % kv for kv in cnt.items())))
        _dr = str(r.get("방향", "")).strip()   # 카메라 방향 파악(관리자 지시 2026-10-09: 계산은 못 해도 책 그림의 어느 쪽이 가깝고·오른쪽·위인지는 맞춘다). 25번부터 비어 있으면 막는다
        items.append((k >= 25, len(_dr) >= 12 and not _dr.startswith("미"), "카메라 방향 파악(가까운 쪽·화면 오른쪽·위가 로봇의 어느 쪽인지 읽기 표 '방향')"))
        over = {n: (cum[n], lst[n]) for n in cnt if n in lst and cum[n] > lst[n]}
        items.append((True, not over, "쓴 부품 합계 ≤ 교재 LIST" + ("" if not over else " — 초과: " + ", ".join("%s %d/%d" % (n, a, b) for n, (a, b) in over.items()))))
        _ori = str(r.get("부품방향", "")).strip()   # 부품 방향·제자리 판정(관리자 지시 2026-10-09): 새 부품의 위·바깥 면, 칸1 끝, 줄 방향, 부품 사이 좌우 관계, 그룹이 들어오는 방향·앉는 자세를 책 격자에서 읽어 적는다
        _oex = k in rl.get("orient_exempt", [])   # 면제 번호는 새 순서로 다시 점검할 때까지 통과로 친다(rules 의 orient_exempt 에서 지우면 점검 대상)
        items.append((bool(rl.get("orient_check")) and not _oex, (len(_ori) >= 20 and not _ori.startswith("미")) or _oex or not rl.get("orient_check"), "부품 방향·제자리 판정(읽기 표 '부품방향')" + (" — 면제(재점검 대기)" if _oex and rl.get("orient_check") else "")))
        if any(p.n == "리벳" for p in st.parts):   # 리벳으로 프레임과 프레임을 이으면 딱 붙는다(기본 규칙, 사용자 2026-10-24): 틈 0.3 초과(떠 있음)·겹침 1.0 초과면 막는다
            _rg = rivet_gaps(A, k)
            items.append((k not in _done, not _rg, "리벳 결합 프레임이 딱 붙음(틈 0)" + ("" if not _rg else " — 틈 %s" % ", ".join("%s(%s↔%s) %.1fmm" % x for x in _rg[:3]))))
        if any(p.n in ("8볼트", "12볼트", "너트") for p in st.parts):   # 볼트·너트의 가장 큰 부분은 프레임 구멍 안에 묻혀 프레임 면 밖으로 안 나온다(기본 규칙, 사용자 2026-10-24)
            _fp = fastener_protrusion(A, k)
            items.append((k not in _done, not _fp, "볼트·너트 머리·몸이 프레임 면 밖으로 안 나옴" + ("" if not _fp else " — 나옴 %s" % ", ".join("%s(%s) %.1fmm" % x for x in _fp[:3]))))
        if rl.get("mainboard_check") and any(p.n == "메인보드" for p in st.parts):   # 메인보드 방향 검사(조립도별 켬: _rules.json "mainboard_check": true). 사용자 ✓ 번호는 막지 않는다
            _mb = mainboard_dir(A, k, str(r.get("부품방향", "")))
            items.append((k not in _done, not _mb, "메인보드 방향: 책 버튼 쪽 = 모델 버튼 쪽(+z)" + ("" if not _mb else " — " + "; ".join(_mb))))
        if any(p.n == "부시" for p in st.parts):   # 부시 방향 규칙(관리자 확정 2026-10-11): 넓은 쪽(모델 −y)이 바깥, 좁은 쪽(모델 +y)이 닿은 판 쪽. 사용자 ✓ 번호는 막지 않는다(내용을 못 바꾸므로)
            _bw = bush_wrong(A, k)
            items.append((k not in _done, not _bw, "부시 방향: 좁은 쪽(모델 +y)이 판 쪽" + ("" if not _bw else " — 넓은 쪽이 판에 닿은 부시 %s번째" % ", ".join(str(i + 1) for i in _bw))))
        _cmp = str(r.get("대조", "")).strip()   # 앞·뒤 번호 그림과 완성 사진(00)을 같이 보고 읽은 내용(관리자 지시 2026-10-08: 한 장만 보고 만들어 12번이 틀렸다). 10번부터는 비어 있으면 막는다(1~9번은 아직 안 한 것으로 표시만)
        items.append((k >= 10, len(_cmp) >= 10 and not _cmp.startswith("미"), "앞·뒤 번호 그림·완성 사진(00)과 같이 읽음(읽기 표 '대조')"))
        # 눈으로 하는 확인 4개 — 사용자가 ✓ 완료를 눌렀으면 통과, 아니면 가장 마지막에 만든 번호(화면을 봐야 확인되는 지금 번호)만 안 막고 앞 번호는 막는다.
        _ev = (_evid.get(str(k)) or {})
        _evok = bool(_ev)   # 화면↔책 비교 증거(record_check.py)가 있으면 표시(지문이 지금 내용과 같은지는 build.py 가 최종 내용으로 따로 검사한다)
        _ud = (k in _done) or _evok; _cur = (k == _last_built)
        _eye = [("화면 확대 확인", True), ("책 그림과 나란히 비교(칸 수 대조)", True), ("카메라 책과 대조", True), ("카메라가 짐작(guess)이 아님 — 책 그림에서 가까운 쪽·오른쪽·위를 읽고 정한 값(camSrc eye)", str(getattr(st, "camSrc", "guess")) != "guess")]
        for _txt, _okc in _eye:
            items.append((not _cur, _ud and _okc, _txt + (" (사용자 ✓ 완료)" if k in _done else (" (비교 증거 있음)" if _evok else ""))))
        rows[k] = items
        for need, ok, txt in items:
            if need and not ok: blocking.append("%d번: %s" % (k, txt))
        block = MARK + "\n" + "\n".join(("☑ " if ok else ("☐ " if not need else "☐ ")) + txt + ("" if need else " (눈으로)") for need, ok, txt in items)
        st.note = st.note.split(MARK)[0] + block
    # 완성 번호(마지막 단계)에는 final_audit.py 가 만든 "완성 마무리 점검"을 작업 점검 블록처럼 뒤에 붙인다(관리자만 보임, 2026-10-16)
    _fa = os.path.join(here, "refs", name, "final_audit.md")
    if os.path.exists(_fa) and A.steps:
        _ls = A.steps[-1]; _ls.note = _ls.note.split(MARK)[0].split("\n━ 완성 마무리 점검")[0] + "\n" + MARK + " 전체\n" + open(_fa, encoding="utf-8").read()
    left = {n: lst[n] - cum[n] for n in lst if lst[n] - cum[n] != 0 and n in cum or (n in lst and cum[n] == 0 and False)}
    json.dump({"blocking": blocking, "cum": dict(cum), "list_left": {n: lst[n] - cum.get(n, 0) for n in lst}}, open(os.path.join(here, name + "_checks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return blocking
