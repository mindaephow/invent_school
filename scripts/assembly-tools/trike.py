# 3륜바이크(교재 46~51쪽) 11~29단계 — 1~10단계(저장소 데이터)는 그대로 두고 asmlib 로 이어서 만든다.
# 좌표: 1~10단계와 같은 세계 좌표(바닥 y=0, 몸체 위판 윗면 y=45, 위판 z −155~−75, 포크가 −z 쪽).
import json, sys
import numpy as np
from asmlib import *
from trike_base import load_existing, final_parts

EX = load_existing()
BASE = EX["steps"][:10]
A = Asm(EX["id"], EX["chapter"], EX["book"], camera=EX["camera"], listNote=EX.get("listNote", ""))
A.steps = []          # 새 단계만 담는다(1~10단계는 저장소 데이터를 그대로 붙인다)
A.parts = []
_, old = final_parts(EX)
OLD = {}
for k, pt in old: OLD.setdefault((pt.n, k), []).append(pt)
def old1(n, k, i=0): return OLD[(n, k)][i]

UP = (0, 1, 0)
IDX = {}   # 단계 번호 보정(새 단계 번호 = 10 + 순서)
def step(note, **kw):
    s = A.step(note, **kw); s.index = 10 + len(A.steps); return s

# ───────── 11 ── 모터 윗돌기·블록 윗돌기 위에 윗판 덮기 ─────────
motorL, motorR = old1("DC모터", 9, 0), old1("DC모터", 9, 1)
blk8 = old1("2단블록", 8); blkL, blkR = old1("3단블록", 9, 0), old1("3단블록", 9, 1)   # 교재 9: 모터 옆 유닛의 블록은 3단블록(돌기 3개, 책 그림·LIST 3단블록 9)
s11 = step("[교재 11] 39프레임(검정)을 블록 윗돌기에, 59프레임(흰색)을 모터 윗돌기 4개에 덮어요.")
Rtop = np.eye(3)                                            # 39프레임·59프레임: 긴 쪽이 x
black39 = s11.recv("39프레임", Rtop, [(blk8, "p5"), (blk8, "p6"), (blkL, "p1"), (blkR, "p1")], p=(0, 37.5, -140))
white59 = s11.recv("59프레임", Rtop, [(motorL, "p5"), (motorL, "p6"), (motorR, "p3"), (motorR, "p4")], p=(0, 37.5, -100))

# ───────── 머리: 머리 좌표(M)로 만든다 ─────────
# 머리 로컬: X=j(폭, 구멍 0~4), Y=위(눈 쪽), Z=i(길이, 구멍 0~8, 눈 반대쪽 끝=아래). 최종: 머리가 검정 39프레임 위에 서고 눈이 −z(포크 쪽)를 본다.
M = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]], float)
T0 = np.array([0, 85, -130.0])
def Lp(x, y, z): return M @ np.array([x, y, z], float) + T0
def LR(cols): return M @ np.column_stack(cols)
XL, YL, ZL = (1, 0, 0), (0, 1, 0), (0, 0, 1)
def neg(v): return tuple(-a for a in v)
def hx(j): return -20 + 10 * j
def hz(i): return -40 + 10 * i
R_flat59 = LR([ZL, YL, neg(XL)])                           # 59프레임·25프레임: 긴 쪽이 Z(i), 구멍 축 Y
R_rivet = LR([XL, YL, ZL])
R_blk = LR([ZL, XL, YL])                                    # 블록 눕힘: 긴 쪽 Z, 돌기 면이 ±Y
HEAD = []
def to_build(pt, at, move_marks=None, move_dir=(0, 1, 0), hover=30):
    """머리 부품: 최종(몸체 위) 자세로 계산한 것을 '따로 만드는 자세(side 좌표)'로 바꿔 p·r·marks·dir 로 두고, at 단계에서 최종 자세로 옮겨 붙게(move) 한다."""
    Rs = M.T; Cf = T0; Cs = np.array(BUILD_AT)
    P = lambda q: Rs @ (np.array(q, float) - Cf) + Cs
    fin_p, fin_R = pt.p.copy(), pt.R.copy()
    ex = pt.extra
    if "marks" in ex: ex["marks"] = [rnd(P(m)) for m in ex["marks"]]
    if "dir" in ex: ex["dir"] = rnd(Rs @ np.array(ex["dir"], float))
    pt.p = P(fin_p); pt.R = Rs @ fin_R
    mv = {"at": at, "p": rnd(fin_p), "r": R_to_euler(fin_R), "dir": list(move_dir), "hover": hover}
    if move_marks: mv["marks"] = move_marks
    ex["move"] = mv
