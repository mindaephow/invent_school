import numpy as np, cv2, itertools, sys, runpy
sys.stdout.reconfigure(encoding="utf-8")
g=runpy.run_path("trailer.py",run_name="probe"); A=g['A']
rv=[(q.step.index,np.array(q.p,float)) for q in A.parts if q.n=="리벳" and q.step.index<=22]
R3=np.array([p for s,p in rv]); steps=[s for s,p in rv]
B=np.array([[216,58],[488,56],[450,63],[200,110],[154,119],[599,126],[720,186],[241,207],[344,287],[446,415]],float)
W,H=1001,877
best=[]
for fov in (22,30,40):
    f=0.5*H/np.tan(np.radians(fov)/2); K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
    cand=[i for i in range(len(R3)) if R3[i][1]>=25]
    for tri in itertools.combinations(range(len(B)),3):
        for ra in itertools.permutations(cand,3):
            ok,rvs,tvs=cv2.solveP3P(np.float32(R3[list(ra)]),np.float32(B[list(tri)]),K,None,flags=cv2.SOLVEPNP_AP3P) if False else (0,[],[])
            pass
print("skip")
