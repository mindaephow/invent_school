import os, tempfile
import json, os, re, sys, time, random, string, urllib.request, urllib.parse
DRY = len(sys.argv) > 1 and sys.argv[1] == 'dry'
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_uncontact'); os.makedirs(OUT, exist_ok=True)
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

PPT = {
 'EQ로봇교실1단계': ('EQ1', 'EQ1', ['부품소개','기린','강아지','고무동력자동차','고무줄총','렙터봇','전자팽이','경찰오토바이','푸시봇','파이터봇','무선조종자동차','스모로봇','축구로봇','라인트레이서','배틀봇']),
 'EQ로봇교실2단계': ('EQ2new', 'EQ2new', ['부품소개','장애물회피로봇','레이싱카','가위봇','골키퍼봇','수퍼버그봇','서보배틀봇','서보모터자동차','골프봇','불도저로봇','볼링봇','폭발물제거로봇','트랩봇']),
 'EQ로봇교실3단계': ('EQ3', 'EQ3', ['부품소개','오프로드자동차','로봇팔','달탐사로봇','센서동작로봇','포터봇','변신자동차로봇','낭떠러지감지로봇','크랩봇','포크레인로봇','스콜피온킹','고무줄대포로봇','자동투석기']),
 'EQ로봇교실4단계': ('EQ4', 'EQ4', ['부품소개','지프봇','3단변신로봇','골프로봇','검도로봇','권투로봇','농구로봇','스윙봇','수퍼레이싱카','드래곤봇','서보탱크로봇','덤프트럭','피처봇']),
}
def dl(fn):
    lp = os.path.join(OUT, fn)
    if os.path.exists(lp): return open(lp, 'rb').read()
    u = BASE + 'H_download.php?filename=' + urllib.parse.quote(fn.encode('euc-kr'), safe='')
    b = urllib.request.urlopen(u, timeout=300).read()
    if b[:2] != b'PK': return None
    open(lp, 'wb').write(b); return b
def up(fn, data):
    name = '%d_%s.pptx' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
    r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=data, method='POST', headers={**H, 'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'})
    urllib.request.urlopen(r, timeout=300).read()
    return f'{url}/storage/v1/object/public/textbook-files/{name}'

norm = lambda s: re.sub(r'\s+', '', s)
for book, (prefix, _, titles) in PPT.items():
    row = rest('GET', 'ivs_textbooks?select=id,data&data->>name=eq.' + urllib.parse.quote(book))[0]
    main = [c for c in row['data']['chapters'] if not c.get('sub')]
    assert len(main) == len(titles), (book, len(main), len(titles))
    added = 0; missing = []
    for i, (c, t) in enumerate(zip(main, titles)):
        if i > 0 and not (norm(t).startswith(norm(c['title'])) or norm(c['title']).startswith(norm(t))):
            print('TITLE MISMATCH', book, i, c['title'], t); continue
        fn = '%s-%02d-%s.pptx' % (prefix, i, t)
        nm = '%02d-%s_수업PPT.pptx' % (i, t)
        if any(f['name'] == nm for f in c['files']): continue
        b = dl(fn)
        if b is None: missing.append(fn); continue
        if not DRY:
            c['files'].append({'url': up(fn, b), 'name': nm})
        added += 1
    if not DRY: rest('PATCH', 'ivs_textbooks?id=eq.' + row['id'], {'data': row['data']}, 'return=minimal')
    print(book, 'added', added, 'missing', missing, flush=True)
