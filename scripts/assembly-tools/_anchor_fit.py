# 3D 점(모델 좌표)과 책 그림 점(픽셀) 목록으로 카메라(fov 도 같이)·축선을 풀고, 판 격자 pts 를 그 카메라로 투영해 fits/NN_P.json·NN_axes.json 에 쓴다 (격자 holefit 가 미달인 번호 — 링·윤곽 점 앵커 방식, ⚠)
#   python _anchor_fit.py <이름> <번호> <앵커.json> [no_lines]
#   앵커.json = {"obj": [[x,y,z]...], "img": [[px,py]...], "plate": {"cols":15,"rows":2,"center":[0,5,0],"colDir":"+X","rowDir":"+Z"}, "name": "근거 설명", "origin": [x,y,z] (축선 원점, 생략하면 판 칸1 줄1 구멍 윗면)}
import json, math, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles
name, N = sys.argv[1], int(sys.argv[2]); a = json.load(open(sys.argv[3], encoding="utf-8")); R = "refs/%s/" % name
obj = np.array(a["obj"], float); img = a["img"]; im = cv2.imread(R + "%02d.jpg" % N); H, W = im.shape[:2]; cc = obj.mean(0)
best = None
for fov in range(14, 71, 2):
    r = fit(obj - cc, img, W, H, fov)
    if r:
        e, rv, tv, K = r; C, fwd, up, right = cam_from(rv, tv)
        if up[1] > 0 and (best is None or e < best[0]): best = (e, fov, rv, tv, K)
if not best: sys.exit("카메라를 못 풀었다")
e, fov, rv, tv, K = best; C, fwd, up, right = cam_from(rv, tv); az, el, _ = angles(C + cc, cc)
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - cc]), rv, tv, K, None)[0][0][0]
pl = a["plate"]; cols, rows = pl["cols"], pl["rows"]; cx, cy, cz = pl["center"]; V = {"+X": (0, 1), "-X": (0, -1), "+Z": (2, 1), "-Z": (2, -1)}
def cell(c, r, y=0.0):
    q = [cx, cy + y, cz]; q[V[pl["colDir"]][0]] += V[pl["colDir"]][1] * (c - (cols + 1) / 2) * 10; q[V[pl["rowDir"]][0]] += V[pl["rowDir"]][1] * (r - (rows + 1) / 2) * 10; return q
pts = []
for c, r in [(cc_, rr) for rr in range(1, rows + 1) for cc_ in range(1, cols + 1)]:
    q = P(cell(c, r, 2.5)); pts.append([c, r, round(float(q[0]), 1), round(float(q[1]), 1)])
f = {"name": a.get("name", "") + " · 격자 pts = 앵커 점으로 푼 카메라(오차 %.2fpx, fov %d)로 판 칸·줄을 투영한 환산값(⚠ 구멍 중심 검출값이 아님)" % (e, fov), "cols": cols, "rows": rows, "pts": pts, "est": [], "tool": "anchor-pnp", "fov": fov,
     "xyz3d": a["obj"], "xyz3d_img": a["img"]}
json.dump(f, open(R + "fits/%02d_P.json" % N, "w", encoding="utf-8"), ensure_ascii=False)
b = np.array(a.get("origin") or cell(1, 1, 2.5), float); v = {k: P(b + np.array(d) * 50) - P(b) for k, d in (("X", [1, 0, 0]), ("Y", [0, 1, 0]), ("Z", [0, 0, 1]))}
sc = 55 / max(abs(x) for vv in v.values() for x in vv); g = {k: [round(float(vv[0] * sc), 1), round(float(vv[1] * sc), 1)] for k, vv in v.items()}
roll = math.degrees(math.atan2(right[1], math.hypot(right[0], right[2])))
ax = {"global": g, "fit": {"from": "%02d_P.json" % N, "err_px": round(float(e), 2), "points": len(obj), "theta": round(math.radians(az), 2), "phi": round(math.radians(90 - el), 2), "cols": pl["colDir"], "rows": pl["rowDir"], "roll_deg": round(roll, 1)}, "no_rotate": True, "origin_cell": [1, 1]}
if len(sys.argv) > 4 and sys.argv[4] == "no_lines": ax["no_lines"] = True
if abs(roll) > 3: ax["level"] = True   # 책 그림이 기울어(roll) 있어 뷰어 카메라(roll 없음)로는 같은 그림이 안 나온다 → 그림을 돌려 맞춘다
json.dump(ax, open(R + "%02d_axes.json" % N, "w"), indent=1)
print("오차 %.2fpx (%d점) fov %d theta %.2f phi %.2f roll %.1f°  X%s Y%s Z%s" % (e, len(obj), fov, math.radians(az), math.radians(90 - el), roll, g["X"], g["Y"], g["Z"]))
