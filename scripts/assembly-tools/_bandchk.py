# 밴드 점·가닥이 부품 상자(dims) 안으로 들어가는지 수치로 본다 (2026-10-19): python _bandchk.py <번호>
import sys, json, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
a = json.load(open("autotarget_asm.json", encoding="utf-8"))["steps"]; N = int(sys.argv[1]); st = a[N - 1]
dims = json.load(open("dims.json", encoding="utf-8"))
import runpy
g = runpy.run_path("autotarget.py", run_name="probe"); A = g["A"]; band = A.steps[N - 1].kw["bands"][0]; pts = np.array(band["pts"], float); r = band.get("r", 0.8)
bad = {}
for P in A.parts:
    if P.step.index > N: continue
    d = np.array(dims.get(P.name.split("(")[0].rstrip("0123456789번 ").strip(), dims.get(P.name.split(" ")[0], [0, 0, 0])), float)
    if not d.any(): continue
    R = np.array(P.R, float); c = np.array(P.p, float)
    for k in range(len(pts)):
        for f in np.linspace(0, 1, 6):
            q = pts[k] * (1 - f) + pts[(k + 1) % len(pts)] * f; loc = R.T @ (q - c)
            if np.all(np.abs(loc) < d / 2 + r - 0.2): bad[P.name] = bad.get(P.name, 0) + 1; print('  ',P.name,[round(float(v),1) for v in q]); break
print("밴드가 들어간 부품 상자:", bad or "없음")
