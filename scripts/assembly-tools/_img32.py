# 32번 이미지 작업(홀라인 + 방향 + 결합): 홀라인 격자(32_Q)로 카메라를 풀고, 완성품 기준 앞뒤좌우위 방향선·판 칸/줄 번호·결합할 블록 구멍·나사 경로를 한 장(32_4.jpg)에 그린다
import json,runpy,numpy as np,cv2,math,sys
sys.stdout.reconfigure(encoding="utf-8")
from pnp import cam_from
from PIL import Image,ImageDraw,ImageFont
g=runpy.run_path("battlerobot2.py",run_name="probe")
PL30,PL31=g["PL30"],g["PL31"]; ey=np.array(g["_ey"],float); blk=g["_BLK1"]; hp=g["_hp"]; hov=60.0
def hole(c,r): P,rr=(PL30,r) if r<=5 else (PL31,r-5); return P.hole("h%d_%d"%(c,rr))["pos"]+ey*hov
f=json.load(open('refs/battlerobot2/fits/32_Q.json',encoding='utf-8')); pts=f['pts']
obj=np.array([hole(c,r) for c,r,x,y in pts],np.float64); img=np.array([[x,y] for c,r,x,y in pts],np.float64)
im=cv2.imread('refs/battlerobot2/32.jpg'); H,W=im.shape[:2]; cc=obj.mean(0); best=None
for fov in (22,26,30,34,38,45):
    fl=(H/2)/math.tan(math.radians(fov)/2); K=np.array([[fl,0,W/2],[0,fl,H/2],[0,0,1]])
    n,rvs,tvs,_=cv2.solvePnPGeneric(obj-cc,img,K,None,flags=cv2.SOLVEPNP_IPPE)
    for rv,tv in zip(rvs,tvs):
        pr,_=cv2.projectPoints(obj-cc,rv,tv,K,None); e=float(np.linalg.norm(pr.reshape(-1,2)-img,axis=1).mean())
        C,fwd,up,right=cam_from(rv,tv)
        if up[1]>0 and (best is None or e<best[0]): best=(e,fov,rv,tv,K,C[1])
