# 큐보 1권 오토건(교재 64~69쪽, 32단계) — 조립 프로그램(asmlib)으로 만든다. 1~13: 받침(총이 올라앉는 흰 판+모터+메인보드), 14~28: 총몸, 29: 합체, 30: 고무줄, 31~32: 타깃.
# 좌표: 바닥 y=0(받침 흰 판 아랫면), 315프레임은 +x 로 뻗고(x 0~150, z ±15), 흰 59프레임은 그 왼쪽(x −50~0, 긴 쪽이 z −45~45)에 길이 방향이 직각으로 맞닿는다.
# 구멍 번호는 교재 그림의 판 모서리 위치(+x = 화면 오른쪽 아래, −z = 오른쪽 위)에서 읽었다(짐작 포함 — 안내서 5-7절).
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-1-autogun", "오토건", "교재 64~69쪽 · 오토건 (1~32단계)", camera={"target": [60, 20, 0], "radius": 380, "theta": 0.9, "phi": 1.0},
        listNote="고무밴드(3D 모델 없음)는 조립도에서 제외했다")
import sys
RELOCK = "--relock" in sys.argv   # 잠금 기록을 새로 만들 때(수정 지시는 이번 빌드에서 무시한다)
if not RELOCK: A.load_fixes("autogun_fixes.json")   # 관리자 수정 지시(앞 단계 수정 - 뒤 단계가 따라온다). 파일이 없으면 아무 일도 안 한다
A.load_links("autogun_links.json", relock=RELOCK)   # 좌표로 쓴 결합·절대 좌표로 놓은 판을 이름(어느 부품의 어느 구멍)으로 잠가 두는 기록 - 앞을 고치면 뒤가 따라온다
UP = (0, 1, 0)

R_FLAT = np.eye(3)                                  # 315프레임: 긴 쪽 x, 구멍축 y
R_Z = ori("+z", "+y")                               # 59프레임: 긴 쪽 z(모델 z → 세계 −x), 구멍축 y
R_LIE = ori_z("+x", "-y")                           # 눕힌 블록(긴 쪽 x, 돌기 면이 아래): 모델 y 가 세계 +z → 큰 구멍은 z 방향으로 관통
R_LIE_Z = ori_z("+z", "-y")                         # 눕힌 블록(긴 쪽 z): 블록 끝돌기가 ±z

# ── 1 ── 흰 59프레임 + 315프레임을 이음매에서 맞닿게 놓고 블록 4개
s1 = A.step("[교재 1] 흰 59프레임과 검정 315프레임을 길이 방향이 직각이 되게 맞닿게 놓고, 3단블록 2개는 이음매에 걸쳐(돌기 2개는 흰 판, 1개는 315프레임), 2단블록 2개는 흰 판 왼쪽 끝 모서리에 눕혀 꽂아요.")
W = s1.place("59프레임", R_Z, (-25, 2.5, 0))
P = s1.place("315프레임", R_FLAT, (75, 2.5, 0))
def X(x): return x
blkC = s1.attach("3단블록", R_LIE, {"p5": (W, (-15, 5, 10)), "p4": (W, (-5, 5, 10)), "p3": (P, (5, 5, 10))}, hover=22)
blkD = s1.attach("3단블록", R_LIE, {"p5": (W, (-15, 5, -10)), "p4": (W, (-5, 5, -10)), "p3": (P, (5, 5, -10))}, hover=22)
blkA = s1.attach("2단블록", R_LIE, {"p3": (W, (-45, 5, 40)), "p4": (W, (-35, 5, 40))}, hover=22)
blkB = s1.attach("2단블록", R_LIE, {"p3": (W, (-45, 5, -40)), "p4": (W, (-35, 5, -40))}, hover=22)

# ── 2 ── 흰 19프레임을 2단블록 끝돌기에
s2 = A.step("[교재 2] 흰 19프레임을 세워서 두 2단블록의 끝돌기(왼쪽)에 끼워요.")
R_BAR = ori("+z", "-x")                              # 세운 막대: 긴 쪽 z, 구멍축 x
bar19 = s2.recv("19프레임", R_BAR, {"h9_1": (blkA, "p2"), "h1_1": (blkB, "p2")}, hover=22)

# ── 3 ── 315프레임 끝쪽에 3단블록 2개(긴 쪽 z)
s3 = A.step("[교재 3] 315프레임 위에 3단블록 2개를 가로로(315프레임 폭에 맞게) 꽂아요: 하나는 끝에서 둘째 칸, 하나는 그보다 앞쪽(왼쪽)으로 5칸.")
blkE = s3.attach("3단블록", R_LIE_Z, {"p5": (P, (85, 5, -10)), "p4": (P, (85, 5, 0)), "p3": (P, (85, 5, 10))}, hover=22)
blkF = s3.attach("3단블록", R_LIE_Z, {"p5": (P, (135, 5, -10)), "p4": (P, (135, 5, 0)), "p3": (P, (135, 5, 10))}, hover=22)

# ── 4 ── 115프레임 2개를 세워 양옆에 + 리벳 2개
s4 = A.step("[교재 4] 흰 115프레임 2개를 315프레임 양옆에 세워요: 앞쪽(왼쪽)은 리벳으로 이음매 블록에, 나머지 둘은 3단블록 끝돌기에 끼워요.")
R_SIDE = ori("+x", "+z")                             # 세운 옆 막대: 긴 쪽 x, 구멍축 z
sideL = s4.recv("115프레임", R_SIDE, {"h9_1": (blkE, "p1"), "h14_1": (blkF, "p1")}, hover=22)
sideR = s4.recv("115프레임", R_SIDE, {"h9_1": (blkE, "p2"), "h14_1": (blkF, "p2")}, hover=22)

