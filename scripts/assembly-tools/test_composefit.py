# composefit 검사: 가짜 카메라로 투영한 점에서 그룹 이동·높이·카메라(오차)를 되찾는지.  python test_composefit.py
import sys, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
import composefit

W, H, FOV = 1000, 860, 30
f = (H / 2) / math.tan(math.radians(FOV) / 2); K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1.0]])
rv = np.array([[1.9], [0.3], [-0.1]]); tv = np.array([[-20.0], [10.0], [900.0]])
T_TRUE = (-35.0, 40.0); LV_TRUE = {"b": 42.0, "f": 28.0}
base = [(0, 67.5, 0), (14, 67.5, 14), (0, 67.5, 30), (14, 67.5, 44), (30, 67.5, 5), (50, 67.5, 22)]   # 왼쪽 묶음 점(x,z)
pts = []
for grp in (None, "R"):
    for i, (x, y, z) in enumerate(base):
        lv = [[], ["b"], ["b", "f"]][i % 3]
        p = np.array([x, y, z], float)
        if grp: p[0] += T_TRUE[0]; p[2] += T_TRUE[1]
        for l in lv: p[1] += LV_TRUE[l]
        px = cv2.projectPoints(np.float32([p]), rv, tv, K, None)[0][0][0]
        pts.append({"p": [x, y, z], "px": [float(px[0]), float(px[1])], "group": grp, "level": lv})
spec = {"fov": FOV, "pts": pts, "groups": {"R": {"init": [-20.0, 20.0]}}, "levels": {"b": {"init": 30.0}, "f": {"init": 20.0}}}
r = composefit.solve(spec, W, H)
ok = (r["mean"] < 0.2 and abs(r["groups"]["R"][0] - T_TRUE[0]) < 1.5 and abs(r["groups"]["R"][1] - T_TRUE[1]) < 1.5
      and abs(r["levels"]["b"] - 42) < 1.5 and abs(r["levels"]["f"] - 28) < 1.5)
print("평균 %.3fpx 이동 %s 높이 %s" % (r["mean"], [round(v, 1) for v in r["groups"]["R"]], {k: round(v, 1) for k, v in r["levels"].items()}))
spec["fov"] = None
r2 = composefit.solve(spec, W, H)
ok2 = r2["fov"] in (25, 30, 35)
print("fov 탐색 →", r2["fov"], "평균 %.3f" % r2["mean"])
# 격자 점: holefit 가 찾은 칸만 쓰고(est 제외), 투영해 만든 fits 는 거부하며, 링 가정이 틀리면 링 오차만 커지는지
plate = {(c, r): np.array([-30.0 + 10 * (c - 1), 17.5, -10.0 + 10 * (r - 1)]) for c in range(1, 7) for r in range(1, 4)}
proj = lambda q: cv2.projectPoints(np.float32([q]), rv, tv, K, None)[0][0][0]
fj = {"tool": "holefit", "est": [[2, 2]], "pts": [[c, r, float(proj(q)[0]), float(proj(q)[1])] for (c, r), q in plate.items()]}
gf = {"origin": [-30.0, 17.5, -10.0], "col": [10, 0, 0], "row": [0, 0, 10]}
gp = composefit.grid_points(fj, gf)
ok3 = len(gp) == 17 and all(p["kind"] == "grid" for p in gp)
try: composefit.grid_points(dict(fj, tool="infer3d"), gf); ok4 = False
except SystemExit: ok4 = True
rings = []
for x in (-20, 0, 20):   # 리벳 링: 실제는 줄3(z=+10) 인데 줄2(z=0)로 가정한 점
    q = np.array([x, 30.0, 10.0]); px = proj(q); rings.append({"p": [x, 30.0, 0.0], "px": [float(px[0]), float(px[1])], "kind": "ring"})
r3 = composefit.solve({"fov": FOV, "pts": gp + rings}, W, H)
ok5 = r3["kinds"]["ring"] > 2 * max(r3["kinds"]["grid"], 0.3)
print("격자 점 %d개, 투영 격자 거부 %s, 링 가정 틀림 → 링 %.2f px ≫ 격자 %.2f px %s" % (len(gp), ok4, r3["kinds"]["ring"], r3["kinds"]["grid"], ok5))
sys.exit(0 if ok and ok2 and ok3 and ok4 and ok5 else (print("❌ composefit 검사 실패") or 1))
