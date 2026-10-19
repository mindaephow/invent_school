# 큐보 1권 축구로봇(교재 55~60쪽) 조립도 — asmlib 로 설명서 번호대로 옮긴 것.
# 좌표: 바퀴 아랫면 y=0(바닥), 뒤쪽(바퀴·뒤판)이 +x, 머리·팔이 −x, 위 +y. 왼쪽 벽 z=+47.5, 오른쪽 벽 z=−47.5(판 두께 5, 안쪽 면 z=±45).
# 바퀴 축 = 뒤쪽 벽 끝 칸(15번째 열, x=0)·가운데 줄(y=25). 구멍 번호는 벽 315프레임에서 앞→뒤로 센다(15번째 열 x=0, 1번째 열 x=−140).
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-1-soccer", "축구로봇", "교재 55~60쪽 · 축구로봇 (1~27단계)", camera={"target": [-50, 30, 0], "radius": 360, "theta": 0.6, "phi": 0.95},
        listNote="리모컨은 3D 모델이 없어 조립도에서 제외했다")
UP = (0, 1, 0)

def wallR(sg): return ori("+x", "+z" if sg > 0 else "-z")           # 315프레임 벽: 긴 쪽 x, 구멍축 ±z
def motorR(sg): return ori("-y", "+z") if sg > 0 else ori("+y", "-z")  # 모터: 윗면 돌기(+y_m)가 벽 쪽, 긴 쪽(z_m)이 −x(앞)
BLK_R = ori("+y", "+z")                                               # 뒤 3단블록: 길이가 세로, 돌기 면이 ±x

SIDES = {}   # sg -> dict(parts)
FLAT = {+1: (Rx(90), (-70, 25, 47.5), (-70, 2.5, 120)), -1: (Rx(-90), (-70, 25, -47.5), (-70, 2.5, -120))}

# ── 1 ── 315프레임 위에 DC모터 (옆자리에서 평평하게 조립)
s1 = A.step("[교재 1] 315프레임 2개에 DC모터를 하나씩 꽂아요: 모터 돌기 2개가 판 가운데 줄의 9번째·13번째 구멍(앞에서 센 번호)에 들어가요. 케이블은 판 앞쪽을 봐요.")
for sg in (+1, -1):
    w = s1.place("315프레임", wallR(sg), (-70, 25, sg * 47.5))
    m = s1.attach("DC모터", motorR(sg), {"p1": (w, (-60, 25, sg * 47.5)), "p2": (w, (-20, 25, sg * 47.5))})
    SIDES[sg] = {"wall": w, "motor": m}

# ── 2 ── 리벳 4개 + 3단블록
s2 = A.step("[교재 2] 판 뒤쪽 끝(15번째 열)의 위·아래 구멍에 리벳을 꽂고(2개씩, 모두 4개), 3단블록을 그 위에 얹어 리벳이 블록 양끝 구멍에 들어가게 해요.")
for sg in (+1, -1):
    w = SIDES[sg]["wall"]; rv = []
    for y in (15, 35):
        r = s2.attach("리벳", ori("+x", "+z" if sg > 0 else "-z"), {"p2": (w, (0, y, sg * 47.5))}, rivet=True)
        rv.append(r)
    b = s2.recv("3단블록", BLK_R, [(rv[0], "p1"), (rv[1], "p1")], p=(0, 25, sg * 40), joinOrder=2)
    SIDES[sg].update({"rivets": rv, "block": b})

