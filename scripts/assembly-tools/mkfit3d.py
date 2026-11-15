# 3D 확정 점들로 카메라를 풀어 격자 fits·축(_axes.json)을 만든다 — 판이 가려지거나 비스듬해 holefit·infer_grid 가 안 되는 번호용(배틀바이크 4번, 2026-10-27).
#   python mkfit3d.py <이름> <번호> <라벨> <칸> <줄> <spec.json>
#   spec.json = {"pts": [[[x,y,z],[px,py]], ...](모델 3D ↔ 책 픽셀 8개 내외, 평면 아닌 점이 섞여야 안정), "fov": 25,
#                "grid": {"origin":[x,y,z] 칸1줄1 구멍 위치, "col":[dx,dy,dz] 칸 +1, "row":[dx,dy,dz] 줄 +1}  (구멍 격자는 10mm 간격),
#                "axes_target":[x,y,z](축선 원점, 기본 격자 가운데), "note":"근거"}
#   선택: --허용 <평균 px>  (기본 3 — 올리면 거친 값, 근거에 적을 것)
#   거울 해: pts 가 전부 한 평면(누운 판이든 서 있는 판이든) 위면 평면 앞·뒤 두 해가 같은 오차로 맞는다. spec 에 "check": [[[x,y,z],[px,py]], …]
#           (평면에서 5mm 넘게 떨어진 단서 점 — T축 끝·블록 돌기 끝·앞 번호 부품 구멍. 풀이에는 안 쓰고 두 해를 가르는 데만 쓴다)를 주면 단서 오차가 작은 해를 쓴다.
#           안 주면 예전처럼 고르고(위에서 보는 해) 두 해를 모두 출력해 ⚠ 로 알린다 — 그 값은 거울일 수 있으니 단서 점을 주고 다시 돌린다.
#   하는 일: PnP(fit) 로 카메라를 풀고 점별 오차(px)·theta·phi 를 출력, fits/NN_<라벨>.json(pts=격자 점 투영, xyz3d·xyz3d_img=입력 점, tool="infer3d") 과 NN_axes.json 을 쓴다. 평균 오차 3px 초과면 쓰지 않는다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit, cam_from, angles, planar_pair, check_err
name, N, lab, cols, rows, spec = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), json.load(open(sys.argv[6], encoding="utf-8"))
D = os.path.join(HERE, "refs", name) + os.sep
im = cv2.imread(D + "%02d.jpg" % N); H, W = im.shape[:2]
obj = [p for p, q in spec["pts"]]; img = [q for p, q in spec["pts"]]
best = None
for fv in ([spec["fov"]] if spec.get("fov") else range(15, 71, 5)):
    r = fit(obj, img, W, H, fv)
    if r and (best is None or r[0] < best[0][0]): best = (r, fv)
if not best: sys.exit("풀이 실패")
(e, rv, tv, K), fv = best
CHK = spec.get("check") or []; BYCHK = False; ALT = None
_pair = planar_pair(obj, img, K)
if len(_pair) == 2:
    def _tp(rv_, tv_):
        C_ = cam_from(rv_, tv_)[0]; o_ = np.mean(np.array(obj, float), axis=0); az_, el_, _r = angles(C_, o_); return math.radians(az_), math.radians(90 - el_)
    _nrm = np.linalg.svd(np.array(obj, float) - np.mean(obj, axis=0))[2][-1]
    _far = [abs(float((np.array(p_, float) - np.mean(obj, axis=0)) @ _nrm)) for p_, q_ in CHK]
    print("한 평면 위의 점 — 거울 해 2개:")
    for _i, (_e, _rv, _tv) in enumerate(_pair):
        print("   해%d  평균 %.2fpx  theta %.2f phi %.2f%s" % ((_i + 1, _e) + _tp(_rv, _tv) + ((" | 단서 점 오차 %.1fpx" % check_err(_rv, _tv, K, CHK),) if CHK else ("",))))
    if CHK and max(_far) < 5: print("⚠ 단서 점(check)이 평면에서 %.1fmm 밖에 안 떨어져 두 해를 못 가른다 — 평면 밖 점(T축 끝·돌기 끝 등)을 준다" % max(_far)); CHK = []
    if CHK:
        _s = sorted(_pair, key=lambda t_: check_err(t_[1], t_[2], K, CHK)); _c0, _c1 = check_err(_s[0][1], _s[0][2], K, CHK), check_err(_s[1][1], _s[1][2], K, CHK)
        (e, rv, tv) = _s[0]; BYCHK = True; ALT = _tp(_s[1][1], _s[1][2])
        print("   → 단서 점 %d개로 고름: %.1fpx (다른 해 %.1fpx)%s" % (len(CHK), _c0, _c1, "" if _c1 > 2 * _c0 + 2 else "  ⚠ 두 해의 단서 오차 차이가 작다 — 단서 점을 더 멀리·더 많이 준다"))
    else:
        print("⚠ 두 해 가운데 어느 쪽이 책과 같은지 이 점들만으로는 모른다 — spec 에 \"check\"(평면 밖 단서 점)를 주고 다시 돌린다. 지금은 예전 방식(위에서 보는 해)으로 고른다.")
        ALT = next((_tp(_rv, _tv) for _e, _rv, _tv in _pair if np.linalg.norm(np.ravel(_rv) - np.ravel(rv)) > 1e-3), None)
