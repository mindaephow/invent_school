import sys, json, math
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from scipy.optimize import minimize
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
D = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/"
P3 = lambda c, r, y: [(c - 8) * 10.0, y, (r - 3) * 10.0]
d = json.load(open(D + "fits/03_P.json", encoding="utf-8")); im3 = cv2.imread(D + "03.jpg")
obj = [P3(p[0], p[1], 2.5) for p in d["pts"]]; img = [[p[2], p[3]] for p in d["pts"]]
e, rv3, tv3, K3 = fit(obj, img, im3.shape[1], im3.shape[0], 30.0); print("03 재현 오차", round(float(e), 2))
im = cv2.imread(D + "06.jpg"); Hh, Ww = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
C = np.array([947.7, 272.1, 419.9, 481.0, 323.2, 365.6, 818.3, 187.9], np.float32).reshape(4, 2)
ins = np.zeros(g.shape, np.uint8); cv2.fillPoly(ins, [C.astype(np.int32).reshape(-1, 1, 2)], 1); ie = cv2.erode(ins, np.ones((7, 7), np.uint8))
ex = np.zeros(g.shape, np.uint8); cv2.fillPoly(ex, [np.array([[238, 288], [268, 281], [590, 640], [550, 652]], np.int32)], 1)
m = ((g > 130) & (ie > 0) & (ex == 0)).astype(np.uint8) * 255; n, lab, st, cen = cv2.connectedComponentsWithStats(m)
S = np.array([cen[i] for i in range(1, n) if 15 < st[i][4] < 700 and .3 < st[i][2] / max(1, st[i][3]) < 3.8], float)
cells = [(c, r) for c in range(1, 16) for r in range(1, 6)]; W3 = np.array([P3(c, r, 2.5) for c, r in cells], np.float64)
def proj(x):
    f = (Hh / 2) / math.tan(math.radians(x[4]) / 2); K = np.array([[f, 0, Ww / 2], [0, f, Hh / 2], [0, 0, 1]], float)
    return cv2.projectPoints(W3, np.asarray(rv3, np.float64), np.array(x[:3], np.float64).reshape(3, 1), K, None)[0].reshape(-1, 2)
def loss(x):
    pr = proj(x); d = np.array([np.min(np.hypot(*(S - p).T)) for p in pr]); return float(np.sum(np.minimum(d, 12.0)))
best = None
for fov in (20, 25, 30, 35):
    for dz in (0.8, 1.0, 1.3):
        for sx in (-200, -100, 0, 100, 200):
            for sy in (-100, 0, 100):
                x0 = [tv3[0, 0] + sx * dz * 0.0 + sx * 0.2, tv3[1, 0] + sy * 0.2, tv3[2, 0] * dz, fov]
                r = minimize(lambda y: loss(list(y) + [fov]) if False else loss([y[0], y[1], y[2], 0, y[3]]), x0, method="Nelder-Mead", options={"maxiter": 300, "xatol": 0.05, "fatol": 0.05})
                if best is None or r.fun < best.fun: best = r
x = best.x; pr = proj([x[0], x[1], x[2], 0, x[3]]); dd = np.array([np.min(np.hypot(*(S - p).T)) for p in pr])
print("조각", len(S), "맞은 칸(<3px)", int((dd < 3).sum()), "평균", round(float(dd[dd < 3].mean()), 2), "fov", round(x[3], 1))
np.save("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/p6_rot03.npy", np.concatenate([np.ravel(rv3), x]))