BUILD_AT = (150.0, 0.0, -110.0)

# 12 ── 흰 59프레임 H1 에 리벳 4개, 25프레임 2개
s12 = step("[교재 12] 흰 59프레임(머리 바닥)에 리벳 4개를 꽂고, 25프레임 2개를 그 위에 얹어요: 리벳은 한쪽 짧은 끝 줄의 양끝(1·5번째 구멍)과 4번째 줄의 2·4번째 구멍이에요.")
s13 = step("[교재 13] 1열브라켓 2개의 세로 판 윗구멍에 리벳을 하나씩 꽂아요(리벳 홈 방향 주의, 리벳 끝이 안쪽을 봐요).")
s14 = step("[교재 14] 흰 59프레임 끝 줄 양끝(6번째 줄의 1·5번째 구멍)에 리벳 2개를 꽂고, 13의 브라켓을 발바닥 안쪽 구멍으로 얹어요. 세로 판이 판 밖으로 나와요.")
H1 = s12.place("59프레임", R_flat59, Lp(0, 2.5, 0))
riv12 = [s12.attach("리벳", M, {"p1": (H1, Lp(hx(j), 5, hz(i)))}, rivet=True) for (i, j) in ((0, 0), (3, 1), (0, 4), (3, 3))]
P1 = s12.recv("25프레임", R_flat59, [(riv12[0], "p2"), (riv12[1], "p2")], p=Lp(-15, 7.5, -20))
P2 = s12.recv("25프레임", R_flat59, [(riv12[2], "p2"), (riv12[3], "p2")], p=Lp(15, 7.5, -20))
# 14 리벳(바닥판 6번째 줄 양끝) → 브라켓 발바닥 안쪽 구멍
riv14 = [s14.attach("리벳", M, {"p1": (H1, Lp(hx(j), 5, hz(5)))}, rivet=True) for j in (0, 4)]
RBL = LR([neg(ZL), YL, XL]); RBR = LR([ZL, YL, neg(XL)])          # 브라켓: 세로 판이 밖(왼쪽 −X, 오른쪽 +X), 발바닥이 안쪽
brL = s13.recv("1열브라켓", RBL, {"h2": (riv14[0], "p2")}, joinOrder=2)
brR = s13.recv("1열브라켓", RBR, {"h2": (riv14[1], "p2")}, joinOrder=2)
# 13 리벳: 세로 판 윗구멍(h4)에, 리벳 끝이 안쪽으로 나오게(리벳 몸통 가운데가 판 안쪽 면)
RRL = LR([YL, XL, neg(ZL)]); RRR = LR([YL, neg(XL), ZL])
rvL = s13.attach("리벳", RRL, {"p1": (brL, "h4")}, rivet=True, openEnd=True)
rvR = s13.attach("리벳", RRR, {"p1": (brR, "h4")}, rivet=True, openEnd=True)

HEAD += [H1] + riv12 + [P1, P2]

# 15 ── 3단블록 1 + 2단블록 2 (판 위에 눕혀 꽂는다: 아래 돌기가 구멍에)
s15 = step("[교재 15] 3단블록 1개를 두 검정 판 사이(가운데 줄)에, 2단블록 2개를 판 끝 양옆 줄(7·8번째 줄)에 눕혀 꽂아요: 블록 아래 돌기가 흰 판 구멍에 들어가요.")
B3 = s15.attach("3단블록", R_blk, {"p6": (H1, Lp(hx(2), 5, hz(2))), "p7": (H1, Lp(hx(2), 5, hz(3))), "p8": (H1, Lp(hx(2), 5, hz(1)))}, hover=22)
B2 = [s15.attach("2단블록", R_blk, {"p6": (H1, Lp(hx(j), 5, hz(7))), "p5": (H1, Lp(hx(j), 5, hz(8)))}, hover=22) for j in (0, 4)]

