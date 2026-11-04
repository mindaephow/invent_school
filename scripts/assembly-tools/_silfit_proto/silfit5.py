import sys, math
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools"); sys.path.insert(0, "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad")
sys.argv = ["x"]
import numpy as np, cv2
from scipy.optimize import minimize
from pnp import fit
import fit5 as F5
import silfit4 as S4
sys.stdout.reconfigure(encoding="utf-8")
Hh, Ww, BOOK = F5.Hh, F5.Ww, F5.BOOK
SIG = 1
_g = ((F5.hsv[..., 1] > 70) & (F5.hsv[..., 0] > 30) & (F5.hsv[..., 0] < 95)).astype(np.uint8)
NOIGN = (cv2.dilate(_g, np.ones((5, 5), np.uint8)) == 0).astype(np.uint8)   # 초록 링·화살표(그림 위 표시)는 비교에서 뺀다
# 단독 블록 S: 중심 = 프레임 h2 아래(y 10), x̂ = (σ,0,1)/√2, ẑ = +Y, ŷ = (1,0,−σ)/√2
def rot_S(sig):
    xh = np.array([sig, 0, 1.0]) / math.sqrt(2); zh = np.array([0, 1.0, 0]); yh = np.cross(zh, xh); return np.stack([xh, yh, zh], 1)
def frame_pieces(hw=5.0, ext=5.0):
    # 135도 프레임: 구멍 중심선을 따라 폭 10·두께 5 인 사각 기둥들의 볼록 껍질(로컬 x,z; y ±2.5)
    hs = [F5.HF["h%d" % i] for i in range(1, 10)]; P = []
    for (x0, z0), (x1, z1) in zip(hs[:-1], hs[1:]):
        d = np.array([x1 - x0, z1 - z0]); L = np.linalg.norm(d); d /= L; n = np.array([-d[1], d[0]])
        pts = []
        for e in ((x0, z0, -ext), (x1, z1, ext)):
            for sn in (-hw, hw):
                for sy in (-2.5, 2.5): pts.append([e[0] + n[0] * sn + d[0] * e[2], sy, e[1] + n[1] * sn + d[1] * e[2]])
        P.append(np.array(pts, float))
    return P
FP = frame_pieces()
HW = [5.0]
def scene(sig, hover):
    org = np.array([10 - 11.5 * sig, 17.5 + hover, 5 - 36.5])
    RF = np.stack([np.array([0, 0, 1.0]), np.array([0, -sig, 0.0]), np.array([sig, 0, 0.0])], 1)   # x̂→+Z, ŷ→−σY, ẑ→σX
    out = []
    for pc in frame_pieces(HW[0]): out.append((RF @ pc.T).T + org)
    # S 중심 = 프레임 h2(최종 위치: hover 0) 아래, 높이 10
    h2 = np.array([10 - 11.5 * sig, 17.5, 5 - 36.5]) + RF @ np.array([F5.HF["h2"][0], 0, F5.HF["h2"][1]])
    cS = np.array([h2[0], 10.0, h2[2]]); RS = rot_S(sig)
    for pc in S4.PIECES: out.append((RS @ pc.T).T + cS)
    # L(4번 조립): B 중심 (0,10,5), A 중심 (10,10,−15)
    for pc in S4.PIECES: out.append((S4.RB @ pc.T).T + np.array([0, 10.0, 5.0]))
    for pc in S4.PIECES: out.append((S4.RA @ pc.T).T + np.array([10.0, 10.0, -15.0]))
    return out
def render(params):
    rv = np.array(params[:3], float).reshape(3, 1); tv = np.array(params[3:6], float).reshape(3, 1); fov = params[6]; hv = params[7]; HW[0] = params[8] if len(params) > 8 else 5.0
    f = (Hh / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, Ww / 2], [0, f, Hh / 2], [0, 0, 1]], float)
    m = np.zeros((Hh, Ww), np.uint8)
    for pc in scene(SIG, hv):
        q = cv2.projectPoints(pc, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)): return None
        cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return m
def loss(params):
    if params[6] < 8 or params[6] > 80 or params[7] < 0 or (len(params) > 8 and not (4.0 <= params[8] <= 8.0)): return 9.0
    m = render(params)
    if m is None: return 9.0
    return 1.0 - int((m & BOOK & NOIGN).sum()) / max(1, int(((m | BOOK) & NOIGN).sum()))
if __name__ == "__main__":
    pts = F5.points(SIG, 30.0); obj = [p for p, q in pts]; img = [q for p, q in pts]; best = None
    for fov in range(12, 40, 2):
        r_ = fit(obj, img, Ww, Hh, fov)
        if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
    (e, rv, tv, K), fov = best
    x0 = list(np.load("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/sil5_x.npy")[:8]) + [5.5]
    print("시작 1−IoU %.3f" % loss(x0))
    r = minimize(loss, x0, method="Powell", options={"maxiter": 6, "xtol": 1e-3, "ftol": 1e-5})
    print("Powell 후 IoU %.3f fov %.1f 프레임 띄움 %.1f 프레임 반폭 %.2f" % (1 - r.fun, r.x[6], r.x[7], r.x[8]))
    np.save("C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/sil5_x.npy", r.x)
    m = render(r.x); ov = im = F5.im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/bb/sil5.png")
