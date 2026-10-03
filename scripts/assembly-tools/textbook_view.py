# 교재 쪽의 필요한 곳만 크게 잘라 보고, 흰 구멍을 자동으로 찾아 번호를 붙인다.
#   python textbook_view.py <권> <쪽> [x0 y0 x1 y1] [--scale 2] [--holes] [--out 경로.png]
#   x0 y0 x1 y1 = 쪽 전체를 0~1 로 본 비율(왼쪽 위 → 오른쪽 아래). 생략하면 쪽 전체.
#   결과 PNG 경로가 출력된다 → Read 도구로 열어 본다.  --holes 를 주면 흰 구멍에 번호를 그리고 위치 목록도 출력한다.
# 쪽 이미지는 MCP 의 upload_textbook_page 로 올려 둔 원본 해상도 파일(가로 2524px)이다(올리는 법: textbook_pages.py).
#
# --holes 방법(사용자 설명: 구멍은 하얗고 동그란 것이라 부품과 확실히 다르다):
#   종이 바탕(쪽 가장자리와 이어진 흰색)을 뺀 "부품 덩어리" 안에 갇힌 흰 덩어리 중 크기·동그란 정도가 맞는 것 = 구멍 후보.
#   비스듬히 그려져 찌그러진 타원도 받는다. 흰색·연한 회색 부품 위의 구멍은 못 찾을 수 있다 → 번호 그림을 눈으로 확인한다.
import sys, os, urllib.request, tempfile
import numpy as np, cv2

BASE = "https://brfeszcyjsaprbakqsjl.supabase.co/storage/v1/object/public/textbook-files/pages"

def fetch_page(volume, page):
    url = f"{BASE}/cubo{volume}/p{page:03d}.jpg"
    cache = os.path.join(tempfile.gettempdir(), f"cubo{volume}_p{page:03d}.jpg")
    if not os.path.exists(cache):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
        except Exception as e:
            print(f"{volume}권 {page}쪽 이미지를 못 받았어요({e}). 안 올라가 있으면 textbook_pages.py upload 로 올린다."); sys.exit(1)
        open(cache, "wb").write(data)
    return cv2.imdecode(np.fromfile(cache, dtype=np.uint8), cv2.IMREAD_COLOR)