# 16 ── 위 59프레임 덮기
s16 = step("[교재 16] 59프레임을 위에서 덮어요: 3단블록과 2단블록의 윗돌기가 위판 구멍에 들어가요.")
TOP = s16.recv("59프레임", R_flat59, [(B3, "p3"), (B3, "p5"), (B2[0], "p4"), (B2[0], "p3"), (B2[1], "p4"), (B2[1], "p3")], p=Lp(0, 17.5, 0), hover=22)

# 17 ── 리벳 8 + 35프레임 + 빨간 15프레임 2
s17 = step("[교재 17] 위판에 리벳 8개를 꽂고, 검정 35프레임(끝 줄 모서리 4곳)과 빨간 15프레임 2개(2·4번째 구멍)를 그 위에 얹어요.")
rv35 = [s17.attach("리벳", M, {"p1": (TOP, Lp(hx(j), 20, hz(i)))}, rivet=True) for (i, j) in ((0, 0), (2, 0), (0, 4), (2, 4))]
rvRed = [s17.attach("리벳", M, {"p1": (TOP, Lp(hx(j), 20, hz(i)))}, rivet=True) for (i, j) in ((6, 1), (6, 3), (7, 1), (7, 3))]
R35 = LR([XL, YL, ZL])
B35 = s17.recv("35프레임", R35, [(rv35[0], "p2"), (rv35[1], "p2"), (rv35[2], "p2"), (rv35[3], "p2")], p=Lp(0, 22.5, hz(1)), hover=22)
red = [s17.recv("15프레임", R35, [(rvRed[2 * k], "p2"), (rvRed[2 * k + 1], "p2")], p=Lp(0, 22.5, hz(6 + k)), hover=22) for k in (0, 1)]

# 18 ── 리벳 1 + 눈블록 2
s18 = step("[교재 18] 35프레임 가운데 구멍에 리벳 1개(코)를 꽂고, 눈블록 2개를 그 윗줄 양옆 구멍에 꽂아요.")
nose = s18.attach("리벳", M, {"p1": (B35, Lp(hx(2), 25, hz(2)))}, rivet=True, openEnd=True)
Reye = LR([XL, neg(YL), neg(ZL)])
eyes = [s18.attach("눈블록", Reye, {"p1": (B35, Lp(hx(j), 25, hz(1)))}) for j in (1, 3)]

# 19 ── 머리를 몸체에 세운다
s19 = step("[교재 19] 머리를 뒤집어 세워 몸체 위 검정 39프레임에 올려요: 2단블록 아래 끝돌기 2개가 39프레임 구멍에 꽂혀요.")
HEADPARTS = [H1] + riv12 + [P1, P2, B3] + B2 + [TOP] + rv35 + rvRed + [B35] + red + [nose] + eyes + riv14 + [brL, brR, rvL, rvR]
for pt in HEADPARTS:
    mm = None
    if pt in B2:
        sm = settle_marks(pt, [black39])
        mm = sm
    to_build(pt, 19, move_marks=mm)

# 브라켓 묶음(13)은 따로 만들었다가 14에서 머리에 붙는다: 13 에서는 머리 옆(+z 쪽)에 따로 있다가 14 에 제자리(머리 만드는 자리)로 들어온다
for pt in (brL, brR, rvL, rvR):
    off = np.array([0, 0, 100.0])
    pt.extra["side"] = {"p": rnd(pt.p + off), "r": R_to_euler(pt.R), "until": 14}
    pt.extra["settleDir"] = [0, 1, 0]
    if pt in (brL, brR):                       # 브라켓: 13 에서는 그냥 놓이고(안내 없음), 14 에서 리벳 끝(머리 자리)으로 내려오며 화살표가 따라간다
        pt.extra["settleMarks"] = pt.extra.pop("marks"); pt.extra.pop("dir", None)
    else:                                      # 세로 판 리벳: 13 에서 브라켓(옆자리) 구멍으로 들어가므로 안내를 옆자리 기준으로 옮긴다
        pt.extra["marks"] = [rnd(np.array(m) + off) for m in pt.extra["marks"]]

