# 손으로 읽은 3D 점(fits/NN_P.json 의 xyz3d·xyz3d_img, fov 고정)으로 카메라·축선을 풀어 <번호>_axes.json 에 쓰고, refs_rect 가 격자 그림을 그리도록 판 격자(pts)를 이 카메라로 투영해 적는다
# (holefit 가 비스듬한 면에서 미달할 때 — 배틀로봇 4번 등, 2026-10-17. 격자 pts 는 환산값이라 fits name 에 적는다.)
#   python fit_manual.py <이름> <번호> <cx> <cy> <cz> <칸수> <줄수> <칸방향 +X|-X> <줄방향 +Y|-Y> [판 앞면 z 오프셋=2.5]
#     판 가운데 (cx,cy,cz), 칸 c(화면 왼쪽이 1) → 칸방향 쪽으로 (c−(칸수+1)/2)×10, 줄도 같다.
import json, math, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles
name, N = sys.argv[1], int(sys.argv[2]); cx, cy, cz = [float(v) for v in sys.argv[3:6]]; cols, rows = int(sys.argv[6]), int(sys.argv[7]); cd, rd = sys.argv[8], sys.argv[9]
off = float(sys.argv[10]) if len(sys.argv) > 10 else 2.5
sg = lambda d: 1 if d[0] == "+" else -1
R = "refs/%s/" % name
f = json.load(open(R + "fits/%02d_P.json" % N, encoding="utf-8")); obj = np.array(f["xyz3d"], float); img = f["xyz3d_img"]; c = obj.mean(0); fov = f["fov"]
im = cv2.imread(R + "%02d.jpg" % N); H, W = im.shape[:2]
e, rv, tv, K = fit(obj - c, img, W, H, fov); C, fwd, up, right = cam_from(rv, tv); az, el, _ = angles(C, [0, 0, 0])
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]
b = obj.mean(0); v = {k: P(b + np.array(d) * 50) - P(b) for k, d in (("X", [1, 0, 0]), ("Y", [0, 1, 0]), ("Z", [0, 0, 1]))}
sc = 55 / max(abs(x) for vv in v.values() for x in vv); g = {k: [round(float(vv[0] * sc), 1), round(float(vv[1] * sc), 1)] for k, vv in v.items()}
pts = []
for cc, rr in [(1, 1), (cols, 1), (1, rows), (cols, rows), (2, 1), (1, 2)]:
    q = P([cx + sg(cd) * (cc - (cols + 1) / 2) * 10, cy + sg(rd) * (rr - (rows + 1) / 2) * 10, cz + off]); pts.append([cc, rr, round(float(q[0]), 1), round(float(q[1]), 1)])
f["cols"] = cols; f["rows"] = rows; f["pts"] = pts
f["name"] += " · 격자 pts = 판 칸·줄을 이 카메라로 투영한 환산값(책에서 읽은 점 아님)"
json.dump(f, open(R + "fits/%02d_P.json" % N, "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"global": g, "fit": {"from": "%02d_P.json" % N, "err_px": round(float(e), 2), "points": len(obj), "theta": round(math.radians(az), 2), "phi": round(math.radians(90 - el), 2), "cols": cd, "rows": rd}, "no_rotate": True, "origin_cell": [1, 1]}, open(R + "%02d_axes.json" % N, "w"), indent=1)
print("오차 %.2fpx (%d점) fov %d theta %.2f phi %.2f roll %.1f°  X%s Y%s Z%s" % (e, len(obj), fov, math.radians(az), math.radians(90 - el), math.degrees(math.atan2(right[1], math.hypot(right[0], right[2]))), g["X"], g["Y"], g["Z"]))
