import runpy, numpy as np, os
os.environ["AT_LAST"]="20"
g=runpy.run_path("trailer.py", run_name="probe")
for n in ("BLK20","BAR20A"):
    v=g[n]
    for q in (v if isinstance(v,list) else [v]):
        print(n, q.n, np.round(q.p,1))
        for h in q.holes if hasattr(q,'holes') else []: pass

for B in g["BLK20"]:
    for hid in ("h1","h2"):
        w=B.hole(hid); print(B.n,hid, np.round(w["pos"],1), np.round(w["dir"],2), w["len"])
for hid in ("h1_1","h5_1"):
    w=g["BAR20A"].hole(hid); print("프레임",hid,np.round(w["pos"],1),np.round(w["dir"],2),w["len"])
import partlib
print("리벳 pegs", [(c["id"],c["pos"],c["dir"],c.get("len")) for c in partlib.get("리벳")["pegs"]])
print("15프레임 holes", [(c["id"],c["pos"],c["dir"]) for c in partlib.get("15프레임")["holes"]][:5])
