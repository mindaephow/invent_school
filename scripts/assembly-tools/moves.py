# 동작 묶음 — 조립도마다 손으로 되풀이하던 결합 장면을 함수 하나로 (2026-11-18, 조립도 23개 결합 752줄을 세어 많이 나온 장면부터)
#   조립 스크립트에서:  import moves as mv
#   - 리벳으로 판 잇기(결합 장면 2위, 약 150회):  rv, top = mv.rivet_join(s, 아래판, [(3,3),(5,2)], "25프레임", R_위판, [(1,2),(3,1)])
#   - 리벳만 꽂기:                                 rv = mv.rivets(s, 판, [(3,3),(5,2)])
#   - 꽂힌 리벳 위에 판 얹기:                       top = mv.plate_on_rivets(s, "25프레임", R, rv, [(1,2),(3,1)])
#   - 블록·모터처럼 돌기를 판 구멍에 꽂기(1위, 약 215회): b = mv.pegs_into(s, "2단블록", R, 판, [(7,1),(7,2)], peg_face="+z", hole_face="-y")
#   - DC모터를 판에 꽂기(7위):                       m = mv.pegs_into(s, "DC모터", orient("DC모터", {"홀면 +y": "-Z", "돌기면 +x": "아래"}), 판, [(2,2),(2,4)], pegs=["p4","p3"])
#   - 여러 부품 돌기 위에 판 얹기(판 ← 블록·모터):   top = mv.plate_on(s, "59프레임", R, [(모터, "돌기면 -x 열1·줄2", (2,2)), …])
#   - 축·T축 끝에 부시·기어·바퀴 끼우기(3위, 약 87회): bu = mv.on_shaft(s, "부시", 축, "+z", against=판)   ← 부시 자세는 자동(G5)
#   자세 R 은 그대로 주거나 asmlib.orient("3단블록", {"돌기면 +z": "아래", "홀면 +y": "+Z"}) 로 만든다(새로 계산하지 않는다).
# 하는 일은 asmlib 의 attach/recv 를 규칙대로 부르는 것뿐이다 — 위치는 여전히 결합(돌기 ↔ 구멍)에서 계산되고 손 좌표는 없다(③ 늘 지킬 것 1).
# 규칙: 리벳은 결합 전(띄운) 모양·hover 를 적지 않음·joinOrder 1, 리벳을 받는 판은 hover = 기본 띄움 + 리벳 길이 + 최소 간격·joinOrder 2 (⑤ 리벳·공통 E G12).
# 결과가 손으로 쓴 줄과 같은지는 test_moves.py 가 이미 만든 조립도(kidknight 2번·formula1 1번)로 확인한다.
import numpy as np
import partlib, hovercheck

def plate_hover():
    """리벳을 받는 판의 띄움(G12): 화면 기본 띄움 + 리벳 길이(부품 목록) + 최소 간격 — 손 숫자 없음."""
    return hovercheck.HOVER + float(partlib.get("리벳")["size"][1]) + hovercheck.MIN_GAP

def _hole(h, face):
    """(열, 줄) → '홀면 ±y 열c·줄r', 글자(id·면 이름)는 그대로."""
    return ("홀면 %s 열%d·줄%d" % (face, h[0], h[1])) if isinstance(h, (tuple, list)) else h

def rivets(s, host, holes, face="+y", R=None, **extra):
    """host 의 구멍들에 리벳을 꽂는다. holes = [(열, 줄), …] 또는 구멍 id 목록. face = 리벳이 들어가는 host 의 홀면(위에서 꽂으면 +y).
    리벳 아래 돌기('돌기면 -y 1')가 host 구멍에 들어가고, 결합 전(띄운) 모양·joinOrder 1 이 된다."""
    R = np.eye(3) if R is None else R
    out = []
    for h in holes:
        r = s.attach("리벳", R, {"돌기면 -y 1": (host, _hole(h, face))}, rivet=True, **extra)
        r.extra["joinOrder"] = 1
        out.append(r)
    return out