# 4 리벳: 이음매 3단블록(C·D)의 셋째 큰 구멍(x=5) ↔ 옆 막대 첫 구멍 (막대가 블록 끝면 바로 옆이라 리벳 몸통 가운데는 막대 안쪽 면에 온다)
R_RV_P = ori("+x", "+z"); R_RV_N = ori("+x", "-z")           # 리벳 축 y → 세계 +z / −z
rvL = s4.attach("리벳", R_RV_P, {"p2": (sideL, (5, 10, 17.5))}, rivet=True)
rvR = s4.attach("리벳", R_RV_N, {"p2": (sideR, (5, 10, -17.5))}, rivet=True)

# ── 5 ── 위에서 315프레임·흰 59프레임 덮기
s5 = A.step("[교재 5] 블록 윗돌기 위에 검정 315프레임과 흰 59프레임을 덮어요: 315프레임은 3단블록 2개의 돌기와 이음매 블록 돌기 2개, 흰 59프레임은 4개 블록의 돌기 8개에 끼워요.")
top315 = s5.recv("315프레임", R_FLAT, {"h9_2": (blkE, "p6"), "h9_1": (blkE, "p8"), "h9_3": (blkE, "p7"), "h14_2": (blkF, "p6"), "h14_1": (blkF, "p8"), "h14_3": (blkF, "p7"),
                                          "h1_3": (blkC, "p7"), "h1_1": (blkD, "p7")}, hover=22)
topW = s5.recv("59프레임", R_Z, {"h9_5": (blkA, "p6"), "h9_4": (blkA, "p5"), "h1_5": (blkB, "p6"), "h1_4": (blkB, "p5"),
                                   "h6_2": (blkC, "p8"), "h6_1": (blkC, "p6"), "h4_2": (blkD, "p8"), "h4_1": (blkD, "p6")}, hover=22)

# ───────── 6~10 ── 모터 유닛 (옆에서 따로 만들었다가 11단계에 받침에 올린다) ─────────
# 최종 자세(받침 위, 모터 옆돌기가 위 315프레임 구멍에): 모터 중심 (126.5, 35, −1), 판은 세로(구멍축 z), 37프레임이 뒤(z −17.5), 앞 27프레임이 z +20.5.
#  모터 모델 축 → 세계: x → 아래(−y), y(윗면) → 뒤(−z), z → +x.  윗돌기 p1·p2(간격 40)가 37프레임 1·5번째 칸(가운데 줄)에, 십자 구멍(z −12.5)이 4번째 칸.
OFF = np.array([0.0, 0.0, -110.0])                # 유닛을 만드는 자리(받침 뒤쪽 옆) = 최종 + OFF
R_M = np.column_stack([(0, -1, 0), (0, 0, -1), (1, 0, 0)])
R_37 = np.column_stack([(-1, 0, 0), (0, 0, 1), (0, 1, 0)])
R_27 = np.column_stack([(1, 0, 0), (0, 0, 1), (0, -1, 0)])
R_GEAR = ori("+x", "+z"); R_RVB = ori("+x", "-z")
R_TB = ori("+x", "+z"); R_TF = ori("+x", "-z")
UNIT = []                                          # 유닛 부품(최종 자세로 만든 뒤 build_pose 로 옆자리로 보낸다)

s6 = A.step("[교재 6] 37프레임에 DC모터를 꽂아요: 모터 윗돌기 2개가 37프레임 가운데 줄의 1번째·5번째 칸(왼쪽 끝에서)에 들어가요. 모터 방향에 주의해요.")
p37 = s6.place("37프레임", R_37, (115, 35, -17.5))
motor = s6.attach("DC모터", R_M, {"p1": (p37, "h1_2"), "p2": (p37, "h5_2")}, hover=30)
UNIT += [p37, motor]

s7 = A.step("[교재 7 ①] 27프레임 구멍 3곳(가운데 줄 양옆 칸과 윗줄 가운데 칸)에 리벳 3개를 먼저 꽂아요.")
b27 = s7.place("27프레임", R_27, (115, 40, -22.5))
rvg = [s7.attach("리벳", R_RVB, {"p1": (b27, pt)}, rivet=True) for pt in ((105, 35, -22.5), (125, 35, -22.5), (115, 45, -22.5))]
s7b = A.step("[교재 7 ②] 리벳 위로 큰기어를 꽂아요: 기어의 팔 구멍 3곳(왼쪽·오른쪽·위)이 리벳 3개에 끼워져요.")
gear = s7b.recv("큰기어", R_GEAR, {"h1": (rvg[0], "p2"), "h5": (rvg[1], "p2"), "h2": (rvg[2], "p2")}, hover=22)
UNIT_GEAR = [b27] + rvg + [gear]

s8 = A.step("[교재 8] 7에서 만든 기어판을 37프레임 뒤에 대고, T축을 큰기어 가운데 구멍으로 끼워 27프레임·37프레임을 지나 모터 십자 구멍까지 꽂아요.")
tback = s8.attach("T축", R_TB, {"p1": (gear, "h3")}, hover=45, pegDepth=28.6, headDown=True)

s9 = A.step("[교재 9] 모터 앞쪽에 27프레임을 대고, 작은기어를 T축으로 앞쪽 십자 구멍에 꽂아요.")
f27 = s9.place("27프레임", R_27, (115, 40, 20.5))
sgear = s9.place("작은기어", R_GEAR, (115, 35, 27))
tfront = s9.attach("T축", R_TF, {"p1": (sgear, "h1")}, hover=45, pegDepth=28.6, headDown=True)

s10 = A.step("[교재 10] 긴 축을 두 판의 끝 구멍(37프레임 7번째 칸)에 끼우고 양쪽 끝을 부시로 막아요.")
axle = s10.place("축", ori("+x", "+z"), (85, 35, -0.5), dir=[0, 0, -1], hover=45, pegDepth=40, marks=[[85, 35, 23]])
bush_f = s10.place("부시", R_GEAR, (85, 35, 25.75), recv=True, dir=[0, 0, 1], hover=22, marks=[[85, 35, 32]])
bush_b = s10.place("부시", R_GEAR, (85, 35, -27.75), recv=True, dir=[0, 0, -1], hover=22, marks=[[85, 35, -33]])
UNIT += UNIT_GEAR + [tback, f27, sgear, tfront, axle, bush_f, bush_b]

