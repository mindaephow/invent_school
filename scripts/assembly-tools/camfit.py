# 교재 그림의 판 모서리 점(3D↔화면 픽셀)으로 카메라를 맞춘다. 사용: from camfit import fitcam; fitcam(obj,img,W,H)
import numpy as np, math, cv2
from pnp import fit, cam_from, angles
def fitcam(obj,img,W,H,target=(60,20,0),fovs=(20,25,30,35,40,45,50)):
    out=None
    for fov in fovs:
        r=fit(obj,img,W,H,fov)
        if not r: continue
        e,rv,tv,K=r; C,fwd,up,right=cam_from(rv,tv); az,el,rad=angles(C,target)
        if out is None or e<out[0]: out=(e,fov,az,el,rad)
    e,fov,az,el,rad=out
    return {"err":round(e,1),"fov":fov,"az":round(az,1),"el":round(el,1),"theta":round(math.radians(az),2),"phi":round(math.radians(90-el),2)}
