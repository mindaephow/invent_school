import os, tempfile
import json, os, time, random, string, urllib.request, urllib.parse
BASE = 'http://emsv6.eqrobot.com/community/CEO/eqthinking/'
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
url = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key}
def rest(m, p, b=None, pr=None):
    h = {**H, 'Content-Type': 'application/json'}
    if pr: h['Prefer'] = pr
    r = urllib.request.Request(url + '/rest/v1/' + p, data=json.dumps(b).encode() if b is not None else None, method=m, headers=h)
    raw = urllib.request.urlopen(r, timeout=60).read(); return json.loads(raw) if raw else None
fn = '동영상강좌다운로드.pdf'
b = urllib.request.urlopen(BASE + 'H_download_thinking.php?filename=' + urllib.parse.quote(fn.encode('euc-kr'), safe=''), timeout=300).read()
assert b[:4] == b'%PDF', b[:20]
name = '%d_%s.pdf' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=b, method='POST', headers={**H, 'Content-Type': 'application/pdf'})
urllib.request.urlopen(r, timeout=300).read()
u = f'{url}/storage/v1/object/public/textbook-files/{name}'
assert len(urllib.request.urlopen(u, timeout=120).read()) == len(b)
row = rest('GET', 'ivs_textbooks?select=id,data&data->>subject=eq.invention')[0]
if not any(f['name'] == fn for f in row['data']['files']): row['data']['files'].append({'url': u, 'name': fn})
rest('PATCH', 'ivs_textbooks?id=eq.' + row['id'], {'data': row['data']}, 'return=minimal')
print(len(b), [f['name'] for f in row['data']['files']])
open(os.path.join(tempfile.gettempdir(),'think_video.pdf'), 'wb').write(b)
