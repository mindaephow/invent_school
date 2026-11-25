import os, tempfile
import json, os, urllib.request, urllib.parse
env = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','.env.local'), encoding='utf-8'):
    if '=' in l and not l.strip().startswith('#'):
        k, v = l.strip().split('=', 1); env[k] = v.strip().strip('"')
url = (env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')).rstrip('/'); key = env['SUPABASE_SERVICE_ROLE_KEY']
H = {'Authorization': 'Bearer ' + key, 'apikey': key}
OUT = os.path.join(os.path.expanduser('~'),'Downloads','eq_uncontact')
local = sorted(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
remote = []
for n in range(1, 5):
    r = urllib.request.Request(url + '/rest/v1/ivs_textbooks?select=data&data->>name=eq.' + urllib.parse.quote('EQ로봇교실%d단계' % n), headers=H)
    row = json.load(urllib.request.urlopen(r))[0]
    for c in row['data']['chapters']:
        for f in c['files']:
            if f['name'].endswith('_수업PPT.pptx'):
                remote.append(len(urllib.request.urlopen(f['url'], timeout=120).read()))
print('local', len(local), 'remote', len(remote), 'sorted equal', sorted(remote) == local)
