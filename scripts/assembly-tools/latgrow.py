# 판 구멍 격자 번호 붙이기 — 모서리 4곳을 읽지 않고 밝은 구멍 블롭(흰 구멍 속)에서 격자를 키운다 (바이킹 18·19·20번, 2026-10-21)
#   python latgrow.py <이름> <번호> <시작x> <시작y> [y최소 y최대 x최소 x최대]
#     시작 점 가까운 블롭에서 시작해 이웃 두 방향(기저)을 정하고, 호모그래피로 격자 (i, j) 를 키운다(반복).
#     출력: refs/<이름>/fits/NN_lat.json  {"pts": {"i,j": [x, y]}, "n": 개수, "mean_err": px}
#   이 점들에 모델 칸·줄을 붙이는 법(PnP 로 거울·열 오프셋을 가리는 법)은 process/진행기록_viking.md 18·19번 절.
#   ※ 칸·줄 이름 대응이 거울이면 카메라가 판 아래로 풀린다 — 위에서 내려다보는 해(0.4~0.8px)만 쓴다. 열 오프셋은 평행이동이라 PnP 오차로는 안 갈리니 판 위의 다른 부품(막대·블록) 투영으로 가린다.
import sys, os, json
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def blobs(g, box):
    m = (g > 185).astype(np.uint8) * 255
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    y0, y1, x0, x1 = box
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if 8 < a < 700 and 0.3 < w / max(1, h) < 5 and y0 < cen[i][1] < y1 and x0 < cen[i][0] < x1:
            cx, cy = int(cen[i][0]), int(cen[i][1]); ring = g[max(0, cy - 15):cy + 16, max(0, cx - 15):cx + 16]
            if np.percentile(ring, 30) < 120: out.append(cen[i])
    return np.array(out)

def grow(B, O0, tol=9, rng=(range(-25, 26), range(-8, 9))):
    O = B[np.linalg.norm(B - O0, axis=1).argmin()]; d = np.linalg.norm(B - O, axis=1)
    nb = [B[k] - O for k in np.argsort(d) if 1 < d[k] < 90]; best = None
    for a in nb[:6]:
        for b in nb[:10]:
            if abs(a[0] * b[1] - a[1] * b[0]) < 0.5 * np.linalg.norm(a) * np.linalg.norm(b): continue
            dd = np.linalg.norm(B - (O + a + b), axis=1)
            if dd.min() < tol:
                s = np.linalg.norm(a) + np.linalg.norm(b)
                if best is None or s < best[0]: best = (s, a, b)
    if best is None: sys.exit("기저를 못 찾았다 — 시작 점을 판 가운데 블롭 근처로")
    _, u, v = best
    def snap(p, r):
        dd = np.linalg.norm(B - p, axis=1); j = dd.argmin(); return B[j] if dd[j] < r else None
    pts = {(0, 0): O}
    for i, j in [(1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, -1), (1, -1), (-1, 1)]:
        q = snap(O + i * u + j * v, tol)
        if q is not None: pts[(i, j)] = q
    fitH = lambda p: cv2.findHomography(np.array(list(p.keys()), np.float32), np.array(list(p.values()), np.float32), 0)[0]
    for _ in range(20):
        H = fitH(pts); new = dict(pts)
        for i in rng[0]:
            for j in rng[1]:
                if (i, j) in new: continue
                p = cv2.perspectiveTransform(np.array([[[i, j]]], np.float32), H)[0][0]; q = snap(p, tol - 2)
                if q is not None: new[(i, j)] = q
        if len(new) == len(pts): break
        pts = new
    H = fitH(pts); err = [np.linalg.norm(cv2.perspectiveTransform(np.array([[k]], np.float32), H)[0][0] - v_) for k, v_ in pts.items()]
    return pts, float(np.mean(err)), float(np.max(err))

if __name__ == "__main__":
    if len(sys.argv) < 5: sys.exit(__doc__)
    name, N, x0, y0 = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    im = cv2.imread(os.path.join(HERE, "refs", name, "%02d.jpg" % N)); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    box = tuple(float(v) for v in sys.argv[5:9]) if len(sys.argv) >= 9 else (0, g.shape[0], 0, g.shape[1])
    B = blobs(g, box); print("블롭", len(B))
    pts, me, mx = grow(B, np.array([x0, y0]))
    ks = sorted(pts); print("점 %d개 평균 %.2fpx 최대 %.2fpx  i %d~%d  j %d~%d" % (len(pts), me, mx, min(k[0] for k in ks), max(k[0] for k in ks), min(k[1] for k in ks), max(k[1] for k in ks)))
    out = os.path.join(HERE, "refs", name, "fits", "%02d_lat.json" % N)
    json.dump({"pts": {"%d,%d" % k: [float(v[0]), float(v[1])] for k, v in pts.items()}, "n": len(pts), "mean_err": me}, open(out, "w", encoding="utf-8"))
    print("저장", out)
