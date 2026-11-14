# 번호 하나의 카메라(theta·phi)와 축선 방향(+X·+Y·+Z)을 "그 번호의 격자 점"에서 계산해 <번호>_axes.json 에 쓴다.
#   앞 번호 값을 복사하거나 눈대중으로 쓰지 않기 위한 도구다(2026-10-11 투석기 16번: 15번 값에서 출발해 적은 것을 관리자가 지적).
#   python axes_fit.py <이름> <번호> <라벨> <칸수> <줄수> <칸방향> <줄방향> [간격=10]
#     라벨 = fits/NN_<라벨>.json (한 판의 격자 점, 원본 그림 좌표). 판이 눕혀 있으면(홀면 위) 칸·줄이 X·Z, 서 있으면 칸은 X 또는 Z 이고 줄은 ±Y 다. 책 그림에서 판이 서 있는지 눕는지를 먼저 읽고 정한다.
#     칸방향·줄방향 = +X -X +Y -Y +Z -Z 중 하나(칸이 늘어나는 쪽이 세계 어느 쪽인지). 두 방향은 서로 다른 축이어야 한다(칸 +X 면 줄은 ±Z — 눕힌 판, 또는 ±Y — 서 있는 판).
#   출력: 맞춘 오차(px)·theta·phi·화면에서 +X +Y +Z 가 가리키는 방향. 오차 2px 넘으면 칸·줄 방향이 거울이거나 점이 틀린 것이니 쓰지 않는다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles

