import sys, json, math, shutil
sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools"); sys.path.insert(0, "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad")
sys.argv = ["x"]
import numpy as np, cv2
import silfit4 as S
from pnp import cam_from, angles
sys.stdout.reconfigure(encoding="utf-8")
AT = "C:/Users/user/Downloads/invent_school/scripts/assembly-tools/"; D = AT + "refs/steercar/"
SP = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/scratchpad/"
x = np.load(SP + "sil4_x.npy"); hyp = "a"
iou = 1 - S.loss(list(x), hyp)
rv = x[:3].reshape(3, 1); tv = x[3:6].reshape(3, 1); fov = float(x[6]); g = float(x[7])
f = (S.Hh / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, S.Ww / 2], [0, f, S.Hh / 2], [0, 0, 1]], float)
P = lambda q: cv2.projectPoints(np.array(q, np.float64).reshape(-1, 3), rv, tv, K, None)[0].reshape(-1, 2)
C, fwd, up, right = cam_from(rv, tv); tgt = np.array([0, 0, -10.0]); az, el, rad = angles(C, tgt); th, ph = math.radians(az), math.radians(90 - el)
print("IoU %.3f fov %.1f 간격 %.1f theta %.2f phi %.2f roll %.1f°" % (iou, fov, g, th, ph, math.degrees(math.asin(max(-1, min(1, float(right[1])))))))
xj = 10.0; zc = -20.0 - g
# 받는 블록 B(원점): 구멍 h1~h3 (로컬 x −10,0,10 → 세계 x −10,0,10), 구멍 가운데
Bh = [P([(-10 + 10 * i), 0, 0])[0] for i in range(3)]
# 끼우는 블록 A(중심 (xj,0,zc), 길이 Z): 구멍 h1~h3 = 로컬 x −10,0,10 → 세계 z zc−10, zc, zc+10
Ah = [P([xj, 0, zc + (-10 + 10 * i)])[0] for i in range(3)]
mk = lambda hs: [[i + 1, 1, round(float(h[0]), 2), round(float(h[1]), 2)] for i, h in enumerate(hs)]
base = {"cols": 3, "rows": 1, "tool": "sil-fit", "err_px": round(1 - iou, 3), "max_err_px": None, "est": [],
        "evidence": {"sources": ["책 그림 블록 실루엣 ↔ 모델 실루엣(3단블록 둘) 겹침 최대화(자동, 눈으로 점을 읽지 않음)"], "iou": round(iou, 3), "fov": round(fov, 2), "gap_mm": round(g, 2), "theta": round(th, 3), "phi": round(ph, 3),
                     "hypothesis": "A 끝 돌기 p1 → B 큰 구멍 h3(링, 화면 왼쪽 끝), B 돌기 면 위, 구멍축 = 세계 Z", "silhouette_pieces": "몸통+돌기 6+끝 돌기 2 (한 블록)"}}
pf = dict(base, pts=mk(Bh), name="steercar 4번 P: 받는 3단블록(오른쪽) 구멍 h1~h3 — 실루엣 겹침 카메라(IoU %.3f, fov %.1f, 블록 간격 %.1fmm)로 투영 — silfit" % (iou, fov, g), origin_cell=[2, 1], visible_cells=[[1, 1], [2, 1], [3, 1]])
uf = dict(base, pts=mk(Ah), name="steercar 4번 U: 끼우는 3단블록(왼쪽) 구멍 h1~h3 — 같은 카메라로 투영 — silfit", origin_cell=[2, 1], visible_cells=[[1, 1], [2, 1], [3, 1]])
json.dump(pf, open(D + "fits/04_P.json", "w", encoding="utf-8"), ensure_ascii=False); json.dump(uf, open(D + "fits/04_U.json", "w", encoding="utf-8"), ensure_ascii=False)
o = np.array([0, 0, -10.0]); ax = {}
for k, d in (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))):
    v = P(o + 20 * np.array(d))[0] - P(o)[0]; v = v / np.linalg.norm(v) * 55; ax[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
json.dump({"global": ax, "fit": {"from": "04_P.json", "err_px": round(1 - iou, 3), "points": 0, "theta": round(th, 2), "phi": round(ph, 2), "method": "실루엣 겹침 IoU %.3f" % iou, "origin_world": [0, 0, -10]}, "no_rotate": True}, open(D + "04_axes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(D + "03_lv.json", D + "04_lv.json")
print("B 구멍 픽셀", [[round(float(v), 1) for v in h] for h in Bh], "A 구멍 픽셀", [[round(float(v), 1) for v in h] for h in Ah], "축", ax)
