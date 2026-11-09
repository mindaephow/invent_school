# 큐보 1권 축구로봇(교재 55~60쪽) 조립도 — asmlib 로 설명서 번호대로 옮긴 것.
# 좌표: 바퀴 아랫면 y=0(바닥), 뒤쪽(바퀴·뒤판)이 +x, 머리·팔이 −x, 위 +y. 왼쪽 벽 z=+47.5, 오른쪽 벽 z=−47.5(판 두께 5, 안쪽 면 z=±45).
# 바퀴 축 = 뒤쪽 벽 끝 칸(15번째 열, x=0)·가운데 줄(y=25). 구멍 번호는 벽 315프레임에서 앞→뒤로 센다(15번째 열 x=0, 1번째 열 x=−140).
import os as _o, sys as _s  # asmpath bootstrap: 조립도 폴더에서 도구 폴더를 찾는다
_d = _o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d, 'asmlib.py')) and _o.path.dirname(_d) != _d: _d = _o.path.dirname(_d)
_s.path.insert(0, _d)
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-1-soccer", "축구로봇", "교재 55~60쪽 · 축구로봇 (1~27단계)", camera={"target": [-50, 30, 0], "radius": 360, "theta": 0.6, "phi": 0.95},
        listNote="리모컨은 3D 모델이 없어 조립도에서 제외했다", guideMode="mates")
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
    b = s2.recv("3단블록", BLK_R, {"h1": (rv[0], "p1"), "h3": (rv[1], "p1")}, joinOrder=2, thick=2)   # 리벳 끝(길이 5)이 구멍(길이 10) 가운데에서 끝난다 — spinner 와 같이 링 = 끝 − 두께/2 가 구멍 가운데에 오게 thick=2
    SIDES[sg].update({"rivets": rv, "block": b})

# ── 3 ── 벽 세우기 + 바닥판
s3 = A.step("[교재 3] 바닥에 59프레임(흰색)과 29프레임(검정)을 깔고, 만든 두 벽을 세워요: 모터 아래 돌기 2개는 흰 판에, 블록 아래 끝 돌기는 검은 판에 꽂혀요.")
white_b = s3.place("59프레임", ori("+z", "+y"), (-40, 7.5, 0))   # 책 3번 링: 모터 돌기가 흰 판 칸2·칸8 의 줄2·줄4 에(2026-11-09 책 대조로 x −50→−40 정정)
black_b = s3.place("29프레임", ori("+z", "+y"), (-5, 7.5, 0))   # 책 3번 링: 블록 돌기가 검은 판 칸1·칸9 의 줄2 에(03_B 격자로 링 2개를 계산: 칸1줄2 6.5px·칸9줄2 8.2px; 흰 판 마지막 줄 바로 뒤에 이어진다) — 사용자 2026-11-09 3번 결합위치 수정
for sg in (+1, -1):
    Rs, Cf, Cs = FLAT[sg]
    S = SIDES[sg]
    for key in ("wall", "motor", "block"):
        to_side(S[key], Rs, Cf, Cs, 3, UP, hosts=[white_b, black_b])
    for r in S["rivets"]: to_side(r, Rs, Cf, Cs, 3, UP)
    S["block"].extra["settleRecv"] = False   # 3번에서 블록은 자기 돌기를 검은 판 구멍에 꽂는 쪽이다(받는 쪽 아님) — 안내점은 판 구멍 입구


