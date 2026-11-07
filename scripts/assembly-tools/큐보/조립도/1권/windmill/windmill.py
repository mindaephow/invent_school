# 큐보 1권 풍차(교재 27~31쪽 · 풍차 (1~25단계)) — 저장 데이터(public/design-assemblies.js)를 asmlib 스크립트로 옮긴 것(2026-11-03). 결합점검기가 읽을 수 있게 한다.
# 1~25번 모두 결합·이동·옆자리 변환 규칙(attach·recv·place_rest·place_hang·move_made·to_side)으로 위치를 계산한다(2026-11-06). 손 좌표는 `python handcheck.py windmill` 로 센다(0곳). 새 조립의 바닥 부품만 원점에 직접 놓는다(A4).
import os as _o, sys as _s  # asmpath bootstrap: 조립도 폴더에서 도구 폴더를 찾는다
_d = _o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d, 'asmlib.py')) and _o.path.dirname(_d) != _d: _d = _o.path.dirname(_d)
_s.path.insert(0, _d)
import numpy as np
from asmlib import *
import json as _json
_DIM = _json.load(open('dims.json', encoding='utf-8'))   # 부품 몸통 크기(mm) — 쌓기 계산에 쓴다(손 숫자 금지)
_T = lambda n: float(_DIM[n][1])   # 부품 두께(모델 y)
import partlib as _pl, hovercheck as _hc
_PLATE_HOVER = _hc.HOVER + float(_pl.get('리벳')['size'][1]) + _hc.MIN_GAP   # G12: 판은 리벳(화면 기본 띄움)보다 리벳 길이(부품 목록) + 10mm(규칙) 더 멀리 — 손으로 적은 숫자 없음

A = Asm('cubo-1-windmill', '풍차', '교재 27~31쪽 · 풍차 (1~25단계)', camera={'target': [60, 40, 60], 'radius': 430, 'theta': -0.7, 'phi': 0.95})

s1 = A.step('[교재 1] 315프레임에 DC모터를 꽂아요: 모터 옆면 돌기 2개가 판 가운데 줄의 2번째·4번째 구멍(왼쪽 끝에서 센 번호)에 들어가고, 모터 케이블 쪽이 오른쪽(판 가운데)을 봐요.')
v1_0 = s1.place('315프레임', euler_to_R([0, 0, 0]), (0, 2.5, 0))
v1_1 = s1.attach('DC모터', euler_to_R([90, 0, 90]), {'p5': (v1_0, 'h11'), 'p6': (v1_0, 'h5')}, dir=[0, 1, 0])
A.steps[0].cam = (-0.83, 0.77, False, None, None, None); A.steps[0].camSrc = 'eye'   # 1번 카메라 = 01_P 격자 axes_fit(오차 1.42px·45점, roll 3.4°)

s2 = A.step('[교재 2] 3단블록 3개를 판 오른쪽에 같은 모양(구멍이 모터 쪽, 돌기가 앞·뒤)으로 세워 꽂아요: 뒷줄 11번째 구멍에 1개(맨 끝 15번째에서 뒤로 5번째)(앞줄에서 20mm 뒤쪽), 맨 끝 15번째 열의 앞줄과 뒷줄에 2개(같은 모양으로 한 줄 건너 나란히).')
v2_0 = s2.attach('3단블록', euler_to_R([0, 0, 90]), {'p2': (v1_0, 'h31')}, dir=[0, 1, 0])
v2_1 = s2.attach('3단블록', euler_to_R([0, 0, 90]), {'p2': (v1_0, 'h45')}, dir=[0, 1, 0])
v2_2 = s2.attach('3단블록', euler_to_R([0, 0, 90]), {'p2': (v1_0, 'h43')}, dir=[0, 1, 0])
A.steps[1].cam = (-0.83, 0.77, False, None, None, None); A.steps[1].camSrc = 'eye'   # 2번 카메라 = 1번과 같은 시점(책 2번 그림이 1번과 같은 쪽에서 봄) ⚠ 2번 격자 미확정

s3 = A.step('[교재 3] 다른 315프레임을 위에서 덮어요: 모터 윗돌기 2개와 블록 윗돌기 3개가 구멍에 들어가요.')
v3_0 = s3.recv('315프레임', euler_to_R([180, 0, 0]), {'h5': (v1_1, 'p4'), 'h11': (v1_1, 'p3'), 'h33': (v2_0, 'p1'), 'h43': (v2_1, 'p1'), 'h45': (v2_2, 'p1')}, dir=[0, 1, 0])

s4 = A.step('[교재 4] 315프레임을 옆면(앞쪽)에 대요: 모터 옆돌기 2개(가운데 줄의 1번째·5번째 열)와 맨 끝 블록 돌기 3개(15번째 열의 위·가운데·아래 구멍)에 끼워요.')
v4_0 = s4.recv('315프레임', euler_to_R([-90, 0, 0]), {'h2': (v1_1, 'p2'), 'h14': (v1_1, 'p1'), 'h43': (v2_1, 'p5'), 'h44': (v2_1, 'p4'), 'h45': (v2_1, 'p3')}, dir=[0, 0, 1])

s5 = A.step('[교재 5] 37프레임(3줄×7칸)의 맨 끝 칸 앞줄·뒷줄에 3단블록 2개를 세워 꽂고(돌기가 판 안쪽을 봄), 반대쪽 끝 2칸에는 2단블록 2개를 눕혀서 앞줄·뒷줄에 나란히 꽂아요(가운데 줄은 비움).')
A.steps[4].kw["hideMade"] = {str(_i): "1~4번 조립(몸체, 창고 1)" for _i in range(1, 5)}   # 새 조립을 원점에서 만드는 동안 앞 몸체는 숨긴다(A3)
v5_0 = s5.place('37프레임', euler_to_R([0, 0, 0]), (0, 2.5, 0))   # 새 조립(5~7번)의 바닥 부품 = 원점(A4)
# (v5_0 noGuide 제거 — 점검기가 창고(slot)를 구분하므로 새 창고 첫 부품에 noGuide 가 필요 없다, G1b)
v5_1 = s5.attach('3단블록', euler_to_R([90, 0, 90]), {'p2': (v5_0, 'h3')}, dir=[0, 1, 0])
v5_2 = s5.attach('3단블록', euler_to_R([90, 0, 90]), {'p2': (v5_0, 'h1')}, dir=[0, 1, 0])
v5_3 = s5.attach('2단블록', euler_to_R([-90, 0, 0]), {'p5': (v5_0, 'h21'), 'p6': (v5_0, 'h18')}, dir=[0, 1, 0])
v5_4 = s5.attach('2단블록', euler_to_R([-90, 0, 0]), {'p5': (v5_0, 'h19'), 'p6': (v5_0, 'h16')}, dir=[0, 1, 0])

