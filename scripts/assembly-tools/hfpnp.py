# holefit 의 격자(칸 번호)와 모델의 구멍 3D 좌표를 짝지어 PnP 로 카메라를 푼다 — holefit 가 "평균 오차 2px" 기준을 못 넘는 작은 판(구멍 20개 안팎)·원근이 센 판용(2026-10-23 트레일러 2번).
#   python hfpnp.py <이름> <번호> <라벨> <칸수> <줄수> <부품이름> <부품이 놓인 번호> x1 y1 x2 y2 x3 y3 x4 y4 [--줄뒤집기] [--칸뒤집기]   (모서리 4곳은 holefit 와 같은 순서·눈대중 OK)
#   하는 일: DoG 로 구멍 후보를 찾고(holefit 와 같은 방식) → 눈대중 모서리의 호모그래피로 칸에 붙이고 → 모델 구멍 3D 와 pnp.fit(fov 15~60)으로 카메라를 풀어 투영 → 다시 붙이기를 되풀이하며 오차 큰 점을 덜어낸다.
#   통과 기준: 붙은 구멍 ≥ 6개·평균 오차 ≤ 2.0px. 통과하면 refs/<이름>/fits/NN_<라벨>.json 에 pts(칸·줄·픽셀)·xyz3d·xyz3d_img·fov 를 쓴다(overlay_check·axes 용).
import sys, os, json, runpy
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
HERE = os.path.dirname(os.path.abspath(__file__))
_anc = None; _ref = None
if '--앵커' in sys.argv: _anc = [[float(v) for v in a.split(',')] for a in sys.argv[sys.argv.index('--앵커') + 1].split(';')]   # 책 그림에서 칸·줄이 확실한 점 둘 이상(링 등): c,r,x,y — 이 점과 참조 번호의 격자 모양으로 눈대중 모서리 대신 처음 격자를 만든다
if '--참조' in sys.argv: _ref = int(sys.argv[sys.argv.index('--참조') + 1])
_ini = None
if '--초기' in sys.argv: _ini = int(sys.argv[sys.argv.index('--초기') + 1])   # 눈대중 모서리 대신 이 번호의 풀이 카메라로 판 위치를 먼저 예측한다(판이 앞 조립에 많이 가려져 모서리를 못 읽을 때)
_skip = set(); _rng = None; _fov = None
for _i, _a in enumerate(sys.argv):
    if _a in ('--초기', '--앵커', '--참조'): _skip.add(_i + 1)
    if _a == '--fov': _fov = int(sys.argv[_i + 1]); _skip.add(_i + 1)   # 한 판(평면)만으로는 fov 가 정해지지 않을 때 앞 번호 값쯤으로 고정한다
    if _a == '--칸범위': _rng = (int(sys.argv[_i + 1]), int(sys.argv[_i + 2])); _skip.update((_i + 1, _i + 2))   # 가려지지 않은 칸만 쓴다(예: --칸범위 8 15)
args = [a for _i, a in enumerate(sys.argv) if _i >= 1 and not a.startswith('--') and _i not in _skip]; FLIP_R = '--줄뒤집기' in sys.argv; FLIP_C = '--칸뒤집기' in sys.argv   # 책 그림의 줄·칸 순서가 모델 구멍 번호와 반대일 때(뒤집어 놓은 판)
name, step, label, cols, rows, part, pstep = args[0], int(args[1]), args[2], int(args[3]), int(args[4]), args[5], int(args[6])
C = np.array([float(v) for v in args[7:15]], np.float32).reshape(4, 2) if len(args) >= 15 else None
D = os.path.join(HERE, "refs", name) + os.sep
im = cv2.imread(D + "%02d.jpg" % step); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); Hh, Ww = g.shape
A = runpy.run_path(os.path.join(HERE, name + ".py"), run_name="probe")["A"]
q = next(p for p in A.parts if p.n == part and p.step.index == pstep)
_hv = (np.array(q.extra.get('dir') or [0, 1, 0], float) * float(q.extra.get('hover') or 0)) if (q.extra.get('hover') and q.step.index == step and '--띄움없음' not in sys.argv) else np.zeros(3)   # 책 그림에서 이 번호에 띄워 그려진 부품만 띄운 만큼 옮겨 푼다(앞 번호 부품은 제자리)   # 책 그림에서 이 부품은 띄워진 채 그려져 있으므로 띄운 만큼 옮겨 푼다
world = {}
for c in range(1, cols + 1):
    for r in range(1, rows + 1):
        try: world[(c, r)] = q.hole("h%d_%d" % (cols + 1 - c if FLIP_C else c, rows + 1 - r if FLIP_R else r))["pos"] + _hv
        except KeyError: pass