# ───────── 11~13 ── 받침에 올리기, 메인보드 ─────────
s11 = A.step("[교재 11] 만든 모터 유닛을 받침(5)에 올려요: 모터 옆돌기 2개가 위 검정 315프레임의 구멍 2곳(오른쪽 끝에서 2번째·4번째)에 꽂혀요.")
s12 = A.step("[교재 12] 메인보드를 315프레임 위에 꽂아요: 보드 아래 돌기 2개가 315프레임 왼쪽 구멍 2곳(프레임 길이 방향으로 이웃한 두 칸)에 들어가요. 소켓 쪽이 총 앞(−X), 버튼 쪽이 모터(+X)예요.")
board = s12.attach("메인보드", Ry(90), {"p1": (top315, (15, 20, 0)), "p2": (top315, (35, 20, 0))}, hover=40)   # 사용자 지시 2026-10-03: 메인보드를 y축 +90° — 버튼 쪽이 모터(+X, 총의 뒤), 소켓 쪽이 앞(-X). 돌기 2개는 프레임 가운데 줄의 두 칸(20mm 간격)에 꽂힌다(교재 12)
s13 = A.step("[교재 13] 모터 선을 메인보드에 연결하면 받침 완성!", noPart=True)

# ───────── 14~32 ── 총몸·기둥·합체·타깃 (2026-10-02 1차: 부품 LIST 개수에 맞춘 구조 추정 — 위치는 전부 '추정', 화면에서 짚어 주면 고친다) ─────────
# 총몸은 받침 옆(BODY_O)에서 눕혀 만든다(층이 y 방향). 아래층: 앞(−x)부터 29프레임 D, 35프레임 C, 315프레임 A, 37프레임 B(A 끝에 직각, +z 쪽으로 뻗음).
# 블록 14개 = 14번 3(3단2·2단1) + 15번 2(3단1·2단1) + 16번 3(3단2·2단1) + 19번 2 + 26번 4(2단). 위층: D'·C'(17번), A'·B'(22번).
BODY_O = np.array([0.0, 0.0, 300.0])
R_L = R_LIE                                          # 눕힌 블록(긴 쪽 x, 돌기 면이 아래)
def up_pegs(blk): return [c["id"] for c in blk.conn["pegs"] if blk.world("peg", c)["dir"][1] > 0.9]
def pt(x, y, z): return (x + BODY_O[0], y + BODY_O[1], z + BODY_O[2])

s14 = A.step("[교재 14] 총몸 아래층: 검정 315프레임(A)과 37프레임(B)을 직각으로 맞대고(B 가 앞쪽 +z 로 뻗음), 블록 3개를 꽂아요: 3단블록은 이음매 위쪽 줄(A 끝 1칸 + B 2칸), 2단블록은 이음매 아래쪽 줄(A 끝 1칸 + B 3번째 줄 1칸), 또 하나의 3단블록은 B 맨 끝 줄의 구멍 3개(교재는 바깥 두 곳만 초록 원으로 표시하고, 양 끝 돌기를 꽂으면 가운데 돌기는 자동으로 꽂혀요). (교재에서 칸을 세어 맞춤)")
bA = s14.place("315프레임", R_FLAT, pt(75, 2.5, 0))
bB = s14.place_next("37프레임", R_Z, "홀면 +y 열1·줄3", bA, "홀면 +y 열15·줄1", (10, 0, 0))   # 315프레임 끝에서 한 칸 옆(앞 판을 고치면 따라온다)
k1 = s14.attach("3단블록", R_LIE, {"p5": (bA, pt(145, 5, -10)), "p4": (bB, pt(155, 5, -10)), "p3": (bB, pt(165, 5, -10))}, hover=60)
k2 = s14.attach("2단블록", R_LIE, {"p3": (bA, pt(145, 5, 10)), "p4": (bB, pt(155, 5, 10))}, hover=60)
k3 = s14.attach("3단블록", R_LIE, {"p5": (bB, pt(155, 5, 50)), "p4": (bB, pt(165, 5, 50)), "p3": (bB, pt(175, 5, 50))}, hover=60)
k3.extra["marks"] = [k3.extra["marks"][0], k3.extra["marks"][2]]   # 교재(칸 셈): B 맨 끝 줄 첫째·셋째 구멍 2곳에만 초록 원

s15 = A.step("[교재 15] 14번의 앞쪽(B 반대편) 끝에 35프레임(C)을 이어 붙이고, 블록 2개를 이음매에 꽂아요: 3단블록은 윗줄(C 끝 1칸 + 315프레임 1·2번째 칸), 2단블록은 아랫줄(C 끝 1칸 + 315프레임 1번째 칸), 가운데 줄은 비워요. (교재 스캔으로 확인: 초록 원 5개 = 돌기 3+2)")
bC = s15.place_next("35프레임", R_FLAT, "홀면 +y 열5·줄1", bA, "홀면 +y 열1·줄1", (-10, 0, 0))   # 315프레임 반대쪽 끝에서 한 칸 옆
k4 = s15.attach("3단블록", R_L, {"p5": (bC, pt(-5, 5, -10)), "p4": (bA, pt(5, 5, -10)), "p3": (bA, pt(15, 5, -10))}, hover=45)
k5 = s15.attach("2단블록", R_L, {"p3": (bC, pt(-5, 5, 10)), "p4": (bA, pt(5, 5, 10))}, hover=45)

