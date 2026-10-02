# 큐보 조립 프로그램 — 설명서 번호를 코드로 옮기면 위치·회전·안내점(dir/marks)이 계산되어 design-assemblies.js 항목으로 나온다.
#
#   A = Asm("cubo-1-xxx", "차시이름", "교재 쪽")
#   s = A.step("노트")                               # 설명서 그림 한 장 = 단계 하나
#   w = s.place("315프레임", R=ori("+x", "+z"), p=(−70, 25, 47.5))     # 이미 자리가 정해진 부품(바닥판 등)
#   m = s.attach("DC모터", R, {"p1": (w, (−60, 25, 47.5)), "p2": (w, (−20, 25, 47.5))})  # 내 돌기 → 받는 구멍(점 가까운 구멍)
#   f = s.recv("35프레임", R, {"h1_1": (blk, "p2")}, ...)            # 내 구멍 ← 고정된 돌기
#   A.js()                                          # design-assemblies.js 에 붙일 항목
#
# 규칙(안내서): 돌기가 들어가는 면이 marks(구멍 입구 가운데), dir = 끼우기 전에 떠 있는 쪽(들어가는 방향의 반대),
#   recv(구멍을 받는 쪽이 움직임)는 marks = 고정된 돌기 끝, dir = 돌기 방향.
import json, math
import numpy as np
import partlib

D = math.pi / 180
TOL = 0.8   # 돌기·구멍 어긋남 허용(mm) — 2단블록 돌기 간격이 10.1 이라 0.7 정도는 모델 오차
AX = {"x": 0, "y": 1, "z": 2}

def vec(s):
    if isinstance(s, str):
        v = np.zeros(3); v[AX[s[1]]] = 1 if s[0] == "+" else -1; return v
    v = np.array(s, float); return v / np.linalg.norm(v)

def ori(x, y):
    """모델 x축·y축이 세계의 어느 방향인지 주면(예: ori('+x','+z')) z축은 외적으로 정해진다."""
    ex, ey = vec(x), vec(y); ez = np.cross(ex, ey)
    return np.column_stack([ex, ey, ez])

def ori_z(x, z):
    ex, ez = vec(x), vec(z); ey = np.cross(ez, ex)
    return np.column_stack([ex, ey, ez])

def euler_to_R(r):
    rx, ry, rz = [a * D for a in r]
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx], [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx], [-sy, cy * sx, cy * cx]])

def R_to_euler(R):
    sy = max(-1.0, min(1.0, -R[2, 0])); ry = math.asin(sy)
    if abs(sy) < 0.99999:
        rx = math.atan2(R[2, 1], R[2, 2]); rz = math.atan2(R[1, 0], R[0, 0])
    else:
        rx = math.atan2(-R[1, 2], R[1, 1]); rz = 0.0
    return [round(v / D, 4) + 0.0 for v in (rx, ry, rz)]

def Rx(deg): a = deg * D; c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(deg): a = deg * D; c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(deg): a = deg * D; c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def rnd(v): return [round(float(x), 3) + 0.0 for x in v]

class Part:
    def __init__(s, n, R, p, step, extra=None):
        s.n, s.R, s.p, s.step, s.extra = n, np.array(R, float), np.array(p, float), step, (extra or {})
        s.conn = partlib.get(n); s.side = None
    def world(s, kind, c):
        return {"id": c["id"], "pos": s.p + s.R @ np.array(c["pos"], float), "dir": s.R @ np.array(c["dir"], float), "len": c.get("len", 0), "r": c.get("r", 0), "through": c.get("through", False)}
    def peg(s, id):
        for c in s.conn["pegs"]:
            if c["id"] == id: return s.world("peg", c)
        raise KeyError((s.n, id))
    def hole(s, id):
        for c in s.conn["holes"]:
            if c["id"] == id: return s.world("hole", c)
        raise KeyError((s.n, id))
    def hole_near(s, pt, axis=None):
        """점 pt 에 가장 가까운 구멍(axis 를 주면 그 방향과 나란한 구멍만)."""
        best, bd = None, 1e9
        for c in s.conn["holes"]:
            h = s.world("hole", c)
            if axis is not None and abs(abs(float(np.dot(h["dir"], axis))) - 1) > 1e-3: continue
            d = float(np.linalg.norm(h["pos"] - np.array(pt, float)))
            if d < bd: best, bd = h, d
        return best, bd
    def peg_near(s, pt):
        best, bd = None, 1e9
        for c in s.conn["pegs"]:
            g = s.world("peg", c); d = float(np.linalg.norm(g["pos"] - np.array(pt, float)))
            if d < bd: best, bd = g, d
        return best, bd

class Asm:
    def __init__(s, id, chapter, book, camera=None, **meta):
        s.id, s.chapter, s.book, s.camera, s.meta = id, chapter, book, camera, meta
        s.steps = []; s.parts = []; s.warn = []
    def step(s, note, cam=None, camSrc="guess", **kw):
        st = Step(s, note, cam, camSrc, kw); s.steps.append(st); return st
    def log(s, msg): s.warn.append(msg); print("  [경고]", msg)

