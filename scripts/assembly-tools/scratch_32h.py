import sys, numpy as np, cv2, itertools
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/32.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best
    P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,res,P
y=70.7
corn={(30,-40):0,(30,40):1,(70,-40):2,(70,40):3}
px={'L':(300,350),'B':(410,400),'T':(470,248),'R':(580,298)}
out=[]
for perm in itertools.permutations(list(corn)):
    pts=[((x,y,z),px[k]) for (x,z),k in zip(perm,'LBTR')]
    e,fov,res,P=solve(pts); out.append((round(e,2),perm,fov))
out.sort(); print(out[:3])
e,perm,fov=out[0]
pts=[((x,y,z),px[k]) for (x,z),k in zip(perm,'LBTR')]
e,fov,res,P=solve(pts)
rings=[(415,305),(458,330)]
best=[]
for c1 in range(1,10):
  for r1 in range(1,6):
    for c2 in range(1,10):
      for r2 in range(1,6):
        if (c1,r1)>=(c2,r2): continue
        # plate holes: x = 30+10(r-1), z = -40+10(c-1); pegs 20 apart
        a=(30+10*(r1-1),y,-40+10*(c1-1)); b=(30+10*(r2-1),y,-40+10*(c2-1))
        if np.hypot(a[0]-b[0],a[2]-b[2])!=20: continue
        d=np.linalg.norm(P(a)-np.array(rings[0]))+np.linalg.norm(P(b)-np.array(rings[1])); d2=np.linalg.norm(P(b)-np.array(rings[0]))+np.linalg.norm(P(a)-np.array(rings[1]))
        best.append((round(min(d,d2),1),(c1,r1),(c2,r2),'swap' if d2<d else ''))
best.sort(); print(best[:6])