# ── 4·5 ── T축 + 작은기어 (모터 십자 구멍에, 벽 바깥에서) — 기어 축 = 벽 12번째 열(x=−30), 가운데 줄
def small_gear_step(sg, no):
    st = A.step(f"[교재 {no}] 작은기어를 벽 바깥 면에 대고, T축을 기어 가운데 구멍으로 끼워 벽 구멍을 지나 모터 십자 구멍까지 꽂아요(벽 앞에서 12번째 구멍, 가운데 줄). T축 접시 머리가 바깥이에요.")
    S = SIDES[sg]; w = S["wall"]
    g = st.place("작은기어", ori("+x", "+z" if sg > 0 else "-z"), (-30, 25, sg * 54), recv=True, dir=[0, 0, sg], hover=22, thick=8, joinOrder=2, marks=[[-30, 25, sg * 58]])   # 책 4번: 기어도 벽에서 떠 있고 T축이 기어 구멍을 받는다
    t = st.attach("T축", ori("+x", "-z" if sg > 0 else "+z"), {"p1": (g, "h1")}, dir=(0, 0, sg), hover=60, pegDepth=28.6, headDown=True)   # 사용자 2026-11-09: 4·5번 T축은 조립 전이라 작은기어에서 더 띄운다(45→60)
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
        t = (0, 0, sg)
        ax = st.place("축", Rr, (0, 25, sg * 55), noGuide=True)
        gr = st.place_hang("큰기어", Rr, "h3", ax, "p1", 50, t, dir=[0, 0, sg], hover=68.5, recv=True)   # 벽 바깥면(|z|=50)에 닿게 — 책 6번: 축에 꿰는 순서 기어 → 바퀴 → 부시(spinner 14·24번과 같은 방식)
        wh = st.place_hang("작은바퀴", Rr @ np.diag([1.0, -1.0, -1.0]), "h4", ax, "p1", 59, t, dir=[0, 0, sg], hover=103.5, recv=True)
        bu = st.place_rest("부시", Rr @ np.diag([1.0, -1.0, -1.0]), "h1", wh, "h4", t, dir=[0, 0, sg], hover=131.5, recv=True, via=(ax, "p1"))
        wh.extra["thick"] = 7   # 바퀴 허브 구멍 길이(7) — 면 점이 구멍 길이 안에 오고 링이 구멍 중심에 오도록 두께를 구멍 길이로 둔다
        for _p, _h in ((gr, "h3"), (wh, "h4"), (bu, "h1")):   # 링이 자기 구멍 중심에 오도록 면 점 = 구멍 중심 + 방향×두께/2 (spinner 14번과 같음)
            _p.extra["faceMarks"] = [[round(float(v), 3) for v in np.array(_p.hole(_h)["pos"], float) + np.array(t, float) * float(_p.extra["thick"]) / 2]]
        UNIT[sg] = {"axle": ax, "gear": gr, "wheel": wh, "bush": bu}
wheel_unit_step()

def to_side_unit(sg, S, until):
    # 바퀴 묶음은 축이 위(+y)로 서도록 옆자리(x=100, z=±150)에서 따로 만든다
    Rs = Rx(-90) if sg > 0 else Rx(90)    # 바깥(±z) → +y
    Cf = np.array([0, 25, sg * 55.0]); Cs = np.array([110.0, 40.0, sg * 47.0])
    for k, pt in S.items():
        fm = pt.extra.get("faceMarks")   # 링 = 끝 − 방향×두께/2 가 구멍 중심에 오는 면 점(final 좌표)도 같은 변환으로 옆자리로 옮긴다
        to_side(pt, Rs, Cf, Cs, until, (0, 0, sg))
        if fm: pt.extra["faceMarks"] = [rnd(Rs @ (np.array(m, float) - Cf) + Cs) for m in fm]

# ── 7·8 ── 바퀴 묶음을 벽에 끼우고 안쪽에 부시
def wheel_mount_step(sg, no):
    st = A.step(f"[교재 {no}] 바퀴 묶음의 축을 벽 뒤쪽 끝 구멍(15번째 열, 가운데 줄)에 끼우고, 안쪽 축 끝에 부시를 끼워 고정해요.")
    inner = st.place("부시", ori("+x", "+z" if sg > 0 else "-z"), (0, 25, sg * 32.25), recv=True, dir=[0, 0, -sg], hover=22, thick=5.5, joinOrder=2, marks=[[0, 25, sg * 22.5]], faceMarks=[[0, 25, sg * 29.5]])   # 꼬리 = 축 안쪽 끝, 링 = 끝 − 두께/2 가 부시 구멍 중심 (spinner 14번과 같은 방식)
    return inner
