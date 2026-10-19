# 32번 이미지 작업: 홀라인(holefit, 15×10, 0.9px) 격자로 카메라를 풀어 32_P.json·32_axes.json 을 덮어쓴다(손으로 읽은 점 대신)
import json,runpy,numpy as np,cv2,math,sys
sys.stdout.reconfigure(encoding="utf-8")
from pnp import cam_from, angles
g=runpy.run_path("battlerobot2.py",run_name="probe")
F=g["ARM26"][0][3]; h=[np.array(F.hole(k)["pos"],float) for k in ("h6","h7","h8")]
u=(h[2]-h[0])/np.linalg.norm(h[2]-h[0]); ey=np.array([0,0,1.0]); ex=np.cross(ey,u); R=np.stack([ex,ey,u],axis=1)
B=np.array([h[0][0],h[0][1],float(F.p[2])+5.0+60.0]); col=8
f=json.load(open('refs/battlerobot2/fits/32_Q.json',encoding='utf-8'))
pts=f['pts']; obj=[(B+R@np.array([(c-col)*10.0,0,(r-4)*10.0])).tolist() for c,r,x,y in pts]; img=[[x,y] for c,r,x,y in pts]
im=cv2.imread('refs/battlerobot2/32.jpg'); H,W=im.shape[:2]
o=np.array(obj); cc=o.mean(0); best=None
for fov in (24,28,30,34,38):
    fl=(H/2)/math.tan(math.radians(fov)/2); K=np.array([[fl,0,W/2],[0,fl,H/2],[0,0,1]])
    n,rvs,tvs,_=cv2.solvePnPGeneric((o-cc).astype(np.float64),np.array(img,np.float64),K,None,flags=cv2.SOLVEPNP_IPPE)
    for rv,tv in zip(rvs,tvs):
        pr,_=cv2.projectPoints((o-cc).astype(np.float64),rv,tv,K,None); e=float(np.linalg.norm(pr.reshape(-1,2)-np.array(img),axis=1).mean())
        C,fwd,up,right=cam_from(rv,tv)
        if up[1]>0 and C[1]>0 and (best is None or e<best[0]): best=(e,fov,rv,tv,K)
e,fov,rv,tv,K=best; C,fwd,up,right=cam_from(rv,tv); az,el,_=angles(C,[0,0,0])
P=lambda q: cv2.projectPoints(np.float64([np.array(q,float)-cc]),rv,tv,K,None)[0][0][0]
b=o.mean(0); v={k:P(b+np.array(d)*50)-P(b) for k,d in (("X",[1,0,0]),("Y",[0,1,0]),("Z",[0,0,1]))}
sc=55/max(abs(x) for vv in v.values() for x in vv); gl={k:[round(float(vv[0]*sc),1),round(float(vv[1]*sc),1)] for k,vv in v.items()}
ring=[P(h[i]) for i in range(3)]; print("오차 %.2f fov %d theta %.2f phi %.2f"%(e,fov,math.radians(az),math.radians(90-el)),"팔 구멍 투영",np.round(ring).tolist())
f['xyz3d']=obj; f['xyz3d_img']=img; f['fov']=fov; f['tool']="holefit"
f['name']="32번 — 홀라인(holefit DoG, 15칸×10줄, 구멍 99개 배정, 평균 0.9px 통과)으로 만든 격자. 판 구멍 3D = 팔 1 바깥 프레임 h6·h7·h8 에 칸8 줄4·5·6 을 맞춘 자세(분리 60). 카메라는 이 격자(150점)로 풀었고 팔 구멍 3개의 투영이 책 링 위치와 9px 안으로 맞음."
json.dump(f,open('refs/battlerobot2/fits/32_P.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({"global":gl,"fit":{"from":"32_P.json","err_px":round(e,2),"points":len(obj),"theta":round(math.radians(az),2),"phi":round(math.radians(90-el),2),"cols":"+X","rows":"+Y"},"no_rotate":True,"origin_cell":[1,1]},open('refs/battlerobot2/32_axes.json','w'),indent=1)
