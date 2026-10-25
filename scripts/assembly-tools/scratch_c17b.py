import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('scratch_17P_ring.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/17.jpg'); Hh,Ww=im0.shape[:2]
e,rv,tv,K=fit(O-c,I,Ww,Hh,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
F=lambda w:tuple(w)
g=runpy.run_path('trailer.py',run_name='probe'); A=g['A']; pl=g['PL17']; bl=g['_BL17']
hv=np.array([-36.0,0,0])
Wp=[]
for cc in range(1,10):
    for r in (1,2):
        w=np.array(pl.hole("h%d_%d"%(cc,r))["pos"],float)+hv; p=P(F(w)); Wp.append([cc,r,round(float(p[0]),2),round(float(p[1]),2)])
Rp=[]
for i,b in enumerate(bl):
    for r,h in enumerate(("h1","h2"),1):
        w=np.array(b.hole(h)["pos"],float); p=P(F(w)); Rp.append([i+1,r,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/17_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",9,2,Wp,"trailer 17번 W: 검은 29프레임 구멍 18개 — holefit 어두운판·DoG 18/18개 평균 3.0px(2px 기준 미달, 링 가린 칸 2.x·9.x) → 모델 3D(띄움 36)를 ringfit 카메라로 투영")
put("R",2,2,Rp,"trailer 17번 R: 블록 구멍 4개(왼쪽 옆면 14번 블록·11번 블록의 h1·h2) — 모델 3D 를 ringfit 카메라로 투영")
im=im0.copy()
for cc,r,x,y in Wp: cv2.circle(im,(int(x),int(y)),4,(0,0,255),-1); cv2.putText(im,"%d.%d"%(cc,r),(int(x)+4,int(y)-6),0,0.45,(200,0,0),1)
for cc,r,x,y in Rp: cv2.circle(im,(int(x),int(y)),4,(0,140,0),-1); cv2.putText(im,"B%d.h%d"%(cc,r),(int(x)+6,int(y)-6),0,0.45,(0,110,0),1)
cv2.putText(im,"red=black 29 plate holes (hover 36) green=block holes",(8,Hh-10),0,0.55,(0,0,0),2)
cv2.imwrite('refs/trailer/17_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
print(len(Wp),len(Rp))
