# 책 그림 한 장을 픽셀 눈금과 함께 저장해 모서리·구멍 좌표를 읽는다: python _gridview.py <이름> <번호> [x0 y0 x1 y1 [배율]]
import sys,cv2
n,s=sys.argv[1],int(sys.argv[2]); im=cv2.imread("refs/%s/%02d.jpg"%(n,s)); H,W=im.shape[:2]
x0,y0,x1,y1=[int(v) for v in sys.argv[3:7]] if len(sys.argv)>6 else (0,0,W,H); z=float(sys.argv[7]) if len(sys.argv)>7 else 1.0
a=cv2.resize(im[y0:y1,x0:x1],None,fx=z,fy=z,interpolation=cv2.INTER_CUBIC); st=50 if z<2 else 20
for x in range((x0//st+1)*st,x1,st): X=int((x-x0)*z); cv2.line(a,(X,0),(X,a.shape[0]),(0,0,255),1); cv2.putText(a,str(x),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,0,0),1)
for y in range((y0//st+1)*st,y1,st): Y=int((y-y0)*z); cv2.line(a,(0,Y),(a.shape[1],Y),(0,0,255),1); cv2.putText(a,str(y),(2,Y-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,0,0),1)
cv2.imwrite(r"C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/2642ae62-1c8a-4475-817f-8b0fc23f8fb0/scratchpad/gv.png",a); print("ok")
