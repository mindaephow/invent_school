import os, tempfile
import json, os, re, sys, urllib.request, urllib.parse, hashlib
M = os.path.join(os.path.dirname(os.path.abspath(__file__)),'eq_manifest')
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_levels')
BASE = 'http://emsv6.eqrobot.com/community/CEO/cyber2014/'
os.makedirs(OUT, exist_ok=True)

def url_of(p):
    if p.startswith('H_download'):
        head, fn = p.split('filename=', 1)
        return BASE + head + 'filename=' + urllib.parse.quote(fn.encode('euc-kr'), safe='')
    return BASE + urllib.parse.quote(p, safe='/')

def kind_of(p):
    if p.startswith('H_download'): return 'prog' if p.endswith('.ufc') else 'doc'
    if p.endswith('.pdf'): return 'pdf'
    if p.endswith('.pptx'): return 'ppt'
    if 'plan' in p: return 'plan'
    if re.search(r'(-sc-|/sc_|-s\.jpg)', p): return 'sc'
    return 'img'

def local_of(course, p):
    if p.startswith('H_download'):
        fn = p.split('filename=', 1)[1]
        return os.path.join(OUT, course, 'prog_' + re.sub(r'[\\/:*?"<>|]', '_', fn))
    return os.path.join(OUT, course, p.replace('/', '__'))

catalog = {}
want = {}
def add(course, entry):
    for it in entry['files']:
        want[(course, it['p'])] = None
    catalog.setdefault(course, []).append(entry)

for c in (1, 2, 3, 4):
    d = json.load(open(os.path.join(M, 'eq%d.json' % c), encoding='utf-8'))
    prog = json.load(open(os.path.join(M, 'eq3_prog.json'), encoding='utf-8')) if c == 3 else {}
    course = 'eq%d' % c
    for r in d['rows']:
        for it in r['i']:
            kind, name, paths = it[0], it[1], list(it[2:])
            if c == 3:
                pp = prog.get(str(r['n']), {}).get(name)
                if pp: paths.append(pp)
            if c == 4 and kind == '교' and False: pass
            files = [{'p': p, 'k': kind_of(p)} for p in paths]
            if kind == '교' and r.get('plan'):
                files.append({'p': r['plan'], 'k': 'plan'})
            if kind == '교' and c in (1, 2, 3):
                pass
            add(course, {'n': r['n'], 't': r.get('t'), 'kind': kind, 'name': name, 'files': files})
    if c == 1:
        for p in d['ppt']:
            add(course, {'n': 0, 't': '공개수업용 참고자료', 'kind': 'book', 'name': os.path.basename(p), 'files': [{'p': p, 'k': 'ppt'}]})
    if c == 3:
        for p in prog['_book']:
            add(course, {'n': 0, 't': '교재 공통', 'kind': 'book', 'name': 'EQ다운로더 사용설명서', 'files': [{'p': p, 'k': 'doc'}]})

d = json.load(open(os.path.join(M, 'eq5.json'), encoding='utf-8'))
for r in d['rows']:
    for it in r['i']:
        add('eq5', {'n': r['n'], 't': None, 'kind': it[0], 'name': it[1], 'files': [{'p': p, 'k': kind_of(p)} for p in it[2:]]})
for p in d['book']:
    add('eq5', {'n': 0, 't': '교재 공통', 'kind': 'book', 'name': '프로그램(only-program)', 'files': [{'p': p, 'k': 'prog'}]})

def check(path, data):
    ext = path.rsplit('.', 1)[-1].lower()
    if ext == 'pdf' or path.endswith('.pdf'): return data[:4] == b'%PDF'
    if ext == 'jpg': return data[:2] == b'\xff\xd8'
    if ext == 'gif': return data[:3] == b'GIF'
    if ext == 'pptx': return data[:2] == b'PK'
    return len(data) > 20 and data[:5] != b'Canno'

bad, ok, cache = [], 0, {}
for (course, p) in list(want):
    lp = local_of(course, p)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    if not os.path.exists(lp):
        try:
            data = urllib.request.urlopen(url_of(p), timeout=180).read()
            if not check(p if not p.startswith('H_download') else p.split('filename=')[1], data):
                bad.append((course, p, data[:30])); continue
            open(lp, 'wb').write(data)
        except Exception as e:
            bad.append((course, p, str(e)[:80])); continue
    ok += 1
json.dump(catalog, open(os.path.join(M, 'catalog.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('ok', ok, 'bad', len(bad))
for b in bad: print(b)
