import numpy as np, cv2, math
def fit(obj,img,W,H,fov_deg):
    f=(H/2)/math.tan(math.radians(fov_deg)/2)
    K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1]],float)
    obj=np.array(obj,float);img=np.array(img,float)
    best=None
    for flags in ((cv2.SOLVEPNP_ITERATIVE,) if len(obj)>=6 or abs(obj[:,1].max()-obj[:,1].min())<1e-6 else (cv2.SOLVEPNP_EPNP,)):
        try:
            ok,rv,tv=cv2.solvePnP(obj,img,K,None,flags=flags)
        except cv2.error:
            continue
        if not ok: continue
        if flags==cv2.SOLVEPNP_EPNP:
            rv,tv=cv2.solvePnPRefineLM(obj,img,K,None,rv,tv)
        proj,_=cv2.projectPoints(obj,rv,tv,K,None)
        err=np.linalg.norm(proj.reshape(-1,2)-img,axis=1)
        if best is None or err.mean()<best[0]: best=(err.mean(),rv,tv,K)
    return best
def cam_from(rv,tv):
    R,_=cv2.Rodrigues(rv); C=-R.T@tv.reshape(3)   # camera position (world), OpenCV: x right, y down, z forward
    fwd=R.T@np.array([0,0,1.0]); up=-(R.T@np.array([0,1.0,0])); right=R.T@np.array([1.0,0,0])
    return C,fwd,up,right
def angles(C,target):
    d=C-np.array(target,float); r=np.linalg.norm(d)
    az=math.degrees(math.atan2(d[0],d[2])); el=math.degrees(math.asin(d[1]/r))
    return az,el,r
if __name__=="__main__":
    obj=[[-40,0,-20],[40,0,-20],[40,0,70],[-40,0,70]]
    img=[[105,491],[451,262],[828,516],[486,843]]
    for fov in (20,25,30,35,45,60):
        e,rv,tv,K=fit(obj,img,1083,953,fov)
        C,fwd,up,right=cam_from(rv,tv)
        # intersection of view axis with plane y=0 -> target
        t=-C[1]/fwd[1]; T=C+fwd*t
        print(fov,"err",round(e,2),"cam",np.round(C,0),"target",np.round(T,0),"az,el,r",[round(v,1) for v in angles(C,T)],"up_y",round(up[1],2))

def best_fit(obj,img,W,H,fovs=range(20,71,5)):
    best=None
    for fov in fovs:
        r=fit(obj,img,W,H,fov)
        if r is None: continue
        if best is None or r[0]<best[0][0]: best=(r,fov)
    return best
def pix_to_plane(K,rv,tv,uv,y):
    """ray through pixel uv hits plane Y=y (world)."""
    R,_=cv2.Rodrigues(rv); C=-R.T@tv.reshape(3)
    d=R.T@np.linalg.inv(K)@np.array([uv[0],uv[1],1.0])
    t=(y-C[1])/d[1]
    return C+d*t
def plane_from_pixels(obj,img,pix,y,W=1083,H=949,fovs=range(20,71,5)):
    (e,rv,tv,K),fov=best_fit(obj,img,W,H,fovs)
    out=[pix_to_plane(K,rv,tv,p,y) for p in pix]
    return e,fov,out,(rv,tv,K)
