import os, tempfile
import json, time, datetime, urllib.request, urllib.parse
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
cats=rest('GET','ivs_robot_categories?select=id,data')
print([c['data'].get('name') for c in cats if c['data'].get('subject')=='robot'][:30])
assert not any(c['data'].get('name')=='공개수업' for c in cats)
row=rest('GET','ivs_textbooks?select=id,data&data->>name=eq.'+urllib.parse.quote('EQ로봇교실1단계'))[0]
ppt=[f for f in row['data']['files'] if f['name'].endswith('.pptx')]
print(len(ppt),[f['name'] for f in ppt])
assert len(ppt)==6
cat=rest('POST','ivs_robot_categories',{'data':{'name':'공개수업','subject':'robot','volumes':1,'createdAt':int(time.time()*1000),'description':'공개수업용 참고자료'}},'return=representation')[0]
tb=rest('POST','ivs_textbooks',{'data':{'name':'EQ로봇 공개수업 참고자료','files':ppt,'volume':1,'subject':'robot','category':cat['id'],'chapters':[],'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')}},'return=representation')[0]
row['data']['files']=[f for f in row['data']['files'] if not f['name'].endswith('.pptx')]
rest('PATCH','ivs_textbooks?id=eq.'+row['id'],{'data':row['data']},'return=minimal')
print('cat',cat['id'],'tb',tb['id'],'eq1 files left',len(row['data']['files']))
