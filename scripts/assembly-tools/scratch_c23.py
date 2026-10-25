import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.'); sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
g=runpy.run_path('trailer.py',run_name='probe'); PL=g['PL23']; BR=g['BR23']
f=json.load(open('refs/trailer/fits/23_P.json',encoding='utf-8'))
O=np.array([np.array(PL.hole("h%d_%d"%(c,r))["pos"],float) for c,r,x,y in f['pts']]); I=[[x,y] for c,r,x,y in f['pts']]; cc=O.mean(0)
im0=cv2.imread('refs/trailer/23.jpg'); Hh,Ww=im0.shape[:2]; best=None
for fov in range(15,61):
    r=fit(O-cc,I,Ww,Hh,fov,None,None)
    if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
e,fov,rv,tv,K=best
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-cc]),rv,tv,K,None)[0][0][0]
hv=np.array([0,42.0,0]); 
Wp=[]; 
for k,h in enumerate(("h1","h2","h3","h4"),1):
    p=P(np.array(BR.hole(h)["pos"],float)+hv); Wp.append([k,1,round(float(p[0]),2),round(float(p[1]),2)])
Rp=[]
for k,h in enumerate(("h5_2","h5_3"),1):
    p=P(np.array(PL.hole(h)["pos"],float)+np.array([0,2.5,0])); Rp.append([k,1,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(e),2),"max_err_px":3.0,"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + 판 격자 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/23_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",4,1,Wp,"trailer 23번 W: 1열브라켓 구멍 4개(발 h1·h2, 팔 h3·h4) — 판 구멍 45점 PnP(0.94px) 카메라로 모델 투영(발이 판 위 42 뜬 높이)")
put("R",2,1,Rp,"trailer 23번 R: 판 칸5 줄2(리벳)·줄3(볼트·너트) 구멍 — 모델 3D 투영")
im=im0.copy()
for k,_,x,y in Wp: cv2.circle(im,(int(x),int(y)),5,(0,0,255),-1); cv2.putText(im,"B.h%d"%k,(int(x)+6,int(y)-8),0,0.5,(200,0,0),1)
for k,_,x,y in Rp: cv2.circle(im,(int(x),int(y)),5,(0,140,0),-1); cv2.putText(im,"P5.%d"%(k+1),(int(x)+6,int(y)-8),0,0.5,(0,110,0),1)
cv2.putText(im,"book rings: green(454,243)=bracket h1 <- rivet(plate 5.2) ; yellow(513,277)=bracket h2 <- bolt (plate 5.3, nut below)",(6,865),0,0.42,(0,0,0),1)
cv2.imwrite('refs/trailer/23_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite('refs/trailer/23_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
print(e,fov,Wp,Rp)