s16 = A.step("[교재 16] 앞쪽에 29프레임(D)을 이어 붙이고, 블록 3개를 꽂아요: 맨 앞 3단블록은 D 끝 구멍 2개에(돌기 하나는 판 밖으로 나와요), 나머지는 D·C 이음매에. (추정)")
bD = s16.place_next("29프레임", R_FLAT, "홀면 +y 열9·줄1", bC, "홀면 +y 열1·줄1", (-10, 0, 0))   # 35프레임에서 한 칸 옆
k6 = s16.attach("3단블록", R_L, {"p5": (bD, pt(-65, 5, -10)), "p4": (bD, pt(-55, 5, -10)), "p3": (bC, pt(-45, 5, -10))}, hover=45)
k7 = s16.attach("3단블록", R_L, {"p4": (bD, pt(-135, 5, -10)), "p3": (bD, pt(-125, 5, -10))}, hover=60)   # 교재 16: 맨 앞 블록은 돌기 2개만 D 끝 구멍 2개에(셋째 돌기는 판 밖으로 나옴)
k8 = s16.attach("2단블록", R_L, {"p3": (bD, pt(-55, 5, 0)), "p4": (bC, pt(-45, 5, 0))}, hover=45)

def _tip(blk, pid):
    g = blk.peg(pid)
    return g["pos"] + g["dir"] * g["len"] / 2


def tips_in(blocks, xr, zr):
    """블록 윗돌기(+y 방향) 끝 점 중 판 범위(xr, zr, 몸 좌표) 안에 있는 것들."""
    out = []
    for b_ in blocks:
        for c in b_.conn["pegs"]:
            g = b_.world("peg", c)
            if g["dir"][1] > 0.9:
                t = g["pos"] + g["dir"] * g["len"] / 2 - BODY_O
                if xr[0] <= t[0] <= xr[1] and zr[0] <= t[2] <= zr[1]: out.append(rnd(t + BODY_O))
    return out
ALLK = [k1, k2, k3, k4, k5, k6, k7, k8]
s17 = A.step("[교재 17] 위층: 35프레임(C')과 29프레임(D')을 블록 윗돌기 위에 덮어요. (추정)")
tC = s17.place("35프레임", R_FLAT, pt(-25, 17.5, 0), recv=True, dir=[0, 1, 0], hover=45, marks=tips_over(ALLK))
tD = s17.place("29프레임", R_FLAT, pt(-95, 17.5, -5), recv=True, dir=[0, 1, 0], hover=45, marks=tips_over(ALLK))

s18 = A.step("[교재 18] T축 2개를 315프레임(A) 아래에서 위로 꽂아요(기어·방아쇠 축). (추정)")
tax1 = s18.place("T축", np.eye(3), pt(55, 14, -10), dir=[0, -1, 0], hover=50, pegDepth=28.6, headDown=True, marks=[list(pt(55, 5, -10))])   # 교재: 판 윗면 구멍에 초록 원
tax2 = s18.place("T축", np.eye(3), pt(95, 14, -10), dir=[0, -1, 0], hover=50, pegDepth=28.6, headDown=True, marks=[list(pt(95, 5, -10))])

# 19~20 방아쇠: 3단블록(T1)+2단블록(T2)을 빨간 15프레임 2개로 양옆에서 끼운다(블록 돌기면 ±x). 따로 만들었다가 21번에 T축 2번에 끼운다.
R_TRG = ori("+z", "+y")                                  # 블록 긴 쪽 z, 돌기면 ±x, 큰 구멍은 y 방향(T축이 지나감)
R_BAR = ori("+z", "+x")                                  # 빨간 막대: 긴 쪽 z, 구멍축 x
s19 = A.step("[교재 19] 방아쇠: 3단블록 양옆에 빨간 15프레임 2개를 끼워요 — 십자 블록 쪽 막대는 3번째·5번째 구멍에 3단블록 돌기 2개가, 반대쪽 막대는 1번째·3번째 구멍에 돌기 2개가 들어가요. 십자 블록(2단블록) 끝 돌기는 첫 번째 막대의 1번째 구멍에 들어가요.")
R_T2 = np.eye(3)                                         # 2단블록(십자 블록): 긴 쪽 x(막대와 직각), 큰 구멍은 y(T축이 지나감), 끝 돌기가 ±x(막대 구멍 쪽)
R_BAR_A = ori("+z", "-x")                                # +x 쪽 막대: 구멍 방향이 +x(블록 돌기가 +x 로 들어감)
t1 = s19.place("3단블록", R_TRG, pt(95, 10, 20))         # 막대와 나란한 3단블록(돌기면 ±x)
def side_pegs_t1(sgn): return [c["id"] for c in t1.conn["pegs"] if t1.world("peg", c)["dir"][0] * sgn > 0.9]
def pegs_t1(sgn):                                        # 3단블록 옆면(±x) 돌기 중 바깥 두 개(z 방향 20 간격)
    ids = sorted(side_pegs_t1(sgn), key=lambda i: t1.peg(i)["pos"][2]); return [ids[0], ids[-1]]
bar_l = s19.recv("15프레임", R_BAR_A, {"h3_1": (t1, pegs_t1(+1)[0]), "h5_1": (t1, pegs_t1(+1)[1])}, hover=45)  # 십자 블록 쪽 막대(+x): 3·5번째 구멍
bar_r = s19.recv("15프레임", R_BAR, {"h1_1": (t1, pegs_t1(-1)[0]), "h3_1": (t1, pegs_t1(-1)[1])}, hover=45)    # 반대쪽 막대(−x): 1·3번째 구멍(더 뻗음)
t2 = s19.attach("2단블록", R_T2, {"p1": (bar_l, "h1_1")}, hover=45)                                          # 십자 블록 끝 돌기가 첫 막대 1번째 구멍에
TRG = [t1, t2, bar_l, bar_r]
# 교재 21·22: 방아쇠(빨간 막대)는 T축을 중심으로 받침 앞쪽(+z)에서 오른쪽(+x)으로 기울어져 있다(약 8~23°, 평균 15° — 교재 그림 격자 계산)
TRG_ANGLE = 15.0
_Ry = Ry(TRG_ANGLE)
_Q = np.array([95.0, 0.0, -10.0]) + BODY_O                 # 피벗 = 두 번째 T축(x 95, 먼 줄 z −10)
for _p in TRG:
    _p.p = _Q + _Ry @ (_p.p - _Q); _p.R = _Ry @ _p.R
    for _k in ("marks", "settleMarks"):
        if _k in _p.extra: _p.extra[_k] = [rnd(_Q + _Ry @ (np.array(m, float) - _Q)) for m in _p.extra[_k]]
    if "dir" in _p.extra: _p.extra["dir"] = rnd(_Ry @ np.array(_p.extra["dir"], float))
