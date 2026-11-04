import sys, json, itertools
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from pnp import fit
sys.stdout.reconfigure(encoding="utf-8")
im = cv2.imread("C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/04.jpg"); Hh, Ww = im.shape[:2]
# 책에서 읽은 점(원본 좌표 ±3px)
A_px = {"capm10": (147, 407), "cap0": (253, 357), "capp10": (355, 308), "p1tip": (466, 350), "p2tip": (52, 572)}      # A: 돌기 머리(xl −10·0·+10), 끝 돌기 p1(B 쪽)·p2(반대)
B_px_scr = {"cap_l": (680, 155), "cap_m": (763, 203), "cap_r": (846, 262), "ring": (622.5, 265), "end_l": (575, 200), "end_r": (918, 410)}   # B: 화면 왼쪽→오른쪽
def build(hyp, g):
    # hyp "a": 화면 왼쪽 = +X (링 구멍 x=+10), "b": 화면 왼쪽 = −X (링 구멍 x=−10)
    s = +1 if hyp == "a" else -1                  # 화면 왼쪽 쪽 B 의 x 부호
    xj = 10.0 * s
    pts = []
    # B (원점, 길이 X, 위 +Y, 구멍축 Z): 돌기 머리 높이 y=10, 링은 A 쪽 면 z=−5
    pts.append(((s * 10, 10, 0), B_px_scr["cap_l"])); pts.append(((0, 10, 0), B_px_scr["cap_m"])); pts.append(((-s * 10, 10, 0), B_px_scr["cap_r"]))
    pts.append(((xj, 0, -5), B_px_scr["ring"])); pts.append(((s * 20, 0, 0), B_px_scr["end_l"])); pts.append(((-s * 20, 0, 0), B_px_scr["end_r"]))
    # A: 길이 Z(B 쪽이 +Z), 위 +Y, 중심 (xj, 0, −20−g)
    zc = -20.0 - g
    pts.append(((xj, 10, zc - 10), A_px["capm10"])); pts.append(((xj, 10, zc), A_px["cap0"])); pts.append(((xj, 10, zc + 10), A_px["capp10"]))
    pts.append(((xj, 0, zc + 20), A_px["p1tip"])); pts.append(((xj, 0, zc - 20), A_px["p2tip"]))
    return pts
if __name__ == '__main__':
    res = []
    for hyp in ("a", "b"):
        for g in range(0, 81, 5):
            pts = build(hyp, g); obj = [p for p, q in pts]; img = [q for p, q in pts]; best = None
            for fov in range(15, 71, 5):
                r_ = fit(obj, img, Ww, Hh, fov)
                if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
            if not best: continue
            (e, rv, tv, K), fov = best
            pj = cv2.projectPoints(np.array(obj, np.float64), np.asarray(rv, np.float64), np.asarray(tv, np.float64), np.asarray(K, np.float64), None)[0].reshape(-1, 2)
            er = np.hypot(*(pj - np.array(img)).T); res.append((float(er.mean()), float(er.max()), hyp, g, fov))
    res.sort()
    for r in res[:8]: print("가설 %s 간격 %d fov %d → 평균 %.2f 최대 %.2f" % (r[2], r[3], r[4], r[0], r[1]))
