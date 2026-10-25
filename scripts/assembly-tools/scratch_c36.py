import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.'); sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit
f=json.load(open('refs/trailer/fits/36_P.json',encoding='utf-8')); pts=f['pts']
im0=cv2.imread('refs/trailer/36.jpg'); Hh,Ww=im0.shape[:2]
world=lambda c,R: (5.0+(-70.0+10*(c-1)),5.0,140.0+(R-6)*10.0)
O=np.array([world(c,r) for c,r,x,y in pts],float); I=[[x,y] for c,r,x,y in pts]; cc=O.mean(0); best=None
for fov in range(15,61):
    r=fit(O-cc,I,Ww,Hh,fov,None,None)
    if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
e,fov,rv,tv,K=best; print("fit",round(e,2),fov)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-cc]),rv,tv,K,None)[0][0][0]
f['xyz3d']=[list(map(float,o)) for o in O]; f['xyz3d_img']=I; json.dump(f,open('refs/trailer/fits/36_P.json','w',encoding='utf-8'),ensure_ascii=False)
g=runpy.run_path('trailer.py',run_name='probe'); bl=g['BL36']
Wp=[]; 
for i,q in enumerate(bl):
    for pid in [c["id"] for c in q.conn["pegs"] if c["id"] in ("p3","p4","p5")]:
        pg=q.peg(pid)
        if abs(pg["dir"][1])<0.9: continue
        w=np.array(pg["pos"],float)+np.array(q.extra.get("dir",[0,1,0]),float)*float(q.extra.get("hover",0)); p=P(w); Wp.append([i+1,int(pid[1]),round(float(p[0]),2),round(float(p[1]),2)])
print(len(Wp))
json.dump({"cols":6,"rows":3,"pts":Wp,"est":[],"name":"trailer 36번 W: 블록 여섯의 아래 돌기(띄운 자리) — 모델 3D 를 판 구멍 격자 PnP 카메라로 투영","tool":"cam-proj","err_px":round(float(e),2),"max_err_px":4.2,"found":len(Wp),"found_ratio":1.0,"mode":"모델 돌기 3D + 판 격자 카메라 투영"},open('refs/trailer/fits/36_W.json','w',encoding='utf-8'),ensure_ascii=False)
Rg=[[c,r,*[round(float(v),2) for v in P(world(c,rr))]] for c in (1,2,15) for r,rr in ((1,1),(2,2),(3,5),(4,6),(5,7),(6,10),(7,11))]
json.dump({"cols":3,"rows":7,"pts":Rg,"est":[],"name":"trailer 36번 R: 블록이 꽂힐 판 구멍(칸1·2·15 × 줄1·2·5·6·7·10·11) — 모델 3D 투영","tool":"cam-proj","err_px":round(float(e),2),"max_err_px":4.2,"found":len(Rg),"found_ratio":1.0,"mode":"모델 구멍 3D + 판 격자 카메라 투영"},open('refs/trailer/fits/36_R.json','w',encoding='utf-8'),ensure_ascii=False)
im=im0.copy()
for c,r,x,y in Rg: cv2.circle(im,(int(x),int(y)),3,(0,0,255),-1)
for i,k,x,y in Wp: cv2.circle(im,(int(x),int(y)),4,(0,140,0),-1)
cv2.putText(im,"red = target plate holes, green = block pegs (hover)",(6,862),0,0.45,(0,0,0),1)
cv2.imwrite('refs/trailer/36_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite('refs/trailer/36_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
