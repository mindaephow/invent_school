import sys; sys.argv = ['x']
sys.path.insert(0, '_silfit_proto')
import numpy as np, cv2, math
from scipy.optimize import minimize
import silfit6 as S
Hh, Ww, g = S.Hh, S.Ww, S.g
cells = [(c, r) for c in range(1, 16) for r in range(1, 6)]; W = np.array([[(c - 8) * 10.0, 2.5, (r - 3) * 10.0] for c, r in cells])
m = ((g > 130)).astype(np.uint8) * 255; n, lab, st, cen = cv2.connectedComponentsWithStats(m)
B = np.array([cen[i] for i in range(1, n) if 15 < st[i][4] < 700 and .3 < st[i][2] / max(1, st[i][3]) < 3.8])
def holeterm(x):
    rv, tv, fov = S.parts(x); K = S.K_(fov); K = K
    pr = cv2.projectPoints(W, rv, tv, K, None)[0].reshape(-1, 2); ms = S.hull_mask(S.SERVO, rv, tv, K, 9)
    use = []
    for p in pr:
        xi, yi = int(round(p[0])), int(round(p[1]))
        if 0 <= xi < Ww and 0 <= yi < Hh and not S.EXC[yi, xi] and not ms[yi, xi]: use.append(p)
    if len(use) < 10: return 1.0, 0
    d = np.array([np.min(np.hypot(*(B - p).T)) for p in use]); return float(np.mean(np.minimum(d, 10.0)) / 10.0), int((d < 3).sum())
def loss(x):
    l = S.loss(x)
    if l >= 9: return 9.0
    return l + 0.8 * holeterm(x)[0]
x = list(np.load(S.SP + 'sil6_x.npy')); print('시작', round(S.loss(x), 3), holeterm(x))
best = None
for fov in (12.2, 16, 20, 26, 32):
    x0 = list(x); x0[6] = fov
    r = minimize(loss, x0, method='Powell', options={'maxiter': 10, 'xtol': 1e-3, 'ftol': 1e-6}); r = minimize(loss, r.x, method='Powell', options={'maxiter': 10, 'xtol': 1e-3, 'ftol': 1e-6})
    print('fov 시작', fov, '→', round(r.x[6], 1), 'IoU', round(1 - S.loss(list(r.x)), 3), '구멍', holeterm(list(r.x)))
    if best is None or r.fun < best.fun: best = r
np.save(S.SP + 'sil6b_x.npy', best.x)
