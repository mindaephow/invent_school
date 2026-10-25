import sys, itertools, numpy as np, cv2
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
base=[((-79.5,65,-40),(780,337)),((-79.5,45,-40),(775,412)),((79,65,-40),(287,290)),((79,45,-40),(290,322)),((40,55,-50),(630,350))]
out=[]
for sg in (1,-1):   # side of the left pair rows / near z
  for hw in range(30,181,15):
    for hb in range(hw+10,261,20):
        pts=base+[((40,55,-88-hw),(432,495)),((40,55,-98-hb),(60,780))]
        try: e,fov,th,ph,res=solve(pts,(15,50))
        except Exception: continue
        out.append((e,sg,hw,hb,fov,th,ph)); 
    break
out.sort(); print(np.round(out[:6],3).tolist())
