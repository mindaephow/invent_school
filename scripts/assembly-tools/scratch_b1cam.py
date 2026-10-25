import numpy as np, cv2, math
from scipy.optimize import least_squares
W,H=1000,870
def proj(P,th,ph,fov,D,tgt):
    fwd=np.array([-math.sin(th)*math.sin(ph),-math.cos(ph),-math.cos(th)*math.sin(ph)])
    right=np.array([-fwd[2],0,fwd[0]]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
    C=np.array(tgt)-fwd*D; f=(H/2)/math.tan(math.radians(fov)/2)
    out=[]
    for p in P:
        d=np.array(p)-C; x=d@right; y=d@up; z=d@fwd
        out.append((W/2+f*x/z, H/2-f*y/z))
    return np.array(out)
# (x,z, which height, pixel)
pts=[(-40,-5,'a',(345,222)),(-40,5,'a',(367,239)),(40,-5,'a',(693,177)),(40,5,'a',(720,188)),
     (-40,-5,'f',(360,455)),(40,-5,'f',(685,383)),(-40,5,'n',(380,520)),(40,5,'n',(708,445)),
     (0,-5,'a',(528,198)),(0,5,'a',(548,210)),(0,-5,'f',(527,430)),(0,5,'n',(545,495))]
img=np.array([p[3] for p in pts],float)
def res(v):
    th,ph,fov,D,ha,hf,hn=v
    P=[(x,{'a':ha,'f':hf,'n':hn}[k],z) for x,z,k,_ in pts]
    return (proj(P,th,ph,fov,D,(0,60,0))-img).ravel()
best=None
for th in np.linspace(-3,3,13):
    for ph in (0.7,1.0,1.3):
        for fov in (20,30,40):
            v0=[th,ph,fov,500,160,80,0]
            try: r=least_squares(res,v0,bounds=([-7,0.3,10,100,-50,-50,-50],[7,1.5,60,3000,400,400,400]))
            except Exception as e: continue
            if best is None or r.cost<best.cost: best=r
v=best.x; e=np.linalg.norm(res(v).reshape(-1,2),axis=1)
print('cost',best.cost,'th %.2f ph %.2f fov %.1f D %.0f ha %.0f hf %.0f hn %.0f'%tuple(v)); print(e.round(1))