s6 = A.step('[교재 6] 다른 37프레임에도 2단블록 2개를 같은 방법으로 눕혀서 맨 끝 2칸 앞줄·뒷줄에 꽂아요.')
A.steps[5].kw["hideMade"] = {str(_i): "1~5번 조립(몸체, 창고 1·2)" for _i in range(1, 6)}   # 6번 책 그림은 새 37프레임만 보인다 — 앞 번호(5번 조립 포함)는 숨긴다(A3, 2026-11-07 풍차 6번 비교에서 발견)
v6_0 = s6.recv('37프레임', euler_to_R([180, 0, 0]), {'h1': (v5_1, 'p1'), 'h3': (v5_2, 'p1')}, settleDir=[0, 1, 0])
v6_1 = s6.attach('2단블록', euler_to_R([90, 0, 0]), {'p5': (v6_0, 'h19'), 'p6': (v6_0, 'h16')}, dir=[0, -1, 0])   # 6번 묶음은 뒤집힌 좌표(판이 블록 위)로 만들고 옆자리로 뒤집어 보낸다 — 블록이 옆자리(책 6번: 판 아래, 블록 위)에서 판 위로 뜨려면 여기서는 −y
v6_2 = s6.attach('2단블록', euler_to_R([90, 0, 0]), {'p5': (v6_0, 'h21'), 'p6': (v6_0, 'h18')}, dir=[0, -1, 0])
_Cs6 = side_row([[v6_0, v6_1, v6_2]], [q for q in A.parts if q.step.index == 5], euler_to_R([-180.0, 0.0, 0.0]), (0, 0, 1), (1, 0, 0), refs=[v6_0], floor=True)[0]   # 옆자리 작업 위치(새 창고)는 규칙으로: 5번 상자 위로 묶음 크기 + 격자 간격
_Cf6_0 = np.array(v6_0.p, float)   # 이 묶음의 최종 자리 기준점
for _q in (v6_0,): to_side(_q, euler_to_R([-180.0, 0.0, 0.0]), _Cf6_0, _Cs6, 7, [0, 1, 0], keep_settle=True)
for _q in (v6_1, v6_2,): to_side(_q, euler_to_R([-180.0, 0.0, 0.0]), _Cf6_0, _Cs6, 7, [], keep_settle=True)
v6_0.extra.pop('dir', None)   # 6번에서 판은 제자리(바닥 부품)에 있고 블록이 내려와 꽂힌다(책 6번). 판의 dir 은 7번 합치기용 settleDir 로만 쓴다 — 6번에서 판이 뜨거나 안내점이 허공에 생기지 않게 한다

s7 = A.step('[교재 7] 6에서 만든 것을 뒤집어서, 3단블록 윗돌기 2개가 구멍에 들어가게 5 위에 얹어요.')
A.steps[6].kw["hideMade"] = {str(_i): "1~4번 조립(몸체, 창고 1)" for _i in range(1, 5)}   # 새 조립을 원점에서 만드는 동안 앞 몸체는 숨긴다(A3)
A.steps[6].kw["madeNoPart"] = True   # 7번은 6번에서 옆자리에 만든 묶음을 5번 위로 합치기만 한다(새 부품 없음, 05_조립.md 0절 madeNoPart)

s8 = A.step('[교재 8] 만든 상자(07)를 몸체(04) 오른쪽 끝에 맞춰요: 끝 블록의 돌기 6개가 몸체 끝 블록 구멍 6개에 들어가요.')
_gm8 = A.group('8번에서 옮기는 묶음', [v5_0, v5_1, v5_2, v5_3, v5_4, v6_0, v6_1, v6_2])
s8.move_made(_gm8, np.eye(3), pivot=np.zeros(3), shift=tuple(merge_shift(v5_1, 'p6', v2_1, 'h2')), dir=[1, 0, 0], hover=50, group='8번 묶음', marks='auto')

s9 = A.step('[교재 9] 앞쪽(열린 쪽)에 37프레임을 덮어요: 리벳 4개를 끝 블록 구멍(3단블록의 맨 위·맨 아래 구멍, 2단블록 끝의 위·아래 구멍)에 먼저 끼우고, 37프레임의 네 모서리 구멍(맨 끝 두 열의 위줄·아래줄)을 맞춰 눌러요.')
v9_1 = s9.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v5_1, 'h1')}, rivet=True)
v9_2 = s9.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v5_1, 'h3')}, rivet=True)
v9_3 = s9.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v5_3, 'h2')}, rivet=True)
v9_4 = s9.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v6_1, 'h2')}, rivet=True)
v9_0 = s9.recv('37프레임', euler_to_R([-90, 0, 0]), {'h1': (v9_1, 'p2'), 'h3': (v9_2, 'p2'), 'h19': (v9_3, 'p2'), 'h21': (v9_4, 'p2')}, dir=[0, 0, 1], hover=_PLATE_HOVER)
v9_0.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다

s10 = A.step('[교재 10] 뒤집어서 뒤쪽(반대쪽 열린 쪽)을 막아요: 같은 방법으로 리벳 4개와 37프레임을 끼우고, 빨간 15프레임 3개를 맨 끝 블록 돌기(위·가운데·아래)와 11번째 열 블록 돌기(위·가운데·아래)에 가로로 걸어요.')
v10_1 = s10.recv('15프레임', euler_to_R([-90, 0, 0]), {'h1': (v2_0, 'p8'), 'h5': (v2_2, 'p8')}, dir=[0, 0, -1])
v10_2 = s10.recv('15프레임', euler_to_R([-90, 0, 0]), {'h1': (v2_0, 'p6'), 'h5': (v2_2, 'p6')}, dir=[0, 0, -1])
v10_3 = s10.recv('15프레임', euler_to_R([-90, 0, 0]), {'h1': (v2_0, 'p7'), 'h5': (v2_2, 'p7')}, dir=[0, 0, -1])
v10_4 = s10.attach('리벳', euler_to_R([90, 0, 0]), {'p2': (v5_2, 'h1')}, rivet=True)
v10_5 = s10.attach('리벳', euler_to_R([90, 0, 0]), {'p2': (v5_2, 'h3')}, rivet=True)
v10_6 = s10.attach('리벳', euler_to_R([90, 0, 0]), {'p2': (v5_4, 'h2')}, rivet=True)
v10_7 = s10.attach('리벳', euler_to_R([90, 0, 0]), {'p2': (v6_2, 'h2')}, rivet=True)
v10_0 = s10.recv('37프레임', euler_to_R([-90, 0, 0]), {'h1': (v10_4, 'p1'), 'h3': (v10_5, 'p1'), 'h19': (v10_6, 'p1'), 'h21': (v10_7, 'p1')}, dir=[0, 0, -1], hover=_PLATE_HOVER)
v10_0.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다

