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
import faces
import re

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

def orient(n, mapping):
    """부품 n 의 면이 월드 어느 쪽을 보게 할지로 자세 R 을 만든다. 예: orient("3단블록", {"돌기면 +z": "아래", "홀면 +y": "+Z"}) — 돌기면 +z 가 아래, 홀면 +y 가 +Z 쪽."""
    return faces.orient(partlib.get(n), mapping)

def rnd(v): return [round(float(x), 3) + 0.0 for x in v]

class Part:
    def __init__(s, n, R, p, step, extra=None):
        s.n, s.R, s.p, s.step, s.extra = n, np.array(R, float), np.array(p, float), step, (extra or {})
        s.conn = partlib.get(n); s.side = None
        s._base = None   # 그룹으로 옮겨지기 전의 (p, R) — 내보낼 때 원래 자세는 p·r, 옮긴 자세는 move 로 쓴다
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
    def feature(s, kind, id):
        """kind: 홀 | 돌기 -> 세계 좌표의 구멍/돌기."""
        return s.hole(id) if kind == "홀" else s.peg(id)
    @property
    def name(s):
        return f"{s.n} {s.step.A.numbering().get(id(s), 0)}번"
    def peg_near(s, pt):
        best, bd = None, 1e9
        for c in s.conn["pegs"]:
            g = s.world("peg", c); d = float(np.linalg.norm(g["pos"] - np.array(pt, float)))
            if d < bd: best, bd = g, d
        return best, bd

def rot_x(deg):
    a = np.radians(deg); c, sn = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]], float)
def rot_y(deg):
    a = np.radians(deg); c, sn = np.cos(a), np.sin(a); return np.array([[c, 0, sn], [0, 1, 0], [-sn, 0, c]], float)
def rot_z(deg):
    a = np.radians(deg); c, sn = np.cos(a), np.sin(a); return np.array([[c, -sn, 0], [sn, c, 0], [0, 0, 1]], float)

# ── 부품 방향 보고(2026-10-05): 부품마다 구멍 면·돌기 면·끝돌기가 세계의 어느 방향을 보는지 적어 준다 → 교재 그림의 모양 특징과 나란히 비교한다
def _dir_name(v):
    v = np.array(v, float); k = int(np.argmax(np.abs(v)))
    if abs(abs(v[k]) - 1) < 1e-3: return ("+" if v[k] > 0 else "-") + "XYZ"[k]
    return "(%.2f,%.2f,%.2f)" % tuple(v)
def part_orientation(pt):
    """부품 하나: [(면 이름, 세계 방향)] — 홀면 ±축 = 구멍 입구가 보는 쪽, 돌기면 ±축 = 돌기가 나온 쪽."""
    out = []
    for f in faces.faces_of(pt.conn):
        v = np.zeros(3); v[AX[f["axis"]]] = f["sign"]
        out.append((f["key"], _dir_name(pt.R @ v), len(f["items"])))
    return out
def orient_report(A, steps=None):
    """python <스크립트>.py --orient 2,4,5 처럼 부른다(steps 가 없으면 전 단계)."""
    for st in A.steps:
        if steps and st.index not in steps: continue
        for pt in st.parts:
            desc = " · ".join("%s(%d개) → %s" % (k, n, d) for k, d, n in part_orientation(pt))
            print("%d단계 %s 중심 (%.0f, %.0f, %.0f): %s" % (st.index, pt.name, pt.p[0], pt.p[1], pt.p[2], desc))

def euler_p(po): return po["p"]

FLOOR_TOL = 0.5   # 바닥 아래로 내려가도 되는 한계(mm) — floor_check 와 side_row 가 같은 값을 쓴다
ROUND_UNIT = 0.001   # rnd() 반올림 단위 — side_row 가 한계에 정확히 맞추면 반올림 오차로 floor_check 에 걸리므로 이만큼 위에 둔다
def floor_check(A, tol=FLOOR_TOL, keys=False):
    """바닥 아래로 내려가는 부품 검사(관리자 기본 규칙 2026-10-05: 조립도는 바닥 아래로 내려가지 않게).
    부품마다 ① 제자리(앞으로 옮겨지는 단계가 있으면 건너뜀) ② 새로 놓일 때 띄운 자리(옆자리면 옆자리 자세, dir·hover 만큼) ③ 옆자리에서 합쳐질 때 띄운 자리의 가장 낮은 점이 y 0 보다 tol 넘게 낮으면 모은다.
    반환: [(단계, 부품 이름, 가장 낮은 y, 어느 자리)] (keys=True 면 끝에 화면 키 "만든번호:부품순서" 를 더한다)"""
    out = []
    xf = A.meta.get("xform")
    def low(pt, p, R, off=(0, 0, 0), lift=0.0, stp=None):   # stp: 그 자세가 화면에 나오는 단계(xform 은 단계 기준으로 걸린다 — 부품이 놓인 단계가 아니라)
        size = (pt.conn or {}).get("size")
        if not size: return None
        p, R, off = np.array(p, float), np.array(R, float), np.array(off, float)
        if xf and (stp if stp is not None else pt.step.index) >= xf["at"]:   # xform(16번부터 전체를 세워 놓는 변환)이 걸린 단계는 변환한 서 있는 세계 좌표로 잰다
            Mx = np.array(xf["m"], float); p = Mx @ p + np.array(xf["t"], float); R = Mx @ R; off = Mx @ off
        sz = np.array(size, float) / 2
        if pt.n in ("중간바퀴", "작은바퀴"):   # 둥근 부품: 축(모델 y)에 수직인 원판 — 기울여도 가장 낮은 점은 반지름(x·z 최대)·두께 방향의 원통 값(상자 모서리로 재면 기울인 바퀴가 바닥 아래로 잘못 나온다, 사용자 지시 2026-10-29 배틀바이크 35번 기울이기)
            _ax = R[:, 1]; half = float(sz[1] * abs(_ax[1]) + max(sz[0], sz[2]) * float(np.sqrt(max(0.0, 1.0 - _ax[1] ** 2))))
        else:
            half = np.abs(R[1]) @ sz
        return float(p[1] + off[1] + lift - half + float(A.meta.get("floorDy") or 0))   # floorDy: 출력 단계에서 전체를 y 로 올리는 값(trike FLOOR_DY) — 검사도 올린 뒤 값으로 잰다
    for st in A.steps:
        for pt in st.parts:
            ex = pt.extra; side = ex.get("side")
            p0, R0 = pt._base if getattr(pt, "_base", None) else (pt.p, pt.R)   # 나중에 한 덩어리로 옮겨진 부품(move)은 처음 놓인 자세로 잰다
            dirv = ex.get("dir"); hv = ex.get("hover") or (20 if ex.get("recv") else 22)
            off = tuple(np.array(dirv, float) * hv) if dirv else (0, 0, 0)
            checks = []
            if side:
                checks.append(("옆자리", side["p"], euler_to_R(side["r"]), off))
                sd = ex.get("settleDir")
                if sd: checks.append(("합쳐질 때", p0, R0, tuple(np.array(sd, float) * (ex.get("settleHover") or 22))))
            else:
                _own = (ex.get("poseAt") or {}).get(str(st.index))   # 이 부품이 놓이는 단계에 별도 자세(poseAt)가 있으면 그 자세에서 띄운다(23번처럼 로봇 전체를 띄워 보여 주는 단계)
                _lf = float(((A.meta.get("lift") or {}).get(str(st.index))) or 0)   # def.lift: 이 단계는 화면 전체를 띄워 보여 준다
                checks.append(("새로 놓일 때", euler_p(_own) if _own else p0, euler_to_R(_own["r"]) if _own else R0, off, _lf))
                if "move" not in ex: checks.append(("제자리", p0, R0, (0, 0, 0), _lf))   # 그 단계가 화면 전체를 띄우면(def.lift) 띄운 값까지 더해서 잰다
                else: checks.append(("옮긴 뒤 제자리", ex["move"]["p"], euler_to_R(ex["move"]["r"]), (0, 0, 0), float(((A.meta.get("lift") or {}).get(str(ex["move"]["at"]))) or 0), int(ex["move"]["at"])))   # def.lift 가 있는 단계는 띄운 값까지 더해서 잰다
            if not side and "move" not in ex and not getattr(pt, "_base", None) and not ex.get("poseAt"):   # 뒤 번호·완성에서도 바닥 아래로 안 내려가게(사용자 지적 2026-11-01 조향자동차 완성): 이 부품이 보이는 뒤 모든 번호(완성 = 마지막+1)를 그 번호의 lift 로 잰다
                for _stp in range(max(st.index + 1, len(A.steps) - 1), len(A.steps) + 2):   # 끝 두 번호와 완성 — 차 전체가 보이는 번호(중간 번호는 창고에 따로 놓아 숨은 부품이 많아 잰 값이 틀린다)
                    checks.append(("%d단계 제자리" % _stp, p0, R0, (0, 0, 0), float(((A.meta.get("lift") or {}).get(str(_stp))) or 0), _stp))
            for _stp, _po in (ex.get("poseAt") or {}).items():   # 단계마다 다른 자세로 보여 주는 부품(눕혀서 조립)
                checks.append(("%s단계 자세" % _stp, _po["p"], euler_to_R(_po["r"]), (0, 0, 0), float(((A.meta.get("lift") or {}).get(str(_stp))) or 0), int(_stp)))   # def.lift 가 있는 단계는 띄운 값까지 더해서 잰다
            for where, p, R, o, *_lfx in checks:
                y = low(pt, p, R, o, _lfx[0] if _lfx else 0.0, _lfx[1] if len(_lfx) > 1 else None)
                if y is not None and y < -tol: out.append((st.index, pt.name, round(y, 1), where) + ((("%d:%d" % (pt.step.index, pt.step.parts.index(pt))),) if keys else ()))
    for st in A.steps:   # 앞 번호 묶음을 옮기는 번호(moveMade): 옮기는 동안 띄운 자리와 옮긴 뒤 자리도 바닥 아래로 가면 안 된다(풍차 12번, 사용자 지적 2026-11-08 — 이 자리는 부품 데이터에 안 적혀 위 검사가 못 봤다)
        for key, e in (st.kw.get("moveMade") or {}).items():
            si, pi = (int(x) for x in key.split(":")); pt = A.steps[si - 1].parts[pi]
            _lf = float(((A.meta.get("lift") or {}).get(str(st.index))) or 0); u = np.array(e["dir"], float); u = u / (np.linalg.norm(u) or 1.0)
            for where, off in (("옮기는 번호 띄운 자리", u * float(e.get("hover") or 22)), ("옮긴 뒤 제자리", (0, 0, 0))):
                y = low(pt, e["p"], euler_to_R(e["r"]), off, _lf, st.index)
                if y is not None and y < -tol: out.append((st.index, pt.name, round(y, 1), where) + ((("%d:%d" % (pt.step.index, pt.step.parts.index(pt))),) if keys else ()))
    return out