if _ini is not None:   # 이전 번호 카메라로 칸 가운데 4모서리를 투영해 모서리를 만든다
    f0 = json.load(open(D + "fits/%02d_P.json" % _ini, encoding="utf-8")); O0 = np.array(f0["xyz3d"], float); I0 = f0["xyz3d_img"]; c00 = O0.mean(0)
    r0 = fit(O0 - c00, I0, Ww, Hh, int(f0["fov"]), None, None); _, rv0, tv0, K0 = r0
    Pj = lambda w: cv2.projectPoints(np.float32([np.array(w, float) - c00]), rv0, tv0, K0, None)[0][0][0]
    cw = lambda c, r: world[(c, r)]
    # 칸 가운데 격자 점을 투영해 호모그래피(칸-0.5 좌표 → 그림)를 만든다
    src0 = np.array([[c - 0.5, r - 0.5] for (c, r) in world], np.float32); dst0 = np.array([Pj(world[k]) for k in world], np.float32)
    Hi, _ = cv2.findHomography(src0, dst0, 0)
    C = np.array([cv2.perspectiveTransform(np.array([[[a, b]]], np.float32), Hi)[0][0] for a, b in ((0, 0), (cols, 0), (cols, rows), (0, rows))], np.float32)
    print("  이전 카메라로 예측한 모서리:", " ".join("%.0f %.0f" % (c[0], c[1]) for c in C))
if _anc is not None and _ref is None and len(_anc) >= 4:   # 참조 없이 앵커 4점 이상이면 앵커로 호모그래피를 만들어 처음 모서리로 쓴다
    Ha, _ = cv2.findHomography(np.array([[a[0] - 0.5, a[1] - 0.5] for a in _anc], np.float32), np.array([[a[2], a[3]] for a in _anc], np.float32), 0)
    C = np.array([cv2.perspectiveTransform(np.array([[[a, b]]], np.float32), Ha)[0][0] for a, b in ((0, 0), (cols, 0), (cols, rows), (0, rows))], np.float32)
    print("  앵커로 만든 처음 모서리:", " ".join("%.0f %.0f" % (c[0], c[1]) for c in C))
if _anc is not None and _ref is not None:   # 앵커 점 + 참조 번호의 격자 모양(칸·줄 방향 벡터)으로 처음 격자를 만든다
    fr_ = json.load(open(D + "fits/%02d_P.json" % _ref, encoding="utf-8")); fp_ = [t for t in fr_["pts"] if [t[0], t[1]] not in fr_.get("est", [])]
    Hr, _ = cv2.findHomography(np.array([[t[0] - 0.5, t[1] - 0.5] for t in fp_], np.float32), np.array([[t[2], t[3]] for t in fp_], np.float32), 0)
    a0, a1 = _anc[0], _anc[1]; mid = ((a0[0] + a1[0]) / 2 - 0.5, (a0[1] + a1[1]) / 2 - 0.5)
    pr = lambda c, r: cv2.perspectiveTransform(np.array([[[c, r]]], np.float32), Hr)[0][0]
    dcol = pr(mid[0] + 0.5, mid[1]) - pr(mid[0] - 0.5, mid[1]); drow = pr(mid[0], mid[1] + 0.5) - pr(mid[0], mid[1] - 0.5)
    vA = np.array([a1[2] - a0[2], a1[3] - a0[3]]); vR = (a1[0] - a0[0]) * dcol + (a1[1] - a0[1]) * drow
    sc = np.linalg.norm(vA) / np.linalg.norm(vR); an = np.arctan2(vA[1], vA[0]) - np.arctan2(vR[1], vR[0]); Rr = np.array([[np.cos(an), -np.sin(an)], [np.sin(an), np.cos(an)]]) * sc
    aff = lambda c, r: np.array([a0[2], a0[3]]) + Rr @ ((c - a0[0]) * dcol + (r - a0[1]) * drow)
    C = np.array([aff(a, b) for a, b in ((0.5, 0.5), (cols + 0.5, 0.5), (cols + 0.5, rows + 0.5), (0.5, rows + 0.5))], np.float32)
    print("  앵커·참조로 만든 처음 모서리:", " ".join("%.0f %.0f" % (c[0], c[1]) for c in C))
if _rng: world = {k: v for k, v in world.items() if _rng[0] <= k[0] <= _rng[1]}
inside = np.zeros(g.shape, np.uint8); cv2.fillPoly(inside, [C.astype(np.int32).reshape(-1, 1, 2)], 1)
g32 = g.astype(np.float32); inn = cv2.erode(inside, np.ones((9, 9), np.uint8))
d = cv2.GaussianBlur(g32, (0, 0), 8.0) - cv2.GaussianBlur(g32, (0, 0), 3.0); d[inn == 0] = 0
pk = (d == cv2.dilate(d, np.ones((11, 11), np.uint8))) & (d > np.percentile(d[inn > 0], 85))
ys, xs = np.nonzero(pk); P = np.array([[x, y] for x, y in zip(xs, ys)], float)
H0, _ = cv2.findHomography(np.array([[0, 0], [cols, 0], [cols, rows], [0, rows]], np.float32), C, 0)
node = lambda H, c, r: cv2.perspectiveTransform(np.array([[[c - 0.5, r - 0.5]]], np.float32), H)[0][0]
pitch = float(np.mean([np.hypot(*(node(H0, c + 1, r) - node(H0, c, r))) for c in range(1, cols) for r in range(1, rows + 1)]))
def assign(pred, tol):
    out, used = {}, set()
    for cr, pos in pred.items():
        dist = np.hypot(*(P - pos).T); k = int(np.argmin(dist))
        if dist[k] < tol * pitch and k not in used: out[cr] = k; used.add(k)
    return out
