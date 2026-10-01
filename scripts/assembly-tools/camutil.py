import numpy as np, cv2, math, subprocess, os
from PIL import Image
from pnp import best_fit, fit
def cm_query(rv,tv,fov):
    R,_=cv2.Rodrigues(rv); C=-R.T@tv.reshape(3)
    ox,oy,oz=R.T[:,0],R.T[:,1],R.T[:,2]
    cols=[ox,-oy,-oz]
    a=[]
    for c in cols: a+=list(c)
    a+=list(C)
    return "cm="+",".join(f"{v:.5f}" for v in a)+f"&fov={fov}"
def render(out,step,rv,tv,fov,W=1083,H=949,extra=""):
    q=f"step={step}&{cm_query(rv,tv,fov)}&W={W}&H={H}&{extra}"
    tmp=os.path.abspath("_r.png")
    subprocess.run(["bash",os.path.abspath("shot.sh"),tmp,q,str(W+40),str(H+200)])
    Image.open(tmp).crop((0,0,W,H)).save(out)
def overlay(panel,rendered,out,gain=0.5):
    a=Image.open(panel).convert("RGB"); b=Image.open(rendered).convert("RGB").resize(a.size)
    A=np.asarray(a).astype(float);B=np.asarray(b).astype(float)
    A=255-(255-A)*gain; C=(A*B/255).clip(0,255).astype("uint8"); Image.fromarray(C).save(out)
