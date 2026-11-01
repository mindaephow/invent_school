# 조향자동차 바퀴 축 관절 등록(2026-11-01): ivs_assembly_joints / ivs_assembly_joint_groups
import json,urllib.request,sys
sys.stdout.reconfigure(encoding="utf-8")
import _jq
U,K=_jq.U,_jq.K
def post(t,rows):
    r=urllib.request.Request(U+'/rest/v1/'+t,data=json.dumps(rows).encode('utf-8'),method='POST',headers={'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'return=minimal'})
    urllib.request.urlopen(r); print(t,len(rows),'등록')
A='cubo-3-steercar'; NOTE='[색칠할 부품 = part_a, 좌표는 part_a 기준 로컬 mm] '
J=[]; G=[]
def add(jid,name,step,gid,pa,pb,members,gname,gnote,jnote,motor=False):
    J.append(dict(assembly_id=A,joint_id=jid,name=name,step=step,group_id=gid,kind='axis',rides_group_id=None,is_driver=motor,part_a=pa,part_b=pb,pivot_x=0,pivot_y=0,pivot_z=0,axis_x=0,axis_y=1,axis_z=0,min_angle=None,max_angle=None,note=NOTE+('[모터직결] ' if motor else '')+jnote+' 사용자 확인 필요.'))
    G.append(dict(assembly_id=A,group_id=gid,name=gname,parent_group_id=None,kind='body',link_length=None,root_joint_id=jid,members=[{'name':m} for m in members],note=gnote))
add('front_axle_r','앞 오른쪽 바퀴 축',33,'fwheelR','축 1번','중간바퀴 1번',['축 1번','중간바퀴 1번'],'앞 오른쪽 바퀴 묶음','축과 중간바퀴가 같이 돈다(블록 구멍에서 자유 회전).','앞 오른쪽(+Z) 바퀴 축 — 3단블록 큰 구멍 속에서 바퀴와 함께 돈다.')
add('front_axle_l','앞 왼쪽 바퀴 축',35,'fwheelL','축 2번','중간바퀴 2번',['축 2번','중간바퀴 2번'],'앞 왼쪽 바퀴 묶음','축과 중간바퀴가 같이 돈다(블록 구멍에서 자유 회전).','앞 왼쪽(−Z) 바퀴 축 — 3단블록 큰 구멍 속에서 바퀴와 함께 돈다.')
add('rear_axle_r','뒤 오른쪽 구동 축',38,'rwheelR','축 3번','중간바퀴 3번',['축 3번','중간바퀴 3번','큰기어 1번'],'뒤 오른쪽 구동 묶음','DC모터 십자 구멍에 직접 꽂힌 축이 바퀴·큰기어와 함께 돈다.','뒤 오른쪽 DC모터 십자 구멍에 직접 꽂힌 축 — 중간바퀴·큰기어가 같이 돈다.',True)
add('rear_axle_l','뒤 왼쪽 구동 축',40,'rwheelL','축 4번','중간바퀴 4번',['축 4번','중간바퀴 4번','큰기어 2번'],'뒤 왼쪽 구동 묶음','DC모터 십자 구멍에 직접 꽂힌 축이 바퀴·큰기어와 함께 돈다.','뒤 왼쪽 DC모터 십자 구멍에 직접 꽂힌 축 — 중간바퀴·큰기어가 같이 돈다.',True)
if _jq.get('ivs_assembly_joints','assembly_id=eq.%s&select=joint_id'%A): sys.exit('이미 등록됨')
post('ivs_assembly_joint_groups',G); post('ivs_assembly_joints',J)
