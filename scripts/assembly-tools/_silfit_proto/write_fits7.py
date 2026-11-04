import sys, json, math, shutil, pickle
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools"); sys.path.insert(0, ".")
import numpy as np, cv2
import silfit7 as S
from pnp import cam_from, angles
sys.stdout.reconfigure(encoding="utf-8")
AT = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/"; D = AT + "refs/steercar/"; STEP = S.STEP; NN = "%02d" % STEP
res = pickle.load(open(S.SP + "sil%d_res.pkl" % STEP, "rb")); f, hyp, p = res[0]; iou = 1 - f
az, el, dist, fov, ox, oy, g = p; rv, tv, K = S.mk_cam(az, el, dist, fov, ox, oy)
P = lambda q: cv2.projectPoints(np.array(q, np.float64).reshape(-1, 3), rv, tv, K, None)[0].reshape(-1, 2)
C, fwd, up, right = cam_from(rv, tv); tgt = np.array([0, 0, -10.0]); a2, e2, rad = angles(C, tgt); th, ph = math.radians(a2), math.radians(90 - e2)
zs, xs = hyp; roll = math.degrees(math.asin(max(-1, min(1, float(right[1])))))
print("IoU %.3f fov %.1f 간격 %.1f theta %.2f phi %.2f roll %.1f" % (iou, fov, g, th, ph, roll), "가설", hyp)
Bh = [P([(-10 + 10 * i), 0, 0])[0] for i in range(3)]
zc = zs * (20.0 + g); RAh = S.RA if zs < 0 else np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], float)
Ah = [P(RAh @ np.array([-10 + 10 * i, 0, 0.0]) + np.array([10.0 * xs, 0, zc]))[0] for i in range(3)]
mk = lambda hs: [[i + 1, 1, round(float(h[0]), 2), round(float(h[1]), 2)] for i, h in enumerate(hs)]
base = {"cols": 3, "rows": 1, "tool": "sil-fit", "err_px": round(1 - iou, 3), "max_err_px": None, "est": [],
        "evidence": {"sources": ["책 그림 블록 실루엣 ↔ 모델 실루엣(3단블록 둘) 겹침 최대화(자동, 눈으로 점을 읽지 않음). 가설 4가지(끼우는 블록이 받는 블록의 −Z/+Z 쪽 × 링 구멍 +X/−X 끝) 중 IoU 1등 %.3f, 2등 %.3f" % (iou, res[1][0] and 1 - res[1][0])], "iou": round(iou, 3), "fov": round(fov, 2), "gap_mm": round(g, 2), "theta": round(th, 3), "phi": round(ph, 3),
                     "hypothesis": "끼우는 블록 끝 돌기 p1 → 받는 블록 큰 구멍(링, 화면 왼쪽 끝), 돌기 면 위, 구멍축 = 세계 Z", "silhouette_pieces": "몸통+돌기 6+끝 돌기 2 (한 블록)"}}
json.dump(dict(base, pts=mk(Bh), name="steercar %d번 P: 받는 3단블록 구멍 h1~h3 — 실루엣 겹침 카메라(IoU %.3f, fov %.1f)로 투영 — silfit" % (STEP, iou, fov), origin_cell=[2, 1], visible_cells=[[1, 1], [2, 1], [3, 1]]), open(D + "fits/%s_P.json" % NN, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(dict(base, pts=mk(Ah), name="steercar %d번 U: 끼우는 3단블록 구멍 h1~h3 — 같은 카메라로 투영 — silfit" % STEP, origin_cell=[2, 1], visible_cells=[[1, 1], [2, 1], [3, 1]]), open(D + "fits/%s_U.json" % NN, "w", encoding="utf-8"), ensure_ascii=False)
o = np.array([0, 0, -10.0]); ax = {}
for k, d in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    v = P(o + 20 * np.array(d))[0] - P(o)[0]; v = v / np.linalg.norm(v) * 55; ax[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
json.dump({"global": ax, "fit": {"from": "%s_P.json" % NN, "err_px": round(1 - iou, 3), "points": 0, "theta": round(th, 2), "phi": round(ph, 2), "method": "실루엣 겹침 IoU %.3f" % iou, "origin_world": [0, 0, -10]}, "no_rotate": True}, open(D + "%s_axes.json" % NN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(D + "03_lv.json", D + "%s_lv.json" % NN); print("축", ax, "gap", round(g, 1), "roll", round(roll, 1))