s11 = A.step('[교재 11] 59프레임 2개를 눕혀 놓고 각각 리벳을 4개씩 꽂아요(5칸 폭의 첫 열·끝 열, 긴 방향 4번째·6번째 구멍). 그 위에 315프레임을 얹어 리벳 8개에 끼워요(315프레임의 1·5번째 열, 11·15번째 열의 위줄·아래줄).')
A.steps[10].kw["hideMade"] = {str(_i): "1~10번 조립(몸체, 창고 1)" for _i in range(1, 11)}   # 새 조립(받침)을 원점에서 만드는 동안 앞 몸체는 숨긴다(A3)
v11_10 = s11.place('315프레임', euler_to_R([-90, -90, 0]), (0, _DIM['59프레임'][0] / 2, 0))   # 새 조립(받침)의 바닥 부품 = 원점(x·z), 높이는 서 있는 59프레임(긴 쪽 90)이 바닥에 서도록 판 크기에서 계산(G15)
v11_2 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h1')}, rivet=True)
v11_3 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h3')}, rivet=True)
v11_4 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h13')}, rivet=True)
v11_5 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h15')}, rivet=True)
v11_6 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h31')}, rivet=True)
v11_7 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h33')}, rivet=True)
v11_8 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h43')}, rivet=True)
v11_9 = s11.attach('리벳', euler_to_R([0, 0, 90]), {'p2': (v11_10, 'h45')}, rivet=True)
v11_0 = s11.recv('59프레임', euler_to_R([0, 0, 90]), {'h16': (v11_2, 'p1'), 'h26': (v11_3, 'p1'), 'h20': (v11_4, 'p1'), 'h30': (v11_5, 'p1')}, hover=_PLATE_HOVER)
v11_0.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12)
v11_1 = s11.recv('59프레임', euler_to_R([0, 0, 90]), {'h16': (v11_6, 'p1'), 'h26': (v11_7, 'p1'), 'h20': (v11_8, 'p1'), 'h30': (v11_9, 'p1')}, hover=_PLATE_HOVER)
v11_1.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12)


# 받침(11번)은 책처럼 눕혀서 만든다 — 옆자리 자세는 최종 자리에서 규칙으로 계산(옆자리 작업 위치도 규칙)
_g11 = [v11_0, v11_1, v11_2, v11_3, v11_4, v11_5, v11_6, v11_7, v11_8, v11_9, v11_10]
for _q in (v11_0, v11_1): _q.extra['dir'] = list(v11_2.extra['dir'])   # 판의 띄움 방향 = 같은 번호 리벳의 방향 — side_row 가 판 띄움까지 바닥 위로 올린다(바닥 보정 숫자 없음)
_Cs11 = side_row([_g11], [q for q in A.parts if q.step.index <= 10], euler_to_R([180, 0, -90]), (0, 0, 1), (1, 0, 0), refs=[v11_10], floor=True)[0]
_Cf11 = np.array(v11_10.p, float)   # 이 묶음의 최종 자리 기준점
for _q in _g11: to_side(_q, euler_to_R([180, 0, -90]), _Cf11, _Cs11, 12, [1, 0, 0], keep_settle=True)
s12 = A.step('[교재 12] 10에서 만든 몸체를 세워서, 만든 받침(315프레임+59프레임 2개) 위에 올려요: 2단블록 끝 돌기 4개가 315프레임 가운데(7번째·9번째 열)의 위줄·아래줄 구멍 4개에 들어가요.')
_gm12 = A.group('12번에서 옮기는 묶음', [v11_0, v11_1, v11_2, v11_3, v11_4, v11_5, v11_6, v11_7, v11_8, v11_9, v11_10])
s12.move_made(_gm12, np.eye(3), pivot=np.zeros(3), shift=tuple(recv_shift(v11_10, 'h25', v5_3, 'p1')), dir=[1, 0, 0], hover=50, group='12번 묶음', marks='auto')   # 몸체 2단블록 돌기가 받침 315프레임 구멍에 들어가도록(규칙)

s13 = A.step('[교재 13] 큰기어(허브 아래)의 팔 구멍 2곳에 리벳 2개를 꽂고, 빨간 15프레임을 그 위에 얹어 리벳이 프레임의 2번째·4번째 구멍에 들어가게 해요(기어 가운데 십자 구멍과 프레임 가운데 구멍이 겹쳐요).')
A.steps[12].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}
v13_0 = s13.place('큰기어', euler_to_R([90, 0, 0]), (0, 20, 0))   # 새 조립(13~22번 허브)의 바닥 부품 = 원점(A4)
v13_1 = s13.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v13_0, 'h2')}, rivet=True)
v13_2 = s13.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v13_0, 'h4')}, rivet=True)
v13_3 = s13.recv('15프레임', euler_to_R([90, 0, -90]), {'h2': (v13_1, 'p2'), 'h4': (v13_2, 'p2')}, dir=[0, 0, 1], hover=_PLATE_HOVER)
v13_3.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다

s14 = A.step('[교재 14] 큰기어의 나머지 두 팔 구멍(좌·우)에 리벳 2개를 꽂고, 25프레임 2개를 빨간 프레임 양옆에 얹어요(리벳은 25프레임 안쪽 줄 가운데 구멍).')
A.steps[13].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}
v14_0 = s14.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v13_0, 'h1')}, rivet=True)
v14_1 = s14.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v13_0, 'h5')}, rivet=True)
v14_2 = s14.recv('25프레임', euler_to_R([90, 0, -90]), {'h5': (v14_0, 'p2')}, dir=[0, 0, 1], hover=_PLATE_HOVER)
v14_2.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다
v14_3 = s14.recv('25프레임', euler_to_R([90, 0, -90]), {'h6': (v14_1, 'p2')}, dir=[0, 0, 1], hover=_PLATE_HOVER)
v14_3.extra['joinOrder'] = 2   # 리벳이 먼저, 판이 나중(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다

s15 = A.step('[교재 15] 25프레임 위에 리벳 8개를 꽂아요(양쪽 프레임 모두 앞·뒤 줄에서 번갈아 지그재그: 안쪽 줄 맨 끝 구멍, 바깥 줄 두 번째·네 번째 구멍). 이 돌기에 날개 4개가 끼워져요.')
A.steps[14].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}
v15_0 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_2, 'h1')}, rivet=True)
v15_1 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_2, 'h4')}, rivet=True)
v15_2 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_2, 'h8')}, rivet=True)
v15_3 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_2, 'h9')}, rivet=True)
v15_4 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_3, 'h2')}, rivet=True)
v15_5 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_3, 'h3')}, rivet=True)
v15_6 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_3, 'h7')}, rivet=True)
v15_7 = s15.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v14_3, 'h10')}, rivet=True)

