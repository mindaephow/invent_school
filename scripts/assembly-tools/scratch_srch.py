import sys, numpy as np, cv2, runpy, itertools
sys.stdout.reconfigure(encoding="utf-8")
from scipy.spatial import cKDTree
from pnp import fit, cam_from
N=int(sys.argv[1]); th0=float(sys.argv[2]); ph0=float(sys.argv[3])
g=runpy.run_path("trailer.py",run_name="probe"); A=g['A']
R3=np.array([q.p for q in A.parts if q.n=="리벳" and q.step.index<=24],float)
im=cv2.imread('refs/trailer/%d.jpg'%N); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,(5,150,120),(20,255,255)); m=cv2.dilate(m,np.ones((9,9),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
B=np.array([cen[i] for i in range(1,n) if st[i,4]>150 and cen[i][0]>120 and cen[i][1]>80]); print(len(B),"blobs",np.round(B).astype(int).tolist())
def proj(th,ph):
    fwd=np.array([-np.sin(th)*np.sin(ph),-np.cos(ph),-np.cos(th)*np.sin(ph)]); right=np.cross(fwd,[0,1.,0]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
    return np.stack([R3@right,-(R3@up)],1)
tree=cKDTree(B); best=[]
for th in np.arange(th0-0.4,th0+0.41,0.05):
  for ph in np.arange(ph0-0.25,ph0+0.26,0.05):
    P=proj(th,ph)
    for s in np.arange(2.0,6.0,0.25):
      Q=P*s
      for bi in range(len(B)):
        for ri in range(len(Q)):
          t=B[bi]-Q[ri]; d,_=tree.query(Q+t); sc=(d<12).sum()
          if sc>=7: best.append((int(sc),round(th,2),round(ph,2),round(s,2),round(float(t[0])),round(float(t[1]))))
best.sort(reverse=True); print(best[:8])
