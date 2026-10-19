import json,runpy,numpy as np,cv2,math,sys
sys.stdout.reconfigure(encoding="utf-8")
from pnp import cam_from, angles
g=runpy.run_path("battlerobot2.py",run_name="probe"); P30,P31=g["PL30"],g["PL31"]
mb=np.array(g["MB37"].p,float)
def hole(c,r): P,rr=(P30,r) if r<=5 else (P31,r-5); return P.hole("h%d_%d"%(c,rr))["pos"]
f=json.load(open('refs/battlerobot2/fits/00_P.json',encoding='utf-8')); pts=f['pts']
print(f['cols'],f['rows'])
if f['cols']==10: pts=[(r,c,x,y) for c,r,x,y in pts]   # 10×15 파일: 파일 칸=모델 줄, 파일 줄=모델 칸
im=cv2.imread('refs/battlerobot2/00.jpg'); H,W=im.shape[:2]
wh=[np.array([-30,25,-39.]),np.array([-30,25,94.])]
res=[]
for cm in (0,1):
  for rm in (0,1):
    obj=np.array([hole(c if cm==0 else 16-c, r if rm==0 else 11-r) for c,r,x,y in pts],np.float64); img=np.array([[x,y] for c,r,x,y in pts],np.float64); cc=obj.mean(0)
    for fov in (24,30,36,45):
        fl=(H/2)/math.tan(math.radians(fov)/2); K=np.array([[fl,0,W/2],[0,fl,H/2],[0,0,1]])
        n,rvs,tvs,_=cv2.solvePnPGeneric(obj-cc,img,K,None,flags=cv2.SOLVEPNP_IPPE)
        for rv,tv in zip(rvs,tvs):
            pr,_=cv2.projectPoints(obj-cc,rv,tv,K,None); e=float(np.linalg.norm(pr.reshape(-1,2)-img,axis=1).mean())
            C,fwd,up,right=cam_from(rv,tv)
            Pj=lambda q: cv2.projectPoints(np.float64([np.array(q,float)-cc]),rv,tv,K,None)[0][0][0]
            az,el,_=angles(C,[0,0,0])
            res.append((round(e,2),cm,rm,fov,round(float(up[1]),2),round(float(C[1])),[np.round(Pj(w)).astype(int).tolist() for w in wh],np.round(Pj(mb)).astype(int).tolist(),round(math.radians(az),2),round(math.radians(90-el),2)))
res=[r for r in res if r[4]>0 and r[5]>0]; res.sort(key=lambda t:t[0])
print("사진: 가까운 바퀴 허브 약 (190,430), 메인보드 약 (460,170)")
for r in res[:6]: print(r)