class Step:
    def __init__(s, A, note, cam, camSrc, kw):
        s.A, s.note, s.cam, s.camSrc, s.kw, s.parts = A, note, cam, camSrc, kw, []
        s.index = len(A.steps) + 1
    def _add(s, part):
        s.parts.append(part); s.A.parts.append(part); return part
    def place(s, n, R, p, **extra):
        """위치가 정해진 부품(구멍에 끼우는 안내가 필요 없는 부품: 바닥판 등)."""
        return s._add(Part(n, R, p, s, extra))
    # 내 돌기 → 받는 구멍
    def attach(s, n, R, links, dir=None, hover=None, rivet=False, **extra):
        """links: {내 돌기 id: (받는 부품, 목표점 또는 구멍 id)}. 첫 연결로 위치를 정하고 나머지는 어긋남을 검사한다.
        rivet=True 면 리벳 몸통 가운데가 구멍 입구 면에 온다(양 끝이 두 부품에 반반 들어감)."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        items = list(links.items()); p = None; marks = []; d0 = None
        def target(host, tgt, mypeg):
            return host.hole(tgt) if isinstance(tgt, str) else host.hole_near(tgt, axis=mypeg["dir"])[0]
        for pid, (host, tgt) in items:
            mypeg = tmp.peg(pid); h = target(host, tgt, mypeg)
            if h is None: s.A.log(f"{s.index}단계 {n}.{pid}: 받는 구멍이 없음({host.n} {tgt})"); continue
            d = mypeg["dir"]; surf = h["pos"] - d * (h["len"] / 2)   # 돌기가 들어가는 면(구멍 입구) 가운데
            if p is None:
                p = surf if rivet else (surf + d * mypeg["len"] / 2) - mypeg["pos"]   # tmp 는 p=0 이라 mypeg["pos"] 가 곧 R·(로컬 위치)
                d0 = d
            marks.append(rnd(surf))
        part = Part(n, R, p if p is not None else (0, 0, 0), s, extra)
        for pid, (host, tgt) in items[1:]:
            pg = part.peg(pid); h = target(host, tgt, pg)
            if h is None: continue
            diff = pg["pos"] - h["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, pg["dir"]) * pg["dir"]))
            if err > TOL: s.A.log(f"{s.index}단계 {n}.{pid}: {host.n} 구멍과 {err:.1f}mm 어긋남")
        part.extra.update({"dir": rnd(-d0 if dir is None else vec(dir)), "marks": marks})
        if hover: part.extra["hover"] = hover
        return s._add(part)
    def recv(s, n, R, links, dir=None, hover=None, p=None, **extra):
        """움직이는 쪽이 구멍을 받는 쪽(프레임이 블록 끝 돌기에 얹히는 경우).
        links 가 dict {내 구멍 id: (고정 부품, 돌기 id)} 면 위치 p 를 계산하고, [(고정 부품, 돌기 id), ...] 목록이면 p 를 직접 줘야 한다."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        pairs = list(links.items()) if isinstance(links, dict) else [(None, x) for x in links]
        marks = []; d0 = None; calc = p is None
        for pid, (host, gid) in pairs:
            g = host.peg(gid); d = g["dir"]; tip = g["pos"] + d * g["len"] / 2
            if calc:
                myh = tmp.hole(pid); base = g["pos"] - d * g["len"] / 2
                hole_center = base + d * myh["len"] / 2 if g["len"] >= myh["len"] else g["pos"] + d * (myh["len"] - g["len"]) / 2
                if p is None: p = hole_center - myh["pos"]   # myh 는 이미 세계 방향으로 돌린 값(tmp 의 p=0)
            if d0 is None: d0 = d
            marks.append(rnd(tip))
        part = Part(n, R, p, s, extra)
        if calc:
            for pid, (host, gid) in pairs[1:]:
                g = host.peg(gid); h = part.hole(pid); diff = h["pos"] - g["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"]))
                if err > TOL: s.A.log(f"{s.index}단계 {n}.{pid}: 돌기 {host.n}.{gid} 와 {err:.1f}mm 어긋남")
        else:  # 위치를 직접 준 경우: 돌기마다 받는 구멍이 실제로 있는지 본다
            for pid, (host, gid) in pairs:
                g = host.peg(gid); h, dist = part.hole_near(g["pos"], axis=g["dir"])
                diff = (h["pos"] - g["pos"]) if h else np.array([9, 9, 9.]); err = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"])) if h else 99
                if err > TOL: s.A.log(f"{s.index}단계 {n}: 돌기 {host.n}.{gid} 를 받는 구멍이 없음({err:.1f}mm)")
        part.extra.update({"recv": True, "dir": rnd(d0 if dir is None else vec(dir)), "marks": marks})
        if hover: part.extra["hover"] = hover
        return s._add(part)

