import json, sys, runpy, numpy as np, cv2, subprocess
sys.path.insert(0,'.'); sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
im0=cv2.imread('refs/trailer/34.jpg'); Hh,Ww=im0.shape[:2]
riv=[((-79.5,30,-40),(237,437)),((-79.5,10,-40),(241,498)),((-79.5,30,40),(480,541)),((-79.5,10,40),(478,605))]
rings=[((-80,30,-30),(265,452)),((-80,10,-30),(268,512)),((-80,30,30),(440,527)),((-80,10,30),(442,592))]
pts=riv+rings; O=np.array([p[0] for p in pts],float); I=[list(map(float,p[1])) for p in pts]; c=O.mean(0)
best=None
for fov in range(15,61):
    r=fit(O-c,I,Ww,Hh,fov,None,None)
    if r and (best is None or r[0]<best[0]): best=(r[0],fov,r[1],r[2],r[3])
e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv); th=float(np.arctan2(-fwd[0],-fwd[2])); ph=float(np.arccos(-fwd[1]))
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
pr=cv2.projectPoints(np.float32(O-c),rv,tv,K,None)[0].reshape(-1,2); res=np.linalg.norm(pr-np.array(I),axis=1)
print("PnP",round(e,2),fov,round(th,2),round(ph,2),np.round(res,1).tolist())
g=runpy.run_path('trailer.py',run_name='probe'); wall=g['PL8']
json.dump({"cols":len(pts),"rows":1,"pts":[[i+1,1,I[i][0],I[i][1]] for i in range(len(pts))],"est":[],"name":"trailer 34번 P: 벽 끝 리벳 4점+센서 링 4점 PnP 평균 %.2fpx(fov %d) — 책 읽음"%(e,fov),"tool":"ringfit","err_px":round(float(e),2),"max_err_px":round(float(res.max()),1),"found":len(pts),"found_ratio":1.0,"mode":"ring+PnP","xyz3d":[list(map(float,p[0])) for p in pts],"xyz3d_img":I},open('refs/trailer/fits/34_P.json','w',encoding='utf-8'),ensure_ascii=False)
Rp=[]
for cc in range(1,10):
    for r in range(1,4):
        w=np.array(wall.hole("h%d_%d"%(cc,r))["pos"],float)+np.array([-2.5,0,0]); p=P(w); Rp.append([cc,r,round(float(p[0]),2),round(float(p[1]),2)])
Wp=[]
for i,q in enumerate(g['LED34']):
    for k,pid in enumerate(("p1","p3")):
        w=np.array(q.peg(pid)["pos"],float)+np.array([-40.0,0,0])*0; p=P(w); Wp.append([i+1,k+1,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts_,name):
    json.dump({"cols":cols,"rows":rows,"pts":pts_,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(e),2),"max_err_px":round(float(res.max()),1),"found":len(pts_),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"},open('refs/trailer/fits/34_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("R",9,3,Rp,"trailer 34번 R: 벽 끝 검은 39프레임 구멍 9칸×3줄(받는 쪽) — 모델 3D 를 벽 끝 리벳 4점+링 4점 PnP 카메라로 투영")
put("W",2,2,Wp,"trailer 34번 W: LED센서 돌기 4개(센서마다 p1·p3, 끼우는 쪽, 안착 자리) — 모델 3D 투영")
im=im0.copy()
for cc,r,x,y in Rp: cv2.circle(im,(int(x),int(y)),3,(0,0,255),-1)
for i,k,x,y in Wp: cv2.circle(im,(int(x),int(y)),5,(0,140,0),-1); cv2.putText(im,"S%d.p%d"%(i,1 if k==1 else 3),(int(x)+6,int(y)-6),0,0.45,(0,110,0),1)
cv2.putText(im,"red = wall holes (cols 1..9, rows y10/20/30), green = LED sensor pegs p1(row y10)/p3(row y30) at cols 2 and 8",(6,862),0,0.42,(0,0,0),1)
cv2.imwrite('refs/trailer/34_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88]); cv2.imwrite('refs/trailer/34_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
json.dump({"M":[[1,0,0],[0,1,0]],"size":[Ww,Hh],"angle":0.0,"crop":[0,0,Ww,Hh],"erase":[]},open('refs/trailer/34_lv.json','w'))
gl={}
for k,v in (("X",np.array([1.,0,0])),("Y",np.array([0,1.,0])),("Z",np.array([0,0,1.]))):
    d=P(c+v*50)-P(c); gl[k]=[float(d[0]),float(d[1])]
sc=55.0/max(abs(x) for v in gl.values() for x in v); gl={k:[round(x*sc,1) for x in v] for k,v in gl.items()}
json.dump({"global":gl,"fit":{"from":"34_P.json 벽 끝 리벳 4점+링 4점 PnP","err_px":round(float(e),2),"points":8,"theta":round(th,2),"phi":round(ph,2),"cols":"+Z","rows":"+Y"}},open('refs/trailer/34_axes.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
