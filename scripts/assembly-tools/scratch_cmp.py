import runpy, numpy as np, json, sys, os
out={}
for nm in sys.argv[1:]:
    try:
        A=runpy.run_path(nm+'.py',run_name='probe')['A']
        out[nm]=[[p.name,np.array(p.p).tolist()] for p in A.parts]
    except BaseException as e: out[nm]=str(e)[:80]
json.dump(out,open(os.environ['OUTF'],'w'))
