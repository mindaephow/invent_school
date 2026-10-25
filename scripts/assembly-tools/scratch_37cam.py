import sys, numpy as np, cv2, itertools
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/37.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
# plate corners (top face y=5), x ±45 z ±10 ; T hole c5 r2: (0,5,+5)
corn=[((-45,5,-10),(120,695)),((45,5,-10),(770,398)),((45,5,10),(863,481)),((-45,5,10),(156,825))]
out=[]
for hr in (5,10,15,20,30):
  for hb in (-30,-20,-10):
    pts=corn+[((0,5,5),(534,582)),((0,5+hr,5),(535,410)),((0,5+hb,5),(535,738))]
    try: e,fov,th,ph,res=solve(pts)
    except Exception: continue
    out.append((round(e,2),hr,hb,fov,round(th,2),round(ph,2)))
out.sort(); print(out[:6])
