# 3륜바이크(교재 46~51쪽) 11~29단계 — 1~10단계(저장소 데이터)는 그대로 두고 asmlib 로 이어서 만든다.
# 좌표: 1~10단계와 같은 세계 좌표(바닥 y=0, 몸체 위판 윗면 y=45, 위판 z −155~−75, 포크가 −z 쪽).
import os as _o, sys as _s  # asmpath bootstrap: 조립도 폴더에서 도구 폴더를 찾는다
_d = _o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d, 'asmlib.py')) and _o.path.dirname(_d) != _d: _d = _o.path.dirname(_d)
_s.path.insert(0, _d)
import json, sys
import numpy as np
from asmlib import *
from trike_base import load_existing, final_parts
import partlib as _pl, hovercheck as _hc
_PLATE_HOVER = _hc.HOVER + float(_pl.get('리벳')['size'][1]) + _hc.MIN_GAP   # G12: 판은 리벳(화면 기본 띄움)보다 리벳 길이(부품 목록) + 10mm(규칙) 더 멀리 — 손으로 적은 숫자 없음

EX = load_existing()
BASE = EX["steps"][:10]
A = Asm('cubo-1-trike', EX["chapter"], EX["book"], camera=EX["camera"], listNote=EX.get("listNote", ""), guideMode="mates")   # 연결점은 부품 DB 돌기·구멍 그대로(다른 조립도와 같다)
A.steps = []
A.parts = []
# 1~10단계: 내보내는 값은 저장소 데이터(BASE)를 그대로 쓰되, 번호별 검사(stepchecks)가 번호를 맞춰 보도록 A 에도 같은 번호·최종 자세로 자리표시 단계를 둔다.
OLD = {}; _STUB = []
for _k, _st in enumerate(BASE, 1):
    _S = A.step(_st["note"]); _S.index = _k
    for _pt in _st["parts"]:
        _p0, _r0 = _pt["p"], _pt.get("r", [0, 0, 0]); _mv = _pt.get("move")
        _q = _S._add(Part(_pt["n"], euler_to_R(_r0), _p0, _S, {}))
        if _mv and _mv["at"] <= 10:   # move_group 과 같은 상태: 원래 자세는 _base·p·r, 옮긴 자세는 p·R 과 extra["move"]
            _q._base = (_q.p.copy(), _q.R.copy()); _fp = _mv.get("p") or [a + b for a, b in zip(_p0, _mv["by"])]
            _q.p = np.array(_fp, float); _q.R = euler_to_R(_mv.get("r") or _r0)
        OLD.setdefault((_pt["n"], _k), []).append(_q); _STUB.append((_q, _pt))
def old1(n, k, i=0): return OLD[(n, k)][i]

UP = (0, 1, 0)
IDX = {}   # 단계 번호 보정(새 단계 번호 = 10 + 순서)
def step(note, **kw):
    s = A.step(note, **kw); return s

# ───────── 11 ── 모터 윗돌기·블록 윗돌기 위에 윗판 덮기 ─────────
motorL, motorR = old1("DC모터", 9, 0), old1("DC모터", 9, 1)
blk8 = old1("2단블록", 8); blkL, blkR = old1("3단블록", 9, 0), old1("3단블록", 9, 1)   # 교재 9: 모터 옆 유닛의 블록은 3단블록(돌기 3개, 책 그림·LIST 3단블록 9)
s11 = step("[교재 11] 39프레임(검정)을 블록 윗돌기에, 59프레임(흰색)을 모터 윗돌기 4개에 덮어요.")
Rtop = np.eye(3)                                            # 39프레임·59프레임: 긴 쪽이 x
black39 = s11.recv("39프레임", Rtop, {"h15": (blk8, "p5"), "h14": (blk8, "p6"), "h1": (blkL, "p1"), "h25": (blkR, "p2")}, hover=30)
white59 = s11.recv("59프레임", Rtop, {"h6": (motorL, "p5"), "h8": (motorL, "p6"), "h36": (motorR, "p3"), "h38": (motorR, "p4")}, hover=30)

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
s14 = step("[교재 14] 흰 59프레임 끝 줄 양끝(5번째 줄의 1·5번째 구멍)에 리벳 2개를 꽂고, 13의 브라켓을 발바닥 안쪽 구멍으로 얹어요. 세로 판이 판 밖으로 나와요.")
H1 = s12.place("59프레임", R_flat59, Lp(0, 2.5, 0))
riv12 = [s12.attach("리벳", M, {"p1": (H1, Lp(hx(j), 5, hz(i)))}, rivet=True) for (i, j) in ((0, 0), (3, 1), (0, 4), (3, 3))]
P1 = s12.recv("25프레임", R_flat59, {"h4": (riv12[0], "p2"), "h9": (riv12[1], "p2")}, joinOrder=2, hover=_PLATE_HOVER)
P2 = s12.recv("25프레임", R_flat59, {"h3": (riv12[2], "p2"), "h10": (riv12[3], "p2")}, joinOrder=2, hover=_PLATE_HOVER)
# 14 리벳(바닥판 6번째 줄 양끝) → 브라켓 발바닥 안쪽 구멍
riv14 = [s14.attach("리벳", M, {"p1": (H1, Lp(hx(j), 5, hz(4)))}, rivet=True) for j in (0, 4)]
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
B3 = s15.attach("3단블록", R_blk, {"p6": (H1, Lp(hx(2), 5, hz(1))), "p7": (H1, Lp(hx(2), 5, hz(2))), "p8": (H1, Lp(hx(2), 5, hz(0)))}, hover=22)
B2 = [s15.attach("2단블록", R_blk, {"p6": (H1, Lp(hx(j), 5, hz(7))), "p5": (H1, Lp(hx(j), 5, hz(8)))}, hover=22) for j in (0, 4)]