def find_holes(img):
    """부품 안의 구멍 후보 [(cx, cy, 가로, 세로), ...] (이미지 픽셀).
    구멍 안쪽은 흰색~연한 회색이라 둘레 부품 면보다 밝다 → 주변 평균보다 밝은 덩어리 중 타원 모양이고 둘레가 어두운 것."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    H, W = gray.shape
    # 종이 바탕 = 쪽 가장자리와 이어진 아주 밝은 영역
    paper = (gray > 225).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(paper, connectivity=4)
    bg = np.zeros_like(paper)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if x == 0 or y == 0 or x + w >= W or y + h >= H:
            bg[lab == i] = 1
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] > 35) & (hsv[..., 0] < 90) & (hsv[..., 1] > 80)).astype(np.uint8)  # 초록 안내 원·선은 구멍이 아님
    loc = cv2.GaussianBlur(gray, (0, 0), 18)
    cand = (((gray - loc) > 8) & (gray > 95) & (bg == 0) & (green == 0)).astype(np.uint8)
    cand = cv2.morphologyEx(cand, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(cand, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if not (80 <= area <= 5000) or min(w, h) < 8:  # 글자·점 같은 작은 것 제외
            continue
        ar = max(w, h) / max(1, min(w, h))
        fill = area / (np.pi / 4 * w * h)
        if ar > 3.2 or fill < 0.72:
            continue
        # 둘레(한 겹 바깥)가 안쪽보다 확실히 어두워야 한다 — 구멍은 어두운 테두리 안의 밝은 면
        pad = 5
        y0, y1, x0, x1 = max(0, y - pad), min(H, y + h + pad), max(0, x - pad), min(W, x + w + pad)
        inner = gray[y0:y1, x0:x1][lab[y0:y1, x0:x1] == i]
        ring = (lab[y0:y1, x0:x1] != i)
        ringpix = gray[y0:y1, x0:x1][ring]
        if inner.size == 0 or ringpix.size < 20:
            continue
        if np.mean(ringpix) > np.mean(inner) - 18 or np.mean(green[y0:y1, x0:x1][ring]) > 0.2:
            continue
        out.append((float(cen[i][0]), float(cen[i][1]), float(w), float(h)))
    return out

def find_marks(img):
    """교재의 초록 안내 원(꽂을 구멍 표시) 중심 [(cx, cy, 가로, 세로), ...] — 속이 빈 초록 고리(타원)만.
    안내선(가는 초록 선)이 고리에 붙어 있어도 되도록, 5px 열기로 선을 얇게 지우고 고리의 안쪽 구멍을 기준으로 잰다."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    g = ((hsv[..., 0] > 47) & (hsv[..., 0] < 73) & (hsv[..., 1] > 40) & (hsv[..., 2] > 60)).astype(np.uint8) * 255  # 안내 원 색: 색상 50~69, 채도 50~140, 밝기 75~185 (66쪽에서 잼; 연두색 쪽 테두리는 색상 ~38 이라 제외)
    g = cv2.morphologyEx(g, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    g = cv2.morphologyEx(g, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, hier = cv2.findContours(g, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    if hier is None:
        return out
    for i, c in enumerate(cnts):
        child = hier[0][i][2]
        if hier[0][i][3] != -1 or child == -1:  # 바깥 윤곽이면서 안쪽 구멍(고리)이 있는 것
            continue
        # 안쪽 구멍이 여럿이면(선이 고리를 가르는 경우) 가장 큰 것
        holes = []
        k = child
        while k != -1:
            holes.append(k); k = hier[0][k][0]
        k = max(holes, key=lambda q: cv2.contourArea(cnts[q]))
        x, y, w, h = cv2.boundingRect(cnts[k])
        if not (10 <= w <= 70 and 6 <= h <= 70) or max(w, h) / max(1, min(w, h)) > 3.5:
            continue
        m = cv2.moments(cnts[k])
        if m["m00"] <= 0:
            continue
        out.append((m["m10"] / m["m00"], m["m01"] / m["m00"], float(w + 8), float(h + 8)))
    return out

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    a = [x for x in sys.argv[1:]]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    holes = "--holes" in a
    scale = 2.0; out = None
    if "--scale" in a: i = a.index("--scale"); scale = float(a[i + 1]); del a[i:i + 2]
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    a = [x for x in a if x != "--holes"]
    volume, page = int(a[0]), int(a[1])
    box = [float(v) for v in a[2:6]] if len(a) >= 6 else [0.0, 0.0, 1.0, 1.0]
    img = fetch_page(volume, page)
    H, W = img.shape[:2]
    x0, y0, x1, y1 = int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)
    crop = img[y0:y1, x0:x1].copy()
    found = []
    marks = []
    if holes:
        marks = find_marks(crop)
        found = find_holes(crop)
        # 왼쪽→오른쪽, 위→아래 순서(교재 스캔 절차)로 번호
        found.sort(key=lambda f: (round(f[1] / 40), f[0]))
        for k, (cx, cy, mj, mn) in enumerate(found, 1):
            cv2.ellipse(crop, ((cx, cy), (mj + 6, mn + 6), 0.0), (0, 160, 0), 2)
            cv2.putText(crop, str(k), (int(cx - 6), int(cy + 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1, cv2.LINE_AA)
    for k, (cx, cy, mj, mn) in enumerate(marks, 1):
        cv2.putText(crop, "M" + str(k), (int(cx + mj / 2 + 3), int(cy - mn / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 0, 0), 2, cv2.LINE_AA)
    if scale != 1.0:
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    path = out or os.path.join(tempfile.gettempdir(), f"cubo{volume}_p{page:03d}_view.png")
    cv2.imencode(".png", crop)[1].tofile(path)
    print(f"저장: {path}  (원본 {W}×{H}px 중 {x1 - x0}×{y1 - y0}px 를 {scale}배)")
    if holes:
        print(f"흰 구멍 후보 {len(found)}개 (번호 = 왼쪽→오른쪽, 위→아래; 잘라낸 그림 안 좌표, 원본 픽셀):")
        for k, (cx, cy, mj, mn) in enumerate(found, 1):
            print(f"  {k:>3}: ({x0 + cx:.0f}, {y0 + cy:.0f})  크기 {mj:.0f}×{mn:.0f}px")
        print(f"교재의 초록 안내 원 {len(marks)}개 (그림의 M번호; 초록 고리만 찾는다 — 66쪽 14단계 7/7, 12단계 2/2 확인):")
        for k, (cx, cy, mj, mn) in enumerate(marks, 1):
            near = sorted(range(len(found)), key=lambda q: (found[q][0] - cx) ** 2 + (found[q][1] - cy) ** 2)[:1]
            q = near[0] if near else None
            d = ((found[q][0] - cx) ** 2 + (found[q][1] - cy) ** 2) ** 0.5 / max(1.0, found[q][2]) if q is not None else 99
            if d <= 1.2:
                print(f"  M{k}: ({x0 + cx:.0f}, {y0 + cy:.0f}) → 구멍 {q + 1}번 (거리 {d:.1f})")
            else:
                print(f"  M{k}: ({x0 + cx:.0f}, {y0 + cy:.0f}) → 근처에서 구멍을 못 찾음(이 그림은 구멍 검출이 안 되는 부분 — 그림을 눈으로 세어 본다)")
        print("※ 흰 구멍을 찾는 방식이라 순백으로 날아간 구멍·아주 납작하게 보이는 구멍·가려진 구멍은 빠질 수 있다(긴 프레임도 일부 빠짐). 구멍 번호는 참고만 하고 번호 그림(M 표시 포함)을 눈으로 확인한다.")

if __name__ == "__main__":
    main()