pj = cv2.projectPoints(np.float32(obj), rv, tv, K, None)[0].reshape(-1, 2); er = np.hypot(*(pj - np.array(img)).T)
tgt = spec.get("axes_target")
g = spec["grid"]; o = np.array(g["origin"], float); dc = np.array(g["col"], float); dr = np.array(g["row"], float)
if tgt is None: tgt = (o + dc * (cols - 1) / 2 + dr * (rows - 1) / 2).tolist()
MIRROR = False
C, fwd, up, right = cam_from(rv, tv)
LYING = "--눕힌좌표" in sys.argv   # 입력 3D 점이 눕힌 좌표(위 = −z, 서 있는 y = 20 − z, 서 있는 z = y)면 카메라 각도는 뷰어의 서 있는 좌표로 바꿔 계산한다(양팔저울 19~22번, 2026-11-05: 안 바꾸면 theta·phi 가 엉뚱한 값이 나온다)
if LYING:
    _cv = lambda p: np.array([p[0], 20 - p[2], p[1]], float)
    az, el, rad = angles(_cv(C), _cv(tgt))
else:
    az, el, rad = angles(C, tgt)
th, ph = math.radians(az), math.radians(90 - el)
if not BYCHK and LYING and ph > 1.55 and all(abs(q[2] - obj[0][2]) < 3 for q in obj):   # 한 평면(z 일정)의 점은 평면 반대쪽 거울 해가 같이 맞는다 — 카메라가 판 아래(φ>π/2)로 나오면 위쪽 해로 바꾼다
    ph = math.pi - ph; MIRROR = True
if not BYCHK and ph > 1.55 and not LYING and all(abs(q[1] - obj[0][1]) < 3 for q in obj):   # 한 평면의 점들은 판 반대쪽 거울 해가 같이 맞는다 — 카메라가 판 아래(φ>1.55)로 나오면 판 위쪽 해(φ→π−φ, 같은 θ)로 바꾼다
    ph = math.pi - ph; MIRROR = True
print("fov %d 평균 %.2f 최대 %.2f px 점별 %s | theta %.2f phi %.2f roll %.1f°" % (fv, er.mean(), er.max(), [round(float(v), 1) for v in er], th, ph, math.degrees(math.asin(max(-1, min(1, float(right[1])))))))
LOOSE = float(sys.argv[sys.argv.index("--허용") + 1]) if "--허용" in sys.argv else 3.0   # 평균 오차 허용치(px) — 올리면 근거 글에 "거친 값"을 적는다
if er.mean() > LOOSE or er.max() > 2 * LOOSE: sys.exit("❌ 오차 기준(평균 %.1f·최대 %.1fpx) 미달 — 쓰지 않는다" % (LOOSE, 2 * LOOSE))
P = lambda q: cv2.projectPoints(np.float32([q]), rv, tv, K, None)[0][0][0]
pts = [[c, r, round(float(P(o + dc * (c - 1) + dr * (r - 1))[0]), 2), round(float(P(o + dc * (c - 1) + dr * (r - 1))[1]), 2)] for c in range(1, cols + 1) for r in range(1, rows + 1)]
out = {"cols": cols, "rows": rows, "pts": pts, "name": "%s %d번 %s: 3D 확정 점 %d개 PnP(평균 %.2f px)로 푼 카메라로 격자를 투영 — %s" % (name, N, lab, len(obj), er.mean(), spec.get("note", "")),
       "est": [[c, r] for c in range(1, cols + 1) for r in range(1, rows + 1)], "err_px": round(float(er.mean()), 2), "max_err_px": round(float(er.max()), 2), "tool": "infer3d", "xyz3d": obj, "xyz3d_img": img,
       "evidence": {"sources": ["3D 점 %d개 PnP" % len(obj)], "fov": fv, "theta": round(th, 3), "phi": round(ph, 3)}}
os.makedirs(D + "fits", exist_ok=True); json.dump(out, open(D + "fits/%02d_%s.json" % (N, lab), "w", encoding="utf-8"), ensure_ascii=False)
o0 = np.array(tgt, float); p0 = P(o0)
ax = {}
for k, v in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    d = P(o0 + 20 * np.array(v)) - p0; d = d / np.linalg.norm(d) * 55; ax[k] = [round(float(d[0]), 1), round(float(d[1]), 1)]
if MIRROR: ax["Y"] = [-ax["Y"][0], -ax["Y"][1]]   # 거울 해: 위(+Y) 방향이 반대로 그려진다
ad = {"global": ax, "fit": {"from": "%02d_%s.json" % (N, lab), "err_px": round(float(er.mean()), 2), "points": len(obj), "theta": round(th, 2), "phi": round(ph, 2), "origin_world": [round(float(v), 1) for v in o0]}, "no_rotate": True}
if ALT: ad["fit"]["mirror"] = {"by": "check" if BYCHK else None, "other": {"theta": round(ALT[0], 2), "phi": round(ALT[1], 2)}}   # 거울 해가 있었던 번호 — by 가 없으면 단서 없이 고른 값(확인 필요)
json.dump(ad, open(D + "%02d_axes.json" % N, "w", encoding="utf-8"), ensure_ascii=False)
print("쓴 파일: fits/%02d_%s.json, %02d_axes.json" % (N, lab, N))
