# 볼링머신 레인 관절 등록(2026-10-26, 사용자 설명: "모터와 상관없이 블록의 돌기가 관절 — 3단블록 돌기가 관절처럼 움직이면서 살짝 움직임")
import json,urllib.request,sys,runpy
sys.stdout.reconfigure(encoding="utf-8")
import _jq
U,K=_jq.U,_jq.K; A_ID='cubo-2-bowling'
g=runpy.run_path("bowling.py",run_name="probe"); A=g["A"]
def names(steps): return [q.name for q in A.parts if q.step.index in steps]
L1=names([7,8,9,10,11]); L2=names([13,14])
def post(t,rows):
    r=urllib.request.Request(U+'/rest/v1/'+t,data=json.dumps(rows).encode('utf-8'),method='POST',headers={'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'return=minimal'})
    urllib.request.urlopen(r); print(t,len(rows),'등록')
NOTE='[색칠할 부품 = part_a, 좌표는 part_a 기준 로컬 mm: 3단블록 가운데 돌기 p6(0,0,−7.5), 축 = 돌기 방향 −z] [모터와 무관] 레인의 3단블록 돌기 셋(p6·p7·p8)이 벽 블록 구멍에 끼워진 채 돌기가 관절처럼 움직여 레인이 살짝 기울어진다(사용자 설명 2026-10-26). 각도 범위는 추정, 사용자 확인 필요.'
G=[dict(assembly_id=A_ID,group_id='lane1',name='첫째 레인(흰 판+검은 판+막대+블록+브라켓+215프레임)',parent_group_id=None,kind='body',link_length=None,root_joint_id='lane_pivot1',members=[{'name':m} for m in L1],note='벽 블록 구멍에 낀 3단블록 돌기를 중심으로 레인 전체가 살짝 기운다.'),
   dict(assembly_id=A_ID,group_id='lane2',name='둘째 레인',parent_group_id=None,kind='body',link_length=None,root_joint_id='lane_pivot2',members=[{'name':m} for m in L2],note='첫째 레인과 같은 방식(7~9번 복사).')]
J=[dict(assembly_id=A_ID,joint_id=j,name=n,step=st,group_id=gid,kind='pin',rides_group_id=None,is_driver=False,part_a=pa,part_b=pb,pivot_x=0,pivot_y=0,pivot_z=-7.5,axis_x=0,axis_y=0,axis_z=-1,min_angle=-8,max_angle=8,note=NOTE) for j,n,st,gid,pa,pb in (('lane_pivot1','첫째 레인 돌기 관절',12,'lane1','3단블록 7번','3단블록 3번'),('lane_pivot2','둘째 레인 돌기 관절',15,'lane2','3단블록 8번','3단블록 6번'))]

print(len(L1),len(L2)); post('ivs_assembly_joints',J)
