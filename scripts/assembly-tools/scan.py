# 모델 스캔 — 바닥에서 위로(높이 스캔), 가운데에서 좌우로(좌우 대칭 스캔) (사용자 지시 2026-10-17: "스캔 = 바닥에서 위로, 좌우 대칭은 가운데에서 좌우로").
#   python scan.py <이름> 높이 [--번호 N] [--간격 1] [--부품 이름…]
#     바닥(y 가장 낮은 곳)에서 위로 간격(mm)마다 그 층을 지나는 부품을 묶어, 같은 구성이 이어지는 높이 구간으로 보여 준다.
#     맨 끝에 부품마다 바닥·윗면 높이 표와, 위아래로 이웃한 부품 사이 틈(mm)을 보여 준다 — 책 그림에서 잰 높이와 비교하는 데 쓴다.
#   python scan.py <이름> 좌우 [--번호 N] [--중심 0] [--간격 1] [--허용 0.5]
#     가운데(x = 중심)에서 바깥으로 간격마다 왼쪽(−d)·오른쪽(+d) 층을 비교한다. 같은 종류 부품이 같은 높이(y)·앞뒤(z) 범위에 있어야 같다.
#     어긋난 거리 구간과 어느 쪽에 무슨 부품이 더 있는지/높이가 얼마나 다른지 적는다. (symcheck.py 는 부품 위치만 쌍으로 비교한다.)
#   --번호 N 이면 1~N번까지 만든 부품만 본다(모델 좌표는 마지막 자세라서 마지막으로 만든 번호만 정확하다).
#   부품은 dims.json 크기의 상자로 본다(구멍·돌기 모양은 보지 않는다).
import json, os, runpy, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))

def opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default

def boxes(name, upto, only):
    g = runpy.run_path(os.path.join(here, name + ".py"), run_name="probe"); A = g["A"]
    dims = json.load(open(os.path.join(here, "dims.json"), encoding="utf-8")); out = []
    for q in A.parts:
        nm = q.name.split(" ")[0]
        if nm not in dims or (upto and q.step.index > upto) or (only and nm not in only): continue
        half = np.abs(np.array(q.R, float)) @ np.array(dims[nm], float) / 2; p = np.array(q.p, float)
        out.append((q.name, nm, p - half, p + half))
    return out

def height_scan(bs, step):
    lo = min(b[2][1] for b in bs); hi = max(b[3][1] for b in bs)
    print("높이 스캔 — 바닥 y %.1f 에서 위 y %.1f 까지 %.1fmm 간격, 부품 %d개" % (lo, hi, step, len(bs)))
    runs = []; y = lo
    while y < hi - 1e-9:
        mid = y + step / 2
        names = sorted(b[1] for b in bs if b[2][1] <= mid < b[3][1] - 1e-9)
        key = tuple(sorted(set((n, names.count(n)) for n in names)))
        if runs and runs[-1][2] == key: runs[-1][1] = y + step
        else: runs.append([y, y + step, key])
        y += step
    for a, b, key in runs:
        print("  y %6.1f ~ %6.1f (%5.1fmm) | %s" % (a, b, b - a, ", ".join("%s %d" % kv for kv in key) or "(비어 있음)"))
    print("\n부품별 바닥·윗면 높이(y) — 위로 이웃한 부품 사이 틈")
    order = sorted(bs, key=lambda b: (b[2][1], b[3][1]))
    for n, nm, mn, mx in order:
        up = [m for m in order if m[2][1] >= mx[1] - 1e-6 and m[1] != nm or (m[2][1] >= mx[1] - 1e-6 and m[0] != n)]
        up = [m for m in up if not (m[3][0] < mn[0] or m[2][0] > mx[0] or m[3][2] < mn[2] or m[2][2] > mx[2])]   # 위에 겹쳐 올라앉을 수 있는(앞뒤·좌우 겹치는) 부품만
        gap = min((m[2][1] - mx[1] for m in up), default=None)
        print("  %-14s 바닥 %6.1f · 윗면 %6.1f%s" % (n, mn[1], mx[1], "" if gap is None else " · 위 부품까지 %.1fmm" % gap))

def sym_scan(bs, center, step, tol):
    xs = max(max(abs(b[2][0] - center), abs(b[3][0] - center)) for b in bs)
    print("좌우 스캔 — 가운데 x=%.1f 에서 바깥으로 %.1fmm 간격, 왼쪽(−)·오른쪽(+) 비교, 허용 %.2fmm" % (center, step, tol))
    def side(d, sgn):
        a, b = center + sgn * d, center + sgn * (d + step); lo, hi = min(a, b), max(a, b); out = []
        for n, nm, mn, mx in bs:
            if mn[0] < hi - 1e-9 and mx[0] > lo + 1e-9: out.append((nm, round(float(mn[1]), 1), round(float(mx[1]), 1), round(float(mn[2]), 1), round(float(mx[2]), 1)))
        return sorted(out)
    bad = []; d = 0.0; same_runs = []
    while d < xs - 1e-9:
        L, Rr = side(d, -1), side(d, +1)
        ok = len(L) == len(Rr) and all(l[0] == r[0] and all(abs(l[i] - r[i]) <= tol for i in range(1, 5)) for l, r in zip(L, Rr))
        if ok:
            if same_runs and same_runs[-1][1] == d: same_runs[-1][1] = d + step
            else: same_runs.append([d, d + step])
        else: bad.append((d, L, Rr))
        d += step
    print("같은 구간(가운데에서 거리): " + (", ".join("%.0f~%.0fmm" % (a, b) for a, b in same_runs) or "없음"))
    if not bad: print("어긋난 구간 없음 — 왼쪽·오른쪽이 가운데 기준으로 끝까지 같다."); return
    print("어긋난 구간 %d개:" % len(bad))
    for d, L, Rr in bad[:30]:
        ls = {(a, b, c, e, f) for a, b, c, e, f in L}; rs = {(a, b, c, e, f) for a, b, c, e, f in Rr}
        print("  거리 %.1f~%.1f : 왼쪽에만 %s / 오른쪽에만 %s" % (d, d + step, sorted(ls - rs)[:4], sorted(rs - ls)[:4]))

def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ("높이", "좌우"): sys.exit(__doc__)
    name, mode = a[0], a[1]
    only = set(a[a.index("--부품") + 1:]) if "--부품" in a else None
    bs = boxes(name, opt(a, "--번호", 0, int), only)
    if not bs: sys.exit("부품이 없다")
    step = opt(a, "--간격", 1.0)
    if mode == "높이": height_scan(bs, step)
    else: sym_scan(bs, opt(a, "--중심", 0.0), step, opt(a, "--허용", 0.5))

if __name__ == "__main__": main()
