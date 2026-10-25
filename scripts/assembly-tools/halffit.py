# usage: halffit.py N label cols rows x1 y1 ... x8 y8 [mode]  -> runs holefit on 0.5x copy, writes refs/bowling/fits/NN_label.json (x2) with true px errors
import sys, os, json, subprocess, shutil, cv2, numpy as np
N=int(sys.argv[1]); lab=sys.argv[2]; cols=sys.argv[3]; rows=sys.argv[4]; C=[float(v) for v in sys.argv[5:13]]; mode=sys.argv[13:] 
root="refs/bowling_half"; os.makedirs(root+"/fits",exist_ok=True); os.makedirs(root+"/hf",exist_ok=True)
im=cv2.imread("refs/bowling/%02d.jpg"%N); h=cv2.resize(im,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA); cv2.imwrite(root+"/%02d.jpg"%N,h)
arg=["python","holefit.py","bowling_half",str(N),lab,cols,rows]+["%.1f"%(v/2) for v in C]+mode
r=subprocess.run(arg,capture_output=True,env={**os.environ,"PYTHONIOENCODING":"utf-8"}); out=r.stdout.decode("utf-8","replace")
print("\n".join(l[:150] for l in out.splitlines() if "후보" in l or "통과" in l or "다시" in l))
f=root+"/fits/%02d_%s.json"%(N,lab)
if "✅" in out and os.path.exists(f):
    d=json.load(open(f,encoding="utf-8")); d["pts"]=[[c,r_,round(x*2,2),round(y*2,2)] for c,r_,x,y in d["pts"]]
    d["err_px"]=round(d["err_px"]*2,2); d["max_err_px"]=round(d["max_err_px"]*2,2)
    d["name"]=d["name"].replace("bowling_half","bowling")+" | 책 그림이 클로즈업(구멍 간격 ~100px)이라 0.5배 사본으로 holefit 한 뒤 좌표·오차를 2배로 환산(오차는 실제 px). 사용자 확인 필요"
    d["scale_note"]="0.5x copy"; json.dump(d,open("refs/bowling/fits/%02d_%s.json"%(N,lab),"w",encoding="utf-8"),ensure_ascii=False)
    shutil.copy(root+"/hf/%02d_%s.png"%(N,lab),"refs/bowling/hf/%02d_%s.png"%(N,lab)); print("SAVED true err",d["err_px"],d["max_err_px"])