# 16 ── 위 59프레임 덮기
s16 = step("[교재 16] 59프레임을 위에서 덮어요: 3단블록과 2단블록의 윗돌기가 위판 구멍에 들어가요.")
TOP = s16.recv("59프레임", R_flat59, {"h13": (B3, "p3"), "h3": (B3, "p5"), "h45": (B2[0], "p4"), "h40": (B2[0], "p3"), "h41": (B2[1], "p4"), "h36": (B2[1], "p3")}, hover=22)

# 17 ── 리벳 8 + 35프레임 + 빨간 15프레임 2
s17 = step("[교재 17] 위판에 리벳 8개를 꽂고, 검정 35프레임(끝 줄 모서리 4곳)과 빨간 15프레임 2개(2·4번째 구멍)를 그 위에 얹어요.")
rv35 = [s17.attach("리벳", M, {"p1": (TOP, Lp(hx(j), 20, hz(i)))}, rivet=True) for (i, j) in ((0, 0), (2, 0), (0, 4), (2, 4))]
rvRed = [s17.attach("리벳", M, {"p1": (TOP, Lp(hx(j), 20, hz(i)))}, rivet=True) for (i, j) in ((7, 0), (7, 2), (8, 0), (8, 2))]
R35 = LR([XL, YL, ZL])
B35 = s17.recv("35프레임", R35, {"h1": (rv35[0], "p2"), "h3": (rv35[1], "p2"), "h13": (rv35[2], "p2"), "h15": (rv35[3], "p2")}, joinOrder=2, hover=_PLATE_HOVER)
red = [s17.recv("15프레임", R35, {"h2": (rvRed[2 * k], "p2"), "h4": (rvRed[2 * k + 1], "p2")}, joinOrder=2, hover=_PLATE_HOVER) for k in (0, 1)]

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
        pt.extra["settleOrder"] = 2                # 14: 리벳이 먼저 꽂히고 브라켓이 그 위로 내려온다(G12 순서)
    else:                                      # 세로 판 리벳: 13 에서 브라켓(옆자리) 구멍으로 들어가므로 안내를 옆자리 기준으로 옮긴다
        pt.extra["marks"] = [rnd(np.array(m) + off) for m in pt.extra["marks"]]

