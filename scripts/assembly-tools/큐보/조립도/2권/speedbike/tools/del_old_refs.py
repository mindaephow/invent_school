import os, tempfile
import json, urllib.request
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),*(['..']*7),'.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
U = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key, 'Content-Type': 'application/json'}
def req(m, p, b=None):
    r = urllib.request.Request(U + p, data=json.dumps(b).encode() if b is not None else None, method=m, headers=H)
    raw = urllib.request.urlopen(r, timeout=60).read(); return json.loads(raw) if raw else None
paths = ['cubo-2-speedbike/%d_%d.jpg' % (s, i) for s in range(34, 38) for i in (1, 2)]
print('storage', len(req('DELETE', '/storage/v1/object/assembly-refs', {'prefixes': paths}) or []))
q = '/rest/v1/ivs_assembly_refs?assembly_id=eq.cubo-2-speedbike&step=gte.34&step=lte.37&idx=in.(1,2)'
H['Prefer'] = 'return=representation'
print('rows', len(req('DELETE', q)))
