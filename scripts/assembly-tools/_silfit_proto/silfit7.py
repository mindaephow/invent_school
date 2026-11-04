# 7번(4번의 거울 쪽): 3단블록 둘 실루엣 겹침으로 카메라·배치 가설을 푼다 — 눈으로 점을 읽지 않음
import sys, math, itertools
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
sys.argv = ["x"]
import numpy as np, cv2
from scipy.optimize import minimize
sys.stdout.reconfigure(encoding="utf-8")
SP = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/"
STEP = int(__import__("os").environ.get("STEP", "7"))
im = cv2.imread("C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/%02d.jpg" % STEP); Hh, Ww = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
book = ((gray < 225) & (hsv[..., 1] < 60)).astype(np.uint8); book = cv2.morphologyEx(book, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
gm = ((hsv[..., 1] > 70) & (hsv[..., 0] > 30) & (hsv[..., 0] < 95)).astype(np.uint8); noign = (cv2.dilate(gm, np.ones((9, 9), np.uint8)) == 0)
def block_pieces():
    P = [np.array([[sx * 15, sy * 5, sz * 5] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float)]
    def cyl(c, ax, a0, a1, r=3.8, n=14):
        pts = []
        for t in np.linspace(0, 2 * math.pi, n, endpoint=False):
            for a in (a0, a1):
                if ax == "z": pts.append([c[0] + r * math.cos(t), c[1] + r * math.sin(t), a])
                else: pts.append([a, c[1] + r * math.cos(t), c[2] + r * math.sin(t)])
        return np.array(pts, float)
    for x in (-10, 0, 10): P.append(cyl((x, 0), "z", 5, 10)); P.append(cyl((x, 0), "z", -10, -5))
    P.append(cyl((0, 0, 0), "x", 15, 20)); P.append(cyl((0, 0, 0), "x", -20, -15))
    return P
PIECES = block_pieces()
RB = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)   # 받는 블록: x̂→X, ŷ→−Z, ẑ→Y
RA = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)    # 끼우는 블록(4번과 같은 자세): x̂→Z, ŷ→X, ẑ→Y
def placed(hyp, g):
    zs, xs = hyp   # zs: 끼우는 블록이 받는 블록의 −Z(−1)/+Z(+1) 쪽, xs: 링 구멍이 +X(+1)/−X(−1)
    RAh = RA if zs < 0 else np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], float)   # 반대쪽이면 길이 방향(끝 돌기 p1)이 받는 블록을 향하게 돌린다(x̂→−Z·ŷ→−X)
    out = [(RB @ pc.T).T for pc in PIECES]
    zc = zs * (20.0 + g)
    out += [(RAh @ pc.T).T + np.array([10.0 * xs, 0, zc]) for pc in PIECES]
    return out
def mk_cam(az, el, dist, fov, ox, oy):
    a, e = math.radians(az), math.radians(el)
    C = np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)]) * dist + np.array([0, 0, -10.0])
    z = (np.array([0, 0, -10.0]) - C); z /= np.linalg.norm(z); x = np.cross(z, [0, 1.0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    R = np.array([x, y, z]); rv = cv2.Rodrigues(R)[0]; tv = (-R @ C).reshape(3, 1)
    f = (Hh / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, Ww / 2 + ox], [0, f, Hh / 2 + oy], [0, 0, 1]], float)
    return rv, tv, K
def render(p, hyp):
    az, el, dist, fov, ox, oy, g = p
    rv, tv, K = mk_cam(az, el, dist, fov, ox, oy); m = np.zeros((Hh, Ww), np.uint8)
    for pc in placed(hyp, g):
        q = cv2.projectPoints(pc, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)) or np.abs(q).max() > 1e5: return None
        cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return m
def loss(p, hyp):
    if p[3] < 8 or p[3] > 60 or p[6] < 0 or p[6] > 120 or p[2] < 50 or p[2] > 3000 or p[1] < 5 or p[1] > 85: return 9.0
    m = render(p, hyp)
    if m is None: return 9.0
    a = m & noign.astype(np.uint8); b = book & noign.astype(np.uint8)
    return 1.0 - int((a & b).sum()) / max(1, int((a | b).sum()))
if __name__ == "__main__":
    res = []
    for hyp in itertools.product((-1, 1), (1, -1)):
        best = None
        for az in range(0, 360, 30):
            for el in (25, 40, 55):
                for g in (25.0, 50.0):
                    p0 = [az, el, 300.0, 22.0, 0.0, 0.0, g]; l = loss(p0, hyp)
                    if best is None or l < best[0]: best = (l, p0)
        p = best[1]
        for rnd in range(3):
            r = minimize(loss, p, args=(hyp,), method="Powell", options={"maxiter": 6, "xtol": 1e-2, "ftol": 1e-5}); p = list(r.x)
        print("가설 A쪽 %+d 링 x %+d → IoU %.3f az %.0f el %.0f fov %.1f 간격 %.1f" % (hyp[0], hyp[1], 1 - r.fun, p[0], p[1], p[3], p[6])); res.append((r.fun, hyp, p))
    res.sort(key=lambda t: t[0]); print("1등", res[0][1], "2등", res[1][1], "비 %.2f" % (res[1][0] / max(res[0][0], 1e-6)))
    import pickle; pickle.dump(res, open(SP + "sil%d_res.pkl" % STEP, "wb"))
    f, hyp, p = res[0]; m = render(p, hyp); ov = im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/cubo_crops/sil%d.png" % STEP)