s16 = A.step('[교재 16] 날개 모듈 만들기: 39프레임에 리벳 4개를 꽂고(첫 줄 3번째·9번째 구멍, 3번째 줄 5번째 구멍, 2번째 줄 9번째 구멍), 그 위에 빨간 17프레임(첫 줄 3~9번째)과 회색 35프레임(2~4번째 줄 5~9번째 칸)을 얹어요.')
A.steps[15].kw["hideMade"] = {str(_i): "1~15번 조립(몸체·받침·허브)" for _i in range(1, 16)}   # 책 16번은 새 날개 모듈만 그린다 — 앞 번호(허브까지)는 숨긴다(A3a, 2026-11-07 사용자 지적: 창고정리 누락)
v16_0 = s16.recv('39프레임', euler_to_R([90, 0, 0]), {'h1': (v15_5, 'p2'), 'h3': (v15_6, 'p2')}, settleDir=[0, 0, 1])
v16_3 = s16.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v16_0, 'h7')}, settleDir=[0, 0, 1], rivet=True)
v16_4 = s16.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v16_0, 'h25')}, settleDir=[0, 0, 1], rivet=True)
v16_5 = s16.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v16_0, 'h15')}, settleDir=[0, 0, 1], rivet=True)
v16_6 = s16.attach('리벳', euler_to_R([90, 0, 0]), {'p1': (v16_0, 'h26')}, settleDir=[0, 0, 1], rivet=True)
v16_1 = s16.recv('17프레임', euler_to_R([90, 0, 0]), {'h1': (v16_3, 'p2'), 'h7': (v16_4, 'p2')}, settleDir=[0, 0, 1])
v16_2 = s16.recv('35프레임', euler_to_R([90, 0, 0]), {'h2': (v16_5, 'p2'), 'h13': (v16_6, 'p2')}, settleDir=[0, 0, 1])

s17 = A.step('[교재 17] 16번과 똑같은 날개 모듈을 3개 더 만들어요(모두 4개).')
A.steps[16].kw["hideMade"] = {str(_i): "1~15번 조립(몸체·받침·허브)" for _i in range(1, 16)}   # 책 17번은 날개 모듈 4개만 그린다 — 허브는 숨긴다(A3a)
v17_0 = s17.recv('39프레임', euler_to_R([90, 0, -90]), {'h1': (v15_7, 'p2'), 'h3': (v15_3, 'p2')}, settleDir=[0, 0, 1])
v17_3 = s17.attach('리벳', euler_to_R([90, 0, -90]), {'p1': (v17_0, 'h7')}, settleDir=[0, 0, 1], rivet=True)
v17_4 = s17.attach('리벳', euler_to_R([90, 0, -90]), {'p1': (v17_0, 'h25')}, settleDir=[0, 0, 1], rivet=True)
v17_5 = s17.attach('리벳', euler_to_R([90, 0, -90]), {'p1': (v17_0, 'h15')}, settleDir=[0, 0, 1], rivet=True)
v17_6 = s17.attach('리벳', euler_to_R([90, 0, -90]), {'p1': (v17_0, 'h26')}, settleDir=[0, 0, 1], rivet=True)
v17_7 = s17.recv('39프레임', euler_to_R([90, 0, 180]), {'h1': (v15_2, 'p2'), 'h3': (v15_1, 'p2')}, settleDir=[0, 0, 1])
v17_10 = s17.attach('리벳', euler_to_R([90, 0, 180]), {'p1': (v17_7, 'h7')}, settleDir=[0, 0, 1], rivet=True)
v17_11 = s17.attach('리벳', euler_to_R([90, 0, 180]), {'p1': (v17_7, 'h25')}, settleDir=[0, 0, 1], rivet=True)
v17_12 = s17.attach('리벳', euler_to_R([90, 0, 180]), {'p1': (v17_7, 'h15')}, settleDir=[0, 0, 1], rivet=True)
v17_13 = s17.attach('리벳', euler_to_R([90, 0, 180]), {'p1': (v17_7, 'h26')}, settleDir=[0, 0, 1], rivet=True)
v17_14 = s17.recv('39프레임', euler_to_R([90, 0, 90]), {'h1': (v15_0, 'p2'), 'h3': (v15_4, 'p2')}, settleDir=[0, 0, 1])
v17_17 = s17.attach('리벳', euler_to_R([90, 0, 90]), {'p1': (v17_14, 'h7')}, settleDir=[0, 0, 1], rivet=True)
v17_18 = s17.attach('리벳', euler_to_R([90, 0, 90]), {'p1': (v17_14, 'h25')}, settleDir=[0, 0, 1], rivet=True)
v17_19 = s17.attach('리벳', euler_to_R([90, 0, 90]), {'p1': (v17_14, 'h15')}, settleDir=[0, 0, 1], rivet=True)
v17_20 = s17.attach('리벳', euler_to_R([90, 0, 90]), {'p1': (v17_14, 'h26')}, settleDir=[0, 0, 1], rivet=True)
v17_1 = s17.recv('17프레임', euler_to_R([90, 0, -90]), {'h1': (v17_3, 'p2'), 'h7': (v17_4, 'p2')}, settleDir=[0, 0, 1])
v17_2 = s17.recv('35프레임', euler_to_R([90, 0, -90]), {'h2': (v17_5, 'p2'), 'h13': (v17_6, 'p2')}, settleDir=[0, 0, 1])
v17_8 = s17.recv('17프레임', euler_to_R([90, 0, 180]), {'h1': (v17_10, 'p2'), 'h7': (v17_11, 'p2')}, settleDir=[0, 0, 1])
v17_9 = s17.recv('35프레임', euler_to_R([90, 0, 180]), {'h2': (v17_12, 'p2'), 'h13': (v17_13, 'p2')}, settleDir=[0, 0, 1])
v17_15 = s17.recv('17프레임', euler_to_R([90, 0, 90]), {'h1': (v17_17, 'p2'), 'h7': (v17_18, 'p2')}, settleDir=[0, 0, 1])
v17_16 = s17.recv('35프레임', euler_to_R([90, 0, 90]), {'h2': (v17_19, 'p2'), 'h13': (v17_20, 'p2')}, settleDir=[0, 0, 1])
for _q in (v16_1, v16_2, v17_1, v17_2, v17_8, v17_9, v17_15, v17_16): _q.extra['hover'] = _PLATE_HOVER; _q.extra['joinOrder'] = 2   # 리벳이 먼저(hover 20), 판이 나중(hover 45)(G12): 판의 화살표가 떠 있는 리벳 끝에서 시작한다
_wings = [[v16_0, v16_3, v16_4, v16_5, v16_6, v16_1, v16_2], [v17_0, v17_3, v17_4, v17_5, v17_6, v17_1, v17_2], [v17_7, v17_10, v17_11, v17_12, v17_13, v17_8, v17_9], [v17_14, v17_17, v17_18, v17_19, v17_20, v17_15, v17_16]]   # 날개 4개(16번 1개 + 17번 3개)
_XFM = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]], float)   # 12번부터 화면 전체를 돌리는 xform 의 m(맨 아래 A.meta["xform"] 과 같은 값) — 12번 이후 번호는 옆자리 자세도 이 변환을 거쳐 그려진다
import math as _m2
_anc_wing = [q for q in A.parts if 13 <= q.step.index <= 15]
_Rs_wing = []   # 날개마다 옆자리 회전: 최종 자리(십자 네 팔)는 90°씩 다르지만 책 17번은 네 개를 같은 방향으로 놓는다 → 날개 판의 긴 축을 모두 같은 방향(모델 y)으로 돌린다(허브 축 z 둘레)
for _g in _wings:
    _a = np.array(_g[0].R, float)[:, 0]; _th = math.pi / 2 - math.atan2(_a[1], _a[0])
    _Rs_wing.append(np.array([[math.cos(_th), -math.sin(_th), 0.0], [math.sin(_th), math.cos(_th), 0.0], [0.0, 0.0, 1.0]]))