inner_R = wheel_mount_step(-1, 7)
inner_L = wheel_mount_step(+1, 8)
for sg in (+1, -1):
    U = UNIT[sg]
    to_side_unit(sg, U, 8 if sg > 0 else 7)
    if sg > 0:
        for _p in U.values(): _p.extra["hideAt"] = [7]; _p.extra["store"] = "보관 중(왼쪽 바퀴 묶음 — 책 7번에는 안 보임)"   # 책 7번은 오른쪽 바퀴만 보인다
    U["axle"].extra["settleMarks"] = [[0, 25, sg * 50]]
    for _p in U.values(): _p.extra["settleHover"] = 90   # 책 7·8번: 바퀴 묶음이 벽에서 멀리 떠 있고 긴 초록 선으로 벽 구멍에 간다

# ── 9 ── 윗판: 흰 59프레임은 모터 위 돌기에, 검은 39프레임은 블록 위 끝 돌기에
st9 = A.step("[교재 9] 모터 위쪽 돌기 4개에 59프레임(흰색)을, 뒤쪽 블록 위 끝 돌기 2개에 39프레임(검정)을 덮어요.")
Rp = ori("+z", "+y")
wt = st9.recv("59프레임", Rp, {"h38": (SIDES[1]["motor"], "p5"), "h36": (SIDES[1]["motor"], "p6"), "h8": (SIDES[-1]["motor"], "p5"), "h6": (SIDES[-1]["motor"], "p6")}, hover=85)   # 책 9번: 흰 판이 모터 위 돌기에서 높이 떠 있고 긴 초록 선으로 간다(높이는 책에서 못 읽어 ⚠ 추정)
bt = st9.recv("39프레임", Rp, {"h25": (SIDES[1]["block"], "p1"), "h1": (SIDES[-1]["block"], "p1")}, hover=85)

# ── 10 ── 뒤판
st10 = A.step("[교재 10] 39프레임을 뒤쪽 두 블록의 뒤쪽 돌기(위·아래 줄)에 끼워 뒤판을 세워요.")
rear = st10.recv("39프레임", ori("+z", "+x"), {"h27": (SIDES[1]["block"], "p3"), "h25": (SIDES[1]["block"], "p5"), "h3": (SIDES[-1]["block"], "p3"), "h1": (SIDES[-1]["block"], "p5")}, hover=75)

# ── 11~14 ── 팔(왼쪽 → 오른쪽): 3단블록 2개를 벽 바깥에 꽂고, 37프레임·빨간 17프레임
ARM = {}
def arm_steps(sg, no_a, no_b):
    S = SIDES[sg]; w = S["wall"]
    Rb = ori("+y", "+x") if sg > 0 else ori_z("+y", "+z")
    st = A.step(f"[교재 {no_a}] 3단블록 2개를 벽 바깥 면(앞에서 1번째·7번째 열)에 돌기 3개씩 꽂고, 바깥 돌기에 37프레임(위·아래 줄)을 끼워요.")
    blks = []
    for x in (-140, -80):
        b = st.attach("3단블록", Rb, {"p3": (w, (x, 35, sg * 47.5)), "p4": (w, (x, 25, sg * 47.5)), "p5": (w, (x, 15, sg * 47.5))}, hover=0.01, noGuide=True)   # 책 11번: 3단블록은 벽에 이미 끼워진 채 이름표만 있고 화살표는 37프레임 쪽 4개뿐
        b.extra.pop("dir", None); b.extra.pop("marks", None)   # 화살표·떠 있음 없이 벽에 끼운 채(책 그림)
        blks.append(b)
    _hr = ("h1", "h3") if sg > 0 else ("h3", "h1")   # 뒤집힌 쪽(sg<0)은 줄 번호가 반대
    pl = st.recv("37프레임", ori("+x", "+z" if sg > 0 else "-z"), {_hr[0]: (blks[0], "p7"), _hr[1]: (blks[0], "p8"), "h" + str(18 + int(_hr[0][1:])): (blks[1], "p7"), "h" + str(18 + int(_hr[1][1:])): (blks[1], "p8")}, hover=55, joinOrder=2)
    st2 = A.step(f"[교재 {no_b}] 빨간 17프레임 2개를 블록 위·아래 끝 돌기에 끼워요.")
    top = st2.recv("17프레임", ori("+x", "+y"), {"h1": (blks[0], "p1"), "h7": (blks[1], "p1")})
    bot = st2.recv("17프레임", ori("+x", "+y"), {"h1": (blks[0], "p2"), "h7": (blks[1], "p2")}, hover=22)   # 사용자 2026-11-09: 아래 프레임이 너무 가까워 위 프레임처럼 띄우고, 바닥 아래로 내려가는 만큼 화면 전체를 올린다(floor_lift)
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
    b2.append(b); HEAD.append(b)

