# 사용: python camfile.py <번호> <theta> <phi> "<설명>" [from_tag]   — 손으로 맞춘 카메라(theta·phi)에서 축선 벡터를 계산해 NN_axes.json 을 쓴다(눈으로 맞춘 값 = 추정)
import sys, json, math, numpy as np
n=int(sys.argv[1]); th=float(sys.argv[2]); ph=float(sys.argv[3]); why=sys.argv[4]
f=-np.array([math.sin(ph)*math.sin(th), math.cos(ph), math.sin(ph)*math.cos(th)])
r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
d={}
for k,v in (("X",(1,0,0)),("Y",(0,1,0)),("Z",(0,0,1))):
    q=np.array([np.dot(v,r),-np.dot(v,u)]); q=q/np.linalg.norm(q)*55; d[k]=[round(float(q[0]),1),round(float(q[1]),1)]
out={"global":d,"fit":{"from":why,"err_px":None,"points":0,"theta":th,"phi":ph,"cols":"+X","rows":"+Z","hand":True},"no_rotate":True,"origin_cell":[1,1]}
json.dump(out,open("refs/avoider/%02d_axes.json"%n,"w",encoding="utf-8"),ensure_ascii=False); print(d)
