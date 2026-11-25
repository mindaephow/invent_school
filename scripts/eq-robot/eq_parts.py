import os, tempfile
# EQ로봇 부품 리스트업(이름·단계·수량만, 3D 없음) — 출처: 단계별 부품구성.pdf(EQ로봇교실 1~4단계), EQ베이직 제안서 5쪽, EQ키즈 제안서 6쪽(+뉴EQ키즈 7쪽)
import json, sys, time, urllib.request, urllib.parse
WRITE = '--write' in sys.argv
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

BRICK = {'1단브릭': 4, '2단브릭': 4, '3단브릭': 4, '4단브릭': 4, '5단브릭': 4}
ORANGE = lambda q: {'주황 2칸 프레임': q, '주황 3칸 프레임': q, '주황 5칸 프레임': q, '주황 7칸 프레임': q}
BLUE = lambda q: {'파랑 판(소)': q, '파랑 판(중)': q, '파랑 긴 판(큰 구멍)': q, '파랑 넓은 판': q}
GREEN = lambda q, b: {'초록 4칸 프레임(양끝 돌기)': q, '초록 5칸 프레임(가운데 돌기)': q, '초록 135° 꺾임 프레임': b, '초록 90° 꺾임 프레임': b, '초록 긴홈 프레임': q, '초록 계단 프레임': q}
YELLOW = lambda q: {'노랑 L자 프레임': q, '노랑 꺾임 프레임(짧은)': q, '노랑 꺾임 프레임(긴)': q, '노랑 곡선 프레임': q, '노랑 T자 프레임': q, '노랑 긴홈 프레임': q, '노랑 십자 프레임': q}
AXLE = lambda h, m, l, b1, b2, b3, c, r: {'머리축': h, '50mm축(중)': m, '75mm축(대)': l, '1구부싱': b1, '2구부싱': b2, '3구부싱': b3, '축연결부싱': c, '고무링': r}
BOLTS = {'스페이서(소)': 4, '스페이서(대)': 4, '너트': 10, '볼트(소)': 25, '볼트(대)': 20}
TRACK = {'캐터필러 스프로킷': 2, '캐터필러 롤러': 2, '캐터필러 마디': 34, '캐터필러 고무패드': 34}
CONN = lambda a, b, c, d, e, f, g: {'6면 돌기': a, '4면 돌기': b, '큰 기둥': c, '작은 기둥': d, '기둥연결부': e, '프레임 연결핀': f, '핀빼기 공구': g}
def M(*ds):
    o = {}
    for d in ds: o.update(d)
    return o

EQ = {
 1: M(BRICK, ORANGE(4), BLUE(2), GREEN(2, 10), YELLOW(2), AXLE(8, 6, 2, 20, 4, 4, 2, 5),
      {'작은기어': 2, '풀리': 2, '캠': 4, '큰기어': 2, '중간바퀴': 2}, BOLTS,
      {'DC모터': 2, 'DC모터축': 4, 'IR센서': 2, '드라이버': 1, '스패너': 1, '메인보드(건전지 분리형)': 1, '부품통': 1, '건전지 홀더': 1, '리모컨': 1, '빨강 판 3×3': 2}),
 2: M(BRICK, ORANGE(2), BLUE(1), GREEN(2, 5), YELLOW(1), AXLE(4, 3, 1, 10, 2, 2, 1, 2),
      {'작은기어': 2, '풀리': 2, '큰기어': 2, '큰바퀴': 2},
      {'메인보드(일체형 LCD)': 1, '서보모터': 1, '리모컨수신센서': 1, 'IR센서': 1}),
 3: M(BRICK, ORANGE(2), BLUE(1), GREEN(2, 5), YELLOW(1), AXLE(8, 6, 2, 20, 4, 4, 2, 5),
      {'작은기어': 2, '풀리': 2, '큰기어': 2, '중간바퀴': 2}, TRACK, {'초록 H 연결부품': 4, '초록 힌지 부품': 4}, BOLTS,
      {'서보모터': 1, '터치센서': 2, 'LED모듈': 2, 'USB 케이블': 1}),
 4: M(BRICK, ORANGE(2), BLUE(1), GREEN(2, 5), YELLOW(1), AXLE(4, 3, 1, 10, 2, 2, 1, 2), TRACK, CONN(8, 8, 8, 8, 8, 4, 2),
      {'서보모터': 1, 'DC모터': 2, 'DC모터축': 4, '부저모듈': 1, '빨강 판 3×5': 2, '빨강 반원판': 2}),
}
BASIC = M(BRICK, AXLE(8, 6, 2, 20, 4, 4, 2, 5), {'축(소)': 10},
          {'큰바퀴': 2, '중간바퀴': 2, '큰기어': 2, '작은기어': 2, '풀리': 2, '캠': 4},
          {'유선리모컨': 1, '모터 연결선': 2, 'DC모터': 2, 'DC모터축': 4},
          BLUE(2), GREEN(2, 10), YELLOW(2), ORANGE(4), {'볼트(소)': 20, '볼트(대)': 10, '드라이버': 1, '스패너': 1})