def plate_on_rivets(s, name, R, rv, holes, face="-y", **extra):
    """꽂힌 리벳들의 다른 끝 돌기('돌기면 +y 1')에 판 name 을 얹는다. holes 는 rv 와 같은 순서의 판 구멍(첫 쌍으로 위치를 정하고 나머지는 검사).
    face = 리벳 돌기를 받는 판의 홀면(아래에서 올라오면 -y). joinOrder 2·hover = plate_hover() 가 기본(다른 값을 주면 그 값)."""
    if len(rv) != len(holes): raise ValueError("리벳 %d개 ↔ 판 구멍 %d개 — 개수가 같아야 한다" % (len(rv), len(holes)))
    links = {_hole(h, face): (r, "돌기면 +y 1") for r, h in zip(rv, holes)}
    extra.setdefault("joinOrder", 2); extra.setdefault("hover", plate_hover())
    return s.recv(name, R, links, **extra)

def rivet_join(s, lower, lower_holes, upper_name, R_upper, upper_holes, lower_face="+y", upper_face="-y", R_rivet=None, **upper_extra):
    """리벳으로 판 잇기 한 장면: lower 의 구멍들에 리벳을 꽂고 그 위에 upper_name 판을 얹는다. 돌려주는 값 = (리벳 목록, 위판)."""
    rv = rivets(s, lower, lower_holes, lower_face, R_rivet)
    return rv, plate_on_rivets(s, upper_name, R_upper, rv, upper_holes, upper_face, **upper_extra)

def _v(d):
    """'+z'·'-X'·[0,0,1] → 단위 벡터."""
    if isinstance(d, str):
        v = np.zeros(3); v["xyz".index(d[-1].lower())] = -1.0 if d.startswith("-") else 1.0; return v
    v = np.array(d, float); return v / np.linalg.norm(v)

def bush_R(end):
    """부시 자세(G5): 좁은 쪽(모델 +y)이 축에 먼저 들어가 판을 향한다 = 끼우는 쪽 끝(end)의 반대. 모델 x 는 +X(축이 X 면 +Z)."""
    y = -_v(end); x = np.array([1.0, 0, 0]) if abs(y[0]) < 0.9 else np.array([0, 0, 1.0])
    x = x - np.dot(x, y) * y; x /= np.linalg.norm(x)
    return np.column_stack([x, y, np.cross(x, y)])

def on_shaft(s, name, shaft, end, R=None, against=None, hole="h1", peg="p1", **extra):
    """축·T축(shaft)의 한쪽 끝(end = 끼우는 쪽, '+z' 또는 벡터)에 부시·기어·바퀴 name 을 끼운다(규칙집 C6 ③).
    against = 닿을 때까지 밀어 넣는 부품(판·블록·바퀴). R 을 안 주면 부시는 bush_R(end)(G5), 다른 부품은 R 을 꼭 준다(orient 로)."""
    if R is None:
        if name != "부시": raise ValueError("%s 는 자세 R 을 준다 — orient(\"%s\", {면: 방향}) 로 만든다" % (name, name))
        R = bush_R(end)
    if against is not None: extra["against"] = against
    return s.recv(name, R, {hole: (shaft, peg)}, dir=[float(x) for x in _v(end)], **extra)

def slide_end(pt, d, goal, end="+"):
    """축·T축 pt 를 길이 방향 d(단위 벡터·'+z' 같은 이름)으로만 옮겨, d 쪽 끝(end="+")이나 반대 끝(end="-")의 d 좌표가 goal 이 되게 한다(G21: 끼워지는 부품이 정한 자리에 끝을 맞춤).
    pt.p 의 d 에 수직인 성분은 그대로라 기어·판·블록 구멍을 지나는 줄은 변하지 않는다. 손 좌표 없이 goal(부시 바깥 면 같은 계산값)만 받는다. 돌려주는 값 = 옮긴 거리(mm)."""
    d = _v(d); half = _len_along(pt, d) / 2.0; cur = float(np.dot(pt.p, d)) + (half if end == "+" else -half)
    mvd = float(goal) - cur; pt.p = np.asarray(pt.p, float) + d * mvd; return mvd

def plate_on(s, name, R, links, face="-y", **extra):
    """판 name 을 여러 부품의 돌기 위에 얹는다(판 ← 블록·모터·메인보드 돌기, 결합 장면 4·5·10위).
    links = [(돌기 가진 부품, 돌기 id, 판 구멍 (열, 줄) 또는 id), …] — 첫 쌍으로 위치를 정하고 나머지는 검사."""
    return s.recv(name, R, {_hole(h, face): (host, peg) for host, peg, h in links}, **extra)