def floor_lift(A, k):
    """k번에서 바닥 아래로 내려가는 만큼을 계산해 그 번호의 화면 전체 띄움(A.meta["lift"][k])으로 적는다 — 손으로 숫자를 적지 않는다(사용자 지시 2026-11-07·08).
    부품을 띄운 자리(moveMade·dir×hover)가 바닥 아래면 그만큼(올림) 화면 전체를 올려 보여 준다. 필요 없으면 아무것도 안 한다. 반환: 올린 mm(0 이면 안 올림)."""
    lift = dict(A.meta.get("lift") or {}); lift.pop(str(k), None); A.meta["lift"] = lift
    ys = [y for (st, _n, y, _w) in floor_check(A, tol=0.0) if st == k]
    if not ys: return 0
    amt = float(np.ceil(-min(ys) - 1e-9)); A.meta["lift"] = {**lift, str(k): amt}
    return amt

class Group:
    """끝낸 조립품을 한 부품처럼 움직이게 묶는다 (사용자 지시 2026-10-04: 1번 완성품은 부품이 아니라 그룹이 하나처럼 움직인다).
    g = A.group("1번 완성품", [부품…]);  단계.move_group(g, rot_x(90), floor=True) 처럼 돌리고 옮기면 묶음 전체가 같은 회전·이동을 받는다.
    그 뒤 단계에서는 옮겨진 자세 기준으로 이름 결합(attach/recv)이 그대로 된다."""
    def __init__(s, name, parts):
        s.name, s.parts = name, list(parts)
    def center(s):
        return np.mean([pt.p for pt in s.parts], axis=0)
    def lowest(s):
        """묶음에서 가장 낮은 점의 y (부품 크기 상자를 자세대로 돌려서 잰다)."""
        lo = 1e9
        for pt in s.parts:
            size = (pt.conn or {}).get("size")
            if not size: continue
            half = np.array(size, float) / 2; ext_y = float(np.abs(pt.R[1]) @ half)
            lo = min(lo, float(pt.p[1]) - ext_y)
        return lo if lo < 1e8 else 0.0

class LazyMarks:
    """부품이 놓이는 자리(위치·방향)가 정해진 뒤에 계산하는 안내 위치. fn(part) -> 점 목록.
    lazy + [점…] 으로 좌표 목록을 이어 붙이고, lazy.where(조건)으로 일부를 거를 수 있다."""
    def __init__(s, fn, extra=None, flt=None):
        s.fn, s.extra, s.flt = fn, list(extra or []), flt
    def __add__(s, other):
        return LazyMarks(s.fn, s.extra + [list(map(float, q)) for q in other], s.flt)
    def where(s, flt):
        return LazyMarks(s.fn, s.extra, flt)
    def resolve(s, part):
        pts = s.fn(part)
        if s.flt:
            pts = [m for m in pts if s.flt(m)]
        return pts + s.extra


def tips_over(blocks):
    """놓이는 판의 윗면 위(판 발자국 안)에 있는 블록 윗돌기(+y) 끝 점들 - 판이 옮겨지면 같이 따라간다."""
    def fn(part):
        size = np.array(partlib.get(part.n)["size"], float) / 2
        h = np.abs(part.R) @ size                      # 판 발자국의 반 크기(월드 축 기준)
        lo, hi = part.p - h, part.p + h
        out = []
        for b_ in blocks:
            for c in b_.conn["pegs"]:
                g = b_.world("peg", c)
                if g["dir"][1] > 0.9:
                    t = g["pos"] + g["dir"] * g["len"] / 2
                    if lo[0] - 1e-6 <= t[0] <= hi[0] + 1e-6 and lo[2] - 1e-6 <= t[2] <= hi[2] + 1e-6:
                        out.append(rnd(t))
        return out
    return LazyMarks(fn)


def _host(A, h):
    """받는/고정 부품: Part 객체이거나 '315프레임 3번' 같은 부품 번호 이름."""
    return h if isinstance(h, Part) else A.find(h)

def _item(part, spec, kind):
    """연결점 id 이거나 이름('홀면 +y 열5·줄1', '돌기면 +z 1')이면 (id, (면 부호, 면 축) 또는 None). 점 좌표는 그대로 돌려준다."""
    if not isinstance(spec, str): return spec, None
    ids = [c["id"] for c in part.conn["pegs" if kind == "돌기" else "holes"]]
    if spec in ids: return spec, None
    r = faces.resolve_item(part.conn, spec)
    if r is None: return spec, None          # id 도 이름도 아님 → 기존 방식의 오류가 나게 둔다
    cid, k, sign, axis = r
    if k != kind: raise KeyError(f"{part.n} '{spec}': {kind} 자리에 {k} 이름을 썼다")
    return cid, (sign, axis)

def _enters(host, face, travel):
    """돌기가 travel 방향으로 들어갈 때 이름에 쓴 면(host 의 face)이 실제 입구인지(입구 면의 바깥쪽 방향은 travel 과 반대여야 한다)."""
    sign, axis = face
    n = np.zeros(3); n[AX[axis]] = sign
    return float(np.dot(host.R @ n, np.array(travel, float))) < -0.5

