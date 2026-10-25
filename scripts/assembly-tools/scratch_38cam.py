import sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/38.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
Y=22.5
pts=[((-70,5,195),(417,724)),
 ((-65,Y,99.4),(221,408)),((-55,Y,130),(316,459)),((-55,Y,150),(361,508)),((-65,Y,179.4),(394,611)),
 ((75,Y,99.4),(663,257)),((75,Y,130),(739,301)),((75,Y,150),(794,331)),((75,Y,179.4),(889,386))]
e,fov,th,ph,res=solve(pts); print(round(e,2),fov,round(th,2),round(ph,2),res.round(1))
Z=lambda z:280-z   # reflect z about 140
for name,fz in (("flipz",Z),):
    p2=[((x,y,fz(z)),i) for (x,y,z),i in pts]
    e,fov,th,ph,res=solve(p2); print(name,round(e,2),fov,round(th,2),round(ph,2),res.round(1))
# x flipped (near end = +x): mirror x about 5
p3=[((10-x,y,z),i) for (x,y,z),i in pts]
e,fov,th,ph,res=solve(p3); print("flipx",round(e,2),fov,round(th,2),round(ph,2),res.round(1))
p4=[((10-x,y,280-z),i) for (x,y,z),i in pts]
e,fov,th,ph,res=solve(p4); print("flipboth",round(e,2),fov,round(th,2),round(ph,2),res.round(1))