s16 = hs("[교재 16] 판 가운데 줄 양옆(위에서 5번째 줄, 양쪽 끝에서 2번째 구멍)에 리벳 2개를 꽂고, 1열브라켓 2개를 그 위에 얹어요. 브라켓 세로 판이 판 밖으로 나와요(귀).")
ears = []
for z, Rbr in ((20, np.array(ori("-y", "-x")) if False else None), (-20, None)): pass
RBR = {+1: np.column_stack([(0, -1, 0), (-1, 0, 0), (0, 0, -1)]), -1: np.column_stack([(0, 1, 0), (-1, 0, 0), (0, 0, 1)])}
for sg in (+1, -1):
    rv = s16.attach("리벳", ori("+y", "+x"), {"p2": (PA, (-62.5, 90, sg * 20))}, rivet=True); HEAD.append(rv)   # 책 16번: 리벳도 결합 전(판 위로 떠서 내려온다)
    br = s16.recv("1열브라켓", RBR[sg], {"h1": (rv, "p1")}, joinOrder=2, hover=55); HEAD.append(br)   # 책 16번: 리벳도 브라켓도 결합 전 모습(리벳 → 브라켓 순서)(리벳 결합 뒤 브라켓 순서라 리벳보다 더 높이 뜬다 — hover 55)   # 책 16번: 브라켓은 이미 꽂힌 리벳 위에 떠서 내려온다(리벳 → 브라켓 순서); 위치는 리벳 돌기에서 계산; ears.append(br)

s17 = hs("[교재 17] 앞판 59프레임을 블록 위쪽 돌기 6개(3단블록 2개, 2단블록 2개씩)에 얹어 샌드위치처럼 덮어요.")
PB = s17.recv("59프레임", Ra, {"h42": (b3, "p3"), "h44": (b3, "p5"), "h6": (b2[0], "p5"), "h1": (b2[0], "p6"), "h10": (b2[1], "p5"), "h5": (b2[1], "p6")}, hover=70); HEAD.append(PB)

s18 = hs("[교재 18] 앞판에 리벳 6개를 꽂고, 검은 35프레임(위 줄 3개·모서리 4곳)과 빨간 15프레임(2번째·4번째 구멍 2곳)을 얹어요(아래에서 2~5번째 줄).")
rv4 = [s18.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, y, z))}, rivet=True) for (y, z) in ((70, 20), (70, -20), (90, 20), (90, -20))]
rv2 = [s18.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, 60, z))}, rivet=True) for z in (10, -10)]
Rf = ori("+z", "-x") if False else np.column_stack([(0, 0, 1), (-1, 0, 0), (0, -1, 0)])  # 35프레임: 길이 z, 구멍축 −x... (구멍축은 x, 줄 방향 −y)
black35 = s18.recv("35프레임", Rf, dict(zip(["h15", "h3", "h13", "h1"], [(r, "p1") for r in rv4])), hover=85, joinOrder=2)
red15 = s18.recv("15프레임", np.column_stack([(0, 0, 1), (-1, 0, 0), (0, -1, 0)]), dict(zip(["h4", "h2"], [(r, "p1") for r in rv2])), hover=55, joinOrder=2)
HEAD += rv4 + rv2 + [black35, red15]