class Asm:
    def __init__(s, id, chapter, book, camera=None, **meta):
        s.id, s.chapter, s.book, s.camera, s.meta = id, chapter, book, camera, meta
        s.steps = []; s.parts = []; s.warn = []; s.info = []
        s.fixes = []; s.fix_used = set()
    def load_fixes(s, path):
        """관리자 수정 지시(<이름>_fixes.json)를 읽는다. 스크립트가 아니라 이 파일에 적어 두면 다시 빌드해도 지워지지 않는다.
          {"type": "join",  "part": "3단블록 5번", "peg": "돌기면 +z 1", "host": "315프레임 3번", "hole": "홀면 +y 열14·줄1", "note": "…"}   # 이 돌기가 꽂히는 자리를 바꾼다
          {"type": "shift", "part": "315프레임 3번", "delta": [dx, dy, dz], "note": "…"}                                            # place 로 놓은 부품을 옮긴다(위에 꽂힌 뒤 단계는 다시 계산되어 따라온다)
        부품 이름은 만든 순서의 번호('3단블록 5번')다. 앞 단계를 고치면 이 부품에 이름으로 붙인 뒤 단계가 자동으로 따라온다."""
        import os
        if os.path.exists(path):
            s.fixes = json.load(open(path, encoding="utf-8"))
        return s
    # ---------- 잠금(links): 좌표로 쓴 결합, 절대 좌표로 놓은 판을 "어느 부품의 어느 구멍에 붙었나"(이름)로 기록해 두고 다음 빌드부터 그것으로 위치를 계산한다 ----------
    def load_links(s, path, relock=False):
        """<이름>_links.json. 파일이 없으면 이번 빌드에서 자동으로 만든다. relock=True 면 기존 기록을 버리고 다시 만든다.
        기록은 스크립트의 좌표가 그대로일 때만 쓴다 - 스크립트를 고치면 그 부분은 낡은 기록을 버리고 다시 기록한다."""
        import os
        s.links_path = path
        s.relock = relock
        s.lock = {"attach": {}, "place": {}, "marks": {}}
        if os.path.exists(path) and not relock:
            d = json.load(open(path, encoding="utf-8"))
            s.lock["attach"] = d.get("attach", {})
            s.lock["place"] = d.get("place", {})
            s.lock["marks"] = d.get("marks", {})
        s.rec = {"attach": {}, "place": {}, "marks": {}}
        s.stale = []
        s.roots = []
        return s
    def lock_get(s, kind, key):
        return getattr(s, "lock", {}).get(kind, {}).get(key)
    def save_links(s):
        """이번 빌드의 기록을 쓴다. 수정 지시(fixes)가 있는 빌드는 위치가 수정을 포함하므로 기록을 갱신하지 않는다(--relock 으로 따로)."""
        import os
        if not hasattr(s, "links_path"):
            return None
        # 그룹으로 옮겨진 부품(move_group)은 원래 자세로 되돌려 놓고 기록한다 - 옮긴 자리로 기록하면 다음 빌드에서 판이 엉뚱한 부품에 붙어 버린다(조종형비행기 21번에서 빌드가 번갈아 실패했다)
        _sw = [(q, q.p, q.R) for q in s.parts if getattr(q, "_base", None) is not None]
        for q, _, _ in _sw: q.p, q.R = q._base[0].copy(), q._base[1].copy()
        try:
            anchors = compute_anchors(s)
        finally:
            for q, pp, RR in _sw: q.p, q.R = pp, RR
        out = {"attach": s.rec["attach"], "place": {}, "marks": s.rec["marks"]}
        for me, rec in s.rec["place"].items():
            if me in anchors:
                out["place"][me] = {**anchors[me], "p": rec["p"]}
        s.roots = [m for m in s.rec["place"] if m not in out["place"]]
        if s.fixes:
            if s.stale:
                s.log("수정 지시가 있는 빌드라 잠금 기록을 갱신하지 않았다. 낡은 기록: " + ", ".join(s.stale[:6]) + " - 수정 파일을 비우고 --relock 으로 다시 만들 것")
            return out
        old = json.load(open(s.links_path, encoding="utf-8")) if os.path.exists(s.links_path) else None
        if old != out:
            json.dump(out, open(s.links_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return out
    def lock_points(s, owner, field, pts, tol=3.5):
        """좌표로 적은 안내 위치 pts 를 "어느 부품의 구멍 입구/돌기 끝에서 얼마 떨어진 점"으로 잠가 돌려준다.
        처음엔 지금까지 만든 부품 중 tol(mm) 안에서 가장 가까운 구멍 입구·돌기 끝을 찾아 기록하고, 다음 빌드부터(스크립트 좌표가 그대로면) 그 부품의 현재 위치에서 다시 계산한다.
        가까운 특징이 없으면 좌표 그대로 둔다."""
        pts = [np.array(q, float) for q in pts]
        if not hasattr(s, "lock"):
            return [list(map(float, q)) for q in pts]
        key = f"{owner}|{field}"
        lit = [[round(float(x), 3) for x in q] for q in pts]
        L = s.lock_get("marks", key)
        if L is not None and len(L["pts"]) == len(lit):
            out = []
            ok = True
            for e, q in zip(L["pts"], lit):
                if "part" not in e:                                   # 특징에 안 붙은 점: 좌표가 그대로여야 한다
                    if np.allclose(e["point"], q, atol=0.5):
                        out.append(q)
                        continue
                    ok = False
                    break
                try:
                    Q = s.find(e["part"])
                    fid = _item(Q, e["name"], e["kind"])[0]
                    rc = list(_feature_pos(Q, e["kind"], fid, e["variant"]) + np.array(e["residual"], float))
                except KeyError:
                    ok = False
                    break
                # 스크립트 좌표가 기록과 같다(그대로 적은 점) 또는 이미 잠금 계산과 같다(앞 부품이 움직여 따라온 계산된 점) -> 유효, 잠금으로 계산한 위치를 쓴다
                if np.allclose(e["point"], q, atol=0.5) or np.allclose(rc, q, atol=0.5):
                    out.append(rc)
                else:
                    ok = False
                    break
            if ok:
                s.rec["marks"][key] = L
                return out
            s.stale.append(key)
        entries = []
        for q in pts:
            best = None
            for Q in s.parts:
                for var, kind, fid, pos in _feature_points(Q):
                    d = float(np.linalg.norm(pos - q))
                    if d <= tol and (best is None or d < best[0] - 1e-9):
                        best = (d, Q, var, kind, fid, pos)
            point = [round(float(x), 3) for x in q]
            if best:
                d, Q, var, kind, fid, pos = best
                entries.append({"part": Q.name, "variant": var, "kind": kind, "name": faces.name_of(Q.conn, kind, fid), "residual": [round(float(x), 4) + 0.0 for x in (q - pos)], "point": point})
            else:
                entries.append({"point": point})
        s.rec["marks"][key] = {"pts": entries}
        return [list(map(float, q)) for q in pts]
    def lock_marks(s, part, field, pts):
        """스크립트가 만든 부품에 나중에 좌표로 넣는 안내 위치(예: part.extra[field] = ...)도 잠가서 넣는다."""
        part.extra[field] = s.lock_points(part.name, field, pts)
        return part.extra[field]
    def next_name(s, n):
        """지금 만들려는 n 부품의 번호 이름('3단블록 5번') — 만든 순서 기준."""
        return f"{n} {1 + sum(1 for q in s.parts if q.n == n)}번"
    def fix_of(s, kind, name, key=None):
        for i, f in enumerate(s.fixes):
            if f.get("type") == kind and f.get("part") == name and (key is None or f.get("peg") == key or f.get("hole") == key):
                s.fix_used.add(i); return f
        return None
    def check_fixes(s):
        """적용되지 않은 수정 지시(부품 번호가 밀렸거나 오타)를 알려 준다 — 조용히 무시하지 않는다."""
        bad = [f for i, f in enumerate(s.fixes) if i not in s.fix_used]
        for f in bad: s.log(f"수정 지시가 적용되지 않았다: {f}")
        return bad
    def group(s, name, parts):
        g = Group(name, parts); s.__dict__.setdefault('groups', []).append(g); return g
    def apply_axes_cams(s, name, max_err=3.0, min_pts=4):
        """카메라 자동 적용: refs/<이름>/NN_axes.json 의 fit(theta·phi)이 있고 점 수·오차가 기준 안이면, 아직 짐작값(camSrc=="guess")인 번호의 카메라로 쓴다(bookcam·tiltcam·axes_fit 결과를 손으로 옮겨 적지 않는다, 사용자 지시 2026-11-09). 바뀐 번호 목록을 돌려준다."""
        import json as _j, os as _o
        R = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "refs", name); done = []
        for i, st in enumerate(s.steps, 1):
            if st.camSrc != "guess" or (st.cam and len(st.cam) > 2): continue   # 이미 맞춘 번호·tight/focus 같은 특수 카메라(다른 값이 붙은 것)는 건드리지 않는다
            fp = _o.path.join(R, "%02d_axes.json" % i)
            if not _o.path.exists(fp): continue
            try: f = (_j.load(open(fp, encoding="utf-8")) or {}).get("fit") or {}
            except Exception: continue
            if f.get("theta") is None or f.get("phi") is None or (f.get("points") or 0) < min_pts or f.get("err_px") is None or f["err_px"] > max_err: continue
            st.cam = (float(f["theta"]), float(f["phi"])); st.camSrc = "fit"; done.append(i)
        return done
    def step(s, note, cam=None, camSrc="guess", **kw):
        st = Step(s, note, cam, camSrc, kw); s.steps.append(st); return st
    def log(s, msg): s.warn.append(msg); print("  [경고]", msg)
    def note(s, msg): s.info.append(msg); print("  [규칙 자동]", msg)
    def numbering(s):
        """부품 번호 — 조립도 전체에서 같은 이름이 나온 순서(단계 → 부품 순). public/design-faces.js numberParts 와 같다."""
        order = [p for st in s.steps for p in st.parts]
        return faces.number_parts(order)
    def find(s, name):
        """'315프레임 3번'(또는 '315프레임 3/4') → 그 Part. 지금까지 만든 부품 중에서 찾는다."""
        m = re.match(r"^(.+?)\s+(\d+)\s*(?:번|/\s*\d+)?$", str(name).strip())
        if not m: raise KeyError(f"부품 번호 이름이 아니다: {name!r} (예: '315프레임 3번')")
        n, k = m.group(1), int(m.group(2)); num = s.numbering()
        for p in (q for st in s.steps for q in st.parts):
            if p.n == n and num[id(p)] == k: return p
        have = sorted(num[id(p)] for p in (q for st in s.steps for q in st.parts) if p.n == n)
        raise KeyError(f"{name}: 아직 없는 부품이다. {n} 은(는) 지금까지 {len(have)}개 만들었다")

class Step:
    def __init__(s, A, note, cam, camSrc, kw):
        s.A, s.note, s.cam, s.camSrc, s.kw, s.parts = A, note, cam, camSrc, kw, []
        s.index = len(A.steps) + 1
    def _add(s, part):
        s.parts.append(part); s.A.parts.append(part); return part
    def built(s):
        """이 단계 직전까지 끝낸 조립품 전체 = 자동으로 만들어지는 그룹(사용자 지시 2026-10-04: 순서대로 1번이 완성되면 자동으로 그룹화)."""
        return Group(f"{s.index - 1}단계까지 완성품", [pt for st in s.A.steps if st.index < s.index for pt in st.parts])
    def sprocket_wheel(s, center):
        """기본 조립세트 — 스프라켓 바퀴(스프라켓 1 + 캐터필러 14, 축 = 세계 Z, 허브 십자 구멍이 +Z 쪽). 드롭체커 12번에서 사용자 지시로 다듬은 배치를 그대로 쓴다(2026-10-24 사용자 "이 바퀴도 기본 조립세트로 등록"):
        둘레 반지름 25.8(스프라켓 피치 반지름), 링크 14개 = 25.7° 간격(톱니 14개와 0°에서 같은 각도), 링크는 축 방향 −9 에 두어 스프라켓 톱니 띠가 링크 안쪽 받침에 낀다. 링크 로컬 x → 축(Z), y → 바깥(돌기), z → 둘레. 부품 DB 에 서로 끼우는 구멍·돌기가 없어 loose(허공 검사 면제).
        center: 스프라켓 가운데(세계). 반환: (스프라켓, [캐터필러 14]).
        ★ 방향 기본 규칙(사용자 2026-10-24): 스프라켓의 돌기(+y 허브 관)는 항상 몸통(가운데) 쪽을 본다 — 대칭으로 양쪽에 다는 바퀴 모두. 이 세트는 돌기가 +Z 를 본다: 몸통이 +Z 쪽에 있으면 그대로, 몸통이 −Z 쪽이면 세트를 세로축(Y)으로 180° 돌려 쓴다. 허브 관 끝이 옆판 구멍에 3.5 들어가고 캐터필러 안쪽 끝이 옆판 바깥면에 닿게 중심을 정한다(관 끝 = 중심 +13.5)."""
        c = np.array(center, float); sp = s.place("스프라켓", np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]]), tuple(c)); sp.extra["loose"] = True; links = []
        for k in range(14):
            a = 2 * math.pi * k / 14; u = np.array([math.cos(a), math.sin(a), 0.0]); t = np.array([-math.sin(a), math.cos(a), 0.0])
            q = s.place("캐터필러", np.stack([np.array([0.0, 0.0, 1.0]), u, t], axis=1), tuple(c + 25.8 * u + np.array([0.0, 0.0, -9.0]))); q.extra["loose"] = True; links.append(q)
        return sp, links

    def copy_to_slot(s, g, slot, store, until, shift=(0, 0, 300)):
        """이미 만든 부품 묶음 g 를 그대로 복사해 다른 창고(slot)에 보관한다(교재 "N~M번 2개 만들기"의 둘째 벌 — 새로 만들지 않고 복사).
        복사본은 이번 단계 부품으로 들어가 이번 단계부터 until−1 단계까지 창고 slot 에 '보관 중'(store 이름, 화면에 안 그려짐)이고 until 단계부터 보인다.
        shift: 원본과 겹침 검사가 안 걸리게 떨어뜨려 두는 거리(보관 중에는 안 보인다). 복사본에는 안내점·화살표가 없고, 부품 개수 검사(읽기 표)에서는 빠진다. 반환: 복사한 부품 묶음(Group)."""
        sh = np.array(shift, float); out = []; hide = list(range(s.index, int(until)))
        for pt in g.parts:
            p, R = pt._base if pt._base else (pt.p, pt.R)
            ex = {"hideAt": hide, "store": store, "slot": int(slot), "noGuide": True, "copyOf": "%d:%d" % (pt.step.index, pt.step.parts.index(pt))}   # noGuide: 복사본은 안내 화살표가 없다
            out.append(s._add(Part(pt.n, R, np.array(p, float) + sh, s, ex)))
        return Group(store, out)
    def move_built(s, R, pivot=None, shift=(0, 0, 0), floor=False):
        """지금까지 끝낸 조립품 전체를 한 부품처럼 돌리고 옮긴다 (그룹을 따로 만들 필요 없음)."""
        return s.move_group(s.built(), R, pivot, shift, floor)
    def move_group(s, g, R, pivot=None, shift=(0, 0, 0), floor=False):
        """그룹 g 를 한 덩어리로 돌리고(R: 회전행렬, pivot 둘레 — 생략하면 묶음 중심) shift 만큼 옮긴다. floor=True 면 가장 낮은 점이 바닥(y=0)에 닿게 올린다.
        부품들의 새 자세는 move 로 내보내고(이 단계부터), 원래 자세는 그대로 p·r 에 남는다."""
        R = np.array(R, float); pv = g.center() if pivot is None else np.array(pivot, float)
        for pt in g.parts:
            if pt._base is None: pt._base = (pt.p.copy(), pt.R.copy())
            pt.p = R @ (pt.p - pv) + pv
            pt.R = R @ pt.R
        sh = np.array(shift, float)
        if floor: sh = sh + np.array([0.0, -g.lowest(), 0.0])
        for pt in g.parts:
            pt.p = pt.p + sh
            pt.extra["move"] = {"at": s.index, "p": rnd(pt.p), "r": R_to_euler(pt.R)}
        return g
    def move_made(s, g, R, pivot=None, shift=(0, 0, 0), dir=None, hover=60, group=None, marks=None, recv=()):
        """이미 ✓ 한 앞 번호에서 만든 부품 묶음을 이번 번호에서 옮긴다(투석기 17번). move_group 은 앞 번호 부품 데이터에 move 를 써서 ✓ 단계 지문이 바뀌어 빌드가 막히므로,
        이동은 이번 단계 데이터(kw["moveMade"] = {"만든번호:부품순서": {p, r, dir, hover, moveGroup, marks}})에만 적는다. 화면·도구는 design-assemblies.js 끝의 합치기 코드로 part.move 를 본다.
        marks 는 {부품: [안내점…]} (부품 하나당 한 번). 부품마다 한 번만 옮길 수 있다(여러 번 옮기려면 poseAt).
        recv=(부품…): 구멍을 받는 쪽으로 움직이는 부품(프레임) — 초록 링을 그 부품의 구멍 중심에 붙이고 화살표는 고정된 돌기 끝에서 시작한다(G23). 안 주면 링이 고정된 돌기 끝에 찍힌다."""
        if hover == 0: print("[경고] %s단계 move_made hover=0 — 0 은 화면 코드의 `hover || HOVER` 에서 기본 띄움이 되어 옮기는 묶음만 위로 뜬다. 띄움이 필요 없으면 hover=0.01 을 쓴다(큐보 부품결합규칙.md C6)" % getattr(s, "index", "?"))
        R = np.array(R, float); pv = g.center() if pivot is None else np.array(pivot, float); sh = np.array(shift, float)
        mm = s.kw.setdefault("moveMade", {})
        for pt in g.parts:
            if pt._base is None: pt._base = (pt.p.copy(), pt.R.copy())
            pt.p = R @ (pt.p - pv) + pv + sh; pt.R = R @ pt.R
            e = {"p": rnd(pt.p), "r": R_to_euler(pt.R), "dir": [float(v) for v in (dir if dir is not None else [0, 1, 0])], "hover": hover}
            if group is not None: e["moveGroup"] = group
            if isinstance(marks, dict) and id(pt) in marks: e["marks"] = marks[id(pt)]
            mm["%d:%d" % (pt.step.index, pt.step.parts.index(pt))] = e
        if isinstance(marks, str) and marks == "auto":   # 옮긴 묶음이 제자리에서 합쳐지는 안내점은 결합에서 계산한다(손 좌표·숫자 금지, G21): 끼우는 돌기 → 받는 구멍 입구, 받는 구멍 ← 받는 돌기 끝
            hosts = [q for q in s.A.parts if all(q is not pt for pt in g.parts)]
            for pt in g.parts:
                mk = join_marks(pt, hosts)
                if mk: mm["%d:%d" % (pt.step.index, pt.step.parts.index(pt))]["marks"] = mk
        for pt in recv:
            k_ = "%d:%d" % (pt.step.index, pt.step.parts.index(pt))
            if k_ in mm: mm[k_]["recv"] = True
        return g
    def place(s, n, R, p, **extra):
        """위치가 정해진 부품(구멍에 끼우는 안내가 필요 없는 부품: 바닥판 등). 수정 파일에 shift 가 있으면 그만큼 옮긴다."""
        p = s._anchored(n, R, p)
        f = s.A.fix_of("shift", s.A.next_name(n))
        if f: p = tuple(np.array(p, float) + np.array(f["delta"], float))
        if "enter" in extra:   # enter=(받는 부품, 구멍) — 이 부품의 돌기가 들어가는 구멍 입구가 안내점(손 좌표 금지: 결합에서 계산, 옆자리 조립이면 옆자리만큼 옮긴다)
            _host_, _hole_ = extra.pop("enter"); hp = _host(s.A, _host_); h = hp.hole(_item(hp, _hole_, "홀")[0])
            _tmp = Part(n, np.array(R, float), (0, 0, 0), s); d = _tmp.peg(_tmp.conn["pegs"][0]["id"])["dir"]
            ent = h["pos"] - d * (h["len"] / 2); sd = extra.get("side")
            _hv = extra.get("dir")   # 끼우는 쪽(dir)이 돌기 방향과 같거나 반대여도(축처럼 양 끝을 쓰는 부품) 입구는 dir 쪽 면이다(G21)
            if _hv is not None and abs(float(np.dot(np.array(_hv, float) / np.linalg.norm(np.array(_hv, float)), d))) > 0.98:
                ent = h["pos"] + np.array(_hv, float) / np.linalg.norm(np.array(_hv, float)) * (h["len"] / 2)
            if sd: ent = ent + (np.array(sd["p"], float) - np.array(p, float))
            extra["marks"] = [rnd(ent)]
        s._resolve_lazy(n, R, p, extra)
        s._lock_extra(n, extra)
        return s._add(Part(n, R, p, s, extra))
    def _resolve_lazy(s, n, R, p, extra):
        """LazyMarks 로 준 안내 위치를 이 부품의 최종 자리(p, R)로 계산한다."""
        for field in ("marks", "faceMarks", "holeMarks", "settleMarks"):
            if isinstance(extra.get(field), LazyMarks):
                extra[field] = extra[field].resolve(Part(n, np.array(R, float), p, s))
    def _lock_extra(s, n, extra):
        """부품을 만들 때 좌표로 같이 준 안내 위치(marks 등)를 잠근다."""
        for field in ("marks", "faceMarks", "holeMarks", "settleMarks"):
            if field in extra and extra[field]:
                extra[field] = s.A.lock_points(s.A.next_name(n), field, extra[field])
    def _anchored(s, n, R, p):
        """절대 좌표로 준 위치 p 를, 잠긴 기록이 있으면 "앞 부품 구멍 옆" 상대 위치로 바꾼다(기록은 스크립트 좌표가 그대로일 때만 쓴다)."""
        A = s.A
        if not hasattr(A, "lock"):
            return p
        me = A.next_name(n)
        lit = [round(float(x), 3) for x in p]
        A.rec["place"][me] = {"p": lit}
        L = A.lock_get("place", me)
        if L is None:
            return p
        if np.linalg.norm(np.array(L["p"], float) - np.array(lit)) > 0.5:
            A.stale.append(me)
            return p
        host = None
        try:
            host = A.find(L["host"])
            if getattr(host, "_base", None) is not None:   # 앞 번호에서 move_made 로 옮겨진 부품은 만들 때의 자세로 계산한다(save_links 의 기록과 같은 기준 — 옮긴 자리로 계산하면 새 창고 부품이 옮겨진 부품 옆으로 날아가 빌드마다 위치가 번갈아 바뀐다, 스티어카 7번 2026-10-31)
                _pp, _RR = host.p, host.R; host.p, host.R = host._base[0].copy(), host._base[1].copy()
            else:
                _pp = None
            tmp = Part(n, np.array(R, float), (0, 0, 0), s)
            mid = _item(tmp, L["mine"][1], L["mine"][0])[0]
            hid = _item(host, L["hostf"][1], L["hostf"][0])[0]
            return tuple(host.feature(L["hostf"][0], hid)["pos"] + np.array(L["offset"], float) - tmp.feature(L["mine"][0], mid)["pos"])
        except (KeyError, IndexError):
            A.stale.append(me)
            return p
        finally:
            if host is not None and _pp is not None: host.p, host.R = _pp, _RR
    def place_next(s, n, R, mine, host, hole, offset=(0, 0, 0), **extra):
        """판처럼 돌기가 없는 부품을 **앞 부품의 구멍 옆**에 놓는다(안내 화살표 없이). 내 구멍(mine)이 host 의 구멍(hole)에서 offset(월드 mm)만큼 떨어진 자리가 되게 위치를 계산한다.
        예: s.place_next("35프레임", R, "홀면 +y 열5·줄1", "315프레임 3번", "홀면 +y 열1·줄1", (-10, 0, 0)) — 35프레임 열5·줄1 이 315프레임 열1·줄1 에서 −x 로 한 칸 옆.
        host 가 옮겨지면(수정 지시) 이 부품도 따라온다. 수정 파일의 shift 는 여기에도 적용된다."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        hp = _host(s.A, host); mid = _item(tmp, mine, "홀")[0]; hid = _item(hp, hole, "홀")[0]
        p = hp.hole(hid)["pos"] + np.array(offset, float) - tmp.hole(mid)["pos"]
        f = s.A.fix_of("shift", s.A.next_name(n))
        if f: p = p + np.array(f["delta"], float)
        return s._add(Part(n, R, p, s, extra))
    def _rest_pos(s, n, R, mine, host, hole, toward):
        """place_rest 의 위치 계산(몸통 면이 host 구멍 끝면에 닿는 자리) → (부품 원점 위치, toward 방향 몸통 반폭)."""
        tmp = Part(n, R, (0, 0, 0), s); t = np.array(toward, float); t = t / np.linalg.norm(t)
        hp = _host(s.A, host); mid = _item(tmp, mine, "홀")[0]; hid = _item(hp, hole, "홀")[0]; h = hp.hole(hid)
        size = np.array(tmp.conn.get("size") or partlib.get(n)["size"], float)
        half = float(np.dot(np.abs(t), np.abs(R) @ (size / 2)))   # toward 방향으로 몸통 반폭(상자, 몸통 중심 = 부품 원점)
        face = h["pos"] + t * (h["len"] / 2)
        hsize = np.array(hp.conn.get("size") or partlib.get(hp.n)["size"], float)   # 받는 부품의 몸통 면이 구멍 끝보다 더 나와 있으면(구멍 길이 < 몸통 두께, 작은기어) 몸통 면에 닿는다 — 파고들지 않는다(G21)
        face_t = max(float(np.dot(face, t)), float(np.dot(np.array(hp.p, float), t)) + float(np.dot(np.abs(t), np.abs(np.array(hp.R, float)) @ (hsize / 2))))
        lateral = (h["pos"] - tmp.hole(mid)["pos"]); lateral = lateral - np.dot(lateral, t) * t
        p = lateral + face_t * t + t * half
        return p, half
    def rest_shift(s, part, mine, host, hole, toward):
        """합치는 이동량: 이미 놓은 부품 part 가 host 구멍 끝면에 몸통이 닿도록(place_rest 와 같은 규칙) 옮길 벡터."""
        p, _half = s._rest_pos(part.n, np.array(part.R, float), mine, host, hole, toward)
        return p - np.array(part.p, float)
    def place_rest(s, n, R, mine, host, hole, toward, **extra):
        """부품을 **앞 부품 구멍의 끝면에 몸통이 닿게** 놓는다(물리법칙: 겹치지 않고 떠 있지도 않다). toward = 이 부품이 놓이는 쪽(세계 방향, 예: (0, 1, 0) 은 host 구멍 위쪽).
        끝면 = host 구멍 가운데에서 toward 로 구멍 길이의 절반(홀 테두리 끝면 포함), 몸통 두께 = 부품 크기(dims.json)를 자세 R 로 돌린 toward 방향 폭.
        구멍 길이(place_next)가 아니라 몸통 크기로 재므로 몸통이 구멍보다 길어도 파고들지 않는다. 옆으로는 내 구멍(mine)이 host 구멍(hole) 위에 오게 맞춘다."""
        R = np.array(R, float); p, half = s._rest_pos(n, R, mine, host, hole, toward)
        f = s.A.fix_of("shift", s.A.next_name(n))
        if f: p = p + np.array(f["delta"], float)
        if extra.get("recv") and "thick" not in extra: extra["thick"] = round(2 * half, 3)   # 받는 판 두께 = 몸통 두께(dims)
        via = extra.pop("via", None)   # via=(고정 부품, 돌기) — 위치는 면 규칙으로 정하고, 안내점은 그 돌기에서 끼우는 쪽(dir)에서 먼저 닿는 끝에 찍는다(축에 끼우는 기어·부시, G21)
        if via is not None:
            _vh = _host(s.A, via[0]); _vg = _vh.peg(_item(_vh, via[1], "돌기")[0]); _dv = np.array(extra.get("dir") or _vg["dir"], float)
            extra["marks"] = [rnd(_vg["pos"] + _vg["dir"] * _vg["len"] / 2 * (1 if float(np.dot(_dv, _vg["dir"])) >= 0 else -1))]
        return s._add(Part(n, R, p, s, extra))
    def place_hang(s, n, R, mine, host, peg, face, toward, **extra):
        """축처럼 긴 돌기에 끼우는 부품을 **몸통 면이 face(toward 방향 좌표값)에 닿게** 놓는다 — 닿는 부품이 뒤 번호에서 올라와 아직 없을 때(G21, 면과 면은 틈 없이 붙는다).
        toward = 이 부품 몸통이 face 에서 뻗는 쪽(세계 방향). 옆으로는 내 구멍(mine)이 host 의 돌기(peg) 축 위에 오고, 안내점은 그 돌기에서 끼우는 쪽(dir)에 먼저 닿는 끝이다."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s); t = np.array(toward, float); t = t / np.linalg.norm(t)
        hp = _host(s.A, host); g = hp.peg(_item(hp, peg, "돌기")[0]); mid = _item(tmp, mine, "홀")[0]
        size = np.array(tmp.conn.get("size") or partlib.get(n)["size"], float)
        half = float(np.dot(np.abs(t), np.abs(R) @ (size / 2)))
        lateral = g["pos"] - tmp.hole(mid)["pos"]; lateral = lateral - np.dot(lateral, t) * t
        p = lateral + (float(face) + half) * t
        f = s.A.fix_of("shift", s.A.next_name(n))
        if f: p = p + np.array(f["delta"], float)
        _dv = np.array(extra.get("dir") if extra.get("dir") is not None else g["dir"], float)
        extra["marks"] = [rnd(g["pos"] + g["dir"] * g["len"] / 2 * (1 if float(np.dot(_dv, g["dir"])) >= 0 else -1))]
        if extra.get("recv") and "thick" not in extra: extra["thick"] = round(2 * half, 3)
        return s._add(Part(n, R, p, s, extra))
    def place_by(s, n, R, links, **extra):
        """안내 화살표 없이 놓되 위치를 **앞 부품에 대한 결합으로** 정한다(place 의 상대 위치 판). 앞 부품이 옮겨지면 이 부품도 따라온다.
        links: {내 구멍 이름/id: (고정 부품 이름/객체, 돌기 이름/id)} — recv 와 같은 모양. 첫 결합으로 위치를 정하고 나머지는 어긋남을 검사한다."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s); me = s.A.next_name(n)
        pairs = []
        for pid, (host, gid) in links.items():
            hp = _host(s.A, host); pid2, _ = _item(tmp, pid, "홀"); gid2, _ = _item(hp, gid, "돌기")
            pairs.append((pid2, hp, gid2))
        p = None
        for pid, hp, gid in pairs:
            g = hp.peg(gid); d = g["dir"]; myh = tmp.hole(pid)
            base = g["pos"] - d * g["len"] / 2
            hole_center = base + d * myh["len"] / 2 if g["len"] >= myh["len"] else g["pos"] + d * (myh["len"] - g["len"]) / 2
            if p is None: p = hole_center - myh["pos"]
        part = Part(n, R, p, s, extra)
        for pid, hp, gid in pairs[1:]:
            g = hp.peg(gid); h = part.hole(pid); diff = h["pos"] - g["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"]))
            if err > TOL: s.A.log(f"{s.index}단계 {n}: 돌기 {hp.n}.{gid} 와 {err:.1f}mm 어긋남")
        return s._add(part)
    # 내 돌기 → 받는 구멍
    def attach(s, n, R, links, dir=None, hover=None, rivet=False, **extra):
        """links: {내 돌기 id: (받는 부품, 목표점 또는 구멍 id)}. 첫 연결로 위치를 정하고 나머지는 어긋남을 검사한다.
        rivet=True 면 리벳 몸통 가운데가 구멍 입구 면에 온다(양 끝이 두 부품에 반반 들어감)."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        # 이름으로 쓴 돌기·구멍('돌기면 +z 1', '315프레임 3번' → '홀면 +y 열15·줄1')을 id 로 바꾼다. id·좌표로 써도 된다.
        _lk, _faces = [], []
        for pid, (host, tgt) in links.items():
            hp = _host(s.A, host); pid2, _ = _item(tmp, pid, "돌기"); tgt2, fc = _item(hp, tgt, "홀")
            _lk.append((pid2, (hp, tgt2))); _faces.append((pid2, hp, fc, tgt))
        me = s.A.next_name(n)   # 관리자 수정(join): 이 부품의 이 돌기가 꽂히는 자리를 파일에 적은 대로 바꾼다
        for i, f in enumerate(s.A.fixes):   # 이 부품(me)의 join 수정: 파일의 peg 이름을 id 로 풀어 같은 돌기를 찾는다
            if f.get("type") != "join" or f.get("part") != me: continue
            pfx = _item(tmp, f["peg"], "돌기")[0]
            for j, (pid2, _) in enumerate(_lk):
                if pid2 == pfx:
                    hp2 = _host(s.A, f["host"]); tgt3, fc3 = _item(hp2, f["hole"], "홀")
                    _lk[j] = (pid2, (hp2, tgt3)); _faces[j] = (pid2, hp2, fc3, f["hole"]); s.A.fix_used.add(i)
        # 좌표로 가리킨 결합은 "어느 부품의 어느 구멍"(이름)으로 잠가 둔다 -> 앞 부품이 옮겨지면 따라온다
        pts = {}
        for j, (pid2, (hp, tgt2)) in enumerate(_lk):
            if isinstance(tgt2, str) or not hasattr(s.A, "lock"):
                continue
            key = f"{me}|{pid2}"
            pt = [round(float(x), 3) for x in tgt2]
            L = s.A.lock_get("attach", key)
            if L is not None and np.linalg.norm(np.array(L["point"], float) - np.array(pt)) <= 0.5:
                try:
                    hp2 = s.A.find(L["host"])
                    tgt3, fc3 = _item(hp2, L["hole"], "홀")
                    _lk[j] = (pid2, (hp2, tgt3))
                    _faces[j] = (pid2, hp2, None, tgt2)
                    s.A.rec["attach"][key] = L
                    continue
                except KeyError:
                    pass
            if L is not None:
                s.A.stale.append(key)
            pts[pid2] = (key, pt)
        items = _lk; p = None; marks = []; d0 = None
        def target(host, tgt, mypeg):
            return host.hole(tgt) if isinstance(tgt, str) else host.hole_near(tgt, axis=mypeg["dir"])[0]
        for pid, (host, tgt) in items:
            mypeg = tmp.peg(pid); h = target(host, tgt, mypeg)
            if h is None: s.A.log(f"{s.index}단계 {n}.{pid}: 받는 구멍이 없음({host.n} {tgt})"); continue
            if pid in pts:   # 좌표로 가리킨 결합이 실제로 어느 구멍이었는지 기록
                key, pt = pts[pid]
                s.A.rec["attach"][key] = {"host": host.name, "hole": faces.name_of(host.conn, "홀", h["id"]), "point": pt}
            d = mypeg["dir"]; surf = h["pos"] - d * (h["len"] / 2)   # 돌기가 들어가는 면(구멍 입구) 가운데
            if p is None:
                p = surf if rivet else (surf + d * mypeg["len"] / 2) - mypeg["pos"]   # tmp 는 p=0 이라 mypeg["pos"] 가 곧 R·(로컬 위치)
                d0 = d
            marks.append(rnd(surf))
        if p is not None and not rivet and n in SINK_PARTS and d0 is not None:   # 볼트·너트의 가장 큰 부분(머리·너트 몸)은 프레임 구멍 안으로 들어가 프레임 면 밖으로 안 나온다(사용자 기본 규칙 2026-10-24): 돌기 밑동이 면에 닿는 자리에서 머리 두께만큼 구멍 안쪽으로 더 넣는다
            _dm = _sink_dims().get(n)
            if _dm:
                _pc = next((c for c in tmp.conn["pegs"] if c["id"] == _lk[0][0]), None)
                if _pc:
                    _ld = np.array(_pc["dir"], float); _ax = int(np.argmax(np.abs(_ld)))
                    _prot = float(np.dot(np.array(_pc["pos"], float) - _ld * _pc["len"] / 2, _ld) + _dm[_ax] / 2)
                    if _prot > 0.05: p = p + d0 * _prot
        if p is not None and n == "T축" and d0 is not None and "기어" in items[0][1][0].n:   # 규칙(큐보 부품결합규칙.md '구멍보다 큰 것은 지나갈 수 없다'): 홀 테두리가 없는 기어에서는 T축 머리가 구멍을 못 지나가 기어 윗면 위에 남는다 — T축 길이 30 안에 머리가 들어 있어 몸통 시작점에서 머리 두께만큼 바깥으로 올린다(사용자 2026-11-04, 44·47번 지적)
            _ht = head_thickness(n)
            if _ht is None: s.A.log(f"{s.index}단계 {n}: 머리 두께가 부품 상세내역에 없어 머리가 밖으로 남는 위치를 못 정했다(partlib.py 로 heads.json 을 만든다)")
            else: p = p - d0 * _ht
        part = Part(n, R, p if p is not None else (0, 0, 0), s, extra)
        for pid, (host, tgt) in items[1:]:
            pg = part.peg(pid); h = target(host, tgt, pg)
            if h is None: continue
            diff = pg["pos"] - h["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, pg["dir"]) * pg["dir"]))
            if err > TOL: s.A.log(f"{s.index}단계 {n}.{pid}: {host.n} 구멍과 {err:.1f}mm 어긋남")
        for pid2, hp, fc, tgt in _faces:   # 이름에 쓴 면이 돌기가 들어가는 입구가 맞는지(앞뒤를 거꾸로 쓴 실수)
            if fc is not None and not _enters(hp, fc, part.peg(pid2)["dir"]):
                s.A.log(f"{s.index}단계 {n}: '{tgt}' 은(는) {hp.n} 에서 돌기가 들어오는 쪽 면이 아니다(앞뒤가 반대)")
        if d0 is not None and dir is not None and float(np.dot(np.array(vec(dir), float), np.array(d0, float))) > 0.01:   # 띄우는 방향(dir)은 돌기가 들어가는 방향의 반대여야 한다 — 같으면 부품이 구멍 속으로 파묻혀 안 보이고 연결점(초록 점)만 공중에 남는다(2026-11-08 로봇팽이 12번 리벳, 사용자 "떨어지면 자동 에러로 잡혀야지")
            s.A.log(f"{s.index}단계 {n}: ❌ 띄우는 방향 dir {[round(float(v), 2) for v in vec(dir)]} 이 돌기 방향 {[round(float(v), 2) for v in d0]} 과 같은 쪽 — 부품이 구멍 속으로 파묻혀 안 보이고 연결점만 공중에 뜬다(dir 는 돌기 방향의 반대, 생략하면 자동)")
        part.extra.update({"dir": rnd(-d0 if dir is None else vec(dir)), "marks": marks})
        if hover: part.extra["hover"] = hover
        if n == "T축" and "pegDepth" not in part.extra and _lk and _ht_ok(n):
            part.extra["pegDepth"] = round(float(tmp.peg(_lk[0][0])["len"]) - head_thickness(n), 3)   # 안내 화살표 시작 = 돌기 길이 − 머리 두께(손 pegDepth 금지)
        return s._add(part)
    def _seat_nut(s, n, R, p, hosts):
        """너트를 볼트 끝이 아니라 볼트가 지나는 판 묶음의 맨 아래 면에 앉힌다 — 너트 목(돌기)이 판 구멍 안으로 들어가고 머리(넓은 쪽)가 홀 테두리 면에 닿는다. 볼트가 지나는 판이 없으면 그대로 둔다."""
        import obb
        bolt = next((h for h in hosts if h.n in ("8볼트", "12볼트")), None)
        if bolt is None: return p
        dims = _sink_dims(); c = bolt.conn["pegs"][0]; ld = np.array(c["dir"], float); dw = bolt.R @ ld
        base = bolt.p + bolt.R @ (np.array(c["pos"], float) - ld * c["len"] / 2)
        head = float(np.dot(np.array(c["pos"], float) - ld * c["len"] / 2, ld) + np.array(dims[bolt.n], float)[int(np.argmax(np.abs(ld)))] / 2)
        hide = s.kw.get("hideMade") or {}; bot = None
        for q in s.A.parts:
            if q.n not in dims or not ("프레임" in q.n or "블록" in q.n or q.n == "서보혼") or str(q.step.index) in hide: continue
            d = np.array(dims[q.n], float) / 2
            if any(obb.contains(base - dw * head + dw * t, q.p, q.R, d, 0.01) for t in np.arange(0.25, c["len"] + head, 0.5)):
                sp = obb.span(obb.corners(q.p, q.R, d), dw); bot = sp[1] if bot is None else max(bot, sp[1])
        if bot is None: return p
        nc = partlib.get(n)["pegs"][0]; nl = np.array(nc["dir"], float); dn = np.array(R, float) @ nl
        if float(np.dot(dn, dw)) > -0.9: return p
        nb = np.array(p, float) + np.array(R, float) @ (np.array(nc["pos"], float) - nl * nc["len"] / 2)
        return tuple(float(v) for v in np.array(p, float) + dw * (bot - 1.0 - float(np.dot(nb, dw))))   # 너트 머리(넓은 쪽 1mm)는 홀 테두리 안에 들어가 판 면과 같다 → 목 밑동은 면에서 1.0 안쪽(G2, SINK_PARTS 와 같은 값)
    def recv(s, n, R, links, dir=None, hover=None, p=None, keep_dropped_check=True, against=None, **extra):
        """움직이는 쪽이 구멍을 받는 쪽(프레임이 블록 끝 돌기에 얹히는 경우).
        links 가 dict {내 구멍 id: (고정 부품, 돌기 id)} 면 위치 p 를 계산하고, [(고정 부품, 돌기 id), ...] 목록이면 p 를 직접 줘야 한다."""
        _ffh = extra.pop("faceFromHole", False)   # True 면 리벳에 끼우는 받는 부품의 링(faceMarks·thick)을 구멍 연결점에서 계산한다 — 이 조립도만 켠다(다른 조립도 안내를 안 바꾸려고 2026-11-10)
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        raw = list(links.items()) if isinstance(links, dict) else [(None, x) for x in links]
        pairs, _faces = [], []
        for pid, (host, gid) in raw:   # 이름으로 쓴 내 구멍('홀면 +y 열5·줄1')·고정 부품의 돌기('돌기면 +z 1')를 id 로 바꾼다
            hp = _host(s.A, host)
            pid2, fc = (None, None) if pid is None else _item(tmp, pid, "홀")
            gid2, _ = _item(hp, gid, "돌기")
            pairs.append((pid2, (hp, gid2))); _faces.append((pid2, hp, fc, pid, gid2))
        _keep = [i for i, (pid, (host, gid)) in enumerate(pairs) if not _peg_occupied_by(s.A, host, gid, None, s)]   # 규칙 7: 돌기 하나는 프레임 한 장에만 든다 — 이미 다른 프레임 구멍에 든 돌기는 이 부품에 잇지 않는다(안내점도 안 낸다, 토끼 22번 2026-11-04)
        if keep_dropped_check and 0 < len(_keep) < len(pairs):
            for i, (pid, (host, gid)) in enumerate(pairs):
                if i not in _keep: s.A.note(f"{s.index}단계 {n}: 돌기 {host.n}.{gid} 는 이미 {_peg_occupied_by(s.A, host, gid, None, s)} 구멍에 들어 있어 결합에서 뺐다(규칙 7)")
            pairs = [pairs[i] for i in _keep]; _faces = [_faces[i] for i in _keep]
        _hand = None
        if p is not None and not MAGNET_OFF and ("프레임" in n or "블록" in n) and HAND_LOG is None:
            raise ValueError(f"{s.index}단계 {n}: 프레임·블록 결합에는 손으로 준 위치 p= 를 쓸 수 없다 — 결합(돌기↔구멍)만 적으면 자석처럼 붙는다(사용자 2026-11-03)")
        if p is not None and not MAGNET_OFF and ("프레임" in n or "블록" in n):   # 결합은 항상 자석처럼 붙는다(사용자 2026-11-03: 큐보 모든 결합이 그 방식) — 손으로 준 p 는 어느 구멍인지 찾는 데만 쓰고, 위치는 규칙(돌기 면과 구멍 면이 딱 맞닿음)으로 다시 계산한다
            _hint = Part(n, R, p, s); _np = []
            for pid, (host, gid) in pairs:
                g = host.peg(gid)
                if pid is None:
                    _h, _dist = _hint.hole_near(g["pos"], axis=g["dir"]); pid = _h["id"] if _h else None
                _np.append((pid, (host, gid)))
            if all(x[0] is not None for x in _np):
                _hand = np.array(p, float); pairs = _np; p = None
                if HAND_LOG is not None:
                    import sys as _sys
                    _f = _sys._getframe(1); HAND_LOG.append({"file": _f.f_code.co_filename, "line": _f.f_lineno, "n": n, "ids": [x[0] for x in _np], "was_dict": isinstance(links, dict)})
        marks = []; _face = []; _thick = None; d0 = None; calc = p is None
        for pid, (host, gid) in pairs:
            g = host.peg(gid); d = g["dir"]; tip = g["pos"] + d * g["len"] / 2
            if calc:
                myh = tmp.hole(pid); base = g["pos"] - d * g["len"] / 2
                if against is not None and host.n.endswith("축") and dir is not None:   # 통과 부품(축)에 끼우는 받는 부품이 다른 부품(against)의 면에 닿을 때까지 밀어 넣는다(부시가 블록 바깥면에 붙는 자리, 2026-11-09). 값은 against 부품의 크기·내 두께에서 계산한다 — 손값 p= 아님(C6)
                    import obb
                    _a = -np.array(dir, float); _a = _a / np.linalg.norm(_a)   # dir = 결합 전에 띄우는 방향(뷰어·guidecheck 와 같다) → 밀어 넣는 방향은 그 반대
                    _ag = _host(s.A, against); _hs = np.array(_ag.conn.get("size") or partlib.get(_ag.n)["size"], float) / 2
                    _lo = obb.span(obb.corners(_ag.p, _ag.R, _hs), _a)[0]
                    _th = float(np.array(tmp.conn.get("size") or partlib.get(n)["size"], float)[int(np.argmax(np.abs(np.array([h for h in tmp.conn["holes"] if h["id"] == pid][0]["dir"], float))))])   # 내 구멍 축(부품 로컬) 방향 두께
                    hole_center = g["pos"] + _a * (_lo - _th / 2 + float(np.dot(myh["pos"], _a)) - float(np.dot(g["pos"], _a)))
                    _thick = _th   # 뷰어 링 = 끝 − 방향×두께/2 가 구멍 중심에 오도록 이 부품의 실제 두께를 알려 준다(바퀴 16 처럼 기본 5 와 다른 부품)
                    _face.append(rnd(hole_center - _a * min(_th / 2, float(myh.get('len') or _th) / 2 + 2.5)))   # 끝은 구멍 길이 안쪽(guidecheck: 구멍 반길이+3 이내)으로, 링 오차는 1.5 이내가 되게   # 화살표 끝(faceMarks): 뷰어 링 = 끝 − 방향×두께/2 가 구멍 중심에 오도록(guidecheck G23). 꼬리(marks)는 고정된 돌기 끝(축 끝)   # 몸통 가운데가 면에서 두께/2 떨어지게(구멍 위치 어긋남 myh.pos 보정)
                else:
                    hole_center = base + d * myh["len"] / 2 if g["len"] >= myh["len"] else g["pos"] + d * (myh["len"] - g["len"]) / 2
                if host.n == "리벳":   # 리벳으로 프레임과 프레임을 잇는 곳은 두 프레임이 딱 붙는다(사용자 기본 규칙 2026-10-24): 받는 판의 면이 리벳 가운데(= 먼저 꽂은 쪽 프레임 면)에 닿게 한다 — 돌기 밑동 기준(위)으로 놓으면 1.5mm 뜬다
                    hole_center = np.array(host.p, float) + d * myh["len"] / 2
                    _th = float(np.array(tmp.conn.get("size") or partlib.get(n)["size"], float)[int(np.argmax(np.abs(np.array([h for h in tmp.conn["holes"] if h["id"] == pid][0]["dir"], float))))])   # 리벳에 끼우는 받는 부품(2026-11-10 G26): 꼬리 = 리벳 돌기 끝 연결점(그대로), 머리 = 받는 부품 자기 구멍 연결점에서 계산한 faceMarks 로 링이 구멍 중심에 오게 한다
                    if _ffh and abs(float(np.dot(tip - d * 2.5 - hole_center, d))) > 1.5:   # 기본 두께(5) 공식으로 링이 구멍 중심에서 1.5mm 넘게 벗어날 때만 — 이미 맞는 다른 조립도의 안내는 건드리지 않는다
                        _thick = _th
                        _face.append(rnd(hole_center + d * min(_th / 2, float(myh.get("len") or _th) / 2 + 2.5)))
                if p is None: p = hole_center - myh["pos"]   # myh 는 이미 세계 방향으로 돌린 값(tmp 의 p=0)
            if d0 is None: d0 = d
            _dv = d if dir is None else np.array(dir, float)   # 안내점 = 끼우는 쪽(dir)에서 먼저 닿는 돌기 끝: dir 이 돌기 방향과 반대면 뿌리 쪽 끝(축 아래에서 부시를 끼우는 경우, G21)
            marks.append(rnd((tip if (host.n != "축" or float(np.dot(_dv, d)) >= 0) else g["pos"] - d * g["len"] / 2)))   # against: 화살표 끝 = 받는 구멍이 앉을 자리(면에 닿은 자리)   # 축(양 끝을 쓰는 통과 부품, G21)만 끼우는 쪽 끝, 나머지는 돌기 끝(tip)
        if not calc:
            p = s._anchored(n, R, p)
            s._resolve_lazy(n, R, p, extra)
            s._lock_extra(n, extra)
        if calc and n == "너트" and getattr(s.A, "seat_nuts", True): p = s._seat_nut(n, R, p, [h for _, (h, _g) in pairs])   # 너트 머리가 볼트가 지나는 판 묶음 맨 아래 홀 테두리 면에 닿게(사용자 2026-11-03)
        part = Part(n, R, p, s, extra)
        if calc and _hand is not None and float(np.linalg.norm(np.array(p, float) - _hand)) > 0.2: s.A.log(f"{s.index}단계 {n}: 손으로 준 위치가 결합 규칙 위치와 {float(np.linalg.norm(np.array(p, float) - _hand)):.1f}mm 달라 규칙 위치로 놓음")
        if calc:
            for pid, (host, gid) in pairs[1:]:
                g = host.peg(gid); h = part.hole(pid); diff = h["pos"] - g["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"]))
                if err > TOL: s.A.log(f"{s.index}단계 {n}.{pid}: 돌기 {host.n}.{gid} 와 {err:.1f}mm 어긋남")
        else:  # 위치를 직접 준 경우: 돌기마다 받는 구멍이 실제로 있는지 본다
            for pid, (host, gid) in pairs:
                g = host.peg(gid); h, dist = part.hole_near(g["pos"], axis=g["dir"])
                diff = (h["pos"] - g["pos"]) if h else np.array([9, 9, 9.]); err = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"])) if h else 99
                if err > TOL: s.A.log(f"{s.index}단계 {n}: 돌기 {host.n}.{gid} 를 받는 구멍이 없음({err:.1f}mm)")
        for pid2, hp, fc, pname, gid2 in _faces:   # 내 구멍 이름의 면이 고정 돌기가 들어오는 입구가 맞는지
            if fc is not None and not _enters(part, fc, hp.peg(gid2)["dir"]):
                s.A.log(f"{s.index}단계 {n}: '{pname}' 은(는) {n} 에서 돌기가 들어오는 쪽 면이 아니다(앞뒤가 반대)")
        part.extra.update({"recv": True, "dir": rnd(d0 if dir is None else vec(dir)), "marks": marks})
        if _face: part.extra["faceMarks"] = _face
        if _thick: part.extra.setdefault("thick", round(float(_thick), 2))
        part._axle_links = [(host, gid, pid) for pid, (host, gid) in pairs if host.n.endswith("축")]   # 축에 끼운 부품이면 어느 축·돌기·내 구멍인지 기억(violations 의 축 위치 점검이 읽는다, 저장 데이터에는 안 들어간다)
        if "settleDir" in part.extra and "settleMarks" not in part.extra and marks: part.extra["settleMarks"] = [list(m) for m in marks]; part.extra["marks"] = []   # 옆자리에서 합쳐지는 번호의 안내점 = 받는 돌기 끝(손 좌표 금지, 토끼 15번 2026-11-04)
        if hover: part.extra["hover"] = hover
        _ex = part.extra.get("explode")
        if isinstance(_ex, dict) and "offset" not in _ex and hover: _ex["offset"] = [round(float(x) * hover, 3) for x in vec(part.extra["dir"])]   # 결합 전에 띄운 모습 = 끼우는 방향으로 hover 만큼(손 offset 금지)
        part._hole_ids = [pid for pid, _ in pairs if pid]   # 끼우는 부품이 쓴 자기 구멍 id — stepchecks 의 holeid_check 가 읽기 표 링 칸에 그 번호가 적혔는지 본다(내보내기·지문에는 안 들어간다)
        return s._add(part)

