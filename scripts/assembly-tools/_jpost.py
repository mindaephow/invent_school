# 배틀로봇 관절 등록(2026-10-17): ivs_assembly_joints / ivs_assembly_joint_groups 에 서비스 키로 한 번 넣는다(이미 있으면 건너뜀)
import json,urllib.request,sys
sys.stdout.reconfigure(encoding="utf-8")
import _jq
U,K=_jq.U,_jq._jq.K if hasattr(_jq,'_jq') else _jq.K
def post(t,rows):
    r=urllib.request.Request(U+'/rest/v1/'+t,data=json.dumps(rows).encode('utf-8'),method='POST',headers={'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'return=minimal'})
    urllib.request.urlopen(r); print(t,len(rows),'등록')
A='cubo-2-battlerobot'
NOTE='[색칠할 부품 = part_a, 좌표는 part_a 기준 로컬 mm] '
J=[]; G=[]
def add(jid,name,step,gid,part_a,part_b,members,gname,gnote,jnote,driver=False,motor=False):
    J.append(dict(assembly_id=A,joint_id=jid,name=name,step=step,group_id=gid,kind='axis',rides_group_id=None,is_driver=driver,part_a=part_a,part_b=part_b,pivot_x=0,pivot_y=0,pivot_z=0,axis_x=0,axis_y=1,axis_z=0,min_angle=None,max_angle=None,note=NOTE+('[모터직결] ' if motor else '')+jnote+' 사용자 확인 필요.'))
    G.append(dict(assembly_id=A,group_id=gid,name=gname,parent_group_id=None,kind='body',link_length=None,root_joint_id=jid,members=[{'name':m} for m in members],note=gnote))
add('motor_axis1','모터 구동 축(첫째 유닛)',2,'drive1','T축 1번','작은기어 1번',['T축 1번','작은기어 1번'],'모터 구동 묶음(첫째 유닛)','T축 1번이 모터와 함께 돌고 작은기어 1번이 같이 돈다.','DC모터 십자 구멍에 직접 꽂힌 T축 — 작은기어와 함께 돈다.',True,True)
add('gear_axis1','큰기어 축(첫째 유닛)',3,'gear1','T축 2번','큰기어 1번',['T축 2번','큰기어 1번','작은기어 2번','부시 1번'],'큰기어 묶음(첫째 유닛)','T축 2번 기준으로 큰기어 1번·작은기어 2번(4번)·부시가 같이 돈다.','판 칸5 줄4 에 꽂힌 T축 — 큰기어(작은기어 1번과 맞물림)와 뒤쪽 작은기어가 같이 돈다.',False)
add('wheel_axis1','바퀴 축(첫째 유닛)',9,'wheel1','축 1번','중간바퀴 1번',['축 1번','큰기어 2번','중간바퀴 1번','부시 2번','부시 3번','부시 4번'],'바퀴 묶음(첫째 유닛)','축 1번 기준으로 큰기어 2번(6번)·바퀴·부시가 같이 돈다.','판 칸2 줄4 에 꽂힌 바퀴 축 — 큰기어 2번(뒤 작은기어와 맞물림)과 중간바퀴가 같이 돈다.',False)
add('motor_axis2','모터 구동 축(둘째 유닛)',13,'drive2','T축 3번','작은기어 3번',['T축 3번','작은기어 3번'],'모터 구동 묶음(둘째 유닛)','T축 3번이 모터 2번과 함께 돌고 작은기어 3번이 같이 돈다.','DC모터(둘째 유닛) 십자 구멍에 직접 꽂힌 T축 — 작은기어와 함께 돈다.',True,True)
add('gear_axis2','큰기어 축(둘째 유닛)',14,'gear2','T축 4번','큰기어 3번',['T축 4번','큰기어 3번','작은기어 4번','부시 5번'],'큰기어 묶음(둘째 유닛)','T축 4번 기준으로 큰기어 3번·작은기어 4번·부시가 같이 돈다.','판 칸5 줄4 에 꽂힌 T축(둘째 유닛) — 큰기어와 뒤쪽 작은기어가 같이 돈다.',False)
add('wheel_axis2','바퀴 축(둘째 유닛)',20,'wheel2','축 2번','중간바퀴 2번',['축 2번','큰기어 4번','중간바퀴 2번','부시 6번','부시 7번','부시 8번'],'바퀴 묶음(둘째 유닛)','축 2번 기준으로 큰기어 4번·바퀴·부시가 같이 돈다.','판 칸8 줄4 에 꽂힌 바퀴 축(둘째 유닛) — 큰기어 4번과 중간바퀴가 같이 돈다.',False)
if _jq.get('ivs_assembly_joints','assembly_id=eq.%s&select=joint_id'%A): sys.exit('이미 등록됨')
post('ivs_assembly_joint_groups',G); post('ivs_assembly_joints',J)
