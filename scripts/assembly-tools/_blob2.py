# 어두운 판(구멍으로 흰 배경이 비치는 판)의 홀라인 — 흰 조각 격자 + 링 보정 (오토타깃 20번, 2026-10-19)
#   holefit DoG 는 구멍 안쪽 점이 판 두께 때문에 평균 3~5px 어긋나 기준(2px)에 못 미치고, _blobfit.py 는 첫 짝 4개를 못 찾을 수 있다.
#   흰 조각(구멍 뒤 배경)은 한 구멍마다 같은 방향으로 치우쳐 보이므로 한 호모그래피로는 정확히 맞는다(잔차 작음) — 단 구멍 축에서 일정하게 어긋나 있다.
#   그 어긋남은 판 윗면에 있는 초록 링(리벳 바닥 표시)이 정수 칸이 되도록 칸 좌표를 평행이동해 보정한다(링 칸은 책에서 센 값).
#   python _blob2.py <이름> <번호> <라벨> "<판 윤곽 4점 x,y;…(칸1줄1, 칸N줄1, 칸N줄M, 칸1줄M)>" <칸> <줄> "<링 픽셀 x,y→칸,줄;…>"
#   예: python _blob2.py autotarget 20 P "330,585;700,415;860,590;465,800" 5 3 "385,585>1,1;468,708>1,3;750,500>5,2"
import sys, os, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N, label, poly, cols, rows, rings = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
here = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(here, "refs", name)
C = np.float32([[float(v) for v in t.split(",")] for t in poly.split(";")])
im = cv2.imread(os.path.join(D, "%02d.jpg" % N)); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
mask = np.zeros(g.shape, np.uint8); cv2.fillPoly(mask, [C.astype(np.int32)], 255); mask = cv2.erode(mask, np.ones((7, 7), np.uint8))
AREA = int(os.environ.get("BLOB_AREA", "300")); OPEN = int(os.environ.get("BLOB_OPEN", "5"))   # 얇은 흰 조각(위 판이 비스듬히 보일 때)은 BLOB_AREA=40 BLOB_OPEN=2 처럼 낮춘다
wh = ((g > 200) & (mask > 0)).astype(np.uint8); wh = cv2.morphologyEx(wh, cv2.MORPH_OPEN, np.ones((OPEN, OPEN), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(wh)
B = np.float32([cen[i] for i in range(1, n) if st[i][4] > AREA]); print("흰 조각", len(B))
H = cv2.getPerspectiveTransform(C, np.float32([[0, 0], [cols, 0], [cols, rows], [0, rows]]))   # 픽셀 → 판 좌표(칸 가운데 = c−0.5)
best = None
for tol in (0.5, 0.4, 0.3, 0.25):
    for it in range(4):
        q = cv2.perspectiveTransform(B[None], H)[0]; src, dst = [], []
        for b, p in zip(B, q):
            c, r = round(p[0] + 0.5), round(p[1] + 0.5)
            if 1 <= c <= cols and 1 <= r <= rows and abs(p[0] + 0.5 - c) < tol and abs(p[1] + 0.5 - r) < tol: src.append(b); dst.append([c - 0.5, r - 0.5])
        if len(src) < 4: break
        H, _ = cv2.findHomography(np.float32(src), np.float32(dst), 0)
        err = float(np.mean(np.linalg.norm(cv2.perspectiveTransform(np.float32(dst)[None], np.linalg.inv(H))[0] - np.float32(src), axis=1)))
        best = (len(src), err)
print("흰 조각 배정 %d개 / %d칸, 잔차 평균 %.2fpx" % (best[0], cols * rows, best[1]))
Hi = np.linalg.inv(H)
# 링 보정: 링(판 윗면) 판 좌표가 정수 칸이 되도록 평행이동 (dc, dr)
off = []
for t in rings.split(";"):
    px, cr = t.split(">"); x, y = [float(v) for v in px.split(",")]; c, r = [float(v) for v in cr.split(",")]
    p = cv2.perspectiveTransform(np.float32([[[x, y]]]), H)[0][0]; off.append([(c - 0.5) - p[0], (r - 0.5) - p[1]]); print("링 (%g,%g) 칸 %d·줄 %d → 흰 조각 격자에서 (%.2f, %.2f)" % (x, y, c, r, p[0] + 0.5, p[1] + 0.5))
off = np.float32(off); d = off.mean(0); print("링 보정 평행이동 (칸 %.2f, 줄 %.2f), 링별 남는 오차(칸·줄) 최대 %.2f" % (d[0], d[1], float(np.abs(off - d).max())))
pts = []
for c in range(1, cols + 1):
    for r in range(1, rows + 1):
        p = cv2.perspectiveTransform(np.float32([[[c - 0.5 - d[0], r - 0.5 - d[1]]]]), Hi)[0][0]; pts.append([c, r, round(float(p[0]), 1), round(float(p[1]), 1)])
json.dump({"name": "%d번 %s — 흰 조각 격자(%d개 잔차 %.2fpx) + 링 %d개 보정(평행이동 칸 %.2f·줄 %.2f)" % (N, label, best[0], best[1], len(off), d[0], d[1]), "cols": cols, "rows": rows, "pts": pts, "est": [], "tool": "blob-lattice+ring", "found": best[0], "err_px": round(best[1], 2)}, open(os.path.join(D, "fits", "%02d_%s.json" % (N, label)), "w", encoding="utf-8"), ensure_ascii=False)
out = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
for c, r, x, y in pts: cv2.circle(out, (int(x * 2), int(y * 2)), 7, (0, 0, 255), -1); cv2.putText(out, "%d-%d" % (c, r), (int(x * 2) - 14, int(y * 2) - 12), 0, 0.6, (255, 0, 0), 2)
for b in B: cv2.circle(out, (int(b[0] * 2), int(b[1] * 2)), 5, (0, 200, 0), 2)
os.makedirs(os.path.join(D, "hf"), exist_ok=True); cv2.imwrite(os.path.join(D, "hf", "%02d_%s.png" % (N, label)), out); print("저장 fits/%02d_%s.json, hf/%02d_%s.png (눈으로 확인)" % (N, label, N, label))
