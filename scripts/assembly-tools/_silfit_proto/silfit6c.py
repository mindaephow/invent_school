# 6번 위 조립(5번 결과) 자세: 판 카메라 고정, 수직 축 둘레 4방향 × 띄움 높이를 실루엣 겹침으로 가른다
import sys; sys.argv = ['x']
sys.path.insert(0, '_silfit_proto'); sys.path.insert(0, '.')
import numpy as np, cv2, math
from scipy.optimize import minimize
import silfit6 as S6
import silfit5 as S5
Hh, Ww = S6.Hh, S6.Ww
x = list(np.load(S6.SP + 'sil6_x.npy')); rv, tv, fov = S6.parts(x); K = S6.K_(fov)
im = S6.im; g = S6.g; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
roi = np.zeros((Hh, Ww), np.uint8); cv2.fillPoly(roi, [np.array([[0, 0], [560, 0], [560, 300], [330, 330], [200, 420], [0, 440]], np.int32)], 1)
gm = ((hsv[..., 1] > 70) & (hsv[..., 0] > 30) & (hsv[..., 0] < 95)).astype(np.uint8); noign = (cv2.dilate(gm, np.ones((5, 5), np.uint8)) == 0)
book = (((g < 235) & (hsv[..., 1] < 60)).astype(np.uint8) & roi); book = cv2.morphologyEx(book, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
pcs5 = S5.scene(1, 0.0)   # 5번 세계(프레임 hover 0), 반폭 5
TIP5 = np.array([-20.0, 10.0, 5.0])   # 매달린 것은 B(직각 아랫 블록): 끝 돌기 p2 끝이 판 구멍으로(5번 세계)
def Rmat(h):   # 5번 B 의 −x 끝이 아래(−Y), 5번 +Y(돌기 면) → 수평 h
    h = np.array(h, float); c1 = np.array([0, 1.0, 0]); return np.stack([c1, h, np.cross(c1, h)], 1)
def render(R, lift, tip):
    m = np.zeros((Hh, Ww), np.uint8)
    for pc in pcs5:
        w = (R @ (pc - TIP5).T).T + np.array(tip) + np.array([0, lift, 0])
        q = cv2.projectPoints(w, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)): return None
        cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return m
def loss(R, p):
    m = render(R, p[0], (p[1], 0.0, p[2]))
    if m is None: return 9.0
    ok = noign & (roi > 0); a = m & ok; b = book & ok
    return 1 - int((a & b).sum()) / max(1, int((a | b).sum()))
if __name__ == '__main__':
    res = []
    for nm, h in (('+X', (1, 0, 0)), ('−X', (-1, 0, 0)), ('+Z', (0, 0, 1)), ('−Z', (0, 0, -1))):
        R = Rmat(h); bestl = None
        for lift in (120, 160, 200, 250):
            r = minimize(lambda p: loss(R, p), [lift, 81.0, -20.0], method='Powell', options={'maxiter': 6, 'xtol': 1e-2, 'ftol': 1e-5})
            if bestl is None or r.fun < bestl.fun: bestl = r
        print(nm, 'IoU %.3f 띄움 %.1f tip x %.1f z %.1f' % (1 - bestl.fun, *bestl.x)); res.append((bestl.fun, nm, h, bestl.x))
    res.sort(key=lambda t: t[0]); print('1등', res[0][1], '2등', res[1][1], '비', round(res[1][0] / max(res[0][0], 1e-6), 2))
    np.save(S6.SP + 'asm6.npy', np.concatenate([res[0][2], res[0][3]]))
    f, nm, h, p = res[0]; R = Rmat(h); m = render(R, p[0], (p[1], 0, p[2])); ov = im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode('.png', cv2.resize(ov[60:480, 0:700], None, fx=2, fy=2))[1].tofile('C:/Users/user/AppData/Local/Temp/cubo_crops/asm6.png')
