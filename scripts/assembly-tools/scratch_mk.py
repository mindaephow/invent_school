import json, numpy as np, cv2, subprocess
def mk(N,th,ph,pts,desc):
    fwd=np.array([-np.sin(th)*np.sin(ph),-np.cos(ph),-np.cos(th)*np.sin(ph)]); right=np.cross(fwd,[0,1.,0]); right/=np.linalg.norm(right); up=np.cross(right,fwd)
    gl={k:[float(v@right),float(-(v@up))] for k,v in (("X",np.array([1.,0,0])),("Y",np.array([0,1.,0])),("Z",np.array([0,0,1.])))}
    sc=55.0/max(abs(x) for v in gl.values() for x in v); gl={k:[round(x*sc,1) for x in v] for k,v in gl.items()}
    json.dump({"global":gl,"fit":{"from":desc,"err_px":0.0,"points":len(pts),"theta":th,"phi":ph,"cols":"+X","rows":"+Y"}},open('refs/trailer/%02d_axes.json'%N,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    im=cv2.imread('refs/trailer/%02d.jpg'%N); H,W=im.shape[:2]
    json.dump({"M":[[1,0,0],[0,1,0]],"size":[W,H],"angle":0.0,"crop":[0,0,W,H],"erase":[]},open('refs/trailer/%02d_lv.json'%N,'w'))
    json.dump({"cols":len(pts),"rows":1,"pts":[[i+1,1,float(x),float(y)] for i,(x,y) in enumerate(pts)],"est":[],"name":"trailer %d번 P: %s"%(N,desc),"tool":"ring-read","err_px":0.0,"max_err_px":0.0,"found":len(pts),"found_ratio":1.0,"mode":"링 읽음"},open('refs/trailer/fits/%02d_P.json'%N,'w',encoding='utf-8'),ensure_ascii=False)
    subprocess.run(["python","refs_rect.py","trailer",str(N)],capture_output=True)
def texts(N,d,v,idx,rd,via,notes):
    d[str(N)]=rd; v[str(N)]=via
    idx[:]=[r for r in idx if not (r['step']==N and r['idx'] in notes)]
    pos=[j for j,r in enumerate(idx) if r['step']==N]; pos=(pos[0]+1) if pos else [j for j,r in enumerate(idx) if r['step']==N+1][0]
    for k in sorted(notes,reverse=True): idx.insert(pos,{"step":N,"idx":k,"file":"%02d_%d.jpg"%(N,k),"note":notes[k]})
