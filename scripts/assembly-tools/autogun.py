# 큐보 1권 오토건(교재 64~69쪽, 32단계) — 조립 프로그램(asmlib)으로 만든다. 1~13: 받침(총이 올라앉는 흰 판+모터+메인보드), 14~28: 총몸, 29: 합체, 30: 고무줄, 31~32: 타깃.
# 좌표: 바닥 y=0(받침 흰 판 아랫면), 315프레임은 +x 로 뻗고(x 0~150, z ±15), 흰 59프레임은 그 왼쪽(x −50~0, 긴 쪽이 z −45~45)에 길이 방향이 직각으로 맞닿는다.
# 구멍 번호는 교재 그림의 판 모서리 위치(+x = 화면 오른쪽 아래, −z = 오른쪽 위)에서 읽었다(짐작 포함 — 안내서 5-7절).
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-1-autogun", "오토건", "교재 64~69쪽 · 오토건 (1~32단계)", camera={"target": [60, 20, 0], "radius": 380, "theta": 0.9, "phi": 1.0},
        listNote="고무밴드(3D 모델 없음)는 조립도에서 제외했다")
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
s12 = A.step("[교재 12] 메인보드를 315프레임 위에 꽂아요: 보드 아래 돌기 2개가 315프레임 왼쪽 구멍 2곳에 들어가요.")
board = s12.attach("메인보드", np.eye(3), {"p1": (top315, (25, 20, -10)), "p2": (top315, (25, 20, 10))}, hover=40)
s13 = A.step("[교재 13] 모터 선을 메인보드에 연결하면 받침 완성!", noPart=True)

def build_pose(part, off, at, marks=None):
    """유닛 부품: 지금 값은 최종 자세 → 옆자리(off) 자세로 바꿔 p 에 두고, at 단계에서 최종 자세로 옮겨 붙게(move) 한다(motor 만 위 315프레임 구멍 안내 marks)."""
    fin_p, fin_R = part.p.copy(), part.R.copy(); ex = part.extra
    for k in ("marks", "settleMarks"):
        if k in ex: ex[k] = [rnd(np.array(m) + off) for m in ex[k]]
    part.p = fin_p + off
    mv = {"at": at, "p": rnd(fin_p), "r": R_to_euler(fin_R), "dir": [0, 1, 0], "hover": 30}
    if marks: mv["marks"] = marks
    ex["move"] = mv
for pt in UNIT:
    msm = settle_marks(pt, [top315]) if pt is motor else None
    build_pose(pt, OFF, 12, marks=msm)
# 7단계 기어판은 책 그림처럼 위에서 본 모양(27프레임을 눕히고 그 위에 큰기어, 리벳 윗쪽)으로 옆자리에서 만들고, 8단계에 37프레임 뒤로 세워 붙인다.
# 합칠 때 띄우는 방향은 모터 반대쪽(−z, 뒤): 모터 쪽(+z)으로 띄우면 기어가 모터를 뚫고 지나가 보인다(사용자 지적).
GC = np.array([115.0, 35.0, -25.0]) + OFF
for pt in UNIT_GEAR:
    to_side(pt, Rx(90), GC, np.array([115.0, 25.0, -230.0]), 9, (0, 0, -1))

# 카메라(교재 그림 방향): 1~5 는 책 그림이 +x 가 화면 오른쪽 아래로 가게 그려져 있다 → 방위 θ≈0.9, 고도 φ≈1.0 (모두 짐작 'guess')
CAMS = {k: (0.9, 1.0) for k in range(1, 15)}
CAMS[7] = (0.9, 0.55); CAMS[8] = (0.9, 0.55)   # 교재 7 은 위에서 본 그림
for k, (th, ph) in CAMS.items():
    A.steps[k - 1].cam = (th, ph); A.steps[k - 1].camSrc = "guess"

A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("autogun_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("autogun_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
