import os, tempfile
import json, os, re, time, random, string, datetime, urllib.request
OUT=os.path.join(os.path.expanduser('~'),'Downloads','eq_basic_edu'); os.makedirs(OUT,exist_ok=True)
SITE='http://emsv6.eqrobot.com'
env={}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'),encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k,v=l.strip().split('=',1); env[k]=v.strip().strip('"')
url=(env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key=env['SUPABASE_SERVICE_ROLE_KEY']
H={'Authorization':'Bearer '+key,'apikey':key}
I='/community/images/img_ceo/'
L=[ # (section, title, [images])
('로봇교육','로봇교육의 의미와 필요성',['a-2.gif']),('로봇교육','EQ로봇교실로 배울수 있는 것들',['a-3.gif']),
('로봇교육','로봇의 정의와 이해',['c-1.gif']),('로봇교육','로봇과 관련된 최초의 기록들',['c-2.gif']),('로봇교육','국가별 로봇산업의 수준 비교',['c-3.gif']),
('로봇교육','산업현장에서의 로봇활용',['c-4.jpg']),('로봇교육','의료분야에서의 로봇활용',['c-5.jpg']),('로봇교육','우주분야에서의 로봇활용',['c-6.gif']),
('로봇교육','군사용 로봇개발 및 활용',['c-7.gif']),('로봇교육','사이보그, 휴머노이드, 안드로이드',['c-8.jpg']),('로봇교육','이족로봇의 의미와 개발이유',['c-9.jpg']),
('로봇교육','휴머노이드로봇의 해외기술동향',['c-10.jpg']),('로봇교육','휴머노이드로봇의 국내기술동향',['c-11.jpg']),
('로봇의 구성요소','로봇의 구성요소',['e-1.jpg']),('로봇의 구성요소','마이크로프로세서란?',['e-2.jpg']),('로봇의 구성요소','센서의 역할과 종류',['e-3.jpg']),
('로봇의 구성요소','적외선센서',['e-4.jpg']),('로봇의 구성요소','소리센서',['e-5.jpg']),('로봇의 구성요소','모터, 서보모터',['e-7.jpg']),
('로봇의 구성요소','기어',['e-8_01_1.gif','e-8_01_2.jpg','e-8_01_3.gif','gear1.gif','e-8_02.jpg','gear2.gif','e-8_03.jpg','d-3_03.gif']),
('로봇의 구성요소','건전지',['e-9.jpg']),('로봇의 구성요소','라인트레이서의 원리',['d-2_01.gif','d-2_02.gif']),
('로봇의 구성요소','어보이더의 원리',['d-3_01.gif','avoider.gif','d-3_02.gif','d-3_03.gif']),('로봇의 구성요소','메인보드 살펴보기',['d-4.jpg']),('로봇의 구성요소','리모콘 살펴보기',['d-4-1.jpg']),
('재미있는 전기이야기','지레와 도르레',['f-1.jpg']),('재미있는 전기이야기','도체와 부도체',['f-2.jpg']),('재미있는 전기이야기','전기의 역사',['f-3.gif']),
('재미있는 전기이야기','재미있는 전기이야기',['f-4.gif']),('재미있는 전기이야기','전류와 전압',['f-5.gif']),('재미있는 전기이야기','전자부품 이야기',['f-6.gif']),
('초등학교 강의','초등학교 강의에 필요한 규정',['b-1.gif']),('초등학교 강의','참관수업 진행하기',['b-2.gif']),('초등학교 강의','수업계획 세우기',['b-3.gif']),
('초등학교 강의','칭찬하기와 꾸중하기',['b-4.gif']),('초등학교 강의','학생 생활지도',['b-5.gif']),('초등학교 강의','학생안전지도',['b-6.gif']),('초등학교 강의','주의집중을 위한 놀이',['b-7.gif'])]
MAGIC={'gif':b'GIF','jpg':b'\xff\xd8'}
data={}
for sec,t,imgs in L:
    for im in imgs:
        if im in data: continue
        b=urllib.request.urlopen(SITE+I+im,timeout=60).read()
        ext=im.rsplit('.',1)[1]; assert b[:len(MAGIC[ext])]==MAGIC[ext],(im,b[:10])
        open(os.path.join(OUT,im),'wb').write(b); data[im]=b
print('downloaded',len(data),'files',sum(len(b) for b in data.values())//1024,'KB')
CT={'gif':'image/gif','jpg':'image/jpeg'}; cache={}
def up(im):
    if im in cache: return cache[im]
    ext=im.rsplit('.',1)[1]; name='%d_%s.%s'%(int(time.time()*1000),''.join(random.choices(string.ascii_lowercase+string.digits,k=6)),ext)
    r=urllib.request.Request(f'{url}/storage/v1/object/textbook-files/{name}',data=data[im],method='POST',headers={**H,'Content-Type':CT[ext]})
    urllib.request.urlopen(r,timeout=120).read(); cache[im]=f'{url}/storage/v1/object/public/textbook-files/{name}'; return cache[im]
def rest(m,p,b=None,pr=None):
    h={**H,'Content-Type':'application/json'}
    if pr: h['Prefer']=pr
    r=urllib.request.Request(url+'/rest/v1/'+p,data=json.dumps(b).encode() if b is not None else None,method=m,headers=h)
    raw=urllib.request.urlopen(r,timeout=60).read(); return json.loads(raw) if raw else None
chs=[{'id':'ch_edu_00','title':'준비','parts':[],'files':[],'fileUrl':None,'fileName':None}]
for n,(sec,t,imgs) in enumerate(L,1):
    fs=[]
    for k,im in enumerate(imgs,1):
        ext=im.rsplit('.',1)[1]; fs.append({'url':up(im),'name':'%02d-%s_%s.%s'%(n,t,'이미지' if len(imgs)==1 else '이미지%d'%k,ext)})
    chs.append({'id':'ch_edu_%02d'%n,'title':t,'theme':sec,'parts':[],'files':fs,'fileUrl':None,'fileName':None})
cat=[c for c in rest('GET','ivs_robot_categories?select=id,data') if c['data'].get('name')=='공개수업'][0]
tb=rest('POST','ivs_textbooks',{'data':{'name':'EQ로봇 기초교육','files':[],'volume':2,'subject':'robot','category':cat['id'],'chapters':chs,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')}},'return=representation')[0]
print('TB',tb['id'],len(chs),'chapters',sum(len(c['files']) for c in chs),'files')
