# 사진 구도 맞추기: 책 그림(사진)의 링 픽셀로 "카메라 + 떨어져 놓인 부품의 자리·높이"를 한꺼번에 푼다 (사용자 지시 2026-11-11, 조종형비행기 18번에서 쓴 방법을 도구로).
#   왜: mkfit3d 는 3D 점이 이미 정해져 있어야 한다. 그런데 결합 전에 떨어뜨려 그린 번호(날개 둘, 블록·빨간판)는 부품 사이 간격과 옆자리 위치가 책 구도마다 다르다 — 그 값이 틀리면 카메라도 틀어진다.
#   python composefit.py <이름> <번호> <spec.json> [--out 결과.json]      (spec.json 의 "fov": 숫자면 고정, null 이면 20~50 을 찾는다)
#   spec.json = {"fov": 30,
#      "pts": [{"p": [x,y,z], "px": [u,v], "group": "R", "level": ["b","f"]}, ...],   # p = 그 점의 3D(자유 변수를 빼고 쓴 값), px = 책 그림 픽셀
#      "groups": {"R": {"init": [tx, tz]}},      # 그룹에 속한 점은 (x,z) 에 이 이동량이 더해진다 — 책에서 떨어져 놓인 부품 묶음의 자리
#      "levels": {"b": {"init": 40}, "f": {"init": 30}},   # level 이름마다 y 에 더해지는 높이(띄운 간격). 점의 level 이 리스트면 합
#      "grid": {...}, "note": "..."}              # grid·note 는 그대로 결과에 옮긴다(mkfit3d 가 읽는 형식)
#      "grid_fit": {"file": "15_P.json", "origin": [x,y,z], "col": [dx,dy,dz], "row": [dx,dy,dz], "max_points": 24}
#           # 판 격자도 같이 쓴다: holefit 가 책 그림에서 실제로 찾은 구멍(fits/NN_*.json 의 pts 중 est 가 아닌 칸, tool 이 holefit)을 점으로 더한다.
#           # origin/col/row = 칸1·줄1 구멍의 3D 와 칸·줄 +1 의 3D 이동(10mm 간격). mkfit3d/infer3d 가 쓴 fits 는 카메라로 투영한 값이라 쓰지 않는다(순환).
#           # 결과에 "링 점 평균 / 격자 점 평균" 오차를 따로 보여 준다 — 한쪽만 크면 그쪽의 가정(줄·높이·칸 번호)이 틀린 것이다.
#   하는 일: pnp.fit 로 초기 카메라를 잡고, 카메라(6)+그룹 이동+level 높이를 Levenberg–Marquardt 로 한 번에 푼다. 점별 오차(px)·풀린 이동·높이·theta/phi 를 출력하고
#     --out 에 "풀린 3D 점"이 들어간 spec(pts=[[x,y,z],[u,v]], fov 고정)을 쓴다 → 그대로 `python mkfit3d.py <이름> <번호> <라벨> <칸> <줄> 결과.json` 으로 격자·축 파일을 만든다.
#   쓰는 법의 주의: 점은 8개 이상, 자유 변수(그룹 2개씩+level)보다 식(점×2)이 충분히 많아야 한다. 평균 오차가 2.5px 를 넘거나 풀린 값이 말이 안 되면 링 픽셀 읽기를 먼저 다시 본다.
#   검사: python test_composefit.py (가짜 카메라로 투영한 점에서 이동·높이·카메라를 되찾는지)
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit, cam_from, angles


def _lm(fun, x0, iters=400):
    """작은 Levenberg–Marquardt(수치 미분) — scipy 가 없는 PC 에서도 돈다."""
    x = np.array(x0, float); r = fun(x); c = float(r @ r); lam = 1e-2
    for _ in range(iters):
        J = np.empty((len(r), len(x)))
        for j in range(len(x)):
            h = 1e-5 * max(1.0, abs(x[j])); xp = x.copy(); xp[j] += h; J[:, j] = (fun(xp) - r) / h
        A = J.T @ J; g = J.T @ r; done = False
        while True:
            try: dx = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            except np.linalg.LinAlgError: lam *= 10; continue
            rn = fun(x + dx); cn = float(rn @ rn)
            if cn < c: done = (c - cn) < 1e-10 * max(c, 1e-12); x = x + dx; r = rn; c = cn; lam = max(lam / 3, 1e-9); break
            lam *= 4
            if lam > 1e9: done = True; break
        if done: break
    return x


