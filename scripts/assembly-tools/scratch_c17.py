import json, sys, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/17_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
e,rv,tv,K=fit(O-c,I,1000,870,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
F=lambda x,y,z:(x,39.3-y,-z)
book={("h2",1):(310,697),("h2",2):(305,762),("h9",1):(830,580),("h9",2):(830,640)}
# plate holes body: h2_2 (y29.3) h2_1 (y19.3) at z 9.5 ; h9 at z -60.5 ; x -48.5 - H
for H in range(20,70,4):
    es=[]
    for (hc,r),px in book.items():
        z=9.5 if hc=="h2" else -60.5; y=29.3 if r==2 else 19.3
        p=P(F(-48.5-H,y,z)); es.append(np.hypot(*(p-np.array(px))))
    print(H,round(float(np.mean(es)),1),[round(float(v)) for v in es])
