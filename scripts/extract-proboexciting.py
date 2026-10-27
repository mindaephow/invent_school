# 프로보 익사이팅 LV1~4 교재 PDF 에서 차례(챕터 제목)와 챕터별 "필요한 부품 리스트"를 뽑는다. 결과 JSON: {vol: {titles:[...], lists:[{page, items:[[이름,수량],...]}]}}
#   python -I -X utf8 scripts/extract-proboexciting.py <출력.json>
import pymupdf, re, json, sys
D = r'C:\Users\user\Downloads'
ALIAS = {'충전 배터리블럭': '충전배터리블럭', '스프링 스위치블럭': '스프링스위치블럭', '모터케이블(2-PIN)': '모터케이블', '터치케이블(1-PIN)': '터치케이블', '적외선블럭(IR)': '적외선블럭', '터치블럭 레드': '터치블럭레드', '터치블럭 블루': '터치블럭블루'}
def norm(n):
    n = n.strip()
    if n in ALIAS: return ALIAS[n]
    k = re.sub(r'\s+', '', n)
    if k in ('레드', '블루'): return 'LED블럭 ' + k
    for a, b in ALIAS.items():
        if re.sub(r'\s+', '', a) == k: return b
    return k
out = {}
for vol in (1, 2, 3, 4):
    d = pymupdf.open(rf'{D}\익사이팅LV{vol}_내지_대화형_(1).pdf')
    toks = []
    for i in (1, 2): toks += [t.strip() for t in d[i].get_text().replace('\n', '|').split('|') if t.strip()]
    ch = sorted((int(m.group(1)), toks[i - 1]) for i, t in enumerate(toks) for m in [re.match(r'^P\s*(\d+)$', t)] if m)
    titles = [t for _, t in ch]
    lists = []
    for i in range(len(d)):
        t = d[i].get_text()
        if '필요한 부품 리스트' not in t: continue
        toks = [x.strip() for x in t.replace('\n', '|').split('|') if x.strip()]
        j = toks.index('필요한 부품 리스트') if '필요한 부품 리스트' in toks else 0
        items = []
        for k, tk in enumerate(toks[j + 1:], j + 1):
            if re.match(r'^\d+\s*개$', tk):
                if k > 0: items.append([norm(toks[k - 1]), int(re.match(r'^(\d+)', tk).group(1))])
                continue
            for m in re.finditer(r'(.+?)\s*(\d+)\s*개', tk): items.append([norm(m.group(1)), int(m.group(2))])
        lists.append({'page': i + 1, 'items': items})
    out[vol] = {'titles': titles, 'lists': lists}
    print(vol, len(titles), 'titles /', len(lists), 'lists', [l['page'] for l in lists])
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False)
names = {}
for v in out.values():
    for l in v['lists']:
        for n, q in l['items']: names[n] = names.get(n, 0) + 1
print(len(names), sorted(names))
