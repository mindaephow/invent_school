import subprocess, os, sys
from PIL import Image
def render(step, az, el, dist, out, W=830, H=740):
    q=f"id=cubo-1-trike&step={step}&az={az}&el={el}&dist={dist}&v={os.getpid()}"
    subprocess.run(["C:/Program Files/Google/Chrome/Application/chrome.exe","--headless=new","--disable-gpu","--use-angle=swiftshader","--enable-unsafe-swiftshader","--hide-scrollbars",f"--window-size={W},{H}","--virtual-time-budget=9000",f"--screenshot={os.path.abspath(out)}",f"http://localhost:8765/live2.html?{q}"],capture_output=True)
def pair(step, book, az, el, dist, out):
    render(step, az, el, dist, "_m.png")
    a=Image.open(book).convert("RGB"); b=Image.open("_m.png").convert("RGB")
    h=700; a=a.resize((int(a.width*h/a.height),h)); b=b.resize((int(b.width*h/b.height),h))
    s=Image.new("RGB",(a.width+b.width,h),"white"); s.paste(a,(0,0)); s.paste(b,(a.width,0)); s.save(out)
if __name__=="__main__":
    step,book,az,el,dist,out=sys.argv[1:7]; pair(int(step),book,float(az),float(el),float(dist),out)
