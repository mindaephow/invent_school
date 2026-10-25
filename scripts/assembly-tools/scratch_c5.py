import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('scratch_5P_ring.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/05.jpg'); Hh,Ww=im0.shape[:2]
e,rv,tv,K=fit(O-c,I,Ww,Hh,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
g=runpy.run_path('trailer.py',run_name='probe'); pl=g['PL4']; bar=g['BAR5']; rv5=g['RV5']
Wp=[]
for cc in range(1,10):
    for r in range(1,6):
        w=np.array(pl.hole("h%d_%d"%(cc,6-r))["pos"],float); p=P(w); Wp.append([cc,r,round(float(p[0]),2),round(float(p[1]),2)])
hv=np.array([0,48.0,0]); Rp=[]
for i in range(1,8):
    p=P(np.array(bar.hole("h%d_1"%i)["pos"],float)+hv+np.array([0,2.5,0])); Rp.append([i,1,round(float(p[0]),2),round(float(p[1]),2)])
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영"}
    json.dump(d,open('refs/trailer/fits/05_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",9,5,Wp,"trailer 5번 W: 흰 59프레임 구멍 45개 — holefit 기본 45/45 평균 2.12px 격자(칸 1.1 = 위 모서리, 줄1 = 리벳 끝줄)와 같은 칸 중심을 ringfit 카메라(%.2fpx)로 투영"%f['err_px'])
put("R",7,1,Rp,"trailer 5번 R: 빨간 17프레임 구멍 7개(띄움 48) — 같은 카메라로 모델 구멍 투영")
im=im0.copy()
for cc,r,x,y in Wp: cv2.circle(im,(int(x),int(y)),3,(0,0,255),-1)
for cc,r,x,y in Wp:
    if r==1 and cc in (1,3,7,9): cv2.putText(im,"%d.1"%cc,(int(x)+4,int(y)-5),0,0.45,(200,0,0),1)
for cc,r,x,y in Rp: cv2.circle(im,(int(x),int(y)),4,(0,140,0),-1); cv2.putText(im,"b%d"%cc,(int(x)+4,int(y)-6),0,0.45,(0,110,0),1)
cv2.putText(im,"red=white plate holes (edge row 1 = rivet row; rivets at cols 3,7), green=bar holes b1-b7",(8,Hh-10),0,0.5,(0,0,0),2)
cv2.imwrite('refs/trailer/05_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
im=im0.copy()
for ring in ((610,225),(722,310),(620,65),(755,160)): cv2.circle(im,ring,22,(0,0,255),2)
for r in rv5:
    p=P(np.array(r.p,float)+np.array([0,2.5,0])); cv2.drawMarker(im,(int(p[0]),int(p[1])),(255,0,0),cv2.MARKER_CROSS,16,2)
for i in (2,6):
    p=Rp[i-1]; cv2.drawMarker(im,(int(p[2]),int(p[3])),(255,0,0),cv2.MARKER_CROSS,16,2)
cv2.putText(im,"red circle=book ring (4), blue +=model rivet bases (cols 3,7) / bar holes 2,6 (hover 48)",(8,Hh-10),0,0.5,(0,0,0),2)
cv2.imwrite('refs/trailer/05_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
idx=json.load(open('refs/trailer/index.json',encoding='utf-8')); idx=[r for r in idx if not (r['step']==5 and r['idx'] in (4,6))]
idx.append({"step":5,"idx":4,"file":"05_4.jpg","note":"④-2 단계 5 — 번호 대조(칸.줄 번호) 홀라인: 흰 59프레임 구멍 격자(holefit 기본 45/45 평균 2.12px, 칸 1.1 = 위 모서리·줄1 = 리벳 끝줄)와 빨간 17프레임 구멍 b1~b7. 리벳은 끝줄 칸 3·7."})
idx.append({"step":5,"idx":6,"file":"05_6.jpg","note":"⑥ 단계 5 — 책 링 번호 대조 ↔ 모델: 빨간 원 = 책 링 4(판 칸 3·7 리벳, 막대 구멍 2·6), 파란 + = 모델 위치."})
idx.sort(key=lambda r:(r['step'],r['idx'])); json.dump(idx,open('refs/trailer/index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(Wp),len(Rp))
