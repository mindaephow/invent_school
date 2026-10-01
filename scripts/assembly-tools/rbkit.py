import numpy as np, json, math
from rbtools import euler_to_R, R_to_euler, orient, conn
EX=np.array([1.,0,0]);EY=np.array([0,1.,0]);EZ=np.array([0,0,1.])
def U(v): v=np.array(v,float); return v/np.linalg.norm(v)
def rnd(v): return [round(float(x),3)+0.0 for x in v]
class Model:
    def __init__(s): s.steps=[]; s.cur=None; s.parts_T={}   # name->pose
    def step(s,note,view=0,**kw):
        s.cur={"note":note,"parts":[]}; 
        if view: s.cur["view"]=view
        s.cur.update(kw); s.steps.append(s.cur); return s.cur
    def add(s,n,p,R,**kw):
        r=R_to_euler(R) if not isinstance(R,list) else R
        d={"n":n,"p":rnd(p),"r":[round(float(x),4)+0.0 for x in r]}; d.update(kw); s.cur["parts"].append(d); return d
def peg_world(n,p,R,pid=None):
    c=conn[n]; out=[]
    for x in c.get("pegs",[]):
        out.append({"id":x["id"],"pos":np.array(p)+R@np.array(x["pos"]),"dir":R@np.array(x["dir"]),"len":x.get("len",0)})
    return out
def hole_world(n,p,R):
    c=conn[n]; out=[]
    for x in c.get("holes",[]):
        out.append({"id":x["id"],"pos":np.array(p)+R@np.array(x["pos"]),"dir":R@np.array(x["dir"]),"len":x.get("len",0),"through":x.get("through",False)})
    return out
def frame_R(length_axis,hole_axis):
    ex=U(length_axis);ey=U(hole_axis);ez=np.cross(ex,ey)
    return np.column_stack([ex,ey,ez])
def block_R(length_axis,up):
    """block: local x along length_axis, local z = up (peg axis). returns R"""
    ex=U(length_axis);ez=U(up);ey=np.cross(ez,ex)
    return np.column_stack([ex,ey,ez])
def solve_p_pegs(n,R,peg_dir,target_mid):
    """place so that mean of pegs pointing along peg_dir (world) has center at target_mid"""
    pw=[q for q in peg_world(n,np.zeros(3),R) if np.dot(q["dir"],U(peg_dir))>0.99]
    assert pw,("no pegs in dir",n,peg_dir)
    mid=np.mean([q["pos"] for q in pw],axis=0)
    return np.array(target_mid,float)-mid
