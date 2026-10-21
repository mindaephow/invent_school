# 책에 판(격자)이 없는 번호의 카메라를 "몸통 윤곽 + 리벳 머리"로 푼다 (바이킹 27·28번에서 쓴 방법을 도구로, 2026-10-22).
#   python bookcam.py <이름> <번호> [--extra 점파일.json] [--mask x0,y0,x1,y1 ...] [--fov-range 20,44] [--no-rivet] [--dry]
# 1) 번호 N 까지 만든 모델의 부품 상자(dims.json)를 후보 카메라(theta·phi·fov·거리·화면 이동)로 투영해 책 그림의 몸통 윤곽(흰 바탕이 아닌 곳)과 겹침 비율(IoU)이 최대가 되게 찾는다(scipy differential_evolution).
# 2) 그 카메라로 모델 리벳 끝(양 끝) 투영을 책의 주황 리벳 머리 점과 최근접으로 짝지어 PnP(pnp.fit, 주점 이동 허용)를 반복한다.
#    --extra: 이미 확실한 3D 점과 책 픽셀 [{"xyz":[x,y,z],"px":[u,v]}, ...] 를 같이 넣는다(막대 꼭대기·돌기·링 등).
#    --dry: 파일을 쓰지 않고 결과만 본다.
# 출력: theta·phi·fov·주점·평균오차, refs/<이름>/fits/NN_P.json(xyz3d·xyz3d_img·fov·cx·cy), NN_axes.json, NN_lv.json. overlay_check.py 가 cx·cy 를 읽는다.
# (camfit.py 는 오토건의 다른 도구라 이름을 bookcam 으로 했다.)
import sys, os, math, json, numpy as np, cv2
from scipy.optimize import differential_evolution
from scipy.spatial import cKDTree
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
from pnp import fit, cam_from


