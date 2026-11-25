import os, tempfile
import json, os, re, time, random, string, urllib.request, urllib.parse
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_extra')
os.makedirs(OUT, exist_ok=True)
BASE = 'http://emsv6.eqrobot.com/community/CEO/cyber2014/'
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
url = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key}

def dl(php, fn):
    u = BASE + php + '?filename=' + urllib.parse.quote(fn.encode('euc-kr'), safe='')
    b = urllib.request.urlopen(u, timeout=300).read()
    ext = fn.rsplit('.', 1)[-1]
    assert (ext == 'pdf' and b[:4] == b'%PDF') or (ext == 'zip' and b[:2] == b'PK') or (ext == 'ufc' and len(b) > 20 and b[:5] != b'Canno'), (fn, b[:20])
    open(os.path.join(OUT, fn), 'wb').write(b)
    return b

CT = {'pdf': 'application/pdf', 'zip': 'application/zip', 'ufc': 'application/octet-stream'}
def up(fn, data):
    ext = fn.rsplit('.', 1)[-1]
    name = '%d_%s.%s' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)), ext)
    r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=data, method='POST', headers={**H, 'Content-Type': CT[ext]})
    urllib.request.urlopen(r, timeout=300).read()
    return f'{url}/storage/v1/object/public/textbook-files/{name}'

def rest(method, path, body=None, prefer=None):
    h = {**H, 'Content-Type': 'application/json'}
    if prefer: h['Prefer'] = prefer
    r = urllib.request.Request(url + '/rest/v1/' + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers=h)
    raw = urllib.request.urlopen(r, timeout=60).read()
    return json.loads(raw) if raw else None

common_names = ['단계별부품구성.pdf', 'EQ로봇-교육제안서.pdf', '년간교육계획서.zip', '차시별교육계획안_21년.zip']
display = {'단계별부품구성.pdf': '단계별 부품구성.pdf', 'EQ로봇-교육제안서.pdf': 'EQ로봇 교육제안서.pdf', '년간교육계획서.zip': '년간교육계획서.zip', '차시별교육계획안_21년.zip': '차시별교육계획안_21년.zip'}
common = []
for fn in common_names:
    b = dl('H_download_2105.php', fn)
    common.append({'url': up(fn, b), 'name': display[fn], 'size': len(b)})
    print('common', fn, len(b), flush=True)
basic_b = dl('H_download_eqbasic.php', 'EQ베이직_24모델_교육제안서.pdf')
basic = {'url': up('x.pdf', basic_b), 'name': 'EQ베이직_24모델_교육제안서.pdf'}
ufc_b = dl('H_download.php', '폭발물제거로봇.ufc')
ufc = {'url': up('x.ufc', ufc_b), 'name': '10-추가모델-폭발물 제거로봇(캐터필러형)_프로그램.ufc'}
print('basic', len(basic_b), 'ufc', len(ufc_b), flush=True)

def get(name):
    rows = rest('GET', 'ivs_textbooks?select=id,data&data->>name=eq.' + urllib.parse.quote(name))
    assert len(rows) == 1, (name, len(rows))
    return rows[0]
def put(row):
    rest('PATCH', 'ivs_textbooks?id=eq.' + row['id'], {'data': row['data']}, 'return=minimal')

for n in range(1, 5):
    row = get('EQ로봇교실%d단계' % n)
    have = {f['name'] for f in row['data']['files']}
    for f in common:
        if f['name'] not in have:
            row['data']['files'].append({'url': f['url'], 'name': f['name']})
    if n == 4:
        ch = [c for c in row['data']['chapters'] if c['id'] == 'ch_eq4_10'][0]
        if not any(x['name'] == ufc['name'] for x in ch['files']): ch['files'].append(ufc)
    put(row); print('patched eq', n, len(row['data']['files']), flush=True)
row = get('EQ로봇 베이직')
if not any(f['name'] == basic['name'] for f in row['data']['files']): row['data']['files'].append(basic)
put(row); print('patched basic', len(row['data']['files']))
