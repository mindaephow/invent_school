import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im=cv2.imread("refs/trailer/21.jpg"); Hh,Ww=im.shape[:2]
blk=[((-15,29.5,100),(315,630)),((25,29.5,100),(712.5,365)),((-5,29.5,100),(427.5,562.5)),((15,29.5,100),(617.5,430))]
frm=[(-15,(265,344)),(-5,(400,272)),(5,(521,197.5)),(15,(632,134)),(25,(726,77.5))]
def run(Hy, use_blk=(0,1,2,3), use_f=(0,1,2,3,4), fovr=(15,60)):
    O=[];I=[]
    for i in use_blk: O.append(blk[i][0]); I.append(blk[i][1])
    for i in use_f: O.append((frm[i][0],Hy,100)); I.append(frm[i][1])
    O=np.array(O,float); c=O.mean(0); best=None
    for fov in range(fovr[0],fovr[1]+1):
        r=fit(O-c,I,Ww,Hh,fov,None,None)
        if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
    e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv)
    pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
    return e,fov,float(np.arctan2(-fwd[0],-fwd[2])),float(np.arccos(-fwd[1])),res
for Hy in range(36,111,6):
    e,fov,th,ph,res=run(Hy); print(Hy,"%.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,1).tolist())
print("--- fine")
for Hy in range(50,64,2):
    e,fov,th,ph,res=run(Hy); print(Hy,"%.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,1).tolist())
print("--- frame only drop ring pts")
for Hy in (54,56,58,60):
    e,fov,th,ph,res=run(Hy,use_blk=(0,1),use_f=(0,4)); print(Hy,"%.2f fov%d th %.3f ph %.3f"%(e,fov,th,ph),np.round(res,1).tolist())
