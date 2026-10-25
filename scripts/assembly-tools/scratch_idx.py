# usage: python scratch_idx.py N "idx:file:note" ...  (adds/replaces entries in refs/bowling/index.json, step N, sorted)
import sys, json
N=int(sys.argv[1]); p='refs/bowling/index.json'; idx=json.load(open(p,encoding='utf-8'))
for a in sys.argv[2:]:
    k,f,n=a.split(':',2); k=int(k)
    idx=[r for r in idx if not (r['step']==N and r['idx']==k)]
    idx.append({"step":N,"idx":k,"file":f,"note":n})
idx.sort(key=lambda r:(r['step'] if r['step']!=99 else 1000, r['idx']))
json.dump(idx,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
