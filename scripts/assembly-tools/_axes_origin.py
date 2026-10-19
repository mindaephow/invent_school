# 누운 판 한 장의 fits(xyz3d·xyz3d_img·fov)로 카메라를 풀고, 축선(X=칸 방향·Y=위·Z=줄 방향, 이름 바꾸지 않음)을 '칸1 줄1 구멍'에서 계산해 NN_axes.json 에 쓴다
#   판의 긴 쪽(칸) 홀라인 = X선, 줄 방향 = Z선(사용자 2026-10-18). fit_from_grid.py 를 먼저 같은 방향으로 돌린다.
#   python _axes_origin.py <이름> <번호> <cx> <cy> <cz> [오프셋 2.5] [--칸 -X] [--줄 -Z]   (기본 +X, +Z)
import json, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
a_ = [x for x in sys.argv[1:] if not x.startswith("--")]; flags = sys.argv[1:]
def opt(k, d):
    return flags[flags.index(k) + 1] if k in flags else d
name, N = a_[0], int(a_[1]); cx, cy, cz = [float(v) for v in a_[2:5]]; off = float(a_[5]) if len(a_) > 5 else 2.5
V = {"+X": [1, 0, 0], "-X": [-1, 0, 0], "+Z": [0, 0, 1], "-Z": [0, 0, -1]}
cd, rd = np.array(V[opt("--칸", "+X")], float), np.array(V[opt("--줄", "+Z")], float)
R = "refs/%s/" % name
f = json.load(open(R + "fits/%02d_P.json" % N, encoding="utf-8")); obj = np.array(f["xyz3d"], float); img = f["xyz3d_img"]; fov = f["fov"]; cols, rows = f["cols"], f["rows"]
im = cv2.imread(R + "%02d.jpg" % N); H, W = im.shape[:2]; cc = obj.mean(0)
e, rv, tv, K = fit(obj - cc, img, W, H, fov)
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - cc]), rv, tv, K, None)[0][0][0]
b = np.array([cx, cy + off, cz]) - cd * (cols - 1) / 2 * 10 - rd * (rows - 1) / 2 * 10
v = {"X": P(b + cd * 50) - P(b), "Y": P(b + np.array([0, 50, 0])) - P(b), "Z": P(b + rd * 50) - P(b)}
sc = 55 / max(abs(x) for vv in v.values() for x in vv); g = {k: [round(float(vv[0] * sc), 1), round(float(vv[1] * sc), 1)] for k, vv in v.items()}
a = json.load(open(R + "%02d_axes.json" % N)); a["global"] = g
a["naming"] = "판의 긴 쪽(칸) 홀라인 = X선, 줄 방향 = Z선(이름 바꾸지 않음), 칸1 줄1 구멍에서 계산"
json.dump(a, open(R + "%02d_axes.json" % N, "w"), indent=1); print("오차 %.2fpx fov %d" % (e, fov), g)
