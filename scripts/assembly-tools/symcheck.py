# 대칭 조립 찾기·검증 도구(2026-10-13, 사용자 지시 "대부분 대칭형이다 — 대칭 쪽 정보로 유추한다").
#   조립 프로그램(<이름>.py)을 실행(파일은 쓰지 않는다)해 만들어진 부품들의 위치로, 같은 종류 부품이 한 평면에 대해 거울 쌍을 이루는 대칭면을 찾는다.
#   python symcheck.py <이름> [--축 x|z] [--중심 mm] [--허용 1.0] [--빠진것]
#     (옵션 없음)  x·z 두 방향에서 가장 많은 부품이 거울 쌍인 대칭면을 찾아 비율을 보여 준다(y 는 위·아래라 보지 않는다).
#     --축·--중심  대칭면을 알고 있으면(예: 드롭체커 713판 가운데 z 5) 그 면으로 검증한다. 쌍 거리의 중앙값·최대(mm)를 보여 준다 — 거울 위치가 맞으면 0.00.
#     --빠진것     짝이 없는 부품(대칭 쪽이 아직 없거나 어긋난 부품)을 번호 순으로 나열한다 — 반대편에서 이 부품이 놓일 자리가 이 부품의 거울 위치다(유추 근거).
#   읽는 법: 비율 = (거울 쌍을 이룬 부품 + 대칭면 위에 놓인 부품) / 전체. 위치만 비교한다(회전은 비교하지 않는다).
import sys, runpy, os, math
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    name = a[0]; ax_opt = None; c_opt = None; tol = 1.0; show_missing = False; i = 1
    while i < len(a):
        if a[i] == "--축": ax_opt = {"x": 0, "z": 2}[a[i + 1]]; i += 2
        elif a[i] == "--중심": c_opt = float(a[i + 1]); i += 2
        elif a[i] == "--허용": tol = float(a[i + 1]); i += 2
        elif a[i] == "--빠진것": show_missing = True; i += 1
        else: sys.exit("모르는 옵션 " + a[i])
    os.chdir(HERE); sys.path.insert(0, HERE)
    g = runpy.run_path(os.path.join(HERE, name + ".py"), run_name="probe")   # __main__ 이 아니라 파일을 쓰지 않는다
    A = g["A"]
    P = [(q.name.split(" ")[0], np.array(q.p, float), q) for q in A.parts]
    n = len(P)
    if n < 4: sys.exit("부품이 너무 적다(%d)" % n)
    def evaluate(axis, c):
        used = set(); pairs = []; onplane = []
        for i, (nm, p, q) in enumerate(P):
            if abs(p[axis] - c) <= tol: onplane.append(i); continue
            if i in used: continue
            m = p.copy(); m[axis] = 2 * c - p[axis]
            best = None
            for j, (nm2, p2, q2) in enumerate(P):
                if j == i or j in used or nm2 != nm: continue
                d = float(np.linalg.norm(p2 - m))
                if d <= tol and (best is None or d < best[0]): best = (d, j)
            if best: used.add(i); used.add(best[1]); pairs.append((best[0], i, best[1]))
        matched = set(used) | set(onplane)
        return pairs, onplane, matched
    cands = []
    if ax_opt is not None and c_opt is not None: cands = [(ax_opt, c_opt)]
    else:
        axes = (ax_opt,) if ax_opt is not None else (0, 2)
        for axis in axes:
            cs = set()
            for i, (nm, p, q) in enumerate(P):
                for j in range(i + 1, n):
                    if P[j][0] == nm and abs(P[j][1][axis] - p[axis]) > 2 * tol: cs.add(round((p[axis] + P[j][1][axis]) / 2.0 * 2) / 2.0)   # 같은 종류 두 부품의 가운데 = 대칭면 후보
            cands += [(axis, c) for c in cs]
    best = None
    for axis, c in cands:
        pairs, onplane, matched = evaluate(axis, c)
        score = len(matched)
        if best is None or score > best[0]: best = (score, axis, c, pairs, onplane, matched)
    score, axis, c, pairs, onplane, matched = best
    an = "xyz"[axis]
    print("%s: 부품 %d개 — 가장 대칭인 면: %s = %.1f  | 거울 쌍 %d쌍(부품 %d개) + 면 위 %d개 = %d/%d (%.0f%%)" % (name, n, an, c, len(pairs), 2 * len(pairs), len(onplane), len(matched), n, 100.0 * len(matched) / n))
    if pairs:
        ds = np.array([d for d, _, _ in pairs]); print("  쌍 거리: 중앙값 %.2fmm · 평균 %.2fmm · 최대 %.2fmm" % (np.median(ds), ds.mean(), ds.max()))
    if show_missing:
        miss = [(q.step.index, nm, q.name) for i, (nm, p, q) in enumerate(P) if i not in matched]
        print("  짝 없는 부품 %d개:" % len(miss))
        for st, nm, full in sorted(miss)[:60]: print("    %d번 %s" % (st, full))

main()
