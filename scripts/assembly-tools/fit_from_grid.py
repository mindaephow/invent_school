# 서 있는 판 한 장의 holefit 결과(fits/NN_<라벨>.json, 찾은 점만)로 카메라(fov 도 같이)·축선을 풀어 <번호>_axes.json 에 쓰고 fits 에 xyz3d·xyz3d_img 를 적는다
# (axes_fit.py 는 est(격자로 채운 점)까지 45점을 쓰고 fov 를 고정해 2px 를 넘기는 번호가 있어서 만든 짝 도구 — 배틀로봇 2번, 2026-10-17).
#   python fit_from_grid.py <이름> <번호> <라벨> <cx> <cy> <cz> <칸방향 +X|−X…> <줄방향> [판 앞면 z 오프셋=2.5]
#     판 가운데 (cx,cy,cz), 칸 c → 칸방향 쪽으로 (c−(칸수+1)/2)×10, 줄 r → 줄방향 쪽으로 (r−(줄수+1)/2)×10, 앞면 = 판 가운데에서 법선 쪽 오프셋(서 있는 판은 z).
#   출력: 오차(px)·fov·theta·phi, fits 에 xyz3d·xyz3d_img·fov, <번호>_axes.json. 판 한 장(한 평면)이라 방향각만 믿는다(⚠).
import json, math, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles

name, N, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cx, cy, cz = float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]); cd, rd = sys.argv[7], sys.argv[8]
off = float(sys.argv[9]) if len(sys.argv) > 9 else 2.5
AX = {"+X": (0, 1), "-X": (0, -1), "+Y": (1, 1), "-Y": (1, -1), "+Z": (2, 1), "-Z": (2, -1)}
R = "refs/%s/" % name
f = json.load(open(R + "fits/%02d_%s.json" % (N, label), encoding="utf-8")); cols, rows = f["cols"], f["rows"]
est = {tuple(e) for e in f.get("est", [])}
im = cv2.imread(R + "%02d.jpg" % N); H, W = im.shape[:2]
xyz, img = [], []
na = ({0, 1, 2} - {AX[cd][0], AX[rd][0]}).pop()
for c, r, x, y in f["pts"]:
    if (c, r) in est: continue
    p = [cx, cy, cz]; p[AX[cd][0]] += AX[cd][1] * (c - (cols + 1) / 2) * 10; p[AX[rd][0]] += AX[rd][1] * (r - (rows + 1) / 2) * 10; p[na] += off
    xyz.append(p); img.append([x, y])
obj = np.array(xyz, float); cc = obj.mean(0); best = None
for fov in range(12, 61):
    r_ = fit(obj - cc, img, W, H, fov)
    if r_:
        e, rv, tv, K = r_; C, fwd, up, right = cam_from(rv, tv)
        if up[1] > 0 and (best is None or e < best[0]): best = (e, fov, rv, tv, K)
if not best: sys.exit("카메라를 못 풀었다")
e, fov, rv, tv, K = best; C, fwd, up, right = cam_from(rv, tv); az, el, _ = angles(C, [0, 0, 0])
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - cc]), rv, tv, K, None)[0][0][0]
b = obj.mean(0); v = {k: P(b + np.array(d) * 50) - P(b) for k, d in (("X", [1, 0, 0]), ("Y", [0, 1, 0]), ("Z", [0, 0, 1]))}
sc = 55 / max(abs(x) for vv in v.values() for x in vv); g = {k: [round(float(vv[0] * sc), 1), round(float(vv[1] * sc), 1)] for k, vv in v.items()}
roll = math.degrees(math.atan2(right[1], math.hypot(right[0], right[2])))
f["xyz3d"] = xyz; f["xyz3d_img"] = img; f["fov"] = fov
f["name"] = f.get("name", "") + " · 3D = 판 구멍(holefit 가 찾은 점만, est 제외) 모델 좌표. 판 한 장(한 평면)이라 카메라 방향각만 믿는다"
json.dump(f, open(R + "fits/%02d_%s.json" % (N, label), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"global": g, "fit": {"from": "%02d_%s.json" % (N, label), "err_px": round(float(e), 2), "points": len(obj), "theta": round(math.radians(az), 2), "phi": round(math.radians(90 - el), 2), "cols": cd, "rows": rd}, "no_rotate": True, "origin_cell": [1, 1]}, open(R + "%02d_axes.json" % N, "w"), indent=1)
print("오차 %.2fpx (%d점) fov %d theta %.2f phi %.2f roll %.1f°  X%s Y%s Z%s" % (e, len(obj), fov, math.radians(az), math.radians(90 - el), roll, g["X"], g["Y"], g["Z"]))
