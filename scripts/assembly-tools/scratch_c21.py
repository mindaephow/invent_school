import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/21_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/21.jpg'); Hh,Ww=im0.shape[:2]
fov=int(f['name'].split('fov ')[1].split(')')[0])
e,rv,tv,K=fit(O-c,I,Ww,Hh,fov,None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
g=runpy.run_path('trailer.py',run_name='probe'); blk=g['BLK20']
Wp=[[k,1,*[round(float(v),2) for v in P((-25+10*k,57.0,100.0))]] for k in range(1,6)]
Rp=[]
for i,b in enumerate(blk):
    for r,h in enumerate(("h1","h2"),1):
        w=np.array(b.hole(h)["pos"],float)+np.array([0,4.5,0]); p=P(w); Rp.append([i+1,r,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/21_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",5,1,Wp,"trailer 21번 W: 빨간 15프레임 구멍 5개(받는 쪽 아님·끼우는 쪽 = 리벳 위) — 링 2점·구멍 3점 읽음, 책 프레임 윗면 높이 y 57 로 ringfit 카메라 투영")
put("R",2,2,Rp,"trailer 21번 R: 2단블록 윗면 큰 구멍 4개(블록1 h1·h2, 블록2 h1·h2) — 모델 3D 를 ringfit 카메라로 투영(윗면 y 29.5)")
im=im0.copy()
for cc,r,x,y in Wp: cv2.circle(im,(int(x),int(y)),5,(0,0,255),-1); cv2.putText(im,"F%d"%cc,(int(x)+6,int(y)-8),0,0.5,(200,0,0),1)
for cc,r,x,y in Rp: cv2.circle(im,(int(x),int(y)),5,(0,140,0),-1); cv2.putText(im,"B%d.h%d"%(cc,r),(int(x)+6,int(y)-8),0,0.5,(0,110,0),1)
cv2.imwrite('refs/trailer/21_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); print(Wp,Rp)
