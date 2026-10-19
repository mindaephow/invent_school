import json,runpy,numpy as np,cv2,math,itertools,sys
g=runpy.run_path("battlerobot2.py",run_name="probe")
arms={0:g["ARM26"][0],1:g["ARM26"][1]}
def frame(ai,outer):   # 바깥(z35) 프레임
    a=arms[ai]; return (a[0] if ai==1 else a[3]) if outer else (a[3] if ai==1 else a[0])
f=json.load(open('refs/battlerobot2/fits/32_Q.json',encoding='utf-8'))
pts=[(c,r,x,y) for c,r,x,y in f['pts']]
im=cv2.imread('refs/battlerobot2/32.jpg'); H,W=im.shape[:2]
ring=np.array([[462,443],[490,475],[518,510]],float)
res=[]
for ai in (0,1):
 for outer in (1,0):
  F=frame(ai,outer); h=[np.array(F.hole(k)["pos"],float) for k in ("h6","h7","h8")]
  u=(h[2]-h[0])/np.linalg.norm(h[2]-h[0])
  for rf in (0,1):
   for sg in (1,-1):
    for col in (4,6,8,10,12):
     for hov in (60,):
      uu=u*(-1 if rf else 1); ey=np.array([0,0,float(sg)]); ex=np.cross(ey,uu); R=np.stack([ex,ey,uu],axis=1)
      dz=1.0 if outer else -1.0
      zf=float(F.p[2])+(5.0 if outer else -5.0)
      B=np.array([h[0][0],h[0][1],zf+dz*hov])
      def W3(c,r): 
          loc=np.array([(c-col)*10.0,0,(r-4)*10.0]); return B+R@loc
      obj=[];img=[]
      for c,r,x,y in pts: obj.append(W3(c,r)); img.append([x,y])
      o=np.array(obj,np.float64); i=np.array(img,np.float64)
      for fov in (30,40):
        fl=(H/2)/math.tan(math.radians(fov)/2); K=np.array([[fl,0,W/2],[0,fl,H/2],[0,0,1]])
        n,rvs,tvs,_=cv2.solvePnPGeneric(o,i,K,None,flags=cv2.SOLVEPNP_IPPE)
        for rv,tv in zip(rvs,tvs):
          pr,_=cv2.projectPoints(o,rv,tv,K,None); e=np.linalg.norm(pr.reshape(-1,2)-i,axis=1).mean()
          rr,_=cv2.Rodrigues(rv); C=-rr.T@tv.reshape(3); up=-(rr.T@np.array([0,1.0,0]))
          ap=cv2.projectPoints(np.array(h),rv,tv,K,None)[0].reshape(-1,2)
          ea=np.linalg.norm(ap-ring,axis=1).mean()
          res.append((round(float(ea),1),round(float(e),1),ai,outer,rf,sg,col,fov,round(float(up[1]),2),np.round(C).astype(int).tolist()))
res.sort(key=lambda t:t[0])
for r in res[:10]: print(r)
