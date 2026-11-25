import os, tempfile
import json, os, urllib.request, urllib.parse
env={}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'),encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k,v=l.strip().split('=',1); env[k]=v.strip().strip('"')
url=(env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key=env['SUPABASE_SERVICE_ROLE_KEY']
H={'Authorization':'Bearer '+key,'apikey':key}
r=urllib.request.Request(url+'/rest/v1/ivs_textbooks?select=data&data->>name=eq.'+urllib.parse.quote('EQ로봇 기초교육'),headers=H)
row=json.load(urllib.request.urlopen(r))[0]
OUT=os.path.join(os.path.expanduser('~'),'Downloads','eq_basic_edu')
local=sorted(os.path.getsize(os.path.join(OUT,f)) for f in os.listdir(OUT))
bad=0; remote=[]
for c in row['data']['chapters']:
    for f in c['files']:
        b=urllib.request.urlopen(f['url'],timeout=60).read(); remote.append(len(b))
# every remote size must exist among local sizes (shared image counted twice)
loc=list(local);
for s in remote:
    if s in loc: loc.remove(s)
    else: bad+=1
print('remote files',len(remote),'unmatched',bad,'local files',len(local))
