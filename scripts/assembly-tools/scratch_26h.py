import sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/26.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
out=[]
for xe in (70,75,79.5):
  for zl in (-40,40):
    for (y1,y2) in ((65,45),(45,65)):
      for xs in (-60,-50,-40,-30,30,40,50):
        pts=[((-79.5,65,-40),(779,340)),((-79.5,45,-40),(771,416)),((xe,y1,zl),(288,292)),((xe,y2,zl),(290,323)),((xs,55,-50),(630,350))]
        try: e,fov,th,ph,res=solve(pts)
        except Exception: continue
        out.append((round(e,2),xe,zl,(y1,y2),xs,fov,round(th,2),round(ph,2)))
out.sort(); print(out[:6])