# ───────── 20~25 ── 앞바퀴 팔(115프레임 2장 + 90도 프레임·3단블록 유닛 2개 + 손잡이 + 작은바퀴) ─────────
# 사용자 확인(2026-10-02): 팔을 기둥 위쪽의 두 3단블록 사이(틈 10mm = 팔 두께 10)에 끼우고, 블록 구멍과 팔 구멍을 맞춰 그 사이로 축을 끼운다(교재 23).
# 팔 좌표(로컬): x=길이 u(바퀴 쪽 끝 구멍 k=1 → 위쪽 끝 구멍 k=15, 구멍 간격 10), y=너비(손잡이 쪽 +), z=두께(구멍축). 최종 자세: 두께가 세계 x(−x 쪽이 로컬 +z),
# 축 구멍 k=12 가 기둥 위쪽 블록 구멍 h2 와 같은 자리(83.64, −223.44), 바퀴가 바닥에 닿도록 팔이 기울어진다(앞바퀴 가운데 높이 21 = 바퀴 반지름 25 − 4).
BUILD2 = np.array([150.0, 21.0, -260.0])         # 따로 만드는 자리(20~22)
colBlk = old1("3단블록", 1, 0)                     # 기둥 위쪽 3단블록(x=+10), 반대쪽은 인덱스 1(x=−10)
PIV = np.array([0.0, 83.64, -223.439]) + 10 * np.array([0.0, 0.7071, -0.7071])   # 기둥 위쪽 3단블록 구멍 h1(위쪽 끝 쪽, 사용자가 표시한 1번 홀) — h2 에서 기둥 방향으로 10mm 위
K_PIV = 12   # 사용자가 표시하기(1번)로 짚은 구멍 — 13번째는 한 칸 위여서 틀렸다. 팔 12번째 구멍이 기둥 위쪽 블록 구멍 h1 과 같은 자리
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
A2 = s20.recv("115프레임", R_A, dict(zip(["h8", "h15"], [(r, "p2") for r in rvA])), joinOrder=2, hover=_PLATE_HOVER)
s21 = step("[교재 21] 90도 프레임에 2단블록을 돌기 2개로 끼워요: 모서리가 아닌 두 구멍에 들어가요(2개 만들어요).")
# 교재 21·22: 블록의 구멍(y)이 팔 너비 방향(위)이고, L 판은 블록의 팔 끝 쪽(+u) 옆면에 붙는다 — L 의 모서리(세로 다리)가 팔에서 먼 쪽, 가로 다리 3칸이 팔 쪽으로 뻗어 블록 돌기 3개를 받고, 세로 다리는 아래(−y)로 내려간다. 두 유닛은 팔 양쪽(±z)에서 거울 모양.
RL1 = AfR(np.column_stack([(0, -1, 0), (-1, 0, 0), (0, 0, -1)])); RL2 = AfR(np.column_stack([(0, -1, 0), (1, 0, 0), (0, 0, 1)]))
L1 = s21.place("90도 프레임", RL1, Af(67.5, -10, 20)); L2 = s21.place("90도 프레임", RL2, Af(67.5, -10, -20))
RB1 = AfR(np.column_stack([(0, 0, 1), (0, -1, 0), (1, 0, 0)])); RB2m = AfR(np.column_stack([(0, 0, -1), (0, 1, 0), (1, 0, 0)]))
U1 = s21.attach("2단블록", RB1, {"p2": (A2, Af(hk(14), 0, 2.5)), "p3": (L1, "h3"), "p4": (L1, "h2")}, hover=22)
U2 = s21.attach("2단블록", RB2m, {"p2": (A1, Af(hk(14), 0, -2.5)), "p3": (L2, "h3"), "p4": (L2, "h2")}, hover=22)
s22 = step("[교재 22] 유닛 2개의 2단블록 끝돌기를 팔의 14번째 구멍에 양쪽에서 끼워요.")
s23b = step("[교재 23] 19 + 22: 22번 팔을 기둥 위쪽 두 3단블록 사이에 끼우고, 3단블록 구멍과 팔 구멍을 지나게 축을 끼워 양쪽 끝을 부시 2개로 고정해요.")
# 23 ── 축(65)을 두 블록 구멍 h2 와 팔 구멍을 지나 끼우고 부시 2개
blkL, blkR = old1("3단블록", 1, 1), old1("3단블록", 1, 0)           # x=−10, x=+10
Rax = np.column_stack([(0, 0, 1), (1, 0, 0), (0, 1, 0)])
axle23 = s23b.place("축", Rax, PIV.copy(), dir=[-1, 0, 0], hover=40, pegDepth=40, joinOrder=2, marks=[rnd(PIV + np.array([-7.5, 0, 0]))])   # 안내 꼬리 = 띄운 축의 앞 돌기 끝(guidecheck 계산값)
bu23a = s23b.recv("부시", np.diag([-1.0, -1.0, 1.0]) @ Rax, {"h1": (axle23, "p1")}, joinOrder=3, hover=22, dir=[1, 0, 0], against=blkL)
bu23b = s23b.recv("부시", Rax, {"h1": (axle23, "p1")}, joinOrder=3, hover=22, dir=[-1, 0, 0], against=blkR)
# 24·25 ── 팔에 건 뒤(최종 자세)에서 손잡이·바퀴
s24 = step("[교재 24] L 프레임 세로 다리 구멍 4곳에 리벳을 꽂고, 37프레임(손잡이)을 그 위에 얹어요.")
Rrv = AfR(np.column_stack([(0, 0, 1), (1, 0, 0), (0, 1, 0)]))     # 리벳 축 = 팔 길이 방향(u)
rv24 = [s24.attach("리벳", Rrv, {"p1": (L, Af(70, y, z))}, rivet=True) for L, z in ((L1, 30), (L2, -30)) for y in (-10, -20)]
handle = s24.recv("37프레임", Rrv, dict(zip(["h21", "h20", "h3", "h2"], [(r, "p2") for r in rv24])), hover=22)   # 판 구멍 y −30·−20·−10 중 리벳이 −10·−20 — 팔 끝(y ±5)을 피해 아래로
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
    U.extra["dir"] = rnd(AfR(np.eye(3)) @ np.array([-1, 0, 0]))   # 블록 돌기가 +u 쪽 L 판으로 들어가므로 블록은 그 반대(−u)에서 접근한다
