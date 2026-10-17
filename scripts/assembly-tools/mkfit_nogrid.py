# 격자를 못 읽는 번호(판이 가려지거나 평면 한 장뿐)의 카메라·축·격자 표시를 fits/NN_P.json 의 3D 점(xyz3d)과 책 그림 점(xyz3d_img)으로 만든다 (어보이더 28~30번에서 만듦, 2026-10-17).
#   python mkfit_nogrid.py <번호> <fov> [판 z(기본 17.5 = 머리 뒤판 바깥면) [칸1 의 x 부호(기본 +1: 뒤에서 볼 때 화면 왼쪽이 +x, 앞에서 볼 땐 −1)]]
#   fits 에 fov 를 고정으로 적고, <번호>_axes.json(축선 방향·theta·phi·오차)과 격자 표시용 pts(머리 뒤판 9×5 칸·줄을 이 카메라로 투영한 환산값)를 쓴다.
#   격자 pts 는 책에서 읽은 점이 아니라 환산값이다(fits name 에 적는다). 다음에 python refs_rect.py <이름> <번호>, python overlay_check.py <이름> <번호>.
import json, math, sys
import numpy as np, cv2
from pnp import fit, cam_from, angles

N = int(sys.argv[1]); fov = int(sys.argv[2]); ZP = float(sys.argv[3]) if len(sys.argv) > 3 else 17.5; XS = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
im = cv2.imread("refs/avoider/%02d.jpg" % N); H, W = im.shape[:2]
f = json.load(open("refs/avoider/fits/%02d_P.json" % N, encoding="utf-8")); obj = np.array(f["xyz3d"], float); img = f["xyz3d_img"]; c = obj.mean(0)
e, rv, tv, K = fit(obj - c, img, W, H, fov); C, fwd, up, right = cam_from(rv, tv); az, el, _ = angles(C, [0, 0, 0])
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]
b = obj.mean(0); v = {k: P(b + np.array(d) * 50) - P(b) for k, d in (("X", [1, 0, 0]), ("Y", [0, 1, 0]), ("Z", [0, 0, 1]))}
sc = 55 / max(abs(x) for vv in v.values() for x in vv); g = {k: [round(float(vv[0] * sc), 1), round(float(vv[1] * sc), 1)] for k, vv in v.items()}
pts = []
for cc, rr in [(1, 1), (9, 1), (1, 5), (9, 5), (2, 1), (1, 2)]:
    q = P([XS * (40 - 10 * (cc - 1)), 215.6 - 10 * (rr - 1), ZP]); pts.append([cc, rr, round(float(q[0]), 1), round(float(q[1]), 1)])
f["cols"] = 9; f["rows"] = 5; f["pts"] = pts; f["fov"] = fov
json.dump(f, open("refs/avoider/fits/%02d_P.json" % N, "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"global": g, "fit": {"from": "%02d_P.json" % N, "err_px": round(float(e), 2), "points": len(obj), "theta": round(math.radians(az), 2), "phi": round(math.radians(90 - el), 2), "cols": "+X" if XS < 0 else "-X", "rows": "-Y"}, "no_rotate": True, "origin_cell": [1, 1]}, open("refs/avoider/%02d_axes.json" % N, "w"), indent=1)
print(round(float(e), 2), "theta", round(math.radians(az), 2), "phi", round(math.radians(90 - el), 2), g)
