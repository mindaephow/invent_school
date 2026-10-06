# 교재 참고 그림 격자 자동화(관리자 지시 2026-10-06): 로컬 MCP(refs-mcp/server.mjs)가 부르는 처리 모듈. 사람이 하던 순서 그대로다.
#   ① view   : 그림에서 부품 부분만 잘라 확대하고 자(픽셀 눈금)를 얹은 PNG 를 만든다            → 눈으로 모서리 구멍 4곳을 읽는다
#   ② fit    : 모서리 구멍 4곳(대략)에서 시작해, 그림에서 찾은 구멍 중심에 맞게 격자(원근)를 반복 보정한다 → 구멍 좌표·오차·미리보기
#   ③ render : 수평 기준 판의 가운데 줄이 가로선이 되도록 그림을 돌리고, 돌린 그림 위(NN_2)·원본 위(NN_3)에 격자를 그린다 → index.json 갱신
#   (등록 = 올리기는 server.mjs 의 refs_register 가 한다)
# 모든 좌표는 "원본 그림(refs/<이름>/NN.jpg)의 픽셀 좌표"다. 입출력은 JSON(표준입력→표준출력).
import sys, os, json
import cv2, numpy as np
from refs_grid import grid

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC = "①②③④"

def refs_dir(name): return os.path.join(HERE, "refs", name)

def load_orig(name, step):
    p = os.path.join(refs_dir(name), "%02d.jpg" % step)
    im = cv2.imread(p)
    if im is None: raise SystemExit("그림이 없어요: " + p)
    return im

def save_png(im, tag):
    out = os.path.join(os.environ.get("TEMP", HERE), "refs_auto_%s.png" % tag); cv2.imwrite(out, im); return out

