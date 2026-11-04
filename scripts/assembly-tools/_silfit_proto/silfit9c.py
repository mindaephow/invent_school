# 9번 위 조립(8번 결과) 자세: 판 카메라(sil9) 고정, 수직 둘레 4방향을 실루엣 겹침으로 가린다
import sys, os, pickle; sys.argv = ['x']; os.environ["STEP"] = "8"
sys.path.insert(0, '.'); sys.path.insert(0, '..')
import numpy as np, cv2, math
from scipy.optimize import minimize
import silfit6 as _s6   # (SP 경로)
import silfit9 as S9
import silfit8 as F8, silfit7 as S7
Hh, Ww = S9.Hh, S9.Ww
x = list(np.load(S9.SP + 'sil9_x.npy')); rv, tv, fov = S9.parts(x); K = S9.K_(fov)
im = S9.im; g = S9.g; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
roi = np.zeros((Hh, Ww), np.uint8); cv2.fillPoly(roi, [np.array([[0, 0], [500, 0], [500, 330], [330, 400], [0, 470]], np.int32)], 1)
gm = ((hsv[..., 1] > 70) & (hsv[..., 0] > 30) & (hsv[..., 0] < 95)).astype(np.uint8); noign = (cv2.dilate(gm, np.ones((9, 9), np.uint8)) == 0)
book = (((g < 235) & (hsv[..., 1] < 60)).astype(np.uint8) & roi); book = cv2.morphologyEx(book, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
_c, _ = cv2.findContours(book, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); _f = np.zeros_like(book); cv2.drawContours(_f, _c, -1, 1, -1); book = _f
pcs = F8.scene("a", 34.0 * 0 + 0.0)   # 8번 세계, 프레임 hover 0 (끝 7.2/5.2 대신 6.15 로 이미 고쳐짐)
TIP = np.array([20.0, 10.0, -5.0])   # B7 의 +x 끝 돌기 끝(자유 끝, 5번 세계)
def Rmat(h):
    h = np.array(h, float); c1 = np.array([0, -1.0, 0]); return np.stack([c1, h, np.cross(c1, h)], 1)
def render(R, lift, tip):
    m = np.zeros((Hh, Ww), np.uint8)
    for pc in pcs:
        w = (R @ (pc - TIP).T).T + np.array(tip) + np.array([0, lift, 0]); q = cv2.projectPoints(w, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)): return None
        cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return m
def loss(R, p):
    m = render(R, p[0], (p[1], 0.0, p[2]))
    if m is None: return 9.0
    ok = noign & (roi > 0); a = m & ok; b = book & ok
    return 1 - int((a & b).sum()) / max(1, int((a | b).sum()))
if __name__ == '__main__':
    R0 = []
    for nm, h in (('+X', (1, 0, 0)), ('−X', (-1, 0, 0)), ('+Z', (0, 0, 1)), ('−Z', (0, 0, -1))):
        R = Rmat(h); best = None
        for lift in range(20, 360, 10):
            l = loss(R, [lift, 81.0, 20.0])
            if best is None or l < best[0]: best = (l, lift)
        print(nm, 'IoU %.3f 띄움 %d' % (1 - best[0], best[1])); R0.append((best[0], nm, h, best[1]))
    R0.sort(key=lambda t: t[0]); f, nm, h, lift = R0[0]; print('비', round(R0[1][0] / R0[0][0], 2), '1등', nm)
    R = Rmat(h); m = render(R, lift, (81.0, 0, 20.0)); ov = im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imwrite('C:/Users/user/AppData/Local/Temp/cubo_crops/asm9.png', cv2.resize(ov[0:480, 0:700], None, fx=2, fy=2)); pickle.dump(R0, open(S9.SP + 'asm9.pkl', 'wb'))
    for L in (0, 40, 60, 80, 100, 120, 140):
        q = cv2.projectPoints(np.array([[70.0, L, 20.0]]), rv, tv, K, None)[0].reshape(2); print('lift', L, np.round(q, 1))
