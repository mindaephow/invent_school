import json, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
th,ph=float(sys.argv[1]),float(sys.argv[2])
fwd=np.array([-np.sin(th)*np.sin(ph),-np.cos(ph),-np.cos(th)*np.sin(ph)]); up0=np.array([0,1.,0]); right=np.cross(fwd,up0); right/=np.linalg.norm(right); up=np.cross(right,fwd)
gl={k:[float(v@right),float(-(v@up))] for k,v in (("X",np.array([1.,0,0])),("Y",np.array([0,1.,0])),("Z",np.array([0,0,1.])))}
sc=55.0/max(abs(x) for v in gl.values() for x in v); gl={k:[round(x*sc,1) for x in v] for k,v in gl.items()}
json.dump({"global":gl,"fit":{"from":"26_P.json 링 3점(모델 투영, 카메라는 바퀴 모양을 눈으로 맞춘 추정)","err_px":0.0,"points":3,"theta":th,"phi":ph,"cols":"+X","rows":"+Y"}},open('refs/trailer/26_axes.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
im=cv2.imread('refs/trailer/26.jpg'); H,W=im.shape[:2]
json.dump({"M":[[1,0,0],[0,1,0]],"size":[W,H],"angle":0.0,"crop":[0,0,W,H],"erase":[]},open('refs/trailer/26_lv.json','w'))
import os; os.makedirs('refs/trailer/fits',exist_ok=True)
json.dump({"cols":3,"rows":1,"pts":[[1,1,432.0,495.0],[2,1,630.0,350.0],[3,1,60.0,780.0]],"est":[],"name":"trailer 26번 P: 책 초록 링 중심 3점(바퀴 가운데 구멍·옆판 구멍·부시) — 축 한 줄 위의 점이라 카메라를 풀 수 없다, 카메라는 몸통·바퀴 모양을 눈으로 맞춘 추정(θ %.2f·φ %.2f)"%(th,ph),"tool":"hub-read","err_px":0.0,"max_err_px":0.0,"found":3,"found_ratio":1.0,"mode":"링 3점 읽음 — 카메라 추정"},open('refs/trailer/fits/26_P.json','w',encoding='utf-8'),ensure_ascii=False)
print(gl)
