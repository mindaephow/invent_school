# 앵커 JSON 의 점으로 카메라를 풀고 하나씩 빼 안정성을 본다: python _lo.py <이름> <번호> [fov고정]
import json, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles
name, N = sys.argv[1], int(sys.argv[2]); fixed = int(sys.argv[3]) if len(sys.argv) > 3 else None
a = json.load(open("refs/%s/anchors/%02d.json" % (name, N), encoding="utf-8")); obj = np.array(a["obj"], float); img = np.array(a["img"], float)
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]
def solve(o, i):
    best = None
    for fov in ([fixed] if fixed else range(14, 71, 2)):
        r = fit(o - o.mean(0), i, W, H, fov)
        if r:
            e, rv, tv, K = r; C, fwd, up, right = cam_from(rv, tv)
            if up[1] > 0 and (best is None or e < best[0]):
                az, el, _ = angles(C + o.mean(0), o.mean(0)); proj = cv2.projectPoints(np.float32(o - o.mean(0)), rv, tv, K, None)[0].reshape(-1, 2)
                best = (round(float(e), 2), fov, round(float(np.radians(az)), 2), round(float(np.radians(90 - el)), 2), np.linalg.norm(proj - i, axis=1).round(1).tolist())
    return best
print("전체", solve(obj, img))
if len(obj) > 4:
    for k in range(len(obj)):
        m = np.arange(len(obj)) != k; print("빼기", k, solve(obj[m], img[m]))