def _world(spec, gnames, lnames, free):
    """풀린 자유 변수(그룹 이동·level 높이)를 넣은 점별 3D 좌표."""
    out = []
    for p in spec["pts"]:
        q = np.array(p["p"], float)
        g = p.get("group")
        if g is not None:
            i = gnames.index(g); q[0] += free[2 * i]; q[2] += free[2 * i + 1]
        lv = p.get("level") or []
        if isinstance(lv, str): lv = [lv]
        for l in lv: q[1] += free[2 * len(gnames) + lnames.index(l)]
        out.append(q)
    return np.array(out)


def grid_points(fj, gf):
    """holefit 가 찾은 구멍(est 아닌 칸)만 3D↔픽셀 점으로 바꾼다. 카메라로 투영해 만든 fits(tool=infer3d 등)는 거부한다."""
    if fj.get("tool") != "holefit": raise SystemExit("❌ 격자 점은 holefit 가 측정한 fits 만 쓴다(이 파일 tool=%s) — 카메라로 투영해 만든 격자는 순환이라 쓰지 않는다" % fj.get("tool"))
    est = {tuple(e) for e in fj.get("est", [])}
    o = np.array(gf["origin"], float); dc = np.array(gf["col"], float); dr = np.array(gf["row"], float)
    pts = [{"p": (o + dc * (c - 1) + dr * (r - 1)).tolist(), "px": [x, y], "kind": "grid"} for c, r, x, y in fj["pts"] if (c, r) not in est]
    return pts[: int(gf.get("max_points", 40))]


