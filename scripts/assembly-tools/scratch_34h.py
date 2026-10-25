import sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/34.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
riv=[((-79.5,30,-40),(237,437)),((-79.5,10,-40),(241,498)),((-79.5,30,40),(480,541)),((-79.5,10,40),(478,605))]
for cl,cr in ((-30,30),(-20,20),(-30,20),(-20,30),(-30,40),(-40,30),(-30,10),(-10,30)):
    rings=[((-80,30,cl),(265,452)),((-80,10,cl),(268,512)),((-80,30,cr),(440,527)),((-80,10,cr),(442,592))]
    e,fov,th,ph,res=solve(riv+rings); print(cl,cr,"%.1f fov%d th %.2f ph %.2f"%(e,fov,th,ph),np.round(res,0).tolist())