s20 = A.step("[교재 20] 완성한 방아쇠에 고무밴드를 묶어요(고무밴드는 3D 모델이 없어 그림에서 뺐어요).", noPart=True)

s21 = A.step("[교재 21] 큰기어를 첫 번째 T축에, 방아쇠(십자 블록의 큰 구멍)를 두 번째 T축에 끼워요. 빨간 막대는 받침 앞쪽으로 늘어져요. (추정)")
gear_b = s21.place("큰기어", np.eye(3), pt(55, 9.5, -10), recv=True, dir=[0, 1, 0], hover=50, marks=[list(pt(55, 29, -10))], holeMarks=[list(pt(55, 5, -10))])   # 결합 위치 원은 프레임 구멍(T축이 서 있는 자리)에 고정
S21 = len(A.steps)                                        # 방아쇠가 합쳐지는 단계 번호(이 단계)
for p_ in TRG: to_side(p_, np.eye(3), np.array([95.0, 10.0, 5.0]) + BODY_O, np.array([95.0, 10.0, 265.0]) + BODY_O, S21, (0, 1, 0))
A.lock_marks(t2, 'settleMarks', [rnd(pt(95, 29, -10))]); A.lock_marks(t2, 'holeMarks', [rnd(pt(95, 5, -10))])   # 십자 블록(2단블록)의 큰 구멍에 두 번째 T축 끝이 들어감

s22 = A.step("[교재 22] 위층 315프레임(A')과 37프레임(B')을 블록 윗돌기와 T축 위에 덮어요. (추정)")
bAt = s22.place("315프레임", R_FLAT, pt(75, 17.5, 0), recv=True, dir=[0, 1, 0], hover=45, marks=tips_over(ALLK) + [list(pt(55, 29, -10)), list(pt(95, 29, -10))])
bAt.extra["faceMarks"] = [[m_[0], 20.0, m_[2]] for m_ in bAt.extra["marks"]]   # 결합 점은 허공(T축 끝 높이)이 아니라 위판 구멍 높이(판 윗면 y=20)에 — 사용자 지시
bBt = s22.place("37프레임", R_Z, pt(165, 17.5, 20), recv=True, dir=[0, 1, 0], hover=45, marks=tips_over(ALLK).where(lambda m_: float(np.linalg.norm(np.array(m_) - _tip(k3, 'p6'))) > 1))   # 교재 22: B 끝 블록(3단)은 바깥 돌기 2개에만 원(가운데 돌기 제외)

s23 = A.step("[교재 23] 빨간 부시 2개를 T축 끝에 끼우고, 리벳 1개를 위판 구멍에 꽂아요(고무밴드 걸이). (추정)")
bu1 = s23.place("부시", np.eye(3), pt(55, 26.25, -10), recv=True, dir=[0, 1, 0], hover=45, marks=[list(pt(55, 29, -10))])
bu2 = s23.place("부시", np.eye(3), pt(95, 26.25, -10), recv=True, dir=[0, 1, 0], hover=45, marks=[list(pt(95, 29, -10))])
rv23 = s23.attach("리벳", ori("+x", "-y"), {"p1": (bAt, "h5_3")}, hover=45, openEnd=True)   # 교재 23(칸 셈): 위판 가까운 줄(3번째 줄) 5열 = 첫 T축(6열) 바로 왼쪽 열, 고무밴드 걸이
rv23.extra["seated"] = True                           # 교재 23: 리벳은 이미 꽂힌 모양(구멍에 초록 원)

s24 = A.step("[교재 24] 고무밴드를 리벳과 방아쇠에 걸어요(고무밴드는 3D 모델이 없어 그림 없음).", noPart=True)

# 25: 블록 옆 큰 구멍에 리벳 4개를 먼저 꽂고(교재 그림), 그 위에 흰 19프레임·빨간 17프레임을 얹는다. 큰 구멍은 블록 옆면(z)을 관통한다.
R_RIN = ori("+x", "-z")                                  # 리벳 p1 이 +z 쪽을 향함(바깥 −z 쪽에서 블록 구멍으로)
s25 = A.step("[교재 25] 앞쪽 위 가장자리: 블록 옆 큰 구멍 4곳에 리벳을 꽂고, 그 위에 흰 19프레임과 빨간 17프레임을 얹어요. (추정)")
rvk = [s25.attach("리벳", R_RIN, {"p1": (blk_, hid)}, hover=45, openEnd=True) for blk_, hid in ((k7, "h2"), (k6, "h2"), (k6, "h3"), (k4, "h3"))]
for _r in rvk: _r.extra["seated"] = True               # 교재 25: 리벳 4개는 이미 꽂힌 모양, 막대만 내려온다
w19 = s25.recv("19프레임", ori("+x", "+z"), {"h1_1": (rvk[0], "p2"), "h9_1": (rvk[1], "p2")}, hover=45)
r17 = s25.recv("17프레임", ori("+x", "+z"), {"h1_1": (rvk[2], "p2"), "h7_1": (rvk[3], "p2")}, hover=45)
w19.extra["joinOrder"] = 2; r17.extra["joinOrder"] = 2   # 교재 25: 리벳 4개를 먼저 꽂고 흰·빨간 막대를 얹는다
BODY_EARLY = [bA, bB, bC, bD, tC, tD, bAt, bBt, tax1, tax2, gear_b, bu1, bu2, rv23] + ALLK + TRG
BODY_LATE = [w19, r17] + rvk                           # 25번에서 새로 놓는 부품(교재 25 는 총몸이 이미 세워진 방향)

