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
                if L is q or L.extra.get("joinOrder", 1) >= q.extra.get("joinOrder", 1) or L.extra.get("dir") is None: continue
                if abs(float(np.dot(_v(L.extra["dir"]), d))) < 0.99 or not _foot(_box(L), qb, d): continue
                hl = L.extra.get("hover") or (hovercheck.HOVER_RECV if L.extra.get("recv") else hovercheck.HOVER)
                need = float(hl) + _len_along(L, d) + hovercheck.MIN_GAP
                if need > h: h, why = need, "먼저 끼우는 %s(%.0f) 바깥" % (L.n, float(hl))
            h0 = h   # ③ 띄운 자리가 앞 번호 부품과 겹치면 겹치지 않을 때까지(1mm 씩)
            while h < h0 + maxadd and any(_hit(_box(q, _pose(q)[0] + d * h * t), _box(P)) for t in (1.0, 0.66, 0.33) for P in prior):
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
    # ④ 바닥(G24 — 띄운 자리도 바닥 위)이 G1c 보다 먼저: asmlib.floor_check(바닥 검사와 같은 계산, xform 포함)가 "새로 놓일 때" 바닥 아래로 잡은 부품은 바닥에 닿기 전까지만 띄운다
    import asmlib
    byk = {"%d:%d" % (st.index, i): q for st in A.steps for i, q in enumerate(st.parts)}
    for _ in range(3):
        bad = [r for r in asmlib.floor_check(A, keys=True) if "새로" in str(r[3]) and str(r[-1]) in byk and id(byk[str(r[-1])]) in mine]
        if not bad: break
        for r in bad:
            q = byk[str(r[-1])]; d = _v(q.extra["dir"]); hv = float(q.extra.get("hover") or 0)
            dy = abs(float(d[1])) or 1.0; nh = max(0.01, round(hv - (-float(r[2]) + 0.5) / dy, 1))
            if nh < hv:
                q.extra["hover"] = nh
                out = [(a, b, (nh if (a, b) == (q.step.index, q.n) and c == hv else c), (w + " · 바닥 때문에 %.0f→%.0f(최소 못 지킴)" % (hv, nh) if (a, b) == (q.step.index, q.n) and c == hv else w)) for a, b, c, w in out]
    return out

def pegs_into(s, name, R, host, holes, peg_face="+z", hole_face="-y", pegs=None, **extra):
    """블록·모터·메인보드처럼 돌기가 있는 부품 name 을 host 판 구멍에 꽂는다.
    holes = 돌기 1, 2, … 차례로 들어갈 host 구멍 [(열, 줄), …] 또는 id. 돌기 이름은 '돌기면 {peg_face} 1', '… 2' … (다르면 pegs=[…] 로 준다)."""
    pegs = pegs or ["돌기면 %s %d" % (peg_face, i + 1) for i in range(len(holes))]
    if len(pegs) != len(holes): raise ValueError("돌기 %d개 ↔ 구멍 %d개 — 개수가 같아야 한다" % (len(pegs), len(holes)))
    return s.attach(name, R, {p: (host, _hole(h, hole_face)) for p, h in zip(pegs, holes)}, **extra)
