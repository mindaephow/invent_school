import sys, json, math, shutil, pickle, os
os.environ["STEP"] = "8"; sys.argv = ["x"]
sys.path.insert(0, "."); sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
import silfit8 as F, silfit7 as S7
from pnp import cam_from, angles
sys.stdout.reconfigure(encoding="utf-8")
D = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/refs/steercar/"
res = pickle.load(open(S7.SP + "sil8_res.pkl", "rb")); f, hyp, p = res[0]; iou = 1 - f
az, el, dist, fov, ox, oy, hover = p[:7]; rv, tv, K = S7.mk_cam(az, el, dist, fov, ox, oy)
P = lambda q: cv2.projectPoints(np.array(q, np.float64).reshape(-1, 3), rv, tv, K, None)[0].reshape(-1, 2)
C, fwd, up, right = cam_from(rv, tv); tgt = np.array([0, 10.0, -40.0]); a2, e2, rad = angles(C, tgt); th, ph = math.radians(a2), math.radians(90 - e2)
roll = math.degrees(math.asin(max(-1, min(1, float(right[1])))))
print("IoU %.3f fov %.1f 띄움 %.1f theta %.2f phi %.2f roll %.1f" % (iou, fov, hover, th, ph, roll))
RF = F.RF_A; h9 = np.array([-10.0, 17.5 + hover, -5.0]); org = h9 - RF @ np.array([F.HF["h9"][0], 0.0, F.HF["h9"][1]])
W = lambda h: org + RF @ np.array([F.HF[h][0], 0.0, F.HF[h][1]])
fh = [P(W("h%d" % i))[0] for i in range(1, 10)]
pegs = [W("h1"), W("h3"), W("h6"), W("h8"), W("h9")]; pegtop = [np.array([w[0], 20.0, w[2]]) for w in pegs]; ph_px = [P(q)[0] for q in pegtop]
mk = lambda hs: [[i + 1, 1, round(float(h[0]), 2), round(float(h[1]), 2)] for i, h in enumerate(hs)]
ev = {"sources": ["책 그림 부품 실루엣(135도 프레임·단독 블록·직각 조립) ↔ 모델 실루엣 겹침 최대화(자동, 눈으로 점을 읽지 않음, 초록 링·화살표·쪽 번호는 비교에서 제외, 프레임 구멍 속 빈 곳은 메움)"], "iou": round(iou, 3), "fov": round(fov, 2), "frame_hover_mm": round(hover, 2), "theta": round(th, 3), "phi": round(ph, 3),
      "layout": "프레임 곧은 팔 h6·h8·h9 = A7.p5·A7.p3·B7.p5, 비스듬한 팔 h1·h3 = 단독 블록 돌기 둘(20mm) — 5번의 거울(비스듬한 팔이 +X 쪽)"}
base = {"rows": 1, "tool": "sil-fit", "err_px": round(1 - iou, 3), "max_err_px": None, "est": [], "evidence": ev}
json.dump(dict(base, cols=9, pts=mk(fh), name="steercar 8번 P: 135도 프레임 구멍 h1~h9 — 실루엣 겹침 카메라(IoU %.3f, 프레임 띄움 %.1fmm)로 투영 — silfit" % (iou, hover), origin_cell=[5, 1], visible_cells=[[i, 1] for i in range(1, 10)]), open(D + "fits/08_P.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(dict(base, cols=5, pts=mk(ph_px), name="steercar 8번 U: 블록 돌기 5곳(단독 블록 둘 + 직각 조립 셋) 윗면 — 같은 카메라로 투영 — silfit", origin_cell=[3, 1], visible_cells=[[i, 1] for i in range(1, 6)]), open(D + "fits/08_U.json", "w", encoding="utf-8"), ensure_ascii=False)
ax = {}
for k, d in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    v = P(tgt + 20 * np.array(d))[0] - P(tgt)[0]; v = v / np.linalg.norm(v) * 55; ax[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
json.dump({"global": ax, "fit": {"from": "08_P.json", "err_px": round(1 - iou, 3), "points": 0, "theta": round(th, 2), "phi": round(ph, 2), "method": "실루엣 겹침 IoU %.3f" % iou, "origin_world": [0, 10, -40]}, "no_rotate": True}, open(D + "08_axes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(D + "03_lv.json", D + "08_lv.json"); print("축", ax)
