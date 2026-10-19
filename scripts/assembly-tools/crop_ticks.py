# 책 그림의 한 부분을 확대하고 원본 좌표 눈금(20px 간격 숫자, 10px 간격 선)을 얹은 그림을 만든다 — 판 바깥 모서리 4곳(holefit 입력)·링 중심·부품 위치를 "눈으로 읽을 때" 쓴다(2026-10-13).
#   python crop_ticks.py <이름> <번호> x0 y0 x1 y1 [배율=4] [눈금=10]      → 만든 그림 경로를 출력한다(Read 로 열어 본다)
#   python crop_ticks.py <이름> <번호> corners x1 y1 x2 y2 x3 y3 x4 y4 [반폭=35]  → 네 점 주변 반폭×2 정사각형 4장을 한 장(2×2)으로 — 모서리 읽기 확인용
# 읽은 좌표는 원본 그림(refs/<이름>/NN.jpg) 좌표다(눈금 숫자 그대로). 한 번에 보이는 범위를 작게(≤ 100×100px) 잡을수록 ±2px 로 읽힌다.
# 함정: 결과는 짧은 임시 폴더(%TEMP%/cubo_crops)에 쓴다 — 프로젝트 안 긴 경로나 한글 경로에 cv2.imwrite 하면 윈도우에서 조용히 실패한다.
import sys, os, tempfile
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def tile(im, x0, y0, x1, y1, s, step):
    x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(im.shape[1], int(x1)), min(im.shape[0], int(y1))
    c = cv2.resize(im[y0:y1, x0:x1], None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    for x in range((x0 // step + 1) * step, x1, step):
        X = int((x - x0) * s); cv2.line(c, (X, 0), (X, c.shape[0]), (0, 200, 255) if x % 50 else (0, 0, 255), 1)
        if x % 20 == 0: cv2.putText(c, str(x), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    for y in range((y0 // step + 1) * step, y1, step):
        Y = int((y - y0) * s); cv2.line(c, (0, Y), (c.shape[1], Y), (0, 200, 255) if y % 50 else (0, 0, 255), 1)
        if y % 20 == 0: cv2.putText(c, str(y), (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    return c

def main():
    a = sys.argv[1:]
    if len(a) < 4: sys.exit(__doc__)
    name, step = a[0], int(a[1])
    im = cv2.imread(os.path.join(HERE, "refs", name, "%02d.jpg" % step))
    if im is None: sys.exit("책 그림이 없다: refs/%s/%02d.jpg" % (name, step))
    out_dir = os.path.join(tempfile.gettempdir(), "cubo_crops"); os.makedirs(out_dir, exist_ok=True)
    if a[2] == "corners":
        pts = [float(v) for v in a[3:11]]; hw = float(a[11]) if len(a) > 11 else 35.0
        tiles = [tile(im, px - hw, py - hw, px + hw, py + hw, 5, 10) for px, py in zip(pts[0::2], pts[1::2])]
        h = max(t.shape[0] for t in tiles); w = max(t.shape[1] for t in tiles)
        tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, w - t.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles]
        c = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])]); path = os.path.join(out_dir, "%s_%02d_corners.png" % (name, step))
    else:
        x0, y0, x1, y1 = [float(v) for v in a[2:6]]; s = float(a[6]) if len(a) > 6 else 4.0; st = int(a[7]) if len(a) > 7 else 10
        c = tile(im, x0, y0, x1, y1, s, st); path = os.path.join(out_dir, "%s_%02d_%d_%d.png" % (name, step, x0, y0))
    ok, buf = cv2.imencode(".png", c)
    if not ok: sys.exit("그림을 못 만들었다")
    buf.tofile(path); print(path, "(%dx%d)" % (c.shape[1], c.shape[0]))

main()