for pt in armparts: to_build2(pt, 23)
# 유닛은 21 에서 팔에서 떨어진 자리(옆)에서 만들고 22 에서 팔에 붙는다(side → 제자리)
for L, U, sg in ((L1, U1, 1), (L2, U2, -1)):
    off = Ma.T @ Za * 0 + np.array([0, 8.0, 50.0 * sg])   # 옆자리는 y +8 올려 90도 프레임 세로 다리가 바닥 아래로 안 가게(최종 자리는 그대로)
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

CAMS = {11: (-1.0, 0.62), 12: (0.5, 0.85), 13: (-2.25, 0.8), 14: (0.5, 0.85), 15: (0.5, 0.85), 16: (0.5, 0.85), 17: (0.6, 0.85), 18: (0.6, 0.85),
        19: (-0.6, 0.95), 20: (0.5, 0.9), 21: (0.5, 0.9), 22: (0.5, 0.9), 23: (-0.6, 0.95), 24: (-2.34, 0.99), 25: (0.5, 0.9), 26: (0.8, 0.95), 27: (-0.8, 0.95), 28: (0.4, 1.05), 29: (0.4, 1.05)}
for k, (th, ph) in CAMS.items():
    A.steps[k - 1].cam = (th, ph); A.steps[k - 1].camSrc = "guess"
# 12번 카메라: 흰 59프레임 구멍 점 45개 axes_fit(holefit DoG 24점 + 격자 21점, 평균 0.89px, roll 2.9°) theta −0.68·phi 0.78 — 칸 +X(짧은 쪽 5)·줄 +Z(긴 쪽 9), 칸1줄1 = 그림 왼쪽 끝. 리벳 = 칸1줄1·칸5줄1·칸2줄4·칸4줄4
A.steps[0].cam = (-0.58, 0.70); A.steps[0].camSrc = "fit"   # 1번: 격자 27점 axes_fit 0.77px
A.steps[12].cam = (0.94, 1.03); A.steps[12].camSrc = "fit"   # 13번: 3D 점 6개 PnP(7.76px 거친 값, 화면 비교로 확인)
A.steps[10].cam = (-2.24, 1.17); A.steps[10].camSrc = "fit"   # 11번: 격자 33점 axes_fit 1.84px(이상치 12점 제외)
A.steps[11].cam = (-0.68, 0.78); A.steps[11].camSrc = "fit"
# 14번 카메라: 흰 59프레임 아랫부분(5~9번째 줄) 구멍 점 25개 axes_fit(holefit 5×5, 평균 1.17px, roll −6.6°) theta −0.40·phi 0.74 — 칸 +X·줄 +Z, 위쪽 4줄은 검정 25프레임에 가려져 격자는 5~9줄만 읽음(소격자 1줄 = 판 5번째 줄)
A.steps[13].cam = (-0.40, 0.74); A.steps[13].camSrc = "fit"
# 15번 카메라: 판 위쪽이 프레임·브라켓에 가려 격자(holefit)가 안 맞아, 책 초록 링 4개(2단블록 구멍: 판 8·9째 줄 양끝 칸1·칸5)의 3D 점 4개 PnP(mkfit3d fov 35, 평균 0.46px) theta −0.70·phi 0.92 — 점 4개뿐이라 거친 값
A.steps[14].cam = (-0.70, 0.92); A.steps[14].camSrc = "fit"
A.steps[15].cam = (-0.69, 1.13); A.steps[15].camSrc = "fit"
A.steps[16].cam = (-0.69, 0.77); A.steps[16].camSrc = "fit"
A.steps[17].cam = (-0.47, 0.79); A.steps[17].camSrc = "fit"
A.steps[18].cam = (-2.43, 0.75); A.steps[18].camSrc = "fit"
A.steps[19].cam = (0.53, 0.88); A.steps[19].camSrc = "fit"
A.steps[20].cam = (2.39, 0.94); A.steps[20].camSrc = "fit"
A.steps[21].cam = (1.01, 0.86); A.steps[21].camSrc = "fit"
A.steps[22].cam = (-2.34, 0.99); A.steps[22].camSrc = "fit"

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
            for _mv in pt.get("moves") or []:
                _mv["p"] = sh(_mv["p"])
                if "marks" in _mv: _mv["marks"] = [sh(m) for m in _mv["marks"]]
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
A.meta["floorDy"] = FLOOR_DY   # 바닥 검사가 출력 단계의 올림을 알게

