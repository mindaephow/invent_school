# 책 링(초록 원)과 모델 결합 구멍을 같은 칸-줄 번호판 위에 그린다 — 책 링이 번호 몇에 있고 모델은 번호 몇에 끼웠는지 눈으로 대조 (2026-10-18)
#   python _cellcmp.py <이름> <번호> <모델 부품의 번호들 콤마>   → refs/<이름>/NN_6.jpg  (파랑 = 칸-줄 번호, 빨강 M = 모델이 돌기를 꽂은 구멍)
import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
name, N = sys.argv[1], int(sys.argv[2]); steps = [int(v) for v in sys.argv[3].split(",")]
f = json.load(open("refs/%s/fits/%02d_P.json" % (name, N), encoding="utf-8"))
src = np.float32([[x, y] for c, r, x, y in f["pts"] if c <= 15]); dst = np.float32([[c, r] for c, r, x, y in f["pts"] if c <= 15])
H, _ = cv2.findHomography(dst, src, 0)
S = 2.0
Pc = lambda c, r: cv2.perspectiveTransform(np.float32([[[c, r]]]), H)[0][0] * S
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); out = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
for c in range(1, 19):
    for r in range(1, 10):
        if c <= 15 and r > 3: continue
        if c > 15 and r > 9: continue
        p = Pc(c, r); cv2.putText(out, "%d-%d" % (c, r), (int(p[0]) - 18, int(p[1]) + 5), 0, 0.5, (255, 0, 0), 1)
src_py = open(name + ".py", encoding="utf-8").read(); cut = src_py.index("# ── 부품 체크")
g = {"__name__": "x", "__file__": name + ".py"}; exec(compile(src_py[:cut], name + ".py", "exec"), g); A = g["A"]
done = set()
for Pt in A.parts:
    if Pt.step.index not in steps: continue
    for h in Pt.conn.get("pegs", []):
        w = Pt.world("peg", h)
        if abs(w["dir"][1]) < 0.7: continue
        x, z = float(w["pos"][0]), float(w["pos"][2]); c, r = x / 10 + 8, z / 10 + 2
        key = (round(c, 1), round(r, 1))
        if key in done or not (0.5 <= c <= 18.5): continue
        if c <= 15.5 and not (0.5 <= r <= 3.5): continue
        done.add(key); p = Pc(c, r); cv2.circle(out, (int(p[0]), int(p[1])), 16, (0, 0, 255), 2)
        cv2.putText(out, "M", (int(p[0]) - 8, int(p[1]) - 20), 0, 0.8, (0, 0, 255), 2)
cv2.imwrite("refs/%s/%02d_6.jpg" % (name, N), out); print("저장", len(done), "개")