s19 = hs("[교재 19] 리벳 1개를 앞판 가운데(위에서 6번째 줄)에 꽂고, 눈블록 2개를 리벳 줄에서 두 줄 뒤(8번째 줄, 리벳 열의 양옆 한 칸씩)에 꽂아요.")
rv1 = s19.attach("리벳", ori("+y", "+x"), {"p2": (PB, (-77.5, 100, 0))}, rivet=True, openEnd=True)   # 사용자 지시: 리벳은 항상 결합 전(구멍 위에 뜬) 모습
eyes = [s19.attach("눈블록", ori("+y", "+x"), {"p1": (PB, (-77.5, 120, z))}) for z in (10, -10)]   # 책 19번 확대: 리벳 줄과 눈 줄 사이에 구멍 줄 1개(두 줄 뒤)
HEAD += [rv1] + eyes

s20 = hs("[교재 20] 3단블록 윗면 구멍 양옆 2곳에 리벳 2개를 꽂고, 35프레임(검정)을 머리 위쪽 끝에 얹어요.")
capR = np.column_stack([(0, 0, 1), (0, 1, 0), (-1, 0, 0)])    # 35프레임 눕힘: 길이 z, 구멍축 y
rv_top = [s20.attach("리벳", ori("+x", "+y"), {"p1": (b3, hid)}, rivet=True) for hid in ("h1", "h3")]
cap = s20.recv("35프레임", capR, dict(zip(["h5", "h11"], [(r, "p2") for r in rv_top])))
HEAD += rv_top + [cap]

s21 = hs("[교재 21] 35프레임 위 3곳(1·3·5번째 구멍)에 리벳 3개를 꽂고, 빨간 15프레임을 얹으면 머리 완성이에요.")
rv3 = [s21.attach("리벳", ori("+x", "+y"), {"p1": (cap, (-70, 137.5, z))}, rivet=True) for z in (-20, 0, 20)]
red_top = s21.recv("15프레임", np.column_stack([(0, 0, 1), (0, 1, 0), (-1, 0, 0)]), dict(zip(["h1", "h3", "h5"], [(r, "p2") for r in rv3])))
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
Rbd = rot_y(180) @ Rbd   # 책 23·24: 주황 버튼 줄이 뒷판에서 먼 쪽(오른쪽·앞)에, 핀 헤더가 뒷판 쪽에 오도록 위에서 본 방향을 180° 돌린다(돌기 2개는 중심 대칭이라 같은 구멍에 그대로 꽂힌다, 사용자 지적 2026-11-03)
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
pole = s26.recv("115프레임", np.column_stack([(0, -1, 0), (1, 0, 0), (0, 0, 1)]), dict(zip(["h1", "h3", "h5"], [(r, "p1") for r in rvf])))
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

floor_lift(A, 14)   # 14번도 같은 arm_steps 함수라 같이 낮아진다(12번과 같은 이유)
floor_lift(A, 12)   # 12번 아래 프레임 띄운 자리가 바닥 아래면 화면 전체를 그만큼 올려 보여 준다(G24)
import stepchecks; stepchecks.apply(A, "soccer")
# ── 04 창고 정리(1차) — 책 55~60쪽을 1→27번 순서로 보며 정했다(2026-11-09, 그림 모양으로 판단=추정).
#   1~14번 몸통(모터·벽·바퀴·팔 틀)은 창고 1 / 15~21번 머리(59프레임 판 위 블록·브라켓·눈블록)는 따로 만들어 창고 2 → 22번에 몸통에 합침 / 23~25번 메인보드·블록은 창고 1 / 26번 깃발(35프레임·115프레임)은 창고 2 → 27번에 합침.
_SLOT_SC = {**{i: 1 for i in range(1, 15)}, **{i: 2 for i in range(15, 22)}, **{i: 1 for i in range(22, 26)}, 26: 2, 27: 1}
for _i, _sl in _SLOT_SC.items(): A.steps[_i - 1].kw["slot"] = _sl
_HIST_SC = {15: "📦 몸통(1~14번)을 창고 1에 두고, 창고 2에서 머리 판(59프레임)과 블록 조립을 새로 시작(그림으로 판단)",
            22: "창고 2의 머리 조립(15~21번)을 가져와 창고 1의 몸통에 합쳐요(그림으로 판단)",
            26: "📦 몸(1~25번)을 창고 1에 두고, 창고 2에서 깃발(35프레임·리벳·115프레임)을 새로 시작(그림으로 판단)",
            27: "창고 2의 깃발(26번)을 가져와 창고 1의 몸에 합쳐요(그림으로 판단)"}