# ───────── 20~25 ── 앞바퀴 팔(115프레임 2장 + 90도 프레임·3단블록 유닛 2개 + 손잡이 + 작은바퀴) ─────────
# 사용자 확인(2026-10-02): 팔을 기둥 위쪽의 두 3단블록 사이(틈 10mm = 팔 두께 10)에 끼우고, 블록 구멍과 팔 구멍을 맞춰 그 사이로 축을 끼운다(교재 23).
# 팔 좌표(로컬): x=길이 u(바퀴 쪽 끝 구멍 k=1 → 위쪽 끝 구멍 k=15, 구멍 간격 10), y=너비(손잡이 쪽 +), z=두께(구멍축). 최종 자세: 두께가 세계 x(−x 쪽이 로컬 +z),
# 축 구멍 k=12 가 기둥 위쪽 블록 구멍 h2 와 같은 자리(83.64, −223.44), 바퀴가 바닥에 닿도록 팔이 기울어진다(앞바퀴 가운데 높이 21 = 바퀴 반지름 25 − 4).
BUILD2 = np.array([150.0, 21.0, -260.0])         # 따로 만드는 자리(20~22)
colBlk = old1("3단블록", 1, 0)                     # 기둥 위쪽 3단블록(x=+10), 반대쪽은 인덱스 1(x=−10)
PIV = np.array([0.0, 83.64, -223.439]) + 10 * np.array([0.0, 0.7071, -0.7071])   # 기둥 위쪽 3단블록 구멍 h1(위쪽 끝 쪽, 사용자가 표시한 1번 홀) — h2 에서 기둥 방향으로 10mm 위
K_PIV = 12
SIN = (PIV[1] - 21.0) / (10 * (K_PIV - 1))
COS = float(np.sqrt(1 - SIN ** 2))
Ua = np.array([0, SIN, COS]); Wa = np.array([0, COS, -SIN]); Za = np.array([-1.0, 0, 0])
Ma = np.column_stack([Ua, Wa, Za])               # 팔 로컬 → 세계
def hk(k): return -70 + 10 * (k - 1)
Q0 = np.array([hk(K_PIV), 0, 0.0])
def Af(u, y, z): return PIV + Ma @ (np.array([u, y, z], float) - Q0)
def AfR(R): return Ma @ np.array(R, float)
def to_build2(pt, at):
    """팔 부품: 최종(몸체에 건) 자세로 계산한 것을 따로 만드는 자세로 바꿔 p·r·marks·dir 로 두고, at 단계에서 최종 자세로 옮겨 붙게(move) 한다."""
    P = lambda q: BUILD2 + Ma.T @ (np.array(q, float) - PIV) + Q0
    fin_p, fin_R = pt.p.copy(), pt.R.copy()
    ex = pt.extra
    for k in ("marks", "settleMarks"):
        if k in ex: ex[k] = [rnd(P(m)) for m in ex[k]]
    for k in ("dir", "settleDir"):
        if k in ex: ex[k] = rnd(Ma.T @ np.array(ex[k], float))
    pt.p = P(fin_p); pt.R = Ma.T @ fin_R
    ex["move"] = {"at": at, "p": rnd(fin_p), "r": R_to_euler(fin_R), "dir": [0, 1, 0], "hover": 30}
