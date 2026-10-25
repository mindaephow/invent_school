import sys, itertools, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/22.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
bar=[((-70,50,0),(204,504)),((-60,50.5,0),(262,462)),((-40,50.5,0),(347,407)),((-30,50,0),(392,395))]
for zs in itertools.product((-40,40),repeat=2):
    wall=[((-78,30,zs[0]),(57,512)),((-78,10,zs[0]),(75,587)),((-78,30,zs[1]),(336,733)),((-78,10,zs[1]),(345,809))]
    if zs[0]==zs[1]: continue
    e,fov,th,ph,res=solve(bar+wall); print(zs,"%.1f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,0).tolist())
print('---- refine')
import runpy, json
bl=[((-70,50,0),(204,504)),((-60,50.5,0),(262,462)),((-40,50.5,0),(347,407)),((-30,50,0),(392,395)),((-78,30,-40),(57,512)),((-78,10,-40),(75,587)),((-78,30,40),(336,733)),((-78,10,40),(345,809))]
O=np.array([p[0] for p in bl],float); I=[p[1] for p in bl]; c=O.mean(0)
e,fov,rv,tv,K=None,None,None,None,None
best=None
for f_ in range(15,61):
    r=fit(O-c,I,Ww,Hh,f_,None,None)
    if r and (best is None or r[0]<best[0]): best=(r[0],f_,r[1],r[2],r[3])
e,fov,rv,tv,K=best
g=runpy.run_path("trailer.py",run_name="probe"); A=g['A']
blobs=[(604,24),(469,97),(317,160),(900,169),(363,193),(262,231),(767,259),(899,279),(186,307),(576,314),(617,338),(520,394),(560,420),(665,437),(428,446),(664,485),(346,499),(651,500)]
pts=[]
for q in A.parts:
    if q.n=="리벳" and q.step.index<=19:
        w=np.array(q.p,float)
        # rivet visible end: use p + dir*? seated, show both ends
        for sgn in (1,-1):
            pass
        pts.append((q.step.index,w))
for si,w in pts:
    pr=cv2.projectPoints(np.float32([w-c]),rv,tv,K,None)[0][0][0]
    d=[np.hypot(pr[0]-bx,pr[1]-by) for bx,by in blobs]; j=int(np.argmin(d))
    print(si,np.round(w,1).tolist(),np.round(pr,0).tolist(),"nearest blob",blobs[j],round(d[j]))
print('---- refit12')
extra=[((-10,72,-40),(317,160)),((-10,72,-30),(363,193)),((-10,72,30),(576,314)),((-10,72,40),(617,338))]
e,fov,th,ph,res=solve(bl+extra); print("%.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,1).tolist())
e,fov,th,ph,res=solve(bl+extra[:0]); print("8pt %.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph))
for dy in (68,70,72,74,76):
    ex=[((x,dy,z),p) for (x,_,z),p in extra]; e,fov,th,ph,res=solve(bl+ex); print(dy,"%.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph))
