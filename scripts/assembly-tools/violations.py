# 규칙 위반을 번호별로 모아 화면이 종류마다 다른 색·기호로 칠하게 한다(사용자 지시 2026-11-08). 읽기만 한다.
#   python violations.py <이름>      번호별 위반 목록을 보여 준다(build.py 는 collect() 로 def.violations 를 만든다)
# 종류: floor ▼ 바닥 아래(asmlib.floor_check) · mark ⌖ 안내점이 부품 자기 연결점에 안 맞음(guidecheck: recv 누락·링이 자기 구멍 아님·화살표 끝/꼬리가 구멍·돌기 끝에서 뜸) · link ◎ 그 밖의 안내 문제(안내점·방향 없음 등)
#       store ▣ 다른 창고에 있는 부품이 이 번호 화면에 보임(hidecheck.stray_loc) · overlap ✕ 겹침(부피 교집합만) · bond ⧉ 결합 규칙(K1 규칙1·4·5~7·16) · gap ↔ 틈 · orient ↻ 방향(cubo_joint_check 가 메시지와 함께 부품 키 LAST 를 내준다).
# 항목: {"type", "keys": ["만든번호:부품순서"…], "msg"} — 키는 화면 부품 키와 같다(moveMade 키와 같은 모양).
import asmpath
import json
import sys, os, re, runpy
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
CENTER_TOL = 100   # mm — 번호 완성 모습의 x·z 중심 허용 오차("대략 중심", 사용자 2026-11-12; 숫자는 임의값 — 비행기 본체가 ±95 라 100 으로 두고 480~650mm 이탈만 잡는다. 사용자가 정하면 바꾼다)

def _load(name):
    os.chdir(HERE)
    g = runpy.run_path(name + ".py", run_name="probe")
    return next(v for v in g.values() if hasattr(v, "steps") and hasattr(v, "parts") and hasattr(v, "meta"))

def axle_bad(A, tol=1.5):
    """축에 끼운 부품(recv 가 _axle_links 를 기억한 것)의 위치 어긋남 [(번호, 부품순서, 설명)]. 번호마다 부품 자세는 guidecheck 와 같이 pose_at 으로 둔다."""
    import stepchecks
    _orig = {id(q): (np.array(q.p, float), np.array(q.R, float)) for q in A.parts}
    out = []
    try:
        for k in range(1, len(A.steps) + 1):
            for q in A.parts: q.p, q.R = _orig[id(q)][0].copy(), _orig[id(q)][1].copy()
            for q in A.parts:
                if q.step.index <= k: q.p, q.R = stepchecks.pose_at(A, q, k)
            for i, q in enumerate(A.steps[k - 1].parts):
                for host, gid, pid in getattr(q, "_axle_links", []):
                    g = host.peg(gid); d = np.array(g["dir"], float); d = d / np.linalg.norm(d)
                    hs = [x for x in q.conn["holes"] if x["id"] == pid] or list(q.conn["holes"])   # 구멍 id 를 모르면(목록 형식 연결) 축 중심선에 가장 가까운 구멍
                    best = None
                    for c in hs:
                        v = np.array(q.world("hole", c)["pos"], float) - np.array(g["pos"], float); al = float(np.dot(v, d)); of = float(np.linalg.norm(v - al * d))
                        if best is None or of < best[0]: best = (of, al)
                    off, along = best
                    if off > tol: out.append((k, i, "%s 가 %s 축 중심선에서 %.1fmm 벗어남(≤%.1f)" % (q.n, host.n, off, tol)))
                    elif abs(along) > g["len"] / 2 + 0.5: out.append((k, i, "%s 가 %s 축 길이 밖에 있음(축 중심에서 %.1fmm, 반 길이 %.1f)" % (q.n, host.n, along, g["len"] / 2)))
    finally:
        for q in A.parts: q.p, q.R = _orig[id(q)][0].copy(), _orig[id(q)][1].copy()
    return out