# ── 3 ── 벽 세우기 + 바닥판
s3 = A.step("[교재 3] 바닥에 59프레임(흰색)과 29프레임(검정)을 깔고, 만든 두 벽을 세워요: 모터 아래 돌기 2개는 흰 판에, 블록 아래 끝 돌기는 검은 판에 꽂혀요.")
white_b = s3.place("59프레임", ori("+z", "+y"), (-50, 7.5, 0))
black_b = s3.place("29프레임", ori("+z", "+y"), (-5, 7.5, 0))
for sg in (+1, -1):
    Rs, Cf, Cs = FLAT[sg]
    S = SIDES[sg]
    for key in ("wall", "motor", "block"):
        to_side(S[key], Rs, Cf, Cs, 3, UP, hosts=[white_b, black_b])
    for r in S["rivets"]: to_side(r, Rs, Cf, Cs, 3, UP)


# ── 4·5 ── T축 + 작은기어 (모터 십자 구멍에, 벽 바깥에서) — 기어 축 = 벽 12번째 열(x=−30), 가운데 줄
def small_gear_step(sg, no):
    st = A.step(f"[교재 {no}] 작은기어를 벽 바깥 면에 대고, T축을 기어 가운데 구멍으로 끼워 벽 구멍을 지나 모터 십자 구멍까지 꽂아요(벽 앞에서 12번째 구멍, 가운데 줄). T축 접시 머리가 바깥이에요.")
    S = SIDES[sg]; w = S["wall"]
    g = st.place("작은기어", ori("+x", "+z" if sg > 0 else "-z"), (-30, 25, sg * 54), dir=[0, 0, sg], hover=22, marks=[[-30, 25, sg * 50]])
    t = st.attach("T축", ori("+x", "-z" if sg > 0 else "+z"), {"p1": (g, "h1")}, dir=(0, 0, sg), hover=45, pegDepth=28.6, headDown=True)
    t.extra["marks"] = [[-30, 25, sg * 50]]
    S["gear"], S["T"] = g, t
small_gear_step(+1, 4)
small_gear_step(-1, 5)

# ── 6 ── 바퀴 묶음(축·큰기어·작은바퀴·부시)을 옆자리에서 따로 조립
UNIT = {}
def wheel_unit_step():
    st = A.step("[교재 6] 바퀴 묶음 2개를 따로 만들어요: 축에 큰기어와 작은바퀴를 끼우고, 바퀴 바깥쪽 끝에 부시로 막아요(2개 똑같이).")
    for sg in (+1, -1):
        Rr = ori("+x", "+z" if sg > 0 else "-z")
        # 바깥(벽 반대쪽) 방향이 축 +방향. 벽 바깥면 |z|=50 기준 큰기어 [50,59], 바퀴 [59,75], 바깥 부시 [75,80.5], 축 [22.5,87.5]
        ax = st.place("축", Rr, (0, 25, sg * 55))
        gr = st.place("큰기어", Rr, (0, 25, sg * 54.5))
        wh = st.place("작은바퀴", Rr, (0, 25, sg * 67))
        bu = st.place("부시", Rr, (0, 25, sg * 77.75))
        UNIT[sg] = {"axle": ax, "gear": gr, "wheel": wh, "bush": bu}
wheel_unit_step()

def to_side_unit(sg, S, until):
    # 바퀴 묶음은 축이 위(+y)로 서도록 옆자리(x=100, z=±150)에서 따로 만든다
    Rs = Rx(-90) if sg > 0 else Rx(90)    # 바깥(±z) → +y
    Cf = np.array([0, 25, sg * 55.0]); Cs = np.array([110.0, 40.0, sg * 150.0])
    for k, pt in S.items(): to_side(pt, Rs, Cf, Cs, until, (0, 0, sg))

# ── 7·8 ── 바퀴 묶음을 벽에 끼우고 안쪽에 부시
def wheel_mount_step(sg, no):
    st = A.step(f"[교재 {no}] 바퀴 묶음의 축을 벽 뒤쪽 끝 구멍(15번째 열, 가운데 줄)에 끼우고, 안쪽 축 끝에 부시를 끼워 고정해요.")
    inner = st.place("부시", ori("+x", "+z" if sg > 0 else "-z"), (0, 25, sg * 32.25), recv=True, dir=[0, 0, -sg], hover=22, marks=[[0, 25, sg * 22.5]])
    return inner
