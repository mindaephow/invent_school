import sys, math
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools"); sys.path.insert(0, "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad")
sys.argv = ["x"]
import fit4 as F
import numpy as np, cv2
from scipy.optimize import minimize
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
im = F.im; Hh, Ww = F.Hh, F.Ww
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
book = ((gray < 225) & (hsv[..., 1] < 60)).astype(np.uint8)   # 블록(어두운 회색), 초록 화살표·링은 뺀다
book = cv2.morphologyEx(book, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# 블록 한 개의 볼록 조각들(자기 좌표: x 길이, y 구멍축, z 돌기 면): 몸통 + 윗·아랫면 돌기 6 + 끝 돌기 2
def block_pieces():
    P = []
    P.append(np.array([[sx * 15, sy * 5, sz * 5] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float))
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
RB = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # B: x̂→X, ŷ→−Z, ẑ→Y  (열이 로컬 축)
RB = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
# 열 = 로컬축의 세계 방향: x̂→(1,0,0), ŷ→(0,0,−1), ẑ→(0,1,0)  → 행렬 [[1,0,0],[0,0,1],[0,-1,0]] 의 열: (1,0,0),(0,0,-1),(0,1,0)
RA = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float)       # A: x̂→Z, ŷ→X, ẑ→Y
def placed(hyp, g):
    s = +1 if hyp == "a" else -1; xj = 10.0 * s
    out = []
    for pc in PIECES: out.append((RB @ pc.T).T + np.array([0, 0, 0.0]))
    for pc in PIECES: out.append((RA @ pc.T).T + np.array([xj, 0, -20.0 - g]))
    return out
def render(params, hyp):
    rv = np.array(params[:3], float).reshape(3, 1); tv = np.array(params[3:6], float).reshape(3, 1); fov = params[6]; g = params[7]
    f = (Hh / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, Ww / 2], [0, f, Hh / 2], [0, 0, 1]], float)
    m = np.zeros((Hh, Ww), np.uint8)
    for pc in placed(hyp, g):
        q = cv2.projectPoints(pc, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)): return None
        h = cv2.convexHull(q.astype(np.float32)).astype(np.int32); cv2.fillConvexPoly(m, h, 1)
    return m
def loss(params, hyp):
    m = render(params, hyp)
    if m is None or params[6] < 8 or params[6] > 80 or params[7] < 0: return 9.0
    inter = int((m & book).sum()); uni = int((m | book).sum()); return 1.0 - inter / max(1, uni)
if __name__ == "__main__":
    hyp = "a"; pts = F.build(hyp, 26.0); obj = [p for p, q in pts]; img = [q for p, q in pts]
    best = None
    for fov in range(14, 40, 3):
        r_ = fit(obj, img, Ww, Hh, fov)
        if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
    (e, rv, tv, K), fov = best
    x0 = list(np.ravel(rv)) + list(np.ravel(tv)) + [float(fov), 26.0]
    x0 = list(np.load("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/sil4_x.npy"))
    print("시작 loss(1−IoU) %.3f" % loss(x0, hyp))
    r = minimize(loss, x0, args=(hyp,), method="Powell", options={"maxiter": 6, "xtol": 1e-3, "ftol": 1e-5})
    print("Powell 후 1−IoU %.3f  IoU %.3f fov %.1f 간격 %.1f" % (r.fun, 1 - r.fun, r.x[6], r.x[7]))
    np.save("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/sil4_x.npy", r.x)
    m = render(r.x, hyp); ov = im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/bb/sil4.png")
