# 기울어진 결합 점검·자세 계산 (사용자 지시 2026-11-01 "기울기가 있는 결합을 하는 규칙? 프로그램을 만들어보자", 조향자동차 41번)
#   python tiltjoin.py <이름> <번호>            그 번호에서 기울어진 부품·결합을 모두 찾아 구멍·돌기 축, 거리, 틈을 숫자로 보여 준다
#   python tiltjoin.py R "<로컬벡터>=<세계벡터>" ["<로컬벡터>=<세계벡터>"]
#        부품 자세 R 계산: 예) python tiltjoin.py R "0,1,0=0.7071,0.7071,0"  (로컬 +y 를 세계 n 으로)
# 규칙(큐보 부품결합규칙.md G14): 기울어진 부품의 구멍·돌기 축은 모델 좌표 dir 을 R 로 돌려 세계 방향을 읽는다(부품 한 개의 축만 보고 판단하지 않는다 — 집게 팔은 구멍 축이 Z 였지만
#   판이 붙는 3단블록 관통 구멍은 (0.71,0.71,0) 이었다). 틈·겹침·소속은 obb.py(회전한 상자)로 잰다. 관통 구멍은 앞·뒤 어느 쪽으로도 들어간다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, json, itertools
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import obb

def _vec(s): return np.array([float(x) for x in s.split(",")], float)

def cmd_R(args):
    pairs = {}
    for a in args:
        l, w = a.split("="); pairs[tuple(_vec(l))] = _vec(w)
    R = obb.align_R(pairs)
    print("R =", np.round(R, 4).tolist())
    for l, w in pairs.items(): print("  로컬", [float(x) for x in l], "→ 세계", np.round(R @ np.array(l, float), 4).tolist(), "(요청", np.round(np.array(w) / np.linalg.norm(w), 4).tolist(), ")")

def cmd_step(name, k):
    import importlib, stepchecks
    S = importlib.import_module(name)
    A = S.A
    dims = stepchecks._dims()
    st = A.steps[k - 1]
    tilted = [p for p in st.parts if obb.is_tilted(p.R)]
    print("═══ %s %d번 — 기울어진 부품 %d개 ═══" % (name, k, len(tilted)))
    from asmlib import euler_to_R
    def pose_k(q):   # k번 시점 자세: 옮겨진(moveMade) 마지막 자세, 없으면 놓은 자세 — stepchecks.rivet_gaps 와 같다
        key = "%d:%d" % (q.step.index, q.step.parts.index(q))
        for j in range(k, 0, -1):
            e = (A.steps[j - 1].kw.get("moveMade") or {}).get(key)
            if e: return np.array(e["p"], float), np.array(euler_to_R(e["r"]), float)
        return stepchecks._pose(q, k)
    allp = [(q, *pose_k(q)) for k2, s2 in enumerate(A.steps, 1) if k2 <= k for q in s2.parts if q.n in dims and q.n != "리벳"]
    for p in tilted:
        print("▸ %s 중심 %s" % (p.name, np.round(p.p, 2).tolist()))
        for kind, lst in (("구멍", p.conn["holes"]), ("돌기", p.conn["pegs"])):
            ax = {}
            for c in lst:
                w = p.world("hole" if kind == "구멍" else "peg", c); key = tuple(float(x) for x in np.round(w["dir"], 2)); ax.setdefault(key, []).append(c["id"])
            for key, ids in ax.items(): print("    %s 세계 방향 %s : %s%s" % (kind, key, ",".join(ids[:8]), " …" if len(ids) > 8 else ""))
    # 결합 쌍(리벳): 리벳 양 끝이 든 두 부품 사이 틈을 축 방향으로 회전한 상자로 잰다(stepchecks.rivet_gaps 와 같은 판정)
    print("─ 리벳 결합 틈(축 방향, 회전한 상자) ─")
    for r in st.parts:
        if r.n != "리벳": continue
        pegs = {c["id"]: np.array(c["pos"], float) for c in r.conn["pegs"]}
        rp, rR = pose_k(r); t1, t2 = rp + rR @ pegs["p1"], rp + rR @ pegs["p2"]; ax_ = (t2 - t1) / np.linalg.norm(t2 - t1)
        def host(pt, skip=None):
            for q, qp, qR in allp:
                if q is skip or q is r: continue
                if obb.contains(pt, qp, qR, np.array(dims[q.n]) / 2, 0.01): return q, qp, qR
        h1 = host(t1 - ax_ * 1.0); h2 = host(t2 + ax_ * 1.0, h1[0] if h1 else None)
        if h1 and h2:
            g = obb.gap_along(ax_, (h1[1], h1[2], np.array(dims[h1[0].n]) / 2), (h2[1], h2[2], np.array(dims[h2[0].n]) / 2))
            print("  %s 축 %s : %s ↔ %s 틈 %.2fmm" % (r.name, [float(x) for x in np.round(ax_, 2)], h1[0].name, h2[0].name, g))
        else:
            print("  %s 축 %s : 받는 부품 %d개(한쪽만 든 결합 전 모습이면 정상)" % (r.name, [float(x) for x in np.round(ax_, 2)], int(bool(h1)) + int(bool(h2))))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "R": cmd_R(a[1:])
    else: cmd_step(a[0], int(a[1]))