inner_R = wheel_mount_step(-1, 7)
inner_L = wheel_mount_step(+1, 8)
for sg in (+1, -1):
    U = UNIT[sg]
    to_side_unit(sg, U, 8 if sg > 0 else 7)
    U["axle"].extra["settleMarks"] = [[0, 25, sg * 50]]

# ── 9 ── 윗판: 흰 59프레임은 모터 위 돌기에, 검은 39프레임은 블록 위 끝 돌기에
st9 = A.step("[교재 9] 모터 위쪽 돌기 4개에 59프레임(흰색)을, 뒤쪽 블록 위 끝 돌기 2개에 39프레임(검정)을 덮어요.")
Rp = ori("+z", "+y")
wt = st9.recv("59프레임", Rp, [(SIDES[1]["motor"], "p5"), (SIDES[1]["motor"], "p6"), (SIDES[-1]["motor"], "p5"), (SIDES[-1]["motor"], "p6")], p=(-50, 42.5, 0))
bt = st9.recv("39프레임", Rp, [(SIDES[1]["block"], "p1"), (SIDES[-1]["block"], "p1")], p=(-10, 42.5, 0))

# ── 10 ── 뒤판
st10 = A.step("[교재 10] 39프레임을 뒤쪽 두 블록의 뒤쪽 돌기(위·아래 줄)에 끼워 뒤판을 세워요.")
rear = st10.recv("39프레임", ori("+z", "+x"), [(SIDES[1]["block"], "p3"), (SIDES[1]["block"], "p5"), (SIDES[-1]["block"], "p3"), (SIDES[-1]["block"], "p5")], p=(7.5, 25, 0))

# ── 11~14 ── 팔(왼쪽 → 오른쪽): 3단블록 2개를 벽 바깥에 꽂고, 37프레임·빨간 17프레임
ARM = {}
def arm_steps(sg, no_a, no_b):
    S = SIDES[sg]; w = S["wall"]
    Rb = ori("+y", "+x") if sg > 0 else ori_z("+y", "+z")
    st = A.step(f"[교재 {no_a}] 3단블록 2개를 벽 바깥 면(앞에서 1번째·7번째 열)에 돌기 3개씩 꽂고, 바깥 돌기에 37프레임(위·아래 줄)을 끼워요.")
    blks = []
    for x in (-140, -80):
        b = st.attach("3단블록", Rb, {"p3": (w, (x, 35, sg * 47.5)), "p4": (w, (x, 25, sg * 47.5)), "p5": (w, (x, 15, sg * 47.5))})
        blks.append(b)
    pl = st.recv("37프레임", ori("+x", "+z" if sg > 0 else "-z"), [(blks[0], "p7"), (blks[0], "p8"), (blks[1], "p7"), (blks[1], "p8")], p=(-110, 25, sg * 62.5))
    st2 = A.step(f"[교재 {no_b}] 빨간 17프레임 2개를 블록 위·아래 끝 돌기에 끼워요.")
    top = st2.recv("17프레임", ori("+x", "+y"), [(blks[0], "p1"), (blks[1], "p1")], p=(-110, 42.5, sg * 55))
    bot = st2.recv("17프레임", ori("+x", "+y"), [(blks[0], "p2"), (blks[1], "p2")], p=(-110, 7.5, sg * 55))
    ARM[sg] = {"blocks": blks, "plate": pl, "top": top, "bot": bot}
arm_steps(+1, 11, 12)
arm_steps(-1, 13, 14)