# 26~27 기둥: 교재 그림처럼 눕혀서 만든다(27프레임 2장이 위·아래 층, 그 사이 양 끝에 2단블록 2개씩 = 4개, 옆면 큰 구멍에 리벳 2개 + 빨간 17프레임). 28번에 세워서 받침 위(x −25)로 옮긴다.
COLX, COLY0 = -30.0, 20.0                              # 기둥 최종 위치: 가운데 x, 받침 윗면 y
COLB = np.array([-25.0, 0.0, 120.0])                   # 눕혀 만드는 자리(받침 옆)
s26 = A.step("[교재 26] 기둥: 27프레임 아래판 위에 2단블록 4개(양 끝에 2개씩)를 꽂고 27프레임 윗판을 덮어요(눕혀서 만들어요). (추정)")
cbot = s26.place("27프레임", R_FLAT, tuple(COLB + np.array([0, 2.5, 0])))
colk = []
for cx in (-25, 25):
    for zz in (-5, 5):
        colk.append(s26.attach("2단블록", R_L, {"p3": (cbot, tuple(COLB + np.array([cx - 5, 5, zz]))), "p4": (cbot, tuple(COLB + np.array([cx + 5, 5, zz])))}, hover=45))
ctop = s26.recv("27프레임", R_FLAT, [(b_, pid) for b_ in colk for pid in ("p5", "p6")], p=tuple(COLB + np.array([0, 17.5, 0])), hover=45)
ctop.extra["joinOrder"] = 2                              # 교재 26: 블록 4개를 아래판에 먼저 꽂고 윗판을 나중에 덮는다
R_CRV = ori("+x", "+z")                               # 리벳 p1 이 −z(블록 구멍 쪽), p2 가 +z(바깥)
s27 = A.step("[교재 27] 기둥 옆면(+z) 바깥 블록의 큰 구멍 2곳에 리벳을 꽂고 빨간 17프레임을 얹어요. (추정)")
crv = [s27.attach("리벳", R_CRV, {"p1": (colk[1], "h1")}, hover=45, openEnd=True), s27.attach("리벳", R_CRV, {"p1": (colk[3], "h2")}, hover=45, openEnd=True)]
for _r in crv: _r.extra["seated"] = True               # 교재 27: 리벳 2개는 이미 꽂힌 모양, 17프레임만 내려온다
cr = s27.recv("17프레임", ori("+x", "+z"), {"h1_1": (crv[0], "p2"), "h7_1": (crv[1], "p2")}, hover=45)
cr.extra["joinOrder"] = 2                                # 교재 27: 리벳을 먼저 꽂고 빨간 17프레임을 얹는다
COL = [cbot, ctop, cr] + colk + crv

# 25번(교재): 총몸을 세워(층이 가로로 서고 37프레임 B 가 아래로, 위쪽 가장자리에 흰·빨간 막대) 최종 자리(받침 위)에 둔다. 28번에 기둥이 눕힌 자세에서 올라와 붙는다.
R_F = Rx(90); F0 = np.array([0.0, 105.0, 0.0])
def to_final_pt(q): return R_F @ (np.array(q, float) - BODY_O - np.array([0.0, 10.0, 0.0])) + F0
def body_final(part, at):
    pf = to_final_pt(part.p); Rf = R_F @ part.R
    part.extra["move"] = {"at": at, "p": rnd(pf), "r": R_to_euler(Rf), "dir": [0, 0, 1], "hover": 40}
def place_final(part):                                   # 25번에서 새로 놓는 부품은 세운 자세로 바로 둔다(marks·dir 도 같이)
    ex = part.extra
    for k in ("marks", "settleMarks"):
        if k in ex: ex[k] = [rnd(to_final_pt(m)) for m in ex[k]]
    if "dir" in ex: ex["dir"] = rnd(R_F @ np.array(ex["dir"], float))
    part.p = to_final_pt(part.p); part.R = R_F @ part.R
S25 = 26                                                 # = 교재 25번 단계(조립도 단계 번호 = 교재 번호 + 1)
for p_ in BODY_EARLY: body_final(p_, S25)
for p_ in BODY_LATE: place_final(p_)
R_COLF = np.column_stack([(0, 1, 0), (0, 0, 1), (1, 0, 0)])   # 눕힌 기둥(긴 쪽 x, 층 y, 폭 z) → 선 기둥(긴 쪽 y, 층 z, 폭 x)
def col_final(part, at):
    pb = part.p - COLB - np.array([0.0, 10.0, 0.0])
    pf = R_COLF @ pb + np.array([COLX, COLY0 + 35, 0.0]); Rf = R_COLF @ part.R
    part.extra["move"] = {"at": at, "p": rnd(pf), "r": R_to_euler(Rf), "dir": [0, 0, 1], "hover": 60}
# 교재 28·29: 총몸+기둥이 받침 위에 띄워진 채 합쳐지고(26~29), 29(교재)에 위에서 내려와 받침 흰 판 구멍에 결합한다 — lift
LIFT_BY = [0.0, 60.0, 0.0]
for _p in BODY_EARLY + BODY_LATE:
    _p.extra["lift"] = {"from": 26, "at": 30, "by": LIFT_BY, "dir": [0, 1, 0], "hover": 60, "marks": []}
S28 = len(A.steps) + 1
s28 = A.step("[교재 28] 기둥을 세워서 총몸 아래에 붙이고 받침 흰 판 위에 올려요(기둥 아래 블록 끝돌기가 받침 구멍에). (추정)")
for p_ in COL: col_final(p_, S28)
for _p in COL: _p.extra["lift"] = {"from": 29, "at": 30, "by": LIFT_BY, "dir": [0, 1, 0], "hover": 60, "marks": []}
# 기둥 아래 블록 2개(최종 x COLX±5)는 끝 돌기가 받침 흰 판 구멍(윗면 y=20, z=0)에 들어간다 — 내려올 때 화살표로 안내
for _b, _x in ((colk[0], COLX - 5), (colk[1], COLX + 5)): _b.extra["lift"]["marks"] = [[_x, 20.0, 0.0]]
for _b in colk[:2]:                                       # 교재 28: 기둥이 총몸 아래로 올라가 붙는다 — 올라간 자리(받침 위 LIFT_BY)에 안내점
    _m = _b.extra["move"]; _m["marks"] = [[_m["p"][0], _m["p"][1] + LIFT_BY[1], _m["p"][2]]]
