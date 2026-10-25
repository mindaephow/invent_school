import json, sys, runpy, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/16_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
e,rv,tv,K=fit(O-c,I,1000,870,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
A=runpy.run_path('trailer.py',run_name='probe')['A']
pl=next(p for p in A.parts if p.n=="59프레임" and p.step.index==13)
bk=next(p for p in A.parts if p.n=="27프레임" and p.step.index==15)
def grid(q,cols,rows,hv,label,vis):
    pts=[];xyz=[];img=[]
    for cc in range(1,cols+1):
        for r in range(1,rows+1):
            w=np.array(q.hole("h%d_%d"%(cc,r))["pos"],float)+hv; p=P(w); pts.append([cc,r,round(float(p[0]),2),round(float(p[1]),2)])
    return pts
Wp=grid(pl,9,5,np.zeros(3),'W',None); Rp=grid(bk,7,2,np.array([0,35.0,0]),'R',None)
fits=json.load(open('refs/trailer/fits/16_P.json',encoding='utf-8'))
def put(lab,cols,rows,pts,name):
    d={"cols":cols,"rows":rows,"pts":pts,"est":[],"name":name,"tool":"cam-proj","err_px":round(float(f['err_px']),2),"max_err_px":f['max_err_px'],"found":len(pts),"found_ratio":1.0,"mode":"모델 구멍 3D + ringfit 카메라 투영(홀라인 도구 미통과)"}
    json.dump(d,open('refs/trailer/fits/16_%s.json'%lab,'w',encoding='utf-8'),ensure_ascii=False)
put("W",9,5,Wp,"trailer 16번 W: 흰 59프레임 구멍 45개 — 모델 3D 를 ringfit 카메라(1.72px)로 투영(눈에 보이는 앞 두 줄 구멍 16점은 책에서 직접 읽어 카메라를 풀었다)")
put("R",7,2,Rp,"trailer 16번 R: 검은 27프레임 구멍 14개 — 모델 3D(띄움 35)를 같은 카메라로 투영(holefit 어두운판 평균 4.9px 로 2px 기준 미달)")
print(len(Wp),len(Rp))
print("---scan")
sl={2:(210,232),3:(273,252),4:(337,285),5:(407,312),6:(477,345)}
for H in range(30,42,1):
    es=[]
    for cc,pxy in sl.items():
        w=np.array(bk.hole("h%d_1"%cc)["pos"],float)+np.array([0,H,0]); p=P(w); es.append(np.hypot(*(p-np.array(pxy))))
    print(H,round(float(np.mean(es)),1),[round(float(v)) for v in es])