def main():
    if len(sys.argv) < 8: sys.exit(__doc__)
    name, step, label, cols, rows, cd, rd = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), sys.argv[6], sys.argv[7]
    pitch = float(sys.argv[8]) if len(sys.argv) > 8 else 10.0
    D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", name)
    f = json.load(open(os.path.join(D, "fits", "%02d_%s.json" % (step, label)), encoding="utf-8"))
    ax = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
    if cd not in ax or rd not in ax or abs(sum(a * b for a, b in zip(ax[cd], ax[rd]))) == 1: sys.exit("칸방향·줄방향은 서로 다른 축이어야 한다(+X -X +Y -Y +Z -Z)")
    cvec = np.array(ax[cd], float); rvec = np.array(ax[rd], float)
    # 칸·줄 방향이 그 번호 모델의 판 긴 축과 맞는지 대조한다(규칙 E2·C8 — 배틀로봇 1번: 칸 +X 로 줄 줄 알았는데 모델 판의 긴 변은 Z 라 카메라가 책과 90° 달랐다). 확실한 불일치만 막는다.
    try:
        import asmlib
        _D = [_q for _st in json.load(open(asmpath.ap(name, "_asm.json"), encoding="utf-8"))["steps"][:step] for _q in _st.get("parts", [])]   # 번호 칸에는 그 번호에 새로 놓은 부품만 있다 — 앞 번호까지 쌓인 부품 전부로 본다
        _dims = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dims.json"), encoding="utf-8"))
        _long = set()
        for _p in _D:
            _dm = _dims.get(_p.get("n"))
            if not _dm or "r" not in _p: continue
            _r = _p["r"]   # 이 번호 시점의 자세: 나중 번호에서 옮기는 값(move·poseAt)은 그 번호가 되기 전엔 쓰지 않는다
            if (_p.get("move") or {}).get("at", 10 ** 6) <= step and "r" in _p["move"]: _r = _p["move"]["r"]
            _pa = [int(k_) for k_ in (_p.get("poseAt") or {}) if int(k_) <= step]
            if _pa and "r" in _p["poseAt"][str(max(_pa))]: _r = _p["poseAt"][str(max(_pa))]["r"]
            _s = sorted([_dm[0], _dm[2]], reverse=True)   # 판 눕힌 면(가로 x 세로) 길이 — 두께(y)는 뺀다
            if abs(_s[0] - max(cols, rows) * pitch) < 1 and _s[1] <= min(cols, rows) * pitch + 1 and _s[1] >= 30 - 1:   # 격자가 판 여러 장(예: 315프레임 둘 = 15×6)이어도 긴 변 길이로 잡는다
                _v = asmlib.euler_to_R(_r) @ np.array([1.0, 0, 0] if _dm[0] >= _dm[2] else [0, 0, 1.0])
                _k = int(np.argmax(np.abs(_v)))
                if abs(abs(_v[_k]) - 1) < 1e-3: _long.add("XYZ"[_k])
        if len(_long) == 1 and cols != rows:
            _L = next(iter(_long)); _axis = cd[-1] if cols > rows else rd[-1]
            if _axis != _L: sys.exit("❌ 칸·줄 방향이 모델과 안 맞는다: 이 번호 모델의 판(%d×%d) 긴 변은 %s 축인데 긴 쪽(%s)을 %s 로 줬다 — 긴 변 방향을 %s 로 다시 준다(거울 후보는 오차가 같으니 블록이 놓인 쪽(앞 판)으로 가른다). 파일은 쓰지 않았다." % (max(cols, rows), min(cols, rows), _L, "칸" if cols > rows else "줄", _axis, _L))
    except SystemExit: raise
    except Exception as _e: print("(판 긴 축 대조를 못 했다: %s)" % _e)
    obj, img = [], []
    for c, r, x, y in f["pts"]:
        u, v = (c - 1) - (cols - 1) / 2.0, (r - 1) - (rows - 1) / 2.0
        obj.append(list(pitch * (u * cvec + v * rvec))); img.append([x, y])
    if f.get("xyz"):   # xyz: 점마다 3D 세계 좌표를 직접 준다(꺾인 프레임 구멍처럼 격자가 아닌 점 — 칸·줄 방향은 쓰지 않는다). 가운데로 옮겨서 카메라 각도만 구한다.
        obj = [list(q) for q in f["xyz"]]; img = [[x, y] for c, r, x, y in f["pts"]]
        obj = np.array(obj, float); obj = (obj - obj.mean(axis=0)).tolist()
    obj = np.array(obj, np.float32); img = np.array(img, np.float32)
    im = cv2.imread(os.path.join(D, "%02d.jpg" % step)); H, W = im.shape[:2]
    best = None; cands = []
    for fov in (20, 25, 30, 35, 40, 45, 50):
        if f.get("xyz"):   # 한 평면 위의 점(xyz): 위에서 보는 해와 아래에서 보는 거울 해를 IPPE 로 둘 다 구해 후보에 넣는다(아래 _ok 가 위에서 보고 위쪽이 위인 해를 고른다)
            fl = (H / 2) / math.tan(math.radians(fov) / 2); K_ = np.array([[fl, 0, W / 2], [0, fl, H / 2], [0, 0, 1]], float)
            _n, rvs_, tvs_, errs_ = cv2.solvePnPGeneric(obj.astype(np.float64), img.astype(np.float64), K_, None, flags=cv2.SOLVEPNP_IPPE)
            for rv_, tv_, e_ in zip(rvs_, tvs_, errs_): cands.append(((float(np.ravel(e_)[0]), rv_, tv_, K_), fov))
            continue
        r = fit(obj, img, W, H, fov)
        if r: cands.append((r, fov))
    # 주점 탐색(2026-11-14 꼬마기사 1번): 책 그림이 잘려 한가운데가 주점이 아니면 오차가 크다(7.5px) — 한가운데로 2px 안에 안 맞을 때만 주점·시야각을 훑어 본다(pnp.fit 의 cx,cy)
    if not f.get("xyz") and min([c[0][0] for c in cands] or [99]) > 2:
        for fov in (30, 40, 50, 60, 70, 80):
            for dx in range(-500, 501, 100):
                for dy in range(-500, 501, 100):
                    try: r = fit(obj, img, W, H, fov, W / 2 + dx, H / 2 + dy)
                    except Exception: continue
                    if r: cands.append((r, fov))
    # 평면 위 점(판 구멍)만으로 푸는 PnP 는 위에서 내려다보는 해와 아래에서 올려다보는 거울 해가 거의 같은 오차로 나온다(드롭체커 27번: 0.88 vs 0.90px).
    #   오차만 보면 거울 해(phi>1.55)나 카메라가 뒤집힌 해(up_y<0)가 뽑힐 수 있어서, 위에서 내려다보고 위쪽이 위인 해(phi≤1.55·up_y>0)를 먼저 고른다(2026-10-13).
    def _ok(c):
        (e_, rv_, tv_, K_), fov_ = c; C_, fwd_, up_, right_ = cam_from(rv_, tv_); az_, el_, rad_ = angles(C_, (0, 0, 0))
        return math.radians(90 - el_) <= 1.55 and float(up_[1]) > 0
    good = [c for c in cands if _ok(c)]
    for c in (good or cands):
        if best is None or c[0][0] < best[0][0]: best = c   # c = (r, fov), r = (오차, rv, tv, K)
    if not best: sys.exit("카메라를 못 맞췄다(점이 한 줄이거나 너무 적다)")
    if cands and not good: print("⚠ 위에서 내려다보는(phi≤1.55, 위쪽이 위) 해가 없다 — 칸·줄 방향(거울)을 다시 본다")
    (e, rv, tv, K), fov = best
    C, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(C, (0, 0, 0))
    P = lambda v: cv2.projectPoints(np.float32([v]), rv, tv, K, None)[0][0][0]
    o = P([0, 0, 0]); d = {}
    for k, v in (("X", [pitch, 0, 0]), ("Y", [0, pitch, 0]), ("Z", [0, 0, pitch])):
        w = P(v) - o; s = 55.0 / max(abs(w[0]), abs(w[1]), 1e-6) if k != "Y" else 55.0 / max(abs(w[1]), 1e-6)
        d[k] = [round(float(w[0] * s), 1), round(float(w[1] * s), 1)]
    out = {"global": d, "fit": {"from": "%02d_%s.json" % (step, label), "err_px": round(float(e), 2), "points": len(obj), "theta": round(math.radians(az), 2), "phi": round(math.radians(90 - el), 2), "cols": cd, "rows": rd, "fov": fov, "cx": round(float(K[0][2]), 1), "cy": round(float(K[1][2]), 1)}}
    out["rotate_to"] = cd[-1]   # 구멍 줄(칸 방향)이 놓인 세계 축 — refs_rect 가 그림을 이 축선과 같은 방향으로 작은 각도만 돌린다(규칙 E3). 안 적으면 격자 줄과 축선이 어긋나 보인다(사용자 지적 2026-11-10: 홀라인·xyz축 그림)
    if rd[-1] == "Y": out["column_axis"] = "Y"   # 서 있는 판은 가운데 열이 Z 가 아니라 Y 선을 따른다(refs_rect 머리말)
    json.dump(out, open(os.path.join(D, "%02d_axes.json" % step), "w", encoding="utf-8"), ensure_ascii=False)
    _roll = math.degrees(math.asin(max(-1, min(1, float(right[1])))))
    try:   # 롤은 뷰어 카메라로 만들 수 없으니 축 파일에도 적는다(롤이 큰 번호는 책과 비슷한 방위의 눈 카메라를 쓸 수 있다 — violations cam 이 인정)
        out["fit"]["roll"] = round(_roll, 1); json.dump(out, open(os.path.join(D, "%02d_axes.json" % step), "w", encoding="utf-8"), ensure_ascii=False)
    except Exception: pass   # 화면 가로축이 수평에서 기운 정도 — 뷰어 카메라는 기울이지(roll) 못하니 0 에 가까워야 한다
    print("카메라 roll %.1f°(0 에 가까워야 뷰어 카메라로 같은 그림이 나온다)" % _roll)
    print("오차 %.2fpx (%d점) theta %.2f phi %.2f  X%s Y%s Z%s" % (e, len(obj), out["fit"]["theta"], out["fit"]["phi"], d["X"], d["Y"], d["Z"]))
    if out["fit"]["phi"] > 1.55: print("⚠ phi 가 1.55(≈90°)를 넘는다 = 판 아래에서 올려다보는 해 — 거울로 맞은 것이다. 책은 위에서 내려다보니 줄방향(또는 칸방향)을 반대로 준다.")
    if e > 2: print("⚠ 오차가 2px 를 넘는다 — 칸·줄 방향(거울)이나 격자 점을 다시 본다. 이 값을 쓰지 않는다.")

main()