for _i, _h in _HIST_SC.items(): A.steps[_i - 1].kw["history"] = _h
# ── 03 번호별 사용 부품(교재 그림에서 읽음, 합계 = LIST: 리모컨 1 은 3D 모델이 없어 제외)
USED = {1: "315프레임 2, DC모터 2", 2: "리벳 4 (그림 옆 4), 3단블록 2", 3: "59프레임 1, 29프레임 1", 4: "작은기어 1, T축 1", 5: "작은기어 1, T축 1", 6: "축 2, 큰기어 2, 작은바퀴 2, 부시 2",
        7: "부시 1", 8: "부시 1", 9: "59프레임 1, 39프레임 1", 10: "39프레임 1", 11: "3단블록 2, 37프레임 1", 12: "17프레임 2", 13: "3단블록 2, 37프레임 1", 14: "17프레임 2",
        15: "59프레임 1, 3단블록 1, 2단블록 2", 16: "리벳 2 (그림 옆 2), 1열브라켓 2", 17: "59프레임 1", 18: "리벳 6 (그림 옆 6), 35프레임 1, 15프레임 1", 19: "리벳 1 (그림 옆 1), 눈블록 2",
        20: "리벳 2 (그림 옆 2), 35프레임 1", 21: "리벳 3 (그림 옆 3), 15프레임 1", 22: "없음(합치는 단계)", 23: "메인보드 1", 24: "없음(메인보드 왼쪽·오른쪽 DC모터 전선 연결)",
        25: "3단블록 1", 26: "리벳 3 (그림 옆 3), 35프레임 1, 115프레임 1", 27: "없음(합치는 단계)"}
for _i, _u in USED.items():
    _pp = A.steps[_i - 1].note.split("\n▣ 사용 부품:")
    _tail = ("\n" + _pp[1].split("\n", 1)[1]) if len(_pp) > 1 and "\n" in _pp[1] else ""
    A.steps[_i - 1].note = _pp[0] + "\n▣ 사용 부품: " + _u + _tail
