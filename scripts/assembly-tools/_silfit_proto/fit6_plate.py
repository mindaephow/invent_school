# 6번 판 카메라: 모서리 호모그래피 → 구멍 흰 조각(밝기 130) 순방향 투영 매칭 반복 → 가장 많이 맞는 카메라 (스티어카 2026-10-31)
import sys, math, json
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
im = cv2.imread("C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/06.jpg"); Hh, Ww = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
C = np.array([947.7, 272.1, 419.9, 481.0, 323.2, 365.6, 818.3, 187.9], np.float32).reshape(4, 2)
ins = np.zeros(g.shape, np.uint8); cv2.fillPoly(ins, [C.astype(np.int32).reshape(-1, 1, 2)], 1); ie = cv2.erode(ins, np.ones((7, 7), np.uint8))
excl = np.array([[238, 288], [268, 281], [590, 640], [550, 652]], np.int32); ex = np.zeros(g.shape, np.uint8); cv2.fillPoly(ex, [excl], 1)
THR = int(sys.argv[1]) if len(sys.argv) > 1 else 130
m = ((g > THR) & (ie > 0) & (ex == 0)).astype(np.uint8) * 255; n, lab, st, cen = cv2.connectedComponentsWithStats(m)
S = np.array([cen[i] for i in range(1, n) if 15 < st[i][4] < 700 and .3 < st[i][2] / max(1, st[i][3]) < 3.8], float)
print("흰 조각", len(S))
cols, rows = 15, 5
P3 = lambda c, r, y: [(c - 8) * 10.0, y, (r - 3) * 10.0]
cells = [(c, r) for c in range(1, cols + 1) for r in range(1, rows + 1)]
cornw = [P3(0.5, 0.5, 5), P3(15.5, 0.5, 5), P3(15.5, 5.5, 5), P3(0.5, 5.5, 5)]
best = []
for fov in range(10, 46, 2):
    r0 = fit(cornw, C, Ww, Hh, fov)
    if not r0: continue
    _, _, rv, tv = (None, None, r0[2], r0[3]) if len(r0) == 4 and False else (None, None, r0[1], r0[2]) if False else (None, None, None, None)
    # fit 는 (오차, rv, tv, K) 순으로 돌려준다
    e, rv, tv, K = r0
    for it in range(14):
        pr = cv2.projectPoints(np.array([P3(c, r, 2.5) for c, r in cells], np.float64), np.asarray(rv, np.float64), np.asarray(tv, np.float64), np.asarray(K, np.float64), None)[0].reshape(-1, 2)
        pitch = np.mean(np.hypot(*(pr[1:] - pr[:-1]).T)) * 0.0 + np.median([np.hypot(*(pr[i + rows] - pr[i])) for i in range(len(pr) - rows)])
        tol = max(0.25, 0.5 - 0.04 * it) * pitch; pairs = {}; used = set()
        for i, (c, r) in enumerate(cells):
            d = np.hypot(*(S - pr[i]).T); k = int(np.argmin(d))
            if d[k] < tol and k not in used: pairs[i] = k; used.add(k)
        if len(pairs) < 8: break
        obj = [P3(*cells[i], 2.5) for i in pairs]; img = [S[k] for k in pairs.values()]
        rr = fit(obj, img, Ww, Hh, fov)
        if not rr: break
        e, rv, tv, K = rr
    pr = cv2.projectPoints(np.array([P3(c, r, 2.5) for c, r in cells], np.float64), np.asarray(rv, np.float64), np.asarray(tv, np.float64), np.asarray(K, np.float64), None)[0].reshape(-1, 2)
    d2 = [float(np.min(np.hypot(*(S - p).T))) for p in pr]; ok = [x for x in d2 if x < 3.0]
    best.append((len(ok), float(np.mean(ok)) if ok else 9, fov, rv, tv, K))
best.sort(key=lambda b: (-b[0], b[1]))
for b in best[:5]: print("fov", b[2], "맞은 칸", b[0], "평균", round(b[1], 2))
b = best[0]; np.save("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/p6_cam.npy", np.concatenate([np.ravel(b[3]), np.ravel(b[4]), [b[2]]]))
