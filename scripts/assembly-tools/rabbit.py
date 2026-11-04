# 큐보 1권 토끼(교재 13~16쪽 · 토끼·양떼저울) — 저장 데이터를 결합(recv·attach)으로 옮긴 것(2026-11-03): 프레임·블록·리벳 위치는 규칙이 계산한다.
import json
import numpy as np
from asmlib import *

A = Asm("cubo-1-rabbit", '토끼', '교재 13~16쪽 · 토끼·양떼저울', camera={'target': [8, 34, 0], 'radius': 240, 'theta': 1.05, 'phi': 1.1})

s1 = A.step('35프레임 2개를 나란히 놓고, 3단블록 2개의 돌기를 프레임 구멍에 꽂아 이어요.', cam=(-2.81, 0.39, False, None, None, None), camSrc='eye')   # 1번 카메라 = 1_P 격자 axes_fit(오차 0.47px, 칸 −Z·줄 −X, roll −0.2°). 책 그림의 3단블록 돌기 위치(왼쪽 판 1개·오른쪽 판 2개)와 모델이 같은 해
v1_0 = s1.place('35프레임', euler_to_R([0, -90, 0]), (-15, 17.5, 0))   # 1번은 원점 중심(A4): 두 프레임 + 블록 범위 x −30~30 이 가운데
v1_1 = s1.place('35프레임', euler_to_R([0, -90, 0]), (15, 17.5, 0))
v1_2 = s1.attach('3단블록', euler_to_R([90, 0, 0]), {'p5': (v1_0, 'h2'), 'p4': (v1_0, 'h1'), 'p3': (v1_1, 'h3')}, dir=[0, 1, 0])
v1_3 = s1.attach('3단블록', euler_to_R([90, 0, 0]), {'p5': (v1_0, 'h14'), 'p4': (v1_0, 'h13'), 'p3': (v1_1, 'h15')}, dir=[0, 1, 0])

s2 = A.step('2단블록 2개를 눕혀서 돌기 2개씩, 바닥 프레임 뒤쪽 끝 두 열 구멍에 꽂아요(3단블록 반대쪽 끝).', cam=(-2.16, 0.64, False, None, None, None), camSrc='eye')   # 2_P 격자(30점 0.93px) axes_fit 칸 +Z 줄 -X (거울 쌍 중 2단블록이 x 25·35 에 가는 쪽)
v2_0 = s2.attach('2단블록', euler_to_R([90, 0, 0]), {'p3': (v1_1, 'h5'), 'p4': (v1_1, 'h4')}, dir=[0, 1, 0])
v2_1 = s2.attach('2단블록', euler_to_R([90, 0, 0]), {'p3': (v1_1, 'h11'), 'p4': (v1_1, 'h10')}, dir=[0, 1, 0])

s3 = A.step('35프레임을 세워서 3단블록의 머리 쪽(2단블록 반대편) 끝 돌기에 끼워요.', view=1, cam=(-2.04, 0.86, False, None, None, None), camSrc='eye')   # 3_F 격자(15점 0.55px) axes_fit 칸 +Z 줄 -Y (거울 쌍 중 −X 쪽에서 보는 해)
v3_0 = s3.recv('35프레임', euler_to_R([-90, 90, 0]), {'h13': (v1_2, 'p2'), 'h1': (v1_3, 'p2')}, dir=[-1, 0, 0])

s4 = A.step('리벳 4개를 끼워 고정해요.', view=2, cam=(-1.94, 1.01, False, None, None, None), camSrc='eye')   # 4_F mkfit3d(3번 모델 3D ↔ 구멍 원 11개 중 6개, 평균 1.34px·최대 2.39px)
v4_0 = s4.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v3_0, 'h2')}, dir=[-1, 0, 0], rivet=True)
v4_1 = s4.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v3_0, 'h3')}, dir=[-1, 0, 0], rivet=True)
v4_2 = s4.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v3_0, 'h14')}, dir=[-1, 0, 0], rivet=True)
v4_3 = s4.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v3_0, 'h15')}, dir=[-1, 0, 0], rivet=True)

s5 = A.step('15프레임 2개를 양옆에 세워요(토끼 귀).', view=2, cam=(-1.87, 1.42, False, None, None, None), camSrc='eye')   # 5_F mkfit3d(4번 모델 3D ↔ 리벳 머리 4+돌기 점 2, 평균 1.20px·최대 2.01px)
v5_0 = s5.recv('15프레임', euler_to_R([0, 0, 90]), {'h2': (v4_0, 'p2'), 'h3': (v4_1, 'p2'), 'h1': (v1_3, 'p2')}, dir=[-1, 0, 0], hover=57)   # 책 5번: 프레임이 판에서 25mm 옆(화면 220px)으로 떠 있다 → hover 57
v5_1 = s5.recv('15프레임', euler_to_R([0, 0, 90]), {'h2': (v4_2, 'p2'), 'h3': (v4_3, 'p2'), 'h1': (v1_2, 'p2')}, dir=[-1, 0, 0], hover=57)

