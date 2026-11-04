import sys, json, math, shutil
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools"); sys.path.insert(0, "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad")
sys.argv = ["x"]
import numpy as np, cv2
import silfit5 as S
import fit5 as F5
from pnp import cam_from, angles
sys.stdout.reconfigure(encoding="utf-8")
AT = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/"; D = AT + "refs/steercar/"
SP = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/"
x = np.load(SP + "sil5_x.npy"); iou = 1 - S.loss(list(x))
rv = x[:3].reshape(3, 1); tv = x[3:6].reshape(3, 1); fov = float(x[6]); hover = float(x[7])
f = (S.Hh / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, S.Ww / 2], [0, f, S.Hh / 2], [0, 0, 1]], float)
P = lambda q: cv2.projectPoints(np.array(q, np.float64).reshape(-1, 3), rv, tv, K, None)[0].reshape(-1, 2)
C, fwd, up, right = cam_from(rv, tv); tgt = np.array([10.0, 10.0, -25.0]); az, el, rad = angles(C, tgt); th, ph = math.radians(az), math.radians(90 - el)
print("IoU %.3f fov %.1f 띄움 %.1f theta %.2f phi %.2f roll %.1f°" % (iou, fov, hover, th, ph, math.degrees(math.asin(max(-1, min(1, float(right[1])))))))
org, W = F5.frame_world(1, hover)
fh = [P(W("h%d" % i))[0] for i in range(1, 10)]                         # 프레임 구멍 9(두께 가운데 높이 = 프레임 윗면 − 2.5)
fh = [P(np.array(W("h%d" % i, 0.0)))[0] for i in range(1, 10)]
pegs = [W("h1"), W("h3")]; pegtop = [np.array([w[0], 20.0, w[2]]) for w in pegs] + [np.array([10, 20, -25.0]), np.array([10, 20, -5.0]), np.array([10, 20, 5.0])]
ph_px = [P(q)[0] for q in pegtop]
mk = lambda hs: [[i + 1, 1, round(float(h[0]), 2), round(float(h[1]), 2)] for i, h in enumerate(hs)]
ev = {"sources": ["책 그림 부품 실루엣↔모델 실루엣(135도 프레임·단독 3단블록·직각 3단블록 조립) 겹침 최대화(자동, 눈으로 점을 읽지 않음, 초록 링·화살표는 비교에서 제외)"], "iou": round(iou, 3), "fov": round(fov, 2), "frame_hover_mm": round(hover, 2), "theta": round(th, 3), "phi": round(ph, 3), "frame_half_width": round(float(x[8]), 2),
      "layout": "프레임 곧은 팔 h6·h8·h9 = 직각 조립 돌기 A.p5(z−25)·A.p3(z−5)·B.p3(x10,z5), 비스듬한 팔 h1·h3 = 단독 블록 돌기 둘(20mm 간격)"}
base = {"rows": 1, "tool": "sil-fit", "err_px": round(1 - iou, 3), "max_err_px": None, "est": [], "evidence": ev}
pf = dict(base, cols=9, pts=mk(fh), name="steercar 5번 P: 135도 프레임 구멍 h1~h9(꺾인 한 줄) — 실루엣 겹침 카메라(IoU %.3f, 프레임 띄움 %.1fmm)로 투영 — silfit" % (iou, hover), origin_cell=[5, 1], visible_cells=[[i, 1] for i in range(1, 10)])
uf = dict(base, cols=5, pts=mk(ph_px), name="steercar 5번 U: 블록 돌기 5곳(단독 블록 둘 + 직각 조립 셋) 윗면 — 같은 카메라로 투영 — silfit", origin_cell=[3, 1], visible_cells=[[i, 1] for i in range(1, 6)])
json.dump(pf, open(D + "fits/05_P.json", "w", encoding="utf-8"), ensure_ascii=False); json.dump(uf, open(D + "fits/05_U.json", "w", encoding="utf-8"), ensure_ascii=False)
o = tgt; ax = {}
for k, d in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    v = P(o + 20 * np.array(d))[0] - P(o)[0]; v = v / np.linalg.norm(v) * 55; ax[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
json.dump({"global": ax, "fit": {"from": "05_P.json", "err_px": round(1 - iou, 3), "points": 0, "theta": round(th, 2), "phi": round(ph, 2), "method": "실루엣 겹침 IoU %.3f" % iou, "origin_world": [10, 10, -25]}, "no_rotate": True}, open(D + "05_axes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(D + "03_lv.json", D + "05_lv.json")
print("축", ax, "프레임 구멍 px", [[round(float(v), 1) for v in h] for h in fh][:3], "...")
