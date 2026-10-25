import sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/28.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
out=[]
for xb in (-50,-40):
  for xf in (20,30,40,50,60,-20,-30):
    pts=[((-79.5,65,40),(181,439)),((-79.5,45,40),(191,513)),((xb,55,103),(380,510)),((xf,55,50),(613,372))]
    try: e,fov,th,ph,res=solve(pts)
    except Exception: continue
    out.append((round(e,2),xb,xf,fov,round(th,2),round(ph,2),np.round(res,0).tolist()))
out.sort(); print(out[:6])
