# 홀라인 맞추기(조립도에서 가장 중요한 첫 단추, 사용자 지시 2026-10-12) — 책 그림의 판 구멍을 찾아 칸×줄 격자에 정확히 맞추고, 오차를 재서 통과 못 하면 fits 를 쓰지 않는다.
#   python holefit.py <이름> <번호> <라벨> <칸> <줄> c1r1x c1r1y cNr1x cNr1y cNrMx cNrMy c1rMx c1rMy [어두운판]
#     뒤 8개 = 판의 **바깥 윤곽 모서리 4곳**(원본 그림 좌표, 눈으로 읽는다): 칸1줄1 쪽 모서리, 칸N줄1 쪽, 칸N줄M 쪽, 칸1줄M 쪽 순서.
#     (칸1줄1 = 세계 −X·−Z 쪽 끝, 칸은 +X, 줄은 +Z 로 늘어난다)
#     어두운판 을 끝에 쓰면 검은 프레임용: 구멍 안쪽 밝은 조각(뒤가 비쳐 보이는 부분)을 찾는다. 기본은 밝은 판 위의 어두운 구멍.
#   하는 일: 모서리로 호모그래피를 만들어 각 구멍 자리(칸 가운데)를 예측 → 그 근처의 실제 구멍 블롭에 붙임 → 붙은 점으로 호모그래피를 다시 맞춤(반복).
#   통과 기준(하나라도 어기면 fits 를 쓰지 않는다): 붙은 구멍 ≥ 격자 칸수의 40%, 평균 오차 ≤ 2.0px, 최대 오차 ≤ 4.5px.
#   출력: refs/<이름>/fits/NN_<라벨>.json(찾은 점 + est=찾지 못해 격자로 채운 점), refs/<이름>/hf/NN_<라벨>.png(찾은 구멍 ●·격자 ✚·번호 겹친 확인 그림 — **반드시 눈으로 본다**).
import sys, os, json
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 14: sys.exit(__doc__)
name, step, label, cols, rows = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
C = np.array([float(v) for v in sys.argv[6:14]], np.float32).reshape(4, 2)
dark_plate = len(sys.argv) > 14 and sys.argv[14] == "어두운판"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", name) + os.sep
im = cv2.imread(D + "%02d.jpg" % step); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
# 판 바깥 윤곽(모서리) → 칸 가운데 자리 예측용 호모그래피: 판 좌표 (0..cols, 0..rows) ↔ 그림. 칸 (c, r) 의 가운데 = (c−0.5, r−0.5)
H0, _ = cv2.findHomography(np.array([[0, 0], [cols, 0], [cols, rows], [0, rows]], np.float32), C, 0)
def node(H, c, r): return cv2.perspectiveTransform(np.array([[[c - 0.5, r - 0.5]]], np.float32), H)[0][0]
def nodes(H): return {(c, r): node(H, c, r) for c in range(1, cols + 1) for r in range(1, rows + 1)}
pred0 = nodes(H0)
pitch = float(np.mean([np.hypot(*(pred0[(c + 1, r)] - pred0[(c, r)])) for c in range(1, cols) for r in range(1, rows + 1)]))
x0, y0 = int(max(0, C[:, 0].min() - 10)), int(max(0, C[:, 1].min() - 10)); x1, y1 = int(min(im.shape[1], C[:, 0].max() + 10)), int(min(im.shape[0], C[:, 1].max() + 10))
sub = g[y0:y1, x0:x1]
# 검출 방식 순서(2026-10-13 추가): 사용자가 준 방식(기본/어두운판)을 먼저 하고, 기준 미달이면 어두운 구멍(DoG) 방식을 이어서 시도한다.
#   DoG: 판이 검은색이라 구멍 뒤가 비쳐 보이지 않을 때(구멍이 검은 판 위의 더 어두운 원) — 주변보다 어두운 원을 후보로 잡고, 오차 큰 배정은 "못 찾음"으로 돌려 다시 맞춘다. 통과 기준은 방식과 상관없이 같다.
inside_full = np.zeros(g.shape, np.uint8); cv2.fillPoly(inside_full, [C.astype(np.int32).reshape(-1, 1, 2)], 1)
def candidates(mode):
    if mode == "DoG":
        g32 = g.astype(np.float32); inn = cv2.erode(inside_full, np.ones((9, 9), np.uint8))
        d = cv2.GaussianBlur(g32, (0, 0), 8.0) - cv2.GaussianBlur(g32, (0, 0), 3.0); d[inn == 0] = 0
        pk = (d == cv2.dilate(d, np.ones((11, 11), np.uint8))) & (d > np.percentile(d[inn > 0], 85))
        ys, xs = np.nonzero(pk); return np.array([[x, y] for x, y in zip(xs, ys)], float)
    inside = np.zeros(sub.shape, np.uint8); cv2.fillPoly(inside, [(C - np.array([x0, y0], np.float32)).astype(np.int32).reshape(-1, 1, 2)], 1); inside = cv2.erode(inside, np.ones((5, 5), np.uint8))
    if mode == "어두운판": m = ((sub > 200) & (inside > 0)).astype(np.uint8) * 255
    else: m = ((sub < 140) & (inside > 0)).astype(np.uint8) * 255
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    return np.array([[cen[i][0] + x0, cen[i][1] + y0] for i in range(1, n) if 15 < st[i][4] < 700 and 0.3 < st[i][2] / max(1, st[i][3]) < 3.8], float)
def fit_grid(P, robust):
    H = H0; sel = {}
    for it in range(12):
        pred = nodes(H); new = {}; used = set()
        tol = max(0.33, 0.5 - 0.04 * it)   # 처음엔 모서리 눈대중 오차를 받아주고(0.5칸), 맞출수록 엄격하게(0.33칸)
        for cr, pos in sorted(pred.items(), key=lambda kv: kv[0]):
            dist = np.hypot(*(P - pos).T); k = int(np.argmin(dist))
            if dist[k] < tol * pitch and k not in used: new[cr] = k; used.add(k)
        if len(new) < 6: break
        src = np.array([[c - 0.5, r - 0.5] for (c, r) in new], np.float32); dst = np.array([P[k] for k in new.values()], np.float32)
        Hn, _ = cv2.findHomography(src, dst, 0)
        if Hn is None: break
        H = Hn
        if new == sel: break
        sel = new
    if robust:   # 오차가 큰 배정은 "못 찾음"으로 돌리고 나머지로 다시 맞춘다
        for _ in range(6):
            pr = nodes(H); e = {cr: float(np.hypot(*(P[k] - pr[cr]))) for cr, k in sel.items()}
            if not e: break
            lim = max(2.5, 2.0 * float(np.median(list(e.values())))); bad = [cr for cr, v in e.items() if v > lim]
            if not bad or len(sel) - len(bad) < 20: break
            for cr in bad: del sel[cr]
            Hn, _ = cv2.findHomography(np.array([[c - 0.5, r - 0.5] for (c, r) in sel], np.float32), np.array([P[k] for k in sel.values()], np.float32), 0)
            if Hn is None: break
            H = Hn
    return H, sel
