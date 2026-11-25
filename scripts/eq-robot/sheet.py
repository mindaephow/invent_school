import os, tempfile
from PIL import Image,ImageDraw
import sys
pairs=[(1,1,'의자'),(2,2,'책상'),(3,5,'가위'),(4,3,'로봇친구'),(5,13,'강아지'),(6,16,'악어'),(7,19,'화분'),(9,6,'안경'),(11,7,'핸드폰'),(12,8,'카메라'),(14,24,'휠체어'),(15,10,'시소'),(16,34,'교회'),(17,36,'고무줄총'),(18,27,'선풍기'),(19,23,'자전거'),(21,25,'경주용차'),(23,28,'비행기'),(27,30,'돛단배'),(28,29,'헬리콥터'),(30,46,'자동삽'),(32,47,'귀뚜라미로봇')]
W=300;H=420
for s in range(0,len(pairs),4):
    sh=Image.new('RGB',(W*8,H+20),'white');d=ImageDraw.Draw(sh)
    for i,(n,o,nm) in enumerate(pairs[s:s+4]):
        a=Image.open(os.path.join(tempfile.gettempdir(),'eq1808','kids_%02d.gif')%n).convert('RGB');a.thumbnail((W,H))
        b=Image.open(os.path.join(tempfile.gettempdir(),'eqold','old_%02d.jpg')%o).convert('RGB');b.thumbnail((W,H))
        sh.paste(a,(i*2*W,20));sh.paste(b,(i*2*W+W,20))
        d.text((i*2*W+5,3),'%s NEW%d | OLD%d'%(nm.encode('ascii','ignore').decode() or 'p',n,o),fill='red')
    sh.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),'sheet%d.png')%(s//4))