def _peg_occupied_by(A, host, gid, skip, step=None):
    """host 의 돌기 gid 가 이미 들어가 있는 다른 부품(구멍 하나라도 축 어긋남 ≤1.2mm·돌기와 구멍 구간이 1mm 이상 겹침)의 이름, 없으면 None."""
    if host.n in ("T축", "8볼트", "12볼트", "너트", "서보고정볼트") or host.n.endswith("축"): return None   # 축·볼트는 여러 판을 지나는 부품(규칙 7 은 리벳·블록·서보·모터 돌기)
    g = host.peg(gid); d = g["dir"]; hide = (step.kw.get("hideMade") or {}) if step is not None else {}   # 이 번호에서 숨긴 앞 부품(다른 창고)은 같은 자리여도 보지 않는다(A3)
    for o in A.parts:
        if o is host or o is skip or not o.conn or str(o.step.index) in hide: continue
        for c in o.conn["holes"]:
            h = o.world("hole", c)
            if abs(float(np.dot(h["dir"], d))) < 0.98: continue
            rel = g["pos"] - h["pos"]; a = float(np.dot(rel, h["dir"])); lat = float(np.linalg.norm(rel - h["dir"] * a))
            if lat > 1.2: continue
            ov = min(a + (g["len"] or 0) / 2, (h["len"] or 0) / 2) - max(a - (g["len"] or 0) / 2, -(h["len"] or 0) / 2)   # 깊이 없는 구멍(큰기어 등)은 0 으로
            if ov >= 1.0: return f"{o.n}.{h['id']}"
    return None

