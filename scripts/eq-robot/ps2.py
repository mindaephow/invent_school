import os, tempfile
import pymupdf
from PIL import Image,ImageDraw
pairs=[(3,5,'scissors'),(11,7,'phone'),(26,31,'tower')]
def pg(path,i):
    d=pymupdf.open(path); p=d[min(i,len(d)-1)]
    pm=p.get_pixmap(matrix=pymupdf.Matrix(0.8,0.8)); return Image.frombytes('RGB',(pm.width,pm.height),pm.samples),len(d)
ims=[]
for n,o,nm in pairs:
    a,na=pg('1808/%02d.pdf'%n,2); b,nb=pg('%dstep.pdf'%o,2); ims.append((a,b,nm,na,nb))
W=ims[0][0].width;H=ims[0][0].height
sh=Image.new('RGB',(W*2,(H+16)*3),'white');d=ImageDraw.Draw(sh)
for k,(a,b,nm,na,nb) in enumerate(ims):
    sh.paste(a,(0,k*(H+16)+16));sh.paste(b.resize((W,H)),(W,k*(H+16)+16))
    d.text((4,k*(H+16)+2),'%s NEW pages=%d'%(nm,na),fill='red');d.text((W+4,k*(H+16)+2),'OLD pages=%d'%nb,fill='red')
sh.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),'pdfsheet2.png'))