s29 = A.step("[교재 29] 총몸과 기둥이 받침 위에 합체됐어요(28번에서 함께 올렸어요).", noPart=True)
s30 = A.step("[교재 30] 고무줄을 끼우면 오토건 본체 완성!(고무밴드는 3D 모델이 없어 그림 없음)", noPart=True)

# 31~32 타깃(받침과 별도): 29프레임을 세우고 아래에 2열브라켓(발이 −x 로 뻗음)을 리벳 2개로.
TO = np.array([130.0, 0.0, 220.0])   # 카메라가 −x·+z 쪽에서 보므로 총(받침 위)이 시선을 가리지 않는 빈자리
s31 = A.step("[교재 31] 타깃 만들기: 29프레임을 세우고 아래에 2열브라켓을 리벳 2개로 붙여요. (추정)")
tgt = s31.place("29프레임", ori("+y", "-x"), tuple(TO + np.array([0, 45, 0])))
R_TRV = ori("+y", "-x")
trv = [s31.attach("리벳", R_TRV, {"p1": (tgt, tuple(TO + np.array([0, yy, zz])))}, rivet=True) for yy, zz in ((15, 5), (25, -5))]   # 리벳 2개를 먼저 프레임에 꽂고
# 2열브라켓은 긴 판(구멍 2×2 h1~h4)이 프레임에 붙고 짧은 팔이 아래에서 −x 로 뻗는 발이 된다(교재 31). 리벳 뒤에 내려와 결합한다
brk = s31.recv("2열브라켓", ori("-z", "-x"), {"h1": (trv[0], "p2"), "h4": (trv[1], "p2")}, hover=45)
brk.extra["joinOrder"] = 2
s32 = A.step("[교재 32] 타깃 완성!", noPart=True)

C_FLIP = np.array([115.0, 35.0])                  # 뒤집는 축(유닛 가운데, 판 법선 z 방향): 교재 6~10 은 유닛이 최종 방향의 위아래를 뒤집은 모양(모터 돌기가 위)
def flipz(q): return np.array([2 * C_FLIP[0] - q[0], 2 * C_FLIP[1] - q[1], q[2]])
R_FLIP = np.diag([-1.0, -1.0, 1.0])               # z축 둘레 180°

def build_pose(part, off, at, marks=None):
    """유닛 부품: 지금 값은 최종 자세 → 교재 6~10 처럼 위아래를 뒤집어(z축 180°) 옆자리(off)에 두고, at 단계에서 최종 자세로 옮겨 붙게(move) 한다(motor 만 위 315프레임 구멍 안내 marks)."""
    fin_p, fin_R = part.p.copy(), part.R.copy(); ex = part.extra
    for k in ("marks", "settleMarks"):
        if k in ex: ex[k] = [rnd(flipz(np.array(m)) + off) for m in ex[k]]
    if "dir" in ex: ex["dir"] = rnd(R_FLIP @ np.array(ex["dir"], float))
    part.p = flipz(fin_p) + off; part.R = R_FLIP @ fin_R
    mv = {"at": at, "p": rnd(fin_p), "r": R_to_euler(fin_R), "dir": [0, 1, 0], "hover": 30}
    if marks: mv["marks"] = marks
    ex["move"] = mv
S12 = 12                                          # 유닛이 받침에 올라가는 단계(교재 11)
for pt_ in UNIT:
    msm = settle_marks(pt_, [top315]) if pt_ is motor else None
    build_pose(pt_, OFF, S12, marks=msm)
# 7단계 기어판은 책 그림처럼 위에서 본 모양(27프레임을 눕히고 그 위에 큰기어, 리벳 윗쪽)으로 옆자리에서 만들고, 8단계에 37프레임 뒤로 세워 붙인다.
# 합칠 때 띄우는 방향은 모터 반대쪽(−z, 뒤): 모터 쪽(+z)으로 띄우면 기어가 모터를 뚫고 지나가 보인다(사용자 지적).
GC = np.array([115.0, 35.0, -25.0]) + OFF
for pt_ in UNIT_GEAR:
    to_side(pt_, Rx(90), GC, np.array([115.0, 25.0, -230.0]), 9, (0, 0, -1))

