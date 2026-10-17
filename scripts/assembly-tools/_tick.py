import cv2,sys
# 사용: python _tick.py <번호> x0 y0 x1 y1 [배율=3] [간격=20]  → scratchpad/tk.png
N,x0,y0,x1,y1=sys.argv[1],*map(int,sys.argv[2:6]); f=int(sys.argv[6]) if len(sys.argv)>6 else 3; g=int(sys.argv[7]) if len(sys.argv)>7 else 20
im=cv2.imread('refs/battlerobot2/%s.jpg'%N); c=im[y0:y1,x0:x1]; c=cv2.resize(c,None,fx=f,fy=f,interpolation=cv2.INTER_CUBIC)
for x in range((x0//g+1)*g,x1,g): k=(x-x0)*f; cv2.line(c,(k,0),(k,c.shape[0]),(0,0,255),1); cv2.putText(c,str(x),(k+2,12),0,0.4,(0,0,255),1)
for y in range((y0//g+1)*g,y1,g): k=(y-y0)*f; cv2.line(c,(0,k),(c.shape[1],k),(255,0,0),1); cv2.putText(c,str(y),(2,k+12),0,0.4,(255,0,0),1)
cv2.imwrite('C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/2642ae62-1c8a-4475-817f-8b0fc23f8fb0/scratchpad/tk.png',c)