s6 = A.step('리벳 2개를 끼워 고정해요.', view=2, cam=(-1.99, 1.38, False, None, None, None), camSrc='eye')   # 6_F mkfit3d(5번 모델 3D ↔ 판 구멍 3+프레임 구멍 4, 평균 1.68px·최대 3.30px)
v6_0 = s6.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v5_0, 'h1')}, dir=[-1, 0, 0], rivet=True)
v6_1 = s6.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v5_1, 'h1')}, dir=[-1, 0, 0], rivet=True)

s7 = A.step('35프레임을 앞에 한 겹 더 붙여요.', view=2, cam=(-1.99, 0.93, False, None, None, None), camSrc='eye')   # 7_N holefit 12점 0.78px, axes_fit 15점 1.26px
v7_0 = s7.recv('35프레임', euler_to_R([-90, 90, 0]), {'h13': (v6_1, 'p2'), 'h1': (v6_0, 'p2'), 'h15': (v4_3, 'p2'), 'h2': (v4_0, 'p2'), 'h3': (v4_1, 'p2'), 'h14': (v4_2, 'p2')}, dir=[-1, 0, 0], hover=55)   # 책 7번: 리벳 머리→링 305px = 프레임 높이(5구멍) 350px 의 0.87배. 화면 hover 55 에서 같은 비 0.88, 73 에서 1.33(너무 멂)

s8 = A.step('리벳 2개를 끼워 고정해요.', view=2, cam=(-1.92, 1.21, False, None, None, None), camSrc='eye')   # 8_N mkfit3d(7번 모델 3D ↔ 구멍 테두리·모서리 9점, 평균 1.35px·최대 2.71px)
v8_0 = s8.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v7_0, 'h4')}, dir=[-1, 0, 0], rivet=True)
v8_1 = s8.attach('리벳', euler_to_R([0, 0, 90]), {'p1': (v7_0, 'h10')}, dir=[-1, 0, 0], rivet=True)

s9 = A.step('15프레임을 앞쪽 아래에 붙여요.', view=2, cam=(-1.92, 1.21, False, None, None, None), camSrc='eye')   # 9_N mkfit3d(8번 모델 3D ↔ 15프레임 흰 구멍 4+판 점 4, 평균 1.31px·최대 2.04px)
v9_0 = s9.recv('15프레임', euler_to_R([-90, 90, 0]), {'h2': (v8_0, 'p2'), 'h4': (v8_1, 'p2'), 'h1': (v6_0, 'p2'), 'h5': (v6_1, 'p2')}, dir=[-1, 0, 0], hover=39)   # 책 9번: 리벳 머리→링 112px ÷ −X 4.5px/mm ≈ 25mm 떠 있음 → +14 = 39

s10 = A.step('눈블록 2개를 앞판에 꽂아요.', view=2, cam=(-1.89, 1.23, False, None, None, None), camSrc='eye')   # 10_N mkfit3d(9번 모델 3D ↔ 15프레임 흰 구멍 4+판 점 3, 평균 1.38px·최대 3.34px)
# 책 10번: 구멍 링→눈 중심 거리 206px = 칸 간격 2.06배, 화면 기본 hover(22)에서 1.18배 → 22×1.75 ≈ 38
v10_0 = s10.attach('눈블록', euler_to_R([90, 90, 0]), {'p1': (v7_0, 'h6')}, dir=[-1, 0, 0], hover=38)
v10_1 = s10.attach('눈블록', euler_to_R([90, 90, 0]), {'p1': (v7_0, 'h12')}, dir=[-1, 0, 0], hover=38)

s11 = A.step('25프레임을 3단블록 위 돌기 4개에 얹어요.', cam=(2.39, 0.57, False, None, None, None), camSrc='eye')   # 11_P mkfit3d(10번 모델 3D ↔ 돌기 링 4+프레임 링 3+판 흰 구멍 4, 평균 1.87px·최대 3.29px)
v11_0 = s11.recv('25프레임', euler_to_R([0, -90, 0]), {'h1': (v1_2, 'p6'), 'h2': (v1_2, 'p8'), 'h9': (v1_3, 'p6'), 'h10': (v1_3, 'p8')}, dir=[0, 1, 0], hover=36)   # 책 11번: 프레임 링이 돌기 위 36mm(PnP d 스캔)

