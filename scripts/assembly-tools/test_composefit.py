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
sys.exit(0 if ok and ok2 else (print("❌ composefit 검사 실패") or 1))