# ───────── 머리 탑(교재 15~21): 따로 조립해서 22단계에 몸체 위에 올린다 ─────────
# 마지막 모양: 59프레임 두 장(앞 B x=−77.5, 뒤 A x=−62.5)이 세로(길이 90, y 45~135)로 서고 그 사이(x −75~−65)에 블록이 끼인다. 머리 중심 x=−70, 눈은 앞(−x).
# 따로 조립하는 자세(옆자리): 뒤판 A 를 바닥에 눕혀 놓고 위로 쌓는다(교재 그림 방향).
FH = (Rz(-90), (-70, 90, 0), (-60, 15, -230))
HEAD = []
def hs(note): return A.step(note)
Ra = ori("+y", "+x")                                   # 59프레임: 길이 y, 구멍축 x
RB2 = ori("+y", "+z")                                   # 2단블록: 길이 y(세로), 돌기 면이 ±x
RB3 = ori("+z", "+y")                                   # 3단블록: 길이 z(가로), 구멍이 위(y), 돌기 면이 ±x

s15 = hs("[교재 15] 뒤판 59프레임 위에 3단블록 1개(위쪽 끝 줄)와 2단블록 2개(아래쪽 양옆 줄)를 눕혀 돌기 2개씩 꽂아요.")
PA = s15.place("59프레임", Ra, (-62.5, 90, 0)); HEAD.append(PA)
b3 = s15.attach("3단블록", RB3, {"p7": (PA, (-62.5, 130, 10)), "p8": (PA, (-62.5, 130, -10))}, hover=22); HEAD.append(b3)
b2 = []
for z in (20, -20):
    b = s15.attach("2단블록", RB2, {"p3": (PA, (-62.5, 50, z)), "p4": (PA, (-62.5, 60, z))}, hover=22)
    b.p = b.p + np.array([0, 0.65, 0])   # 돌기 위치(−4.4·5.7)가 구멍 간격(10)과 0.65 어긋나 있어 몸통 아래 면이 판 윗면(y=45)에 딱 닿게 맞춘다(끝 돌기가 판 구멍 가운데)
    b2.append(b); HEAD.append(b)

s16 = hs("[교재 16] 판 가운데 줄 양옆(위에서 5번째 줄, 양쪽 끝에서 2번째 구멍)에 리벳 2개를 꽂고, 1열브라켓 2개를 그 위에 얹어요. 브라켓 세로 판이 판 밖으로 나와요(귀).")
ears = []
for z, Rbr in ((20, np.array(ori("-y", "-x")) if False else None), (-20, None)): pass
RBR = {+1: np.column_stack([(0, -1, 0), (-1, 0, 0), (0, 0, -1)]), -1: np.column_stack([(0, 1, 0), (-1, 0, 0), (0, 0, 1)])}
for sg in (+1, -1):
    rv = s16.attach("리벳", ori("+y", "+x"), {"p2": (PA, (-62.5, 90, sg * 20))}, rivet=True); HEAD.append(rv)
    br = s16.recv("1열브라켓", RBR[sg], [(rv, "p1")], p=(-80, 90, sg * 20)); HEAD.append(br); ears.append(br)

s17 = hs("[교재 17] 앞판 59프레임을 블록 위쪽 돌기 6개(3단블록 2개, 2단블록 2개씩)에 얹어 샌드위치처럼 덮어요.")
PB = s17.recv("59프레임", Ra, [(b3, "p3"), (b3, "p5"), (b2[0], "p5"), (b2[0], "p6"), (b2[1], "p5"), (b2[1], "p6")], p=(-77.5, 90, 0)); HEAD.append(PB)

s18 = hs("[교재 18] 앞판에 리벳 6개를 꽂고, 검은 35프레임(위 줄 3개·모서리 4곳)과 빨간 15프레임(2번째·4번째 구멍 2곳)을 얹어요(아래에서 2~5번째 줄).")
rv4 = [s18.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, y, z))}, rivet=True) for (y, z) in ((70, 20), (70, -20), (90, 20), (90, -20))]
rv2 = [s18.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, 60, z))}, rivet=True) for z in (10, -10)]
Rf = ori("+z", "-x") if False else np.column_stack([(0, 0, 1), (-1, 0, 0), (0, -1, 0)])  # 35프레임: 길이 z, 구멍축 −x... (구멍축은 x, 줄 방향 −y)
black35 = s18.recv("35프레임", Rf, [(r, "p1") for r in rv4], p=(-82.5, 80, 0))
red15 = s18.recv("15프레임", np.column_stack([(0, 0, 1), (-1, 0, 0), (0, -1, 0)]), [(r, "p1") for r in rv2], p=(-82.5, 60, 0))
HEAD += rv4 + rv2 + [black35, red15]