A.save_links()
A.steps[0].cam = (0.82, 0.70); A.steps[0].camSrc = "fit"   # 1번: 격자 45점 axes_fit 0.44px(P 판, roll −0.2°)
A.steps[1].cam = (0.85, 0.72); A.steps[1].camSrc = "fit"   # 2번: 격자 45점 axes_fit 0.48px(P 판, roll −2.1°)
A.steps[2].cam = (1.08, 0.88); A.steps[2].camSrc = "fit"   # 3번: 흰 판 W 격자 45점 axes_fit 0.73px(검은 판 B 0.36px 와 θ1.02·φ0.81 로 근접, roll 0.8°)
A.steps[3].cam = (0.69, 1.17); A.steps[3].camSrc = "fit"   # 4번: 벽 W 격자 45점 axes_fit 1.32px(holefit DoG 22/45, roll −0.5°)
A.steps[4].cam = (2.59, 1.18); A.steps[4].camSrc = "fit"   # 5번: 오른쪽 벽 W 격자 45점 axes_fit 0.36px(holefit 어두운판 22/45, roll −2.4°)
A.steps[5].cam = (1.66, 0.88); A.steps[5].camSrc = "fit"   # 6번: 판 없는 분해도 — mkfit3d 링 중심 7점 PnP 1.93px(두 묶음 링·축 아래 끝, 띄움 간격은 책에 맞춰 hover 68.5·103.5·131.5)
A.steps[5].kw["hideMade"] = {str(_i): "1~5번 조립(몸체, 창고 1)" for _i in range(1, 6)}   # 책 6번은 바퀴 묶음만 보인다 — 새 조립(바퀴 묶음)을 만드는 동안 앞 몸체는 숨긴다(A3)
A.steps[6].cam = (2.47, 1.17); A.steps[6].camSrc = "fit"   # 7번: 오른쪽 벽 W 격자 45점 axes_fit 0.59px(holefit 어두운판, roll 0.6°)
A.steps[7].cam = (0.79, 1.21); A.steps[7].camSrc = "fit"   # 8번: 왼쪽 벽 W 격자 45점 axes_fit 0.60px(holefit 어두운판, roll 3.9°)
A.steps[8].cam = (0.82, 1.11); A.steps[8].camSrc = "fit"   # 9번: 흰 판 W 격자 45점 axes_fit 1.01px(holefit 31/45, roll 0.1°)
A.steps[9].cam = (0.92, 0.99); A.steps[9].camSrc = "fit"   # 10번: 뒤판 W 격자 27점 axes_fit 0.33px(holefit 어두운판, roll −0.6°)
A.steps[10].cam = (0.83, 1.19); A.steps[10].camSrc = "fit"   # 11번: 37프레임 W 격자 21점 axes_fit 0.80px(holefit DoG 11/21, 슬릿이 구멍 가장자리라 ⚠ 8번 0.79·1.21 과 일치해 채택, roll 4.7°)
A.steps[11].cam = (0.98, 1.09); A.steps[11].camSrc = "fit"   # 12번: 37프레임 W 격자 21점 axes_fit 1.42px(holefit DoG 12/21 평균 1.28px)
A.steps[12].cam = (2.19, 1.14); A.steps[12].camSrc = "fit"   # 13번: 오른쪽 37프레임 W 격자 21점 axes_fit 1.17px(holefit DoG 11/21 0.74px, 모서리는 링 구멍 4개에서 역산, roll 6.7°)
A.steps[13].cam = (2.15, 1.10); A.steps[13].camSrc = "fit"   # 14번: 37프레임 W 격자 21점 axes_fit 0.70px(holefit DoG 12/21 1.06px)
A.steps[14].cam = (-1.08, 0.71); A.steps[14].camSrc = "fit"   # 15번: 흰 59프레임 W 격자 45점 axes_fit 1.32px(holefit DoG 23/45 1.91px, +X +Z; 거울 +X −Z 는 2px 초과로 탈락)
A.steps[15].cam = (-1.12, 0.59); A.steps[15].camSrc = "fit"   # 16번: 구멍 12점 mkfit3d 3.63px(⚠ holefit 불가, --허용 4)
A.steps[16].cam = (-0.93, 0.87); A.steps[16].camSrc = "fit"   # 17번: 위 59프레임 W 격자 45점 axes_fit 0.94px(holefit DoG 30/45 0.48px)
A.steps[17].cam = (-0.91, 0.71); A.steps[17].camSrc = "fit"   # 18번: 위 흰 59프레임 W 격자 45점 axes_fit 1.52px(holefit DoG 30/45 1.99px)
A.steps[18].cam = (-0.91, 0.71); A.steps[18].camSrc = "guess"   # 19번: 책 19번이 18번과 같은 시점(검은·빨간 판이 앞 왼쪽)이라 18번 값으로 임시 — ⚠ 19번 격자 axes_fit 으로 다시 맞춘다
for _k in range(14, 21): A.steps[_k].kw["hideMade"] = {str(_i): "1~14번 조립(몸체, 창고 1)" for _i in range(1, 15)}   # 책 15~21번은 머리만 보인다 — 머리는 따로 조립해 22번에 몸체에 올린다(A3)
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("soccer_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    entry = js_entry(A)
    open("soccer_entry.js", "w", encoding="utf-8").write(entry)
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
