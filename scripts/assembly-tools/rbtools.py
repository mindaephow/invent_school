import numpy as np, json, math
D=math.pi/180
def euler_to_R(r):
    rx,ry,rz=[a*D for a in r]
    cx,sx,cy,sy,cz,sz=math.cos(rx),math.sin(rx),math.cos(ry),math.sin(ry),math.cos(rz),math.sin(rz)
    return np.array([[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]])
def R_to_euler(R):
    sy=-R[2,0]; sy=max(-1,min(1,sy)); ry=math.asin(sy)
    if abs(sy)<0.99999:
        rx=math.atan2(R[2,1],R[2,2]); rz=math.atan2(R[1,0],R[0,0])
    else:
        rx=math.atan2(-R[1,2],R[1,1]); rz=0
    r=[rx/D,ry/D,rz/D]
    return [round(v,4)+0.0 for v in r]
def orient(ex,ey,ez):
    """local x,y,z axes -> these world vectors (columns)"""
    R=np.column_stack([ex,ey,ez]).astype(float)
    assert abs(np.linalg.det(R)-1)<1e-6, ("not right-handed",np.linalg.det(R))
    return R_to_euler(R)
def rot(**kw): pass
# common orientations (local x,y,z -> world) for frames: flat, holes along y
FLAT=[0,0,0]
conn=json.load(open("conn.json",encoding="utf-8"))
def world_conn(part):
    R=euler_to_R(part.get("r",[0,0,0])); p=np.array(part["p"],float); c=conn[part["n"]]
    out={"pegs":[],"holes":[]}
    for k in("pegs","holes"):
        for x in c.get(k,[]):
            out[k].append({"id":x["id"],"pos":p+R@np.array(x["pos"]),"dir":R@np.array(x["dir"]),"len":x.get("len",0),"r":x.get("r",0),"through":x.get("through",False)})
    return out

def _unit(v): v=np.array(v,float); return v/np.linalg.norm(v)
def rot_between(a,b):
    a=_unit(a);b=_unit(b); v=np.cross(a,b); c=float(np.dot(a,b))
    if np.linalg.norm(v)<1e-9:
        if c>0: return np.eye(3)
        # 180: pick axis perpendicular
        ax=np.array([1,0,0]) if abs(a[0])<0.9 else np.array([0,1,0]); ax=_unit(np.cross(a,ax))
        return 2*np.outer(ax,ax)-np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3)+K+K@K*(1/(1+c))
def rot_axis(axis,deg):
    a=_unit(axis);t=deg*D;K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3)+math.sin(t)*K+(1-math.cos(t))*K@K
def _getc(name,cid):
    c=conn[name]
    for k in("pegs","holes"):
        for x in c.get(k,[]):
            if x["id"]==cid: return k,x
    raise KeyError((name,cid))
def attach(mv_name,mv_id,fixed,fixed_id,side=+1,roll=0,flip_base=None,spin_ref=None):
    """moving part connector mv_id goes into/over fixed connector fixed_id.
    peg(moving)->hole(fixed): side=+1 enters along hole.dir (from its -dir face); -1 from the other side (through holes).
    hole(moving)<-peg(fixed): the moving part's hole receives the fixed peg; side ignored (peg direction defines it).
    roll: extra rotation (deg) about the connector axis.  Returns dict(n,p,r)."""
    kind_m,cm=_getc(mv_name,mv_id)
    wf=world_conn(fixed)
    kf=[x for x in wf["pegs"]+wf["holes"] if x["id"]==fixed_id][0]
    kind_f="pegs" if any(x["id"]==fixed_id for x in wf["pegs"]) else "holes"
    if kind_m=="pegs" and kind_f=="holes":
        d=kf["dir"]; Lh=kf["len"]; Lp=cm.get("len",0)
        pdir=d*side
        ctr=kf["pos"]-d*side*0 # center of hole
        # flush with entry face: entry face is at hole center - d*side*Lh/2 ; peg center = that + pdir*Lp/2
        pcenter=kf["pos"]-pdir*Lh/2+pdir*Lp/2
        R0=rot_between(cm["dir"],pdir)
        R=rot_axis(pdir,roll)@R0
        p=pcenter-R@np.array(cm["pos"])
    elif kind_m=="holes" and kind_f=="pegs":
        # moving hole receives fixed peg: hole.dir (insertion dir) must equal fixed peg dir (pointing from base to tip)
        pdir=kf["dir"]; Lh=cm.get("len",0); Lp=kf["len"]
        R0=rot_between(cm["dir"],pdir)
        R=rot_axis(pdir,roll)@R0
        # peg center sits flush: hole center = peg center - ... entry face at peg base side: hole center = peg center + pdir*(Lh-Lp)/2  (hole face flush with peg base)
        hcenter=kf["pos"]+pdir*(Lh-Lp)/2
        p=hcenter-R@np.array(cm["pos"])
    else:
        raise ValueError("peg-peg / hole-hole not supported")
    return {"n":mv_name,"p":[round(float(v),3) for v in p],"r":R_to_euler(R)}
def holes_of(part): return world_conn(part)["holes"]
def pegs_of(part): return world_conn(part)["pegs"]
