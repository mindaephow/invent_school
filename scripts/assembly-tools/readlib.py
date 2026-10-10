import json, sys
def put(step, **kw):
    p='speedbike_read.json'; r=json.load(open(p,encoding='utf-8')); r[str(step)]=kw
    json.dump(dict(sorted(r.items(), key=lambda kv:int(kv[0]))),open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