# 1~10단계 보정: 10단계에서 모터 유닛이 판 양옆에 올라갈 때 블록 아래 끝돌기가 들어갈 바닥판 구멍에도 안내(move.marks)를 단다(교재 10 의 화살표)
_base_pl = [old1("59프레임", 6), old1("29프레임", 6)]
_blk_i = 0
for _pt in BASE[8]["parts"]:
    if _pt["n"] == "3단블록" and "move" in _pt:
        _bl = old1("3단블록", 9, _blk_i); _blk_i += 1
        _sm = settle_marks(_bl, _base_pl)
        if _sm: _pt["move"]["marks"] = _sm
# 5·8단계 리벳: 토끼처럼 구멍 입구를 가리키는 안내점(위에서 내려와 꽂힘)을 단다 — 이전 데이터에 빠져 있었다(안내 화살표 검사)
for _si in (0, 4, 7):
    for _pt in BASE[_si]["parts"]:
        if _pt["n"] == "리벳" and "marks" not in _pt:
            x, y, z = _pt["p"]
            _pt["dir"] = [0, 1, 0]; _pt["marks"] = [[x, round(y - 1.5, 3), z]]
# 4번: 리벳은 항상 결합 전(분리) — 리벳이 먼저 판 구멍에 꽂히고(moves at 4, 먼저) 그다음 포크 묶음이 리벳 위로 내려온다(settleOrder 2, airplane 과 같은 방식; 사용자 지시 2026-11-09, G12)
for _pt in BASE[0]["parts"]:
    if _pt["n"] == "리벳":
        _x, _y, _z = _pt["p"]
        _pt["moves"] = [{"at": 4, "p": [_x, _y, _z], "r": list(_pt["r"]), "dir": [0, 1, 0], "marks": [[_x, round(_y - 1.5, 3), _z]]}, dict(_pt["move"])]
for _st in BASE[1:3]:
    for _pt in _st["parts"]:
        if (_pt.get("side") or {}).get("until") == 4: _pt["settleOrder"] = 2; _pt["settleHover"] = 50.0