_Cs_wing = [side_row([_g], _anc_wing, _Rs_wing[_j], (0, 0, 1), (1, 0, 0), floor=True)[0] for _j, _g in enumerate(_wings)]   # 허브 위로 묶음 크기 + 격자 간격
for _j, (_dx, _dy) in enumerate(((-30.0, -60.0), (-30.0, 60.0), (30.0, -60.0), (30.0, 60.0))): _Cs_wing[_j] = np.array(_Cs_wing[_j], float) + np.array([_dx, _dy, 0.0])   # 책 17번: 날개 4개를 2×2 로(모델 x 두 줄 × 모델 y 두 칸 = 화면 가로 두 개·세로 두 줄)
_Cf_wing = [np.array(_g[0].p, float) for _g in _wings]   # 각 묶음의 최종 자리 기준점
for _j, _g in enumerate(_wings):
    for _q in _g: to_side(_q, _Rs_wing[_j], _Cf_wing[_j], _Cs_wing[_j], 18 if _j < 2 else 19, [0, 0, 1], keep_settle=True)

for _q in (v16_0, v17_0, v17_7, v17_14): _q.extra.pop('dir', None)   # G1a: 날개 판은 18·19번에 허브로 합쳐질 때만 안내(settleMarks) — 16·17번에서는 dir 때문에 부품 중심에 가짜 안내점이 생기지 않게 한다
for _j, _ps in enumerate(((v16_1, v16_2), (v17_1, v17_2), (v17_8, v17_9), (v17_15, v17_16))):   # G1a: 같은 모듈 리벳을 받는 17·35프레임의 안내점은 옆자리(자기 번호) 좌표의 리벳 돌기 끝이다 — recv 가 합치기용 settleMarks 로 옮겨 놓은 값을 옆자리 좌표로 되돌린다
    for _q in _ps: _q.extra['marks'] = [rnd(_Rs_wing[_j] @ (np.array(_m, float) - _Cf_wing[_j]) + _Cs_wing[_j]) for _m in _q.extra.pop('settleMarks', [])]

s18 = A.step('[교재 18] 날개 2개(마주 보는 한 쌍)를 허브 위 리벳 돌기에 끼워요: 날개 39프레임의 첫 칸 양쪽 구멍 2개가 허브 리벳 2개에 들어가요.')
A.steps[17].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}

s19 = A.step('[교재 19] 나머지 날개 2개도 같은 방법으로 끼워서 풍차 날개(십자 모양)를 완성해요.')
A.steps[18].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}

s20 = A.step('[교재 20] 축에 큰기어를 끼우고, 작은기어와 빨간 부시를 같은 쪽 끝에 차례로 끼워요(따로 조립).')
A.steps[19].kw["hideMade"] = {str(_i): "1~19번 조립(몸체·받침·허브·날개)" for _i in range(1, 20)}   # 책 20번은 축·기어·부시만 그린다 — 앞 번호(허브·날개 포함)는 숨긴다(A3a)
v20_0 = s20.place('축', euler_to_R([90, 0, 0]), (float(v13_0.p[0]), float(v13_0.p[1]), float(v13_0.p[2]) + _T('큰기어') / 2), settleDir=[0, 0, 1])   # 축 가운데 = 허브 큰기어 윗면(따로 조립하는 새 조립의 바닥 부품)
v20_0.extra['pegDepth'] = float(_pl.get('축')['pegs'][0]['len']) / 2   # 긴 축의 안내점은 축 가운데라서 꼬리가 앞서 들어가는 끝에 오도록 pegDepth = 부품 목록 돌기 길이/2 (G21)
_face20 = max(float(q.p[2]) + _T('리벳') / 2 for q in (v15_0, v15_1, v15_2, v15_3, v15_4, v15_5, v15_6, v15_7))   # 15번 리벳 머리 윗면 = 큰기어(20)가 닿는 면
v20_1 = s20.place_hang('큰기어', euler_to_R([90, 0, 0]), 'h3', v20_0, 'p1', _face20, (0, 0, 1), settleDir=[0, 0, 1], recv=True)   # 리벳 머리 면에 닿게, 안내점은 축 돌기에서(G21)
v20_2 = s20.place_rest('작은기어', euler_to_R([90, 0, 0]), 'h1', v20_1, 'h3', (0, 0, 1), settleDir=[0, 0, 1], dir=[0, 0, 1], hover=30, recv=True, via=(v20_0, 'p1'))   # 큰기어 윗면에 닿게
v20_3 = s20.place_rest('부시', euler_to_R([-90, 0, 0]), 'h1', v20_2, 'h1', (0, 0, 1), settleDir=[0, 0, 1], dir=[0, 0, 1], hover=55, recv=True, via=(v20_0, 'p1'))   # 작은기어 윗면에 닿게
_Cs20 = side_row([[v20_0, v20_1, v20_2, v20_3]], [q for q in A.parts if 13 <= q.step.index <= 19], euler_to_R([0, 0, 0]), (0, 1, 0), (1, 0, 0), refs=[v20_0])[0]   # 옆자리 작업 위치(새 창고)는 규칙으로: 허브 옆으로 묶음 크기 + 격자 간격
_Cf20 = np.array(v20_0.p, float)   # 이 묶음의 최종 자리 기준점
for _q in (v20_0, v20_1, v20_2, v20_3,): to_side(_q, euler_to_R([0, 0, 0]), _Cf20, _Cs20, 21, [0, 0, 1], hosts=((v13_0, v13_3) if _q is v20_0 else ()), keep_settle=True)
for _q in (v20_2, v20_3):   # 기어·부시의 구멍 점은 십자 구멍 한가운데(몸통 두께 가운데)에 — 받는 쪽 끝 = 구멍 윗면(제자리 + dir×두께/2) + 띄움, 원은 윗면에서 두께/2 안쪽(G23)
    _u = np.array(_q.extra['dir'], float); _u /= np.linalg.norm(_u); _q.extra['faceMarks'] = [rnd(np.array(_q.extra['side']['p'], float) + _u * float(_q.extra['thick']) / 2)]