def _ht_ok(n):
    return head_thickness(n) is not None

HAND_LOG = None
_HEADS = None
def head_thickness(name):
    """대가리(머리) 두께 mm — 부품 상세내역(대가리_몸통."대가리 두께_mm")에서 partlib.py 가 만든 heads.json. 없으면 None(숫자를 지어내지 않는다)."""
    global _HEADS
    if _HEADS is None:
        import os as _o
        _p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "heads.json")
        _HEADS = json.load(open(_p, encoding="utf-8")) if _o.path.exists(_p) else {}
    h = _HEADS.get(name); return None if not h else float(h["두께"])
MAGNET_OFF = False   # True 면 옛 방식(손으로 준 p 를 그대로 씀)
SINK_PARTS = ("8볼트", "12볼트", "너트", "서보고정볼트")   # 머리·몸이 프레임 면 밖으로 나오면 안 되는 부품(구멍에 묻는다)
_SINK_DIMS = None
def _sink_dims():
    global _SINK_DIMS
    if _SINK_DIMS is None:
        import json as _j, os as _o
        _p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "dims.json")
        _SINK_DIMS = _j.load(open(_p, encoding="utf-8")) if _o.path.exists(_p) else {}
    return _SINK_DIMS

def _feature_points(q):
    """부품 q 의 구멍 입구/출구/중심, 돌기 끝/밑동의 세계 좌표 목록 [(변형, 종류, id, 좌표)]."""
    out = []
    for c in q.conn["holes"]:
        h = q.world("hole", c); hl = h["len"] or 0.0   # 길이 없는 연결점(축 구멍 등, len=None)도 중심만 쓴다 — 새 안내점을 잠글 때 단계의 모든 부품을 훑다가 죽던 버그(오토건 10번 2026-11-10)
        out += [("entry", "홀", h["id"], h["pos"] - h["dir"] * hl / 2), ("exit", "홀", h["id"], h["pos"] + h["dir"] * hl / 2), ("center", "홀", h["id"], h["pos"])]
    for c in q.conn["pegs"]:
        g = q.world("peg", c); gl = g["len"] or 0.0
        out += [("tip", "돌기", g["id"], g["pos"] + g["dir"] * gl / 2), ("base", "돌기", g["id"], g["pos"] - g["dir"] * gl / 2)]
    return out


