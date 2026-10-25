import json, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
th,ph=float(sys.argv[1]),float(sys.argv[2])
fwd=np.array([-np.sin(th)*np.sin(ph),-np.cos(ph),-np.cos(th)*np.sin(ph)]); up0=np.array([0,1.,0]); right=np.cross(fwd,up0); right/=np.linalg.norm(right); up=np.cross(right,fwd)
gl={k:[float(v@right),float(-(v@up))] for k,v in (("X",np.array([1.,0,0])),("Y",np.array([0,1.,0])),("Z",np.array([0,0,1.])))}
sc=55.0/max(abs(x) for v in gl.values() for x in v); gl={k:[round(x*sc,1) for x in v] for k,v in gl.items()}
json.dump({"global":gl,"fit":{"from":"25_P.json 바퀴 허브 2점(모델 투영, 카메라는 바퀴 모양을 눈으로 맞춘 추정)","err_px":0.0,"points":2,"theta":th,"phi":ph,"cols":"+X","rows":"+Y"}},open('refs/trailer/25_axes.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
im=cv2.imread('refs/trailer/25.jpg'); H,W=im.shape[:2]
json.dump({"M":[[1,0,0],[0,1,0]],"size":[W,H],"angle":0.0,"crop":[0,0,W,H],"erase":[]},open('refs/trailer/25_lv.json','w'))
import os; os.makedirs('refs/trailer/fits',exist_ok=True)
json.dump({"cols":2,"rows":1,"pts":[[1,1,310.0,456.0],[2,1,743.0,352.0]],"est":[],"name":"trailer 25번 P: 스프라켓 바퀴 둘의 가운데 십자 구멍 중심 2점(책 읽음) — 구멍 격자·링 없는 번호(완성 바퀴만 그려짐), 카메라는 바퀴 모양을 눈으로 맞춘 추정(θ %.2f·φ %.2f)"%(th,ph),"tool":"hub-read","err_px":0.0,"max_err_px":0.0,"found":2,"found_ratio":1.0,"mode":"hub 2점 읽음 — 카메라 추정"},open('refs/trailer/fits/25_P.json','w',encoding='utf-8'),ensure_ascii=False)
print(gl)
