import os, tempfile
import json, re, urllib.request, urllib.parse
env={}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'),encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k,v=l.strip().split('=',1); env[k]=v.strip().strip('"')
url=(env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key=env['SUPABASE_SERVICE_ROLE_KEY']
H={'Authorization':'Bearer '+key,'apikey':key,'Content-Type':'application/json'}
def rest(m,p,b=None,pr=None):
    h=dict(H)
    if pr: h['Prefer']=pr
    r=urllib.request.Request(url+'/rest/v1/'+p,data=json.dumps(b).encode() if b is not None else None,method=m,headers=h)
    raw=urllib.request.urlopen(r,timeout=60).read(); return json.loads(raw) if raw else None
bk={}
for n in ['EQ로봇교실1단계','EQ로봇교실2단계','EQ로봇교실3단계','EQ로봇교실4단계','EQ로봇교실5단계(몬스터)']:
    row=rest('GET','ivs_textbooks?select=id,data&data->>name=eq.'+urllib.parse.quote(n))[0]; bk[n]=row
    out=[]; moved=0
    for c in row['data']['chapters']:
        if any(x.get('sub') for x in [c]): out.append(c); continue
        main=[]; extras={}
        for f in c['files']:
            m=re.match(r'^(\d+)-추가모델-(.+)_(이미지|조립도|과학연계|교육계획안|프로그램|참고자료|문서)\.\w+$', f['name'])
            if m: extras.setdefault(m.group(2),[]).append({'url':f['url'],'name':f['name']})
            else: main.append(f)
        c['files']=main; out.append(c)
        for k,(name,fs) in enumerate(extras.items(),1):
            out.append({'id':'%s_x%d'%(c['id'],k),'title':name+' (추가모델)','sub':True,'parts':[],'files':fs,'fileUrl':None,'fileName':None}); moved+=len(fs)
    row['data']['chapters']=out
    rest('PATCH','ivs_textbooks?id=eq.'+row['id'],{'data':row['data']},'return=minimal')
    print(n,'chapters',len(out),'moved files',moved)
json.dump(bk,open(os.path.join(os.path.expanduser('~'),'Downloads','eqkids_dl','1808','row_before_split.json'),'w',encoding='utf-8'),ensure_ascii=False)