s21 = A.step('[교재 21] 19(날개 허브)와 20(축·기어)을 합쳐요: 축의 긴 쪽 끝이 허브 가운데 구멍(빨간 15프레임 가운데·큰기어 십자 구멍)을 지나가요.')
A.steps[20].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}

s22 = A.step('[교재 22] 반대로 뒤집어서, 축 끝에 빨간 부시를 끼워 고정해요.')
A.steps[21].kw["hideMade"] = {str(_i): "1~12번 조립(몸체·받침, 창고 1)" for _i in range(1, 13)}
v22_0 = s22.place_rest('부시', euler_to_R([90, 0, 0]), 'h1', v13_0, 'h3', (0, 0, -1), dir=[0, 0, -1], hover=_hc.HOVER, recv=True, via=(v20_0, 'p1'))   # 허브 큰기어 아랫면에 닿게, 안내점은 끼우는 쪽(아래) 축 끝(G21). hover 42.75 = 축 끝에서 22 + 끝에서 제자리까지 20.75 — 부시가 축 끝에서 22 떨어진 자리에 떠서 화살표 끝 점이 부시 구멍에 붙는다(점이 부품에서 떨어지지 않게)
_u22 = np.array(v22_0.extra['dir'], float); _u22 /= np.linalg.norm(_u22)
v22_0.extra['hover'] = _hc.HOVER + abs(float((np.array(v22_0.extra['marks'][0], float) - np.array(v22_0.p, float)) @ _u22))   # 축 끝에서 기본 띄움만큼 떨어진 자리에 부시가 뜨도록: 기본 띄움 + 끝에서 제자리까지 거리(계산)
v22_0.extra['faceMarks'] = [rnd(v22_0.p)]   # 부시 구멍 자리(제자리) — 화살표 끝 점·원이 뜬 부시 구멍(제자리+hover)에 붙고, 꼬리 점은 marks(축 끝)에 둔다(연결점이 부품에서 떨어지지 않게)

s23 = A.step('[교재 23] 12(몸체)와 22(풍차 날개)를 합쳐요: 허브를 몸체 쪽으로 밀어서 축 끝이 앞 프레임의 모터 쪽 구멍에 끼워지게 해요.')
_gm23 = A.group('23번에서 옮기는 묶음', [v13_0, v13_1, v13_2, v13_3, v14_0, v14_1, v14_2, v14_3, v15_0, v15_1, v15_2, v15_3, v15_4, v15_5, v15_6, v15_7, v16_0, v16_1, v16_2, v16_3, v16_4, v16_5, v16_6, v17_0, v17_1, v17_2, v17_3, v17_4, v17_5, v17_6, v17_7, v17_8, v17_9, v17_10, v17_11, v17_12, v17_13, v17_14, v17_15, v17_16, v17_17, v17_18, v17_19, v17_20, v20_0, v20_1, v20_2, v20_3, v22_0])
s23.move_made(_gm23, np.eye(3), pivot=np.zeros(3), shift=tuple(s23.rest_shift(v22_0, 'h1', v4_0, 'h5', (0, 0, 1))), dir=[0, 0, 1], hover=30, group='23번 묶음', marks='auto')
_h23 = v4_0.hole('h5'); s23.kw['moveMade']['%d:%d' % (v20_0.step.index, v20_0.step.parts.index(v20_0))]['marks'] = [rnd(np.array(_h23['pos'], float) - np.array([0.0, 0.0, 1.0]) * _h23['len'] / 2)]   # 긴 축은 돌기 가운데가 구멍에서 멀어(join_marks 의 3.5mm 한계) 'auto' 가 못 낸다 — 축이 들어가는 구멍 입구(앞 프레임 h5, 돌기 방향 반대쪽 면)를 결합에서 계산

s24 = A.step('[교재 24] 메인보드를 받침(59프레임) 위에 꽂아요: 메인보드 아래 돌기 2개가 받침 판의 구멍 2곳(길이 5번째 줄의 1번째·3번째 구멍, 판 바깥쪽)에 들어가요.')
v24_0 = s24.attach('메인보드', euler_to_R([180.0, 0.0, -90.0]), {'p1': (v11_0, 'h23'), 'p2': (v11_0, 'h21')}, dir=[-1, 0, 0])   # 책 24·25번: 버튼 줄(+z)이 기둥에서 먼 쪽(규칙 10) — 돌기 축 둘레 180°

s25 = A.step('[교재 25] 메인보드 오른쪽 단자에 DC모터 선을 연결하면 풍차 완성!')

import stepchecks; stepchecks.apply(A, "windmill")