R_A = AfR(ori("+x", "+z"))
s20 = step("[교재 20] 115프레임 2개를 마주 보게 놓고, 한쪽 구멍 2곳(8번째·15번째)에 리벳을 꽂아 다른 한쪽과 붙여요.")
A1 = s20.place("115프레임", R_A, Af(0, 0, -2.5))
rvA = [s20.attach("리벳", R_A, {"p1": (A1, Af(hk(k), 0, -2.5))}, rivet=True) for k in (8, 15)]
A2 = s20.recv("115프레임", R_A, [(r, "p2") for r in rvA], p=Af(0, 0, 2.5), hover=22)
s21 = step("[교재 21] 90도 프레임에 2단블록을 돌기 2개로 끼워요: 모서리가 아닌 두 구멍에 들어가요(2개 만들어요).")
# 교재 21·22: 블록의 구멍(y)이 팔 너비 방향(위)이고, L 판은 블록의 팔 끝 쪽(+u) 옆면에 붙는다 — L 의 모서리(세로 다리)가 팔에서 먼 쪽, 가로 다리 3칸이 팔 쪽으로 뻗어 블록 돌기 3개를 받고, 세로 다리는 아래(−y)로 내려간다. 두 유닛은 팔 양쪽(±z)에서 거울 모양.
RL1 = AfR(np.column_stack([(0, -1, 0), (-1, 0, 0), (0, 0, -1)])); RL2 = AfR(np.column_stack([(0, -1, 0), (1, 0, 0), (0, 0, 1)]))
L1 = s21.place("90도 프레임", RL1, Af(67.5, -10, 20)); L2 = s21.place("90도 프레임", RL2, Af(67.5, -10, -20))
RB1 = AfR(np.column_stack([(0, 0, 1), (0, -1, 0), (1, 0, 0)])); RB2m = AfR(np.column_stack([(0, 0, -1), (0, 1, 0), (1, 0, 0)]))
U1 = s21.attach("2단블록", RB1, {"p2": (A2, Af(hk(14), 0, 2.5)), "p3": (L1, "h3"), "p4": (L1, "h2")}, hover=22)
U2 = s21.attach("2단블록", RB2m, {"p2": (A1, Af(hk(14), 0, -2.5)), "p3": (L2, "h3"), "p4": (L2, "h2")}, hover=22)
s22 = step("[교재 22] 유닛 2개의 2단블록 끝돌기를 팔의 14번째 구멍에 양쪽에서 끼워요.")
s23 = step("[교재 23] 팔을 기둥 위쪽 두 3단블록 사이에 끼우고(팔 12번째 구멍을 블록 구멍에 맞춰요), 그 사이로 축을 끼운 뒤 양쪽 끝을 부시 2개로 고정해요.")
# 23 ── 축(65)을 두 블록 구멍 h2 와 팔 구멍을 지나 끼우고 부시 2개
blkL, blkR = old1("3단블록", 1, 1), old1("3단블록", 1, 0)           # x=−10, x=+10
Rax = np.column_stack([(0, 0, 1), (1, 0, 0), (0, 1, 0)])
axle23 = s23.place("축", Rax, PIV.copy(), dir=[-1, 0, 0], hover=40, pegDepth=40, marks=[rnd(PIV + np.array([-15.0, 0, 0]))])
bu23a = s23.recv("부시", Rax, [(axle23, "p1")], p=PIV + np.array([17.75, 0, 0]), hover=22)
bu23b = s23.recv("부시", Rax, [(axle23, "p1")], p=PIV + np.array([-17.75, 0, 0]), hover=22, dir=[-1, 0, 0])
bu23b.extra["marks"] = [rnd(PIV + np.array([-32.5, 0, 0]))]
# 24·25 ── 팔에 건 뒤(최종 자세)에서 손잡이·바퀴
s24 = step("[교재 24] L 프레임 세로 다리 구멍 4곳에 리벳을 꽂고, 37프레임(손잡이)을 그 위에 얹어요.")
Rrv = AfR(np.column_stack([(0, 0, 1), (1, 0, 0), (0, 1, 0)]))     # 리벳 축 = 팔 길이 방향(u)
rv24 = [s24.attach("리벳", Rrv, {"p1": (L, Af(70, y, z))}, rivet=True) for L, z in ((L1, 30), (L2, -30)) for y in (-10, -20)]
handle = s24.recv("37프레임", Rrv, [(r, "p2") for r in rv24], p=Af(72.5, -10, 0), hover=22)
s25 = step("[교재 25] 팔 끝 구멍에 축을 끼우고, 작은바퀴 2개를 양쪽 끝에 끼운 뒤 바깥쪽을 부시로 고정해요.")
axle = s25.place("축", R_A, Af(hk(1), 0, 0), dir=(-Za).tolist(), hover=40, pegDepth=40, marks=[rnd(Af(hk(1), 0, -5))])
RW = R_A
wh1 = s25.recv("작은바퀴", RW, {"h3": (axle, "p1")}, p=Af(hk(1), 0, 13), hover=30)
wh2 = s25.recv("작은바퀴", RW, [(axle, "p1")], p=Af(hk(1), 0, -13), hover=30, dir=(Ma @ np.array([0, 0, -1])).tolist())
wh2.extra["marks"] = [rnd(Af(hk(1), 0, -32.5))]
bu1 = s25.recv("부시", RW, [(axle, "p1")], p=Af(hk(1), 0, 23.75), hover=22)
bu2 = s25.recv("부시", RW, [(axle, "p1")], p=Af(hk(1), 0, -23.75), hover=22, dir=(Ma @ np.array([0, 0, -1])).tolist())
bu2.extra["marks"] = [rnd(Af(hk(1), 0, -32.5))]

