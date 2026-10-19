# 너트가 프레임 구멍 안에 쏙 들어갔는지(너트 바닥 면 = 프레임 바깥 면) 번호별로 수치 출력
import numpy as np, sys
sys.stdout.reconfigure(encoding="utf-8")
src = open("battlerobot2.py", encoding="utf-8").read()
cut = src.index("# ── 37 ──") if "# ── 37 ──" in src else len(src)
g = {"__name__": "x", "__file__": "battlerobot2.py"}; exec(compile(src[:cut], "battlerobot2.py", "exec"), g)
A = g["A"]
def half(P, a):
    R = np.array(P.R, float); s = P.conn.get("size", [0, 0, 0]); return sum(abs(float(R[:, i] @ a)) * s[i] / 2 for i in range(3))
for nm in ("NUT27", "NUT28", "NUT32", "NUT33", "NUT34", "NUT35", "NUT36"):
    nuts = g[nm] if isinstance(g[nm], list) else [g[nm]]
    for n in nuts:
        pg = n.world("hole", n.conn["holes"][0]) if False else None
        pegp = next(x for x in n.conn["pegs"] if x["id"] == "p1"); w = n.world("peg", pegp); d = np.array(w["dir"], float); d /= np.linalg.norm(d)
        c = np.array(n.p, float); cd = float(c @ d)
        out = []
        for P in A.parts if hasattr(A, "parts") else []:
            if P is n: continue
            try: hs = [np.array(P.hole(h["id"])["pos"], float) for h in P.conn["holes"]]
            except Exception: continue
            for hp in hs:
                v = hp - c; perp = np.linalg.norm(v - (v @ d) * d)
                if perp < 1.5 and -3 < float(v @ d) < 12:
                    out.append((P.n, round(float(P.p @ d - half(P, d)) - cd, 2), round(float(P.p @ d + half(P, d)) - cd, 2))); break
        print(nm, np.round(c, 1).tolist(), "축", np.round(d, 2).tolist(), "프레임(이름, 아랫면−너트중심, 윗면−너트중심):", out)
