import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import numpy as np, cv2, math
def fit(obj,img,W,H,fov_deg,cx=None,cy=None):   # cx,cy = 주점(책 그림이 잘려 있으면 한가운데가 아니다, 2026-10-19 _regcam.py)
    f=(H/2)/math.tan(math.radians(fov_deg)/2)
    K=np.array([[f,0,W/2 if cx is None else cx],[0,f,H/2 if cy is None else cy],[0,0,1]],float)
    obj=np.array(obj,float);img=np.array(img,float)
    best=None
    c=obj-obj.mean(0); planar=np.linalg.svd(c,compute_uv=False)[-1]<1e-6*max(1.0,np.abs(c).max())   # 한 평면 위의 점(어느 방향이든)은 EPNP 가 불안정 → IPPE 도 시도(2026-10-17, 배틀로봇 13번에서 평면 점이 19px 로 잘못 풀린 것을 발견)
    cands=[(cv2.SOLVEPNP_ITERATIVE,)] if (len(obj)>=6 or abs(obj[:,1].max()-obj[:,1].min())<1e-6) else [(cv2.SOLVEPNP_EPNP,)]
    if planar and len(obj)>=4: cands.append((cv2.SOLVEPNP_IPPE,))
    for (flags,) in cands:
        try:
            if flags==cv2.SOLVEPNP_IPPE:
                n,rvs,tvs,_=cv2.solvePnPGeneric(obj,img,K,None,flags=flags); sols=[(rvs[i],tvs[i]) for i in range(n)]
            else:
                ok,rv,tv=cv2.solvePnP(obj,img,K,None,flags=flags); sols=[(rv,tv)] if ok else []
        except cv2.error:
            continue
        for rv,tv in sols:
            if flags in (cv2.SOLVEPNP_EPNP,cv2.SOLVEPNP_IPPE):
                try: rv,tv=cv2.solvePnPRefineLM(obj,img,K,None,rv,tv)
                except cv2.error: pass
            proj,_=cv2.projectPoints(obj,rv,tv,K,None)
            err=np.linalg.norm(proj.reshape(-1,2)-img,axis=1)
            C_=-cv2.Rodrigues(rv)[0].T@np.array(tv).reshape(3); up=-(cv2.Rodrigues(rv)[0].T@np.array([0,1.0,0]))
            behind=(cv2.Rodrigues(rv)[0]@obj.T).T[:,2]+np.array(tv).reshape(3)[2]<=0   # 점이 카메라 뒤로 간 해는 거울 해(2026-11-02 해머배틀 17번: 화면에서 프레임이 위아래로 뒤집혀 보였다)
            key=err.mean()+(0 if up[1]>0 else 1e6)+(1e6 if behind.any() else 0)   # 위쪽이 위인 해를 먼저(두 해가 거울이면 위쪽이 위인 것)
            if best is None or key<best[0]: best=(key,err.mean(),rv,tv)
    if (best is None or best[0]>=1e6) and len(obj)>=4:   # 위쪽이 위인 해를 못 찾았으면(거의 한 평면·가까운 두 평면 점) 여러 초기 방향에서 반복해 위쪽이 위인 해를 찾는다(2026-10-17 배틀로봇 25번)
        ctr=obj.mean(0); span=max(40.0,float(np.abs(obj-ctr).max()))
        for th in np.linspace(-math.pi,math.pi,13)[:-1]:
            for ph in (0.7,1.0,1.3):
                for dist in (3.0,6.0):
                    d=np.array([math.sin(th)*math.sin(ph),math.cos(ph),math.cos(th)*math.sin(ph)])*span*dist
                    z=-d/np.linalg.norm(d); x=np.cross([0,1.0,0],z); x/=np.linalg.norm(x); y=np.cross(z,x)
                    R0=np.array([x,y,z]); rv0,_=cv2.Rodrigues(R0); tv0=(-R0@(d)).reshape(3,1)
                    try: ok,rv,tv=cv2.solvePnP(obj-0,img,K,None,rvec=rv0.copy(),tvec=tv0.copy(),useExtrinsicGuess=True,flags=cv2.SOLVEPNP_ITERATIVE)
                    except cv2.error: continue
                    if not ok: continue
                    proj,_=cv2.projectPoints(obj,rv,tv,K,None); err=np.linalg.norm(proj.reshape(-1,2)-img,axis=1)
                    up=-(cv2.Rodrigues(rv)[0].T@np.array([0,1.0,0]))
                    behind=(cv2.Rodrigues(rv)[0]@obj.T).T[:,2]+np.array(tv).reshape(3)[2]<=0
                    key=err.mean()+(0 if up[1]>0 else 1e6)+(1e6 if behind.any() else 0)
                    if best is None or key<best[0]: best=(key,err.mean(),rv,tv)
    if best is None: return None
    return (best[1],best[2],best[3],K)
def planar_pair(obj,img,K,tol=1.5):
    """점이 (거의) 한 평면 위면 그 평면 앞에서 보는 해와 뒤에서 보는 거울 해를 둘 다 돌려준다 -> [(평균 오차 px, rv, tv)] (평면이 아니면 []).
    누운 판(y 일정)뿐 아니라 서 있는 판(z·x 일정)·기운 판도 같다 — 점을 가장 잘 맞는 평면에 내려 IPPE 로 두 해를 구한 뒤 원래 점으로 다듬는다(2026-11-15 꼬마기사 9번: 서 있는 판의 거울 해를 손으로 갈랐다)."""
    obj=np.array(obj,float);img=np.array(img,float)
    if len(obj)<4: return []
    ctr=obj.mean(0);u,sv,vt=np.linalg.svd(obj-ctr)
    if sv[-1]/math.sqrt(len(obj))>tol: return []
    nrm=vt[-1];flat=obj-np.outer((obj-ctr)@nrm,nrm)
    try: n,rvs,tvs,_=cv2.solvePnPGeneric(flat,img,K,None,flags=cv2.SOLVEPNP_IPPE)
    except cv2.error: return []
    out=[]
    for i in range(n):
        rv,tv=rvs[i],tvs[i]
        try: rv,tv=cv2.solvePnPRefineLM(obj,img,K,None,rv,tv)
        except cv2.error: pass
        if ((cv2.Rodrigues(rv)[0]@obj.T).T[:,2]+np.array(tv).reshape(3)[2]<=0).any(): continue   # 점이 카메라 뒤로 간 해
        err=np.linalg.norm(cv2.projectPoints(obj,rv,tv,K,None)[0].reshape(-1,2)-img,axis=1).mean()
        out.append((float(err),rv,tv))
    return out
def check_err(rv,tv,K,chk):
    """평면 밖 단서 점 chk=[[[x,y,z],[px,py]],…] 를 이 해로 투영했을 때의 평균 오차(px) — 두 거울 해 가운데 작은 쪽이 책과 같은 쪽이다."""
    o=np.array([p for p,q in chk],float);q=np.array([q for p,q in chk],float)
    return float(np.linalg.norm(cv2.projectPoints(o,rv,tv,K,None)[0].reshape(-1,2)-q,axis=1).mean())
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
