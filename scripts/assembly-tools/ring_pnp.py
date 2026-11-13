# 책 그림의 초록 링 픽셀 ↔ 모델 구멍 3D 로 카메라·격자(fits)·축(_axes.json)을 한 번에 만든다 — 판이 없거나 holefit 가 안 되는 번호의 카메라를 "링 점"으로 푼다(mkfit3d 의 앞단, 2026-11-13).
#   python ring_pnp.py <이름> <번호> <spec.json> [--보기]
#   spec.json = {"label": "P", "cols": 9, "rows": 3, "grid_part": {"part": "39프레임", "n": 1, "hole": "홀면 -y 열1·줄1", "col": "홀면 -y 열2·줄1", "row": "홀면 -y 열1·줄2"},
#                "rings": [{"part": "39프레임", "n": 1, "hole": "홀면 -y 열1·줄1", "px": [330, 300]}, ...], "fov": null}
#     part·n = 그 번호(단계)에 새로 놓인 같은 이름 부품 중 n 번째(1부터). hole = 부품 구멍 이름(스크립트에서 쓰는 "홀면 ±y 열N·줄M" 형식).
#     링 3D = 구멍 위치 + 띄운 만큼(dir·hover) — 책 그림은 부품이 떠 있는 모습이라서. px = 책 원본 그림(refs/<이름>/NN.jpg) 픽셀(눈금 그림으로 읽는다).
#   하는 일: 모델에서 링 3D 를 계산 → pnp 로 카메라(θ·φ·오차) 출력 → mkfit3d.py 로 fits/NN_<label>.json·NN_axes.json 쓰기(평균 3px·최대 6px 넘으면 쓰지 않는다). --보기 는 계산만.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, runpy, subprocess, tempfile
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asmlib as al
if len(sys.argv) < 4: sys.exit(__doc__)
name, N, spec = sys.argv[1], int(sys.argv[2]), json.load(open(sys.argv[3], encoding="utf-8")); view = "--보기" in sys.argv
g = runpy.run_path(asmpath.ap(name, ".py"), run_name="probe"); A = g["A"]; st = A.steps[N - 1]
def part_of(nm, n):
    c = [p for p in st.parts if p.n == nm]
    if len(c) < n: sys.exit("❌ %d번에 %s 가 %d개 없다(%d개)" % (N, nm, n, len(c)))
    return c[n - 1]
def hole_pos(p, label):
    pos = np.array(p.hole(al._item(p, label, "홀")[0])["pos"], float)
    return pos
def lifted(p, pos):   # 책 그림은 떠 있는 모습 — dir·hover(결합 전 띄움)를 더한다
    ex = p.extra or {}; d = ex.get("dir"); h = ex.get("hover") or 0
    return pos + (np.array(d, float) / np.linalg.norm(np.array(d, float)) * float(h) if d is not None and h > 1 else 0)
pts = []
for r in spec["rings"]:
    p = part_of(r["part"], r.get("n", 1)); q = lifted(p, hole_pos(p, r["hole"]))
    pts.append([[round(float(x), 3) for x in q], r["px"]]); print("  링 %-8s %-14s → 3D %s · 픽셀 %s" % (r["part"], r["hole"], [round(float(x), 1) for x in q], r["px"]))
gp = spec["grid_part"]; gpt = part_of(gp["part"], gp.get("n", 1)); o = lifted(gpt, hole_pos(gpt, gp["hole"]))
col = lifted(gpt, hole_pos(gpt, gp["col"])) - o; row = lifted(gpt, hole_pos(gpt, gp["row"])) - o
out = {"pts": pts, "grid": {"origin": [round(float(x), 3) for x in o], "col": [round(float(x), 3) for x in col], "row": [round(float(x), 3) for x in row]}, "note": spec.get("note", "링 점 PnP(ring_pnp.py): 링 픽셀(눈으로 읽음) ↔ 모델 구멍 3D(띄운 자리)")}
if spec.get("fov"): out["fov"] = spec["fov"]
tf = os.path.join(tempfile.gettempdir(), "ring_pnp_%s_%02d.json" % (name, N)); json.dump(out, open(tf, "w", encoding="utf-8"), ensure_ascii=False)
if view: print("계산만 했다:", tf); sys.exit(0)
r = subprocess.run([sys.executable, os.path.join(HERE, "mkfit3d.py"), name, str(N), spec.get("label", "P"), str(spec["cols"]), str(spec["rows"]), tf] + (["--허용", str(spec["tol"])] if spec.get("tol") else []), capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
print(r.stdout.strip()[-600:], r.stderr.strip()[-300:])
