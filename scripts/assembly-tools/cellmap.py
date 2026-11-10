# 책 링 ↔ 판 칸·줄 대조(사용자 지시 2026-11-10 — "격자를 저렇게 그리고 결합 구멍을 대충 볼 거면 왜 하나"): 격자(fits)의 목적은 책의 초록 링이 어느 판의 몇 번째 칸·몇 번째 줄 구멍인지를 숫자로 정하는 것이다.
#   python cellmap.py <이름> <번호> [--메모 "설명"]
#   하는 일: ① 책 그림에서 초록 링을 색으로 찾아 중심 픽셀을 구한다(규칙 D1 ①) ② 번호의 모든 격자(fits/NN_*.json)로 링 중심이 몇 칸·몇 줄인지 환산한다(호모그래피 역변환)
#            ③ 칸·줄 번호를 큰 글씨로 적은 "번호 대조 그림" refs/<이름>/NN_4.jpg 를 만들고 index.json idx 4 에 올릴 설명을 적는다 ④ 표로 출력한다 — 읽기 표 '링'(칸·줄)과 모델의 결합 구멍 번호를 이 숫자와 맞춘다(D2·D4·D8).
#   링 중심은 구멍 중심과 0.4칸 넘게 어긋나면 "구멍 중심 아님"으로 표시한다. 칸·줄 번호는 fits 의 번호(화면 왼쪽 위가 칸1줄1 쪽, refs_rect 그림의 번호와 같다).
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, glob
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw, ImageFont
FONTS = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\Hancom Gothic Bold.ttf"]
def font(sz):
    for p in FONTS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

