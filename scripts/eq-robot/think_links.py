import os, tempfile
import json, urllib.request
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
url = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key, 'Content-Type': 'application/json'}
def rest(m, p, b=None, pr=None):
    h = dict(H)
    if pr: h['Prefer'] = pr
    r = urllib.request.Request(url + '/rest/v1/' + p, data=json.dumps(b).encode() if b is not None else None, method=m, headers=h)
    raw = urllib.request.urlopen(r, timeout=60).read(); return json.loads(raw) if raw else None
L = {14: 'PZSTC8HOjZg', 17: 'GGdMyNlkQvs', 21: 'HRTaTgUrWlM', 25: 'D9jyEfBIGKE', 29: 'uCYtr-E00kw', 33: 'QC4HVqRXT8E', 37: 'anYDtcYr0KE', 41: 'uorY8FlJqHo', 45: 'Ygw40Assv74'}
row = rest('GET', 'ivs_textbooks?select=id,data&data->>subject=eq.invention')[0]
n = 0
for c in row['data']['chapters']:
    num = int(c['id'].rsplit('_', 1)[1])
    if num in L and not any(f['name'] == '유튜브 링크' for f in c['files']):
        c['files'].append({'url': 'https://youtu.be/' + L[num], 'name': '유튜브 링크'}); n += 1
rest('PATCH', 'ivs_textbooks?id=eq.' + row['id'], {'data': row['data']}, 'return=minimal')
print('added', n)