def nohole_bad(A, tol=1.5, minlen=10.0):
    """모터(DC·서보)에 T축·축(돌기 길이 ≥minlen)을 결합하는 번호에서, 막대가 모터 안으로 들어가는 자리에 막대와 나란한 모터 구멍이 있는지(옆 거리 ≤tol) 본다(사용자 지시 2026-11-10: 8번 T축이 모터 구멍 없는 곳에 끼워짐 — 모터에 T축·축을 결합할 때만).
    막대가 그 번호에 새로 놓인 번호만 본다. [(번호, 막대 부품순서, 설명)]"""
    import stepchecks
    out = []
    for k in range(1, len(A.steps) + 1):
        allp = [q for j in range(1, k + 1) for q in A.steps[j - 1].parts if q.conn]
        if not any(q.n in ("T축", "축") for q in A.steps[k - 1].parts): continue   # 막대가 새로 놓이는 번호만 자세를 계산한다
        try: pose = {id(q): stepchecks.pose_at(A, q, k) for q in allp}
        except Exception: continue   # 옛 형식(구멍 id 가 다른) 조립도는 자세를 못 구하면 건너뛴다
        for i, s in enumerate(A.steps[k - 1].parts):
            if s.n not in ("T축", "축") or not s.conn: continue
            for g in s.conn.get("pegs", []):
                ln = float(g.get("len") or 0)
                if ln < minlen: continue
                p, R = pose[id(s)]; c = p + R @ np.array(g["pos"], float); d = R @ np.array(g["dir"], float); d = d / np.linalg.norm(d)
                ts = np.arange(-ln / 2 + 0.5, ln / 2 - 0.4, 1.0)
                for o in allp:
                    if o is s or o.n not in ("DC모터", "서보모터") or not o.conn.get("size"): continue
                    op, oR = pose[id(o)]; half = np.array(o.conn["size"], float) / 2 - 0.3
                    tin = [t for t in ts if np.all(np.abs(oR.T @ (c + d * t - op)) <= half)]
                    if len(tin) < 2: continue
                    best = None
                    for h in o.conn.get("holes", []):
                        hp = op + oR @ np.array(h["pos"], float); hd = oR @ np.array(h["dir"], float); hd = hd / (np.linalg.norm(hd) or 1.0)
                        if abs(abs(float(np.dot(hd, d))) - 1) > 0.02: continue
                        w = hp - c; al = float(np.dot(w, d))
                        if al < min(tin) - 1.0 or al > max(tin) + 1.0: continue   # 막대가 들어가는 구간의 구멍만(모터 뒷면 구멍이 우연히 같은 줄에 있어도 안 쳐 준다)
                        off = float(np.linalg.norm(w - al * d))
                        if best is None or off < best: best = off
                    if best is None or best > tol:
                        out.append((k, i, "%s 가 들어가는 %s 에 그 자리 구멍이 없음 — 막대 중심선에서 가장 가까운 모터 구멍이 %s(≤%.1f)" % (s.n, o.n, "없음" if best is None else "%.1fmm" % best, tol)))
    return out

_SHAFTY = ("DC모터", "서보모터", "T축", "축", "부시")

def _hidden_at(q, k):
    """k번 화면에서 숨겨진 부품인가(hideAt 은 숨길 번호 목록, 한 개면 그 번호부터)."""
    ha = (q.extra or {}).get("hideAt")
    return bool(ha) and (k in [int(x) for x in ha] if isinstance(ha, (list, tuple, set)) else int(ha) <= k)

def occupied_holes(A, k, lat=1.5, ov=0.5):
    """k번 화면에서 한 구멍에 서로 다른 부품의 돌기가 둘 이상 들어 있는 곳(사용자 지시 2026-11-09: 연결점을 이미 쓴 구멍에 또 결합하면 모니터링 — 리벳·블록 돌기로 막힌 프레임 구멍에 눈블록 같은 돌기를 또 꽂음).
    결합 자세(최종 자리) 기준이다. 돌기 둘이 한 구멍 축(옆 거리 ≤lat)·구멍 깊이 안에서 ov mm 넘게 겹치고, 둘 중 하나는 k번에 새로 놓였거나 옮긴 부품이면 걸린다.
    [(k번 부품 순서들, 설명)] — 부품 순서는 A.steps[k-1].parts 의 index."""
    import stepchecks
    out = []
    cur = {id(p): i for i, p in enumerate(A.steps[k - 1].parts)}
    allp = [q for j in range(1, k + 1) for q in A.steps[j - 1].parts if q.conn and not _hidden_at(q, k)]   # 숨겨진 부품(작업대로 옮겨 만든 1번 부품 등)은 같은 자리의 작업대 부품과 겹쳐 잡히지 않게 뺀다
    pose = {id(q): stepchecks.pose_at(A, q, k) for q in allp}
    def wr(q, c):
        p, R = pose[id(q)]; return p + R @ np.array(c["pos"], float), R @ np.array(c["dir"], float)
    pegs = []   # (부품, 돌기id, 시작점, 방향, 길이)
    for q in allp:
        for c in q.conn.get("pegs", []):
            pos, d = wr(q, c); pegs.append((q, c["id"], pos, d / (np.linalg.norm(d) or 1.0), float(c.get("len") or 0)))
    seen = set()
    for h in allp:
        if not h.n.endswith("프레임"): continue   # 프레임 구멍만(블록 구멍은 양쪽에서 돌기가 들어가는 것이 정상)
        for hc in h.conn.get("holes", []):
            hp, hd = wr(h, hc); hd = hd / (np.linalg.norm(hd) or 1.0); hl = float(hc.get("len") or 0) or 5.0
            ins = []
            for q, pid, pos, d, ln in pegs:
                if q is h: continue
                if abs(abs(float(np.dot(d, hd))) - 1) > 0.02: continue
                w = pos - hp; t0 = float(np.dot(w, hd)); lt = np.linalg.norm(w - t0 * hd)
                if lt > lat: continue
                t1 = t0 + float(np.dot(d, hd)) * ln; a, b = sorted((t0, t1))
                if q.n not in _SHAFTY and min(b, hl) - max(a, -hl) > ov: ins.append((q, pid))   # 축·모터 돌기는 구멍 안 축 결합이 정상이라 뺀다
            if len({id(q) for q, _ in ins}) >= 2:
                mine = sorted({cur[id(q)] for q, _ in ins if id(q) in cur})
                if not mine: continue
                key = (id(h), hc["id"])
                if key in seen: continue
                seen.add(key)
                out.append((mine, "%s %s 구멍에 %s 돌기가 이미 들어 있는데 또 결합함(막힌 구멍)" % (h.n, hc["id"], " + ".join("%s.%s" % (q.n, pid) for q, pid in ins))))
    return out