for _q, _pt in _STUB: _q.extra.update({a: b for a, b in _pt.items() if a not in ('n', 'p', 'r')})   # 위 보정(dir·marks)까지 끝난 값을 자리표시 부품에도 붙여 검사가 같은 값을 보게 한다
# 2번 카메라: 135도 프레임 두 개(서 있음, 띄움 30)의 구멍 18개를 모델 3차원 좌표로 PnP — 맞춤 11점 평균 1.76px·최대 3.37px(모델 좌표 오차가 큰 구멍 7개를 뺌: 가까운 쪽 h2·h4·h5·h7, 먼 쪽 h1·h7·h9 — 18점 전부는 평균 4.75px 에 theta −0.116·phi 1.019 로 거의 같다), fov 30
BASE[1]["cam"] = {"theta": -0.109, "phi": 1.017}; BASE[1]["camSrc"] = "fit"; A.steps[1].cam = (-0.109, 1.017); A.steps[1].camSrc = "fit"
# 3번 카메라: 가까운 135도 프레임 바깥면 구멍 9개를 눈으로 읽어 PnP — 평균 4.5px(기준 2px 초과 ⚠), fov 30, 옛 초안(−0.611·0.96)과 theta 가 비슷하다
BASE[2]["cam"] = {"theta": -0.625, "phi": 0.858}; BASE[2]["camSrc"] = "fit"; A.steps[2].cam = (-0.625, 0.858); A.steps[2].camSrc = "fit"
for _i in (3, 6, 9): A.steps[_i].kw["madeNoPart"] = True; BASE[_i]["madeNoPart"] = True
for _i in (18, 21): A.steps[_i].kw["madeNoPart"] = True   # 19·22번도 새 부품 없이 앞 번호를 합친다(BASE 는 11번까지)   # 4·7·10번은 새 부품 없이 앞 번호를 합친다 — 번호별 검사 대상
# 5번 카메라: 윗판 링 7개 중심 PnP(mkfit3d, 평균 1.19px·최대 2.03px, roll −1.7°) theta −0.56·phi 0.86 — 구멍 뒤 흰 조각 기준(3.3px)은 비스듬한 시야에서 윗면 중심과 어긋나 쓰지 않았다
BASE[4]["cam"] = {"theta": -0.56, "phi": 0.86}; BASE[4]["camSrc"] = "fit"; A.steps[4].cam = (-0.56, 0.86); A.steps[4].camSrc = "fit"
# 5번: 리벳이 먼저 판 구멍에 꽂히고 윗판이 그 뒤에 내려온다(G12) — 윗판 순서 2, 리벳보다 10mm 이상 더 띄운다
BASE[4]["parts"][1]["joinOrder"] = 2; BASE[4]["parts"][1]["hover"] = 34
# 5·4번: 책 그림에는 포크 끝 블록의 가운데 돌기(칸4 줄2) 링이 없다 — 링 수 = 화살표 수(책 기준)로 가운데 안내점을 뺀다(돌기는 물리적으로 그 구멍에 들어간다)
BASE[4]["parts"][1]["marks"] = [m for m in BASE[4]["parts"][1]["marks"] if not (m[0] == -10 and m[2] == 0)]
BASE[2]["parts"][0]["settleMarks"] = [m for m in BASE[2]["parts"][0]["settleMarks"] if not (m[0] == -10 and m[2] == 0)]
# 4번 카메라: 39프레임 격자 axes_fit(27점 평균 0.54px, roll −1.6°) theta −0.63·phi 0.79
BASE[3]["cam"] = {"theta": -0.63, "phi": 0.79}; BASE[3]["camSrc"] = "fit"; A.steps[3].cam = (-0.63, 0.79); A.steps[3].camSrc = "fit"
# 6번 카메라: 새 59프레임(흰 판) 구멍 점 45개 axes_fit(holefit DoG 40점 + 격자 5점, 평균 0.99px, roll −0.6°) theta −0.96·phi 0.73 — 칸 +X·줄 +Z, 칸1줄1 = 그림 왼쪽 끝
BASE[5]["cam"] = {"theta": -0.96, "phi": 0.73}; BASE[5]["camSrc"] = "fit"; A.steps[5].cam = (-0.96, 0.73); A.steps[5].camSrc = "fit"
# 7번 카메라: 아래 59프레임(흰 판) 구멍 점 45개 axes_fit(holefit 42점 + 격자 3점, 평균 0.66px, roll −2.7°) theta −1.02·phi 0.70 — 칸 +X·줄 +Z (6번과 같은 판·같은 방향)
BASE[6]["cam"] = {"theta": -1.02, "phi": 0.70}; BASE[6]["camSrc"] = "fit"; A.steps[6].cam = (-1.02, 0.70); A.steps[6].camSrc = "fit"
# 6번: 새 창고(판 둘+3단블록)가 7번에서 창고 1 로 합쳐진다는 선언(side.until 7, 자리는 그대로) — 7번 화면에 다른 창고 부품으로 붉게 칠해지지 않게.
#   ⚠ 6번 완성 중심(z −122)을 원점으로 옮기려 side 를 떨어뜨리면 공용 검사(cubo_joint_check·check_local)가 창고를 안 봐서 몸체와 겹침 오탐이 난다 — 공용 검사의 창고 인식은 다음 과제.
_off6 = [0, 0, 0]
# 8번 카메라: 59프레임(흰 판) 구멍 점 45개 axes_fit(holefit DoG 26점 + 격자 19점, 평균 1.52px, roll −5.0°) theta −0.92·phi 0.72 — 칸 +X·줄 +Z. 리벳 3개 = 칸5 줄3~5(x 0), 15프레임이 그 위(저장된 자리표시는 x −10 이라 책과 달라 0 으로 고쳤다)
BASE[7]["cam"] = {"theta": -0.92, "phi": 0.72}; BASE[7]["camSrc"] = "fit"; A.steps[7].cam = (-0.92, 0.72); A.steps[7].camSrc = "fit"
# 10번 카메라: 59프레임(흰 판) 구멍 점 45개 axes_fit(holefit DoG·holesearch 모서리 24점 + 격자 21점, 평균 0.89px, roll −4.6°) theta −0.41·phi 0.72 — 칸 +X·줄 +Z(⚠ 구멍 24/45 만 실측, 모터에 가려짐)
BASE[9]["cam"] = {"theta": -0.41, "phi": 0.72}; BASE[9]["camSrc"] = "fit"; A.steps[9].cam = (-0.41, 0.72); A.steps[9].camSrc = "fit"
# 9번 카메라: 가까운 37프레임(검은 판) 구멍 점 21점 axes_fit(holefit 14점 + 격자 7점, 평균 0.43px, roll −0.7°) theta 0.58·phi 0.67 — 칸 +X(화면 오른쪽 아래)·줄 +Z(화면 왼쪽 아래). 옛 짐작(−0.698·0.873)은 반대편에서 본 값이라 틀렸다. ⚠ 어두운 판의 흰 조각(구멍 뒤)은 윗면 링 중심과 몇 px 어긋난다
BASE[8]["cam"] = {"theta": 0.58, "phi": 0.67}; BASE[8]["camSrc"] = "fit"; A.steps[8].cam = (0.58, 0.67); A.steps[8].camSrc = "fit"
# 9번 모터 유닛 2개(창고 2)는 10번에서 창고 1 로 합쳐진다는 선언(side.until 10, 자리는 그대로) — 10번 화면에서 다른 창고 부품으로 붉게 칠해지지 않게(6번과 같은 방식)
for _pt in BASE[8]["parts"]:
    _pt["side"] = {"p": list(_pt["p"]), "r": list(_pt["r"]), "until": 10}