s19 = hs("[교재 19] 리벳 1개를 앞판 가운데(위에서 6번째 줄)에 꽂고, 눈블록 2개를 그 위 줄(7번째 줄, 가운데에서 양옆 2칸)에 꽂아요.")
rv1 = s19.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, 100, 0))}, rivet=True, openEnd=True)
eyes = [s19.attach("눈블록", ori("+y", "+x"), {"p1": (PB, (-77.5, 110, z))}) for z in (10, -10)]
HEAD += [rv1] + eyes

s20 = hs("[교재 20] 3단블록 윗면 구멍 양옆 2곳에 리벳 2개를 꽂고, 35프레임(검정)을 머리 위쪽 끝에 얹어요.")
capR = np.column_stack([(0, 0, 1), (0, 1, 0), (-1, 0, 0)])    # 35프레임 눕힘: 길이 z, 구멍축 y
rv_top = [s20.attach("리벳", ori("+x", "+y"), {"p1": (b3, hid)}, rivet=True) for hid in ("h1", "h3")]
cap = s20.recv("35프레임", capR, [(r, "p2") for r in rv_top], p=(-70, 137.5, 0))
HEAD += rv_top + [cap]

s21 = hs("[교재 21] 35프레임 위 3곳(1·3·5번째 구멍)에 리벳 3개를 꽂고, 빨간 15프레임을 얹으면 머리 완성이에요.")
rv3 = [s21.attach("리벳", ori("+x", "+y"), {"p1": (cap, (-70, 137.5, z))}, rivet=True) for z in (-20, 0, 20)]
red_top = s21.recv("15프레임", np.column_stack([(0, 0, 1), (0, 1, 0), (-1, 0, 0)]), [(r, "p2") for r in rv3], p=(-70, 142.5, 0))
HEAD += rv3 + [red_top]

# 몸체 위 흰 59프레임(wt)에 머리 올리기(교재 22) — 머리 부품은 모두 옆자리에서 합쳐진다
s22 = hs("[교재 22] 머리를 몸체 윗판(흰 59프레임) 앞쪽 줄에 올려요: 2단블록 아래 끝 돌기 2개가 윗판 구멍 2곳(양옆에서 3번째 줄)에 꽂혀요.")
for pt in HEAD:
    to_side(pt, FH[0], FH[1], FH[2], 22, (0, 1, 0), hosts=[wt] if pt.n == "2단블록" else ())

# ── 23·24 ── 메인보드
s23 = hs("[교재 23] 메인보드를 윗판 위에 꽂아요: 보드 아래 돌기 2개가 흰 판과 검은 판 구멍에 들어가요.")
board = s23.attach("메인보드", ori("+z", "+y"), {"p1": (bt, (-10, 42.5, 20)), "p2": (wt, (-30, 42.5, 20))}) if False else None
Rbd = ori("+z", "+y")
tmp = Part("메인보드", Rbd, (0, 0, 0), s23)
pp = tmp.peg("p1")["pos"]
board_p = np.array([-10, 42.5, 0.0]) - pp
board = s23.place("메인보드", Rbd, board_p, dir=[0, 1, 0], hover=40, marks=[[-10, 45, 0]])
bp = Part("메인보드", Rbd, board_p, s23)
board.extra["marks"] = [rnd(np.array(q["pos"]) - np.array(q["dir"]) * 0 + np.array([0, 2.5 + 0, 0]) - np.array([0, 0, 0])) for q in (bp.peg("p1"), bp.peg("p2"))]
s24 = A.step("[교재 24] 메인보드 왼쪽 단자에 왼쪽 DC모터 선을, 오른쪽 단자에 오른쪽 DC모터 선을 연결해요.", noPart=True)