s12 = A.step('25프레임 하나를 더, 3단블록·2단블록 위 돌기 4개에 얹어요(앞 덮개 뒤쪽 옆).', cam=(1.93, 0.57, False, None, None, None), camSrc='eye')   # 12_P mkfit3d(11번 모델 3D ↔ 돌기 링 4+프레임 링 4, 평균 1.20px·최대 1.97px)
v12_0 = s12.recv('25프레임', euler_to_R([0, -90, 0]), {'h2': (v1_2, 'p7'), 'h10': (v1_3, 'p7'), 'h3': (v2_0, 'p6'), 'h7': (v2_1, 'p6')}, dir=[0, 1, 0], hover=42)   # 책 12번: 프레임 링이 돌기 위 42mm(PnP d 스캔)

s13 = A.step('T축을 작은기어에 끼워요(따로 조립). 기어 가운데 구멍으로 T축을 위에서 내려 끼워요.', cam=(-0.02, 0.89, False, None, None, None), camSrc='eye')   # 13_axes.json: mkfit3d 7점(기어 윗면 이빨 4곳·가운데·T축 머리·끝) 평균 1.05px·최대 2.01px
s14 = A.step('15프레임이 아래에서 올라와 T축 가운데 구멍에 끼워지고, 그다음 부시가 올라와 T축 끝에 끼워 고정돼요(따로 조립). 지금은 끼우기 전 모습이에요.', cam=(1.59, 0.88, False, None, None, None), camSrc='eye')   # 14_axes.json: mkfit3d 8점(기어 이빨 3·T축 머리·떠 있는 15프레임 구멍 4) 평균 1.60px·최대 2.70px
# 13·14번은 옆자리(창고 2)에서 따로 조립 — 모든 부품을 15번에서 합쳐진 최종 자리에서 결합 규칙으로 계산하고(15프레임은 2단블록 돌기, 기어는 프레임 위 flush, T축은 기어 구멍 입구에서 아래로, 부시는 프레임 아래 flush), 같은 강체 변환(to_side)으로 옆자리로 보낸다. 손 좌표 없음.
_R14 = euler_to_R([0, -90, 0])
v14_0 = s14.recv('15프레임', _R14, {'h2': (v2_0, 'p5'), 'h4': (v2_1, 'p5')}, dir=[0, -1, 0], hover=44, explode={'step': 14, 'order': 1})
_tips14 = v14_0.extra['marks']; v14_0.extra['marks'] = []   # 15번에서 합칠 때의 안내점 = 2단블록 돌기 끝(결합에서 계산)
_Rb = euler_to_R([0, 0, 0])
v14_1 = s14.place_rest('부시', _Rb, 'h1', v14_0, 'h3', (0, -1, 0), dir=[0, -1, 0], hover=66, joinOrder=2, recv=True)   # 책 14번 PnP(fits/14_N 7점 1.56px) 투영: 부시 윗면 가운데가 책 초록 링 중심(512,760)에 오는 hover = 66.1(실루엣 윗가장자리로는 66.6). 면과 면은 자석처럼 붙는다 — 부시 몸통 윗면이 프레임 홀 테두리 아래 끝면에 닿는다(겹침·틈 없음)
_Rg = euler_to_R([0, 0, 0])
v13_0 = s13.place_rest('작은기어', _Rg, 'h1', v14_0, 'h3', (0, 1, 0))   # 기어 몸통 아랫면이 프레임 홀 테두리 윗면에 닿는다
v13_1 = s13.attach('T축', euler_to_R([180, 0, 0]), {'p1': (v13_0, 'h1')}, dir=[0, 1, 0], hover=45)   # 몸통이 기어·프레임 구멍을 지난다
_Cf = np.array(v14_0.p, float)
def _low(q):   # 옆자리에서 끼우기 직전까지 띄웠을 때 부품 맨 아래(몸통 반높이까지)가 바닥(y=0) 아래로 내려가지 않게 올릴 높이
    sz = np.array(partlib.get(q.n)["size"], float); hy = float((np.abs(q.R) @ (sz / 2))[1])
    return float(q.extra.get("hover", 0)) - float(q.p[1]) + hy
_lift = max(_low(q) for q in (v13_0, v13_1, v14_0, v14_1))
_Cs = np.array([0.0, _Cf[1] + _lift, 0.0])   # 새 창고(2)는 화면 가운데(원점, A4) — 본체는 hideMade 로 숨어 있어 옆으로 띄울 필요가 없다. 높이만 바닥 아래로 안 내려가게 _lift   # 옆자리(창고 2): 높이는 띄운 부품이 바닥 아래로 안 가는 최소값(계산), 옆으로 70 = 창고 2 간격
for _q in (v13_0, v13_1, v14_0, v14_1): to_side(_q, np.eye(3), _Cf, _Cs, 15, (0, 1, 0))
v14_0.extra['settleMarks'] = [list(m) for m in _tips14]

