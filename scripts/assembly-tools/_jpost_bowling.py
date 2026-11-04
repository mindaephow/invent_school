# 볼링머신 관절 등록(2026-10-26): 모터 축 둘레로 도는 팔(큰기어·판·프레임·25번 블록 조립) — 상자마다 한 묶음, 축 둘 = T축(앞)·T축(뒤, 모터직결)
import json,urllib.request,sys,runpy
sys.stdout.reconfigure(encoding="utf-8")
import _jq
U,K=_jq.U,_jq.K
A_ID='cubo-2-bowling'
g=runpy.run_path("bowling.py",run_name="probe"); A=g["A"]
def names(steps_orig, copy=False):
    out=[]
    for q in A.parts:
        if copy:
            c=q.extra.get("copyOf","")
            if q.step.index==35 and c and int(c.split(":")[0]) in steps_orig: out.append(q.name)
        elif q.step.index in steps_orig: out.append(q.name)
    return out
ROT=[21,22,23,24,25,27,28,29]
m1=names(ROT); m2=names(ROT,True)
def post(t,rows):
    r=urllib.request.Request(U+'/rest/v1/'+t,data=json.dumps(rows).encode('utf-8'),method='POST',headers={'apikey':K,'Authorization':'Bearer '+K,'Content-Type':'application/json','Prefer':'return=minimal'})
    urllib.request.urlopen(r); print(t,len(rows),'등록')
NOTE='[색칠할 부품 = part_a, 좌표는 part_a 기준 로컬 mm: T축 몸통 가운데·축 방향 = 로컬 y] '
J=[];G=[]
def add(gid,gname,members,joints,gnote):
    G.append(dict(assembly_id=A_ID,group_id=gid,name=gname,parent_group_id=None,kind='body',link_length=None,root_joint_id=joints[0][0],members=[{'name':m} for m in members],note=gnote))
    for jid,jname,step,pa,pb in joints:
        J.append(dict(assembly_id=A_ID,joint_id=jid,name=jname,step=step,group_id=gid,kind='axis',rides_group_id=None,is_driver=True,part_a=pa,part_b=pb,pivot_x=0,pivot_y=0,pivot_z=0,axis_x=0,axis_y=1,axis_z=0,min_angle=None,max_angle=None,note=NOTE+'[모터직결] T축이 모터 십자 구멍에 직접 꽂힌 구동 축 — 앞뒤 두 T축이 한 축선(x −55·y 20)이라 두 기어·판·프레임·25번 블록 조립이 한 덩어리로 돈다. 사용자 확인 필요.'))
add('arm1','첫째 상자 팔(앞뒤 기어+판+프레임+블록 조립)',m1,[('arm_axis1_front','첫째 상자 구동 축(앞)',30,'T축 1번','큰기어 1번'),('arm_axis1_back','첫째 상자 구동 축(뒤)',30,'T축 2번','큰기어 2번')],'T축 둘이 모터에 꽂혀 돌 때 앞뒤 큰기어·29프레임·135도 프레임·35프레임·2단블록·15프레임(25번 조립)이 한 덩어리로 같이 돈다(23·26·30번 결합).')
add('arm2','둘째 상자 팔(앞뒤 기어+판+프레임+블록 조립)',m2,[('arm_axis2_front','둘째 상자 구동 축(앞)',35,'T축 3번','큰기어 3번'),('arm_axis2_back','둘째 상자 구동 축(뒤)',35,'T축 4번','큰기어 4번')],'둘째 상자(16~33번 둘째 벌)도 같은 방식으로 한 덩어리로 돈다.')
if _jq.get('ivs_assembly_joints','assembly_id=eq.%s&select=joint_id'%A_ID): sys.exit('이미 등록됨')
print(len(m1),len(m2)); post('ivs_assembly_joint_groups',G); post('ivs_assembly_joints',J)