# ── 결합 전 띄움 거리 자동 계산(2026-11-18, 사용자 "최소만 넘치면 돼 — 너무 가까우면 부품들끼리 가려서 조립할 곳이 안 보인다") ──
#   조립 스크립트 끝(stepchecks.apply 앞)에 `mv.auto_hover(A)` 한 줄. hover 를 직접 주지 않은 부품마다:
#   ① 최소 = 띄우는 방향(dir)으로 그 부품이 차지하는 길이 + gap(20mm, 규칙 G1c "자기 높이 + 20 이상")
#   ② 순서 = 같은 번호에서 먼저 끼우는(joinOrder 작은) 부품이 아래에 있으면 그 부품의 띄움 + 그 길이 + 최소 간격 바깥(G12 리벳 위 판 식을 넓힌 것)
#   ③ 길 = 띄운 자리(제자리 + dir × 거리, 화면과 같은 식)에서 앞 번호 부품과 겹치지 않을 때까지만 늘림(check_local 처럼 거리의 1·0.66·0.33 세 곳, 여유 2.5mm, 상자 근사)
#   리벳은 G12 대로 적지 않는다(화면 기본 띄움). 결과를 돌려주고 부품 extra["hover"] 에 넣는다. 최종 확인은 build 의 띄우는 길 검사.
def _size(pt): return np.array(partlib.get(pt.n).get("size") or [0, 0, 0], float)
def _pose(pt):   # 그 부품이 처음 놓인(만든 번호 화면의) 자세 — move_made 로 옮겨진 부품은 _base 에 원래 자리가 있다
    b = getattr(pt, "_base", None); return (np.asarray(b[0], float), np.asarray(b[1], float)) if b is not None else (np.asarray(pt.p, float), np.asarray(pt.R, float))
def _len_along(pt, d): return float(np.sum(np.abs(_pose(pt)[1].T @ d) * _size(pt)))
def _box(pt, at=None):
    p0, R0 = _pose(pt); c = p0 if at is None else np.asarray(at, float); h = np.abs(R0) @ (_size(pt) / 2); return c - h, c + h
def _hit(a, b, m=2.5): return bool(np.all(a[0] < b[1] - m) and np.all(b[0] < a[1] - m))
def _foot(a, b, d):   # 띄우는 방향에 수직인 면에서 두 상자가 겹치는가(아래에 있는가)
    k = int(np.argmax(np.abs(d))); idx = [i for i in range(3) if i != k]
    return all(a[0][i] < b[1][i] and b[0][i] < a[1][i] for i in idx)

