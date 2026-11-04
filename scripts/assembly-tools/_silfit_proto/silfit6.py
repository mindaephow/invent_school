# 6번 판 카메라: 판(515프레임) 실루엣 ↔ 책 그림 어두운 판 실루엣 겹침(서보·흰 프레임·위 조립은 비교에서 뺀다) — 눈으로 점을 읽지 않음
import sys, math
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from scipy.optimize import minimize
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
SP = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/"
im = cv2.imread("C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/06.jpg"); Hh, Ww = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
dark = ((g < 120) & (hsv[..., 1] < 80)).astype(np.uint8); dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
# 판 좌표(infer 세계): 칸 c → x (c−8)·10, 줄 r → z (r−3)·10, 판 바닥 y 0 윗면 5
BOX = np.array([[sx * 75.0, y, sz * 25.0] for sx in (-1, 1) for y in (0, 5.0) for sz in (-1, 1)], float)
SERVO = np.array([[x, y, z] for x in (-30.0, 10.0) for y in (5.0, 45.0) for z in (-14.0, 14.0)], float)   # 서보 자리(칸 6~8 둘레, 넉넉한 상자) — 비교에서만 뺀다
EXC = np.zeros((Hh, Ww), np.uint8)
cv2.fillPoly(EXC, [np.array([[0, 0], [480, 0], [480, 300], [250, 300], [0, 450]], np.int32)], 1)   # 위 왼쪽 조립 자리
cv2.fillPoly(EXC, [np.array([[238, 288], [268, 281], [600, 640], [550, 652]], np.int32)], 1); EXC = cv2.dilate(EXC, np.ones((15, 15), np.uint8))   # 흰 프레임
def K_(fov): f = (Hh / 2) / math.tan(math.radians(fov) / 2); return np.array([[f, 0, Ww / 2], [0, f, Hh / 2], [0, 0, 1]], float)
def hull_mask(pts, rv, tv, K, grow=0):
    q = cv2.projectPoints(pts, rv, tv, K, None)[0].reshape(-1, 2)
    m = np.zeros((Hh, Ww), np.uint8)
    if not np.all(np.isfinite(q)) or np.abs(q).max() > 1e5: return None
    cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return cv2.dilate(m, np.ones((grow, grow), np.uint8)) if grow else m
def parts(x):
    return np.array(x[:3], float).reshape(3, 1), np.array(x[3:6], float).reshape(3, 1), x[6]
def loss(x):
    if x[6] < 8 or x[6] > 60: return 9.0
    rv, tv, fov = parts(x); K = K_(fov); mp = hull_mask(BOX, rv, tv, K); ms = hull_mask(SERVO, rv, tv, K, 9)
    if mp is None or ms is None: return 9.0
    ign = (EXC | ms); ok = (ign == 0)
    a = (mp & ok); b = (dark & ok)
    return 1.0 - int((a & b).sum()) / max(1, int((a | b).sum()))
if __name__ == "__main__":
    C = np.array([947.7, 272.1, 419.9, 481.0, 323.2, 365.6, 818.3, 187.9], np.float32).reshape(4, 2)
    cornw = [[-75, 5, -25], [75, 5, -25], [75, 5, 25], [-75, 5, 25]]
    best = None
    for fov in range(12, 44, 4):
        r0 = fit(cornw, C, Ww, Hh, fov)
        if not r0: continue
        e, rv, tv, K = r0; x0 = list(np.ravel(rv)) + list(np.ravel(tv)) + [fov]
        l = loss(x0)
        if best is None or l < best[0]: best = (l, x0)
        print("시작 fov", fov, "1−IoU %.3f" % l)
    x = best[1]
    for rnd in range(4):
        r = minimize(loss, x, method="Powell", options={"maxiter": 8, "xtol": 1e-3, "ftol": 1e-6}); x = list(r.x); print("라운드", rnd, "IoU %.3f fov %.1f" % (1 - r.fun, x[6]))
    np.save(SP + "sil6_x.npy", np.array(x))
    rv, tv, fov = parts(x); K = K_(fov); ov = im.copy(); mp = hull_mask(BOX, rv, tv, K)
    ov[mp > 0] = (0.55 * ov[mp > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8); cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/cubo_crops/sil6.png")
