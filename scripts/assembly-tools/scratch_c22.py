import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/22_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/22.jpg'); Hh,Ww=im0.shape[:2]
fov=int(f['name'].split('fov ')[1].split(')')[0])
e,rv,tv,K=fit(O-c,I,Ww,Hh,fov,None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
g=runpy.run_path('trailer.py',run_name='probe'); bar=g['BAR7']; blk=g['BLK20']; sh=np.array([-55.0,29.5,-100.0])
Wp=[]
for k in range(1,6):
    w=np.array(bar.hole("h%d_1"%k)["pos"],float)+np.array([0,2.5,0]); p=P(w); Wp.append([k,1,round(float(p[0]),2),round(float(p[1]),2)])
Rp=[]
for i,bq in enumerate(blk):
    for r,h in enumerate(("h1","h2"),1):
        w=np.array(bq.hole(h)["pos"],float)+np.array([0,-4.5,0]); p=P(w); Rp.append([i+1,r,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/22_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",5,1,Wp,"trailer 22번 W: 몸통 위 15프레임(7번) 구멍 5개 — 1·3·5번 = 7번 리벳 머리(구멍 속 주황), 2·4번 = 새 리벳 링. 링·리벳 12점 ringfit 카메라로 모델 구멍 투영(막대 윗면 y 50)")
put("R",2,2,Rp,"trailer 22번 R: 20~21번 조립 블록 아래 구멍 4개(블록1 h1·h2, 블록2 h1·h2) — 내려앉은 자리(밑면 y 50)에서 ringfit 카메라로 투영; 안쪽 구멍 둘(블록1 h2·블록2 h1)이 리벳을 받는다")
im=im0.copy()
for cc,r,x,y in Wp: cv2.circle(im,(int(x),int(y)),5,(0,0,255),-1); cv2.putText(im,"F%d"%cc,(int(x)+6,int(y)-8),0,0.5,(200,0,0),1)
for cc,r,x,y in Rp: cv2.circle(im,(int(x),int(y)),5,(0,140,0),-1); cv2.putText(im,"B%d.h%d"%(cc,r),(int(x)+6,int(y)-8),0,0.5,(0,110,0),1)
cv2.imwrite('refs/trailer/22_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); print(Wp,Rp)
