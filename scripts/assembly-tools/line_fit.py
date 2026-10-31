# 한 줄 부품(1×N 구멍 막대: 115프레임·15프레임·17프레임·19프레임 …)의 홀라인(구멍 격자)을 도구로 만든다 — 2026-10-31 steercar 3번, 사용자 지시 "한 줄 부품이 많은데 그게 안 통과하게 만든 규칙부터 잘못이다 → 해결하거나 규칙을 바꿔라".
#   왜 필요한가: holefit 는 점들로 호모그래피를 다시 구하는데 한 줄이면 점이 전부 일직선이라 풀리지 않는다(구멍 0개 배정). frame_fit 은 "한 직선이면 거부", infer_grid 는 막대 구멍(안쪽이 배경과 같은 흰색)에서 선명한 조각을 못 찾는다.
#   방법: 같은 번호의 다른 부품(판 등) 격자에서 카메라를 푼다(그림은 하나라서 카메라가 같다) → 막대의 위치(높이·길이 방향·폭 방향 3개 값)만 crop_ticks 로 읽은 구멍 중심들에 맞춰 푼다 → 구멍 N개를 그 카메라로 투영해 fits 에 쓴다.
#   python line_fit.py <이름> <번호> <라벨> <기준라벨> "<k>:x,y;<k>:x,y;…" --원점 x,y,z --방향 dx,dy,dz [--칸수 15]
#     기준라벨   같은 번호의 판 격자 라벨(예: P) — fits/NN_<기준라벨>.json 의 점(칸·줄 → 화면)과 판 좌표(가운데 원점·10mm 간격·윗면 높이 5)로 카메라를 푼다. 기준 격자 오차(err_px)가 2.5px 넘으면 쓰지 않는다.
#     "k:x,y"   막대 구멍 k(1부터)의 중심 픽셀(원본 그림 좌표) — crop_ticks.py 로 ≤100×100px 창에서 읽는다(구멍 한 개의 타원 전체 가운데). 6개 이상.
#     --원점    구멍 가운데((N+1)/2 번째) 의 판 좌표 시작값 x,y,z(높이는 대략 값 — 도구가 푼다). 판 좌표 = 기준 판 가운데가 원점, 칸 +X·줄 +Z, 판 바닥 0.
#     --방향    구멍 번호가 늘어나는 쪽의 판 좌표 단위 방향(예: 구멍 1 이 +Z 끝이면 0,0,-1).
#   통과 기준(규칙 점검과 같다, infer_grid 앵커와 같은 값): 읽은 구멍 6개 이상 · 평균 ≤2.5px · 최대 ≤4.5px · 기준 격자 err ≤2.5px. 미달이면 fits 를 쓰지 않는다 — 읽기를 다시 한다(점을 빼서 맞추지 않는다).
#   출력: fits/NN_<라벨>.json(tool "line-fit", evidence 에 카메라 근거·읽은 수·오차·푼 위치) — rulecheck 는 ⚠ "사용자 확인 권장"으로 본다(진행은 막지 않음).
import sys, os, json, math
import numpy as np, cv2
from scipy.optimize import least_squares
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit
a = sys.argv[1:]
if len(a) < 5: sys.exit(__doc__)
name, step, label, ref, spec = a[0], int(a[1]), a[2], a[3], a[4]
def opt(k, default=None):
    return a[a.index(k) + 1] if k in a else default
org = [float(v) for v in opt("--원점").split(",")]; dr = np.array([float(v) for v in opt("--방향").split(",")]); dr = dr / np.linalg.norm(dr)
D = os.path.join(HERE, "refs", name) + os.sep
reads = {}
for tok in spec.split(";"):
    k, xy = tok.split(":"); x, y = [float(v) for v in xy.split(",")]; reads[int(k)] = (x, y)
