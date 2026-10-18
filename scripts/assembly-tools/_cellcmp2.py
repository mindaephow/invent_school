# 책 링 ↔ 모델 구멍 번호 대조 그림(어떤 크기 판이든): 판 격자 fits(칸·줄 번호판, 파랑) 위에 책 초록 링 중심(초록 ○ 와 환산 칸)과 이 번호에서 모델이 꽂은 리벳의 칸(빨강 M)을 그린다 — 2026-10-19
#   python _cellcmp2.py <이름> <번호> <판 중심 x> <판 중심 z> <칸수> <줄수> "링x,y;링x,y;…"   → refs/<이름>/NN_6.jpg
import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N, xc, zc, cols, rows = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
rings = [tuple(float(v) for v in t.split(",")) for t in sys.argv[7].split(";")] if len(sys.argv) > 7 else []
f = json.load(open("refs/%s/fits/%02d_P.json" % (name, N), encoding="utf-8"))
src = np.float32([[x, y] for c, r, x, y in f["pts"]]); dst = np.float32([[c, r] for c, r, x, y in f["pts"]])
H, _ = cv2.findHomography(dst, src, 0); Hi = np.linalg.inv(H)
S = 2.0; Pc = lambda c, r: cv2.perspectiveTransform(np.float32([[[c, r]]]), H)[0][0] * S
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); out = cv2.resize(im, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
for c in range(1, cols + 1):
    for r in range(1, rows + 1):
        p = Pc(c, r); cv2.putText(out, "%d-%d" % (c, r), (int(p[0]) - 18, int(p[1]) + 5), 0, 0.5, (255, 0, 0), 1)
for (x, y) in rings:
    q = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hi)[0][0]; cv2.circle(out, (int(x * S), int(y * S)), 22, (0, 160, 0), 2)
    cv2.putText(out, "book %.1f-%.1f" % (q[0], q[1]), (int(x * S) + 24, int(y * S) - 20), 0, 0.5, (0, 130, 0), 2)
src_py = open(name + ".py", encoding="utf-8").read(); cut = src_py.index("# ── 부품 체크")
g = {"__name__": "x", "__file__": name + ".py"}; exec(compile(src_py[:cut], name + ".py", "exec"), g); A = g["A"]
n = 0
for Pt in A.parts:
    if Pt.step.index != N or not Pt.name.startswith("리벳"): continue
    x, z = float(Pt.p[0]), float(Pt.p[2]); c, r = (x - xc) / 10 + (cols + 1) / 2, (z - zc) / 10 + (rows + 1) / 2
    p = Pc(c, r); cv2.circle(out, (int(p[0]), int(p[1])), 16, (0, 0, 255), 2); cv2.putText(out, "M %d-%d" % (round(c), round(r)), (int(p[0]) - 20, int(p[1]) - 20), 0, 0.7, (0, 0, 255), 2); n += 1
cv2.imwrite("refs/%s/%02d_6.jpg" % (name, N), out); print("모델 리벳 %d개 표시" % n)
