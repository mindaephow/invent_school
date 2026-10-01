import json,copy
def _shift_pt(p,dy): return [p[0],round(p[1]+dy,3),p[2]]
def shifted(steps,dy):
    S=copy.deepcopy(steps)
    for st in S:
        for pt in st["parts"]:
            pt["p"]=_shift_pt(pt["p"],dy)
            for k in("marks","faceMarks","settleMarks"):
                if k in pt: pt[k]=[_shift_pt(m,dy) for m in pt[k]]
            if "side" in pt: pt["side"]["p"]=_shift_pt(pt["side"]["p"],dy)
            if "explode" in pt:
                e=pt["explode"]
                if "from" in e: e["from"]=_shift_pt(e["from"],dy)
                if "marks" in e: e["marks"]=[_shift_pt(m,dy) for m in e["marks"]]
    return S
def write_viewer(steps,path="viewer/asm.js"):
    open(path,"w",encoding="utf-8").write("window.ASM="+json.dumps({"steps":steps},ensure_ascii=False)+";")
