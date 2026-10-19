# 같은 시점 번호끼리 점 옮기기: python _xfer.py <이름> <앞번호> <번호> <x0> <x1> [TLx TLy]  — 앞 번호 fits(xyz3d·xyz3d_img)를 SIFT 유사변환(모터·판 오른쪽 특징)으로 이 번호 그림에 옮겨 fits/NN_P.json 에 쓴다(⚠ 옮긴 점). TLx TLy 를 주면 첫 점은 직접 읽은 값으로 바꾼다
import cv2, json, sys, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
n, a, b, x0, x1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
R = "refs/%s/" % n
ia = cv2.imread(R + "%02d.jpg" % a, 0); ib = cv2.imread(R + "%02d.jpg" % b, 0)
sift = cv2.SIFT_create(4000)
ma = np.zeros_like(ia); ma[60:760, x0:x1] = 255; mb = np.zeros_like(ib); mb[60:760, x0:x1] = 255
ka, da = sift.detectAndCompute(ia, ma); kb, db = sift.detectAndCompute(ib, mb)
m = cv2.BFMatcher().knnMatch(da, db, k=2); good = [p for p, q in m if p.distance < 0.75 * q.distance]
pa = np.float32([ka[g.queryIdx].pt for g in good]); pb = np.float32([kb[g.trainIdx].pt for g in good])
M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=3)
s = float(np.hypot(M[0, 0], M[1, 0])); rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
print("일치 %d / 후보 %d, 확대 %.2f, 회전 %.1f°" % (int(inl.sum()), len(good), s, rot))
f = json.load(open(R + "fits/%02d_P.json" % a, encoding="utf-8"))
img = [[float(v) for v in (M @ np.array([p[0], p[1], 1.0]))] for p in f["xyz3d_img"]]
if len(sys.argv) > 7: img[0] = [float(sys.argv[6]), float(sys.argv[7])]
g = dict(f); g["xyz3d_img"] = [[round(u, 0), round(v, 0)] for u, v in img]
g.pop("pts", None); g.pop("cols", None); g.pop("rows", None)
g["name"] = "%d번 — %d번과 같은 시점: 판 모서리 1점%s을 직접 읽고 나머지는 %d번 점을 SIFT 유사변환(확대 %.2f배·회전 %.1f°, 일치 %d개)으로 옮긴 값(±8px). 한 평면(z −2.5)이라 방향각만 믿는다(⚠ 옮긴 점)" % (b, a, "" if len(sys.argv) > 7 else "(옮김)", a, s, rot, int(inl.sum()))
json.dump(g, open(R + "fits/%02d_P.json" % b, "w", encoding="utf-8"), ensure_ascii=False)
print(g["xyz3d_img"])
