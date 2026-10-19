# 판의 구멍으로 비쳐 보이는 흰 조각(blob)의 중심으로 홀라인 격자를 맞춘다 — DoG 점이 구멍 가장자리에 앉는 holefit 의 약점 대신(오토타깃 5번, 2026-10-18). 같은 평면의 두 판(막대·검은 판)을 한 호모그래피로 맞추고 잔차(px)를 낸다.
#   python _blobfit.py <이름> <번호> "<막대 윤곽 x,y;x,y;x,y;x,y>" <칸> <줄> ["<다른 판 윤곽>"]
import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N, poly, cols, rows = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
polys = [np.array([[float(v) for v in t.split(",")] for t in p.split(";")], np.float32) for p in ([poly] + sys.argv[6:])]
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
mask = np.zeros(g.shape, np.uint8)
for p in polys: cv2.fillPoly(mask, [p.astype(np.int32)], 255)
mask = cv2.erode(mask, np.ones((9, 9), np.uint8))
wh = ((g > 200) & (mask > 0)).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(wh)
B = np.array([cen[i] for i in range(1, n) if 20 < st[i][4] < 600], np.float32)
print("흰 조각", len(B))
# 초기 호모그래피: 막대 윤곽 모서리 → 칸 좌표(구멍 가운데 = c−0.5). 왼쪽(원근이 덜한 쪽) 칸부터 조각을 짝지어 맞추고 칸을 한 칸씩 늘려 가며 다시 맞춘다
C = polys[0]; H = cv2.getPerspectiveTransform(C, np.float32([[0, 0], [cols, 0], [cols, rows], [0, rows]]))
def assign(H, cmax, tol):
    pr = cv2.perspectiveTransform(B[None], H)[0]; src, dst = [], []
    for b, q in zip(B, pr):
        c, r = round(q[0] + 0.5), round(q[1] + 0.5)
        if 1 <= c <= cmax and 1 <= r <= rows and abs(q[0] + 0.5 - c) < tol and abs(q[1] + 0.5 - r) < tol: src.append(b); dst.append([c - 0.5, r - 0.5])
    return np.float32(src), np.float32(dst)
for cmax in list(range(4, cols + 1)):
    for it in range(3):
        src, dst = assign(H, cmax, 0.40 if it == 0 else 0.28)
        if len(src) >= 8:
            H2, inl = cv2.findHomography(src, dst, cv2.RANSAC, 1.2)
            if H2 is not None: H = H2
src, dst = assign(H, cols, 0.28)
H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 1.2); src, dst = assign(H, cols, 0.25)
Hi = np.linalg.inv(H)
d = np.float32(dst); back = cv2.perspectiveTransform(d[None], Hi)[0]; err = np.hypot(*(back - np.float32(src)).T)
print("배정 %d개 / %d칸 | 오차 평균 %.2fpx 최대 %.2fpx" % (len(src), cols * rows, err.mean(), err.max()))
json.dump({"H": H.tolist(), "n": len(src), "err_mean": float(err.mean()), "err_max": float(err.max())}, open("refs/%s/anchors/%02d_blob.json" % (name, N), "w"))
out = im.copy()
for c in range(1, cols + 1):
    for r in range(1, rows + 1): cv2.circle(out, tuple(int(v) for v in cv2.perspectiveTransform(np.float32([[[c - .5, r - .5]]]), Hi)[0][0]), 4, (0, 0, 255), -1)
for b in B: cv2.circle(out, (int(b[0]), int(b[1])), 6, (0, 200, 0), 1)
cv2.imwrite("refs/%s/hf/%02d_blob.png" % (name, N), out)