def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    name, N = a[0], int(a[1]); extra = []; masks = []; fr = (20, 44); rivet = True; dry = False; i = 2
    while i < len(a):
        if a[i] == "--extra": extra = json.load(open(a[i + 1], encoding="utf-8")); i += 2
        elif a[i] == "--mask": masks.append([int(v) for v in a[i + 1].split(",")]); i += 2
        elif a[i] == "--fov-range": fr = tuple(int(v) for v in a[i + 1].split(",")); i += 2
        elif a[i] == "--no-rivet": rivet = False; i += 1
        elif a[i] == "--dry": dry = True; i += 1
        else: i += 1
    src = open(name + ".py", encoding="utf-8").read(); cut = src.find("# ── %d ──" % (N + 1)); end = src.index("import stepchecks")
    src = src[:cut if 0 < cut < end else end] + "\n"
    ns = {"__name__": "probe", "__file__": os.path.abspath(name + ".py")}; exec(compile(src, name + ".py", "exec"), ns); A = ns["A"]
    dims = json.load(open("dims.json", encoding="utf-8")); hide = (A.steps[N - 1].kw.get("hideMade") or {})
    boxes = []
    for q in A.parts:
        d = dims.get(q.n)
        if not d or q.step.index > N or q.n in ("리벳", "8볼트", "12볼트", "너트") or str(q.step.index) in hide: continue
        R = np.array(q.R, float); c = np.array(q.p, float)
        if q.step.index == N: c = c + np.array(q.extra.get("dir", [0, 0, 0]), float) * float(q.extra.get("hover", 0))
        boxes.append(np.array([c + R @ np.array([sx * d[0] / 2, sy * d[1] / 2, sz * d[2] / 2]) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]))
    im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    M = ((g < 225) | (hsv[:, :, 1] > 60)).astype(np.uint8); gr = ((hsv[:, :, 0] > 45) & (hsv[:, :, 0] < 85) & (hsv[:, :, 1] > 100)).astype(np.uint8); M[cv2.dilate(gr, np.ones((5, 5))) > 0] = 0
    M[:120, :230] = 0; M[700:, 840:] = 0
    for x0, y0, x1, y1 in masks: M[y0:y1, x0:x1] = 0
    S = 0.25; Ms = (cv2.resize(M, None, fx=S, fy=S, interpolation=cv2.INTER_AREA) > 0.4).astype(np.uint8); hs, ws = Ms.shape
    tgt = np.vstack(boxes).mean(0)

    def render(p):
        th, ph, fov, r, tx, ty = p
        C = tgt + r * np.array([math.sin(ph) * math.sin(th), math.cos(ph), math.sin(ph) * math.cos(th)]); z = (tgt - C) / np.linalg.norm(tgt - C); x = np.cross(z, [0, 1.0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x); Rm = np.array([x, y, z]); f = (H / 2) / math.tan(math.radians(fov) / 2) * S
        out = np.zeros((hs, ws), np.uint8)
        for bx in boxes:
            pc = (Rm @ (bx - C).T).T
            if (pc[:, 2] <= 1).any(): continue
            u = f * pc[:, 0] / pc[:, 2] + ws / 2 + tx * S; v = f * pc[:, 1] / pc[:, 2] + hs / 2 + ty * S
            cv2.fillConvexPoly(out, cv2.convexHull(np.c_[u, v].astype(np.float32)).astype(np.int32), 1)
        return out
    cost = lambda p: (lambda o: 1 - (o & Ms).sum() / max(((o | Ms) > 0).sum(), 1))(render(p))
    r = differential_evolution(cost, [(-math.pi, math.pi), (0.3, 1.5), (fr[0], fr[1] + 11), (250, 1100), (-300, 300), (-300, 300)], seed=2, maxiter=90, popsize=18, tol=1e-6, polish=False)
    print("① 윤곽 IoU %.2f  theta %.3f phi %.3f fov %.1f 거리 %.0f 이동 (%.0f,%.0f)" % (1 - r.fun, r.x[0], r.x[1], r.x[2], r.x[3], r.x[4], r.x[5]))
    th, ph, fov, rad, tx, ty = r.x
    C = tgt + rad * np.array([math.sin(ph) * math.sin(th), math.cos(ph), math.sin(ph) * math.cos(th)]); z = (tgt - C) / np.linalg.norm(tgt - C); x = np.cross(z, [0, 1.0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x); Rm = np.array([x, y, z])
    f = (H / 2) / math.tan(math.radians(fov) / 2); cx, cy = W / 2 + tx, H / 2 + ty; K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]]); rv, _ = cv2.Rodrigues(Rm); tv = (-Rm @ C).reshape(3, 1)
    EX = np.array([e["xyz"] for e in extra], float).reshape(-1, 3); EI = np.array([e["px"] for e in extra], float).reshape(-1, 2)
    O = EX; I = EI
    if rivet:
        ends = []
        for q in A.parts:
            if q.n == "리벳" and q.step.index <= N and str(q.step.index) not in hide:
                for pg in q.conn["pegs"]:
                    w = q.world("peg", pg); ends.append(np.array(w["pos"], float) + np.array(w["dir"], float) * float(pg["len"]) / 2)
        ends = np.array(ends); org = ((hsv[:, :, 0] >= 5) & (hsv[:, :, 0] <= 22) & (hsv[:, :, 1] > 150) & (hsv[:, :, 2] > 110)).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(org); B = np.array([cen[k] for k in range(1, n) if 10 < st[k][4] < 500]); print("리벳 끝 %d · 주황 점 %d" % (len(ends), len(B)))
        for it in range(8):
            pr = cv2.projectPoints(ends, rv, tv, K, None)[0].reshape(-1, 2); t = cKDTree(B); pairs = []; used = set()
            for k in np.argsort([t.query(p)[0] for p in pr]):
                d, j = t.query(pr[k])
                if d < 16 and j not in used: pairs.append((k, j)); used.add(j)
            O = np.vstack([EX, ends[[p[0] for p in pairs]]]) if len(pairs) else EX; I = np.vstack([EI, B[[p[1] for p in pairs]]]) if len(pairs) else EI
            if len(O) < 6: break
            best = None
            for fv in range(fr[0], fr[1] + 1, 2):
                for ccx, ccy in ((cx, cy), (W / 2, H / 2)):
                    rr = fit(O, I, W, H, fv, ccx, ccy)
                    if rr and (best is None or rr[0] < best[0][0]): best = (rr, fv, ccx, ccy)
            if not best: break
            (e, rv, tv, K), fov, cx, cy = best; C2, fwd, up, right = cam_from(rv, tv)
            print("  반복 %d 짝 %d 오차 %.2fpx fov %d 주점 (%d,%d) theta %.3f phi %.3f" % (it, len(pairs), e, fov, cx, cy, math.atan2(-fwd[0], -fwd[2]), math.acos(-fwd[1])))
    if len(O) < 6: sys.exit("점이 6개 미만 — --extra 로 확실한 점을 더한다")
    for _ in range(3):   # 잔차가 큰 짝(리벳 잘못 짝지음)을 덜어 낸다 — 중앙값의 2.5배 또는 8px 넘는 점, 추가 점(--extra)은 남긴다
        rr = fit(O, I, W, H, int(fov), cx, cy)
        if not rr: break
        e0, rv0, tv0, K0 = rr; res = np.linalg.norm(cv2.projectPoints(O, rv0, tv0, K0, None)[0].reshape(-1, 2) - I, axis=1)
        lim = max(8.0, 2.5 * float(np.median(res))); keep = np.array([k < len(EX) or res[k] <= lim for k in range(len(O))])
        if keep.all() or keep.sum() < 8: break
        O, I = O[keep], I[keep]; print("  이상점 %d개 덜어냄 → %d점" % (int((~keep).sum()), len(O)))
    e, rv, tv, K = fit(O, I, W, H, int(fov), cx, cy); C2, fwd, up, right = cam_from(rv, tv); th2 = round(math.atan2(-fwd[0], -fwd[2]), 3); ph2 = round(math.acos(-fwd[1]), 3)
    print("★ 최종: 점 %d개 오차 %.2fpx fov %d 주점 (%d,%d)  theta %.3f phi %.3f   (윤곽 해 theta %.3f phi %.3f)" % (len(O), e, fov, cx, cy, th2, ph2, th, ph))
    json.dump({"rv": [float(v) for v in np.ravel(rv)], "tv": [float(v) for v in np.ravel(tv)], "K": [[float(v) for v in row] for row in K], "W": W, "H": H}, open(os.path.join(HERE, "refs", name, "%02d_cam.json" % N), "w"))   # 풀이 카메라(후보 점을 투영해 볼 때 쓴다)
    if dry: return
    P = lambda v: cv2.projectPoints(np.float32([v]), rv, tv, K, None)[0][0][0]; ctr = O.mean(0); o = P(ctr); gg = {}
    for k, v in (("X", [10, 0, 0]), ("Y", [0, 10, 0]), ("Z", [0, 0, 10])):
        w = P(ctr + np.array(v)) - o; s = 55.0 / max(abs(w[0]), abs(w[1]), 1e-6) if k != "Y" else 55.0 / max(abs(w[1]), 1e-6); gg[k] = [round(float(w[0] * s), 1), round(float(w[1] * s), 1)]
    D = os.path.join(HERE, "refs", name); pts = [[k + 1, 1, float(u), float(v)] for k, (u, v) in enumerate(I)]
    json.dump({"cols": len(pts), "rows": 1, "pts": pts, "est": [], "err_px": round(float(e), 2), "max_err_px": 12, "tool": "bookcam", "found": len(pts), "found_ratio": 1.0, "mode": "bookcam", "name": "%d번 P: 몸통 윤곽 IoU %.2f + 리벳 머리·추가 점 %d개 PnP %.2fpx(fov %d, 주점 (%d,%d))" % (N, 1 - r.fun, len(O), e, fov, cx, cy), "evidence": {"visible_holes": len(pts), "anchors": [], "anchor_mean_px": round(float(e), 2), "anchor_max_px": 12, "loo_dtheta": 0.0, "loo_dphi": 0.0, "fov": int(fov)}, "xyz3d": [[float(v) for v in q] for q in O], "xyz3d_img": [[float(v) for v in q] for q in I], "fov": int(fov), "cx": float(cx), "cy": float(cy)}, open(os.path.join(D, "fits", "%02d_P.json" % N), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"global": gg, "fit": {"from": "%02d_P.json bookcam 3D 점 %d개 PnP" % (N, len(O)), "err_px": round(float(e), 2), "points": len(O), "theta": round(th2, 2), "phi": round(ph2, 2), "cols": "+X", "rows": "+Y", "note": "bookcam: 몸통 윤곽 IoU %.2f 해(theta %.2f·phi %.2f)와 비교" % (1 - r.fun, th, ph)}, "no_rotate": True}, open(os.path.join(D, "%02d_axes.json" % N), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"M": [[1, 0, 0], [0, 1, 0]], "size": [W, H], "angle": 0.0, "crop": [0, 0, W, H], "erase": []}, open(os.path.join(D, "%02d_lv.json" % N), "w"))
    print("파일 저장: fits/%02d_P.json · %02d_axes.json · %02d_lv.json" % (N, N, N))


main()