def _mate_pairs(A, k, lat=1.5, ov=0.5):
    """k번 화면(최종 자세)에서 돌기가 다른 부품의 구멍 안에 들어가 결합된 쌍들 {frozenset({id(돌기 부품), id(구멍 부품)})} 와 id → 부품. occupied_holes 와 같은 기준."""
    import stepchecks
    allp = [q for j in range(1, k + 1) for q in A.steps[j - 1].parts if q.conn and not _hidden_at(q, k)]
    pose = {id(q): stepchecks.pose_at(A, q, k) for q in allp}
    def wr(q, c):
        p, R = pose[id(q)]; return p + R @ np.array(c["pos"], float), R @ np.array(c["dir"], float)
    holes = []
    for h in allp:
        for hc in h.conn.get("holes", []):
            hp, hd = wr(h, hc); holes.append((h, hp, hd / (np.linalg.norm(hd) or 1.0), float(hc.get("len") or 0) or 5.0))
    pairs = set()
    for q in allp:
        for c in q.conn.get("pegs", []):
            ln = float(c.get("len") or 0)
            if ln <= 0: continue
            pos, d = wr(q, c); d = d / (np.linalg.norm(d) or 1.0)
            for h, hp, hd, hl in holes:
                if h is q or abs(abs(float(np.dot(d, hd))) - 1) > 0.02: continue
                w = pos - hp; t0 = float(np.dot(w, hd))
                if abs(t0) > ln + hl + 1 or float(np.linalg.norm(w - t0 * hd)) > lat: continue
                t1 = t0 + float(np.dot(d, hd)) * ln; a, b = sorted((t0, t1))
                if min(b, hl) - max(a, -hl) > ov: pairs.add(frozenset((id(q), id(h))))
    return pairs, {id(q): q for q in allp}

def split_bad(A):
    """결합이 된 것인데 다른 곳으로 이동(합치기)할 때 분리되는 것(사용자 지시 2026-11-10: 10번에서 합쳐진 축이 11번 합치기에서 유닛과 따로 내려와 있었다). [(번호, 부품 키 목록, 설명)]
    ① 제자리(seated)로 그려지는 부품이 move 로 옮겨 붙는 번호인데 moveGuide·noGuide 가 없어 묶음과 같이 안 뜨는 것(화면 코드: seated 분기가 먼저 걸려 제자리에 남는다)
    ② 앞 번호(k−1)에서 돌기↔구멍으로 결합돼 있던 두 부품이, 이동(move)이 있는 k번에서 결합이 풀린 것(한쪽만 옮겨짐)."""
    out = []
    for q in A.parts:
        ex = q.extra or {}
        if ex.get("seated") and "move" in ex and not (ex.get("moveGuide") or ex.get("noGuide")):
            at = int(ex["move"]["at"]); si = q.step.index; pi = A.steps[si - 1].parts.index(q)
            out.append((at, ["%d:%d" % (si, pi)], "%s(%d번)는 제자리(seated)라 %d번 합치기 이동에서 묶음과 같이 안 뜨고 따로 남음 — moveGuide·noGuide 를 켠다" % (q.n, si, at)))
    moved_at = {}
    for q in A.parts:
        mv = (q.extra or {}).get("moves") or ([q.extra["move"]] if "move" in (q.extra or {}) else [])
        for m in mv: moved_at.setdefault(int(m["at"]), set()).add(id(q))
    for k in sorted(moved_at):
        if k < 2: continue
        try:
            prev, _ = _mate_pairs(A, k - 1); now, byid = _mate_pairs(A, k)
        except Exception: continue   # 옛 형식 조립도는 자세를 못 구하면 건너뛴다
        for pr in sorted(prev - now, key=lambda s: sorted(map(str, s))):
            ids = list(pr)
            if not all(i in byid for i in ids): continue
            if not any(i in moved_at[k] for i in ids): continue   # 둘 다 안 움직였으면 이 번호 때문이 아니다
            a, b = byid[ids[0]], byid[ids[1]]
            keys = ["%d:%d" % (x.step.index, A.steps[x.step.index - 1].parts.index(x)) for x in (a, b)]
            out.append((k, keys, "%s(%d번)와 %s(%d번)는 %d번에 결합돼 있었는데 %d번 이동으로 떨어짐 — 같이 옮겨야 한다" % (a.n, a.step.index, b.n, b.step.index, k - 1, k)))
    return out