if len(reads) < 6: sys.exit("읽은 구멍이 6개 미만이다(%d) — crop_ticks 로 더 읽는다" % len(reads))
R = json.load(open(D + "fits/%02d_%s.json" % (step, ref), encoding="utf-8"))
cols, rows = R["cols"], R["rows"]
refErr = float(R.get("err_px") if R.get("err_px") is not None else (R.get("evidence") or {}).get("anchor_mean_px", 99))   # 기준 격자가 스스로 보고한 오차
if refErr > 2.5: sys.exit("기준 격자 %s 오차가 크다(%.2fpx > 2.5) — 카메라를 못 믿는다" % (ref, refErr))
P3 = lambda c, r: [(c - (cols + 1) / 2.0) * 10.0, 5.0, (r - (rows + 1) / 2.0) * 10.0]   # 기준 판 윗면 높이 5 (판 가운데 원점)
obj = [P3(c, r) for c, r, x, y in R["pts"]]; img = [[x, y] for c, r, x, y in R["pts"]]
im = cv2.imread(D + "%02d.jpg" % step); Hh, Ww = im.shape[:2]; best = None
for fov in range(15, 71, 5):
    r_ = fit(obj, img, Ww, Hh, fov)
    if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
if not best: sys.exit("기준 격자로 카메라를 못 풀었다")
(_, rv, tv, K), fov = best
proj = lambda P: cv2.projectPoints(np.array(P, np.float64).reshape(-1, 3), np.asarray(rv, np.float64), np.asarray(tv, np.float64), np.asarray(K, np.float64), None)[0].reshape(-1, 2)
N = int(opt("--칸수", max(reads))); mid = (N + 1) / 2.0
hole = lambda k, p: [org[i] + p[i] + dr[i] * (k - mid) * 10 for i in range(3)]   # p = 위치 보정(x,y,z)
ks = sorted(reads); target = np.array([reads[k] for k in ks], float)
res = least_squares(lambda p: (proj([hole(k, p) for k in ks]) - target).ravel(), [0.0, 0.0, 0.0], diff_step=1e-3)
er = np.hypot(*(proj([hole(k, res.x) for k in ks]) - target).T); mean, mx = float(er.mean()), float(er.max())
print("기준 격자 %s: 카메라 fov %d (기준 오차 %.2fpx)" % (ref, fov, refErr))
print("푼 막대 위치 보정 x %+.2f y %+.2f z %+.2f → 구멍 가운데 (%.1f, %.1f, %.1f)" % (res.x[0], res.x[1], res.x[2], org[0] + res.x[0], org[1] + res.x[1], org[2] + res.x[2]))
print("읽은 %d개 오차 평균 %.2f 최대 %.2f px %s" % (len(ks), mean, mx, {k: round(float(e), 1) for k, e in zip(ks, er)}))
if mean > 2.5 or mx > 4.5: sys.exit("❌ 기준 미달(평균 ≤2.5·최대 ≤4.5px) — fits 를 쓰지 않는다. 오차가 큰 구멍을 더 작은 창에서 다시 읽는다(점을 빼서 맞추지 않는다).")
pts = [[k, 1, round(float(q[0]), 2), round(float(q[1]), 2)] for k, q in zip(range(1, N + 1), proj([hole(k, res.x) for k in range(1, N + 1)]))]
out = {"origin_cell": [int(round(mid)), 1], "visible_cells": [[k, 1] for k in ks], "cols": N, "rows": 1, "pts": pts, "tool": "line-fit", "err_px": round(mean, 2), "max_err_px": round(mx, 2), "est": [[k, 1] for k in range(1, N + 1) if k not in reads],
       "name": "%s %d번 %s: 한 줄 부품 격자 — 같은 번호 %s 격자의 카메라(fov %d, 오차 %.2fpx)로 구멍 %d개를 투영, 막대 위치 3값을 읽은 구멍 %d개에 맞춤(평균 %.2f·최대 %.2f px) — line_fit.py" % (name, step, label, ref, fov, refErr, N, len(ks), mean, mx),
       "evidence": {"sources": ["%s 격자 카메라" % ref, "crop_ticks 로 읽은 구멍 %d개" % len(ks)], "camera_from": "%02d_%s.json" % (step, ref), "camera_err_px": round(refErr, 2), "fov": fov, "readings": len(ks), "reading_ids": ks,
                    "pose_shift": [round(float(v), 3) for v in res.x], "hole_mid": [round(org[i] + float(res.x[i]), 2) for i in range(3)], "direction": [float(v) for v in dr]}}
os.makedirs(D + "fits", exist_ok=True); json.dump(out, open(D + "fits/%02d_%s.json" % (step, label), "w", encoding="utf-8"), ensure_ascii=False)
print("✅ 저장 — fits/%02d_%s.json (rulecheck 는 ⚠ 사용자 확인 권장으로 본다)" % (step, label))
