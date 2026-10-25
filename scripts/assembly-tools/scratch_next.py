import json,sys,re
N=int(sys.argv[1]); b=json.load(open('scratch_blocks.json',encoding='utf-8')); s=open('trailer.py',encoding='utf-8').read()
e=s.index("\nimport stepchecks; stepchecks.apply")
mkmap={28:'(AX28, [_XF, _YW, 50.0]), (BU28, [_XF, _YW, 55.5])',29:'(WH29, [_XF, _YW, 55.5]), (BU29, [_XF, _YW, 93.0])',30:'(AX30, [_XF, _YW, -50.0]), (BU30, [_XF, _YW, -55.5])',31:'(WH31, [_XF, _YW, -55.5]), (BU31, [_XF, _YW, -93.0])'}
if N<=31:
    add=b['parts'][str(N)]+'\nfor _q, _m in (%s,):   # 안내 링 = 받는 구멍 입구\n    _q.extra["marks"] = [[round(float(v), 2) for v in _m]]; _q.extra["noMarkCheck"] = True\n'%mkmap[N]
else:
    add=b['b32']
open('trailer.py','w',encoding='utf-8').write(s[:e]+"\n"+add+s[e:])
