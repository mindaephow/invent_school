import sys, numpy as np, cv2, itertools, runpy
sys.stdout.reconfigure(encoding="utf-8")
g=runpy.run_path("trailer.py",run_name="probe"); A=g['A']; MB=g['MB32']
# buttons: local (x,z) with y +20.5 above board center
btn=[(-33.6,9),(-26.5,25.2),(4.5,26.1),(17.5,26.1)]
B3=[np.array(MB.p)+MB.R@np.array([x,20.5,z]) for x,z in btn]
pxb=[(435,51),(361,31),(292,70),(251,88)]   # A(−33.6) B(big) C D from book 33
print("buttons 3D",[np.round(b,1).tolist() for b in B3])
riv=[]
for q in A.parts:
    if q.n=="리벳" and q.step.index in (9,10): riv.append((q.step.index,np.array(q.p,float)))
print(len(riv))
# unflipped: model currently final state (step 32 flip applied to p) -> p are final upright
pr=[(620,216),(597,230),(661,265),(640,278)]
W,H=1000,877
def pnp(obj,img,fov):
    f=0.5*H/np.tan(np.radians(fov)/2); K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
    ok,rv,tv=cv2.solvePnP(np.float32(obj),np.float32(img),K,None,flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok: return 1e9,None
    p,_=cv2.projectPoints(np.float32(obj),rv,tv,K,None); e=np.linalg.norm(p.reshape(-1,2)-np.array(img),axis=1).mean(); return e,(rv,tv,K)
best=[]
cand=[r for r in riv]
for perm in itertools.permutations(range(len(cand)),4):
    obj=B3+[cand[i][1] for i in perm]; img=pxb+pr
    for fov in (25,35):
        e,_=pnp(obj,img,fov)
        best.append((e,fov,perm))
best.sort(key=lambda t:t[0]); print(best[:5])