def evaluate(mode):
    P = candidates(mode)
    if len(P) < 6: print("  [%s] 구멍 후보가 너무 적다(%d)" % (mode, len(P))); return None
    H, sel = fit_grid(P, mode == "DoG"); pred = nodes(H)
    err = [float(np.hypot(*(P[k] - pred[cr]))) for cr, k in sel.items()]
    mean_e, max_e = (float(np.mean(err)), float(np.max(err))) if err else (99.0, 99.0)
    ok = len(sel) >= 0.4 * cols * rows and mean_e <= 2.0 and max_e <= 4.5
    print("  [%s] 구멍 후보 %d개 → 격자 %d×%d 중 %d개 배정(%.0f%%) | 오차 평균 %.2fpx 최대 %.2fpx | %s" % (mode, len(P), cols, rows, len(sel), 100 * len(sel) / (cols * rows), mean_e, max_e, "통과" if ok else "기준 미달"))
    return dict(mode=mode, P=P, H=H, sel=sel, pred=pred, mean_e=mean_e, max_e=max_e, ok=ok)
_first = "어두운판" if dark_plate else "기본"
_tried = []
for _mode in (_first, "DoG"):
    _r = evaluate(_mode)
    if _r: _tried.append(_r)
    if _r and _r["ok"]: break
