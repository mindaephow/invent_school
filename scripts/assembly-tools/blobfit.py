# 구멍 흰 부분(슬리버)을 검출해 칸×줄 격자 노드에 배정하고 fits/NN_<라벨>.json 으로 저장한다 (refs_rect.py 의 입력).
#   python blobfit.py <이름> <번호> <라벨> <칸> <줄> x0 y0 x1 y1  c1r1x c1r1y  cNr1x cNr1y  cNrMx cNrMy  c1rMx c1rMy
#   (x0..y1 = 판이 있는 영역(원본 좌표), 뒤 8개 = 모서리 4곳 대략 위치(칸1줄1, 칸N줄1, 칸N줄M, 칸1줄M) — 눈으로 대략만 읽어도 된다. 검출점에 맞춰 반복 보정)
import sys, os, json
import cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
name, step, label, cols, rows = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
x0, y0, x1, y1 = [int(float(v)) for v in sys.argv[6:10]]; cr = [float(v) for v in sys.argv[10:18]]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', name) + os.sep
im = cv2.imread(D + '%02d.jpg' % step); c = im[y0:y1, x0:x1]; g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
thr = int(os.environ.get('BF_THR', 200))
m = ((g > thr) & ~((hsv[..., 0] > 30) & (hsv[..., 0] < 90) & (hsv[..., 1] > 50))).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(m); B = []
for i in range(1, n):
    a = st[i, 4]; x, y, w, h = st[i, :4]
    if 30 < a < 2500 and x > 0 and y > 0 and x + w < c.shape[1] and y + h < c.shape[0]:
        px0, py0, px1, py1 = max(0, x - 6), max(0, y - 6), min(c.shape[1], x + w + 6), min(c.shape[0], y + h + 6)
        ring = g[py0:py1, px0:px1][m[py0:py1, px0:px1] == 0]
        if ring.size and np.percentile(ring, 25) < float(os.environ.get('BF_RING', 120)): B.append([cen[i][0] + x0, cen[i][1] + y0])
B = np.array(B, np.float64); print('검출 구멍', len(B))
src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32); H = cv2.getPerspectiveTransform(src, np.array(cr, np.float32).reshape(4, 2))
lat = [(cc, rr) for cc in range(cols) for rr in range(rows)]; L = np.array(lat, np.float32)
match = {}
for it in range(8):
    P = cv2.perspectiveTransform(L[None], H)[0]; pitch = np.median([np.hypot(*(P[i] - P[j])) for i in range(len(P)) for j in range(len(P)) if abs(lat[i][0] - lat[j][0]) + abs(lat[i][1] - lat[j][1]) == 1]) if len(P) > 1 else 30
    match = {}
    for bi, b in enumerate(B):
        d = np.hypot(*(P - b).T); k = int(d.argmin())
        if d[k] < 0.45 * pitch and (k not in match or d[k] < match[k][1]): match[k] = (bi, d[k])
    if len(match) < 4: print('매칭 부족', len(match)); break
    ks = list(match); H2, _ = cv2.findHomography(L[ks], np.array([B[match[k][0]] for k in ks], np.float32), cv2.LMEDS)
    if H2 is None: break
    H = H2
P = cv2.perspectiveTransform(L[None], H)[0]
err = float(np.mean([match[k][1] for k in match])) if match else None
print('매칭', len(match), '/', cols * rows, '평균오차px', None if err is None else round(err, 2))
keep = list(match) if len(match) >= 0.5 * cols * rows else list(range(len(lat)))
pts = [[lat[k][0] + 1, lat[k][1] + 1, round(float(P[k][0]), 1), round(float(P[k][1]), 1)] for k in range(len(lat)) if k in keep]
os.makedirs(D + 'fits', exist_ok=True); json.dump({'cols': cols, 'rows': rows, 'pts': pts, 'corners': [[round(float(v), 1) for v in P[i]] for i in (0, (cols - 1) * rows, cols * rows - 1, rows - 1)]}, open(D + 'fits/%02d_%s.json' % (step, label), 'w'))
vis = im.copy()
for k in range(len(lat)):
    col = (0, 0, 255) if k in match else (255, 0, 0)
    cv2.circle(vis, (int(P[k][0]), int(P[k][1])), 4, col, -1)
for b in B: cv2.circle(vis, (int(b[0]), int(b[1])), 2, (0, 200, 0), -1)
ys, xs = P[:, 1], P[:, 0]; cv2.imwrite(os.environ.get('TEMP', '.') + '/bf_%02d.png' % step, vis[int(max(0, ys.min() - 40)):int(ys.max() + 40), int(max(0, xs.min() - 40)):int(xs.max() + 40)])