def settle_marks(part, hosts, down=None):
    """옆자리에서 제자리로 합쳐질 때 이 부품의 돌기가 들어가는 구멍 입구(받는 부품 hosts 의 구멍) 점들."""
    out = []
    for c in part.conn["pegs"]:
        g = part.world("peg", c)
        for h in hosts:
            hh, d = h.hole_near(g["pos"], axis=g["dir"])
            if hh is None: continue
            diff = hh["pos"] - g["pos"]; lat = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"]))
            along = float(np.dot(g["pos"] - hh["pos"], g["dir"]))
            if lat < 1.2 and abs(along) < 3.5: out.append(rnd(hh["pos"] - g["dir"] * hh["len"] / 2)); break
    return out

def to_side(part, Rs, Cf, Cs, until, settle_dir, hosts=()):
    """부품 하나를 옆자리(옆에서 따로 조립) 자세로 보낸다: 지금까지 계산한 자리(마지막 모양)를 final 로 두고,
    같은 강체 변환(Rs: 마지막→옆자리 회전, Cf→Cs)으로 옆자리 자세·안내(dir/marks)를 만든다. 합쳐지는 단계의 안내는 settleDir/settleMarks."""
    Rs = np.array(Rs, float); Cf = np.array(Cf, float); Cs = np.array(Cs, float)
    P = lambda q: Rs @ (np.array(q, float) - Cf) + Cs
    ex = part.extra
    side = {"p": rnd(P(part.p)), "r": R_to_euler(Rs @ part.R), "until": until}
    if "marks" in ex:
        ex["settleMarks"] = settle_marks(part, hosts) if hosts else []
        ex["marks"] = [rnd(P(m)) for m in ex["marks"]]
    if "dir" in ex: ex["dir"] = rnd(Rs @ np.array(ex["dir"], float))
    ex["settleDir"] = list(settle_dir)
    if "settleMarks" in ex and not ex["settleMarks"]: del ex["settleMarks"]
    if not hosts and "marks" not in ex: pass
    ex["side"] = side
    if hosts and "settleMarks" not in ex:
        sm = settle_marks(part, hosts)
        if sm: ex["settleMarks"] = sm

def js_value(v): return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))

def part_dict(pt, final_of=None):
    p, R = pt.p, pt.R
    d = {"n": pt.n, "p": rnd(p), "r": R_to_euler(R)}
    d.update(pt.extra)
    return d

def export_steps(A):
    out = []
    for st in A.steps:
        o = {"note": st.note}
        if st.cam:
            o["cam"] = {"theta": round(st.cam[0], 3), "phi": round(st.cam[1], 3)}; o["camSrc"] = st.camSrc
            if len(st.cam) > 2 and st.cam[2]: o["cam"]["tight"] = True   # 이번 부품만 크게(교재가 그 부분만 크게 그린 단계)
            if len(st.cam) > 3 and st.cam[3]: o["cam"]["focus"] = [[round(float(v), 1) for v in q] for q in st.cam[3]]   # 이 점들을 화면 가운데에(부품 없는 단계)
            if len(st.cam) > 4 and st.cam[4]: o["cam"]["axes"] = [round(float(v), 1) for v in st.cam[4]]   # 바닥 방향선(+X·+Z·+Y) 원점을 이 자리로(원점에서 떨어진 자리에서 만드는 단계)
            if len(st.cam) > 5 and st.cam[5]: o["cam"]["holeNums"] = True
            if len(st.cam) > 6 and st.cam[6]: o["cam"]["rings"] = [[round(float(v), 1) for v in r] for r in st.cam[6]]   # 이 단계에 고정으로 칠할 결합 점   # 이 단계에서 프레임 구멍 번호를 칠해서 보여줌   # 바닥 방향선(+X·+Z·+Y) 원점을 이 자리로(원점에서 떨어진 자리에서 만드는 단계)
        o.update(st.kw)
        o["parts"] = [part_dict(pt) for pt in st.parts]
        out.append(o)
    return out

def js_entry(A):
    L = ["  {", f"      id: {js_value(A.id)},", "      category: '큐보',", "      volume: 1,", f"      chapter: {js_value(A.chapter)},", f"      book: {js_value(A.book)},"]
    if A.camera: L.append(f"      camera: {js_value(A.camera)},")
    for k, v in A.meta.items(): L.append(f"      {k}: {js_value(v)},")
    L.append("      steps: [")
    for st in export_steps(A):
        parts = st.pop("parts"); head = ", ".join(f"{k}: {js_value(v)}" for k, v in st.items())
        L.append(f"        {{ {head}, parts: [")
        for pt in parts:
            keys = ["n", "p", "r"]; seg = ", ".join(f"{k}: {js_value(pt[k])}" for k in keys)
            for k, v in pt.items():
                if k not in keys: seg += f", {k}: {js_value(v)}"
            L.append("          { " + seg + " },")
        L.append("        ] },")
    L += ["      ],", "  }"]
    return "\n".join(L)