KIDS = M(BRICK, CONN(8, 8, 8, 8, 8, 4, 8), AXLE(8, 6, 2, 20, 4, 4, 2, 5), {'축(소)': 10},
         {'큰바퀴': 2, '중간바퀴': 2, '큰기어': 2, '작은기어': 2, '풀리': 2, '캠': 4},
         {'유선리모컨': 1, '모터 연결선': 2, 'DC모터': 1, 'DC모터축': 2},
         {'빨강 판 3×11': 2, '빨강 판 3×5': 2, '빨강 판 3×3': 2, '빨강 직각삼각판(소)': 4, '빨강 직각삼각판(대)': 4, '빨강 정삼각판': 4,
          '빨강 판 2×9': 2, '빨강 판 2×5': 2, '빨강 판 2×3': 2, '빨강 반원판': 4, '빨강 막대 1×6': 4, '빨강 막대 1×13': 2},
         BLUE(2), GREEN(2, 10), YELLOW(2), ORANGE(4))
KIDS_NEW_ONLY = ['캐터필러 스프로킷', '캐터필러 롤러', '캐터필러 마디', '건전지 박스']   # 뉴EQ키즈 7쪽에만 있음, 수량 표시 없음

print('베이직', len(BASIC), '종', sum(BASIC.values()), '개 (제안서: 49종 202개)')
print('키즈(옛)', len(KIDS), '종', sum(KIDS.values()), '개 + 뉴키즈만', len(KIDS_NEW_ONLY), '종(수량 없음)')
for v in EQ: print('EQ%d단계' % v, len(EQ[v]), '종', sum(EQ[v].values()), '개')
allEQ = sorted({n for v in EQ for n in EQ[v]})
print('EQ로봇교실 전체 종류', len(allEQ))

CATS = {'EQ로봇교실': '3fadbf9d-61d4-4096-8505-959770364929', 'EQ로봇 베이직': '47f37e80-cb5b-4443-b4e0-c88a7b4ec783', 'EQ로봇 키즈': '119a2f68-0948-40ba-a14d-92fe30bd858d'}
rows = []
now = int(time.time() * 1000)
for n in allEQ:
    rows.append({'data': {'name': n, 'icon': '', 'subject': 'robot', 'category': CATS['EQ로봇교실'], 'volumes': [{'volume': v, 'qty': EQ[v][n]} for v in sorted(EQ) if n in EQ[v]], 'color': None, 'size': None, 'createdAt': now}})
for n, q in BASIC.items():
    rows.append({'data': {'name': n, 'icon': '', 'subject': 'robot', 'category': CATS['EQ로봇 베이직'], 'volumes': [{'volume': 1, 'qty': q}], 'color': None, 'size': None, 'createdAt': now}})
for n, q in KIDS.items():
    rows.append({'data': {'name': n, 'icon': '', 'subject': 'robot', 'category': CATS['EQ로봇 키즈'], 'volumes': [{'volume': 1, 'qty': q}], 'color': None, 'size': None, 'createdAt': now}})
for n in KIDS_NEW_ONLY:
    rows.append({'data': {'name': n, 'icon': '', 'subject': 'robot', 'category': CATS['EQ로봇 키즈'], 'volumes': [{'volume': 1, 'qty': None}], 'color': None, 'size': None, 'createdAt': now}})
print('등록할 행', len(rows))
if WRITE:
    for cid in CATS.values():
        have = rest('GET', 'ivs_part_catalog?select=id&data->>category=eq.' + cid)
        assert not have, ('이미 부품 있음', cid, len(have))
    rest('POST', 'ivs_part_catalog', rows, 'return=minimal')
    print('등록 완료')
