import json,re
def fmt(v):
    return json.dumps(v,ensure_ascii=False,separators=(", ",": "))
def js_part(pt):
    keys=["n","p","r"]
    s="{ "+", ".join(f"{k}: {fmt(pt[k])}" for k in keys)
    for k,v in pt.items():
        if k in keys or k=="tag": continue
        s+=f", {k}: {fmt(v)}"
    return s+" }"
def js_step(st,ind="        "):
    head=f"{{ view: {st['view']}, note: {fmt(st['note'])}, parts: [" if st.get("view") else f"{{ note: {fmt(st['note'])}, parts: ["
    extra=""
    body=("\n"+"\n".join(ind+"  "+js_part(p)+"," for p in st["parts"])+"\n"+ind) if st["parts"] else ""
    return ind+head+body+"] },"
def js_entry(id_,chapter,book,camera,steps):
    out=[ "  {", f"      id: {fmt(id_)},", "      category: '큐보',", "      volume: 1,", f"      chapter: {fmt(chapter)},", f"      book: {fmt(book)},", f"      camera: {fmt(camera)},","      steps: ["]
    out+= [js_step(s) for s in steps]
    out+=["      ],","  }"]
    return "\n".join(out)
