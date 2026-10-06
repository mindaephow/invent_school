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

def fit_grid(im, cols, rows, corners, lo=90, hi=200, pad=45, amin=250):
    """corners = [(칸1·줄1), (끝 칸·줄1), (끝 칸·끝 줄), (칸1·끝 줄)] 의 대략적인 구멍 중심. 반환: H(격자→그림), 맞은 점 수, 평균 오차."""
    C = np.array(corners, np.float32); src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32)
    H = cv2.getPerspectiveTransform(src, C)
    bb = [C[:, 0].min() - pad, C[:, 1].min() - pad, C[:, 0].max() + pad, C[:, 1].max() + pad]
    P = detect(im, bb, lo, hi, amin); lat = lattice(cols, rows); used = 0; err = None
    if len(P) < 6: return H, 0, None, P
    for it in range(14):
        q = cv2.perspectiveTransform(lat[None], H)[0]; D = np.linalg.norm(q[:, None, :] - P[None, :, :], axis=2); j = D.argmin(1); d = D.min(1)
        ok = d < max(8, 26 - 2 * it)
        if ok.sum() < 6: break
        H2, _ = cv2.findHomography(lat[ok], P[j][ok], cv2.RANSAC if it < 3 else 0, 6.0)
        if H2 is None: break
        H = H2; used = int(ok.sum()); err = float(d[ok].mean())
    return H, used, err, P


