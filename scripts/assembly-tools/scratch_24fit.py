import sys, itertools, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/24.jpg"); Hh,Ww=im.shape[:2]
def solve(pts, fovr=(15,60)):
    O=np.array([p[0] for p in pts],float); I=[p[1] for p in pts]; c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
for zs in (1,-1):
  for xr in (70,72.5,74.5):
    for xb in (77.5,80,82.5):
        pts=[((xb,60.1,zs*30),(405,399)),((xb,60.1,-zs*30),(681,316)),((xr,30,zs*40),(367,504)),((xr,10,zs*40),(371,595)),((xr,30,-zs*40),(718,389))]
        e,fov,th,ph,res=solve(pts)
        print(zs,xr,xb,"%.1f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,0).tolist())
print("---- with plate rings")
body=[((80,60.1,30),(405,399)),((80,60.1,-30),(681,316)),((75,30,40),(367,504)),((75,10,40),(371,595)),((75,30,-40),(718,389))]
for h in range(0,71,5):
    xo=85+h
    plate=[((xo,50,30),(589,533)),((xo,30,40),(530,662)),((xo,10,40),(527,758)),((xo,50,-30),(883,423)),((xo,30,-40),(907,506)),((xo,10,-40),(890,596))]
    e,fov,th,ph,res=solve(body+plate,(15,50)); print(h,"%.1f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,0).tolist())
print("---- variants")
res_all=[]
for yb in (50.1,60.1):
  for xb in (77.5,80,82.5):
    for ps in (1,-1):  # plate z side flip relative to body
      for rowoff in (0,10,-10,20):  # plate top row y offset
        for h in range(25,66,5):
            xo=85+h
            body=[((xb,yb,30),(405,399)),((xb,yb,-30),(681,316)),((75,30,40),(367,504)),((75,10,40),(371,595)),((75,30,-40),(718,389))]
            yt=50+rowoff
            plate=[((xo,yt,30*ps),(589,533)),((xo,yt-20,40*ps),(530,662)),((xo,yt-40,40*ps),(527,758)),((xo,yt,-30*ps),(883,423)),((xo,yt-20,-40*ps),(907,506)),((xo,yt-40,-40*ps),(890,596))]
            try: e,fov,th,ph,res=solve(body+plate,(15,50))
            except Exception as ex: continue
            res_all.append((e,yb,xb,ps,rowoff,h,fov,th,ph))
res_all.sort(); 
for r in res_all[:8]: print(np.round(r,3).tolist())
