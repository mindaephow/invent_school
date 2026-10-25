import sys, numpy as np, cv2, runpy
sys.stdout.reconfigure(encoding="utf-8")
g=runpy.run_path("trailer.py",run_name="probe"); A=g['A']
R3=np.array([q.p for q in A.parts if q.n=="리벳" and q.step.index<=22],float)
print(len(R3))
im=cv2.imread('refs/trailer/24.jpg'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,(5,150,120),(20,255,255)); m=cv2.dilate(m,np.ones((9,9),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
B=np.array([cen[i] for i in range(1,n) if st[i,4]>200]); print(len(B),"blobs")
np.save('scratch_24blobs.npy',B); np.save('scratch_24r3.npy',R3)
best=[]
def proj(th,ph):
    # camera orbit: forward from camera to target
    cth,sth,cph,sph=np.cos(th),np.sin(th),np.cos(ph),np.sin(ph)
    # camera position direction (viewer): matches arctan2(-fwd_x,-fwd_z)=th, arccos(-fwd_y)=ph
    fwd=np.array([-sth*sph,-cph,-cth*sph])
    up0=np.array([0,1,0.]); right=np.cross(fwd,up0); right/=np.linalg.norm(right); up=np.cross(right,fwd)
    return np.stack([R3@right,-(R3@up)],1)
from scipy.spatial import cKDTree
tree=cKDTree(B)
for th in np.arange(-3.1,3.15,0.1):
    for ph in np.arange(0.5,1.4,0.1):
        P=proj(th,ph)
        for s in np.arange(2.0,6.0,0.4):
            Q=P*s
            # translation candidates: align each blob-rivet pair among a few
            for bi in range(0,len(B),1):
                for ri in range(0,len(Q),3):
                    t=B[bi]-Q[ri]; d,_=tree.query(Q+t); sc=(d<14).sum()
                    if sc>=9: best.append((sc,th,ph,s,tuple(t)))
best.sort(reverse=True); print(best[:10])