# ── 25 ── 뒤판에 3단블록
s25 = A.step("[교재 25] 3단블록 하나를 뒤판 바깥 면(왼쪽에서 앞으로 8번째 줄, 위·아래 줄)에 꽂아요.")
blk25 = s25.attach("3단블록", ori_z("+y", "-x"), {"p3": (rear, (7.5, 35, 30)), "p5": (rear, (7.5, 15, 30))})

# ── 26·27 ── 깃발: 35프레임(검정)+리벳 3개+115프레임, 따로 조립했다가 3단블록에 끼운다
FF = (np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1.]]), (22.5, 85, 30), (-70, 10, 230))
s26 = A.step("[교재 26] 35프레임(검정)의 한 줄 1·3·5번째 구멍에 리벳 3개를 꽂고, 115프레임(긴 막대)의 1·3·5번째 구멍을 그 위에 얹어요.")
flag_plate = s26.place("35프레임", ori("+y", "+x"), (27.5, 135, 30))
rvf = [s26.attach("리벳", ori("+y", "+x"), {"p2": (flag_plate, (25, y, 30))}, rivet=True) for y in (155, 135, 115)]
pole = s26.recv("115프레임", np.column_stack([(0, -1, 0), (1, 0, 0), (0, 0, 1)]), [(r, "p1") for r in rvf], p=(22.5, 85, 30))
s27 = A.step("[교재 27] 깃발의 115프레임 아래쪽 끝 2곳(13번째·15번째 구멍)을 3단블록 바깥 돌기 2개에 끼우면 완성!")
FLAG = [flag_plate] + rvf + [pole]
for pt in FLAG:
    to_side(pt, FF[0], FF[1], FF[2], 27, (1, 0, 0))
pole.extra["settleMarks"] = [[25, 35, 30], [25, 15, 30]]


# 카메라(교재 그림 방향을 눈으로 본 값 — 모두 짐작 'guess': 단계 방위 θ, 고도 φ(라디안). 카메라 위치 = 대상 + (sinφ·sinθ, cosφ, sinφ·cosθ)
#  θ=0: +z(왼쪽 벽 쪽)에서 봄, θ=π/2: +x(뒤)에서, θ=−π/2: −x(앞)에서, θ=π: −z(오른쪽 벽 쪽)에서.
CAMS = {1: (-0.5, 0.95), 2: (-0.5, 0.95), 3: (-0.45, 0.95), 4: (-0.35, 0.95), 5: (2.8, 0.95), 6: (-0.3, 0.9), 7: (2.8, 0.95), 8: (-0.35, 0.95),
        9: (1.2, 0.95), 10: (1.5, 1.1), 11: (-0.45, 1.05), 12: (-0.45, 1.05), 13: (3.59, 1.05), 14: (3.59, 1.05),
        15: (0.6, 0.85), 16: (0.6, 0.85), 17: (0.6, 0.85), 18: (0.6, 0.85), 19: (0.6, 0.85), 20: (0.6, 0.85), 21: (0.6, 0.85),
        22: (-1.5, 1.1), 23: (0.15, 1.15), 24: (-0.5, 1.0), 25: (1.2, 1.1), 26: (0.0, 0.9), 27: (0.9, 1.05)}
for k, (th, ph) in CAMS.items():
    A.steps[k - 1].cam = (th, ph); A.steps[k - 1].camSrc = "guess"

A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("soccer_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    entry = js_entry(A)
    open("soccer_entry.js", "w", encoding="utf-8").write(entry)
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