# 카메라(교재 그림 방향): camfit.py 로 교재 그림의 판 모서리 4점 → solvePnP (2026-10-02). 오차 3px 이하만 'fit', 나머지는 'guess'.
#  단계 번호는 조립도 단계(교재 6 이후는 7①·7② 때문에 교재 번호 +1~).  값 = (theta, phi, 출처)
CAMS = {k: (0.9, 1.0, "guess") for k in range(1, len(A.steps) + 1)}
CAMS[1] = (0.85, 0.97, "fit")      # 교재 1: 검은 315프레임 4점, 오차 2.9px, 방위 48.7° 고도 34.2°
CAMS[2] = (0.69, 0.91, "guess")    # 교재 2: 같은 4점, 오차 4.0px(방위 39.3° 고도 37.7°) — 3px 초과라 짐작으로 둠
CAMS[3] = (0.74, 0.98, "guess")    # 교재 3: 오차 1.5px 이지만 왼쪽 위 모서리 1점은 블록에 가려 추정
CAMS[4] = (0.68, 1.05, "guess")    # 교재 4: 3·5 사이 값(맞추지 못함)
CAMS[5] = (0.61, 1.13, "fit")      # 교재 5: 위 검은 판 4점, 오차 1.9px, 방위 35.0° 고도 25.1°
CAMS[7] = (0.9, 0.55, "guess"); CAMS[8] = (0.9, 0.55, "guess")   # 교재 7 은 위에서 본 그림
CAMS[12] = (0.75, 1.07, "fit")     # 교재 11: 위 검은 판 4점, 오차 2.2px, 방위 42.9° 고도 28.5°
CAMS[13] = (-0.9, 1.01, "guess")   # 교재 12: 흰 윗판 4점 오차 4.9px — 카메라가 반대편(방위 −51°)으로 돌아감
CAMS[14] = (-0.9, 1.0, "guess")    # 교재 13: 판이 가려져 오차 31px — 교재 12 와 같은 시점으로 봄
# 6·9·10·11단계(교재 6·8·9·10, 유닛): 유닛을 교재처럼 위아래 뒤집은 방향(돌기가 위)으로 만들었다. 교재 6 의 37프레임 4점(뒤집은 자세)으로 맞춘 값 — 방위 −151.3° 고도 42.5°, 오차 5.3px(fov 20, 3px 초과) → 짐작으로 둔다. 8·9·10 은 같은 시점으로 그린 그림이라 같은 값.
for k in (6, 9, 10, 11): CAMS[k] = (-2.64, 0.83, "guess")
for k in range(15, 26): CAMS[k] = (-0.82, 1.03, "guess")    # 교재 14~24(총몸 눕혀 만드는 단계): 교재 14 의 315프레임 4점 오차 5.9px(방위 −47° 고도 31°) → 짐작으로 두고 같은 시점으로 봄
CAMS[20] = (-2.356, 0.87, "guess"); CAMS[21] = (-2.356, 0.87, "guess")   # 교재 19·20: 막대가 오른쪽 위로 뻗는 기울기 약 32° ↔ 방위 −135° 고도 40°(구멍 5점 맞춤은 오차 20px라 쓰지 않음)
CAMS[22] = (-0.358, 0.78, "guess"); CAMS[23] = (-0.44, 1.10, "guess"); CAMS[24] = (-0.44, 1.10, "guess"); CAMS[25] = (-0.44, 1.10, "guess")   # 교재 21: 구멍 격자 벡터 → 방위 −20.5° 고도 45.5°(격자 오차 0.2px) / 교재 22: 판 두 기울기 → 방위 −25° 고도 27° / 24·25 는 같은 시점으로 봄(미확인)
CAMS[26] = (-0.96, 1.18, "guess")   # 교재 25: 윗면 기울기 약 −0.6 → 방위 −55° 고도 22°(추정)
for k in (29, 30, 31): CAMS[k] = (-0.576, 1.309, "guess")   # 교재 28~30: 총신이 거의 수평(기울기 −0.17), 옆면이 크게 보이는 낮은 시점 → 방위 −33° 고도 15°(추정 — 📷 로 사용자가 맞춘 값으로 바꿀 것)
for k in (27, 28): CAMS[k] = (-0.51, 1.05, "guess")   # 교재 26·27(눕힌 기둥): 판 긴 쪽이 왼쪽 아래→오른쪽 위(기울기 −0.28) → 방위 −29° 고도 30°(추정 — 📷 로 사용자가 맞춘 값으로 바꿀 것)
CAMS[32] = (-1.1, 1.45, "guess"); CAMS[33] = (-1.1, 1.45, "guess")   # 교재 31: 판 4점, 오차 3.1px(3px 초과라 짐작으로 둠), 방위 −117.9° 고도 6.9° / 교재 32 는 같은 시점으로 봄
TIGHT = set(range(15, 28)) | {32, 33}                # 총몸 만들기(15~27)와 타깃(32·33)은 그 부분만 크게
# 바닥 방향선(원점) 위치: 총몸·방아쇠·기둥·타깃은 원점에서 떨어진 자리에서 만들므로 그 자리의 기준점에 방향선을 둔다(안내서 3절 기본 규칙)
AXES = {}
for k in list(range(15, 20)) + list(range(22, 26)): AXES[k] = tuple(BODY_O)                          # 총몸 작업대: 판 A 왼쪽 끝 가운데가 (0,0,0)
for k in (20, 21): AXES[k] = tuple(np.array([95.0, 0.0, 265.0]) + BODY_O)                              # 따로 만드는 방아쇠 자리
for k in (27, 28): AXES[k] = tuple(COLB)                                                                # 눕혀 만드는 기둥 자리
for k in (32, 33): AXES[k] = tuple(TO)
for k in (7, 8): AXES[k] = (115.0, 0.0, -230.0)                                                               # 기어판을 따로 만드는 옆자리(교재 7①·7②)                                                                  # 타깃 자리
# 교재 29: 기둥 아래 블록 2개의 끝 돌기가 받침 흰 판(59프레임) 구멍 2곳에 — 결합 점(구멍에 고정)
RINGS = {}
FOCUS = {                                              # 부품이 없는 단계: 총몸·타깃을 가운데에 크게
    21: [pt(70, 0, 235), pt(125, 25, 320)], 25: [pt(25, 0, -30), pt(135, 35, 50)],   # 25(교재 24): 기어·두 T축·리벳·방아쇠 부분만 크게(교재가 그 부분만 가까이 그림)
      # 21: 따로 만든 방아쇠(옆자리 위)를 가운데에
    30: [(-145, 20, -10), (180, 125, 10)], 31: [(-145, 20, -10), (180, 125, 10)], 33: [tuple(TO + np.array([-20, 0, -15])), tuple(TO + np.array([5, 90, 15]))],
}
for k, v in CAMS.items():
    th, ph, src = v[:3]
    A.steps[k - 1].cam = (th, ph, k in TIGHT, FOCUS.get(k), AXES.get(k), RINGS.get(k)); A.steps[k - 1].camSrc = src

A.save_links()                                    # 이번 빌드의 잠금 기록 저장(수정 지시가 있는 빌드는 갱신하지 않는다)
A.check_fixes()                                   # 적용되지 않은 수정 지시가 있으면 경고(번호가 밀렸거나 오타)
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("autogun_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("autogun_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
