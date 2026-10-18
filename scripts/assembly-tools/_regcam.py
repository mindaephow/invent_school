# 앞 번호 책 그림(카메라를 이미 푼 것)과 이번 번호 책 그림의 특징점(SIFT)을 맞춰, 위 판 평면(기본 y 37)의 호모그래피로 이번 번호 카메라를 푼다 — 손으로 점을 읽는 대신(2026-10-19).
#   python _regcam.py <이름> <앞번호> <번호> [평면y=37] [fov고정]      → refs/<이름>/anchors/<번호>.json (obj=판 평면 격자 점, img=이 그림으로 옮긴 점, fov 고정)을 쓰고 잔차를 출력한다
#   이어서 python _anchor_fit.py <이름> <번호> refs/<이름>/anchors/<번호>.json  (fits·axes 작성)
# 가정: 같은 위 판(평면 하나)이 두 그림에 보이고 책 그림 크기가 같으며 fov 가 같다(앞 번호 풀이 fov 고정). 앞 번호 앵커 풀이의 오차가 그대로 따라온다(⚠).
import sys, json, math, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
name, n0, n1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); Y0 = float(sys.argv[4]) if len(sys.argv) > 4 else 37.0
R = "refs/%s/" % name
a0 = json.load(open(R + "anchors/%02d.json" % n0, encoding="utf-8")); obj0 = np.array(a0["obj"], float); img0 = np.array(a0["img"], float)
im0 = cv2.imread(R + "%02d.jpg" % n0); im1 = cv2.imread(R + "%02d.jpg" % n1); H0, W0 = im0.shape[:2]
fov = int(sys.argv[5]) if len(sys.argv) > 5 else int(a0.get("fov") or json.load(open(R + "fits/%02d_P.json" % n0, encoding="utf-8")).get("fov"))
cc = obj0.mean(0); e, rv, tv, K = fit(obj0 - cc, img0, W0, H0, fov)
print("앞 번호 카메라 오차 %.2fpx fov %d" % (e, fov))
# 판 평면 점 → 앞 그림 픽셀
gx, gz = np.meshgrid(np.linspace(-70, 105, 15), np.linspace(-15, 75, 10)); P3 = np.stack([gx.ravel(), np.full(gx.size, Y0), gz.ravel()], 1)
P3 = P3[((np.abs(P3[:, 0]) <= 75) & (np.abs(P3[:, 2]) <= 15)) | ((P3[:, 0] >= 75) & (P3[:, 2] <= 75))]   # 실제 판 자리만(315프레임 + L자 39프레임) — 판 밖으로 외삽하면 오차가 커진다
px0 = cv2.projectPoints(np.float32(P3 - cc), rv, tv, K, None)[0].reshape(-1, 2)
sift = cv2.SIFT_create(4000); g0 = cv2.cvtColor(im0, cv2.COLOR_BGR2GRAY); g1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
# 평면 위 영역만 쓰기: 앞 그림에서 판 평면 점들의 볼록 껍질 안
mask0 = np.zeros(g0.shape, np.uint8); cv2.fillConvexPoly(mask0, cv2.convexHull(px0.astype(np.int32)), 255)
k0, d0 = sift.detectAndCompute(g0, mask0); k1, d1 = sift.detectAndCompute(g1, None)
m = cv2.BFMatcher().knnMatch(d0, d1, k=2); good = [x for x, y in (t for t in m if len(t) == 2) if x.distance < 0.8 * y.distance]
s = np.float32([k0[x.queryIdx].pt for x in good]); d = np.float32([k1[x.trainIdx].pt for x in good])
M, inl = cv2.findHomography(s, d, cv2.RANSAC, 3.0); ni = int(inl.sum())
res = np.linalg.norm(cv2.perspectiveTransform(s[inl.ravel() > 0][None], M)[0] - d[inl.ravel() > 0], axis=1)
print("특징점 매칭 %d · 인라이어 %d · 잔차 평균 %.2fpx 최대 %.2fpx" % (len(good), ni, res.mean(), res.max()))
px1 = cv2.perspectiveTransform(px0[None].astype(np.float32), M)[0]
# 책 그림이 잘려 있으면 주점이 한가운데가 아니다 → 주점(cx,cy)·fov 를 격자로 찾아 판 평면 점 잔차가 가장 작은 것을 고른다
from pnp import cam_from
best = None; ccp = P3.mean(0)
for f_ in range(max(14, fov - 14), fov + 15, 4):
    for cx in range(int(W0 / 2) - 240, int(W0 / 2) + 241, 40):
        for cy in range(int(H0 / 2) - 240, int(H0 / 2) + 241, 40):
            r = fit(P3 - ccp, px1, W0, H0, f_, cx, cy)
            if r:
                e2, rv2, tv2, K2 = r; C2, fwd2, up2, right2 = cam_from(rv2, tv2)
                if up2[1] > 0 and (best is None or e2 < best[0]): best = (e2, f_, cx, cy)
print("주점·fov 탐색 최소 잔차 %.2fpx fov %d 주점 (%d,%d)" % best)
fov, CX, CY = best[1], best[2], best[3]
out = {"cx": CX, "cy": CY, "obj": [[round(float(v), 2) for v in q] for q in P3], "img": [[round(float(v), 1) for v in q] for q in px1], "fov": fov,
       "plate": a0["plate"], "origin": a0.get("origin"),
       "name": "%d번 — %d번 책 그림과 위 판(y %g) 특징점 %d개(RANSAC 인라이어, 잔차 %.2fpx)를 맞춰 옮긴 판 평면 점 %d개, fov %d 고정(앞 번호 풀이 따름 ⚠ 앞 번호 오차가 따라옴)" % (n1, n0, Y0, ni, res.mean(), len(P3), fov)}
json.dump(out, open(R + "anchors/%02d.json" % n1, "w", encoding="utf-8"), ensure_ascii=False)
vis = im1.copy()
for q in px1: cv2.circle(vis, (int(q[0]), int(q[1])), 3, (0, 0, 255), -1)
cv2.imwrite("%s/cubo_reg_%02d.png" % (__import__("tempfile").gettempdir(), n1), vis); print("확인 그림: %s/cubo_reg_%02d.png" % (__import__("tempfile").gettempdir(), n1))