# ---------- ②-b autofit: 모서리를 읽지 않고 검출된 구멍들을 격자로 자동 연결 ----------
def auto_fit(im, cols, rows, bbox, lo=200, hi=256, amin=30, col_start=1, row_start=1, flip_cols=False, flip_rows=False):
    """bbox 안에서 검출된 구멍 중심들을 이웃끼리 이어(BFS) 정수 격자 좌표를 매기고, 호모그래피를 맞춘다.
    col_start/row_start = 검출된 가장 왼쪽·위 구멍이 판의 몇 번째 칸·줄인지(가려져서 1이 아닐 때). flip_* = 번호가 오른쪽→왼쪽, 아래→위로 늘어날 때.
    반환: H(판 번호 → 그림), 연결된 점 수, 평균 오차, 검출점. 실패하면 H=None."""
    P = detect(im, bbox, lo, hi, amin)
    if len(P) < 6: return None, 0, None, P
    P = P.astype(np.float64); n = len(P)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2); np.fill_diagonal(D, 1e9)
    nn = np.sort(D, axis=1)[:, :4]; unit = float(np.median(nn[:, 0]))   # 이웃 간격(대표값)
    best = None
    for seed in np.argsort(D.min(axis=1))[:: max(1, n // 12)][:12]:   # 여러 시작점으로 시도해 가장 큰 연결을 고른다
        near = np.argsort(D[seed])[:6]; vecs = [P[j] - P[seed] for j in near if D[seed, j] < 1.6 * unit]
        if len(vecs) < 2: continue
        a = vecs[0]; b = None
        for v in vecs[1:]:
            c = abs(a[0] * v[1] - a[1] * v[0]) / (np.linalg.norm(a) * np.linalg.norm(v) + 1e-9)
            if c > 0.45 and np.dot(a, v) > -0.1 * np.linalg.norm(a) * np.linalg.norm(v) or c > 0.45: b = v; break
        if b is None: continue
        idx = {int(seed): (0, 0)}; step = {(1, 0): a, (0, 1): b, (-1, 0): -a, (0, -1): -b}; q = [int(seed)]; pos = {(0, 0): int(seed)}
        while q:
            k = q.pop(0); ci, cj = idx[k]
            for (di, dj), vec in step.items():
                tgt = (ci + di, cj + dj)
                if tgt in pos: continue
                # 예측: 이미 이어진 반대편 이웃과의 간격(원근에 따라 서서히 변함)을 쓴다
                back = pos.get((ci - di, cj - dj)); v = (P[k] - P[back]) if back is not None else vec
                pred = P[k] + v; d = np.linalg.norm(P - pred, axis=1); m = int(d.argmin())
                if d[m] < 0.38 * np.linalg.norm(v) and m not in idx: idx[m] = tgt; pos[tgt] = m; q.append(m)
        if best is None or len(idx) > len(best): best = idx
    if best is None or len(best) < 6: return None, len(best or {}), None, P
    ii = np.array([v[0] for v in best.values()]); jj = np.array([v[1] for v in best.values()]); pts = P[list(best.keys())]
    # 어느 축이 칸(긴 쪽)인지: 연결된 격자에서 더 많이 뻗은 축
    ei, ej = ii.max() - ii.min() + 1, jj.max() - jj.min() + 1; cols_is_i = ei >= ej
    # 검증: 이어진 격자의 크기가 판(칸×줄)을 넘으면 구멍이 아닌 것을 이은 것이다 → 거절
    if max(ei, ej) > max(cols, rows) or min(ei, ej) > min(cols, rows): return None, len(best), None, P
    ci_, ri_ = (ii, jj) if cols_is_i else (jj, ii)
    # 번호 방향: 기본 = 칸은 왼쪽→오른쪽, 줄은 위→아래(그림 좌표 기준). 축 부호를 평균 이동 방향으로 맞춘다
    def sign_along(idxs, axis_x):
        # idxs 가 늘어날 때 x(또는 y)가 늘어나는지
        A = np.vstack([idxs, np.ones_like(idxs)]).T; coef = np.linalg.lstsq(A, pts[:, 0 if axis_x else 1], rcond=None)[0][0]; return 1 if coef >= 0 else -1
    cs = sign_along(ci_.astype(float), True); rs = sign_along(ri_.astype(float), False)
    if flip_cols: cs = -cs
    if flip_rows: rs = -rs
    C = (ci_ - ci_.min()) if cs > 0 else (ci_.max() - ci_); R = (ri_ - ri_.min()) if rs > 0 else (ri_.max() - ri_)
    src = np.stack([C + (col_start - 1), R + (row_start - 1)], axis=1).astype(np.float32)
    H, _ = cv2.findHomography(src, pts.astype(np.float32), 0)
    if H is None: return None, len(best), None, P
    q = cv2.perspectiveTransform(src[None], H)[0]; err = float(np.linalg.norm(q - pts, axis=1).mean())
    # 검증: 칸 방향은 판이 길게 놓인 쪽이라 줄 방향보다 한 칸 간격이 짧아 보이는 일이 흔하지만, 두 방향 간격이 비슷하면(정사각형 비) 판 방향을 잘못 읽은 것이다
    return H, len(best), err, P

def cmd_autofit(a):
    im = load_orig(a["name"], a["step"]); cols, rows = int(a["cols"]), int(a["rows"])
    H, used, err, P = auto_fit(im, cols, rows, a["bbox"], a.get("lo", 200), a.get("hi", 256), a.get("amin", 30), a.get("col_start", 1), a.get("row_start", 1), a.get("flip_cols", False), a.get("flip_rows", False))
    if H is None: return {"ok": False, "matched": used, "note": "구멍을 격자로 잇지 못했어요 — bbox 를 좁히거나 lo/hi/amin 을 바꾸거나 corners 로 refs_fit 을 쓴다."}
    q = project(H, cols, rows); n = cols * rows
    pts = [[int(c) + 1, int(r) + 1, round(float(x), 1), round(float(y), 1)] for (c, r), (x, y) in zip(lattice(cols, rows), q)]
    conf = "높음" if (used >= 0.4 * n and err < 3) else "보통" if used >= 0.25 * n else "낮음(눈으로 확인)"
    return {"ok": True, "matched": used, "total": n, "mean_err_px": round(err, 2), "confidence": conf, "pts": pts}

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
    if a.get("corners"): H, used, err, P = fit_grid(im, cols, rows, a["corners"], a.get("lo", 90), a.get("hi", 200), amin=a.get("amin", 250))
    else:   # 모서리 없이 bbox 만: 구멍들을 격자로 자동 연결(autofit)
        H, used, err, P = auto_fit(im, cols, rows, a["bbox"], a.get("lo", 200), a.get("hi", 256), a.get("amin", 30), a.get("col_start", 1), a.get("row_start", 1), a.get("flip_cols", False), a.get("flip_rows", False))
        if H is None: return {"ok": False, "matched": used, "note": "구멍을 격자로 잇지 못했어요 — bbox 를 좁히거나 lo/hi/amin 을 바꾸거나 corners 를 직접 준다."}
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

def render_plain(name, step, d, im):
    """판이 없는 단계: NN_1 = 부품만 잘라 낸 원본 1장(설명 앞 글자 ① = 화면에서 "교재 원본"으로 보인다). 2차 격자는 없다."""
    cv2.imwrite(os.path.join(d, "%02d_1.jpg" % step), im, [cv2.IMWRITE_JPEG_QUALITY, 82])
    for k in (2, 3):
        pk = os.path.join(d, "%02d_%d.jpg" % (step, k))
        if os.path.exists(pk): os.remove(pk)
    ip = os.path.join(d, "index.json"); index = json.load(open(ip, encoding="utf-8")); index = [r for r in index if not (r["step"] == step and r["idx"] in (1, 2, 3))]
    index.append({"step": step, "idx": 1, "file": "%02d_1.jpg" % step, "note": "① 단계 %d — 부품만 잘라 낸 교재 원본(판이 없는 단계라 격자 없음)" % step})
    index.sort(key=lambda r: (r["step"], r["idx"])); json.dump(index, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"rotated_deg": 0, "files": ["%02d_1.jpg" % step], "preview": os.path.join(d, "%02d_1.jpg" % step), "original_preview": os.path.join(d, "%02d_1.jpg" % step)}

def cmd_render(a):
    """plates = [{name, cols, rows, pts:[[칸,줄,x,y]...](원본 좌표, 4개 이상), ref:true(수평 기준 판 1개)}]
    crop = [x0,y0,x1,y1] 부품만 남길 영역(원본 좌표, 쪽 테두리·글씨를 빼고), erase = [[x0,y0,x1,y1],...] 영역 안에 끼어 있는 글씨·이름표를 흰색으로 지운다.
    저장: NN_1 = 1차 격자(잘라 낸 원본 위), NN_2 = 2차 격자(잘라 낸 그림을 수평으로 돌리고 위에 격자 + 파란 수평선). 둘 다 부품만 있다."""
    name, step = a["name"], int(a["step"]); d = refs_dir(name); im0 = load_orig(name, step); plates = a["plates"]
    im = im0.copy()
    for (ex0, ey0, ex1, ey1) in a.get("erase") or []: im[int(ey0):int(ey1), int(ex0):int(ex1)] = 255   # 글씨·이름표 지우기(가위로 부품만 추출)
    h0, w0 = im.shape[:2]; cx0, cy0, cx1, cy1 = [int(v) for v in (a.get("crop") or [0, 0, w0, h0])]; cx0, cy0, cx1, cy1 = max(0, cx0), max(0, cy0), min(w0, cx1), min(h0, cy1)
    im = im[cy0:cy1, cx0:cx1].copy(); h, w = im.shape[:2]
    if not plates: return render_plain(name, step, d, im)   # 판이 없는 단계(기어·축 등): 격자 없이 부품만 잘라 낸 원본 1장
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
