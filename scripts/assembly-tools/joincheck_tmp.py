import runpy, numpy as np, json, sys
g=runpy.run_path(sys.argv[1],run_name='probe'); A=g['A']
dims=json.load(open('dims.json',encoding='utf-8'))
def box(p):
    d=np.array(dims[p.n])/2; e=np.abs(np.array(p.R))@d; return np.array(p.p)-e,np.array(p.p)+e
for r in A.parts:
    if r.n!="리벳": continue
    t1=np.array(r.peg("p1")['pos']); t2=np.array(r.peg("p2")['pos']); ax=(t2-t1)/np.linalg.norm(t2-t1)
    def host(pt):
        for p in A.parts:
            if p is r or p.n not in dims: continue
            lo,hi=box(p)
            if np.all(pt>=lo-0.01) and np.all(pt<=hi+0.01): return p
    h1=host(t1-ax*1.0); h2=host(t2+ax*1.0)
    if h1 and h2 and h1 is not h2:
        pr=lambda p:[float(np.dot(np.array([x,y,z]),ax)) for x in(box(p)[0][0],box(p)[1][0]) for y in (box(p)[0][1],box(p)[1][1]) for z in (box(p)[0][2],box(p)[1][2])]
        a=pr(h1); b=pr(h2); gap=max(min(b)-max(a),min(a)-max(b))
        print(r.step.index,r.name,h1.name,h2.name,round(gap,2))