e,fov,rv,tv,K,cy=best
P=lambda q: cv2.projectPoints(np.float64([np.array(q,float)-cc]),rv,tv,K,None)[0][0][0]
ring=[P(hole(8,r)) for r in (4,5,6)]; blkp=[P(q+ey*hov*0) for q in hp]
from pnp import angles
Cc,_,_,_=cam_from(rv,tv); az,el,_=angles(Cc,[0,0,0]); TH=round(math.radians(az),2); PH=round(math.radians(90-el),2)
b=np.array(hole(1,1),float); vv={k:P(b+np.array(dd)*50)-P(b) for k,dd in (("X",[1,0,0]),("Y",[0,1,0]),("Z",[0,0,1]))}
sc=55/max(abs(x) for v_ in vv.values() for x in v_); gl0={k:[float(v_[0]*sc),float(v_[1]*sc)] for k,v_ in vv.items()}; gl={"X":[round(-gl0["Z"][0],1),round(-gl0["Z"][1],1)],"Y":[round(gl0["Y"][0],1),round(gl0["Y"][1],1)],"Z":[round(gl0["X"][0],1),round(gl0["X"][1],1)]}   # 완성품 이름: 앞 +Z = 모델 +x, 왼쪽 +X = 모델 -z
f['xyz3d']=obj.tolist(); f['xyz3d_img']=img.tolist(); f['fov']=fov; f['tool']="holefit"
f['name']="32번 — 홀라인(holefit DoG, 15칸x10줄, 구멍 99개 배정, 평균 0.9px 통과)으로 만든 격자. 3D = 모델의 판 구멍(팔 끝 블록 구멍에 칸8 줄4·5·6 을 맞춘 자세, 분리 60). 카메라를 이 격자로 풀었고 팔 끝 블록 구멍 3개의 투영이 책 팔 링과 9px 안으로 맞음."
json.dump(f,open('refs/battlerobot2/fits/32_P.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({"global":gl,"fit":{"from":"32_P.json","err_px":round(e,2),"points":len(obj),"theta":TH,"phi":PH,"cols":"+X","rows":"+Y"},"no_rotate":True,"origin_cell":[1,1]},open('refs/battlerobot2/32_axes.json','w'),indent=1)
print("THETA_PHI",TH,PH)
print("카메라 오차 %.2f fov %d 카메라 높이 %.0f"%(e,fov,cy)); wh=[np.array([-30,25,-39.]),np.array([-30,25,94.])]; print("바퀴 투영",[np.round(P(w)).tolist() for w in wh]," 몸 가운데",np.round(P(np.array([0,40,27.5]))).tolist())
print("판 링 투영",np.round(ring).tolist(),"책 링 (685,300)(710,337)(740,375)"); print("블록 구멍 투영(분리 전)",np.round(blkp).tolist(),"책 팔 링 (462,443)(490,475)(518,510)")
# 방향: 완성품 기준 앞=팔1 쪽(−x), 위=+y, 왼쪽=+X(book)=model +z
D={"앞(+Z)":np.array([1,0,0.]),"뒤(-Z)":np.array([-1,0,0.]),"위(+Y)":np.array([0,1,0.]),"왼쪽(+X)":np.array([0,0,-1.]),"오른쪽(-X)":np.array([0,0,1.])}
pil=Image.open('refs/battlerobot2/32.jpg').convert("RGB"); d=ImageDraw.Draw(pil)
try: ft=ImageFont.truetype("malgun.ttf",22); fs=ImageFont.truetype("malgun.ttf",15)
except Exception: ft=fs=ImageFont.load_default()
col={"앞(+Z)":(220,30,30),"뒤(-Z)":(150,60,200),"위(+Y)":(20,140,40),"왼쪽(+X)":(230,130,0),"오른쪽(-X)":(120,60,200)}
o2=np.array([150.0,690.0]); pc=P(hp[1])
for k,v in D.items():
    dv=P(hp[1]+v*60)-pc; dv=dv/np.linalg.norm(dv)*95; q=o2+dv
    d.line([tuple(o2),tuple(q)],fill=col[k],width=5); d.ellipse([q[0]-5,q[1]-5,q[0]+5,q[1]+5],fill=col[k]); d.text((q[0]+6,q[1]-12),k,fill=col[k],font=ft)
d.text((60,600),"방향(완성품 기준)",fill=(0,0,0),font=ft)
for c,r,x,y in pts:
    d.ellipse([x-2,y-2,x+2,y+2],fill=(255,0,0))
    if r==1 and (c%2==1 or c==15): d.text((x-6,y-20),str(c),fill=(0,60,255),font=fs)
    if c==1 and r in (1,4,5,6,10): d.text((x-24,y-6),"줄%d"%r,fill=(0,140,0),font=fs)
for (c,r),q in zip(((8,4),(8,5),(8,6)),ring):
    d.ellipse([q[0]-16,q[1]-16,q[0]+16,q[1]+16],outline=(255,200,0),width=4); d.text((q[0]+18,q[1]-8),"칸8 줄%d"%r,fill=(255,120,0),font=ft)
for i,q in enumerate(blkp):
    d.ellipse([q[0]-14,q[1]-14,q[0]+14,q[1]+14],outline=(0,200,255),width=3); d.text((q[0]-90,q[1]-8),"블록 구멍%d"%(i+1),fill=(0,120,200),font=fs)
for a,b in zip(ring,blkp): d.line([tuple(a),tuple(b)],fill=(220,200,0),width=2)
d.text((10,780),"32번: 홀라인(15칸×10줄, 0.9px) + 완성품 기준 방향(완성품 기준 앞=+Z(모델 +x, 판 쪽)·왼쪽=+X(모델 -z)·위=+Y) + 나사 경로(판 칸8 줄4·5·6 → 팔 끝 블록 구멍 3개)",fill=(0,0,0),font=fs)
# 홀라인 방향선: 칸 방향·줄 방향·판 법선을 판 구멍 격자 위에 그린다
c1r1=np.array([x for c,r,x,y in pts if c==1 and r==1]+[y for c,r,x,y in pts if c==1 and r==1]); 
def pt(c,r): return next(np.array([x,y]) for cc_,rr_,x,y in pts if cc_==c and rr_==r)
a0=pt(3,2); a1=pt(13,2); b0=pt(3,2); b1=pt(3,9)
def arrow(p,q,colr,txt):
    d.line([tuple(p),tuple(q)],fill=colr,width=6); v=(q-p)/np.linalg.norm(q-p); n=np.array([-v[1],v[0]])
    d.polygon([tuple(q),tuple(q-v*22+n*10),tuple(q-v*22-n*10)],fill=colr); d.text((q[0]-(len(txt)*21 if q[0]>650 else -8),q[1]-34 if q[0]>650 else q[1]-10),txt,fill=colr,font=ft)
_exw=np.array(g["_ex"],float); arrow(a0,a1,(230,130,0),"칸 방향 = 좌우(+X 왼쪽)")
_ezw=np.array(g["_ez"],float); arrow(b0,b1,(220,30,30),"줄 방향 = 팔 방향(앞·아래)")
nv=P(hp[1]+ey*60)-P(hp[1]); nv=nv/np.linalg.norm(nv)*90; p0=pt(8,5)
arrow(p0,p0+nv,(20,140,40),"판 법선(나사 들어가는 쪽)")
pil.save('refs/battlerobot2/32_4.jpg',quality=92)
idx=json.load(open('refs/battlerobot2/index.json',encoding='utf-8'))
if not any(r['step']==32 and r['idx']==4 for r in idx): idx.append({"step":32,"idx":4,"file":"32_4.jpg","note":"32번 방향·결합 확인: 홀라인 격자 번호, 완성품 기준 앞뒤좌우위 방향선, 나사 경로(판 칸8 줄4·5·6 → 팔 끝 블록 구멍)"}); json.dump(idx,open('refs/battlerobot2/index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