def move_hover_bad(A):
    """앞 번호(k−1)에서 결합돼 있던 부품들이 이동(move)하는 k번에 서로 다른 거리·방향으로 떠서 오면 결합이 풀려 보인다 — [(번호, 부품 키 목록, 설명)]
    (사용자 지적 2026-11-14 배틀로봇 15번: 오른쪽 옆판 3단블록만 noGuide 라 move 에 hover 가 없으면 자기 hover 40 으로 떠 판·프레임에서 떨어졌다).
    화면(design-assembly.js 이동 띄움)과 같은 규칙: 띄움 = move.hover, 없으면 noGuide 부품은 자기 hover, 그것도 없으면 22. 방향 = move.dir."""
    out = []; moved = {}
    for q in A.parts:
        ex = q.extra or {}
        for m in (ex.get("moves") or ([ex["move"]] if "move" in ex else [])):
            if m.get("dir"): moved.setdefault(int(m["at"]), {})[id(q)] = (q, m)
    def off(q, m):
        ex = q.extra or {}; u = np.array(m["dir"], float); u = u / (np.linalg.norm(u) or 1.0)
        hv = m.get("hover") or (ex.get("hover") if ex.get("noGuide") else None) or 22
        return u * float(hv), float(hv)
    for k in sorted(moved):
        if k < 2: continue
        try: prev, _ = _mate_pairs(A, k - 1)
        except Exception: continue
        for pr in sorted(prev, key=lambda s: sorted(map(str, s))):
            ids = list(pr)
            if not all(i in moved[k] for i in ids): continue
            (a, ma), (b, mb) = moved[k][ids[0]], moved[k][ids[1]]
            (oa, ha), (ob, hb) = off(a, ma), off(b, mb)
            if float(np.linalg.norm(oa - ob)) > 0.5:
                keys = ["%d:%d" % (x.step.index, A.steps[x.step.index - 1].parts.index(x)) for x in (a, b)]
                out.append((k, keys, "%s(%d번)와 %s(%d번)는 %d번에 결합돼 있었는데 %d번 이동에서 띄우는 거리가 %g·%g 로 달라 떨어져 보임 — move 에 hover 를 같게 적는다" % (a.n, a.step.index, b.n, b.step.index, k - 1, k, ha, hb)))
    return out

def group_broken(A):
    """기록된 그룹(extra["moveGroup"] 같은 이름)이 풀리면 올린다 — [(번호, 부품 키 목록, 설명)] (사용자 지시 2026-11-14: 그룹이 된 것은 기록하고, 분리되면 경고).
    ① 같은 그룹이 이동하는 번호에 띄우는 거리·방향이 부품마다 다르다(한쪽만 떨어져 보인다)
    ② 이동 전후 그룹 안 부품끼리의 상대 자세(위치·회전)가 바뀐다(모양이 흐트러졌다)
    ③ 그룹의 일부만 따로 이동하는 번호가 있다(나머지는 그대로)"""
    import stepchecks
    out = []; groups = {}
    for q in A.parts:
        g = (q.extra or {}).get("moveGroup")
        if isinstance(g, str) and g: groups.setdefault(g, []).append(q)
    key = lambda x: "%d:%d" % (x.step.index, A.steps[x.step.index - 1].parts.index(x))
    for g, ms in groups.items():
        if len(ms) < 2: continue
        ev = {}   # 부품 → 이동 번호 집합
        for q in ms: ev[id(q)] = {int(m["at"]) for m in ((q.extra.get("moves")) or ([q.extra["move"]] if "move" in q.extra else []))}
        allk = set().union(*ev.values())
        for k in sorted(allk):
            part = [q for q in ms if k in ev[id(q)]]; rest = [q for q in ms if k not in ev[id(q)]]
            if rest:   # ③
                out.append((k, [key(x) for x in ms], "그룹 '%s'의 %s 만 %d번에 따로 움직임 — %s 는 그대로라 결합이 풀림" % (g, "·".join(sorted({x.n for x in part})), k, "·".join(sorted({x.n for x in rest})))))
                continue
            offs = {}
            for q in part:   # ① 화면 규칙과 같은 띄움(move.hover → noGuide 면 자기 hover → 22)
                m = [m for m in ((q.extra.get("moves")) or [q.extra["move"]]) if int(m["at"]) == k][0]
                if not m.get("dir"): continue
                u = np.array(m["dir"], float); u = u / (np.linalg.norm(u) or 1.0)
                hv = float(m.get("hover") or (q.extra.get("hover") if q.extra.get("noGuide") else None) or 22); offs[id(q)] = (u * hv, hv, q)
            vs = list(offs.values())
            if vs and any(float(np.linalg.norm(v[0] - vs[0][0])) > 0.5 for v in vs[1:]):
                out.append((k, [key(v[2]) for v in vs], "그룹 '%s'가 %d번에 부품마다 띄우는 거리가 %s 로 달라 떨어져 보임 — move 에 hover 를 같게 적는다" % (g, k, "·".join("%s %g" % (v[2].n, v[1]) for v in vs))))
            try:   # ②
                a, b = part[0], None
                pa0, Ra0 = stepchecks.pose_at(A, a, k - 1); pa1, Ra1 = stepchecks.pose_at(A, a, k)
                for b in part[1:]:
                    pb0, Rb0 = stepchecks.pose_at(A, b, k - 1); pb1, Rb1 = stepchecks.pose_at(A, b, k)
                    d0 = Ra0.T @ (pb0 - pa0); d1 = Ra1.T @ (pb1 - pa1); r0 = Ra0.T @ Rb0; r1 = Ra1.T @ Rb1
                    if float(np.linalg.norm(d0 - d1)) > 0.5 or float(np.abs(r0 - r1).max()) > 0.01:
                        out.append((k, [key(a), key(b)], "그룹 '%s'의 %s·%s 가 %d번 이동 뒤 서로의 자리·방향이 달라져 결합이 풀림" % (g, a.n, b.n, k)))
            except Exception: pass
        # ④ 그룹은 새 결합으로 커질 뿐 풀리지 않는다(사용자 지시 2026-11-14: 또 결합이 되면 그룹이 수정) — 이동 번호부터 끝 번호까지 매 번호,
        #    그룹 부품이 모두 한 결합 덩어리(돌기↔구멍으로 이어진 연결 성분) 안에 있어야 한다. 덩어리가 커지는 것은 정상, 그룹 부품이 덩어리에서 떨어지면 풀림.
        k0 = min(allk) if allk else 0; seen = False
        for k in range(k0, len(A.steps) + 1):
            if k < 2: continue
            vis = [q for q in ms if q.step.index <= k and not _hidden_at(q, k)]
            if len(vis) < 2: continue
            try: pairs, byid = _mate_pairs(A, k)
            except Exception: break
            par = {}
            def find(x):
                while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
                return x
            for pr in pairs:
                i, j = list(pr); par[find(i)] = find(j)
            roots = {}
            for q in vis: roots.setdefault(find(id(q)), []).append(q)
            if len(roots) > 1:
                parts_ = sorted(roots.values(), key=len)
                out.append((k, [key(x) for x in ms], "그룹 '%s'이 %d번에 풀림 — %s 가 나머지(%s)와 결합이 끊어짐" % (g, k, "·".join(sorted({x.n for x in parts_[0]})), "·".join(sorted({x.n for x in parts_[-1]})))))
                break   # 한 번 풀리면 뒤 번호는 같은 경고를 반복하지 않는다
    return out