def find_rings(im):
    """책 그림의 초록 링 중심 [(x, y, r)] — 초록 마스크 위 허프 원, 가까운 것은 하나로 합친다."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); m = cv2.inRange(hsv, (40, 90, 90), (85, 255, 255))
    c = cv2.HoughCircles(cv2.GaussianBlur(m, (5, 5), 1.5), cv2.HOUGH_GRADIENT, dp=1, minDist=12, param1=80, param2=14, minRadius=10, maxRadius=45)
    out = []
    md = cv2.dilate(m, np.ones((5, 5), np.uint8))
    def perim(x, y, r):   # 원 둘레 위 점 중 초록인 비율 — 링은 고리라 중심은 비어 있고 둘레가 초록이다
        a = np.linspace(0, 2 * np.pi, 72, endpoint=False); xs = np.clip((x + r * np.cos(a)).astype(int), 0, m.shape[1] - 1); ys = np.clip((y + r * np.sin(a)).astype(int), 0, m.shape[0] - 1)
        return float((md[ys, xs] > 0).mean())
    for x, y, r in sorted(([] if c is None else c[0]), key=lambda t: -perim(*t)):
        if perim(x, y, r) >= 0.6 and not any(np.hypot(x - a, y - b) < max(r, ra) * 0.9 for a, b, ra in out): out.append((float(x), float(y), float(r)))
    # 링은 고리라 원 안쪽이 비어 있다 — 안쪽이 초록으로 꽉 찬 것(화살표 몸통)은 뺀다
    keep = []
    for x, y, r in out:
        yy, xx = np.ogrid[:m.shape[0], :m.shape[1]]; inner = ((xx - x) ** 2 + (yy - y) ** 2) <= (r * 0.45) ** 2
        if (m[inner] > 0).mean() < 0.35: keep.append((x, y, r))
    return keep

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    name, N = sys.argv[1], int(sys.argv[2]); R = os.path.join(HERE, "refs", name)
    im = cv2.imread(os.path.join(R, "%02d.jpg" % N))
    if im is None: sys.exit("❌ 책 그림 없음: refs/%s/%02d.jpg" % (name, N))
    fits = []
    for f in sorted(glob.glob(os.path.join(R, "fits", "%02d_*.json" % N))):
        j = json.load(open(f, encoding="utf-8")); P = np.array([[c, r, x, y] for c, r, x, y in j["pts"]], float)
        if len(P) < 4: continue
        H, _ = cv2.findHomography(P[:, :2].astype(np.float32), P[:, 2:].astype(np.float32), 0)
        fits.append((os.path.basename(f)[3:-5], j, P, H, np.linalg.inv(H)))
    if not fits: sys.exit("❌ 이 번호에 격자(fits)가 없다 — 먼저 holefit")
    rings = find_rings(im)
    rows = []
    for i, (x, y, r) in enumerate(rings, 1):
        best = None
        for lab, j, P, H, Hi in fits:
            v = Hi @ np.array([x, y, 1.0]); v = v[:2] / v[2] if abs(v[2]) > 1e-9 else None
            if v is None: continue
            c, rr = float(v[0]), float(v[1]); inside = 0.3 <= c <= j["cols"] + 0.7 and 0.3 <= rr <= j["rows"] + 0.7
            off = float(np.hypot(c - round(c), rr - round(rr)))
            if inside and (best is None or off < best[0]): best = (off, lab, c, rr, j)
        rows.append((i, x, y, r, best))
    # 그림
    pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil); fb = font(26); fs = font(16)
    palette = [(0, 130, 255), (255, 140, 0), (160, 60, 220)]
    for k, (lab, j, P, H, Hi) in enumerate(fits):
        col = palette[k % 3]
        for c, r_, x, y in P: d.ellipse((x - 3, y - 3, x + 3, y + 3), outline=col, width=1)   # 격자 점은 작게(구멍을 가리지 않게)
        for c, r_, x, y in P:
            if c in (1, j["cols"]) and r_ in (1, j["rows"]): d.text((x + 6, y - 22), "%s%d.%d" % (lab, c, r_), fill=col, font=fs)
    for i, x, y, r, best in rows:
        d.ellipse((x - r, y - r, x + r, y + r), outline=(230, 0, 140), width=4)
        if best: off, lab, c, rr, j = best; txt = "링%d→%s %d칸 %d줄" % (i, lab, round(c), round(rr)) + ("" if off <= 0.4 else "?")
        else: txt = "링%d→판 밖" % i
        w = d.textlength(txt, font=fb); d.rectangle((x - w / 2 - 4, y + r + 3, x + w / 2 + 4, y + r + 33), fill=(255, 255, 255)); d.text((x - w / 2, y + r + 4), txt, fill=(200, 0, 120), font=fb)
    out = os.path.join(R, "%02d_4.jpg" % N); pil.save(out, quality=92)
    note = "번호 대조 — 책 링↔칸·줄: " + "; ".join(("링%d=%s %d칸 %d줄" % (i, b[1], round(b[2]), round(b[3]))) if b else ("링%d=판 밖" % i) for i, x, y, r, b in rows)
    ip = os.path.join(R, "index.json"); idx = json.load(open(ip, encoding="utf-8")); idx = [e for e in idx if not (int(e["step"]) == N and int(e["idx"]) == 4)]
    idx.append({"step": N, "idx": 4, "file": "%02d_4.jpg" % N, "note": note}); idx.sort(key=lambda e: (int(e["step"]), int(e["idx"]))); json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("═══ %s %d번 책 링 ↔ 칸·줄 (격자 %s) ═══" % (name, N, ", ".join(l for l, *_ in fits)))
    for i, x, y, r, best in rows:
        if best: off, lab, c, rr, j = best; print("  링%d 중심 (%.0f,%.0f) → 격자 %s %.2f칸 %.2f줄  → %d칸 %d줄  %s" % (i, x, y, lab, c, rr, round(c), round(rr), "" if off <= 0.4 else "⚠ 구멍 중심에서 %.2f칸 어긋남" % off))
        else: print("  링%d 중심 (%.0f,%.0f) → 어느 격자 판에도 없음(다른 부품 위·판 밖)" % (i, x, y))
    print("그림:", out, "(index.json idx 4 — DB 에 올린다)")

if __name__ == "__main__": main()
