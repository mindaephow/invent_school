# 부품 하나만 기준으로 책 방향(theta·phi)을 푼다 — 그 부품의 돌기 끝(p1…)·구멍(h1…)을 책 그림에서 읽은 픽셀과 짝지어 PnP(2026-11-11, 오토건 19번 3단블록에서 손으로 풀어 맞은 방법을 도구로).
#   python partcam.py <이름> <번호> "<부품이름>" "p5:442,420;h1:390,344;…" [--fov 15,60] [--몇째 k]
#     id: p* = 돌기 끝(중심 + 방향×길이/2), h* = 구멍 윗면 열린 곳(중심에서 구멍 방향 반대로 두께/2). 픽셀 = 원본 그림 좌표(crop_ticks.py 로 확대해 읽는다). 점 6개 이상·한 직선 아님.
#     --단계 M  그 부품이 놓인 번호(기본 N). 앞 번호에서 놓은 부품 기준이면 쓴다(예: 20번 책을 19번에서 놓은 3단블록으로).
#     --몇째 k  같은 이름 부품이 여럿일 때 그 번호(N)에서 새로 놓인 k번째(기본 첫째).
#   출력: fov 별 평균 오차·theta·phi·up_y — 정상 해(위에서 내려다봄 phi<π/2·up_y>0)에 ✔. 오차 2px 이하면 fit, 넘으면 ⚠ 추정값. 파일은 쓰지 않고 화면도 돌리지 않는다.
#   ★ 어느 면·어느 끝이 책의 어느 쪽인지(돌기 번호 ↔ 픽셀 짝)는 사람이 정한다. 틀리면 180° 뒤집힌 해(theta±π)나 바닥에서 올려다보는 해가 나온다 — 두 짝짓기를 돌려 정상 해 오차가 작은 쪽을 쓴다.
import asmpath
import sys, os, json, math, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
from pnp import fit, cam_from
a = sys.argv[1:]
if len(a) < 4: sys.exit(__doc__)
name, N, part, spec = a[0], int(a[1]), a[2], a[3]; fr = (15, 60); nth = 1
for i, v in enumerate(a):
    if v == "--fov": fr = tuple(int(x) for x in a[i + 1].split(","))
    if v == "--몇째": nth = int(a[i + 1])
src = open(name + ".py", encoding="utf-8").read(); cut = src.find("# ── %d ──" % (N + 1)); end = src.index("import stepchecks")
src = src[:cut if 0 < cut < end else end] + "\n"
ns = {"__name__": "probe", "__file__": os.path.abspath(name + ".py")}; exec(compile(src, name + ".py", "exec"), ns); A = ns["A"]
SRC = N
for i, v in enumerate(a):
    if v == "--단계": SRC = int(a[i + 1])
cand = [p for p in A.parts if p.n == part and p.step.index == SRC] or [p for p in A.parts if p.n == part and p.step.index <= N]
if len(cand) < nth: sys.exit("부품 없음: %s (번호 %d)" % (part, N))
q = cand[nth - 1]; dims = json.load(open("dims.json", encoding="utf-8")).get(part); th = dims[1] if dims else 0
pg = {g["id"]: g for g in q.conn.get("pegs", [])}; hl = {h["id"]: h for h in q.conn.get("holes", [])}
obj, img, ids = [], [], []
for tok in spec.split(";"):
    k, xy = tok.split(":"); x, y = [float(v) for v in xy.split(",")]
    if k in pg: w = q.world("peg", pg[k]); P = np.array(w["pos"]) + np.array(w["dir"]) * float(pg[k]["len"]) / 2
    elif k in hl: w = q.world("hole", hl[k]); P = np.array(w["pos"]) - np.array(w["dir"]) * th / 2
    else: sys.exit("없는 id " + k + " (돌기 %s · 구멍 %s)" % (",".join(pg), ",".join(hl)))
    obj.append(P); img.append((x, y)); ids.append(k)
obj = np.array(obj); c = obj - obj.mean(0)
if len(obj) < 5 or np.linalg.svd(c, compute_uv=False)[1] < 1.0: sys.exit("점이 5개 미만이거나 한 직선이다")
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]
rows = []
for fv in range(fr[0], fr[1] + 1, 5):
    r = fit(obj, img, W, H, fv)
    if not r: continue
    e, rv, tv, K = r; C, fwd, up, right = cam_from(rv, tv); ph = math.acos(max(-1, min(1, -fwd[1]))); ok = ph < math.pi / 2 and up[1] > 0
    rows.append((e, fv, math.atan2(-fwd[0], -fwd[2]), ph, up[1], ok))
for e, fv, t, p, u, ok in sorted(rows, key=lambda r: (not r[5], r[0]))[:5]:
    print("%s 오차 %.1fpx fov %d theta %.3f phi %.3f up_y %.2f" % ("✔" if ok else "✖(올려다봄·뒤집힘)", e, fv, t, p, u))
good = [r for r in rows if r[5]]
if good: b = min(good); print("→ 정상 해 최선: theta %.3f phi %.3f 오차 %.1fpx %s" % (b[2], b[3], b[0], "✅ fit" if b[0] <= 2 else "⚠ 2px 초과 — 추정값"))
else: print("→ 정상 해 없음 — 돌기·구멍 짝짓기를 바꿔 다시")