s15 = A.step('13·14단계에서 만든 것을 2단블록 위 돌기 2개(덮개 옆 맨 끝 열)에 끼워요.', cam=(2.21, 0.80, False, None, None, None), camSrc='eye')   # 15_axes.json: mkfit3d 6점(빨간 귀 구멍 4·2단블록 돌기 링 2, 읽기 ±4px 안에서 조정)
s15.kw["madeNoPart"] = True   # 새 부품 없는 합치는 번호(13·14번 조립품을 2단블록 돌기에 끼움)

s16 = A.step('15프레임을 2단블록 끝 돌기 2개(프레임의 2·4번째 구멍)에 끼워요.', cam=(1.96, 1.17, False, None, None, None), camSrc='eye')   # 16_axes.json: mkfit3d 8점(빨간 귀 구멍 4·2단블록 옆 돌기 링 2·떠 있는 프레임 구멍 링 2, 읽기 ±3px 안에서 조정)
v16_0 = s16.recv('15프레임', euler_to_R([-90, 90, 0]), {'h4': (v2_0, 'p1'), 'h2': (v2_1, 'p1')}, dir=[1, 0, 0], hover=40)   # 책 16번: 프레임 링이 돌기 끝에서 +X 로 약 40mm(PnP g 스캔)

s17 = A.step('리벳 1개를 3단블록 옆 구멍(머리 쪽 끝)에 끼워 고정해요.', cam=(2.44, 1.31, False, None, None, None), camSrc='eye')   # 17_axes.json: mkfit3d 6점(빨간 귀 구멍 4·앞 프레임 돌기 끝 1·꽂힌 리벳 받침) 평균 1.44px·최대 1.80px
v17_0 = s17.attach('리벳', euler_to_R([-90, 0, 180]), {'p1': (v1_2, 'h1')}, dir=[0, 0, -1], rivet=True)

s18 = A.step('1열브라켓 하나를 오른쪽 앞다리로 붙여요. 세로 판(30mm)이 밖, 발바닥(30mm)은 안쪽이에요. 리벳은 위쪽 구멍에 끼워요(리벳 홈 방향 주의).', cam=(2.41, 1.14, False, None, None, None), camSrc='eye')   # 18_axes.json: mkfit3d 6점(빨간 귀 앞면 구멍 4·벽 리벳 끝 링 2) 평균 1.95px·최대 2.85px
v18_0 = s18.recv('1열브라켓', euler_to_R([0, 0, 0]), {'h4': (v17_0, 'p2')}, dir=[0, 0, -1])

s19 = A.step('리벳 1개를 반대쪽 3단블록 옆 구멍(머리 쪽 끝)에 끼워 고정해요.', cam=(0.78, 1.15, False, None, None, None), camSrc='eye')   # 19_axes.json: mkfit3d 6점(빨간 귀 앞면 구멍 4·벽 리벳 끝 링 2, fov 24) 평균 1.91px·최대 2.99px
v19_0 = s19.attach('리벳', euler_to_R([-90, 0, 180]), {'p2': (v1_3, 'h1')}, dir=[0, 0, 1], rivet=True)

s20 = A.step('1열브라켓 하나를 왼쪽 앞다리로 붙여요. 세로 판(30mm)이 밖, 발바닥(30mm)은 안쪽이에요. 리벳은 위쪽 구멍에 끼워요(리벳 홈 방향 주의).', cam=(0.45, 1.26, False, None, None, None), camSrc='eye')   # 20_axes.json: mkfit3d 6점(빨간 귀 앞면 구멍 4·벽 리벳 끝 링 2, fov 30) 평균 1.96px·최대 4.43px
v20_0 = s20.recv('1열브라켓', euler_to_R([-180, 0, 180]), {'h4': (v19_0, 'p1')}, dir=[0, 0, 1])

s21 = A.step('리벳 2개를 뒤 막대(15프레임) 양 끝 구멍에 끼워요. 리벳 홈 방향에 주의해요.', cam=(1.17, 1.22, False, None, None, None), camSrc='eye')   # 21_axes.json: mkfit3d 6점(빨간 귀 앞면 구멍 4·벽 리벳 끝 링 2, fov 25) 평균 1.35px·최대 2.21px (책 21번 그림 하나를 21·22단계가 같이 쓴다)
v21_0 = s21.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v16_0, 'h1')}, dir=[1, 0, 0], rivet=True)
v21_1 = s21.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v16_0, 'h5')}, dir=[1, 0, 0], rivet=True)