if not _tried: sys.exit("❌ 구멍 후보가 너무 적다 — 모서리·밝기 기준(어두운판)을 확인한다")
_best = next((t for t in _tried if t["ok"]), max(_tried, key=lambda t: len(t["sel"])))
P, H, sel, pred, mean_e, max_e, used_mode = _best["P"], _best["H"], _best["sel"], _best["pred"], _best["mean_e"], _best["max_e"], _best["mode"]
print("→ 사용한 방식: %s | 구멍 간격 약 %.1fpx" % (used_mode, pitch))
_cn = [cv2.perspectiveTransform(np.array([[[a, b]]], np.float32), H)[0][0] for a, b in ((0, 0), (cols, 0), (cols, rows), (0, rows))]   # 찾은 구멍들로 다시 맞춘 격자의 모서리 — 눈대중 모서리가 어긋나 기준 미달이면 이 값으로 다시 돌린다(2026-10-23 트레일러)
print("  다시 맞춘 모서리(다음 실행에 쓴다): " + " ".join("%.1f %.1f" % (c[0], c[1]) for c in _cn))
os.makedirs(D + "hf", exist_ok=True)
ov = im.copy()
for (c, r), pos in pred.items():
    found = (c, r) in sel
    cv2.drawMarker(ov, (int(pos[0]), int(pos[1])), (0, 0, 255) if found else (255, 0, 0), cv2.MARKER_CROSS, 8, 1)
    if found: cv2.circle(ov, (int(P[sel[(c, r)]][0]), int(P[sel[(c, r)]][1])), 3, (0, 200, 0), -1)
    cv2.putText(ov, "%d.%d" % (c, r), (int(pos[0]) + 3, int(pos[1]) - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 120, 255), 1)
cv2.polylines(ov, [C.astype(np.int32).reshape(-1, 1, 2)], True, (0, 255, 255), 1)
crop = ov[max(0, y0 - 10):y1 + 10, max(0, x0 - 10):x1 + 10]
cv2.imwrite(D + "hf/%02d_%s.png" % (step, label), cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
ok = len(sel) >= 0.4 * cols * rows and mean_e <= 2.0 and max_e <= 4.5
if not ok:
    sys.exit("❌ 통과 못 함(기준: 구멍 ≥40%%, 평균 ≤2.0px, 최대 ≤4.5px) — fits 를 쓰지 않는다. 확인 그림 %s 를 보고 모서리를 고쳐 다시 한다." % (D + "hf/%02d_%s.png" % (step, label)))
pts = [[c, r, round(float(P[sel[(c, r)]][0]), 2), round(float(P[sel[(c, r)]][1]), 2)] if (c, r) in sel else [c, r, round(float(pred[(c, r)][0]), 2), round(float(pred[(c, r)][1]), 2)] for c in range(1, cols + 1) for r in range(1, rows + 1)]
est = [[c, r] for c in range(1, cols + 1) for r in range(1, rows + 1) if (c, r) not in sel]
out = {"cols": cols, "rows": rows, "pts": pts, "name": "%s %d번 %s: 구멍 %d개를 찾아 %d×%d 격자에 호모그래피로 맞춤(오차 평균 %.2fpx·최대 %.2fpx) — holefit.py" % (name, step, label, len(sel), cols, rows, mean_e, max_e), "est": est, "err_px": round(mean_e, 2), "max_err_px": round(max_e, 2)}
out.update({"tool": "holefit", "err_px": round(mean_e, 2), "max_err_px": round(max_e, 2), "found": len(sel), "found_ratio": round(len(sel) / (cols * rows), 2), "mode": used_mode})   # 규칙 점검(rulecheck.py)이 읽는 출처 기록 — 이 도구가 기준을 통과해 만든 격자라는 표시
os.makedirs(D + "fits", exist_ok=True)
json.dump(out, open(D + "fits/%02d_%s.json" % (step, label), "w", encoding="utf-8"), ensure_ascii=False)
print("✅ 통과 — fits/%02d_%s.json 저장(찾지 못해 격자로 채운 점 %d개). 확인 그림 hf/%02d_%s.png 를 눈으로 본다." % (step, label, len(est), step, label))