def _feature_pos(q, kind, fid, variant):
    for var, k, i, pos in _feature_points(q):
        if var == variant and k == kind and i == fid:
            return pos
    raise KeyError((q.n, kind, fid, variant))


def _mate(peg, hole):
    dd = float(np.dot(peg["dir"], hole["dir"]))
    if not (dd > 0.9 or (hole["through"] and dd < -0.9)):
        return False
    rel = peg["pos"] - hole["pos"]
    along = float(np.dot(rel, hole["dir"]))
    lat = float(np.linalg.norm(rel - along * hole["dir"]))
    return lat < 2 and abs(along) <= ((peg["len"] or 0) + (hole["len"] or 0)) / 2 + 1


def compute_anchors(A):
    """절대 좌표로 놓은 부품(place / recv(p=...))마다 "앞에 만든 부품 Q 의 어느 구멍에서 얼마 떨어져 있나"를 구한다.
    Q 와 직접 꽂혀 있거나(돌기<->구멍), 둘 다에 돌기를 꽂은 부품(예: 이음매에 걸친 블록)으로 이어진 가장 가까운 앞 부품을 고른다.
    이어진 앞 부품이 없으면 뿌리(절대 좌표 그대로)다."""
    parts = [q for st in A.steps for q in st.parts]
    idx = {id(q): i for i, q in enumerate(parts)}
    pegs = {id(q): [q.world("peg", c) for c in q.conn["pegs"]] for q in parts}
    holes = {id(q): [q.world("hole", c) for c in q.conn["holes"]] for q in parts}
    inn = {}   # 구멍 가진 부품 b -> [(돌기 가진 부품 a, 돌기 id, 구멍 id)]
    for a in parts:
        for pg in pegs[id(a)]:
            for b in parts:
                if b is a:
                    continue
                for ho in holes[id(b)]:
                    if _mate(pg, ho):
                        inn.setdefault(id(b), []).append((a, pg["id"], ho["id"]))
    names = {id(q): q.name for q in parts}
    out = {}
    for me in A.rec["place"]:
        P = next((q for q in parts if names[id(q)] == me), None)
        if P is None:
            continue
        best = None
        for Q in sorted((q for q in parts if idx[id(q)] < idx[id(P)] and q.step.kw.get("slot", 1) == P.step.kw.get("slot", 1)), key=lambda q: -idx[id(q)]):   # 같은 창고 부품만 — 새 창고(원점)의 부품이 다른 창고 부품의 돌기·구멍과 우연히 같은 자리에 있다고 그 뒤를 따라가면 안 된다(해머배틀 29번 오른쪽 블록이 19번 서보고정볼트를 따라 1.3mm 내려앉음, 2026-11-03)
            for a, pgid, hoid in inn.get(id(P), []):      # Q 의 돌기가 P 의 구멍에
                if a is Q:
                    best = (("홀", hoid), ("돌기", pgid), Q)
                    break
            if best:
                break
            for a, pgid, hoid in inn.get(id(Q), []):      # P 의 돌기가 Q 의 구멍에
                if a is P:
                    best = (("돌기", pgid), ("홀", hoid), Q)
                    break
            if best:
                break
            for a, pgid, hoid in inn.get(id(P), []):      # 다리: P 의 구멍과 Q 의 구멍에 모두 돌기를 꽂은 부품 K
                for a2, pgid2, hoid2 in inn.get(id(Q), []):
                    if a2 is a and a is not Q and a is not P and pgid2 != pgid:
                        best = (("홀", hoid), ("홀", hoid2), Q)
                        break
                if best:
                    break
            if best:
                break
        if not best:
            continue
        (mk, mid), (hk, hid), Q = best
        off = P.feature(mk, mid)["pos"] - Q.feature(hk, hid)["pos"]
        out[me] = {"host": Q.name, "mine": [mk, faces.name_of(P.conn, mk, mid)], "hostf": [hk, faces.name_of(Q.conn, hk, hid)],
                   "offset": [round(float(x), 4) + 0.0 for x in off]}
    return out


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

