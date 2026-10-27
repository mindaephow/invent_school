# 프로보 테크닉 LV1~7 교재 PDF 에서 ① 권별 키트 부품 목록("프로보 테크닉 LEVELn의 부품을 살펴보아요" 쪽) ② 차시 제목("NN. 이름")과 차시별 "필요한 부품" 을 뽑는다.
#   python -I -X utf8 scripts/extract-techniq.py <출력.json>
import pymupdf, re, json, sys, os
D = r'C:\Users\user\Downloads\테크닉 교재_LV1-LV7'
NAMES = {1: '프로보 테크닉 1권_1판7쇄_워터마크_210209.pdf', 2: '프로보 테크닉 2권_1판6쇄_워터마크_210209.pdf', 3: '프로보 테크닉 3권_1판3쇄_워터마크_210209.pdf', 4: '프로보 테크닉 4권_1판2쇄_워터마크_200429.pdf', 5: '프로보 테크닉 5권_1판2쇄_워터마크_210210.pdf', 6: '프로보 테크닉 6권_1판1쇄_워터마크_210210.pdf', 7: '프로보 테크닉 7권_1판1쇄_워터마크_210210.pdf'}
KIT = {1: [10, 11], 2: [6, 7], 3: [6, 7], 4: [6, 7], 5: [6, 7], 6: [6, 7], 7: [4, 5]}
def toks(t): return [x.strip().replace('\t', ' ') for x in t.replace('\n', '|').split('|') if x.strip()]
def items_of(tk):
    items = []
    for i, t in enumerate(tk):
        if re.match(r'^\d+\s*개$', t):
            if i > 0 and not re.search(r'개$', tk[i - 1]): items.append([re.sub(r'\s+', ' ', tk[i - 1]).strip(), int(re.match(r'^\d+', t).group(0))])
            continue
        for m in re.finditer(r'(.+?)\s*(\d+)\s*개', t): items.append([re.sub(r'\s+', ' ', m.group(1)).strip(), int(m.group(2))])
    return items
out = {}
for v, fn in NAMES.items():
    d = pymupdf.open(os.path.join(D, fn))
    kit = []
    for p in KIT[v]: kit += items_of(toks(d[p - 1].get_text()))
    chs = []
    for i in range(len(d)):
        t = d[i].get_text()
        if '필요한 부품을 알아보아요' not in t: continue
        tk = toks(t)
        title = None
        for x in tk[:6]:
            m = re.match(r'^(\d\d)\.\s*(.+)$', x)
            if m: title = (int(m.group(1)), m.group(2).strip()); break
        chs.append({'page': i + 1, 'no': title[0] if title else None, 'title': title[1] if title else None, 'items': items_of(tk)})
    toc = ' '.join(toks(d[2].get_text()) + toks(d[3].get_text()))
    out[v] = {'kit': kit, 'chapters': chs, 'toc_has_changjak': '창작' in toc}
    print(v, 'kit', len(kit), 'chapters', [(c['no'], c['title'], len(c['items'])) for c in chs], 'toc 창작', '창작' in toc)
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False)