def auto_hover(A, gap=20.0, skip=("리벳",), maxadd=200.0):
    out = []; mine = set()   # mine: 이 함수가 띄움을 정한 부품만 바닥 조정(④) 대상
    byk0 = {"%d:%d" % (s2.index, i): q for s2 in A.steps for i, q in enumerate(s2.parts)}
    for st in A.steps:
        hide = {str(k) for k in (st.kw.get("hideMade") or {})}; slot = st.kw.get("slot")   # 그 번호 화면에 보이는 앞 부품만 장애물 — 같은 창고, 숨기지 않은 번호
        prior = [q for s2 in A.steps if s2.index < st.index and str(s2.index) not in hide and s2.kw.get("slot") == slot
                 for q in s2.parts if not (q.extra.get("side") or {}) and "%d:%d" % (s2.index, s2.parts.index(q)) not in hide]
        cand = [q for q in st.parts if q.extra.get("dir") is not None and q.extra.get("hover") is None and not q.extra.get("seated")
                and not q.extra.get("noGuide") and q.n not in skip and not q.extra.get("side")]
        for q in sorted(cand, key=lambda q: q.extra.get("joinOrder", 1)):
            if getattr(q, "_how", "") in ("place", "Part"):   # 바탕(새 창고 첫 부품 — place·직접 생성, 규칙 A4)은 띄우지 않는다: G19 의 0.01(띄우지 않음)
                q.extra["hover"] = 0.01; out.append((st.index, q.n, 0.01, "바탕(A4) — 띄우지 않음(G19 0.01)")); continue
            d = _v(q.extra["dir"]); h = _len_along(q, d) + gap; why = "자기 길이 %.0f + %.0f" % (_len_along(q, d), gap)
            qb = _box(q)
            for L in st.parts:   # ② 먼저 끼우는 부품이 같은 길 아래에 있으면 그보다 바깥
                if L is q or L.extra.get("joinOrder", 1) >= q.extra.get("joinOrder", 1) or L.extra.get("dir") is None or (L.extra.get("seated") and not L.extra.get("moveGuide")): continue   # seated(책이 이미 끼운 모양, 안 움직이는 축 등 — moveGuide 로 같이 떠오르는 seated 블록은 제외)는 먼저 끼우는 부품이 아니다 — 그 뒤 부시를 바깥으로 밀지 않는다(catapult 11번 부시 둘 hover 25.5/97)
                if float(np.dot(_v(L.extra["dir"]), d)) < 0.99 or not _foot(_box(L), qb, d): continue
                hl = L.extra.get("hover") or (hovercheck.HOVER_RECV if L.extra.get("recv") else hovercheck.HOVER)
                need = float(hl) + _len_along(L, d) + hovercheck.MIN_GAP
                if need > h: h, why = need, "먼저 끼우는 %s(%.0f) 바깥" % (L.n, float(hl))
            # 끼워질 축: 제자리 상자가 이미 앞 부품 P 와 겹치면 q 가 P 에 꿰이는 것 — 충돌 검사에서 빼고, q 앞면이 P 의 바깥 끝(d 방향)을 넘도록만 띄운다
            thr = [P for P in prior + [L for L in st.parts if L is not q and L.extra.get("seated") and L.extra.get("dir") is not None] if _hit(qb, _box(P))]   # 같은 번호에서 책이 이미 끼운(seated) 축도 끼워질 축이다 — 부시는 그 축 끝 바깥으로 띄운다(catapult 4번 바깥 부시, 31번 바퀴와 같다)
            for P in thr:
                pb = _box(P); far = float(np.sum(np.where(d > 0, pb[1], pb[0]) * d))
                need = far - float(np.dot(_pose(q)[0], d)) + _len_along(q, d) / 2 + gap
                if need > h: h, why = need, "끼워질 %s 끝을 넘김" % P.n
            for mk, m in (st.kw.get("moveMade") or {}).items():   # 같은 번호에서 합쳐 들어오는 묶음(move_made)은 띄운 채 시작한다 — 제자리 상자가 q 와 겹치면(q 가 그 묶음에 꿰이는 것) q 는 묶음이 뜬 자리의 바깥 끝을 넘도록 띄운다(catapult 30번 T축이 큰기어 안에 이미 든 모양으로 시작하던 것)
                if mk not in byk0 or float(np.dot(_v(m.get("dir") or [0, 1, 0]), d)) < 0.99: continue
                from asmlib import euler_to_R
                pt_ = byk0[mk]; ch_ = np.abs(euler_to_R(m["r"])) @ (_size(pt_) / 2); cc_ = np.asarray(m["p"], float)
                if not _hit(qb, (cc_ - ch_, cc_ + ch_)): continue
                far = float(np.sum(np.where(d > 0, cc_ + ch_, cc_ - ch_) * d)) + float(m.get("hover") or 0)
                need = far - float(np.dot(_pose(q)[0], d)) + _len_along(q, d) / 2 + gap
                if need > h: h, why = need, "합쳐 들어오는 %s 가 뜬 자리의 바깥 끝을 넘김" % pt_.n
            h0 = h   # ③ 띄운 자리가 앞 번호 부품과 겹치면 겹치지 않을 때까지(1mm 씩)
            while h < h0 + maxadd and any(_hit(_box(q, _pose(q)[0] + d * h * t), _box(P)) for t in (1.0, 0.66, 0.33) for P in prior if P not in thr):
                h += 1.0
            if h >= h0 + maxadd: h, why = h0, why + " · ⚠ 길이 끝까지 막힘 — 거리가 아니라 띄우는 방향(dir)·결합 순서를 의심(그대로 최소 거리)"
            elif h > h0: why += " · 길 비키기 +%.0f" % (h - h0)
            q.extra["hover"] = round(h, 1); out.append((st.index, q.n, round(h, 1), why)); mine.add(id(q))
    # 복사본(copy_to_slot — extra["copyOf"]="번호:순서")은 원본과 같은 띄움(두 벌은 같은 모양으로 보여야 한다)
    byk0 = {"%d:%d" % (s2.index, i): q for s2 in A.steps for i, q in enumerate(s2.parts)}
    for s2 in A.steps:
        for q in s2.parts:
            o = byk0.get(str(q.extra.get("copyOf") or ""))
            if o is not None and q.extra.get("dir") is not None and o.extra.get("hover") is not None and q.extra.get("hover") != o.extra["hover"]:
                q.extra["hover"] = o.extra["hover"]; out.append((s2.index, q.n, o.extra["hover"], "복사본 — 원본(%s)과 같게" % q.extra["copyOf"]))
    # ④ 바닥(G24 — 띄운 자리도 바닥 위): 띄운 자리가 바닥 아래로 가면 띄움은 그대로 두고 그 번호 화면 전체를 올린다(asmlib.floor_lift — 바닥 검사와 같은 계산, xform 포함).
    #   띄움을 줄이면 끼우기 전 부품이 이미 꽂힌 것처럼 보인다(사용자 2026-11-20 dog 1~9번 — 번호마다 floor_lift 를 손으로 앞에 두던 것을 도구가 한다)
    import asmlib
    byk = {"%d:%d" % (st.index, i): q for st in A.steps for i, q in enumerate(st.parts)}
    for k in sorted({int(r[0]) for r in asmlib.floor_check(A, keys=True) if "새로" in str(r[3]) and str(r[-1]) in byk and id(byk[str(r[-1])]) in mine}):
        old = float(((A.meta.get("lift") or {}).get(str(k))) or 0); amt = max(old, asmlib.floor_lift(A, k))
        A.meta["lift"] = {**(A.meta.get("lift") or {}), str(k): amt}
        if amt > old: out.append((k, "(화면 전체)", amt, "띄운 자리가 바닥 아래 — 띄움은 그대로, %d번 화면 전체를 %.0f→%.0f 올림(G24)" % (k, old, amt)))
    return out

