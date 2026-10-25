import json, sys, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/16_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
e,rv,tv,K=fit(O-c,I,1000,870,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
for H in (30,35,40,45):
    print(H,[np.round(P((x,28.5+H,14.5)),0).tolist() for x in (-35,35)], np.round(P((35,8.5+H,14.5)),0).tolist())
