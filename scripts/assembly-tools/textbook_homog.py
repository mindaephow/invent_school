# 교재 그림에서 판 하나의 구멍 격자를 원근(호모그래피)으로 맞추고, 점들이 몇 열·몇 줄 칸인지 계산한다 (가위로 판을 오려서 사용).
#   from textbook_homog import plate_grid
#   g = plate_grid(vol, page, box, pt, neg, cols, rows)   → 격자 객체 (cell(p) = 점 p 의 (열, 줄) 실수 칸 좌표)
# 방향(어느 끝이 열1·어느 쪽이 줄1)은 판 사각형 네 모서리의 가능한 8가지 대응 중 구멍이 가장 잘 맞는 것을 고르되, 대칭이라 같은 점수가 나오면 "모호"로 알린다.
import numpy as np, cv2, itertools
from textbook_view import fetch_page, find_holes
from textbook_cut import cut

class Grid:
    def __init__(s, H, cols, rows, res, nholes, amb): s.H, s.cols, s.rows, s.res, s.nholes, s.amb = H, cols, rows, res, nholes, amb
    def cell(s, p):
        v = s.H @ np.array([p[0], p[1], 1.0]); return v[:2] / v[2]
    def idx(s, p):
        c = s.cell(p); return int(np.floor(c[0])), int(np.floor(c[1]))

def plate_grid(vol, page, box, pt, neg, cols, rows):
    img = fetch_page(vol, page); H, W = img.shape[:2]
    x0, y0, x1, y1 = int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)
    crop = img[y0:y1, x0:x1]
    m, iou = cut(crop, [(pt[0] - x0, pt[1] - y0)], [(n[0] - x0, n[1] - y0) for n in neg])
    cnt = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea)
    rect = cv2.minAreaRect(cnt); box4 = cv2.boxPoints(rect)
    hs = find_holes(crop)
    if hs:
        med = np.median([max(h[2], h[3]) for h in hs]); hs = [h for h in hs if max(h[2], h[3]) >= 0.7 * med]
    holes = np.array([(h[0], h[1]) for h in hs if m[int(h[1]), int(h[0])] > 0], np.float32)
    # 긴 변 방향을 열 방향으로: 사각형의 두 변 중 긴 쪽
    e = [np.linalg.norm(box4[(i + 1) % 4] - box4[i]) for i in range(4)]
    best = None; allres = []
    base = [box4[i] for i in range(4)]
    for k in range(4):
        for flip in (False, True):
            pts = base[k:] + base[:k]
            if flip: pts = [pts[0], pts[3], pts[2], pts[1]]
            L = np.linalg.norm(pts[1] - pts[0]); Wd = np.linalg.norm(pts[3] - pts[0])
            if (cols >= rows) != (L >= Wd): continue    # 열이 긴 쪽이어야(rows>cols 이면 반대)
            src = np.array(pts, np.float32); dst = np.array([[0, 0], [cols, 0], [cols, rows], [0, rows]], np.float32)
            Hm, _ = cv2.findHomography(src, dst)
            for it in range(8):
                c = np.array([cv2.perspectiveTransform(np.array([[p]], np.float32), Hm)[0, 0] for p in holes]); idx = np.floor(c).astype(int)
                ok = (idx[:, 0] >= 0) & (idx[:, 0] < cols) & (idx[:, 1] >= 0) & (idx[:, 1] < rows)
                if ok.sum() < 4: break
                Hn, _ = cv2.findHomography(holes[ok], (idx + 0.5)[ok].astype(np.float32), cv2.RANSAC, 0.3)
                if Hn is None: break
                Hm = Hn
            c = np.array([cv2.perspectiveTransform(np.array([[p]], np.float32), Hm)[0, 0] for p in holes])
            r = float(np.abs(c - (np.floor(c) + 0.5)).max(1).mean()) if len(c) else 9
            allres.append((r, k, flip, Hm))
    allres.sort(key=lambda t: t[0])
    amb = sum(1 for t in allres if t[0] - allres[0][0] < 0.01)
    r, k, flip, Hm = allres[0]
    return Grid(Hm, cols, rows, r, len(holes), amb), m, crop, (x0, y0)