for _pt in BASE[5]["parts"]:
    _pt["side"] = {"p": [round(_pt["p"][i] + _off6[i], 3) for i in range(3)], "r": list(_pt["r"]), "until": 7}
    if _pt.get("marks"): _pt["marks"] = [[round(m[i] + _off6[i], 3) for i in range(3)] for m in _pt["marks"]]
# 3번: 새 3단블록이 −x 쪽에서 들어간다 — 화살표 꼬리(marks) = 고정된 돌기 끝(x −10), 화살표 끝(faceMarks) = 링이 구멍 중심에 오도록 −12.5(링 = 끝 − 방향×두께 5/2, guidecheck G23)
BASE[2]["parts"][0]["marks"] = [[-10, 10.0, 110]]; BASE[2]["parts"][0]["faceMarks"] = [[-12.5, 10.0, 110]]; BASE[2]["parts"][0].pop("thick", None); BASE[2]["parts"][0]["settleRecv"] = False   # 4번에 합칠 때는 이 블록의 돌기 3개가 판 구멍에 꽂힌다(링은 판 구멍)
for _q, _pt in _STUB: _q.extra.update({a: b for a, b in _pt.items() if a not in ('n', 'p', 'r')})   # 번호별 보정(위 BASE[n] 수정)을 자리표시 부품에도 다시 반영
_PREP = {}
# ── 04 창고 정리(1차) — 책 46~51쪽을 1→29번 순서로 보며 정했다(2026-11-09).
#   번호표로 확인: 7번 "4 + 5" · 10번 "8 + 9"(번호표 없음, 모양) · 14번 "12 + 13"(모양) · 19번 "11 + 18"(모양) · 22번 "20 + 21"(모양) · 23번 "19 + 22". 나머지는 그림 모양으로 판단(추정).
#   1번 몸체(창고 1) / 2~3번 프레임 뭉치(창고 2, 판 없음) / 4번 1+3 합침(창고 1) / 5번 39프레임 덮기(창고 1) / 6번 59프레임+29프레임(새 창고 2) / 7번 합침(창고 1) / 8번 몸체 이어서(창고 1)
#   / 9번 모터 묶음(새 창고 2) / 10번 합침(창고 1) / 11번 몸체 이어서(창고 1) / 12번 25프레임 판(새 창고 2) / 13번 브라켓(새 창고 3) / 14번 13을 12에 합침(창고 2) / 15~18번 이어서(창고 2)
#   / 19번 18을 몸체에 합침(창고 1) / 20번 115프레임(새 창고 2) / 21번 90도 프레임(새 창고 3) / 22번 21을 20에 합침(창고 2) / 23번 22를 몸체에 합침(창고 1) / 24~29번 몸체 이어서(창고 1).
_SLOT = {1: 1, 2: 2, 3: 2, 4: 1, 5: 1, 6: 2, 7: 1, 8: 1, 9: 2, 10: 1, 11: 1, 12: 2, 13: 3, 14: 2, 15: 2, 16: 2, 17: 2, 18: 2, 19: 1, 20: 2, 21: 3, 22: 2, **{i: 1 for i in range(23, 30)}}
for _i, _sl in _SLOT.items(): _PREP.setdefault(_i, {})["slot"] = _sl
_HIST = {2: "📦 1번 39프레임을 창고 1에 두고, 창고 2에서 135도 프레임 2개를 3단블록으로 잇는 조립을 새로 시작",
         4: "창고 2의 3번(프레임 뭉치)을 창고 1로 불러와 1번 판에 합침 → 그룹 1",
         6: "📦 1~5번 몸체를 창고 1에 두고, 창고 2에서 59프레임·29프레임 판을 새로 시작",
         7: "창고 2의 6번 판을 창고 1로 불러와 5번 몸체와 합침 → 그룹 1",
         9: "📦 1~8번 몸체를 창고 1에 두고, 창고 2에서 37프레임 위에 모터 묶음을 새로 시작",
         10: "창고 2의 9번 모터 묶음을 창고 1로 불러와 8번 몸체에 합침 → 그룹 1",
         12: "📦 1~11번 몸체를 창고 1에 두고, 창고 2에서 59프레임에 25프레임을 올리는 조립을 새로 시작",
         13: "📦 창고 3에서 1열브라켓 2개를 새로 시작",
         14: "창고 3의 브라켓(13번)을 창고 2로 불러와 12번 판에 합침 → 그룹 2",
         19: "창고 2의 18번 묶음을 창고 1로 불러와 11번 몸체에 합침 → 그룹 1",
         20: "📦 1~19번 몸체를 창고 1에 두고, 창고 2에서 115프레임 2개를 새로 시작",
         21: "📦 창고 3에서 90도 프레임 2개를 새로 시작",
         22: "창고 3의 블록 묶음(21번)을 창고 2로 불러와 115프레임에 합침 → 그룹 2",
         23: "창고 2의 팔(22번)을 창고 1로 불러와 19번 몸체에 축으로 연결"}
