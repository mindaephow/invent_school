import os, tempfile
import json, os, time, random, string, datetime, urllib.request, urllib.parse
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_thinking'); os.makedirs(OUT, exist_ok=True)
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
R = """군대 숟가락|트리즈 - 더하기 기법
맨홀 뚜껑은 왜 동그란 모양일까?|트리즈 - 곡선화 기법
주사 맞는 것이 싫어요|트리즈 - 사전반대조치
주방에서 일하시는 엄마를 도와주세요|제품디자인
한국, 중국, 일본의 젓가락|디자인씽킹
나누면 편리해지는 것들을 찾아보아요|트리즈 - 분할기법
태풍에도 떨어지지 않는 사과 팔기|트리즈 - 해로운것을 이롭게
주전자 뚜껑 구멍의 비밀|트리즈 - 사전반대조치
시키지 않아도 잘 따라해요|넛지디자인
바람부는 날에도 끄떡없는 우산|트리즈 - 비대칭 기법
식판을 바꾸어 보세요!|제품디자인
회전문을 달면 어떤 점이 좋을까요?|트리즈 - 곡선화 기법
야쿠르트, 혹시 얼려 먹으세요?|제품디자인
짜장면 비닐랩 벗기기|제품디자인
건물이 부식되는 이유를 찾아라!|트리즈 - 5 whys 기법
화장실에 휴지가 걸려있어요|트리즈 - 사전조치
[학생발명] 편하고 맛있게 음료수 먹기|학생발명 사례분석
쇼핑카트들이 포개져 있어요.|트리즈 - 포개기 기법
엘리베이터에서 기다리는 시간 줄이기|트리즈 - 분리 기법
미끄러지지 않으면서 편안한 장갑|트리즈 - 국소적 품질
[학생발명] 우리 반 청소도구 바꾸기|학생발명 사례분석
밝은 빛 때문에 잠을 못자요 !|트리즈 - 추출 기법
X-레이에서 나오는 광선은 위험해요.|트리즈 - 추출 기법
낮잠용 베게를 만들어요.|트리즈 - 국소적 품질 기법
[학생발명] 화분에 꽃을 키워요|학생발명 사례분석
한 겨울, 푸른 색 묘지의 비밀|디자인씽킹
[생각꺼내기 게임] 패트병|브레인스토밍
프랑스 축구선수 '지단'의 발길질|트리즈 - 해로운것을 이롭게 기법
[학생발명] 필기도구 보관함|학생발명 사례분석
에스컬레이터에선 쇼핑카트가 안움직여요|트리즈 - 차원변화 기법
메인보드에 숨겨진 비밀 찾기|트리즈 - 사전조치 기법
비 온 뒤에도 앉은 수 있는 의자|제품디자인
[힉생발명] 컵라면 용기에 변화를 !|학생발명 사례분석
어떤 친구의 몸집이 더 클까요?|과학의 원리
[생각꺼내기 게임] 상상속의 알람시계|브레인스토밍
[재미있는 상상] 다이어트에 좋은 허리띠|트리즈 - 더하기 기법
[학생발명] 갖고 싶은 책상 만들기|학생발명 사례분석
사용하기 편리한 약병 만들기|디자인씽킹
어느 선풍기 바람이 더 쎌까요?|트리즈 - 분할 기법
십자 나사못이 엄청난 발명품이라고요?|트리즈 - 분할 기법
[학생발명] 옷걸이에 변화를 !|학생발명 사례분석
[생각꺼내기 게임] 상상속의 돼지저금통|브레인스토밍
눈 감고 미로 탈출하기|과학의 원리
거꾸로 생각해 보기|트리즈 - 가꾸로 기법
[학생발명] 의자에 변화를 !|학생발명 사례분석
안전하게 건널 수 있는 신호등|제품디자인
불편한 것 찾아보기|마무리 과제
불편한 것 개선하기|마무리 과제""".split('\n')
assert len(R) == 48
def get(u):
    b = urllib.request.urlopen(u, timeout=300).read()
    assert b[:4] == b'%PDF', (u, b[:20]); return b
def up(b):
    name = '%d_%s.pdf' % (int(time.time() * 1000), ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)))
    r = urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}', data=b, method='POST', headers={**H, 'Content-Type': 'application/pdf'})
    urllib.request.urlopen(r, timeout=300).read()
    u = f'{url}/storage/v1/object/public/textbook-files/{name}'
    assert len(urllib.request.urlopen(u, timeout=120).read()) == len(b); return u
chs = [{'id': 'ch_think_00', 'title': '준비', 'parts': [], 'files': [], 'fileUrl': None, 'fileName': None}]
for n, line in enumerate(R, 1):
    t, th = line.split('|')
    b = get(BASE + 'contents/EQ_thinking_%02d.pdf' % n); open(os.path.join(OUT, 'EQ_thinking_%02d.pdf' % n), 'wb').write(b)
    chs.append({'id': 'ch_think_%02d' % n, 'title': t, 'theme': th, 'parts': [], 'files': [{'url': up(b), 'name': '%02d-%s.pdf' % (n, t.replace('/', '_').replace('?', ''))}], 'fileUrl': None, 'fileName': None})
sub = get(BASE + 'H_download_thinking.php?filename=' + urllib.parse.quote('제출용자료다운로드.pdf'.encode('euc-kr'), safe=''))
open(os.path.join(OUT, 'submit.pdf'), 'wb').write(sub)
tb = rest('POST', 'ivs_textbooks', {'data': {'name': 'EQ씽킹 (로봇교육에 발명교육 더하기)', 'files': [{'url': up(sub), 'name': '제출용자료다운로드.pdf'}], 'volume': 1, 'subject': 'invention', 'category': None, 'chapters': chs, 'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')}}, 'return=representation')[0]
print('TB', tb['id'], len(chs), 'chapters; pdf sizes KB', sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) // 1024)
