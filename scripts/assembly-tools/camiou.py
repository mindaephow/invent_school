# 풀린 카메라(fits/NN_P.json 의 xyz3d·fov)로 모델 부품 상자를 투영해 책 그림 몸통 윤곽과의 겹침(IoU)을 잰다 — 후보 카메라(띄움 가정이 다른 해 등)를 비교할 때(2026-10-23).
#   python camiou.py <이름> <번호> [fits 파일(기본 fits/NN_P.json)]
import sys, os, json, numpy as np, cv2, runpy
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
from pnp import fit
name, N = sys.argv[1], int(sys.argv[2]); fp = sys.argv[3] if len(sys.argv) > 3 else "refs/%s/fits/%02d_P.json" % (name, N)
f = json.load(open(fp, encoding="utf-8")); A = runpy.run_path(name + ".py", run_name="probe")["A"]; dims = json.load(open("dims.json", encoding="utf-8"))
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
M = ((g < 225) | (hsv[:, :, 1] > 60)).astype(np.uint8); gr = ((hsv[:, :, 0] > 45) & (hsv[:, :, 0] < 85) & (hsv[:, :, 1] > 100)).astype(np.uint8); M[cv2.dilate(gr, np.ones((5, 5))) > 0] = 0
O = np.array(f["xyz3d"], float); c = O.mean(0); r = fit(O - c, [list(map(float, q)) for q in f["xyz3d_img"]], W, H, f["fov"], f.get("cx"), f.get("cy")); e, rv, tv, K = r
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]
hide = (A.steps[N - 1].kw.get("hideMade") or {}); out = np.zeros((H, W), np.uint8)
for q in A.parts:
    d = dims.get(q.n)
    if not d or q.step.index > N or q.n in ("리벳", "8볼트", "12볼트", "너트") or str(q.step.index) in hide: continue
    R = np.array(q.R, float); cc = np.array(q.p, float)
    if q.step.index == N and q.extra.get("hover") and q.extra.get("dir"): cc = cc + np.array(q.extra["dir"], float) * float(os.environ.get("HOV") or q.extra["hover"])
    pts = np.array([P(cc + R @ np.array([sx * d[0] / 2, sy * d[1] / 2, sz * d[2] / 2])) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    cv2.fillConvexPoly(out, cv2.convexHull(pts.astype(np.float32)).astype(np.int32), 1)
M[:120, :230] = 0; M[700:, 840:] = 0; out[:120, :230] = 0; out[700:, 840:] = 0
print("%s: 점 오차 %.2f  윤곽 IoU %.3f" % (os.path.basename(fp), e, ((out & M).sum() / max(((out | M) > 0).sum(), 1))))