# ── 작업 공간(창고) 정리(04, 1차) — 교재 27~31쪽을 1→25번 순서로 보며 정했다(2026-11-06).
#   번호표로 확인: 7번 "05 + 06" · 8번 "04 + 07" · 12번 "10 + 11" · 21번 "19 + 20" · 23번 "12 + 22". 나머지는 그림 모양으로 판단(추정).
#   1~4번 몸체(창고 1) / 5번 37프레임 상자(창고 2) / 6번 둘째 상자(창고 3) / 7번 5+6 합침(번호가 작은 창고 2) / 8번 몸체+상자(창고 1) / 9~10번 몸체 이어서(창고 1)
#   / 11번 받침(창고 2) / 12번 몸체+받침(창고 1) / 13~15번 허브(창고 2) / 16~17번 날개 모듈(창고 3) / 18~19번 허브에 날개를 합침(창고 2)
#   / 20번 축·기어(창고 3) / 21~22번 허브+축(창고 2) / 23번 몸체+허브(창고 1) / 24~25번 창고 1.
_SLOT = {**{i: 1 for i in range(1, 5)}, 5: 2, 6: 3, 7: 2, 8: 1, 9: 1, 10: 1, 11: 2, 12: 1, 13: 2, 14: 2, 15: 2, 16: 3, 17: 3, 18: 2, 19: 2, 20: 3, 21: 2, 22: 2, 23: 1, 24: 1, 25: 1}
for _i, _sl in _SLOT.items(): A.steps[_i - 1].kw["slot"] = _sl
_HIST = {5: "📦 몸체(1~4번)를 창고 1에 두고, 창고 2에서 37프레임 상자 조립을 새로 시작",
         6: "창고 2의 첫째 상자(5번)는 두고, 창고 3에서 둘째 37프레임 상자를 새로 시작",
         7: "창고 3의 둘째 상자(6번)를 가져와 창고 2의 첫째 상자(5번)에 합쳐요 — 번호표 '05 + 06', 번호가 작은 창고 2에서 합친다",
         8: "창고 2의 상자(7번)를 가져와 창고 1의 몸체(4번)에 합쳐요 — 번호표 '04 + 07', 번호가 작은 창고 1에서 합친다",
         11: "📦 몸체(1~10번)를 창고 1에 두고, 창고 2에서 흰 59프레임 받침 조립을 새로 시작",
         12: "창고 2의 받침(11번)을 가져와 창고 1의 몸체(10번)에 합쳐요 — 번호표 '10 + 11', 번호가 작은 창고 1에서 합친다",
         13: "📦 몸체(1~12번)를 창고 1에 두고, 창고 2에서 큰기어 허브 조립을 새로 시작",
         16: "창고 2의 허브(13~15번)는 두고, 창고 3에서 날개 모듈을 새로 시작(17번에서 4개 만들기)",
         18: "창고 3의 날개 모듈(16·17번)을 가져와 창고 2의 허브에 합쳐요(마주 보는 날개 한 쌍씩)",
         20: "창고 2의 허브(13~19번)는 두고, 창고 3에서 축·기어 조립을 새로 시작",
         21: "창고 3의 축·기어(20번)를 가져와 창고 2의 허브(19번)에 합쳐요 — 번호표 '19 + 20', 번호가 작은 창고 2에서 합친다",
         23: "창고 2의 풍차 날개(22번)를 가져와 창고 1의 몸체(12번)에 합쳐요 — 번호표 '12 + 22', 번호가 작은 창고 1에서 합친다"}
for _i, _h in _HIST.items(): A.steps[_i - 1].kw["history"] = _h

# 번호별 사용 부품(03 부품 체크, 1차). 교재 27쪽 LIST(17종 89개)와 합계가 같고, 번호별 개수는 교재 28~31쪽 그림에서 읽었다(2026-11-06). 18·19·21·23·25번은 새 부품 없이 합치거나 연결하는 단계.
USED = {1: "315프레임 1, DC모터 1", 2: "3단블록 3", 3: "315프레임 1", 4: "315프레임 1", 5: "37프레임 1, 3단블록 2, 2단블록 2", 6: "37프레임 1, 2단블록 2",
        7: "없음(합치는 단계)", 8: "없음(합치는 단계)", 9: "37프레임 1, 리벳 4", 10: "37프레임 1, 15프레임 3, 리벳 4", 11: "59프레임 2, 315프레임 1, 리벳 8", 12: "없음(합치는 단계)",
        13: "큰기어 1, 15프레임 1, 리벳 2", 14: "25프레임 2, 리벳 2", 15: "리벳 8", 16: "39프레임 1, 17프레임 1, 35프레임 1, 리벳 4", 17: "39프레임 3, 17프레임 3, 35프레임 3, 리벳 12",
        18: "없음(합치는 단계)", 19: "없음(합치는 단계)", 20: "축 1, 큰기어 1, 작은기어 1, 부시 1", 21: "없음(합치는 단계)", 22: "부시 1", 23: "없음(합치는 단계)", 24: "메인보드 1", 25: "없음(선 연결)"}
for _i, _u in USED.items():
    _pp = A.steps[_i - 1].note.split("\n▣ 사용 부품:")
    _tail = ("\n" + _pp[1].split("\n", 1)[1]) if len(_pp) > 1 and "\n" in _pp[1] else ""
    A.steps[_i - 1].note = _pp[0] + "\n▣ 사용 부품: " + _u + _tail


# 저장 데이터(public/design-assemblies.js)에 있던 화면 값: 12단계부터 몸체를 세워 전체를 돌려 놓는 xform 과 번호별 카메라(13~25번은 출처 guess)
A.meta["xform"] = {"at": 12, "m": [[0, -1, 0], [-1, 0, 0], [0, 0, -1]], "t": [0, 160, 0]}  # m 은 위 _XFM 과 같은 값   # 12단계부터 몸체를 세워서(위가 몸체 −x 쪽) 받침 위에 올린 모양으로 전체를 돌려 놓는다
# 13~16·18~21번 카메라: 눕힌 허브(15프레임·25프레임·39프레임 긴 축)가 책 그림에서 놓인 각도에 맞춰 방위각 theta 를 풀고(18·19·21번은 두 축으로 theta·phi), 높이각은 눕히기 회전(_FL)으로 옮긴 값 — 책과 화면 비교로 확인(허브는 180° 대칭이라 theta 와 theta+π 는 같은 그림)
_CAM = {2: (-0.35, 1.05), 3: (-0.7, 0.95), 4: (-0.45, 0.85), 5: (2.5, 0.95), 6: (2.5, 0.95), 7: (2.5, 0.95), 8: (1.94, 1.08), 9: (0.46, 0.89), 10: (2.64, 1.2), 11: (1.5, 0.95, True), 12: (0.7, 0.95), 13: (0.640, 0.472), 14: (1.488, 0.621), 15: (1.571, 0.382), 16: (3.060, 0.649), 17: (3.1416, 0.78), 18: (-1.277, 0.72), 19: (2.543, 0.94), 20: (-0.585, 0.601), 21: (2.188, 0.94), 22: (2.62, 1.00), 23: (0.80, 1.05), 24: (-2.38, 1.12), 25: (3.491, 1.187)}
for _k, _c in _CAM.items(): A.steps[_k - 1].cam = (_c[0], _c[1], len(_c) > 2 and _c[2], None, None, None)
for _k in range(13, 26): A.steps[_k - 1].camSrc = 'guess'
A.steps[23].camSrc = 'eye'   # 24번 카메라 = 받침 59프레임 구멍 24점↔모델 3D 구멍 mkfit3d(fov 31, 평균 2.27·최대 5.30px, roll -59° 모델이 책과 90° 다르게 서 있음) — 판 2개·배정 8가지 중 초록 링·큰기어 투영이 책과 맞는 것
A.steps[21].camSrc = 'eye'   # 22번 카메라 = 모델 리벳 16개↔책 리벳 16개 등록(mkfit3d, 평균 0.78·최대 1.27px, roll -48° — 허브가 모델에서 세로로 서 있어 책 그림이 기울어 보임, 규칙 C3)
A.steps[19].camSrc = 'eye'   # 20번 카메라 = 큰기어 구멍 5개(십자 10mm)↔책 구멍 mkfit3d(평균 1.57·최대 2.04px, fov 31 고정, roll 5.5°) — 기어가 90° 대칭이라 구멍 배정은 roll 최소·위에서 보는 해로 골랐다
A.steps[12].camSrc = 'eye'   # 13번 카메라 = 큰기어 구멍 5개↔책 mkfit3d(평균 2.13·최대 2.66px, fov 31 고정, roll -47° 허브가 모델에서 세로) — 구멍 배정 8가지가 같은 오차라 20번 카메라와 같은 계열을 골랐다(⚠ 화면↔책 비교로 확인)
A.steps[22].camSrc = 'eye'   # 23번: 탑 315프레임 격자(23_T, 2.08px)에서 푼 카메라
A.steps[16].camSrc = 'eye'   # 17번 카메라 = 17_G 격자(왼쪽 위 모듈 회색 35프레임 5×3) axes_fit — 오차 1.70px·15점
A.steps[14].camSrc = 'eye'   # 15번 카메라 = 15_L·15_R 유추 격자(리벳 링 앵커 4+빈 구멍 4, infer_grid 평균 1.99·1.73px) axes_fit — L theta 3.06·R 3.17 phi 1.19 일치, ⚠ 사용자 확인 권장
A.steps[13].camSrc = 'eye'   # 14번 카메라 = 14_P 격자(왼쪽 25프레임 2×5) axes_fit — 오차 0.54px·10점, roll -2.0°, 오른쪽 판 14_U 1.27px(phi 0.96 같음)
A.steps[7].camSrc = 'eye'   # 8번 카메라 = 08_P 격자(몸체 윗판 15×3) axes_fit — 오차 1.08px·45점, roll 8.5°
A.steps[8].camSrc = 'eye'   # 9번 카메라 = 09_P 격자(앞 37프레임 판) axes_fit — 오차 0.18px·21점
A.steps[24].kw["noPart"] = True   # 25번: 부품 없이 선만 연결

