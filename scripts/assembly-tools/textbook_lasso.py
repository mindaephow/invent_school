# 교재 그림에서 "선으로 둘러싼 부분만" 남기고 나머지는 흰색으로 지운다 (올가미 자르기, 이 컴퓨터 안에서만 처리).
#   방법 A — 관리자가 그림 위에 검은 선으로 둘러싼 파일이 있을 때:
#     python textbook_lasso.py --lasso 선그린그림.png [--out 결과.png] [--scale 2] [--thr 30]
#       선그린그림.png = 교재 그림 위에 검은 선(닫힌 곡선)을 그린 스크린샷. 선 안쪽만 남긴다. 선이 끊겨 있으면 안쪽을 못 찾는다(--close 로 끊긴 틈 메움).
#   방법 B — 쪽 원본 픽셀 좌표로 다각형을 줄 때(교재 쪽은 가로 2527px):
#     python textbook_lasso.py --page <권> <쪽> --poly "x,y x,y x,y …" [--out 결과.png] [--scale 1]
#       점들을 이은 다각형 안쪽만 남기고 그 범위로 자른다. 좌표는 textbook_view.py 로 같은 범위를 잘라 본 그림의 좌표 + 범위 시작점으로 계산한다.
# 결과: 선 안쪽만 남은 PNG(바깥은 흰색) 와 마스크(_mask.png). Read 도구로 열어 본다.
import sys, os
import numpy as np, cv2

def arg(name, default=None, cast=str):
    if name in sys.argv:
        i = sys.argv.index(name)
        return cast(sys.argv[i + 1])
    return default

def from_drawn_line(path, thr, close):
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape
    line = (gray <= thr).astype(np.uint8)                      # 거의 검은색 = 그린 선(그림 속 어두운 부품과 구분하려고 임계값을 낮게 둔다)
    # 그린 선 = 화면 크기에 비해 길게 이어진 덩어리들(끊겨 있어도 가까운 조각은 모두 선으로 본다). 작은 검은 점(부품의 어두운 부분)은 버린다.
    n, lab, st, _ = cv2.connectedComponentsWithStats(line, connectivity=8)
    ln = np.zeros_like(line)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if max(w, h) >= 0.15 * max(W, H): ln[lab == i] = 1
    if not ln.any():
        raise SystemExit("그린 선을 못 찾았어요(검은 선이 끊겼거나 임계값 --thr 이 낮아요).")
    k = max(3, close)
    ln = cv2.morphologyEx(ln, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    ln = cv2.dilate(ln, np.ones((3, 3), np.uint8))
    # 선이 그림 가장자리 밖으로 나가 닫히지 않은 경우를 위해 그림 가장자리도 경계로 본다 → 선과 가장자리로 나뉜 영역들 중 가장 큰 것을 "안쪽"으로 고른다
    wall = ln.copy(); wall[0, :] = 1; wall[-1, :] = 1; wall[:, 0] = 1; wall[:, -1] = 1
    inv = (1 - wall).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    if n2 <= 1: raise SystemExit("선 안쪽 영역이 없어요.")
    big = 1 + int(np.argmax(st2[1:, cv2.CC_STAT_AREA]))
    mask = ((lab2 == big) & (ln == 0)).astype(np.uint8) * 255   # 그린 선 자체는 결과에서 지운다
    return img, mask

def from_poly(vol, page, poly_str):
    from textbook_view import fetch_page
    img = fetch_page(vol, page); H, W = img.shape[:2]
    pts = np.array([[int(float(v)) for v in p.split(",")] for p in poly_str.split()], np.int32)
    mask = np.zeros((H, W), np.uint8); cv2.fillPoly(mask, [pts], 255)
    return img, mask

def main():
    out = arg("--out")
    scale = arg("--scale", 1.0, float)
    if "--lasso" in sys.argv:
        src = arg("--lasso"); img, mask = from_drawn_line(src, arg("--thr", 30, int), arg("--close", 0, int))
        base = os.path.splitext(src)[0] + "_lasso"
    elif "--page" in sys.argv:
        i = sys.argv.index("--page"); vol, page = int(sys.argv[i + 1]), int(sys.argv[i + 2])
        img, mask = from_poly(vol, page, arg("--poly")); base = os.path.join(os.environ.get("TEMP", "."), f"cubo{vol}_p{page:03d}_lasso")
    else:
        raise SystemExit(__doc__)
    res = img.copy(); res[mask == 0] = 255
    ys, xs = np.where(mask > 0)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    res, m = res[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    if scale != 1.0:
        res = cv2.resize(res, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    out = out or (base + ".png")
    cv2.imencode(".png", res)[1].tofile(out); cv2.imencode(".png", m)[1].tofile(os.path.splitext(out)[0] + "_mask.png")
    print(f"저장: {out}  (선 안쪽 {int((mask > 0).sum())}px, 범위 {x1 - x0}×{y1 - y0})")

if __name__ == "__main__":
    main()
