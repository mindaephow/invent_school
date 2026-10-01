import numpy as np, cv2, math
from PIL import Image, ImageDraw
from pnp import fit
class Cam:
    def __init__(self,obj,img,W,H,fov=45):
        e,rv,tv,K=fit(obj,img,W,H,fov); self.rv,self.tv,self.K,self.err=rv,tv,K,e; self.W,self.H=W,H
    def proj(self,pts):
        pts=np.array(pts,float).reshape(-1,3)
        p,_=cv2.projectPoints(pts,self.rv,self.tv,self.K,None); return p.reshape(-1,2)
def draw_points(panel,cam,pts,labels=None,out="ov.png",color=(255,0,0),r=5,fs=11,base=None):
    im=Image.open(panel).convert("RGB") if base is None else base
    d=ImageDraw.Draw(im)
    P=cam.proj(pts)
    for i,(x,y) in enumerate(P):
        d.ellipse([x-r,y-r,x+r,y+r],outline=color,width=2)
        if labels: d.text((x+r+1,y-r),str(labels[i]),fill=color)
    im.save(out); return im

import glob,os
from rbtools import euler_to_R
_mesh={}
def mesh(name):
    if name not in _mesh: _mesh[name]=np.load(f"parts/{name}.npy")
    return _mesh[name]
def part_points(part,step=7):
    V=mesh(part["n"])[::step]
    R=euler_to_R(part.get("r",[0,0,0])); return V@R.T+np.array(part["p"],float)
def draw_parts(panel,cam,parts,out,colors=None,base=None,step=5,alpha=1.0):
    im=Image.open(panel).convert("RGB") if base is None else base
    d=ImageDraw.Draw(im)
    for i,pt in enumerate(parts):
        col=(colors[i] if colors else (255,0,0))
        P=cam.proj(part_points(pt,step))
        for x,y in P:
            if 0<=x<im.width and 0<=y<im.height: d.point((x,y),fill=col)
    im.save(out); return im

import itertools,json
_dims=json.load(open("dims.json",encoding="utf-8"))
def draw_boxes(panel,cam,parts,out,colors=None,base=None,width=2,label=None):
    im=Image.open(panel).convert("RGB") if base is None else base
    d=ImageDraw.Draw(im)
    for i,pt in enumerate(parts):
        ext=np.array(_dims[pt["n"]])/2
        R=euler_to_R(pt.get("r",[0,0,0])); c=np.array(pt["p"],float)
        corners=np.array([[sx*ext[0],sy*ext[1],sz*ext[2]] for sx in(-1,1) for sy in(-1,1) for sz in(-1,1)])
        W=corners@R.T+c
        P=cam.proj(W)
        col=colors[i] if colors else (255,0,0)
        for a,b in itertools.combinations(range(8),2):
            if np.sum(np.abs(corners[a]-corners[b])>1e-6)==1: d.line([tuple(P[a]),tuple(P[b])],fill=col,width=width)
        if label: 
            q=cam.proj([c])[0]; d.text((q[0],q[1]),str(label[i]) if isinstance(label,list) else label,fill=col)
    im.save(out); return im