for _i, _h in _HIST.items(): _PREP.setdefault(_i, {})["history"] = _h
# 새 조립이 다른 창고에서 진행되는 동안 안 보여야 할 만들어진 번호(hideMade) — 창고별로 살아 있는 번호를 따라가며 정한다(A3).
_alive = {1: [], 2: [], 3: []}
_MERGE = {4: (2, 1), 7: (2, 1), 10: (2, 1), 14: (3, 2), 19: (2, 1), 22: (3, 2), 23: (2, 1)}
for _i in range(1, 30):
    _sl = _SLOT[_i]
    _hide = {str(_j): "%d번 조립(창고 %d)" % (_j, _k) for _k, _lst in _alive.items() if _k != _sl and _k != _MERGE.get(_i, (0, 0))[0] for _j in _lst}
    if _hide: _PREP.setdefault(_i, {})["hideMade"] = _hide
    if _i in _MERGE:
        _a, _b = _MERGE[_i]; _alive[_b] = _alive[_b] + [_j for _j in _alive[_a]] + [_i]; _alive[_a] = []
    else:
        _alive[_sl] = _alive[_sl] + [_i]

# ── 03 부품 정리(1차) — 책 46~51쪽 번호별 그림에서 센 값(리벳은 그림 옆 "(n)" 숫자: 1번 1·5번 1·8번 3·12번 4·13번 2·14번 2·17번 8·18번 1·20번 2·24번 4 = 28).
#   LIST(46쪽)와 맞춘다. 리모컨 1 은 3D 모델이 없어 번호에 넣지 않는다(LIST 쪽에 제외로 기록, 29번 DC모터 연결 번호는 부품 없음).
USED = {1: "39프레임 1, 3단블록 2, 리벳 1", 2: "135도 프레임 2, 3단블록 2", 3: "3단블록 1", 4: "없음(합치는 단계)", 5: "39프레임 1, 리벳 1",
        6: "29프레임 1, 59프레임 1, 3단블록 1", 7: "없음(합치는 단계)", 8: "2단블록 1, 15프레임 1, 리벳 3", 9: "37프레임 2, DC모터 2, 3단블록 2",
        10: "없음(합치는 단계)", 11: "39프레임 1, 59프레임 1", 12: "25프레임 2, 59프레임 1, 리벳 4", 13: "1열브라켓 2, 리벳 2", 14: "리벳 2",
        15: "2단블록 2, 3단블록 1", 16: "59프레임 1", 17: "15프레임 2, 35프레임 1, 리벳 8", 18: "눈블록 2, 리벳 1", 19: "없음(합치는 단계)",
        20: "115프레임 2, 리벳 2", 21: "2단블록 2, 90도 프레임 2", 22: "없음(합치는 단계)", 23: "부시 2, 축 1", 24: "37프레임 1, 리벳 4",
        25: "부시 2, 작은바퀴 2, 축 1", 26: "T축 1, 데코바퀴 1", 27: "T축 1, 데코바퀴 1", 28: "메인보드 1", 29: "없음(DC모터 연결)"}
def apply_prep(steps):
    """03 부품 정리(▣ 사용 부품 줄)·04 창고 정리(slot·history·hideMade)를 번호별 단계에 붙인다."""
    for _i, _st in enumerate(steps, 1):
        _pp = (_st.get("note") or "").split("\n▣ 사용 부품:")
        _st["note"] = _pp[0] + "\n▣ 사용 부품: " + USED[_i]
        _st.update(_PREP.get(_i, {}))
    return steps
def export_all():
    steps = shift_steps([dict(st) for st in BASE] + export_steps(A)[10:], FLOOR_DY)
    return apply_prep(steps)
import stepchecks; stepchecks.apply(A, "trike")
if __name__ == "__main__":
    for st in A.steps: print(st.index, st.note[:40], len(st.parts))
    steps = export_all()
    json.dump({"steps": steps}, open("trike_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("총", len(steps), "단계", "경고", len(A.warn))
    # design-assemblies.js 항목으로 내보내기(trike_entry.js) — python emit.py trike_entry.js cubo-1-trike
    def jv(v): return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))
    L = ["  {", f"      id: {jv(EX['id'])},", "      category: '큐보',", "      volume: 1,", f"      chapter: {jv(EX['chapter'])},",
         f"      book: {jv('교재 46~51쪽 · 3륜바이크 (1~29단계)')},",
         f"      listNote: {jv('리모컨은 3D 모델이 없어 조립도에서 제외했다')},", '      guideMode: "mates",',
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
