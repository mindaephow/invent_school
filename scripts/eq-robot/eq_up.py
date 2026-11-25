import os, tempfile
import json, os, re, sys, time, random, string, datetime, urllib.request, mimetypes
sys.path.insert(0, os.path.dirname(__file__))
M = os.path.join(os.path.dirname(os.path.abspath(__file__)),'eq_manifest')
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_levels')
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
url = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key}
catalog = json.load(open(os.path.join(M, 'catalog.json'), encoding='utf-8'))

def local_of(course, p):
    if p.startswith('H_download'):
        fn = p.split('filename=', 1)[1]
        return os.path.join(OUT, course, 'prog_' + re.sub(r'[\\/:*?"<>|]', '_', fn))
    return os.path.join(OUT, course, p.replace('/', '__'))

CT = {'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'gif': 'image/gif', 'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ufc': 'application/octet-stream'}
cache = {}
def up(course, p):
    lp = local_of(course, p)
    if lp in cache: return cache[lp]
    ext = lp.rsplit('.', 1)[-1].lower()
    name = '%d_%s.%s' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)), ext)
    for attempt in range(3):
        try:
            r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=open(lp, 'rb').read(), method='POST', headers={**H, 'Content-Type': CT.get(ext, 'application/octet-stream')})
            urllib.request.urlopen(r, timeout=300).read()
            break
        except Exception as e:
            if attempt == 2: raise
            time.sleep(2)
    cache[lp] = f'{url}/storage/v1/object/public/textbook-files/{name}'
    return cache[lp]

LABEL = {'img': '이미지', 'pdf': '조립도', 'sc': '과학연계', 'plan': '교육계획안', 'prog': '프로그램', 'ppt': '참고자료', 'doc': '문서'}
def post(table, body):
    r = urllib.request.Request(f'{url}/rest/v1/{table}', data=json.dumps(body).encode(), method='POST', headers={**H, 'Content-Type': 'application/json', 'Prefer': 'return=representation'})
    return json.load(urllib.request.urlopen(r, timeout=60))[0]

PPT_TITLES = ['주제1 부저모듈에서 소리가 나요', '주제2 운동을 방해하는 힘, 마찰력', '주제3 눈에 보이지 않는 빛, 적외선', '주제4 나사에 숨겨진 재미있는 이야기', '주제5 메인보드에 숨겨진 비밀을 찾아라', '주제6 조금 다르게 생각해 보기(비대칭)']
BOOKS = {'eq1': 'EQ로봇교실1단계', 'eq2': 'EQ로봇교실2단계', 'eq3': 'EQ로봇교실3단계', 'eq4': 'EQ로봇교실4단계', 'eq5': 'EQ로봇교실5단계(몬스터)'}

cat = post('ivs_robot_categories', {'data': {'name': 'EQ로봇교실', 'subject': 'robot', 'volumes': 5, 'createdAt': int(time.time() * 1000), 'description': '1~4단계 + 5단계(몬스터)'}})
print('CAT', cat['id'], flush=True)
for vol, course in enumerate(['eq1', 'eq2', 'eq3', 'eq4', 'eq5'], 1):
    chapters = {}
    bookfiles = []
    for e in catalog[course]:
        if e['kind'] == 'book':
            for f in e['files']:
                ext = f['p'].rsplit('.', 1)[-1].split('?')[0]
                if course == 'eq1': nm = PPT_TITLES[int(re.search(r'sub(\d)', f['p']).group(1)) - 1] + '.pptx'
                else: nm = e['name'] + '.' + ('ufc' if f['p'].endswith('.ufc') else ext)
                bookfiles.append({'url': up(course, f['p']), 'name': nm})
            continue
        n = e['n']
        ch = chapters.setdefault(n, {'id': 'ch_%s_%02d' % (course, n), 'files': [], 'parts': [], 'title': None, 'fileUrl': None, 'fileName': None})
        if e['t'] and not ch.get('theme'): ch['theme'] = e['t']
        main = e['kind'] == '교'
        if main: ch['title'] = e['name']
        for f in e['files']:
            ext = f['p'].rsplit('.', 1)[-1].split('?')[0]
            if f['k'] == 'prog': ext = 'ufc'
            nm = ('%02d-%s_%s.%s' % (n, e['name'], LABEL[f['k']], ext)) if main else ('%02d-추가모델-%s_%s.%s' % (n, e['name'], LABEL[f['k']], ext))
            ch['files'].append({'url': up(course, f['p']), 'name': nm})
        print(course, n, e['name'], len(e['files']), flush=True)
    ch_list = [chapters[k] for k in sorted(chapters)]
    for c in ch_list:
        if not c['title']: c['title'] = '%d차시' % int(c['id'][-2:])
    tb = post('ivs_textbooks', {'data': {'name': BOOKS[course], 'files': bookfiles, 'volume': vol, 'subject': 'robot', 'category': cat['id'], 'chapters': ch_list, 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')}})
    print('TB', course, tb['id'], len(ch_list), 'chapters', sum(len(c['files']) for c in ch_list), 'files', len(bookfiles), 'book files', flush=True)
