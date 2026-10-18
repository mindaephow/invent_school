# 한 번호의 책 그림 위에 모델 돌기 끝(peg tip)을 점으로 찍는다 — 카메라는 fits/NN_P.json 점으로 푼 값 (2026-10-18, 코너 블록 위치를 책 돌기와 직접 대조)
#   python _pegproj.py <이름> <번호> <부품이름들 콤마> 
import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
name, N = sys.argv[1], int(sys.argv[2]); want = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else None
f = json.load(open("refs/%s/fits/%02d_P.json" % (name, N), encoding="utf-8"))
obj = np.array(f["xyz3d"], float); img = f["xyz3d_img"]; im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; c = obj.mean(0)
r = fit(obj - c, img, W, H, f["fov"]); e, rv, tv, K = r
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]
src = open(name + ".py", encoding="utf-8").read(); cut = src.index("# ── 부품 체크")
g = {"__name__": "x", "__file__": name + ".py"}; exec(compile(src[:cut], name + ".py", "exec"), g); A = g["A"]
out = im.copy(); col = {}
for p in A.parts:
    if p.step.index > N: continue
    if want and p.n.split()[0] not in want and p.n not in want: continue
    print(p.step.index, p.n, np.round(p.p,1).tolist()) if p.step.index in (4,5) else None
    for h in p.conn.get("pegs", []):
        w = p.world("peg", h);
        if len(sys.argv) > 4 and w["dir"][1] < 0.7: continue
        if len(sys.argv) > 4 and p.step.index not in [int(v) for v in sys.argv[4].split(",")]: continue
        tip = np.array(w["pos"], float) + np.array(w["dir"], float) * h.get("len", 5)
        q = P(tip); cv2.circle(out, (int(q[0]), int(q[1])), 5, (0, 0, 255), 2)
        cv2.putText(out, p.n[:3] + h["id"], (int(q[0]) + 4, int(q[1]) - 4), 0, 0.35, (255, 0, 0), 1)
cv2.imwrite("refs/%s/hf/%02d_pegs.png" % (name, N), out); print("err", e, "saved")
