import numpy as np, cv2, math
def lookat(az,el,dist,target):
    a,e=math.radians(az),math.radians(el)
    C=np.array(target)+dist*np.array([math.sin(a)*math.cos(e),math.sin(e),math.cos(a)*math.cos(e)])
    f=(np.array(target)-C); f/=np.linalg.norm(f)
    r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
    # opencv: x right, y down, z forward
    R=np.array([r,-u,f]); t=-R@C
    return R,t
def scan(obj,img,W,H,target,fovs=range(10,61,5),azs=range(-90,91,6),els=range(10,71,5),dists=(250,400,600,900)):
    obj=np.array(obj,float);img=np.array(img,float);best=None
    for fov in fovs:
        f=(H/2)/math.tan(math.radians(fov)/2);K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
        for az in azs:
            for el in els:
                for dist in dists:
                    R,t=lookat(az,el,dist,target)
                    rv,_=cv2.Rodrigues(R)
                    try:
                        ok,rv2,tv2=cv2.solvePnP(obj,img,K,None,rv.copy(),t.reshape(3,1).copy(),True,cv2.SOLVEPNP_ITERATIVE)
                    except cv2.error: continue
                    if not ok: continue
                    p,_=cv2.projectPoints(obj,rv2,tv2,K,None); e=np.linalg.norm(p.reshape(-1,2)-img,axis=1).mean()
                    R2,_=cv2.Rodrigues(rv2); C=-R2.T@tv2.reshape(3)
                    if C[1]<=0: continue
                    if best is None or e<best[0]: best=(e,fov,C,R2,tv2)
    e,fov,C,R2,tv2=best
    d=C-np.array(target); az=math.degrees(math.atan2(d[0],d[2])); el=math.degrees(math.asin(d[1]/np.linalg.norm(d)))
    return e,fov,az,el
