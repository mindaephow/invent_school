# 투석기 팔을 T축(z 방향 선)을 기준으로 당길 때(−각도) 처음 부딪히는 각도를 구한다 — 팔 묶음 부품 상자(OBB)와 나머지 부품 상자의 겹침(SAT) 검사.
import numpy as np
def obb(pt):
    size = (pt.conn or {}).get("size")
    if not size: return None
    return np.array(pt.p, float), np.array(pt.R, float), np.array(size, float) / 2.0
def rotz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def overlap(A, B, shrink=0.6):
    ca, Ra, ha = A; cb, Rb, hb = B; ha = ha - shrink; hb = hb - shrink
    d = cb - ca
    axes = [Ra[:, i] for i in range(3)] + [Rb[:, i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            x = np.cross(Ra[:, i], Rb[:, j]); n = np.linalg.norm(x)
            if n > 1e-9: axes.append(x / n)
    for ax in axes:
        ra = sum(ha[i] * abs(np.dot(Ra[:, i], ax)) for i in range(3)); rb = sum(hb[i] * abs(np.dot(Rb[:, i], ax)) for i in range(3))
        if abs(np.dot(d, ax)) > ra + rb: return False
    return True
def sweep(group, others, pivot, max_deg=100.0, step=0.5):
    pivot = np.array(pivot, float); G = [(pt, obb(pt)) for pt in group]; G = [(p, b) for p, b in G if b]
    O = [(pt, obb(pt)) for pt in others]; O = [(p, b) for p, b in O if b]
    def rotated(b, a):
        c, R, h = b; Rz_ = rotz(a); return Rz_ @ (c - pivot) + pivot, Rz_ @ R, h
    base = {(id(g), id(o)) for g, bg in G for o, bo in O if overlap(bg, bo)}   # 처음부터 겹쳐 있는 쌍(T축이 팔 구멍을 지나는 것 등)은 무시
    a = 0.0
    while a < np.radians(max_deg):
        a += np.radians(step)
        for g, bg in G:
            rg = rotated(bg, -a)
            for o, bo in O:
                if (id(g), id(o)) in base: continue
                if np.linalg.norm(rg[0] - bo[0]) > np.linalg.norm(rg[2]) + np.linalg.norm(bo[2]) + 2: continue
                if overlap(rg, bo): return float(np.degrees(a)), "%s ↔ %s" % (g.n, o.n)
    return max_deg, "부딪히지 않음"
