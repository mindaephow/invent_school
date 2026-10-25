import sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/27.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
wall=[((-79.5,65,40),(236,351)),((-79.5,45,40),(238,419)),((-79.5,65,-40),(92,217)),((-79.5,45,-40),(97,283))]
for xs in (-50,-40,-30,-20,0,20,30,40,50):
    for zs in (50,):
        pts=wall+[((xs,55,zs),(365,375))]
        e,fov,th,ph,res=solve(pts); print(xs,"%.1f fov%d th %.2f ph %.2f"%(e,fov,th,ph),np.round(res,0).tolist())