pred = {(c, r): node(H0, c, r) for (c, r) in world}; sel = assign(pred, 0.5)
H = H0
for it in range(10):   # 호모그래피로 다시 붙이기(눈대중 모서리 보정)
    if len(sel) < 6: break
    Hn, _ = cv2.findHomography(np.array([[c - 0.5, r - 0.5] for (c, r) in sel], np.float32), np.array([P[k] for k in sel.values()], np.float32), cv2.RANSAC, 6.0)
    if Hn is None: break
    H = Hn; pred = {(c, r): node(H, c, r) for (c, r) in world}; sel = assign(pred, max(0.3, 0.5 - 0.04 * it))
print('  다시 맞춘 모서리(실행에 다시 쓴다): ' + ' '.join('%.0f %.0f' % tuple(cv2.perspectiveTransform(np.array([[[a, b]]], np.float32), H)[0][0]) for a, b in ((0, 0), (cols, 0), (cols, rows), (0, rows))))
best = None
for rounds in range(14):   # PnP 로 풀고 오차 큰 점을 덜어낸다
    keys = list(sel); 
    if len(keys) < 6: break
    O = np.array([world[k] for k in keys], float); I = np.array([P[sel[k]] for k in keys], float); c0 = O.mean(0); cand = None
    for fov in ([_fov] if _fov else range(15, 61)):
        r = fit(O - c0, I.tolist(), Ww, Hh, fov, None, None)
        if r and (cand is None or r[0] < cand[0]): cand = (r[0], fov, r[1], r[2], r[3])
    if not cand: break
    e, fov, rv, tv, K = cand
    proj = cv2.projectPoints(np.float32(O - c0), rv, tv, K, None)[0].reshape(-1, 2); res = np.linalg.norm(proj - I, axis=1)
    best = (e, fov, keys, res, rv, tv, K, c0); selb = {k: sel[k] for k in keys}
    print("  라운드 %d: 점 %d개 평균 %.2fpx 최대 %.1fpx fov %d" % (rounds, len(keys), e, res.max(), fov))
    if (res.max() <= 3.5 and e <= 2.0) or len(keys) <= 8: break
    worst = keys[int(np.argmax(res))]; del sel[worst]
if not best: sys.exit("❌ PnP 를 못 풀었다 — 모서리를 고쳐 다시 한다")
e, fov, keys, res, rv, tv, K, c0 = best; sel = selb
Cc, fwd, up, right = cam_from(rv, tv)
print("★ 점 %d개 평균 %.2fpx fov %d theta %.3f phi %.3f" % (len(keys), e, fov, float(np.arctan2(-fwd[0], -fwd[2])), float(np.arccos(-fwd[1]))))
if (e > 2.0 and '--저장강행' not in sys.argv) or len(keys) < 6: sys.exit("❌ 통과 못 함(평균 ≤2.0px·점 ≥6) — fits 를 쓰지 않는다")
pts = []; est = []
Hfin, _ = cv2.findHomography(np.array([[c - 0.5, r - 0.5] for (c, r) in keys], np.float32), np.array([P[sel[k]] for k in keys], np.float32), 0)
for (c, r) in sorted(world):
    if (c, r) in sel: pts.append([c, r, round(float(P[sel[(c, r)]][0]), 2), round(float(P[sel[(c, r)]][1]), 2)])
    else: p_ = node(Hfin, c, r); pts.append([c, r, round(float(p_[0]), 2), round(float(p_[1]), 2)]); est.append([c, r])
out = {"cols": cols, "rows": rows, "pts": pts, "est": est, "name": "%s %d번 %s: DoG 구멍 %d개 + 모델 구멍 3D → hfpnp PnP 평균 %.2fpx(fov %d)" % (name, step, part, len(keys), e, fov), "tool": "hfpnp", "err_px": round(float(e), 2), "max_err_px": round(float(res.max()), 2), "found": len(keys), "found_ratio": round(len(keys) / (cols * rows), 2), "mode": "DoG+PnP",
       "xyz3d": [[float(v) for v in world[k]] for k in keys], "xyz3d_img": [[float(v) for v in P[sel[k]]] for k in keys], "fov": fov}
os.makedirs(D + "fits", exist_ok=True); json.dump(out, open(D + "fits/%02d_%s.json" % (step, label), "w", encoding="utf-8"), ensure_ascii=False)
print("✅ 저장: fits/%02d_%s.json (찾은 점 %d, 격자로 채운 점 %d)" % (step, label, len(keys), len(est)))