armparts = [A1] + rvA + [A2, L1, L2, U1, U2]
# 유닛의 안내(marks)는 L 구멍 3곳, 합칠 때(settleMarks)는 팔 구멍 — 변환 전에 정리한다
for L, U, sg in ((L1, U1, 1), (L2, U2, -1)):
    U.extra["settleMarks"] = [U.extra["marks"][0]]; U.extra["marks"] = U.extra["marks"][1:]
    U.extra["dir"] = rnd(AfR(np.eye(3)) @ np.array([0, -1, 0]))
for pt in armparts: to_build2(pt, 23)
# 유닛은 21 에서 팔에서 떨어진 자리(옆)에서 만들고 22 에서 팔에 붙는다(side → 제자리)
for L, U, sg in ((L1, U1, 1), (L2, U2, -1)):
    off = Ma.T @ Za * 0 + np.array([0, 0, 50.0 * sg])
    for pt in (L, U):
        pt.extra["side"] = {"p": rnd(pt.p + off), "r": R_to_euler(pt.R), "until": 22}
        pt.extra["settleDir"] = [0, 0, 1 if sg > 0 else -1]
    U.extra["marks"] = [rnd(np.array(m) + off) for m in U.extra["marks"]]

# ───────── 26·27 ── 몸체 뒷바퀴(T축 + 데코바퀴) / 28 메인보드 / 29 선 연결 ─────────
def rear_wheel(no, sg):
    st = step(f"[교재 {no}] T축을 데코바퀴 가운데 구멍에 끼워 벽 구멍을 지나 모터 십자 구멍까지 꽂아요(벽 뒤쪽 가운데 줄 구멍).")
    RWh = ori("+z", "+x" if sg < 0 else "-x")
    wheel = st.place("데코바퀴", RWh, (sg * 58, 20, -90), dir=[sg, 0, 0], hover=30, marks=[[sg * 50, 20, -90]])
    t = st.attach("T축", RWh, {"p1": (wheel, "h1")}, dir=(sg, 0, 0), hover=45, pegDepth=28.6, headDown=True)
    t.extra["marks"] = [[sg * 50, 20, -90]]
    return wheel, t
rear_wheel(26, +1)
rear_wheel(27, -1)
s28 = step("[교재 28] 메인보드를 윗판(흰 59프레임) 위에 꽂아요: 보드 아래 돌기 2개가 판의 구멍 2곳에 들어가요.")
Rbd = np.eye(3)
bd_p = np.array([0, 56.25, -90.0])
board = s28.place("메인보드", Rbd, bd_p, dir=[0, 1, 0], hover=40)
board.extra["marks"] = [[0, 40, -100], [0, 40, -80]]
s29 = step("[교재 29] 메인보드 왼쪽·오른쪽 단자에 DC모터 선을 연결하면 3륜바이크 완성!", noPart=True)