s22 = A.step('2열브라켓 2개를 뒷다리로 붙이면 완성! 긴 쪽(30mm, 구멍 4개 판)이 밖(막대에 닿는 면), 발바닥(25mm)은 안(앞쪽, 몸체 아래)이에요. 리벳은 위쪽 구멍에 끼워요.', cam=(1.17, 1.22, False, None, None, None), camSrc='eye')   # 22_axes.json: 21번과 같은 책 그림·같은 6점(평균 1.35px)
v22_0 = s22.recv('2열브라켓', euler_to_R([-90, 90, 0]), {'h2': (v21_0, 'p1')}, dir=[1, 0, 0])   # 2단블록 옆 돌기는 이미 막대 한 장을 지나므로 브라켓 구멍에 꽂지 않는다(규칙 7: 돌기는 프레임 한 장)
v22_1 = s22.recv('2열브라켓', euler_to_R([-90, 90, 0]), {'h4': (v21_1, 'p1')}, dir=[1, 0, 0])

for _q in (v22_0, v22_1): _q.extra["faceMarks"] = [list(_m) for _m in _q.extra["marks"]]   # 판 바깥 면 구멍 자리 = 돌기 끝 자리(x 같음) — 손 좌표 대신 계산값(전체 위치가 옮겨져도 따라간다)
import stepchecks; stepchecks.apply(A, "rabbit")

# ── 작업 공간(창고) 정리(04, 1차) — 책을 1→21번 순서로 보며 정했다(2026-11-04).
#   번호표로 확인: 15번 "12 + 14". 나머지는 그림 모양으로 판단(추정):
#   1~12번 본체(창고 1) / 13~14번 작은기어·T축·15프레임·부시를 따로 조립(창고 2) → 15번에서 본체와 합침(번호가 작은 창고 1에서) / 15~22번 창고 1에서 이어서.
_SLOT_RB = {**{i: 1 for i in range(1, 13)}, 13: 2, 14: 2, **{i: 1 for i in range(15, 23)}}
for _i, _sl in _SLOT_RB.items(): A.steps[_i - 1].kw["slot"] = _sl
_HIST_RB = {13: "📦 본체(1~12번)를 창고 1에 두고, 창고 2에서 작은기어에 T축을 끼우는 조립을 새로 시작",
            15: "창고 2의 기어 조립(13~14번)을 가져와 창고 1의 본체에 합쳐요 — 번호표 '12 + 14', 번호가 작은 창고 1 에서 합친다"}
for _i, _h in _HIST_RB.items(): A.steps[_i - 1].kw["history"] = _h
for _i in (13, 14): A.steps[_i - 1].kw["hideMade"] = {str(_n): "1~12번 본체(창고 1)" for _n in range(1, 13)}   # 창고 2에서 만드는 동안 본체는 창고 1 에 둔다(15번에서 합칠 때 다시 보임)

# 번호별 사용 부품(03 부품 체크, 1차). 책 21번(리벳 2 + 2열브라켓 2)을 처음 만들 때 복잡해서 21·22번 둘로 나눴다(사용자 설명 2026-11-04).
# 5번 그림 옆 "(4)" 는 4번에서 꽂은 리벳을 다시 가리키는 표시로 보고 새 리벳으로 세지 않았다(세면 16개로 LIST 12 와 안 맞음 — 추정).
USED = {1: "35프레임 2, 3단블록 2", 2: "2단블록 2", 3: "35프레임 1", 4: "리벳 4", 5: "15프레임 2", 6: "리벳 2", 7: "35프레임 1", 8: "리벳 2",
        9: "15프레임 1", 10: "눈블록 2", 11: "25프레임 1", 12: "25프레임 1", 13: "T축 1, 작은기어 1", 14: "15프레임 1, 부시 1", 15: "없음(합치는 단계)",
        16: "15프레임 1", 17: "리벳 1", 18: "1열브라켓 1", 19: "리벳 1", 20: "1열브라켓 1", 21: "리벳 2", 22: "2열브라켓 2"}
for _i, _u in USED.items():
    _pp = A.steps[_i - 1].note.split("\n▣ 사용 부품:")
    _tail = ("\n" + _pp[1].split("\n", 1)[1]) if len(_pp) > 1 and "\n" in _pp[1] else ""
    A.steps[_i - 1].note = _pp[0] + "\n▣ 사용 부품: " + _u + _tail

A.save_links()
A.check_fixes()
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("rabbit_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("rabbit_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
