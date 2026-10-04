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
        s.steps = []; s.parts = []; s.warn = []
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
        anchors = compute_anchors(s)
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
    def step(s, note, cam=None, camSrc="guess", **kw):
        st = Step(s, note, cam, camSrc, kw); s.steps.append(st); return st
    def log(s, msg): s.warn.append(msg); print("  [경고]", msg)
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
    def place(s, n, R, p, **extra):
        """위치가 정해진 부품(구멍에 끼우는 안내가 필요 없는 부품: 바닥판 등). 수정 파일에 shift 가 있으면 그만큼 옮긴다."""
        p = s._anchored(n, R, p)
        f = s.A.fix_of("shift", s.A.next_name(n))
        if f: p = tuple(np.array(p, float) + np.array(f["delta"], float))
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
        try:
            host = A.find(L["host"])
            tmp = Part(n, np.array(R, float), (0, 0, 0), s)
            mid = _item(tmp, L["mine"][1], L["mine"][0])[0]
            hid = _item(host, L["hostf"][1], L["hostf"][0])[0]
            return tuple(host.feature(L["hostf"][0], hid)["pos"] + np.array(L["offset"], float) - tmp.feature(L["mine"][0], mid)["pos"])
        except (KeyError, IndexError):
            A.stale.append(me)
            return p
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
        part = Part(n, R, p if p is not None else (0, 0, 0), s, extra)
        for pid, (host, tgt) in items[1:]:
            pg = part.peg(pid); h = target(host, tgt, pg)
            if h is None: continue
            diff = pg["pos"] - h["pos"]; err = float(np.linalg.norm(diff - np.dot(diff, pg["dir"]) * pg["dir"]))
            if err > TOL: s.A.log(f"{s.index}단계 {n}.{pid}: {host.n} 구멍과 {err:.1f}mm 어긋남")
        for pid2, hp, fc, tgt in _faces:   # 이름에 쓴 면이 돌기가 들어가는 입구가 맞는지(앞뒤를 거꾸로 쓴 실수)
            if fc is not None and not _enters(hp, fc, part.peg(pid2)["dir"]):
                s.A.log(f"{s.index}단계 {n}: '{tgt}' 은(는) {hp.n} 에서 돌기가 들어오는 쪽 면이 아니다(앞뒤가 반대)")
        part.extra.update({"dir": rnd(-d0 if dir is None else vec(dir)), "marks": marks})
        if hover: part.extra["hover"] = hover
        return s._add(part)
    def recv(s, n, R, links, dir=None, hover=None, p=None, **extra):
        """움직이는 쪽이 구멍을 받는 쪽(프레임이 블록 끝 돌기에 얹히는 경우).
        links 가 dict {내 구멍 id: (고정 부품, 돌기 id)} 면 위치 p 를 계산하고, [(고정 부품, 돌기 id), ...] 목록이면 p 를 직접 줘야 한다."""
        R = np.array(R, float); tmp = Part(n, R, (0, 0, 0), s)
        raw = list(links.items()) if isinstance(links, dict) else [(None, x) for x in links]
        pairs, _faces = [], []
        for pid, (host, gid) in raw:   # 이름으로 쓴 내 구멍('홀면 +y 열5·줄1')·고정 부품의 돌기('돌기면 +z 1')를 id 로 바꾼다
            hp = _host(s.A, host)
            pid2, fc = (None, None) if pid is None else _item(tmp, pid, "홀")
            gid2, _ = _item(hp, gid, "돌기")
            pairs.append((pid2, (hp, gid2))); _faces.append((pid2, hp, fc, pid, gid2))
        marks = []; d0 = None; calc = p is None
        for pid, (host, gid) in pairs:
            g = host.peg(gid); d = g["dir"]; tip = g["pos"] + d * g["len"] / 2
            if calc:
                myh = tmp.hole(pid); base = g["pos"] - d * g["len"] / 2
                hole_center = base + d * myh["len"] / 2 if g["len"] >= myh["len"] else g["pos"] + d * (myh["len"] - g["len"]) / 2
                if p is None: p = hole_center - myh["pos"]   # myh 는 이미 세계 방향으로 돌린 값(tmp 의 p=0)
            if d0 is None: d0 = d
            marks.append(rnd(tip))
        if not calc:
            p = s._anchored(n, R, p)
            s._resolve_lazy(n, R, p, extra)
            s._lock_extra(n, extra)
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
        for pid2, hp, fc, pname, gid2 in _faces:   # 내 구멍 이름의 면이 고정 돌기가 들어오는 입구가 맞는지
            if fc is not None and not _enters(part, fc, hp.peg(gid2)["dir"]):
                s.A.log(f"{s.index}단계 {n}: '{pname}' 은(는) {n} 에서 돌기가 들어오는 쪽 면이 아니다(앞뒤가 반대)")
        part.extra.update({"recv": True, "dir": rnd(d0 if dir is None else vec(dir)), "marks": marks})
        if hover: part.extra["hover"] = hover
        return s._add(part)

def _feature_points(q):
    """부품 q 의 구멍 입구/출구/중심, 돌기 끝/밑동의 세계 좌표 목록 [(변형, 종류, id, 좌표)]."""
    out = []
    for c in q.conn["holes"]:
        h = q.world("hole", c)
        out += [("entry", "홀", h["id"], h["pos"] - h["dir"] * h["len"] / 2), ("exit", "홀", h["id"], h["pos"] + h["dir"] * h["len"] / 2), ("center", "홀", h["id"], h["pos"])]
    for c in q.conn["pegs"]:
        g = q.world("peg", c)
        out += [("tip", "돌기", g["id"], g["pos"] + g["dir"] * g["len"] / 2), ("base", "돌기", g["id"], g["pos"] - g["dir"] * g["len"] / 2)]
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
    return lat < 2 and abs(along) <= (peg["len"] + hole["len"]) / 2 + 1


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
        for Q in sorted((q for q in parts if idx[id(q)] < idx[id(P)]), key=lambda q: -idx[id(q)]):
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
    p, R = pt._base if getattr(pt, "_base", None) else (pt.p, pt.R)
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
            if len(st.cam) > 5 and st.cam[5]: o["cam"]["rings"] = [[round(float(v), 1) for v in r] for r in st.cam[5]]   # 이 단계에 고정으로 칠할 결합 점   # 이 단계에서 프레임 구멍 번호를 칠해서 보여줌   # 바닥 방향선(+X·+Z·+Y) 원점을 이 자리로(원점에서 떨어진 자리에서 만드는 단계)
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
