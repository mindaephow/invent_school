import json, os, sys, runpy, subprocess, numpy as np, cv2
sys.path.insert(0,'.')
from pnp import fit
f=json.load(open('refs/trailer/fits/16_P.json',encoding='utf-8')); O=np.array(f['xyz3d'],float); I=f['xyz3d_img']; c=O.mean(0)
im=cv2.imread('refs/trailer/16.jpg'); Hh,Ww=im.shape[:2]
e,rv,tv,K=fit(O-c,I,Ww,Hh,f['fov'],None,None)
P=lambda q: cv2.projectPoints(np.float32([np.array(q,float)-c]),rv,tv,K,None)[0][0][0]
A=runpy.run_path('trailer.py',run_name='probe')['A']
q=next(p for p in A.parts if p.n=="27프레임" and p.step.index==15)
h11=np.array(q.hole("h1_1")["pos"],float); h71=np.array(q.hole("h7_1")["pos"],float); h12=np.array(q.hole("h1_2")["pos"],float)
dc=(h71-h11)/6; dr=h12-h11
print("pitch",dc,dr)
for H in [float(a) for a in sys.argv[1:]]:
    up=np.array([0,H,0])
    corners=[h11-dc/2-dr/2,h11+dc*6+dc/2-dr/2,h11+dc*6+dc/2+dr*1+dr/2,h11-dc/2+dr+dr/2]
    cp=[P(x+up) for x in corners]
    arg=" ".join("%.0f %.0f"%tuple(p) for p in cp)
    print(H,arg)
