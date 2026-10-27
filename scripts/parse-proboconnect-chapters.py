# extract-proboconnect-chapters.py 의 JSON → 차시별 [이름, 수량] 목록(JSON). 부품 이름은 공백을 정리해 부품 DB 이름으로 맞춘다.
#   python -I -X utf8 scripts/parse-proboconnect-chapters.py <ch.json> <parsed.json>
import json, re, sys
ALIAS = {'RF수신보드': 'RF 수신모듈', 'RF수신커버': 'RF 수신모듈커버', '리모컨': 'RF 리모컨', '고무줄레드': '고무줄 레드', 'LED블럭레드': 'LED블럭 레드', 'LED블럭블루': 'LED블럭 블루', '충전배터리블럭': '충전배터리블럭', '스프링스위치블럭': '스프링스위치블럭', '캐터타이어': '캐터고무', '고무줄': '고무줄', '스티로폼공': '스티로폼 공'}
def norm(n):
    n = re.sub(r'\s+', '', n)
    return ALIAS.get(n, n)
data = json.load(open(sys.argv[1], encoding='utf-8')); out = {}; unknown = {}
for vol, chs in data.items():
    out[vol] = []
    for c in chs:
        toks = [t.strip() for t in c['text'].replace('\n', '|').split('|') if t.strip()]
        items = []
        def fix(n, prev):
            k = re.sub(r'\s+', '', n)
            if k in ('레드', '블루'): return 'LED블럭 ' + k # "LED블럭 | 블루 2개" 처럼 쪼개진 이름
            if k == '블럭' and prev.endswith('스페이서'): return '스페이서블럭'
            if k == '공': return '스티로폼 공'
            if k == '캐터블럭': return '캐터필러'
            return norm(n)
        for i, t in enumerate(toks):
            ms = list(re.finditer(r'(.+?)\s*(\d+)\s*개', t))
            if ms and not re.match(r'^\d+\s*개$', t):
                for m in ms: items.append((fix(m.group(1), toks[i - 1] if i else ''), int(m.group(2))))
                continue
            m = re.match(r'^(\d+)\s*개$', t)
            if m and i > 0: items.append((fix(toks[i - 1], toks[i - 2] if i > 1 else ''), int(m.group(1))))
        out[vol].append({'page': c['page'], 'items': items})
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
names = {}
for vol in out:
    for c in out[vol]:
        for n, q in c['items']: names[n] = names.get(n, 0) + 1
print(len(names), sorted(names.items(), key=lambda x: x[0]))