def collect(name):
    import asmlib, guidecheck
    A = _load(name); out = {}
    def add(k, type_, keys, msg):
        out.setdefault(str(k), []).append({"type": type_, "keys": sorted(set(keys)), "msg": msg[:120]})
    fl = {}
    for k, nm, y, where, key in asmlib.floor_check(A, keys=True): fl.setdefault((k, where), []).append((nm, y, key))
    for (k, where), v in fl.items():
        add(k, "floor", [x[2] for x in v], "%s %d개 가장 낮은 y %.1f (%s)" % ("·".join(sorted({x[0].rsplit(" ", 1)[0] for x in v})), len(v), min(x[1] for x in v), where))
    try:   # 창고: 다른 창고에 있는 부품이 이 번호 화면에 보이면 그 부품을 붉게 칠한다(2026-11-08 풍차 18번 날개 4개 사고)
        import hidecheck, json as _j
        for k, m, pis in hidecheck.stray_loc(_j.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"]):
            add(k, "store", ["%d:%d" % (m, pi) for pi in pis], "%d번의 부품 %d개가 다른 창고에 있는데 보임(hideMade 에 없음)" % (m, len(pis)))
    except Exception as e_:
        print("violations: 창고 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    bad, _n, _sk = guidecheck.run(name)
    for k, msg in bad:
        nm = re.match(r"(\S+?)(?:\(옮김\))?\s", msg + " ")
        keys = []
        if nm:
            mm = (A.steps[k - 1].kw.get("moveMade") or {})
            for key in mm:
                si, pi = (int(x) for x in key.split(":"))
                if A.steps[si - 1].parts[pi].n == nm.group(1) and mm[key].get("marks"): keys.append(key)
            if not keys:
                keys = ["%d:%d" % (k, i) for i, p in enumerate(A.steps[k - 1].parts) if p.n == nm.group(1)]
        _mark = re.search(r"자기 구멍|자기 자리가 아니다|구멍 축 위에 없|돌기 끝에서 .{0,12}떨어|recv 표시가 없|돌기 끝에 찍힌", msg)   # 안내점·링·화살표 끝이 부품 자기 연결점(구멍·돌기)에 안 맞는 것은 따로 칠한다(2026-11-08)
        add(k, "mark" if _mark else "link", keys, msg)
    try:   # 겹침·틈·방향: cubo_joint_check 가 메시지와 함께 화면 부품 키를 내준다(LAST) — 틈·피치는 ↔, 방향은 ↻, 물리적 겹침은 ✕, 결합 규칙 위반(규칙1·4·5~7·16)은 ⧉
        import cubo_joint_check as cj
        for k in range(1, len(A.steps) + 1):
            for msg in cj.check(A, k):
                t = "orient" if msg.startswith("규칙10") else "gap" if re.search(r"틈|피치", msg) else "overlap" if "겹침" in msg else "bond"   # 겹침 = 부품이 물리적으로 교집합일 때만(사용자 지시 2026-11-14) — 규칙1·4·5~7·16 은 결합 규칙 위반(bond)
                add(k, t, cj.LAST.get(msg, []), msg)
    except Exception as e_:
        print("violations: 겹침·틈·방향 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 몸통 겹침(node check_local.js 의 '겹침 k.i 이름 <> k.i 이름'): 부품이 서로 뚫고 들어간 것 — 터미널 숫자로만 끝나던 것을 화면 ✕ 로 보이게(사용자 지적 2026-11-08 로봇팽이 15번 큰기어가 판을 뚫음)
        import subprocess, json as _j
        _ap = str(asmpath.resolve(name + "_asm.json")); _st = _j.load(open(_ap, encoding="utf-8"))["steps"]
        _o = subprocess.run(["node", "check_local.js", _ap], capture_output=True, text=True, encoding="utf-8", cwd=HERE).stdout
        def _at(k_, i_):   # 그 부품이 마지막으로 놓이거나 옮겨지는 번호
            key_ = "%d:%d" % (k_, i_); return max([k_] + [n_ + 1 for n_, s_ in enumerate(_st) if key_ in (s_.get("moveMade") or {})])
        for m_ in re.finditer(r"겹침\s+(\d+)\.(\d+)\s+(\S+)\s+<>\s+(\d+)\.(\d+)\s+(\S+)", _o):
            ka, ia, na, kb, ib, nb = int(m_.group(1)), int(m_.group(2)), m_.group(3), int(m_.group(4)), int(m_.group(5)), m_.group(6)
            gear = ("기어" in na) or ("기어" in nb)
            _kk = max(_at(ka, ia), _at(kb, ib))
            # 그 번호 화면에서 창고에 보관 중(hideAt)인 부품은 안 보이는 부품이라 겹침으로 세지 않는다(배틀로봇 5번: 보관 중인 315프레임이 다른 창고의 135도 프레임과 겹친다고 나왔다, 2026-11-13)
            if _hidden_at(A.steps[ka - 1].parts[ia], _kk) or _hidden_at(A.steps[kb - 1].parts[ib], _kk): continue
            add(_kk, "overlap", ["%d:%d" % (ka, ia), "%d:%d" % (kb, ib)], "%s ↔ %s 몸통이 겹침(뚫고 들어감)%s" % (na, nb, " — 기어는 상자 근사라 모서리 오탐일 수 있음, 중심 거리로 확인" if gear else ""))
    except Exception as e_:
        print("violations: 몸통 겹침을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 중심: 번호를 끝낸 모습(그 번호 화면에 보이는 부품 전체)의 x·z 범위 중심이 원점(화면 가운데)에서 CENTER_TOL 넘게 벗어나면 ⊕ (사용자 지시 2026-11-09, A4)
        import json as _j, asmlib as _al
        _st = _j.load(open(str(asmpath.resolve(name + "_asm.json")), encoding="utf-8"))["steps"]
        _pub = os.path.join(HERE, "..", "..", "public")
        _auto = ("fitCenter()" in open(os.path.join(_pub, "design.html"), encoding="utf-8").read()
                 and "b.fitCenter()" in open(os.path.join(_pub, "design-assembly.js"), encoding="utf-8").read())   # 뷰어가 번호를 열 때마다 보이는 부품 상자 가운데로 카메라를 자동으로 맞춘다(상시) — 연결돼 있으면 원점에서 벗어나도 화면 가운데다(사용자 지시 2026-11-09)
        for k in range(1, len(_st) + 1):   # 카메라 자동 맞춤(fitCenter)이 있어도 저장된 📷 카메라가 덮어쓰므로 부품 자리 자체를 항상 본다(사용자 지시 2026-11-12, 비행기 꼬리 23~28번)
            hide = {int(x) for x in (_st[k - 1].get("hideMade") or {}) if str(x).isdigit()}
            lo = np.array([1e9, 1e9]); hi = np.array([-1e9, -1e9]); mine = []
            for j in range(1, k + 1):
                if j in hide or _st[j - 1].get("slot", 1) != _st[k - 1].get("slot", 1): continue
                for i, pt in enumerate(A.steps[j - 1].parts):
                    _ha = (pt.extra or {}).get("hideAt")
                    if _ha and (k in [int(x) for x in _ha] if isinstance(_ha, (list, tuple, set)) else int(_ha) <= k): continue   # hideAt 은 숨길 번호 목록(한 개면 그 번호부터)
                    sz = (pt.conn or {}).get("size")
                    if not sz: continue
                    pose = pt._base if getattr(pt, "_base", None) else (pt.p, pt.R)   # 나중에 옮겨진 부품은 처음 놓인 자세부터(move·moves 가 번호별로 덮는다)
                    mv = [m for m in ((pt.extra or {}).get("moves") or ([pt.extra["move"]] if "move" in (pt.extra or {}) else [])) if int(m["at"]) <= k]
                    if mv: m = max(mv, key=lambda q: int(q["at"])); pose = (m["p"], _al.euler_to_R(m["r"]))
                    sd = (pt.extra or {}).get("side")
                    if sd and k < int(sd.get("until") or 0): pose = (sd["p"], _al.euler_to_R(sd["r"]))   # 옆자리에서 따로 조립하는 번호(합쳐지는 번호 전)는 화면이 그리는 옆자리 자세로 잰다
                    h = np.abs(np.array(pose[1], float)) @ (np.array(sz, float) / 2); c = np.array(pose[0], float)
                    lo = np.minimum(lo, [c[0] - h[0], c[2] - h[2]]); hi = np.maximum(hi, [c[0] + h[0], c[2] + h[2]])
                    if j == k: mine.append("%d:%d" % (j, i))
            if hi[0] < lo[0]: continue
            cx, cz = (lo + hi) / 2
            if max(abs(cx), abs(cz)) > CENTER_TOL: add(k, "center", mine, "완성 모습 x·z 중심이 원점에서 x %+.0f·z %+.0f mm 벗어남(허용 ±%d) — 화면 가운데에 오게 놓는다" % (cx, cz, CENTER_TOL))
    except Exception as e_:
        print("violations: 중심 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 카메라: 그 번호의 맞춘 격자(fits/NN_*.json)가 있는데 카메라가 짐작(guess)이면 ◉ — 맞춘 값을 안 쓴 것(사용자 지시 2026-11-09: 반복 확인은 상시 감시로)
        import glob as _g
        A.apply_axes_cams(A.id.split('-', 2)[-1])   # 빌드(export_steps)와 같은 자동 적용을 먼저 해서, 정말 못 쓴 번호만 걸린다
        for k in range(1, len(A.steps) + 1):
            _cs = getattr(A.steps[k - 1], "camSrc", None)
            if _cs == "eye":   # 오차가 커서 자동 적용(apply_axes_cams)이 안 되는 번호라도, 코드 카메라가 축 파일(NN_axes.json)의 theta·phi 와 같으면 맞춘 값을 쓴 것이다
                try:
                    _ax = json.load(open(os.path.join(HERE, "refs", name, "%02d_axes.json" % k), encoding="utf-8")).get("fit") or {}; _cm = A.steps[k - 1].cam or ()
                    if _ax.get("roll") is not None and abs(float(_ax["roll"])) > 8: continue   # 롤이 커서(뷰어 카메라로 같은 그림이 안 나오는) 번호는 책과 비슷한 방위로 고른 눈 카메라를 인정한다(E11)
                    if _ax.get("theta") is not None and len(_cm) >= 2 and abs(float(_cm[0]) - float(_ax["theta"])) < 0.015 and abs(float(_cm[1]) - float(_ax["phi"])) < 0.015: continue
                except Exception: pass
            if _cs != "fit" and _g.glob(os.path.join(HERE, "refs", name, "fits", "%02d_*.json" % k)):
                add(k, "cam", [], "책 그림으로 맞춘 격자(fits)가 있는데 카메라가 짐작값이다 — axes_fit 결과 theta·phi 를 쓴다")
    except Exception as e_:
        print("violations: 카메라 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 손값 경고(사용자 지시 2026-11-08): 조립도 .py 에 손으로 적은 hover=숫자·marks=[[…]]·offset=[…] 는 부품 자리에서 계산된 값이 아니다 → 그 번호·부품을 ✋ 로 경고한다(막지는 않는다)
        _src = open(str(asmpath.resolve(name + ".py")), encoding="utf-8").read()
        for ln in _src.splitlines():
            m_ = re.match(r"\s*(v\d+_\d+)\s*=\s*s(\d+)\.\w+\(\s*'([^']+)'", ln)
            if not m_: continue
            code = ln.split("   #")[0]
            hv = []; mk = re.search(r"\b(marks|settleMarks|faceMarks|offset)=\[\[?-?[0-9]", code)   # 연결점(부품 리스트)이 아닌 숫자는 전부 경고
            if not (hv or mk): continue
            k = int(m_.group(2)); keys = ["%d:%d" % (k, i) for i, p in enumerate(A.steps[k - 1].parts) if p.n == m_.group(3)]
            what = ", ".join(["%s=%s" % h for h in hv] + (["%s 숫자 직접 입력" % mk.group(1)] if mk else []))
            if any(x["type"] == "hand" and x["msg"].startswith(m_.group(3)) for x in out.get(str(k), [])): continue   # 같은 번호에 같은 부품 이름이 여러 줄이면 한 번만
            add(k, "hand", keys, "%s 연결점이 아닌 숫자를 씀(%s) — 부품 리스트의 구멍·돌기 연결점에서 계산해야 한다" % (m_.group(3), what))
    except Exception as e_:
        print("violations: 손값 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 상시 감시로 옮긴 번호별 점검(사용자 지시 2026-11-09): 리벳 틈·볼트 머리/너트 돌출·부시 방향 — stepchecks 가 계산한 값을 그대로 화면 종류로 올린다(새 계산 없음). 볼트·너트 결합·메인보드는 조립도별 켜는 검사라 뺀다
        import stepchecks as sc
        for k in range(1, len(A.steps) + 1):
            st = A.steps[k - 1]
            ks = lambda nm: ["%d:%d" % (k, i) for i, p in enumerate(st.parts) if p.n == nm]
            if any(p.n == "리벳" for p in st.parts):
                for rn, a_, b_, g_ in sc.rivet_gaps(A, k): add(k, "gap", ks(rn) + ks(a_) + ks(b_), "리벳 %s↔%s 틈 %.1fmm (+떠 있음 −겹침)" % (a_, b_, g_))
            if any(p.n in ("8볼트", "12볼트", "너트", "서보고정볼트") for p in st.parts):
                for bn, fr, pr in sc.fastener_protrusion(A, k): add(k, "protrude", ks(bn), "%s 가 %s 면 밖으로 %.1fmm 나옴" % (bn, fr, pr))
            if any(p.n == "부시" for p in st.parts):
                bw = sc.bush_wrong(A, k)
                if bw: add(k, "orient", ["%d:%d" % (k, i) for i in bw], "부시 넓은 쪽이 판에 닿음 — 좁은 쪽(모델 +y)이 판 쪽이어야 한다")
    except Exception as e_:
        print("violations: stepchecks 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 축 위치: 축(·T축)에 끼운 부품은 최종 자리에서 내 구멍 중심이 축 중심선 위(≤1.5mm)이고 축 길이 안에 있어야 한다(사용자 지시 2026-11-09: 축과 위치가 안 맞으면 모니터링)
        for k, q_idx, msg in axle_bad(A):
            add(k, "axle", ["%d:%d" % (k, q_idx)], msg)
    except Exception as e_:
        print("violations: 축 위치 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 구멍 없는 곳(사용자 지시 2026-11-10): 긴 막대(T축·축)가 지나는 부품에 그 자리 구멍이 없으면 올린다
        for k, q_idx, msg in nohole_bad(A):
            add(k, "nohole", ["%d:%d" % (k, q_idx)], msg)
    except Exception as e_:
        print("violations: 구멍 없는 곳 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 가짜 안내점(G1a): 받는 부품(recv)인데 dir 만 있고 marks 가 비며 noGuide 도 아니면 부품 중심에서 허공 화살표가 나간다 — fakeguide_check.py 와 같은 조건(사용자 지시 2026-11-09: 상시 감시로)
        import json as _j2
        for k_, s_ in enumerate(_j2.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"], 1):
            for i_, p_ in enumerate(s_.get("parts", [])):
                if p_.get("recv") and p_.get("dir") and not p_.get("marks") and not p_.get("noGuide"):
                    add(k_, "fake", ["%d:%d" % (k_, i_)], "%s 가짜 안내점 — 안내점(marks)이 비어 부품 중심에서 허공 화살표가 나감(`extra.pop('dir')` 또는 settleMarks)" % p_["n"])
    except Exception as e_:
        print("violations: 가짜 안내점 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 막힌 구멍(사용자 지시 2026-11-09): 이미 돌기·리벳이 들어 있는 프레임 구멍에 또 결합하는 번호를 ⛔ 로 올린다
        for k in range(1, len(A.steps) + 1):
            for mine, msg in occupied_holes(A, k): add(k, "occupied", ["%d:%d" % (k, i) for i in mine], msg)
    except Exception as e_:
        print("violations: 막힌 구멍 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 분리(사용자 지시 2026-11-10): 결합된 부품이 합치기 이동에서 따로 남거나 떨어지면 ⛓ 로 올린다
        for k, keys, msg in split_bad(A) + move_hover_bad(A) + group_broken(A): add(k, "split", keys, msg)
    except Exception as e_:
        print("violations: 분리 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    return out

def write_entry(name):
    """모은 위반을 항목 파일(<이름>_entry.js)의 def.violations 로 쓴다(번호 지문에 안 들어간다). 바뀐 것이 없으면 쓰지 않는다. -> (위반 번호 수, 종류들, 바뀜 여부)"""
    import json
    vd = collect(name); ef = os.path.join(os.path.dirname(asmpath.resolve(name + "_entry.js")), name + "_entry.js") if False else asmpath.resolve(name + "_entry.js")
    old = open(ef, encoding="utf-8").read()
    new = re.sub(r"      violations: .*\n", "", old)
    if vd: new = new.replace("      steps: [", "      violations: %s,\n      steps: [" % json.dumps(vd, ensure_ascii=False), 1)
    if new != old: open(ef, "w", encoding="utf-8").write(new)
    return len(vd), sorted({v["type"] for l_ in vd.values() for v in l_}), new != old

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--write" in sys.argv:   # 화면 데이터에 위반만 반영한다(빌드가 경고로 막혀도 화면에서 위반을 보기 위해): 항목 파일에 쓰고 emit.py 로 화면 파일을 갱신
        import subprocess, json as _j
        n_, ts_, ch_ = write_entry(sys.argv[1]); ef_ = asmpath.resolve(sys.argv[1] + "_entry.js")
        m_ = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(ef_, encoding="utf-8").read())
        r_ = subprocess.run([sys.executable, "emit.py", ef_ if False else sys.argv[1] + "_entry.js", m_.group(1) if m_ else "cubo-1-" + sys.argv[1]], capture_output=True, text=True, encoding="utf-8")
        print("위반 표시 반영: %d번 (%s)" % (n_, ", ".join(ts_) or "없음"), "· 항목 파일 바뀜" if ch_ else "· 변화 없음"); print((r_.stdout or r_.stderr).strip()[-200:]); sys.exit(0)
    r = collect(sys.argv[1])
    for k in sorted(r, key=int):
        for v in r[k]: print("%s번 %s %s 부품 %d개 — %s" % (k, v["type"], "", len(v["keys"]), v["msg"]))
    print("위반 번호 %d개" % len(r))
