import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/16_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im0=cv2.imread('refs/trailer/16.jpg'); Hh,Ww=im0.shape[:2]
e,rv,tv,K=fit(O-c,I,Ww,Hh,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
A=runpy.run_path('trailer.py',run_name='probe')['A']
W=json.load(open('refs/trailer/fits/16_W.json',encoding='utf-8')); R=json.load(open('refs/trailer/fits/16_R.json',encoding='utf-8'))
im=im0.copy()
for cc,r,x,y in W['pts']:
    seen=(r>=4 and 2<=cc<=8) or (cc==7)
    col=(0,0,255) if seen else (160,160,160); cv2.circle(im,(int(x),int(y)),3,col,-1)
    if cc in (1,2,5,8,9) and r in (4,5): cv2.putText(im,"%d.%d"%(cc,r),(int(x)+4,int(y)-5),0,0.42,(200,0,0),1)
for cc,r,x,y in R['pts']:
    cv2.circle(im,(int(x),int(y)),3,(0,140,0),-1)
    if r==1 or cc in (1,7): cv2.putText(im,"R%d.%d"%(cc,r),(int(x)+4,int(y)-5),0,0.42,(0,110,0),1)
cv2.putText(im,"red=white plate (read 16 holes -> cam 1.72px), green=black plate (model, hover 35)",(8,Hh-10),0,0.55,(0,0,0),2)
cv2.imwrite('refs/trailer/16_4.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
im=im0.copy()
pl=next(p for p in A.parts if p.n=="59프레임" and p.step.index==13)
bl=[p for p in A.parts if p.n=="2단블록" and p.step.index==15]
for ring,k in (((162,512),"h2_5"),((512,700),"h8_5")):
    cv2.circle(im,ring,18,(0,0,255),2)
    pp=P(np.array(pl.hole(k)["pos"],float)); cv2.drawMarker(im,tuple(int(v) for v in pp),(255,0,0),cv2.MARKER_CROSS,18,2)
for b in bl:
    pg=np.array(b.peg("p2")["pos"],float)+np.array([0,35.0,0]); pp=P(pg); cv2.drawMarker(im,tuple(int(v) for v in pp),(0,160,0),cv2.MARKER_TILTED_CROSS,18,2)
    print("block p2 hover35 px",np.round(pp,0))
cv2.putText(im,"red circle=book ring, blue +=model plate hole h2_5/h8_5, green x=block p2 tip (hover 35)",(8,Hh-10),0,0.55,(0,0,0),2)
cv2.imwrite('refs/trailer/16_6.jpg',im,[cv2.IMWRITE_JPEG_QUALITY,88])
idx=json.load(open('refs/trailer/index.json',encoding='utf-8'))
idx=[r for r in idx if not (r['step']==16 and r['idx'] in (4,6))]
idx.append({"step":16,"idx":4,"file":"16_4.jpg","note":"④-2 단계 16 — 번호 대조(칸.줄 번호) 홀라인 두 판: 빨강 = 흰 59프레임(맨 앞 두 줄 구멍 16점을 책에서 읽어 카메라 2.04px 로 풀고 45칸 투영), 초록 = 검은 27프레임(모델 띄움 35 투영 14칸). ⚠ holefit 기준 미달이라 근거 기반 격자."})
idx.append({"step":16,"idx":6,"file":"16_6.jpg","note":"⑥ 단계 16 — 책 링 번호 대조 ↔ 모델: 빨간 원 = 책 링 2(흰 판 맨 앞 줄 칸2·칸8), 파란 + = 모델 구멍 h2_5·h8_5 투영, 초록 × = 블록 돌기 끝(띄움 35)."})
idx.sort(key=lambda r:(r['step'],r['idx'])); json.dump(idx,open('refs/trailer/index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
