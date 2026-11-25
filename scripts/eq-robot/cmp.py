import os, tempfile
from PIL import Image
import glob,sys
def h(p):
    im=Image.open(p).convert('L').resize((17,16),Image.LANCZOS); px=list(im.getdata())
    return [1 if px[r*17+c]>px[r*17+c+1] else 0 for r in range(16) for c in range(16)]
new={p[-6:-4]:h(p) for p in glob.glob(os.path.join(tempfile.gettempdir(),'eq1808','kids_*.gif'))}
old={p[-6:-4]:h(p) for p in glob.glob(os.path.join(tempfile.gettempdir(),'eqold','old_*.jpg'))}
for n in sorted(new):
    d=sorted((sum(a!=b for a,b in zip(new[n],o)),k) for k,o in old.items())[:2]
    print(n,d)
