import os,json,urllib.request,sys
sys.stdout.reconfigure(encoding='utf-8')
env=dict(l.strip().split('=',1) for l in open('../../.env.local',encoding='utf-8') if '=' in l and not l.startswith('#'))
U=env['SUPABASE_URL']; K=env['SUPABASE_SERVICE_ROLE_KEY']
def get(t,q):
    r=urllib.request.Request(U+'/rest/v1/'+t+'?'+q,headers={'apikey':K,'Authorization':'Bearer '+K}); return json.load(urllib.request.urlopen(r))
if __name__=="__main__":
    for a in ('cubo-2-avoider','cubo-2-mantis'):
        print(a)
        for r in get('ivs_assembly_joints','assembly_id=eq.%s&select=*'%a): print(' J',{k:v for k,v in r.items() if k not in('id','updated_by','updated_at','assembly_id')})
        for r in get('ivs_assembly_joint_groups','assembly_id=eq.%s&select=*'%a): print(' G',{k:v for k,v in r.items() if k not in('id','updated_by','updated_at','assembly_id')})
