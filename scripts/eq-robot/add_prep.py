import os, tempfile
import json, urllib.request, urllib.parse
env={}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'),encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k,v=l.strip().split('=',1); env[k]=v.strip().strip('"')
url=(env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key=env['SUPABASE_SERVICE_ROLE_KEY']
H={'Authorization':'Bearer '+key,'apikey':key,'Content-Type':'application/json'}
def rest(m,p,b=None,pr=None):
    h=dict(H); 
    if pr: h['Prefer']=pr
    r=urllib.request.Request(url+'/rest/v1/'+p,data=json.dumps(b).encode() if b is not None else None,method=m,headers=h)
    raw=urllib.request.urlopen(r,timeout=60).read(); return json.loads(raw) if raw else None
names={'EQ로봇 베이직':'eqb','EQ로봇교실1단계':'eq1','EQ로봇교실2단계':'eq2','EQ로봇교실3단계':'eq3','EQ로봇교실4단계':'eq4','EQ로봇교실5단계(몬스터)':'eq5'}
backup={}
for n,c in names.items():
    rows=rest('GET','ivs_textbooks?select=id,data&data->>name=eq.'+urllib.parse.quote(n)); assert len(rows)==1
    row=rows[0]; backup[n]=row
    chs=row['data']['chapters']
    if chs and chs[0].get('title')=='준비': print('skip',n); continue
    chs.insert(0,{'id':'ch_%s_00'%c,'files':[],'parts':[],'title':'준비','fileUrl':None,'fileName':None})
    rest('PATCH','ivs_textbooks?id=eq.'+row['id'],{'data':row['data']},'return=minimal')
    print('ok',n,len(chs))
json.dump(backup,open(os.path.join(os.path.expanduser('~'),'Downloads','eqkids_dl','1808','row_before_prep.json'),'w',encoding='utf-8'),ensure_ascii=False)
