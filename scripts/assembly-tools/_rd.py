# 읽기 표 한 번호를 넣는 도우미: python _rd.py <이름> <번호> <json파일>
import json,sys
n,s,f=sys.argv[1],sys.argv[2],sys.argv[3]
p=n+"_read.json"
try: r=json.load(open(p,encoding="utf-8"))
except Exception: r={}
r[s]=json.load(open(f,encoding="utf-8")); json.dump(r,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=1); print("ok",s)
