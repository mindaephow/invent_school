import os, tempfile
import json, os, time, random, string, datetime, urllib.request, urllib.parse
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_old2'); os.makedirs(OUT, exist_ok=True)
BASE = 'http://emsv6.eqrobot.com/community/CEO/uncontact/'
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
titles = ['부품소개','레이싱카','수퍼버그봇','장애물회피로봇','가위봇','롤러봇','배틀로봇','험로탐색로봇','폭발물제거로봇','불도저로봇','하키로봇','트랩봇','대전차포지프']
data = []
for i, t in enumerate(titles):
    fn = 'EQ2-%02d-%s.pptx' % (i, t)
    b = urllib.request.urlopen(BASE + 'H_download.php?filename=' + urllib.parse.quote(fn.encode('euc-kr'), safe=''), timeout=300).read()
    assert b[:2] == b'PK', fn
    open(os.path.join(OUT, fn), 'wb').write(b); data.append(b)
chs = []
sizes = []
for i, (t, b) in enumerate(zip(titles, data)):
    name = '%d_%s.pptx' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
    r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=b, method='POST', headers={**H, 'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'})
    urllib.request.urlopen(r, timeout=300).read()
    u = f'{url}/storage/v1/object/public/textbook-files/{name}'
    assert len(urllib.request.urlopen(u, timeout=120).read()) == len(b)
    chs.append({'id': 'ch_eq2old_%02d' % i, 'title': '준비' if i == 0 else t, 'parts': [], 'files': [{'url': u, 'name': '%02d-%s_수업PPT.pptx' % (i, t)}], 'fileUrl': None, 'fileName': None})
cat = [c for c in rest('GET', 'ivs_robot_categories?select=id,data') if c['data'].get('name') == 'EQ로봇교실'][0]
tb = rest('POST', 'ivs_textbooks', {'data': {'name': 'EQ로봇교실2단계(구)', 'files': [], 'volume': 6, 'subject': 'robot', 'category': cat['id'], 'chapters': chs, 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')}}, 'return=representation')[0]
print('TB', tb['id'], len(chs), 'chapters; all uploads size-verified')
