import sys, math, json
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
AT = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/"
im = cv2.imread(AT + "refs/steercar/05.jpg"); Hh, Ww = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
BOOK = ((gray < 235) & (hsv[..., 1] < 60)).astype(np.uint8)        # 부품(회색·검정) 마스크, 초록 링·화살표·주황 틀 제외
# 책 링 픽셀(프레임 링 5 = h1·h3·h6·h8·h9, 블록 링 5 = S 둘 + L 셋)
FR = {"h1": (258, 327), "h3": (303, 214), "h6": (495, 100), "h8": (640, 60), "h9": (705, 22)}
BR = {"S_h1": (255, 598), "S_h3": (305, 467), "L_h6": (480, 352), "L_h8": (610, 285), "L_h9": (700, 262)}
HF = {"h1": (-34.5, -9.5), "h2": (-27.5, -2.5), "h3": (-20.5, 4.5), "h4": (-13.5, 11.5), "h5": (-3.5, 11.5), "h6": (6.5, 11.5), "h7": (16.5, 11.5), "h8": (26.5, 11.5), "h9": (36.5, 11.5)}   # 135도 프레임 구멍(로컬 x,z)
def frame_world(sig, hover):
    # 프레임 로컬: x̂→+Z, ẑ→σ·X, ŷ→−σ·Y  / 원점: h9 이 B 돌기(10, ·, 5) 위
    org = np.array([10 - 11.5 * sig, 17.5 + hover, 5 - 36.5])
    def W(h, dy=0.0): x, z = HF[h]; return org + np.array([sig * z, dy, x])
    return org, W
def points(sig, hover):
    org, W = frame_world(sig, hover); pts = []
    for h, px in FR.items(): pts.append((W(h, 2.5), px))                       # 프레임 윗면 구멍(링)
    # 블록 쪽: 돌기 윗면 y=20 (S 중심 = 프레임 h2 아래 y=10, L = 4번 조립)
    xS = lambda h: W(h)[[0, 2]]
    pts.append((np.array([xS("h1")[0], 20, xS("h1")[1]]), BR["S_h1"])); pts.append((np.array([xS("h3")[0], 20, xS("h3")[1]]), BR["S_h3"]))
    pts.append((np.array([10, 20, -25.0]), BR["L_h6"])); pts.append((np.array([10, 20, -5.0]), BR["L_h8"])); pts.append((np.array([10, 20, 5.0]), BR["L_h9"]))
    return pts
if __name__ == "__main__":
    res = []
    for sig in (1, -1):
        for hv in range(24, 56, 2):
            pts = points(sig, float(hv)); obj = [p for p, q in pts]; img = [q for p, q in pts]; best = None
            for fov in range(12, 46, 3):
                r_ = fit(obj, img, Ww, Hh, fov)
                if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
            if not best: continue
            (e, rv, tv, K), fov = best
            pj = cv2.projectPoints(np.array(obj, np.float64), np.asarray(rv, np.float64), np.asarray(tv, np.float64), np.asarray(K, np.float64), None)[0].reshape(-1, 2)
            er = np.hypot(*(pj - np.array(img)).T); res.append((float(er.mean()), float(er.max()), sig, hv, fov))
    res.sort()
    for r in res[:8]: print("σ %+d hover %d fov %d → 평균 %.2f 최대 %.2f" % (r[2], r[3], r[4], r[0], r[1]))
