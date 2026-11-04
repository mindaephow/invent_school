# 레인 관절 고침(2026-10-26, 사용자 지적): 분홍으로 칠한 레인 블록(7번)이 아니라 벽에 돌기 하나로 매달린 3단블록(3번·6번)이 관절 — 돌기(p5·p8, z축)를 중심으로 블록과 레인이 같이 살짝 움직인다.
import json,urllib.request,sys,runpy
sys.stdout.reconfigure(encoding="utf-8")
import _jq
U,K=_jq.U,_jq.K; A_ID='cubo-2-bowling'
g=runpy.run_path("bowling.py",run_name="probe"); A=g["A"]
def req(method,path,rows=None):
    r=urllib.request.Request(U+'/rest/v1/'+path,data=(json.dumps(rows).encode('utf-8') if rows is not None else None),method=method,headers={'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'return=minimal'})
    urllib.request.urlopen(r)
req('DELETE','ivs_assembly_joints?assembly_id=eq.%s&joint_id=in.(lane_pivot1,lane_pivot2)'%A_ID)
req('DELETE','ivs_assembly_joint_groups?assembly_id=eq.%s&group_id=in.(lane1,lane2)'%A_ID)
def names(steps): return [q.name for q in A.parts if q.step.index in steps]
L1=["3단블록 3번"]+names([7,8,9,10,11]); L2=["3단블록 6번"]+names([13,14])
NOTE='[색칠할 부품 = part_a, 좌표는 part_a 기준 로컬 mm: 3단블록 안쪽 돌기 p5·p8 의 가운데 선(x −10, z 0), 축 = 돌기 방향 z] [모터와 무관] 벽 판에 돌기 하나(p5·p8)로 끼워진 이 3단블록이 돌기 둘레로 관절처럼 살짝 움직이고 레인이 같이 기운다(사용자 설명 2026-10-26: 분홍으로 칠했던 레인 블록이 아니라 아래쪽 블록이 관절). 각도 범위는 추정, 사용자 확인 필요.'
G=[dict(assembly_id=A_ID,group_id=gid,name=nm,parent_group_id=None,kind='body',link_length=None,root_joint_id=jid,members=[{'name':m} for m in mem],note='벽에 매달린 3단블록이 돌기를 중심으로 살짝 움직이면 레인 전체가 같이 기운다.') for gid,nm,jid,mem in (('lane1','첫째 레인+관절 블록','lane_pivot1',L1),('lane2','둘째 레인+관절 블록','lane_pivot2',L2))]
J=[dict(assembly_id=A_ID,joint_id=j,name=n,step=st,group_id=gid,kind='pin',rides_group_id=None,is_driver=False,part_a=pa,part_b=pb,pivot_x=-10,pivot_y=0,pivot_z=0,axis_x=0,axis_y=0,axis_z=1,min_angle=-8,max_angle=8,note=NOTE) for j,n,st,gid,pa,pb in (('lane_pivot1','첫째 레인 관절(벽 3단블록 돌기)',12,'lane1','3단블록 3번','3단블록 7번'),('lane_pivot2','둘째 레인 관절(벽 3단블록 돌기)',15,'lane2','3단블록 6번','3단블록 8번'))]
req('POST','ivs_assembly_joint_groups',G); req('POST','ivs_assembly_joints',J); print('고침',len(L1),len(L2))