CAMS = {11: (-0.6, 0.9), 12: (0.5, 0.85), 13: (0.5, 0.85), 14: (0.5, 0.85), 15: (0.5, 0.85), 16: (0.5, 0.85), 17: (0.6, 0.85), 18: (0.6, 0.85),
        19: (-0.6, 0.95), 20: (0.5, 0.9), 21: (0.5, 0.9), 22: (0.5, 0.9), 23: (-0.6, 0.95), 24: (0.5, 0.9), 25: (0.5, 0.9), 26: (0.8, 0.95), 27: (-0.8, 0.95), 28: (0.4, 1.05), 29: (0.4, 1.05)}
for k, (th, ph) in CAMS.items():
    A.steps[k - 11].cam = (th, ph); A.steps[k - 11].camSrc = "guess"

import copy
def shift_steps(steps, dy):
    """모든 y 좌표를 dy 만큼 올린다(p·marks·faceMarks·settleMarks·side·move·explode)."""
    S = copy.deepcopy(steps)
    sh = lambda q: [q[0], round(q[1] + dy, 3), q[2]]
    for st in S:
        for pt in st.get("parts", []):
            pt["p"] = sh(pt["p"])
            for k in ("marks", "faceMarks", "settleMarks"):
                if k in pt: pt[k] = [sh(m) for m in pt[k]]
            if "side" in pt: pt["side"]["p"] = sh(pt["side"]["p"])
            if "move" in pt:
                mv = pt["move"]
                if "p" in mv: mv["p"] = sh(mv["p"])
                if "marks" in mv: mv["marks"] = [sh(m) for m in mv["marks"]]
            if "explode" in pt:
                e = pt["explode"]
                if "from" in e: e["from"] = sh(e["from"])
                if "marks" in e: e["marks"] = [sh(m) for m in e["marks"]]
    return S
FLOOR_DY = 4.0   # 데코바퀴·작은바퀴(반지름 24·25)가 바닥에 닿게 전체를 올린다(바퀴 아랫면 y=0)

# 1~10단계 보정: 10단계에서 모터 유닛이 판 양옆에 올라갈 때 블록 아래 끝돌기가 들어갈 바닥판 구멍에도 안내(move.marks)를 단다(교재 10 의 화살표)
_base_pl = [old1("59프레임", 6), old1("29프레임", 6)]
_blk_i = 0
for _pt in BASE[8]["parts"]:
    if _pt["n"] == "3단블록" and "move" in _pt:
        _bl = old1("3단블록", 9, _blk_i); _blk_i += 1
        _sm = settle_marks(_bl, _base_pl)
        if _sm: _pt["move"]["marks"] = _sm
def export_all():
    steps = shift_steps([dict(st) for st in BASE] + export_steps(A), FLOOR_DY)
    return steps
if __name__ == "__main__":
    for st in A.steps: print(st.index, st.note[:40], len(st.parts))
    steps = export_all()
    json.dump({"steps": steps}, open("trike_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("총", len(steps), "단계", "경고", len(A.warn))
    # design-assemblies.js 항목으로 내보내기(trike_entry.js) — python emit.py trike_entry.js cubo-1-trike
    def jv(v): return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
    L = ["  {", f"      id: {jv(EX['id'])},", "      category: '큐보',", "      volume: 1,", f"      chapter: {jv(EX['chapter'])},",
         f"      book: {jv('교재 46~51쪽 · 3륜바이크 (1~29단계)')},",
         f"      listNote: {jv('리모컨은 3D 모델이 없어 조립도에서 제외했다')},",
         f"      camera: {jv(EX['camera'])},", "      steps: ["]
    for st in steps:
        parts = st.get("parts", []); head = ", ".join(f"{k}: {jv(v)}" for k, v in st.items() if k != "parts")
        L.append(f"        {{ {head}, parts: [" if parts else f"        {{ {head}, parts: [] }},")
        if parts:
            for pt in parts:
                keys = ["n", "p", "r"]; seg = ", ".join(f"{k}: {jv(pt[k])}" for k in keys)
                for k, v in pt.items():
                    if k not in keys: seg += f", {k}: {jv(v)}"
                L.append("          { " + seg + " },")
            L.append("        ] },")
    L += ["      ],", "  }"]
    open("trike_entry.js", "w", encoding="utf-8").write(chr(10).join(L))