def recv_shift(part, hole, host, peg):
    """합치는 이동량(받는 쪽): part 의 구멍(hole)이 host 의 돌기(peg)를 받도록 — recv 와 같은 규칙으로 구멍 가운데가 놓일 자리 — 옮길 벡터."""
    h = part.hole(hole); g = host.peg(peg); d = g["dir"]; base = g["pos"] - d * g["len"] / 2
    hc = base + d * h["len"] / 2 if g["len"] >= h["len"] else g["pos"] + d * (h["len"] - g["len"]) / 2
    return hc - h["pos"]

def merge_shift(part, peg, host, hole):
    """합치는 이동량: part 의 돌기(peg)가 host 의 구멍(hole)에 들어가도록 — 돌기 밑동이 구멍 입구 면에 닿게(attach 와 같은 규칙) — 옮길 벡터."""
    hp = host if hasattr(host, "hole") else None
    g = part.peg(peg); h = hp.hole(hole); d = g["dir"]; surf = h["pos"] - d * (h["len"] / 2)
    return (surf + d * g["len"] / 2) - g["pos"]

def join_marks(part, hosts):
    """옮겨진 부품 part 가 고정 부품 hosts 와 합쳐질 때의 안내점: part 의 돌기가 들어가는 hosts 구멍 입구(돌기 방향 반대쪽 면)와, part 의 구멍으로 들어오는 hosts 돌기의 끝."""
    out = []
    for c in part.conn["pegs"]:
        g = part.world("peg", c)
        for h in hosts:
            if not h.conn: continue
            hh, d = h.hole_near(g["pos"], axis=g["dir"])
            if hh is None: continue
            diff = hh["pos"] - g["pos"]; lat = float(np.linalg.norm(diff - np.dot(diff, g["dir"]) * g["dir"]))
            along = float(np.dot(g["pos"] - hh["pos"], g["dir"]))
            if lat < 1.2 and abs(along) < 3.5: out.append(rnd(hh["pos"] - g["dir"] * hh["len"] / 2)); break
    for c in part.conn["holes"]:
        hp_ = part.world("hole", c)
        for h in hosts:
            if not h.conn: continue
            for pc in h.conn["pegs"]:
                g = h.world("peg", pc)
                if abs(float(np.dot(g["dir"], hp_["dir"]))) < 0.98: continue
                rel = hp_["pos"] - g["pos"]; a = float(np.dot(rel, g["dir"])); lat = float(np.linalg.norm(rel - g["dir"] * a))
                tip = g["pos"] + g["dir"] * g["len"] / 2
                if lat < 1.2 and abs(a) <= g["len"] / 2 + hp_["len"] / 2: out.append(rnd(tip)); break   # 구멍이 돌기(축처럼 긴 것 포함) 구간 안에 있으면 안내점 = 돌기 끝(G21)
    return out