# ---------- ① view ----------
def cmd_view(a):
    im = load_orig(a["name"], a["step"]); h, w = im.shape[:2]
    x0, y0, x1, y1 = a.get("bbox") or [0, 0, w, h]; x0, y0 = max(0, int(x0)), max(0, int(y0)); x1, y1 = min(w, int(x1)), min(h, int(y1))
    sc = float(a.get("scale") or 1.6); step = int(a.get("every") or 50)
    c = cv2.resize(im[y0:y1, x0:x1], None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
    for x in range(x0 - x0 % step + step, x1, step):
        X = int((x - x0) * sc); cv2.line(c, (X, 0), (X, c.shape[0]), (255, 120, 0), 1); cv2.putText(c, str(x), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    for y in range(y0 - y0 % step + step, y1, step):
        Y = int((y - y0) * sc); cv2.line(c, (0, Y), (c.shape[1], Y), (255, 120, 0), 1); cv2.putText(c, str(y), (2, Y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    return {"image": save_png(c, "view_%02d" % a["step"]), "size": [w, h], "bbox": [x0, y0, x1, y1], "note": "눈금 숫자는 원본 그림의 픽셀 좌표다(확대 배율 %.1f)." % sc}

# ---------- ② fit ----------
def detect(im, bbox=None, lo=90, hi=200, amin=250, amax=2500):
    g = cv2.GaussianBlur(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    m = ((g < hi) & (g > lo)).astype(np.uint8) * 255; m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, _, st, cen = cv2.connectedComponentsWithStats(m)
    P = np.array([cen[i] for i in range(1, n) if amin < st[i][4] < amax and st[i][2] < 90 and st[i][3] < 60], np.float32).reshape(-1, 2)
    if bbox is not None and len(P):
        x0, y0, x1, y1 = bbox; P = P[(P[:, 0] > x0) & (P[:, 0] < x1) & (P[:, 1] > y0) & (P[:, 1] < y1)]
    return P

def lattice(cols, rows): return np.array([[c, r] for c in range(cols) for r in range(rows)], np.float32)

def fit_grid(im, cols, rows, corners, lo=90, hi=200, pad=45):
    """corners = [(칸1·줄1), (끝 칸·줄1), (끝 칸·끝 줄), (칸1·끝 줄)] 의 대략적인 구멍 중심. 반환: H(격자→그림), 맞은 점 수, 평균 오차."""
    C = np.array(corners, np.float32); src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32)
    H = cv2.getPerspectiveTransform(src, C)
    bb = [C[:, 0].min() - pad, C[:, 1].min() - pad, C[:, 0].max() + pad, C[:, 1].max() + pad]
    P = detect(im, bb, lo, hi); lat = lattice(cols, rows); used = 0; err = None
    if len(P) < 6: return H, 0, None, P
    for it in range(14):
        q = cv2.perspectiveTransform(lat[None], H)[0]; D = np.linalg.norm(q[:, None, :] - P[None, :, :], axis=2); j = D.argmin(1); d = D.min(1)
        ok = d < max(8, 26 - 2 * it)
        if ok.sum() < 6: break
        H2, _ = cv2.findHomography(lat[ok], P[j][ok], cv2.RANSAC if it < 3 else 0, 6.0)
        if H2 is None: break
        H = H2; used = int(ok.sum()); err = float(d[ok].mean())
    return H, used, err, P

def project(H, cols, rows): return cv2.perspectiveTransform(lattice(cols, rows)[None], H)[0]

def draw_fit(im, H, cols, rows, P=None):
    o = im.copy(); q = project(H, cols, rows)
    for c in range(cols): cv2.polylines(o, [np.int32([q[c * rows + r] for r in range(rows)])], False, (0, 0, 255), 1, cv2.LINE_AA)
    for r in range(rows): cv2.polylines(o, [np.int32([q[c * rows + r] for c in range(cols)])], False, (0, 0, 255), 1, cv2.LINE_AA)
    for (x, y) in q: cv2.circle(o, (int(x), int(y)), 4, (0, 0, 255), -1)
    if P is not None:
        for p in P: cv2.circle(o, (int(p[0]), int(p[1])), 2, (0, 200, 0), -1)
    return o

def cmd_fit(a):
    im = load_orig(a["name"], a["step"]); cols, rows = int(a["cols"]), int(a["rows"])
    H, used, err, P = fit_grid(im, cols, rows, a["corners"], a.get("lo", 90), a.get("hi", 200))
    q = project(H, cols, rows); o = draw_fit(im, H, cols, rows, P)
    xs, ys = q[:, 0], q[:, 1]; x0, y0, x1, y1 = int(max(0, xs.min() - 40)), int(max(0, ys.min() - 40)), int(xs.max() + 40), int(ys.max() + 40)
    crop = cv2.resize(o[y0:y1, x0:x1], None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)
    n = cols * rows; conf = "높음" if (used >= 0.6 * n and err is not None and err < 4) else "보통" if used >= 0.35 * n else "낮음(눈으로 다시 읽어야 함)"
    pts = [[int(c) + 1, int(r) + 1, round(float(x), 1), round(float(y), 1)] for (c, r), (x, y) in zip(lattice(cols, rows), q)]
    corners = [pts[0][2:], pts[(cols - 1) * rows][2:], pts[n - 1][2:], pts[rows - 1][2:]]
    return {"image": save_png(crop, "fit_%02d" % a["step"]), "matched": used, "total": n, "mean_err_px": None if err is None else round(err, 2), "confidence": conf,
            "corners": corners, "pts": pts, "note": "빨강 = 격자 구멍 중심, 초록 점 = 그림에서 찾은 구멍 중심. 빨강이 구멍 한가운데에 앉았는지 눈으로 확인하고, 어긋나면 corners 를 고쳐 다시 fit 한다."}

# ---------- ③ render ----------
def level_alpha(H, cols, rows):
    rm = (rows - 1) / 2.0; a = cv2.perspectiveTransform(np.array([[[0, rm]]], np.float32), H)[0][0]; b = cv2.perspectiveTransform(np.array([[[cols - 1, rm]]], np.float32), H)[0][0]
    if b[0] < a[0]: a, b = b, a
    return float(np.degrees(np.arctan2(-(b[1] - a[1]), b[0] - a[0]))), a, b

def cmd_render(a):
    """plates = [{name, cols, rows, pts:[[칸,줄,x,y]...](원본 좌표, 4개 이상), ref:true(수평 기준 판 1개)}]
    crop = [x0,y0,x1,y1] 부품만 남길 영역(원본 좌표, 쪽 테두리·글씨를 빼고), erase = [[x0,y0,x1,y1],...] 영역 안에 끼어 있는 글씨·이름표를 흰색으로 지운다.
    저장: NN_1 = 1차 격자(잘라 낸 원본 위), NN_2 = 2차 격자(잘라 낸 그림을 수평으로 돌리고 위에 격자 + 파란 수평선). 둘 다 부품만 있다."""
    name, step = a["name"], int(a["step"]); d = refs_dir(name); im0 = load_orig(name, step); plates = a["plates"]
    im = im0.copy()
    for (ex0, ey0, ex1, ey1) in a.get("erase") or []: im[int(ey0):int(ey1), int(ex0):int(ex1)] = 255   # 글씨·이름표 지우기(가위로 부품만 추출)
    h0, w0 = im.shape[:2]; cx0, cy0, cx1, cy1 = [int(v) for v in (a.get("crop") or [0, 0, w0, h0])]; cx0, cy0, cx1, cy1 = max(0, cx0), max(0, cy0), min(w0, cx1), min(h0, cy1)
    im = im[cy0:cy1, cx0:cx1].copy(); h, w = im.shape[:2]
    def Hof(p):
        src = np.array([[c - 1, r - 1] for c, r, _, _ in p["pts"]], np.float32); dst = np.array([[x - cx0, y - cy0] for _, _, x, y in p["pts"]], np.float32); return cv2.findHomography(src, dst, 0)[0]
    ref = next((p for p in plates if p.get("ref")), None); alpha = 0.0; M = np.array([[1, 0, 0], [0, 1, 0]], np.float64); nw, nh = w, h
    if ref:
        alpha, _, _ = level_alpha(Hof(ref), ref["cols"], ref["rows"]); M = cv2.getRotationMatrix2D((w / 2, h / 2), -alpha, 1.0)
        cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * sn + w * cs) + 1, int(h * cs + w * sn) + 1; M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2   # 돌려도 잘리지 않게 캔버스를 키운다
    rot = cv2.warpAffine(im, M, (nw, nh), borderValue=(255, 255, 255)) if ref else im.copy()
    ys, xs = np.where(cv2.cvtColor(rot, cv2.COLOR_BGR2GRAY) < 245); pad = 16   # 가장자리 흰 여백은 잘라낸다
    tx0, ty0, tx1, ty1 = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(rot.shape[1], xs.max() + pad), min(rot.shape[0], ys.max() + pad)) if len(xs) else (0, 0, rot.shape[1], rot.shape[0])
    rot = rot[ty0:ty1, tx0:tx1].copy(); rh, rw = rot.shape[:2]
    def rpts(p): return [(c, r, float(M[0, 0] * (x - cx0) + M[0, 1] * (y - cy0) + M[0, 2]) - tx0, float(M[1, 0] * (x - cx0) + M[1, 1] * (y - cy0) + M[1, 2]) - ty0) for c, r, x, y in p["pts"]]
    o2 = rot.copy(); o3 = im.copy(); names = []
    for p in plates:
        o2 = grid(o2, None, p["cols"], p["rows"], None, rpts(p)); o3 = grid(o3, None, p["cols"], p["rows"], None, [(c, r, x - cx0, y - cy0) for c, r, x, y in p["pts"]]); names.append("%s %d칸×%d줄" % (p.get("name") or "판", p["cols"], p["rows"]))
    if ref:
        _, ra, rb = level_alpha(Hof(ref), ref["cols"], ref["rows"]); pa = M @ np.array([ra[0], ra[1], 1.0]); pb = M @ np.array([rb[0], rb[1], 1.0]); y0 = int(round((pa[1] + pb[1]) / 2 - ty0))
        cv2.line(o2, (0, y0), (rw, y0), (255, 140, 0), 2, cv2.LINE_AA); cv2.putText(o2, "horizontal", (rw - 130, y0 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 140, 0), 2)
    # 등록은 2장만(관리자 지시 2026-10-06): NN_1 = 1차 격자(원본 위, ②), NN_2 = 2차 격자(돌린 그림 위 + 파란 수평선, ④). 돌리기만 한 그림·순수 원본은 만들지도 올리지도 않는다(원본 NN.jpg 는 작업 재료로만 둔다).
    cv2.imwrite(os.path.join(d, "%02d_1.jpg" % step), o3, [cv2.IMWRITE_JPEG_QUALITY, 82]); cv2.imwrite(os.path.join(d, "%02d_2.jpg" % step), o2, [cv2.IMWRITE_JPEG_QUALITY, 82])
    p3 = os.path.join(d, "%02d_3.jpg" % step)
    if os.path.exists(p3): os.remove(p3)
    ip = os.path.join(d, "index.json"); index = json.load(open(ip, encoding="utf-8")); index = [r for r in index if not (r["step"] == step and r["idx"] in (1, 2, 3))]
    nm = " / ".join(names); extra = a.get("note", "")
    index += [{"step": step, "idx": 1, "file": "%02d_1.jpg" % step, "note": "② 단계 %d — 부품만 잘라 낸 원본 그림(돌리기 전, 원근 그대로) 위의 1차 격자(빨강 = 구멍 중심, 위 숫자 = 칸, 왼쪽 숫자 = 줄): %s. %s" % (step, nm, extra)},
              {"step": step, "idx": 2, "file": "%02d_2.jpg" % step, "names": names, "note": "④ 단계 %d — 판의 긴 방향이 수평이 되게 %.1f° 돌린 그림 위의 2차 격자: %s. 파란 가로선 = 판 가운데 줄을 수평으로 맞춘 기준선. 그림 속 구멍을 찾아 맞춘 좌표라 추정이다. %s" % (step, alpha, nm, extra)}]
    index.sort(key=lambda r: (r["step"], r["idx"])); json.dump(index, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gp = os.path.join(d, "grids_orig.json"); G = json.load(open(gp, encoding="utf-8")) if os.path.exists(gp) else []
    G = [g for g in G if g["step"] != step] + [{"step": step, "name": p.get("name") or "판", "cols": p["cols"], "rows": p["rows"], "pts": p["pts"], "ref": bool(p.get("ref")), "crop": [cx0, cy0, cx1, cy1], "erase": a.get("erase") or []} for p in plates]
    json.dump(G, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"rotated_deg": round(alpha, 2), "files": ["%02d_1.jpg" % step, "%02d_2.jpg" % step], "preview": os.path.join(d, "%02d_2.jpg" % step), "original_preview": os.path.join(d, "%02d_1.jpg" % step)}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); a = json.loads(sys.stdin.read() or "{}")
    print(json.dumps({"view": cmd_view, "fit": cmd_fit, "render": cmd_render}[sys.argv[1]](a), ensure_ascii=False))
