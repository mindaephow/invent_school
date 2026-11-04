# 6번 판 카메라: 판(515프레임) 실루엣 ↔ 책 그림 어두운 판 실루엣 겹침(서보·흰 프레임·위 조립은 비교에서 뺀다) — 눈으로 점을 읽지 않음
import sys, math
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from scipy.optimize import minimize
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
SP = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/"
im = cv2.imread("C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/10.jpg"); Hh, Ww = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
dark = ((g < 120) & (hsv[..., 1] < 80)).astype(np.uint8); dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
# 판 좌표(infer 세계): 칸 c → x (c−8)·10, 줄 r → z (r−3)·10, 판 바닥 y 0 윗면 5
BOX = np.array([[sx * 75.0, y, sz * 25.0] for sx in (-1, 1) for y in (0, 5.0) for sz in (-1, 1)], float)
SERVO = np.array([[x, y, z] for x in (-30.0, 10.0) for y in (5.0, 45.0) for z in (-14.0, 14.0)], float)   # 서보 자리(칸 6~8 둘레, 넉넉한 상자) — 비교에서만 뺀다
EXC = np.zeros((Hh, Ww), np.uint8)
cv2.fillPoly(EXC, [np.array([[170, 300], [470, 300], [470, 470], [560, 480], [640, 560], [470, 700], [350, 740], [170, 650]], np.int32)], 1)   # 양쪽 줄에 선 두 조립
cv2.fillPoly(EXC, [np.array([[270, 30], [600, 30], [600, 310], [270, 310]], np.int32)], 1)                                              # 떠 있는 25프레임 둘
cv2.fillPoly(EXC, [np.array([[215, 340], [300, 335], [330, 390], [235, 400]], np.int32)], 1)                                            # 흰 프레임 끝
cv2.fillPoly(EXC, [np.array([[540, 480], [780, 580], [760, 620], [520, 540]], np.int32)], 1)
cv2.fillPoly(EXC, [np.array([[455, 300], [640, 300], [640, 500], [455, 500]], np.int32)], 1)   # 오른쪽 줄 조립 윗부분·화살표 선
cv2.rectangle(EXC, (860, 640), (999, 780), 1, -1); cv2.rectangle(EXC, (30, 40), (190, 140), 1, -1)   # 쪽 번호 '10' · '(6)' 표시
EXC = cv2.dilate(EXC, np.ones((11, 11), np.uint8))
def K_(fov): f = (Hh / 2) / math.tan(math.radians(fov) / 2); return np.array([[f, 0, Ww / 2], [0, f, Hh / 2], [0, 0, 1]], float)
def hull_mask(pts, rv, tv, K, grow=0):
    q = cv2.projectPoints(pts, rv, tv, K, None)[0].reshape(-1, 2)
    m = np.zeros((Hh, Ww), np.uint8)
    if not np.all(np.isfinite(q)) or np.abs(q).max() > 1e5: return None
    cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return cv2.dilate(m, np.ones((grow, grow), np.uint8)) if grow else m
def parts(x):
    return np.array(x[:3], float).reshape(3, 1), np.array(x[3:6], float).reshape(3, 1), x[6]
RV = [(111, -20, (483, 460)), (101, -20, (508, 435)), (91, -20, (532, 400)), (111, 20, (327, 390)), (101, 20, (353, 362)), (91, 20, (377, 338))]   # 리벳 여섯(A 블록 구멍 위 — 책 10번 그림의 주황 링 가운데)
ANCH = [(np.array([[x - 11.0, 38.0, z]]), np.array(px, float)) for x, z, px in RV]
def loss(x):
    if x[6] < 8 or x[6] > 60: return 9.0
    rv, tv, fov = parts(x); K = K_(fov); mp = hull_mask(BOX, rv, tv, K); ms = hull_mask(SERVO, rv, tv, K, 9)
    if mp is None or ms is None: return 9.0
    ign = (EXC | ms); ok = (ign == 0)
    a = (mp & ok); b = (dark & ok)
    iou_l = 1.0 - int((a & b).sum()) / max(1, int((a | b).sum()))
    pen = 0.0
    for P, px in ANCH:
        q = cv2.projectPoints(P, rv, tv, K, None)[0].reshape(2); pen += min(float(np.hypot(*(q - px))), 100.0)
    return iou_l + 0.01 * pen / len(ANCH)
if __name__ == "__main__":
    x = list(np.load(SP + "sil9_x.npy")); print("6번 카메라로 시작 1−IoU %.3f" % loss(x))
    best = (loss(x), x)
    for fov in (12, 16, 20, 26):
        x0 = list(x); x0[6] = fov
        for rnd in range(3):
            r = minimize(loss, x0, method="Powell", options={"maxiter": 8, "xtol": 1e-3, "ftol": 1e-6}); x0 = list(r.x)
        print("fov 시작", fov, "→ IoU %.3f fov %.1f" % (1 - r.fun, x0[6]))
        if r.fun < best[0]: best = (r.fun, list(r.x))
    x = best[1]; np.save(SP + "sil10_x.npy", np.array(x)); print("IoU %.3f" % (1 - best[0]))
    rv, tv, fov = parts(x); K = K_(fov); ov = im.copy(); mp = hull_mask(BOX, rv, tv, K)
    ov[mp > 0] = (0.55 * ov[mp > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8); cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/cubo_crops/sil10.png")