PITCH = 10.0   # 큐보 구멍 간격(mm) — 옆자리 작업 위치를 벌리는 기본 여유(큐보 공통 상수)

def _corners(q):
    size = np.array(q.conn.get("size") or partlib.get(q.n)["size"], float)
    return [np.array(q.p, float) + np.array(q.R, float) @ (np.array([sx, sy, sz]) * size / 2) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]

def side_row(groups, anchor, Rs, lift, row, gap=PITCH, refs=None, floor=False):
    """옆자리 작업 위치(새 창고)를 규칙으로 정한다: 완성된 쪽(anchor 부품들) 위로 묶음 크기 + 여유(gap)만큼 lift 방향으로 띄우고,
    묶음이 여럿이면 폭 + 여유 간격으로 row 방향에 나란히 늘어놓는다(서로 겹치지 않게). groups = [[부품…], …], Rs = to_side 의 회전, refs = 각 묶음의 기준 부품(기본: 첫 부품).
    돌려주는 값 = 묶음마다 to_side 에 줄 Cs(기준 부품의 최종 자리 Cf 가 옮겨 갈 곳)."""
    Rs = np.array(Rs, float); lift = np.array(lift, float); lift = lift / np.linalg.norm(lift); row = np.array(row, float); row = row / np.linalg.norm(row)
    refs = refs or [g[0] for g in groups]
    ac = np.array([c for q in anchor for c in _corners(q)]); amin, amax = ac.min(axis=0), ac.max(axis=0); acen = (amin + amax) / 2
    info = []
    for g, ref in zip(groups, refs):
        Cf = np.array(ref.p, float)
        pts = np.array([Rs @ (c - Cf) for q in g for c in _corners(q)]); mn, mx = pts.min(axis=0), pts.max(axis=0)
        info.append(((mn + mx) / 2, mx - mn))   # 변환 뒤 묶음 가운데(Cs 기준 상대)·크기
    lift_dist = float(np.dot(np.abs(lift), amax - amin)) / 2 + max(float(np.dot(np.abs(lift), e)) for _c, e in info) / 2 + gap
    widths = [float(np.dot(np.abs(row), e)) for _c, e in info]; total = sum(widths) + gap * (len(groups) - 1); pos = -total / 2
    out = []
    for (cen, _e), w in zip(info, widths):
        target = acen + lift * lift_dist + row * (pos + w / 2); pos += w + gap
        out.append(target - cen)
    if floor:   # 바닥(y=0) 아래로 내려가면 그 묶음만 바닥 위로 올린다(G15) — floor_check 와 같게 부품마다 옆자리 자세 + 띄운 자리(dir × hover)까지 잰다
        for j, (g, ref) in enumerate(zip(groups, refs)):
            Cf = np.array(ref.p, float); low = 0.0
            for q in g:
                size = np.array(q.conn.get("size") or partlib.get(q.n)["size"], float) / 2; Rq = Rs @ np.array(q.R, float)
                cen = float((Rs @ (np.array(q.p, float) - Cf))[1]) + float(out[j][1])
                dv = q.extra.get("dir"); hv = q.extra.get("hover") or (20 if q.extra.get("recv") else 22)
                off = float((Rs @ np.array(dv, float))[1]) * hv if dv is not None else 0.0
                low = min(low, cen + off - float(np.abs(Rq[1]) @ size) + FLOOR_TOL - ROUND_UNIT)
            if low < 0: out[j] = out[j] + np.array([0.0, -low, 0.0])
    return out

def to_side(part, Rs, Cf, Cs, until, settle_dir, hosts=(), keep_settle=False):
    """부품 하나를 옆자리(옆에서 따로 조립) 자세로 보낸다: 지금까지 계산한 자리(마지막 모양)를 final 로 두고,
    같은 강체 변환(Rs: 마지막→옆자리 회전, Cf→Cs)으로 옆자리 자세·안내(dir/marks)를 만든다. 합쳐지는 단계의 안내는 settleDir/settleMarks."""
    Rs = np.array(Rs, float); Cf = np.array(Cf, float); Cs = np.array(Cs, float)
    P = lambda q: Rs @ (np.array(q, float) - Cf) + Cs
    ex = part.extra
    side = {"p": rnd(P(part.p)), "r": R_to_euler(Rs @ part.R), "until": until}
    if "marks" in ex:
        if not (keep_settle and ex.get("settleMarks")): ex["settleMarks"] = settle_marks(part, hosts) if hosts else []   # keep_settle=True: recv 가 이미 낸 받는 쪽 안내점(settleMarks)은 지우지 않는다(풍차). 기본은 옛 동작(토끼 저장본 유지)
        ex["marks"] = [rnd(P(m)) for m in ex["marks"]]
        if ex.get("faceMarks"): ex["faceMarks"] = [rnd(P(m)) for m in ex["faceMarks"]]   # 화살표 머리(faceMarks)도 marks 와 같은 변환으로 옆자리에 옮긴다(2026-11-10: 안 옮겨 최종 좌표에 남던 문제)
    if "dir" in ex: ex["dir"] = rnd(Rs @ np.array(ex["dir"], float))
    if settle_dir: ex["settleDir"] = list(settle_dir)   # 합쳐지는 방향이 없는 부품(받는 쪽 안내가 없는 블록 등)은 settleDir 를 새로 만들지 않는다
    if "settleMarks" in ex and not ex["settleMarks"]: del ex["settleMarks"]
    if not hosts and "marks" not in ex: pass
    ex["side"] = side
    if hosts and "settleMarks" not in ex:
        sm = settle_marks(part, hosts)
        if sm: ex["settleMarks"] = sm

def js_value(v): return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))

def part_dict(pt, final_of=None):
    p, R = pt._base if getattr(pt, "_base", None) else (pt.p, pt.R)
    d = {"n": pt.n, "p": rnd(p), "r": R_to_euler(R)}
    d.update(pt.extra)
    return d

def export_steps(A):
    out = []
    A.apply_axes_cams(A.id.split('-', 2)[-1])   # 모든 조립도 공통: NN_axes.json 이 있는 번호의 카메라는 손으로 적지 않고 그 값을 쓴다(사용자 지시 2026-11-09)
    _legacy = A.id in ('cubo-1-airplane', 'cubo-1-autogun', 'cubo-1-soccer', 'cubo-1-trike')   # 규칙(2026-10-05)보다 먼저 만든 조립도는 알림만
    for _si, _nm, _y, _wh in floor_check(A):   # 관리자 기본 규칙: 조립도는 바닥 아래로 내려가지 않게 — 새 조립도는 build.py 가 [경고] 로 막는다
        print('%s 바닥 아래로 내려가는 부품: %d단계 %s (가장 낮은 y %.1f, %s)' % ('[알림]' if _legacy else '[경고]', _si, _nm, _y, _wh))
    for st in A.steps:
        o = {"note": st.note}
        if st.cam:
            o["cam"] = {"theta": round(st.cam[0], 3), "phi": round(st.cam[1], 3)}; o["camSrc"] = st.camSrc
            if len(st.cam) > 2 and st.cam[2]: o["cam"]["tight"] = True   # 이번 부품만 크게(교재가 그 부분만 크게 그린 단계)
            if len(st.cam) > 3 and st.cam[3]: o["cam"]["focus"] = [[round(float(v), 1) for v in q] for q in st.cam[3]]   # 이 점들을 화면 가운데에(부품 없는 단계)
            if len(st.cam) > 4 and st.cam[4]: o["cam"]["axes"] = [round(float(v), 1) for v in st.cam[4]]   # 바닥 방향선(+X·+Z·+Y) 원점을 이 자리로(원점에서 떨어진 자리에서 만드는 단계)
            if len(st.cam) > 5 and st.cam[5]: o["cam"]["rings"] = [[round(float(v), 1) for v in r] for r in st.cam[5]]   # 이 단계에 고정으로 칠할 결합 점   # 이 단계에서 프레임 구멍 번호를 칠해서 보여줌   # 바닥 방향선(+X·+Z·+Y) 원점을 이 자리로(원점에서 떨어진 자리에서 만드는 단계)
        o.update(st.kw)
        o["parts"] = [part_dict(pt) for pt in st.parts]
        out.append(o)
    return out

def js_entry(A):
    _m = re.match(r"cubo-(\d+)-", A.id)   # 조립도 id(cubo-2-speedbike)의 권 번호 — 2권 조립도가 1권으로 등록되던 것을 막는다(2026-10-09)
    _vol = int(_m.group(1)) if _m else 1
    L = ["  {", f"      id: {js_value(A.id)},", "      category: '큐보',", f"      volume: {_vol},", f"      chapter: {js_value(A.chapter)},", f"      book: {js_value(A.book)},"]
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