# ── 13~22번(허브·날개·축 기어): 책은 전부 누워 있는데 12번부터 걸린 xform 이 이 번호들도 세운다 → formula1 의 작업대 변환과 같은 방식: 지금까지 계산한 자세를 "화면(xform 뒤)에서 눕힌 모양"으로 옮기고 저장 좌표만 xform 이전으로 되돌린다.
#   눕히는 회전 = 화면 x축 +90°(허브 축 화면 z → 화면 y, 부품이 쌓이는 화면 −z → 위). 가장 낮은 점이 바닥(y=0)에 닿게 올린다. 23번 이동(moveMade)의 도착 자세는 서 있는 몸체 쪽이라 건드리지 않는다.
#   22번은 책이 "반대로 뒤집기"라 허브 전체가 뒤집혀 보인다 → 13~21번 부품은 22번에서만 뒤집힌 자세(poseAt "22"), 22번 부시는 뒤집힌 자세로 저장한다.
_XF = A.meta["xform"]; _XT = np.array(_XF["t"], float)
_FL = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # 화면 x축 +90° (z → y)
_FX = np.diag([1.0, -1.0, -1.0])                           # 22번 뒤집기: 화면 x축 180°
_pose_of = lambda q: q._base if getattr(q, "_base", None) is not None else (q.p, q.R)
_flat = [q for q in A.parts if 13 <= q.step.index <= 22]
_cen = np.mean([_XFM @ np.array(_pose_of(q)[0], float) + _XT for q in _flat], axis=0)   # 허브 쪽 기준점(화면)
_P = [lambda v: _FL @ (np.array(v, float) - _cen) + _cen, lambda v: _FX @ (_FL @ (np.array(v, float) - _cen)) + _cen]   # 점: 눕힘 / 눕힘 뒤 뒤집음
_Rt = [_FL, _FX @ _FL]
_up = [0.0, 0.0]
for _m in (0, 1):   # 눕힌 뒤 가장 낮은 화면 y 가 0 이 되도록 올린다(눕힘·뒤집음 따로)
    _lo = 1e9
    for q in _flat:
        if _m == 0 and q.step.index == 22: continue
        sz = np.array(q.conn.get("size") or partlib.get(q.n)["size"], float) / 2
        poses = [_pose_of(q)] + ([(q.extra["side"]["p"], euler_to_R(q.extra["side"]["r"]))] if q.extra.get("side") else [])
        for pp, RR in poses:
            Rd = _Rt[_m] @ _XFM @ np.array(RR, float)
            _lo = min(_lo, float(_P[_m](_XFM @ np.array(pp, float) + _XT)[1] - np.abs(Rd[1]) @ sz))
    _up[_m] = -_lo
_OFF = np.array([-40.0, 0.0, 0.0])   # 13~22번 묶음을 화면에서 옮기는 양 — 같은 창고(2)의 5번 몸체(37프레임·2단블록)와 몸통이 겹쳐 insertion_check 가 13번 2건·14번 1건 경고(A4: 숨은 몸과 겹치면 비켜 놓는다). 40mm 가 겹침이 사라지는 가장 작은 값(5·40 시험)
def _st(pp, RR, m): return _XFM.T @ (_P[m](_XFM @ np.array(pp, float) + _XT) + np.array([0.0, _up[m], 0.0]) + _OFF - _XT), _XFM.T @ (_Rt[m] @ _XFM @ np.array(RR, float))
_vec = lambda v, m: _XFM.T @ (_Rt[m] @ _XFM @ np.array(v, float))   # 방향 벡터
for q in _flat:
    ex = q.extra; m = 1 if q.step.index == 22 else 0; p0, R0 = _pose_of(q)
    npos, nR = _st(p0, R0, m)
    if m == 0 and q.step.index != 22:   # 22번에서만 뒤집힌 자세
        fp, fR = _st(p0, R0, 1); ex["poseAt"] = {**(ex.get("poseAt") or {}), "22": {"p": rnd(fp), "r": R_to_euler(fR)}}
    if getattr(q, "_base", None) is not None: q._base = (npos, nR)
    else: q.p, q.R = npos, nR
    for k in ("dir", "settleDir"):
        if ex.get(k) is not None: ex[k] = rnd(_vec(ex[k], m))
    for k in ("marks", "settleMarks", "faceMarks", "holeMarks"):
        if ex.get(k): ex[k] = [rnd(_st(mk, np.eye(3), m)[0]) for mk in ex[k]]
    _sd = ex.get("side")
    if _sd:
        sp, sR = _st(_sd["p"], euler_to_R(_sd["r"]), m)
        _sd["p"], _sd["r"] = rnd(sp), R_to_euler(sR)
v22_0.extra["noMarkCheck"] = True   # 22번 부시는 뒤집힌 자세로 저장하고 축(13~21번 부품)은 22번에서만 poseAt 로 뒤집는다 — 안내점 검사는 기본 자세 기준이라 어긋나 보인다(speedbike·battlerobot 과 같은 방식, 화면으로 확인)
A.save_links()
A.check_fixes()
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("windmill_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("windmill_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