def solve(spec, W, H, fov=None):
    """spec 를 풀어 (평균오차, 점별오차, 카메라 rv·tv·K, 풀린 3D 점, 이동, 높이, fov) 를 돌려준다."""
    fov = fov if fov is not None else spec.get("fov")
    if fov is None:
        best = None
        for f in range(20, 51, 5):
            r = solve(spec, W, H, f)
            if best is None or r["mean"] < best["mean"]: best = r
        return best
    gnames = list(spec.get("groups", {})); lnames = list(spec.get("levels", {}))
    free0 = [v for g in gnames for v in spec["groups"][g]["init"]] + [float(spec["levels"][l]["init"]) for l in lnames]
    px = np.array([p["px"] for p in spec["pts"]], float)
    obj0 = _world(spec, gnames, lnames, np.array(free0, float))
    init = fit(obj0.tolist(), px.tolist(), W, H, fov)
    if not init: raise SystemExit("❌ 초기 카메라를 못 푼다 — 점이 너무 적거나 한 줄이다")
    rv0, tv0 = np.ravel(init[1]), np.ravel(init[2])
    f = (H / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
    nfree = len(free0)
    if 2 * len(px) <= 6 + nfree: raise SystemExit("❌ 식(점×2)이 모자란다: 점 %d개, 풀 변수 %d개" % (len(px), 6 + nfree))

    def res(x):
        pj = cv2.projectPoints(np.float32(_world(spec, gnames, lnames, x[6:])), x[0:3].reshape(3, 1), x[3:6].reshape(3, 1), K, None)[0].reshape(-1, 2)
        return (pj - px).ravel()
    x = _lm(res, np.r_[rv0, tv0, free0])
    err = np.hypot(*res(x).reshape(-1, 2).T)
    free = x[6:]
    return {"mean": float(err.mean()), "max": float(err.max()), "per": err, "rv": x[0:3].reshape(3, 1), "tv": x[3:6].reshape(3, 1), "K": K,
            "obj": _world(spec, gnames, lnames, free), "groups": {g: [float(free[2 * i]), float(free[2 * i + 1])] for i, g in enumerate(gnames)},
            "levels": {l: float(free[2 * len(gnames) + i]) for i, l in enumerate(lnames)}, "fov": fov,
            "kinds": {k: float(np.mean([e for e, p in zip(err, spec["pts"]) if p.get("kind", "ring") == k])) for k in {p.get("kind", "ring") for p in spec["pts"]}}}


def main():
    a = [t for t in sys.argv[1:] if not t.startswith("--")]
    if len(a) < 3: sys.exit(__doc__ or "사용: python composefit.py <이름> <번호> <spec.json> [--out 결과.json]")
    name, N, specp = a[0], int(a[1]), a[2]
    spec = json.load(open(specp, encoding="utf-8"))
    im = cv2.imread(os.path.join(HERE, "refs", name, "%02d.jpg" % N))
    if im is None: sys.exit("❌ 책 그림을 못 읽는다: refs/%s/%02d.jpg" % (name, N))
    H, W = im.shape[:2]
    gf = spec.get("grid_fit")
    if gf:
        fj = json.load(open(os.path.join(HERE, "refs", name, "fits", gf["file"]), encoding="utf-8"))
        extra = grid_points(fj, gf); spec["pts"] = spec["pts"] + extra
        print("격자 점 %d개 추가(%s, holefit 가 실제로 찾은 구멍만)" % (len(extra), gf["file"]))
    r = solve(spec, W, H)
    C, fwd, up, right = cam_from(r["rv"], r["tv"])
    grid = spec.get("grid"); tgt = spec.get("axes_target")
    if tgt is None and grid:
        o = np.array(grid["origin"], float); tgt = (o + np.array(grid["col"], float) * 0 + np.array(grid["row"], float) * 0).tolist()
    az, el, rad = angles(C, tgt if tgt is not None else r["obj"].mean(axis=0))
    print("fov %g 평균 %.2f 최대 %.2f px 점별 %s | theta %.2f phi %.2f" % (r["fov"], r["mean"], r["max"], [round(float(v), 1) for v in r["per"]], math.radians(az), math.radians(90 - el)))
    print("(theta·phi 는 보는 중심(axes_target·grid 가운데)에 따라 달라지는 참고값 — 카메라 파일은 --out 결과를 mkfit3d 에 넣어 만든다)")
    if len(r["kinds"]) > 1: print("종류별 평균 오차(px): " + ", ".join("%s %.2f" % (k, v) for k, v in sorted(r["kinds"].items())) + "  ← 한쪽만 크면 그쪽 가정(줄·높이·칸 번호)이 틀린 것")
    for g, v in r["groups"].items(): print("그룹 %s 이동(x,z) = (%.2f, %.2f)" % (g, v[0], v[1]))
    for l, v in r["levels"].items(): print("높이 %s = %.2f" % (l, v))
    if "--out" in sys.argv:
        outp = sys.argv[sys.argv.index("--out") + 1]
        out = {"fov": r["fov"], "pts": [[o.tolist(), p["px"]] for o, p in zip(r["obj"], spec["pts"])], "note": spec.get("note", "") + " — composefit 풀이(그룹 이동 %s, 높이 %s)" % (
            {g: [round(x, 2) for x in v] for g, v in r["groups"].items()}, {l: round(v, 2) for l, v in r["levels"].items()})}
        if grid: out["grid"] = grid
        if tgt is not None: out["axes_target"] = tgt
        json.dump(out, open(outp, "w", encoding="utf-8"), ensure_ascii=False); print("쓴 파일:", outp, "→ python mkfit3d.py %s %d <라벨> <칸> <줄> %s --허용 2.5" % (name, N, outp))
    if r["mean"] > 2.5: print("⚠ 평균 오차 2.5px 초과 — 링 픽셀 읽기·점 짝·가정(줄·높이)을 다시 본다")


if __name__ == "__main__":
    main()
