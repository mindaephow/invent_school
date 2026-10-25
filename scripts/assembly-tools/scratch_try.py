import subprocess, sys, re, os
sh=sys.argv[1]
s=open('trailer.py',encoding='utf-8').read()
s2=re.sub(r'(_GB17, _RF17, pivot=tuple\(_PV17\), shift=)\([^)]*\)',r'\1(%s)'%sh,s)
open('trailer.py','w',encoding='utf-8').write(s2)
subprocess.run(['git','checkout','--','trailer_links.json'])
out=subprocess.run([sys.executable,'build.py','trailer'],capture_output=True,text=True,encoding='utf-8').stdout
print(sh,[l for l in out.splitlines() if l.startswith('단계별 정밀') or l.startswith('안내 화살표 없는') or '바닥 기준' in l])
subprocess.run(['git','checkout','--','trailer_links.json'])
steps=[str(i) for i in range(1,17)]
t=subprocess.run([sys.executable,'_mates_table.py','trailer','17']+steps,capture_output=True,text=True,encoding='utf-8').stdout
n=0
for l in t.splitlines():
    if '⚠' in l and '옆' in l:
        m=re.search(r'깊이 (-?[\d.]+)',l)
        if m and abs(float(m.group(1)))>8: continue
        n+=1
print("  ⚠옆 줄",n)
subprocess.run(['git','checkout','--','trailer_links.json'])
