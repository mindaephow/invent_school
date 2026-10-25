import sys, cv2, numpy as np
N=int(sys.argv[1]); im=cv2.imread('refs/bowling/%02d.jpg'%N); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
h,s,v=cv2.split(hsv)
m=((h>=40)&(h<=90)&(s>=50)&(v>=90)).astype(np.uint8)*255
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
out=[]
for i in range(1,n):
    x,y,w,hh,a=st[i]
    if a>=60: out.append((int(cen[i][0]),int(cen[i][1]),int(w),int(hh),int(a)))
out.sort(key=lambda t:(t[1],t[0]))
for o in out: print(o)
dbg=im.copy()
for o in out: cv2.circle(dbg,(o[0],o[1]),12,(0,0,255),2); cv2.putText(dbg,'%d,%d'%(o[0],o[1]),(o[0]+8,o[1]-8),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,0,0),1)
cv2.imwrite('C:/Users/user/AppData/Local/Temp/rg%02d.jpg'%N,dbg)