def pegs_into(s, name, R, host, holes, peg_face="+z", hole_face="-y", pegs=None, **extra):
    """블록·모터·메인보드처럼 돌기가 있는 부품 name 을 host 판 구멍에 꽂는다.
    holes = 돌기 1, 2, … 차례로 들어갈 host 구멍 [(열, 줄), …] 또는 id. 돌기 이름은 '돌기면 {peg_face} 1', '… 2' … (다르면 pegs=[…] 로 준다)."""
    pegs = pegs or ["돌기면 %s %d" % (peg_face, i + 1) for i in range(len(holes))]
    if len(pegs) != len(holes): raise ValueError("돌기 %d개 ↔ 구멍 %d개 — 개수가 같아야 한다" % (len(pegs), len(holes)))
    return s.attach(name, R, {p: (host, _hole(h, hole_face)) for p, h in zip(pegs, holes)}, **extra)


# ── 세트 통째 원점 이동 (A4, 2026-11-25) ─────────────────────────────────────────────────────────────
def recenter_set(A, steps, slot=1, follow=()):
    """한 창고(slot)의 세트(steps 번호들)가 원점에서 벗어나 만들어졌으면 세트 전체를 같은 만큼 옮긴다 — 숫자는 적지 않고 빌드 때 계산한다(A4).
    이동량 = −(번호별 '완성 모습 x·z 중심'의 최소와 최대의 가운데). 중심은 violations 의 center 점검과 같은 식(부품 크기·자세 상자, hideMade·hideAt·같은 창고만)이다.
    옮기는 것: 그 번호들의 부품 p·_base, 부품 extra 의 move·moves·side·poseAt 의 p, marks·faceMarks·holeMarks·settleMarks, 그 번호 kw["moveMade"] 의 p·marks.
    follow=[번호..] 는 d 계산에는 안 넣고 같은 d 만 적용한다(몸에 합쳐 들어오는 번호, 예: 투석기 21).
    조립 스크립트 끝(auto_hover 뒤, stepchecks.apply 앞)에서 한 번 부른다. 이미 가운데면(이동량 0) 아무것도 안 바꾼다."""
    from asmlib import euler_to_R
    steps = [int(k) for k in steps]; st = A.steps
    cs = []
    for k in steps:
        hide = {int(x) for x in (st[k - 1].kw.get("hideMade") or {}) if str(x).isdigit()}
        lo = np.array([1e9, 1e9]); hi = np.array([-1e9, -1e9])
        for j in range(1, k + 1):
            if j in hide or st[j - 1].kw.get("slot", 1) != st[k - 1].kw.get("slot", 1): continue
            for pt in st[j - 1].parts:
                ex = pt.extra or {}; ha = ex.get("hideAt")
                if ha and (k in [int(x) for x in ha] if isinstance(ha, (list, tuple, set)) else int(ha) <= k): continue
                sz = (pt.conn or {}).get("size")
                if not sz: continue
                pose = pt._base if getattr(pt, "_base", None) else (pt.p, pt.R)
                mv = [m for m in (ex.get("moves") or ([ex["move"]] if "move" in ex else [])) if int(m["at"]) <= k]
                if mv: m = max(mv, key=lambda q: int(q["at"])); pose = (m["p"], euler_to_R(m["r"]))
                sd = ex.get("side")
                if sd and k < int(sd.get("until") or 0): pose = (sd["p"], euler_to_R(sd["r"]))
                c = np.array(pose[0], float); h = np.abs(np.array(pose[1], float)) @ (np.array(sz, float) / 2)
                lo = np.minimum(lo, [c[0] - h[0], c[2] - h[2]]); hi = np.maximum(hi, [c[0] + h[0], c[2] + h[2]])
        if hi[0] >= lo[0]: cs.append((lo + hi) / 2)
    if not cs: return np.zeros(3)
    cs = np.array(cs); mid = (cs.min(axis=0) + cs.max(axis=0)) / 2
    d = np.array([-mid[0], 0.0, -mid[1]])
    if float(np.abs(d).max()) < 1e-6: return d
    r3 = lambda v: [round(float(x), 3) for x in v]
    mvpt = lambda q: np.array(q, float) + d
    for k in list(steps) + [int(x) for x in follow if int(x) not in steps]:
        S = st[k - 1]
        for pt in S.parts:
            pt.p = pt.p + d
            if getattr(pt, "_base", None) is not None: pt._base = (pt._base[0] + d, pt._base[1])
            ex = pt.extra
            for key in ("move", "side"):
                if isinstance(ex.get(key), dict) and "p" in ex[key]: ex[key]["p"] = r3(mvpt(ex[key]["p"]))
            for m in (ex.get("moves") or []):
                if "p" in m: m["p"] = r3(mvpt(m["p"]))
            for pa in (ex.get("poseAt") or {}).values():
                if "p" in pa: pa["p"] = r3(mvpt(pa["p"]))
            for key in ("marks", "faceMarks", "holeMarks", "settleMarks"):
                if isinstance(ex.get(key), list) and ex[key] and not isinstance(ex[key], str):
                    ex[key] = [r3(mvpt(m)) if hasattr(m, "__len__") and len(m) == 3 and not isinstance(m, dict) else m for m in ex[key]]
        for b_ in (S.kw.get("bands") or []):   # 고무밴드 점도 같이 옮긴다(follow·steps 번호에 bands 가 있을 때)
            if isinstance(b_.get("pts"), list): b_["pts"] = [r3(mvpt(q)) for q in b_["pts"]]
        for e in (S.kw.get("moveMade") or {}).values():
            if "p" in e: e["p"] = r3(mvpt(e["p"]))
            if isinstance(e.get("marks"), list): e["marks"] = [r3(mvpt(m)) if hasattr(m, "__len__") and len(m) == 3 else m for m in e["marks"]]
    return d


def center_between(part, host_a, host_b, axis=2):
    """긴 부품(축)을 두 받는 부품(판 둘) 가운데에 맞춘다 — attach 가 축 한쪽 끝만 구멍에 대 한쪽으로 나오게 놓으므로, 축 가운데의 axis 좌표(0=x 1=y 2=z)를 두 부품 가운데로 옮긴다(계산, 손값 아님)."""
    p = np.array(part.p, float); p[axis] = 0.5 * (float(host_a.p[axis]) + float(host_b.p[axis])); part.p = p
    return part
