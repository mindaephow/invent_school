# 번호 대조 그림(책 링 ↔ 모델 결합 자리): 보이는 판 격자 번호(파랑 c-r)와, 이번 번호 새 부품의 세운 돌기가 꽂힌 칸(빨강 M)을 같은 그림에 그린다.
#   python scratch_cellmap.py <이름> <번호> <cx> <cz> [P]   cx,cz = 판 칸 가운데((cols+1)/2)·줄 가운데((rows+1)/2) 가 놓인 월드 x,z (fits P 의 격자 번호와 모델 좌표를 잇는 값)
import sys, json, runpy, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N, cx, cz = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]); lab = sys.argv[5] if len(sys.argv) > 5 else "P"
f = json.load(open("refs/%s/fits/%02d_%s.json" % (name, N, lab), encoding="utf-8")); cols, rows = f["cols"], f["rows"]
pix = {(int(c), int(r)): (x, y) for c, r, x, y in f["pts"]}
src = open(name + ".py", encoding="utf-8").read(); cut = src.index("# ── 부품 체크")
g = {"__name__": "x", "__file__": name + ".py"}; exec(compile(src[:cut], name + ".py", "exec"), g); A = g["A"]
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); S = 2.0
out = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
for (c, r), (x, y) in pix.items(): cv2.putText(out, "%d-%d" % (c, r), (int(x * S) - 14, int(y * S) + 4), 0, 0.42, (255, 0, 0), 1)
done = set()
for Pt in A.parts:
    if Pt.step.index != N: continue
    for h in Pt.conn.get("pegs", []):
        w = Pt.world("peg", h)
        if abs(w["dir"][1]) < 0.7: continue
        x, z = float(w["pos"][0]), float(w["pos"][2])
        c = (x - cx) / 10 + (cols + 1) / 2; r = (z - cz) / 10 + (rows + 1) / 2
        ci, ri = round(c), round(r)
        if abs(c - ci) > 0.2 or abs(r - ri) > 0.2 or not (1 <= ci <= cols and 1 <= ri <= rows) or (ci, ri) in done: continue
        done.add((ci, ri)); p = pix[(ci, ri)]
        cv2.circle(out, (int(p[0] * S), int(p[1] * S)), 16, (0, 0, 255), 2); cv2.putText(out, "M", (int(p[0] * S) - 8, int(p[1] * S) - 20), 0, 0.8, (0, 0, 255), 2)
cv2.imwrite("refs/%s/%02d_6.jpg" % (name, N), out); print("M", len(done), "칸:", sorted(done))
