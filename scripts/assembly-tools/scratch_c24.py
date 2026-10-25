import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.'); sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
f=json.load(open('refs/trailer/fits/24_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/24.jpg'); Hh,Ww=im0.shape[:2]
fov=int(f['name'].split('fov ')[1].split(')')[0])
e,rv,tv,K=fit(O-c,I,Ww,Hh,fov,None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
g=runpy.run_path('trailer.py',run_name='probe'); pl=g['PL23']
hv=np.array([50.0,0,0])
Wp=[]
for cc in range(1,10):
    for r in range(1,6):
        w=np.array(pl.hole("h%d_%d"%(cc,r))["pos"],float)+hv+np.array([2.5,0,0]); p=P(w); Wp.append([cc,r,round(float(p[0]),2),round(float(p[1]),2)])
tg=[(77.5,50.1,30),(77.5,50.1,-30),(75,30,40),(75,10,40),(75,30,-40),(75,10,-40)]
Rp=[[i+1,1]+[round(float(v),2) for v in P(t)] for i,t in enumerate(tg)]
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/24_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",9,5,Wp,"trailer 24번 W: 흰 59프레임 구멍 9×5(판 띄움 50, 바깥 면) — 링 6점(칸2·8 줄5·칸1·9 줄3·1)과 몸쪽 링 5점 ringfit 4.09px(fov 33)로 모델 구멍 투영")
put("R",6,1,Rp,"trailer 24번 R: 몸통 +X 끝 받는 돌기·리벳 6곳(15번 블록 돌기 p5 둘 z ±30 y 50.1 / 3단블록 끝 구멍 y 30·10 리벳 넷 z ±40) — 모델 3D 투영")
im=im0.copy()
for cc,r,x,y in Wp: cv2.circle(im,(int(x),int(y)),3,(0,0,255),-1)
for cc,r,x,y in Wp:
    if (cc,r) in ((2,5),(8,5),(1,3),(1,1),(9,3),(9,1)): cv2.putText(im,"%d.%d"%(cc,r),(int(x)+5,int(y)-6),0,0.5,(200,0,0),1)
for k,_,x,y in Rp: cv2.circle(im,(int(x),int(y)),5,(0,140,0),-1); cv2.putText(im,"T%d"%k,(int(x)+6,int(y)-8),0,0.5,(0,110,0),1)
cv2.putText(im,"plate holes (red, hover 45) / body targets T1,T2=block pegs p5, T3..T6=rivets (green)",(6,865),0,0.45,(0,0,0),1)
cv2.imwrite('refs/trailer/24_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite('refs/trailer/24_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); print(e,fov)
