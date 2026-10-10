# 큐보 2권 스피드바이크(교재 13~19쪽, 1~37단계+완성) — 조립 프로그램(asmlib)으로 만든다.  (교재 PDF 쪽 번호 = 교재 쪽 번호)
# 순서대로 만든다: 1단계 → 확인 → 2단계 → 확인 …  (뒤에서부터 만들거나 중간부터 시작하지 않는다)
# 각 단계: 교재 그림을 왼쪽→오른쪽, 위→아래로 읽고(부품·초록 원·화살표), get_step_context 로 직전 상태(쓴 부품·남은 부품·빈 구멍)를 본 뒤 적는다.
# 교재 LIST(부품 목록, 25개 종류):
#   2단블록 10
#   3단블록 2
#   17프레임 4
#   19프레임 4
#   115프레임 2
#   25프레임 1
#   27프레임 6
#   215프레임 3
#   39프레임 1
#   315프레임 1
#   713프레임 2
#   리벳 32
#   부시 10
#   축 4
#   1열브라켓 2
#   2열브라켓 4
#   DC모터 2
#   메인보드 1
#   리모컨 1
#   중간바퀴 2
#   캐터필러 28
#   스프라켓 2
#   너트 8
#   8볼트 5
#   12볼트 3
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-2-speedbike", "스피드바이크", "교재 13~19쪽 · 스피드바이크 (1~37단계)", camera={"target": [60, 20, 0], "radius": 380, "theta": 0.9, "phi": 1.0},
        listNote="만드는 중 — 단계가 끝나기 전까지 LIST 개수는 안 맞는 것이 정상", guideMode="mates")   # 연결점은 부품에 붙어 있고 결합할 자리일 때만 보인다(맞물림 방식, 사용자 지시 2026-10-04)
RELOCK = "--relock" in sys.argv   # 잠금 기록을 새로 만들 때(수정 지시는 이번 빌드에서 무시한다)
if not RELOCK: A.load_fixes("speedbike_fixes.json")   # 관리자 수정 지시(앞 단계 수정 → 뒤 단계가 따라온다). 파일이 없으면 아무 일도 안 한다
A.load_links("speedbike_links.json", relock=RELOCK)   # 좌표로 쓴 결합·절대 좌표로 놓은 판을 이름으로 잠가 두는 기록
UP = (0, 1, 0)

import re

# ── 단계 번호 등록(작업 흐름 단계 1): 교재 13~19쪽 훑어 정리 — 모든 단계를 noPart 뼈대로 둔다. 쪽 작업 때 SKEL[n-1].kw.pop("noPart", None) 하고 note 를 채운다 ──
# 쪽 표: 13쪽 1~2(+완성 사진·LIST) / 14쪽 3~8 / 15쪽 9~14 / 16쪽 15~20 / 17쪽 21~26 / 18쪽 27~32 / 19쪽 33~37+완성. (12쪽 로봇 이야기·20쪽 작동 방법은 이 조립도 밖)
# 번호표(합치는 번호)·"뒤집기" 글은 없다. 글: 3번 너트·12볼트, 5·7번 부시·축, 8번 캐터필러 28개, 10번 너트·8볼트, 27번 8볼트·너트·"짧은 쪽", 28번 8볼트·너트, 31번 12볼트·너트,
#        33번 "※ 메인보드 왼쪽/오른쪽에 DC모터 연결". 리벳 개수는 그림 옆: 1(2) 2(2) 9(2) 10(2) 23(4) 24(8) 27(4) 28(2) 30(2) 31(4) = 32개(LIST 32 와 같다).
_PAGE = {**{n: 13 for n in (1, 2)}, **{n: 14 for n in range(3, 9)}, **{n: 15 for n in range(9, 15)}, **{n: 16 for n in range(15, 21)},
         **{n: 17 for n in range(21, 27)}, **{n: 18 for n in range(27, 33)}, **{n: 19 for n in range(33, 38)}}
_LBL = lambda n: str(n)   # 완성 화면은 37번 뒤에 자동으로 붙는다
SKEL = [A.step("[교재 %s] (작성 전) 교재 %d쪽 — 번호만 등록한 뼈대. 쪽 작업 때 채운다." % (_LBL(_n), _PAGE[_n]), noPart=True) for _n in range(1, 38)]
for _k in range(1, 38): A.steps[_k - 1].cam = (-0.79, 0.95, False, None, None, None); A.steps[_k - 1].camSrc = "guess"   # 카메라: 쪽 작업 전까지는 같은 값의 짐작(guess)

# ── 1 ── (교재 1: 첫 부품은 pt/place 로 직접 놓고, 나머지는 이름으로 결합한다)
# 예)  s1 = A.step("[교재 1] ...")
#      base = s1.place("315프레임", orient("315프레임", {"홀면 +y": "위"}), (75, 2.5, 0))
#      blk  = s1.attach("3단블록", orient("3단블록", {"돌기면 +z": "아래", "홀면 +y": "+Z"}), {"돌기면 +z 1": ("315프레임 1번", "홀면 +y 열14·줄1"), "돌기면 +z 3": ("315프레임 1번", "홀면 +y 열15·줄1")}, hover=45)
# 구멍·돌기는 이름(면 +축, 열·줄)으로 말한다(안내서 3-1절). 번호를 모르면 get_part_faces / get_step_context 로 본다.

# ── 1 ── 교재 13쪽 1 (읽은 것 2026-10-09, 격자 01_1·01_2 — 크롭 → 수평선 → 회전(작은 각도) → 215프레임 15칸×2줄, 점이 구멍에 앉음. 칸12 줄2·칸15 줄1 은 리벳이 가린 자리라 연장한 점이 아니라 찾은 점/연장 구분은 fits/01_A.json 의 est)
#   카메라가 보는 면(책): 215프레임(회색) = 구멍 둘레 홈이 보이는 홀면(+y)이 카메라 쪽(위), 칸1 이 화면 왼쪽(먼 쪽)·칸15 가 오른쪽(가까운 쪽), 책 줄1 = 먼 줄, 줄2 = 가까운 줄. 25프레임(검은) = 같은 홀면이 위, 215프레임과 나란히 위에 떠 있다.
#   화살표(꼬리 = 25프레임 구멍(초록 링), 화살촉 = 리벳): 링 2개 — 25프레임 맨 왼쪽 구멍(가까운 줄) → 리벳(215프레임 칸12·줄2), 25프레임 왼쪽에서 4번째 구멍(먼 줄) → 리벳(215프레임 칸15·줄1). 리벳은 215프레임 구멍에 이미 꽂혀 있다(머리가 구멍보다 35px 위에 그려짐).
#   25프레임은 215프레임 칸12~16 위에 놓여 25프레임의 끝 칸 1개(칸16 자리)가 215프레임 끝 밖으로 나온다(2번 그림에서 검은 판이 회색 판 끝 밖으로 나온 것과 같음). 두 판의 방향이 같아 줄은 같은 줄끼리(가까운 줄 = 줄2) 겹친다.
s1 = SKEL[0]; s1.kw.pop("noPart", None)
s1.note = "[교재 1] 회색 215프레임에 리벳 2개를 끼우고 그 위에 검은 25프레임을 얹어요. 리벳은 칸12 가까운 줄과 칸15 먼 줄에 들어가요."
R_FL = np.eye(3)   # 눕힌 프레임: 홀면(모델 +y) → 위(+Y), 긴 쪽(모델 x) → +X(칸1 이 왼쪽), 모델 줄1(−z) → 먼 쪽, 줄2(+z) → 가까운 쪽
P1 = s1.place("215프레임", R_FL, (75.0, 3.5, 0.0))   # 높이 3.5: 아래에서 끼우는 너트 턱(1mm)이 바닥(y 0)을 넘지 않게 프레임 바닥을 1mm 띄운다(안내서 6-1절 18번)
RV1 = [s1.attach("리벳", np.eye(3), {"p1": (P1, "홀면 +y 열%d·줄%d" % cr)}, rivet=True, hover=28) for cr in ((12, 2), (15, 1))]   # 리벳 p1(모델 −y)이 아래로 판 구멍에, p2 가 위로 나온다
for _q in RV1: _q.extra["joinOrder"] = 1
F25_1 = s1.recv("25프레임", R_FL, {"h1_2": (RV1[0], "p2"), "h4_1": (RV1[1], "p2")}, hover=45)   # 25프레임(홀면이 위, 칸1 이 왼쪽): 맨 왼쪽(칸1) 가까운 줄 구멍 → 리벳 칸12, 왼쪽에서 4번째(칸4) 먼 줄 구멍 → 리벳 칸15 (구멍은 관통이라 아래에서 올라오는 리벳 돌기를 받는다)
A.steps[0].cam = (0.3, 0.95, False, None, None, None); A.steps[0].camSrc = "guess"

# ── 2 ── 교재 13쪽 2 (읽은 것 2026-10-09, 격자 02_1·02_2 예정 — 2번 그림은 1번 결과의 오른쪽 끝을 크게 그린 것)
#   카메라가 보는 면(책): 1번과 같은 면(홀면이 위, 칸1 이 왼쪽·위, 오른쪽 아래가 가까이). 검은 25프레임이 215프레임 오른쪽 끝에 얹혀 있고 25프레임 위에 리벳 머리 4개가 보인다: 1번에서 꽂은 2개(링 없음: 가까운 줄 칸1, 먼 줄 칸4)와 이번에 꽂는 2개(초록 링: 먼 줄 칸1, 가까운 줄 칸4).
#   화살표(꼬리 = 위에서 내려오는 검은 27프레임 구멍(링 2개), 화살촉 = 새 리벳): 27프레임 맨 왼쪽(칸1) 먼 줄 구멍 → 새 리벳 A(25프레임 칸1 먼 줄), 27프레임 왼쪽에서 4번째(칸4) 가까운 줄 구멍 → 새 리벳 B(25프레임 칸4 가까운 줄). 27프레임은 7칸이라 25프레임(5칸) 오른쪽 끝 밖으로 2칸 나온다.
s2 = SKEL[1]; s2.kw.pop("noPart", None)
s2.note = "[교재 2] 25프레임에 리벳 2개를 더 끼우고 그 위에 검은 27프레임을 얹어요. 새 리벳은 25프레임 맨 왼쪽 먼 줄과 왼쪽에서 4번째 가까운 줄에 들어가요."
RV2 = [s2.attach("리벳", np.eye(3), {"p1": (F25_1, "홀면 +y 열%d·줄%d" % cr)}, rivet=True, hover=28) for cr in ((1, 1), (4, 2))]   # 새 리벳: 25프레임 칸1 먼 줄, 칸4 가까운 줄
for _q in RV2: _q.extra["joinOrder"] = 1
F27_2 = s2.recv("27프레임", R_FL, {"h1_1": (RV2[0], "p2"), "h4_2": (RV2[1], "p2")}, hover=60)   # 27프레임 칸1 먼 줄 구멍 → 리벳 A, 칸4 가까운 줄 구멍 → 리벳 B
A.steps[1].cam = (0.3, 0.95, False, None, None, None); A.steps[1].camSrc = "guess"

# ── 3 ── 교재 14쪽 3 (읽은 것 2026-10-09, 격자는 2번 격자 02_2(27프레임 7칸×2줄)와 같은 판이라 새로 만들 필요 없이 03_2 를 따로 만든다)
#   카메라가 보는 면(책): 판을 거의 정면(위에서 내려다보는 쪽)에서 본다. 앞에 검은 27프레임(홀면이 위, 칸1 왼쪽, 리벳 머리 4개가 구멍 속에 보임), 그 뒤에 회색 215프레임. 27프레임 오른쪽 2칸(칸6·7)은 아래에 판이 없어 구멍이 하얗다(2번의 "2칸 밖으로 나옴"과 같다).
#   화살표(노란 선: 꼬리 = 12볼트·너트, 화살촉 = 판 구멍): 12볼트가 앞(위)에서 27프레임 칸2 먼 줄 구멍(노란 링)으로 들어가 25프레임·215프레임을 꿰고, 너트가 반대쪽(215프레임 아래)에서 같은 축에 끼운다. 12볼트는 프레임 3장을 꿴다(부품 DB 메모). 구멍 번호: 27프레임 칸2·줄1 ↔ 25프레임 칸2·줄1 ↔ 215프레임 칸13·줄1.
s3 = SKEL[2]; s3.kw.pop("noPart", None)
s3.note = "[교재 3] 27프레임 칸2 먼 줄 구멍에 12볼트를 위에서 꽂아 3장을 꿰고, 215프레임 아래에서 너트를 끼워 조여요."
NT3 = s3.attach("너트", np.eye(3), {"p1": (P1, "홀면 -y 열13·줄1")}, hover=30)      # 너트: 215프레임 아래에서 몸통(모델 +y)이 구멍으로 올라온다
BO3 = s3.attach("12볼트", np.eye(3), {"p1": (F27_2, "홀면 +y 열2·줄1")}, hover=40)  # 12볼트: 몸통(모델 −y)이 위에서 27프레임 구멍으로 내려간다
A.steps[2].cam = (0.3, 1.25, False, None, None, None); A.steps[2].camSrc = "guess"
A.meta["lift"] = {**(A.meta.get("lift") or {}), "3": 35.0}   # 3번: 너트가 215프레임 아래에서 올라오는 모습(떠 있는 자리)이 바닥 아래로 내려가므로 화면 전체를 35mm 띄운다

# ── 4 ── 교재 14쪽 4 (읽은 것 2026-10-09, 격자 04_1·04_2 — 크롭 → 수평선 → 회전 → 27프레임 7칸×2줄, 링 2개가 칸3·칸7 의 줄2)
#   카메라가 보는 면(책): 판 = 3번과 같은 면(홀면이 위, 칸1 왼쪽), 12볼트 머리가 칸2 먼 줄에 보인다. DC모터 = 구멍 8개·빨간 십자가 있는 큰 면이 카메라 쪽(위), 옆면에 돌기 2개(피치 20, 쓰지 않는 옆돌기)가 위쪽으로 보이고 판과 닿는 윗돌기 2개(피치 40)는 판 쪽을 향해 가려져 있다. 케이블은 왼쪽으로 나온다.
#   화살표(꼬리 = 모터 윗돌기, 화살촉 = 판 구멍·초록 링): 링 2개 = 27프레임 줄2(가까운 줄)의 칸3 과 칸7(간격 4칸 = 40mm = 모터 윗돌기 피치 40). 모터는 판 위에 얹히는 쪽에서 돌기를 아래(판 쪽)로 향한다(5번 작은 그림: 모터가 프레임 위에 얹힘).
#   모터 방향(추정): 빨간 십자는 오른쪽 끝(칸7 쪽)에 가까워 돌기 p2(십자에 가까운 쪽)를 칸7 에 꽂는다 — 모터 모델 z → −X.
s4 = SKEL[3]; s4.kw.pop("noPart", None)
s4.note = "[교재 4] DC모터를 27프레임 위에 얹어요. 모터 윗돌기 2개가 가까운 줄의 칸3·칸7 구멍에 들어가요(빨간 십자가 있는 큰 면이 위, 케이블은 왼쪽)."
R_M4 = np.array([[0, 0, -1], [0, -1, 0], [-1, 0, 0]], float)   # DC모터: 윗돌기 면(모델 +y) → 아래(−Y), 모델 z(긴 쪽) → −X(p1 이 칸3 쪽, p2 가 칸7 쪽), 빨간 십자 큰 면(모델 −y)이 위
M4 = s4.attach("DC모터", R_M4, {"p1": (F27_2, "홀면 +y 열3·줄2"), "p2": (F27_2, "홀면 +y 열7·줄2")}, hover=40)
A.steps[3].cam = (0.9, 0.8, False, None, None, None); A.steps[3].camSrc = "guess"

# ── 5 ── 교재 14쪽 5 (읽은 것 2026-10-09, 격자 05_1·05_2 — 크롭 → 수평선 → 회전 → 215프레임 15칸×2줄(칸1 이 오른쪽): 보이는 칸1~11 은 구멍에서 찾은 점(22점, 오차 0.4px), 가려진 칸12~15 는 연장)
#   카메라가 보는 면(책): 조립품을 뒤집어 215프레임의 **아래쪽 면**(1~3번에서 27프레임·25프레임을 얹은 반대쪽)을 본다. 215프레임 끝(칸12~15)에 리벳 4개·너트가 구멍 안에 보이고(밑에서 본 면), 27프레임·모터는 판 반대편(위)이라 왼쪽 끝 뒤에 가려 있다. 칸1 이 오른쪽(먼 쪽)·칸15 가 왼쪽, 책 위쪽 줄 = 줄1(먼 줄), 아래쪽 줄 = 줄2(가까운 줄) — 같은 줄 번호(줄1 = 12볼트·너트가 있던 줄).
#   화살표: 축 2개(꼬리 = 축 끝, 화살촉 = 215프레임 구멍·초록 링)가 아래에서 올라와 줄2 의 칸9·칸2 구멍으로 들어가고, 부시 2개(빨간)가 반대쪽(위)에서 같은 구멍 위에 내려온다(5번 작은 그림: 프레임 위에 빨간 부시, 프레임 아래로 축이 길게 내려옴). 축 길이 65mm 중 부시 쪽 끝이 프레임 위로 부시 높이만큼 나오고 나머지가 아래로 내려온다.
#   작은 그림(옆모습): 모터가 27프레임 위, 215프레임 오른쪽 부분은 평평하고 축 2개가 아래로 늘어진다 = 모델은 서 있는 그대로(모터 위) 두고 카메라를 아래에서 올려다보게 한다.
s5 = SKEL[4]; s5.kw.pop("noPart", None)
s5.note = "[교재 5] 조립품을 뒤집어 보세요. 215프레임 줄2 의 칸9·칸2 구멍에 축을 끼우고, 반대쪽에서 빨간 부시를 끼워요."
def _xcol(c): return 5.0 + (c - 1) * 10.0   # 215프레임 칸 c 의 x (칸1 = 5, 칸15 = 145)
AX5 = [s5.place("축", np.eye(3), (_xcol(c), -18.5, 5.0), dir=[0, -1, 0], hover=45) for c in (9, 2)]   # 축: 아래에서 올라와 215프레임 구멍을 지난다(윗끝이 부시 위 높이)
BU5 = [s5.place("부시", np.eye(3), (_xcol(c), 11.25, 5.0), dir=[0, 1, 0], hover=40) for c in (9, 2)]   # 부시: 프레임 위에서 축 끝에 내려앉는다
for _q, _c in zip(AX5, (9, 2)): _q.extra["marks"] = [[_xcol(_c), 3.5, 5.0]]; _q.extra["loose"] = True   # 안내점 = 215프레임 줄2 구멍(위치 검사용)
for _q, _c in zip(BU5, (9, 2)): _q.extra["marks"] = [[_xcol(_c), 14.0, 5.0]]; _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True   # 안내점 = 축 윗끝(부시가 내려앉는 곳)
A.steps[4].cam = (2.7, 2.5, False, None, None, None); A.steps[4].camSrc = "guess"
A.meta["lift"] = {**(A.meta.get("lift") or {}), "5": 100.0, **{str(_k): 55.0 for _k in range(6, 38)}}   # 축이 215프레임 아래로 51mm 늘어지므로 5번 이후 화면 전체를 띄운다(뒤집어 아래에서 본 책 그림과 같은 모양; 이후 번호에서 축 자리가 바뀌면 다시 정한다)   # 5번: 축이 아래로 65mm 내려가고 아래에서 올라오는 모습이 바닥 아래로 가므로 화면 전체를 띄운다

# ── 6 ── 교재 14쪽 6 (읽은 것 2026-10-09, 격자 06_1·06_2 — 크롭 → 수평선 → 회전 → 215프레임 15칸×2줄 평행 격자, 아래 줄 구멍을 오른쪽부터 세어 축 링 = 칸9·칸2)
#   카메라가 보는 면(책): 5번과 같은 아래쪽 면(칸1 이 오른쪽, 위 줄 = 줄1, 아래 줄 = 줄2). 축 2개가 215프레임 줄2 의 칸9·칸2 에서 아래로 늘어져 있고(5번에서 끼움), 모터는 왼쪽 뒤.
#   화살표(꼬리 = 스프라켓 가운데 구멍(초록 링), 화살촉 = 축 끝): 스프라켓 2개가 아래에서 축 끝을 향해 올라와 축이 스프라켓 가운데 십자 구멍을 지난다(스프라켓은 215프레임 쪽으로 밀어 올린다).
s6 = SKEL[5]; s6.kw.pop("noPart", None)
s6.note = "[교재 6] 축 2개의 아래쪽 끝에 스프라켓을 하나씩 끼워요."
SP6 = [s6.place("스프라켓", np.eye(3), (_xcol(c), -14.5, 5.0), dir=[0, -1, 0], hover=45) for c in (9, 2)]   # 스프라켓: 아래에서 올라와 축을 지나 프레임 바로 아래(윗면이 프레임 아래 면에서 2mm 떨어짐)
for _q, _c in zip(SP6, (9, 2)): _q.extra["marks"] = [[_xcol(_c), -51.0, 5.0]]; _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True   # 안내점 = 축 아래쪽 끝
A.steps[5].cam = (3.6, 2.0, False, None, None, None); A.steps[5].camSrc = "guess"
A.meta["lift"]["6"] = 80.0   # 6번: 스프라켓이 아래에서 올라오는 모습(떠 있는 자리)이 바닥 아래로 내려가므로 화면 전체를 띄운다

# ── 7 ── 교재 14쪽 7 (읽은 것 2026-10-09, 격자 07_1·07_2 — 크롭 → 수평선 → 회전 → 흰 19프레임 9칸×1줄(첫·끝 구멍에서 읽은 점을 같은 간격으로 채운 연장 격자), 링 2개 = 칸2·칸9)
#   카메라가 보는 면(책): 6번과 같은 아래쪽 면. 스프라켓 2개가 축에 끼워져 215프레임 아래에 붙어 있고 축 끝이 스프라켓 밖으로 나온다. 흰 19프레임은 축 끝 앞(아래, 카메라 쪽)에 떠 있고 홀면이 카메라 쪽, 빨간 부시 2개가 그 앞에 떠 있다.
#   화살표(꼬리 = 19프레임·부시, 화살촉 = 축 끝): 19프레임 칸2 → 왼쪽 축(215프레임 칸9), 19프레임 칸9 → 오른쪽 축(칸2), 빨간 부시 2개가 19프레임 구멍을 지나 축 끝에 끼운다. 순서(축 쪽에서 바깥으로): 스프라켓, 19프레임, 부시.
#   19프레임의 방향: 칸 번호가 215프레임 칸 번호와 반대로 커진다(책 7 에서 19프레임 칸1 이 왼쪽 = 215프레임 칸10 쪽). 줄은 한 줄이라 축이 지나는 줄에 놓인다.
s7 = SKEL[6]; s7.kw.pop("noPart", None)
s7.note = "[교재 7] 흰 19프레임 칸2·칸9 구멍을 두 축 끝에 끼우고, 빨간 부시 2개를 바깥쪽 축 끝에 끼워요."
R_19 = np.diag([-1.0, 1.0, -1.0])   # 19프레임: 긴 쪽(칸 번호)이 215프레임과 반대로 커진다(칸2 → 215프레임 칸9 자리, 칸9 → 칸2 자리), 홀면 위
F19_7 = s7.place("19프레임", R_19, (55.0, -30.5, 5.0), dir=[0, -1, 0], hover=30)   # 흰 프레임: 스프라켓 톱니 바퀴 바로 아래(−28~−33)에 붙는다 — 12번에서 축 끝 약 12mm 가 부시 바깥으로 나와 둘째 215프레임 구멍으로 들어간다(책 12)
F19_7.extra["marks"] = [[85.0, -51.0, 5.0], [15.0, -51.0, 5.0]]; F19_7.extra["loose"] = True; F19_7.extra["noMarkCheck"] = True   # 안내점 = 축 끝
F19_7.extra["joinOrder"] = 1
R_BUD = np.diag([1.0, -1.0, -1.0])  # 아래 끝 부시: 열린 면이 위(축 쪽)를 향한다
BU7 = [s7.place("부시", R_BUD, (_x, -35.75, 5.0), dir=[0, -1, 0], hover=40) for _x in (85.0, 15.0)]   # 부시: 흰 프레임 바깥(−33~−38.5), 축 끝은 부시 밖으로 −51 까지 12.5mm 더 나온다
for _q, _x in zip(BU7, (85.0, 15.0)): _q.extra["marks"] = [[_x, -51.0, 5.0]]; _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True; _q.extra["joinOrder"] = 2
A.steps[6].cam = (3.6, 2.0, False, None, None, None); A.steps[6].camSrc = "guess"
A.meta["lift"]["7"] = 115.0   # 7번: 부시가 아래에서 올라오는 모습이 바닥 아래로 내려가므로 화면 전체를 띄운다

# ── 8 ── 교재 14쪽 8 (읽은 것 2026-10-09 — 캐터필러 링크 28개를 두 스프라켓 둘레에 돌려 끼운다. 격자는 8번 그림에 판 구멍이 거의 안 보여 없고, 크롭 후 원본 1장(안내서 0-2 ⓘ: 부품만 있는 단계 — 보고에 적음))
#   카메라가 보는 면(책): 7번과 같은 아래쪽 면. 28개 링크가 이어진 띠(작은 그림, 길이:폭 = 8:1)가 두 스프라켓 둘레에 한 바퀴 돌려 감겨 있다. 링크의 돌기(스터드)는 바깥, 가운데 직사각 창이 스프라켓 톱니에 맞물린다. 흰 19프레임이 띠 앞(카메라 쪽)에서 축 끝을 잡고 빨간 부시가 끝에 끼워져 있다.
#   계산(추정): 두 축 사이 70mm(칸9·칸2), 스프라켓 지름 약 50 → 띠 한 바퀴 = 곧은 구간 2×70 + 둥근 구간 2×(π×25.8) = 302mm, 링크 28개라 링크 한 개 간격 = 302 ÷ 28 ≈ 10.8mm(작은 그림의 띠 길이:폭 ≈ 8:1 → 28×10.8 = 302 = 8×38 와도 맞는다).
#   링크 방향: 폭(모델 x, 38mm)이 축 방향, 돌기(모델 +y)가 바깥, 길이(모델 z)가 띠 진행 방향. 띠는 스프라켓 톱니 바퀴의 가운데 높이에 놓는다.
s8 = SKEL[7]; s8.kw.pop("noPart", None)
s8.note = "[교재 8] 캐터필러 링크 28개를 이어 두 스프라켓 둘레에 한 바퀴 감아요. 돌기가 바깥으로 오게 해요."
_CA, _CB = np.array([85.0, 5.0]), np.array([15.0, 5.0])   # 두 축(칸9·칸2)의 x·z
_RP = 25.8                                               # 링크 가운데가 지나는 반지름(스프라켓 피치 반지름)
_LEN = 140.0 + 2.0 * np.pi * _RP                         # 한 바퀴 길이
_PIT = _LEN / 28.0                                       # 링크 간격(약 10.8mm)
_YT = -23.5                                              # 톱니 바퀴 가운데 높이(스프라켓 가운데 −14.5 + 톱니면 −9)
def _track_pose(s):   # 길이 s 지점의 (x, z, 바깥 방향 n)
    if s < 70.0: return np.array([15.0 + s, 5.0 + _RP]), np.array([0.0, 1.0])
    s -= 70.0
    if s < np.pi * _RP:
        f = s / _RP; n = np.array([np.sin(f), np.cos(f)]); return _CA + _RP * n, n
    s -= np.pi * _RP
    if s < 70.0: return np.array([85.0 - s, 5.0 - _RP]), np.array([0.0, -1.0])
    s -= 70.0
    f = np.pi + s / _RP; n = np.array([np.sin(f), np.cos(f)]); return _CB + _RP * n, n
CAT8 = []
for _i in range(28):
    _xz, _n = _track_pose(_i * _PIT)
    _R = np.array([[0.0, _n[0], _n[1]], [1.0, 0.0, 0.0], [0.0, _n[1], -_n[0]]])   # 열: 모델 x → +Y(축), 모델 y → 바깥 n, 모델 z → 진행 방향 t=(n_z, 0, −n_x)
    _q = s8.place("캐터필러", _R, (float(_xz[0]), _YT, float(_xz[1])))
    _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True
    CAT8.append(_q)
A.steps[7].cam = (3.6, 2.0, False, None, None, None); A.steps[7].camSrc = "guess"

# ── 9 ── 교재 15쪽 9 (읽은 것 2026-10-10, 격자 09_1·09_2 — 크롭 → 수평선 → 회전 → 회색 215프레임 15칸×2줄(찾은 18점 + 연장 12점), 링 2개 = 가까운 줄(줄2)의 칸6·칸13)
#   카메라가 보는 면(책): 215프레임의 앞면(홀면 위, 칸1 왼쪽, 줄2 가까운 쪽)을 거의 정면으로 본다. 흰 19프레임은 그 뒤(그림에서 위·더 작음 = 더 멀리, 215프레임의 뒷면 쪽)에 있고 리벳 2개를 쥔 채 화살표 방향(카메라 쪽)으로 215프레임 구멍을 뚫고 앞면으로 나온다 — 그래서 10번 그림에는 215프레임 앞면에 리벳 끝만 보이고 흰 프레임은 안 보인다.
#   화살표(꼬리 = 흰 19프레임 구멍 2개, 화살촉 = 리벳·215프레임 구멍): 흰 19프레임 칸1 → 215프레임 칸6, 칸8 → 칸13 (간격 7칸 = 70mm). 흰 프레임 칸 i ↔ 215프레임 칸 5+i, 같은 방향(칸 번호가 같은 쪽으로 커진다).
#   창고: 1~8번에서 만든 첫째 조립품은 창고 1 에 두고, 창고 2 에서 둘째 조립품을 새로 시작한다(12번에서 합친다 — 12번 그림에서 첫째 조립품이 둘째 위에 놓인다).
s9 = SKEL[8]; s9.kw.pop("noPart", None)
s9.note = "[교재 9] 새 215프레임(둘째 조립품)에 리벳 2개를 끼우고 그 위에 흰 19프레임을 얹어요. 리벳은 가까운 줄 칸6·칸13 에 들어가요."
ZB9 = -110.0   # 둘째 조립품은 첫째(z −26~36)와 겹치지 않게 뒤쪽 −110 에서 만든다(12번에서 합칠 때 옮김)
P9 = s9._add(Part("215프레임", R_FL, (75.0, 3.5, ZB9), s9, {}))   # place() 는 잠금 기록이 1번 215프레임 옆 상대 위치로 되돌려서 단독 부품은 _add(Part) 로 놓는다
R_FLP = np.diag([1.0, -1.0, -1.0])   # 아래에서 끼우는 부품: 뒤집어 돌기 p1 이 위(215프레임 쪽)를 향하고 홀면은 아래를 향한다
RV9 = [s9.attach("리벳", R_FLP, {"p1": (P9, "홀면 -y 열%d·줄%d" % cr)}, rivet=True, hover=28) for cr in ((6, 2), (13, 2))]   # 리벳: 흰 프레임이 쥐고 있다가 215프레임 아래(뒷면)에서 올라와 가까운 줄 칸6·칸13 구멍에 꽂힌다
for _q in RV9: _q.extra["joinOrder"] = 1
F19_9 = s9.recv("19프레임", R_FLP, {"h1_1": (RV9[0], "p2"), "h8_1": (RV9[1], "p2")}, hover=45)   # 흰 19프레임: 215프레임 뒷면(아래) 쪽, 칸1 → 리벳 칸6, 칸8 → 리벳 칸13
A.steps[8].cam = (0.9, 1.0, False, None, None, None); A.steps[8].camSrc = "guess"

# ── 10 ── 교재 15쪽 10 (읽은 것 2026-10-10, 격자 10_1·10_2 — 215프레임 앞면 15칸×2줄(모서리 4곳 연장) + 검은 27프레임 7칸×2줄(모서리 4곳 연장))
#   카메라가 보는 면(책): 9번과 같은 쪽 — 215프레임 앞면(홀면 위, 칸1 왼쪽, 줄1 먼·위 줄, 줄2 가까운·아래 줄). 9번에서 꽂은 리벳의 끝(주황)이 가까운 줄 칸6·칸13 에 보이고 흰 19프레임은 뒤쪽이라 안 보인다. 검은 27프레임은 앞(카메라 쪽·그림 아래)에 홀면이 카메라 쪽으로 떠 있다(칸1 왼쪽).
#   화살표: 215프레임 새 리벳 2개(칸1 먼 줄 = 리벳 A, 칸4 가까운 줄 = 리벳 B) ← 검은 27프레임 칸4 먼 줄, 칸7 가까운 줄 구멍(초록 링). 노란 선(8볼트): 27프레임 칸6 먼 줄 → 215프레임 칸3 먼 줄 구멍, 너트가 뒤(215프레임 뒷면)에서 받는다.
#   27프레임 칸 i ↔ 215프레임 칸 i−3(같은 방향): 27프레임은 215프레임 왼쪽 끝 밖으로 3칸 나온다.
s10 = SKEL[9]; s10.kw.pop("noPart", None)
s10.note = "[교재 10] 215프레임 칸1 먼 줄·칸4 가까운 줄에 리벳 2개를 끼우고 검은 27프레임을 얹은 뒤, 8볼트를 27프레임 칸6 먼 줄에 꽂고 뒤에서 너트로 조여요(27프레임이 왼쪽으로 3칸 나와요)."
RV10 = [s10.attach("리벳", np.eye(3), {"p1": (P9, "홀면 +y 열%d·줄%d" % cr)}, rivet=True, hover=28) for cr in ((1, 1), (4, 2))]
for _q in RV10: _q.extra["joinOrder"] = 1
F27_10 = s10.recv("27프레임", R_FL, {"h4_1": (RV10[0], "p2"), "h7_2": (RV10[1], "p2")}, hover=60)
NT10 = s10.attach("너트", np.eye(3), {"p1": (P9, "홀면 -y 열3·줄1")}, hover=30)
BO10 = s10.attach("8볼트", np.eye(3), {"p1": (F27_10, "홀면 +y 열6·줄1")}, hover=40)
A.steps[9].cam = (0.9, 1.0, False, None, None, None); A.steps[9].camSrc = "guess"

# ── 11 ── 교재 15쪽 11 (읽은 것 2026-10-10 — 격자는 10번 격자의 27프레임 7칸×2줄과 같은 판: 이 그림은 같은 자리에서 판 구멍 8개가 가려지지 않아 새 크롭은 만들지 않고 11_1·11_2 를 따로 만든다)
#   카메라가 보는 면(책): 10번과 같은 쪽. 검은 27프레임이 215프레임 왼쪽 끝 밖으로 3칸 나온 모습(리벳 A 칸4 먼 줄, 리벳 B 칸7 가까운 줄, 8볼트 칸6 먼 줄이 보임). 앞(그림 아래)에 DC모터가 큰 면(빨간 십자·구멍 8개)을 카메라 쪽으로 두고 돌기 2개가 있는 윗면이 판을 향한다.
#   화살표(초록 링 2개): 27프레임 가까운 줄(줄2)의 칸1 과 칸5(간격 4칸 = 40mm = 모터 윗돌기 피치) ← 모터 돌기 2개. 빨간 십자는 모터 큰 면 왼쪽, 케이블은 오른쪽(4번 그림과 좌우가 반대).
s11 = SKEL[10]; s11.kw.pop("noPart", None)
s11.note = "[교재 11] DC모터 윗돌기 2개를 27프레임 가까운 줄의 칸1·칸5 구멍에 끼워요(빨간 십자가 있는 큰 면이 위, 케이블은 오른쪽)."
R_M11 = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]], float)   # 4번 방향(R_M4)을 위쪽 축으로 180° 돌린 것: 십자가 왼쪽, 케이블 오른쪽. 돌기 p2 가 왼쪽(칸1), p1 이 오른쪽(칸5)
M11 = s11.attach("DC모터", R_M11, {"p2": (F27_10, "홀면 +y 열1·줄2"), "p1": (F27_10, "홀면 +y 열5·줄2")}, hover=40)
A.steps[10].cam = (0.9, 1.0, False, None, None, None); A.steps[10].camSrc = "guess"

# ── 12 ── 교재 15쪽 12 (읽은 것 2026-10-10 — 새 부품 없음: 첫째 조립품(1~8번)을 앞뒤 축(z)으로 180° 돌려 축 끝이 위를 향하게 해서 둘째 조립품(9~11번)의 뒤(아래)쪽에서 끼운다 — 9번과 같이 책은 둘째 조립품 앞면을 보고 있고 첫째 조립품은 그 뒤에 있다)
#   카메라가 보는 면(책): 10·11번과 같은 쪽(둘째 조립품 앞면). 215프레임(둘째 조립품: 왼쪽 끝에 27프레임·DC모터, 가까운 줄 칸6·칸13 리벳 끝)이 가로로 놓이고, 첫째 조립품은 그 뒤(그림에서 위쪽·화살표가 카메라 쪽으로 향함 — 9번의 흰 19프레임과 같은 표시)에 있다. 캐터필러 띠, 215프레임·모터(왼쪽 끝), 흰 19프레임·빨간 부시가 보이고 축 끝 2개가 둘째 조립품 215프레임 앞면 칸7·칸14 를 향한다.
#   화살표(초록 링 2개 = 아래 215프레임 가까운 줄(줄2)의 칸7·칸14, 리벳 칸6·칸13 바로 오른쪽 구멍, 간격 7칸 = 70mm = 두 축 간격): 첫째 조립품의 축 끝 → 칸7·칸14.
#   계산: 첫째 조립품을 앞뒤 축(z)으로 180° 돌리면 축 x 가 85,15 → 65,135 = 215프레임 칸7(x=65)·칸14(x=135)가 되고 축 끝(−51)이 위로 향한다. 축은 둘째 조립품의 19프레임(9번, 215프레임 뒤)의 칸2·칸9 구멍과 215프레임 칸7·칸14 를 차례로 지난다(링이 리벳 칸6·13 바로 옆인 것과 맞음). 이렇게 두 모터가 두 판의 바깥쪽에 놓여 13번에서 713프레임 칸2·칸12(10칸 = 100mm)에 꽂히는 것과 맞는다.
s12 = SKEL[11]   # 새 부품 없음(noPart 유지) — 첫째 조립품을 옮기는 단계
s12.note = "[교재 12] 첫째 조립품(캐터필러·19프레임이 달린 것)을 앞뒤 축으로 180° 돌려 둘째 조립품 뒤쪽에서 올려, 두 축 끝을 둘째 19프레임과 215프레임의 칸7·칸14 구멍에 끼워요."
_U1 = [_q for _q in A.parts if _q.step.index <= 8]
_ZU2 = ZB9 + 5.0   # 둘째 조립품 215프레임 가까운 줄(줄2)의 z
def _move_unit(parts, old_ref, new_ref, Rg, at, dir_, hover):   # 한 덩어리 조립품을 새 자리로 옮긴다(위치·회전을 같은 회전으로)
    for q in parts:
        pf = np.array(new_ref, float) + Rg @ (np.array(q.p, float) - np.array(old_ref, float)); Rf = Rg @ np.array(q.R, float)
        q.extra["move"] = {"at": at, "p": rnd(pf), "r": R_to_euler(Rf), "dir": dir_, "hover": hover}; q.extra["moveGroup"] = at
        q.extra["loose"] = True; q.extra["noMarkCheck"] = True
_move_unit(_U1, (75.0, 0.0, 0.0), (75.0, -45.0, _ZU2 - 5.0), np.diag([-1.0, -1.0, 1.0]), 12, [0, -1, 0], 60)   # 첫째 조립품을 앞뒤축(z)으로 180° 돌려 축 끝이 위를 향하게 하고 둘째 조립품 뒤(아래)에서 올린다: 축 x 85,15 → 65,135, 축 끝이 둘째 19프레임·215프레임 구멍을 지나 y 6 에 닿는다
for _q in AX5:   # 화살표: 축 끝 → 둘째 19프레임 칸2·칸9(= 215프레임 칸7·칸14) 구멍 입구(아래 면)
    _q.extra["moveGuide"] = True; _q.extra["move"]["marks"] = [rnd([150.0 - _q.p[0], -5.5, _ZU2])]
A.steps[11].cam = (0.9, 1.5, False, None, None, None); A.steps[11].camSrc = "guess"

# ── 13 ── 교재 15쪽 13 (읽은 것 2026-10-10, 격자 13_1·13_2 — 713프레임 13칸×7줄(모서리 구멍 4곳, 전부 연장), 링 4개 = 칸2 줄4·줄6 / 칸12 줄4·줄6)
#   카메라가 보는 면(책): 713프레임이 아래에 홀면 위로 놓여 있고, 합쳐진 몸(두 조립품)이 그 위에 떠 있다 — 두 DC모터의 옆돌기(윗돌기가 아닌 큰 면 옆 돌기)가 아래(판 쪽)를 향한다.
#   화살표(초록 링 4개): 왼쪽 모터 돌기 2개 → 판 칸2 줄4·줄6, 오른쪽 모터 돌기 2개 → 판 칸12 줄4·줄6(돌기 간격 20mm = 2칸, 두 모터 간격 10칸 = 100mm). 줄 번호는 모터에서 트랙 쪽이 큰 번호.
#   몸을 돌리는 법: 12번에서 두 모터는 몸 한 가운데 축(y)을 따라 100mm 떨어져 같은 z 에 있고 옆돌기(p3·p4)가 +z 쪽을 본다 → 몸 전체를 x 축으로 +90° 돌려 +z 가 아래(−y)로 가게 한다. 판은 칸 번호가 z 반대 방향, 줄 번호가 +x 로 커지게 놓는다.
s13 = SKEL[12]; s13.kw.pop("noPart", None)
s13.note = "[교재 13] 합친 몸을 옆으로 눕혀, 두 DC모터의 옆돌기 2개씩을 713프레임 칸2·칸12 의 줄4·줄6 구멍에 끼워요."
R_713 = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)   # 713프레임: 긴 쪽(칸) → −Z, 짧은 쪽(줄) → +X, 홀면 위
C713 = np.array([75.0, 6.0, -105.0])
RG13 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)     # x 축으로 +90°: 몸의 +z → −y(아래), +y → +z
def _cur_pose(q):
    m = q.extra.get("move")
    return (np.array(m["p"], float), euler_to_R(m["r"])) if m else (np.array(q.p, float), np.array(q.R, float))
def _hole713(c, r): return C713 + R_713 @ np.array([(c - 7) * 10.0, 0.0, (r - 4) * 10.0])
_M2 = _cur_pose(M11)
_pg3 = RG13 @ (_M2[0] + _M2[1] @ np.array([17.5, -1.0, 8.5]))      # 둘째 모터 돌기 p3 (회전 뒤, 이동 전)
_T13 = _hole713(2, 6) - _pg3                                          # 둘째 모터 p3 → 칸2 줄6
_G13 = [_q for _q in A.parts if _q.step.index <= 11]
_PRE13 = {id(_q): _cur_pose(_q) for _q in _G13}
# 9번부터 화면은 x축 +90°로 세운 자세(xform, 아래 정의)다. 13번부터는 판이 눕고 몸이 그 위에 올라가야 하므로, 13번 이후 자세는 "xform 을 거꾸로 돌린 좌표"로 적어 xform 을 통과한 뒤 눕힌 모습이 되게 한다.
_RS = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]]); _C9S = np.array([75.0, 3.5, ZB9])
_T9S = _C9S - _RS @ _C9S + np.array([0.0, 40.0, 0.0])
def _pre(p, R=None):   # 눕힌 세계 좌표 → xform 이전 좌표
    pp = _RS.T @ (np.array(p, float) - _T9S)
    return (pp, _RS.T @ np.array(R, float)) if R is not None else pp
_pp713, _RR713 = _pre(C713, R_713)
P713 = s13.place("713프레임", _RR713, tuple(_pp713), dir=list(rnd(_RS.T @ np.array([0.0, -1.0, 0.0]))), hover=60)
P713.extra["loose"] = True; P713.extra["noMarkCheck"] = True   # 몸 자세를 poseAt(13번 이후)로 줘서 정밀 검사가 기본 자세로는 판과 몸이 맞물림을 못 본다 — 맞물림은 위 "13번 확인" 출력(돌기 위치 = 구멍 위치)으로 확인한다
for _q in _G13:   # 12번 이동(move at 12, 화살표 유지)은 그대로 두고 13번 이후 자세만 poseAt 로 준다
    _pp, _RR = _cur_pose(_q)
    _pf, _Rf = _pre(RG13 @ _pp + _T13, RG13 @ _RR)
    for _k13 in range(13, 38):
        _q.extra.setdefault("poseAt", {})[str(_k13)] = {"p": rnd(_pf), "r": R_to_euler(_Rf)}
for _mq, _cc, _sx in ((M11, 2, 17.5), (M4, 12, -17.5)):   # 둘째 모터는 옆돌기 p3·p4(모델 +x 면), 첫째 모터는 4번 자세를 z 축으로 돌렸기 때문에 p5·p6(모델 −x 면)이 +z 를 본다
    _Mp, _MR = _PRE13[id(_mq)]
    for _pid, _loc in (("p3" if _sx > 0 else "p5", (_sx, -1.0, 8.5)), ("p4" if _sx > 0 else "p6", (_sx, -1.0, -11.5))):
        _w = RG13 @ (_Mp + _MR @ np.array(_loc)) + _T13   # 확인용: 돌기 위치가 판 구멍 줄4·줄6 와 맞는지
        print("13번 확인", _mq.n, _pid, "→ 판 위치", rnd(_w), "구멍 칸%d 줄6" % _cc, rnd(_hole713(_cc, 6)), "줄4", rnd(_hole713(_cc, 4)))
A.steps[12].cam = (0.9, 1.0, False, None, None, None); A.steps[12].camSrc = "guess"

# ── 14 ── 교재 15쪽 14 (읽은 것 2026-10-10, 격자 14_1·14_2 — 27프레임 7칸×2줄 2장(각각 모서리 구멍 4곳 연장), 링 8개 = 두 판 모두 칸1 줄1·줄2 와 칸7 줄1·줄2)
#   카메라가 보는 면(책): 검은 27프레임 2장이 홀면 위로 놓여 있고(칸1 아래·왼쪽 끝, 칸7 위·오른쪽 끝, 줄1 위쪽·줄2 아래쪽), 각 판 위에 회색 2단블록이 2개씩(양 끝 칸 위) 떠 있다. 블록은 구멍 면(큰 구멍 2개)이 왼쪽 앞을 보고, 긴 쪽 끝 돌기가 오른쪽 아래를 향하며, 돌기 2개가 있는 긴 면이 아래(판 쪽)다.
#   화살표(초록 링 8개): 블록의 아래 돌기 2개 → 판 칸1 의 줄1·줄2, 판 칸7 의 줄1·줄2 (블록 돌기 간격 10mm = 줄 간격). 판 두 장은 같은 모양이라 같은 부품으로 두 벌(2개 만들기)을 한 화면에 나란히 둔다.
#   블록 방향: 돌기 면(모델 +z)이 아래(−y), 긴 쪽(모델 x)이 판 짧은 쪽(줄) 방향(+z), 구멍 축(모델 y)이 판 긴 쪽 −x. 돌기 p3(모델 x −4.4)가 줄1, p4(x 5.7)가 줄2.
s14 = SKEL[13]; s14.kw.pop("noPart", None)
s14.note = "[교재 14] 검은 27프레임 2장 각각의 양 끝(칸1·칸7) 두 줄 구멍에 2단블록의 아래 돌기 2개를 끼워요(블록 4개, 판 2장)."
R_BLK_W = np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]], float)   # 2단블록: 돌기 면(모델 +z) → 아래(−y), 긴 쪽(모델 x) → +z(줄 방향), 구멍 축(모델 y) → −x
ZF14 = (-300.0, -360.0)   # 두 벌을 한 화면에 나란히 둔다(몸은 창고 2 에 숨김)
R_BLK = _RS.T @ R_BLK_W   # 눕힌 세계 → xform 이전 좌표
F27_14 = [s14._add(Part("27프레임", _RS.T @ R_FL, tuple(_pre((0.0, 3.5, _z))), s14, {})) for _z in ZF14]
BLK14 = []
for _f in F27_14:
    for _c in (1, 7):
        BLK14.append(s14.attach("2단블록", R_BLK, {"p3": (_f, "홀면 +y 열%d·줄1" % _c), "p4": (_f, "홀면 +y 열%d·줄2" % _c)}, hover=40))
A.steps[13].cam = (0.9, 1.0, False, None, None, None); A.steps[13].camSrc = "guess"

# ── 15 ── 교재 16쪽 15 (읽은 것 2026-10-10, 격자 15_1·15_2 — 가까운 215프레임(둘째 조립품) 15칸×2줄, 링 4개 = 칸9 줄1·줄2, 칸15 줄1·줄2)
#   카메라가 보는 면(책): 713프레임 위에 눕힌 몸(두 DC모터가 판 가장자리, 사이에 캐터필러 띠). 카메라 쪽 215프레임의 리벳 끝이 보이는 면(몸 바깥쪽 면)에 14번에서 만든 27프레임 조립품(양 끝 2단블록)이 오른쪽 아래에서, 반대쪽(먼 215프레임)에는 같은 조립품이 왼쪽 위에서 다가온다.
#   화살표(초록 링): 블록의 돌기 2개씩 → 215프레임 칸9 줄1·줄2, 칸15 줄1·줄2 (블록 간격 6칸 = 27프레임 칸1·칸7). 먼 쪽 링은 트랙에 가려 안 보인다 — 가까운 쪽과 몸의 가운데 면을 기준으로 좌우 대칭이라고 판단(추정).
s15 = SKEL[14]   # 새 부품 없음(noPart 유지) — 14번 조립품을 옮겨 붙이는 단계
s15.note = "[교재 15] 14번에서 만든 27프레임 조립품 2벌을 몸 양쪽 215프레임 바깥 면에 끼워요(블록 돌기 2개씩, 칸9·칸15의 두 줄 구멍)."
_CONN = json.load(open("conn.json", encoding="utf-8"))
def _hole_w(plate_D, c, r):   # plate_D = (p, R) 눕힌 세계, 215프레임 구멍 h{c}_{r} 의 (위치, 방향)
    h = next(x for x in _CONN["215프레임"]["holes"] if x["id"] == "h%d_%d" % (c, r))
    return plate_D[0] + plate_D[1] @ np.array(h["pos"], float), plate_D[1] @ np.array(h["dir"], float)
def _D(q):
    pp, RR = _cur_pose(q); return RG13 @ pp + _T13, RG13 @ RR
_PL_NEAR, _PL_FAR = _D(P9), _D(P1)
_BP = {x["id"]: x for x in _CONN["2단블록"]["pegs"]}
_BP_ALL = _BP
_BP3 = {x["id"]: x for x in _CONN["3단블록"]["pegs"]}
def _fit_asm(asm_parts, plate_D, want_cols, outer_sign):
    """조립품(프레임+블록 2개)을 눕힌 세계에서 돌려 블록 돌기 p5·p6 가 plate 의 want_cols 칸 두 줄 구멍에 들어가게 하는 변환 (R_g, t) 을 구한다."""
    blocks = [q for q in asm_parts if q.n == "2단블록"]
    W0 = {id(q): (_RS @ np.array(q.p, float) + _T9S, _RS @ np.array(q.R, float)) for q in asm_parts}
    cands = []
    for ax in (+1, -1):
        Rx = np.array([[1, 0, 0], [0, 0, -ax], [0, ax, 0]], float)
        for zr in (0, 1):
            Rz = np.diag([-1.0, -1.0, 1.0]) if zr else np.eye(3)
            cands.append(Rx @ Rz)
    best = None
    for Rg in cands:
        peg_w = lambda q, pid: (Rg @ (W0[id(q)][0] + W0[id(q)][1] @ np.array(_BP[pid]["pos"], float)), Rg @ (W0[id(q)][1] @ np.array(_BP[pid]["dir"], float)))
        for rr0 in (1, 2):
            tgt, hd = _hole_w(plate_D, want_cols[0], rr0)
            t = tgt - peg_w(blocks[0], "p5")[0]
            err = 0.0; ok = True
            for q in blocks:
                for pid in ("p5", "p6"):
                    pw, dw = peg_w(q, pid); pw = pw + t
                    dmin = 1e9
                    for c in want_cols:
                        for r in (1, 2):
                            hw, hdv = _hole_w(plate_D, c, r)
                            d = float(np.linalg.norm(pw - hw))
                            if d < dmin and abs(float(dw @ hdv)) > 0.98: dmin = d
                    err += dmin; ok = ok and dmin < 1.5
                bc = Rg @ W0[id(q)][0] + t   # 블록 몸이 plate 의 바깥쪽에 있어야 한다
                n_out = outer_sign * np.array(_hole_w(plate_D, want_cols[0], 1)[1], float)
                ok = ok and float((bc - plate_D[0]) @ n_out) > 0
            if ok and (best is None or err < best[0]): best = (err, Rg, t)
    return best, W0
_NEARX = (9, 15)
_ASM_W = {}   # 조립품 이름 → {부품 id: (눕힌 세계 위치, 회전)} — 16번 빨간 프레임 자리 계산용
for _name, _asm, _plate, _cols in (("가까운 쪽", [F27_14[0]] + BLK14[0:2], _PL_NEAR, _NEARX), ("먼 쪽", [F27_14[1]] + BLK14[2:4], _PL_FAR, None)):
    if _cols is None:   # 먼 쪽: 가까운 쪽과 같은 x 의 칸(몸 가운데 면 기준 대칭)
        _xs = [float(_hole_w(_PL_NEAR, c, 1)[0][0]) for c in _NEARX]
        _cols = tuple(next(c for c in range(1, 16) if abs(float(_hole_w(_PL_FAR, c, 1)[0][0]) - x) < 1.0) for x in _xs)
    _out = 1 if _name == "가까운 쪽" else -1
    _res, _W0 = _fit_asm(_asm, _plate, _cols, 1)
    if _res is None: _res, _W0 = _fit_asm(_asm, _plate, _cols, -1)
    print("15번 %s: 칸 %s 오차 합 %s" % (_name, _cols, None if _res is None else round(_res[0], 2)))
    if _res is None: continue
    _, _Rg, _t = _res
    _ASM_W[_name] = {}
    for _q in _asm:
        _wp, _wR = _W0[id(_q)]
        _ASM_W[_name][id(_q)] = (_Rg @ _wp + _t, _Rg @ _wR)
        _fp, _fR = _pre(_Rg @ _wp + _t, _Rg @ _wR)
        _q.extra["move"] = {"at": 15, "p": rnd(_fp), "r": R_to_euler(_fR), "dir": list(rnd(_RS.T @ (_Rg @ np.array([0.0, -1.0, 0.0])))), "hover": 60}
        _q.extra["moveGroup"] = 15; _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True
A.steps[14].cam = (-0.45, 0.85, False, [[20.0, 0.0, -190.0], [230.0, 60.0, -20.0]], None, None); A.steps[14].camSrc = "eye"   # 책 15번: 713프레임이 왼쪽·몸이 오른쪽, 위에서 앞쪽(+z)으로 비스듬히

# ── 16 ── 교재 16쪽 16 (읽은 것 2026-10-10, 격자 16_1·16_2 — 빨간 17프레임 7칸 한 줄 2장(링 두 개 = 칸1·칸7에서 읽은 연장 격자))
#   카메라가 보는 면(책): 15번 결과(713프레임 위에 눕힌 몸, 양쪽 215프레임 바깥 끝에 27프레임 조립품이 붙음). 각 조립품의 2단블록 윗돌기(회색 돌기, 초록 링) 2개 위로 빨간 17프레임이 위에서 내려온다 — 먼 쪽(그림 위)은 왼쪽 블록 쌍, 가까운 쪽(그림 오른쪽 아래)은 오른쪽 블록 쌍.
#   화살표(링): 빨간 17프레임 칸1 → 왼쪽 블록 윗돌기, 칸7 → 오른쪽 블록 윗돌기(블록 간격 6칸 = 프레임 칸1~칸7).
s16 = SKEL[15]; s16.kw.pop("noPart", None)
s16.note = "[교재 16] 빨간 17프레임 2개를 각 조립품의 2단블록 윗돌기 2개 위에 끼워요(프레임 칸1·칸7)."
RED16 = []
_by_id = {id(q): q for q in BLK14}
for _name in ("가까운 쪽", "먼 쪽"):
    _pegs = []
    for _qid, (_wp, _wR) in _ASM_W[_name].items():
        _q = _by_id.get(_qid)
        if _q is None: continue
        _best = max((_BP_ALL[_pid] for _pid in ("p1", "p2")), key=lambda pg: float((_wR @ np.array(pg["dir"], float))[1]))
        _pegs.append((_wp + _wR @ np.array(_best["pos"], float), _wR @ np.array(_best["dir"], float)))
    (_pa, _da), (_pb, _db) = sorted(_pegs, key=lambda t: float(t[0][0]))
    _u = (_pb - _pa) / np.linalg.norm(_pb - _pa); _n = _da / np.linalg.norm(_da)
    _Rf = np.column_stack([_u, _n, np.cross(_u, _n)])
    _cw = _pa + 30.0 * _u
    print("16번 %s: 블록 돌기 간격 %.1f, 돌기 방향 %s" % (_name, np.linalg.norm(_pb - _pa), rnd(_n)))
    _rp, _RR = _pre(_cw, _Rf)
    _fq = s16.place("17프레임", _RR, tuple(_rp), dir=list(rnd(_RS.T @ _n)), hover=40)
    _fq.extra["loose"] = True; _fq.extra["noMarkCheck"] = True
    _fq.extra["marks"] = [rnd(_pre(_pa)), rnd(_pre(_pb))]   # 안내점 = 블록 윗돌기 2개(xform 이전 좌표)
    RED16.append(_fq)
A.steps[15].cam = (-0.45, 0.85, False, [[20.0, 0.0, -190.0], [230.0, 60.0, -20.0]], None, None); A.steps[15].camSrc = "eye"

# ── 17 ── 교재 17쪽 17 (읽은 것 2026-10-10, 격자 17_1·17_2 — 39프레임 9칸×3줄(구멍 27곳 자동 맞춤, 오차 0.7px), 링 4개 = 칸1 줄1·줄3, 칸9 줄1·줄3)
#   카메라가 보는 면(책): 검은 39프레임이 홀면 위로 눕고(칸1 왼쪽, 줄1 위쪽), 그 위에 회색 3단블록 2개가 구멍 면(큰 구멍 3개)을 왼쪽 앞으로 두고 떠 있다. 블록 돌기 면(위에서 보이지 않는 아래쪽 3개)이 프레임을 향한다.
#   화살표: 왼쪽 블록 돌기 → 칸1 의 줄1·줄3(가운데 줄2 구멍에도 가운데 돌기가 들어간다), 오른쪽 블록 돌기 → 칸9 의 줄1·줄3. 블록 길이 40 = 줄 3개(30) + 5씩 밖으로 나온다.
s17 = SKEL[16]; s17.kw.pop("noPart", None)
s17.note = "[교재 17] 검은 39프레임 양 끝(칸1·칸9)에 3단블록의 아래 돌기 3개씩을 끼워요(블록 2개)."
ZF17 = -480.0   # 둘째 새 조립품(창고 4) — 몸(창고 2)·14번 판(창고 3)과 겹치지 않는 자리
F39 = s17._add(Part("39프레임", _RS.T @ R_FL, tuple(_pre((0.0, 3.5, ZF17))), s17, {}))
BLK17 = [s17.attach("3단블록", _RS.T @ R_BLK_W, {"p3": (F39, "홀면 +y 열%d·줄3" % _c), "p4": (F39, "홀면 +y 열%d·줄2" % _c), "p5": (F39, "홀면 +y 열%d·줄1" % _c)}, hover=40) for _c in (1, 9)]
A.steps[16].cam = (0.3, 1.0, False, None, None, None); A.steps[16].camSrc = "eye"

# ── 18 ── 교재 17쪽 18 (읽은 것 2026-10-10, 격자 18_1·18_2 — 713프레임 13칸×7줄(구멍 37곳 자동 맞춤 + 연장), 링 2개 = 칸3 줄1, 칸11 줄1)
#   카메라가 보는 면(책): 15·16번과 같은 몸(713프레임 위 두 모터, 215프레임 사이 캐터필러, 빨간 17프레임 2장) 왼쪽에, 17번의 39프레임 조립품이 프레임을 세운 채 713프레임 바깥 줄(줄1) 위로 내려온다 — 블록 한쪽 끝 돌기가 판 구멍으로 들어간다.
#   화살표(링 2개): 위쪽 블록 끝 돌기 → 713프레임 칸3 줄1, 아래쪽 블록 끝 돌기 → 칸11 줄1 (간격 8칸 = 블록 간격).
s18 = SKEL[17]   # 새 부품 없음(noPart 유지) — 17번 조립품을 옮겨 붙이는 단계
s18.note = "[교재 18] 17번에서 만든 39프레임 조립품을 세워서 두 블록의 끝 돌기를 713프레임 바깥 줄(줄1) 칸3·칸11 구멍에 끼워요."
_PL713_W = (C713.copy(), R_713.copy())
_asm18 = [F39] + BLK17
_W17 = {id(q): (_RS @ np.array(q.p, float) + _T9S, _RS @ np.array(q.R, float)) for q in _asm18}
def _fit18():
    import itertools
    best = None
    perms = [np.array(m) for m in itertools.product([-1, 0, 1], repeat=9) if False]
    mats = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3))
            for i, j in enumerate(perm): M[i, j] = sg[i]
            if abs(np.linalg.det(M) - 1.0) < 1e-6: mats.append(M)
    hole = lambda c, r: (_PL713_W[0] + _PL713_W[1] @ np.array([(c - 7) * 10.0, 0.0, (r - 4) * 10.0]))
    target = [hole(3, 1), hole(11, 1)]
    for Rg in mats:
        for pid in ("p1", "p2"):
            pg = []
            for q in BLK17:
                wp, wR = _W17[id(q)]
                pg.append((Rg @ (wp + wR @ np.array(_BP3[pid]["pos"], float)), Rg @ (wR @ np.array(_BP3[pid]["dir"], float))))
            if not all(abs(float(d @ np.array([0.0, -1.0, 0.0])) - 1.0) < 1e-6 for _, d in pg): continue   # 끝 돌기가 아래를 향해야 한다
            for order in ((0, 1), (1, 0)):
                t = target[0] - pg[order[0]][0]
                err = np.linalg.norm(pg[order[1]][0] + t - target[1])
                if err > 1.0: continue
                c = Rg @ (_W17[id(F39)][0]) + t   # 프레임 가운데: 판 안쪽(줄 번호가 늘어나는 +x)에 있어야 한다
                if c[0] <= target[0][0] + 1.0: continue
                key = (err, abs(c[1] - target[0][1]))
                if best is None or key < best[0]: best = (key, Rg, t, pid)
    return best
_b18 = _fit18()
_fit18_holes = [(_PL713_W[0] + _PL713_W[1] @ np.array([(c - 7) * 10.0, 0.0, 0.0 + (1 - 4) * 10.0])) for c in (3, 11)]
print("18번 조립품 자리 풀이:", None if _b18 is None else ("오차 %.2f" % _b18[0][0], _b18[3]))
if _b18 is not None:
    _, _Rg18, _t18, _pid18 = _b18
    for _q in _asm18:
        _wp, _wR = _W17[id(_q)]
        _fp, _fR = _pre(_Rg18 @ _wp + _t18, _Rg18 @ _wR)
        _q.extra["move"] = {"at": 18, "p": rnd(_fp), "r": R_to_euler(_fR), "dir": list(rnd(_RS.T @ np.array([0.0, 1.0, 0.0]))), "hover": 60}
        _q.extra["moveGroup"] = 18; _q.extra["loose"] = True; _q.extra["noMarkCheck"] = True
    for _q, _h in zip(BLK17, _fit18_holes):   # 화살표: 블록 끝 돌기 → 판 구멍 입구(위 면, xform 이전 좌표)
        _q.extra["moveGuide"] = True; _q.extra["move"]["marks"] = [rnd(_pre(_h + np.array([0.0, 2.5, 0.0])))]
A.steps[17].cam = (-0.45, 0.85, False, [[20.0, 0.0, -190.0], [230.0, 80.0, -20.0]], None, None); A.steps[17].camSrc = "eye"

# ── 19 ── 교재 17쪽 19 (읽은 것 2026-10-10 — 새 713프레임을 몸 위(두 모터 옆돌기 4개 + 39프레임 조립품 블록 끝 돌기 2개)로 내려 끼운다)
#   카메라가 보는 면(책): 18번 결과 위로 검은 713프레임(13칸×7줄)이 눕힌 채 내려온다. 링 6개(판 위): 두 모터의 위쪽 옆돌기(모터마다 2개)와 39프레임 조립품 두 블록의 위쪽 끝 돌기 → 판 구멍.
#   자세는 판 구멍 91곳 중 6개 돌기가 오차 0 으로 들어가는 위치를 수치로 구했다(유일 해).
s19 = SKEL[18]; s19.kw.pop("noPart", None)
s19.note = "[교재 19] 새 713프레임을 위에서 내려 두 DC모터 위쪽 옆돌기 4개와 39프레임 조립품 두 블록의 위쪽 끝 돌기 2개에 끼워요."
def _final_W(q):   # 18번 이후 눕힌 세계 자세
    if id(q) in _W17 and _b18 is not None:
        wp, wR = _W17[id(q)]; return _Rg18 @ wp + _t18, _Rg18 @ wR
    return _D(q)
_UP = np.array([0.0, 1.0, 0.0])
_pegs19 = []
for _mq in (M11, M4):
    _Mp, _MR = _final_W(_mq)
    for _pg in _CONN["DC모터"]["pegs"]:
        _dw = _MR @ np.array(_pg["dir"], float)
        if float(_dw @ _UP) > 0.98: _pegs19.append((_mq.n + "." + _pg["id"], _Mp + _MR @ np.array(_pg["pos"], float)))
for _q in BLK17:
    _wp, _wR = _final_W(_q)
    for _pid in ("p1", "p2"):
        _dw = _wR @ np.array(_BP3[_pid]["dir"], float)
        if float(_dw @ _UP) > 0.98: _pegs19.append((_q.n + "." + _pid, _wp + _wR @ np.array(_BP3[_pid]["pos"], float)))
print("19번 위쪽 돌기:", len(_pegs19), [n for n, _ in _pegs19])
_H713 = [(x["id"], np.array(x["pos"], float)) for x in _CONN["713프레임"]["holes"]]
_best19 = None
for _k in range(4):
    _a = np.deg2rad(90 * _k); _Ry = np.array([[np.cos(_a), 0, np.sin(_a)], [0, 1, 0], [-np.sin(_a), 0, np.cos(_a)]])
    _R19 = _Ry @ R_713
    for _hid, _hp in _H713:
        _t = _pegs19[0][1] - _R19 @ _hp
        _t[1] = 0.0
        _n = 0; _err = 0.0
        for _nm, _pp in _pegs19:
            _d = min(float(np.linalg.norm((_pp - _t - _R19 @ hp)[[0, 2]])) for _, hp in _H713)
            if _d < 1.5: _n += 1; _err += _d
        if _best19 is None or (_n, -_err) > (_best19[0], -_best19[1]): _best19 = (_n, _err, _R19, _t.copy(), _k)
print("19번 판 풀이: 맞은 돌기 %d/%d, 오차 %.2f, 회전 %d°" % (_best19[0], len(_pegs19), _best19[1], 90 * _best19[4]))
_ytop = max(float(pp[1]) for _, pp in _pegs19)
_R19, _t19 = _best19[2], _best19[3]
_c19 = _t19.copy(); _c19[1] = _ytop
_pp19, _RR19 = _pre(_c19, _R19)
P713B = s19.place("713프레임", _RR19, tuple(_pp19), dir=list(rnd(_RS.T @ np.array([0.0, 1.0, 0.0]))), hover=60)
P713B.extra["loose"] = True; P713B.extra["noMarkCheck"] = True
P713B.extra["marks"] = [rnd(_pre(pp)) for _, pp in _pegs19]
A.steps[18].cam = (-0.45, 0.85, False, [[20.0, 0.0, -190.0], [230.0, 100.0, -20.0]], None, None); A.steps[18].camSrc = "eye"

def _addhide(pt, steps_, label):   # 새 창고에서 만드는 번호에서는 앞 창고 부품을 숨긴다(hideAt·store, 안내서 6-5절)
    ex = pt.extra; ex["hideAt"] = sorted(set(ex.get("hideAt", [])) | set(steps_)); st_ = ex.setdefault("store", {})
    for k_ in steps_: st_[str(k_)] = label
for _i in range(1, 9): A.steps[_i - 1].kw["slot"] = 1
for _i in (9, 10, 11): A.steps[_i - 1].kw["slot"] = 2   # 9~11번: 둘째 조립품(창고 2) — 10·11번 그림에서 확인 뒤 조정
for _i in range(12, 38): A.steps[_i - 1].kw["slot"] = 2   # 12번부터는 둘째 조립품(창고 2) 위에 합친 몸 — 임시(해당 번호를 읽을 때 확정)
A.steps[8].kw["history"] = "📦 첫째 조립품(1~8번)을 창고 1에 두고, 창고 2에서 둘째 조립품을 새로 시작"
for _q in A.parts:
    if _q.step.index <= 8: _addhide(_q, [9, 10, 11], "창고 1")   # 9~11번(둘째 조립품을 새 창고 2 에서 만듦): 첫째 조립품은 창고 1 에 둔다
A.steps[11].kw["history"] = "창고 1의 첫째 조립품(1~8번)을 가져와 둘째 조립품(9~11번) 위에 합쳐요(12번 그림 — 그림으로 판단, 추정)"
for _i in range(12, 38): A.meta["lift"][str(_i)] = 110.0 if _i == 12 else (62.0 if _i == 13 else 20.0)   # 12번: 첫째 조립품이 둘째 조립품 아래에 매달려 바닥 아래(−100)까지 내려가므로 화면 전체를 띄운다(13번부터 몸을 돌릴 때 조정)
A.steps[13].kw["slot"] = 3
A.steps[13].kw["history"] = "📦 몸(1~13번)을 창고 2에 두고, 창고 3에서 판 2벌을 새로 시작"
A.steps[14].kw["history"] = "창고 3의 14번(블록 붙인 판 2장)을 가져와 몸에 합쳐요(그림으로 판단 — 15번을 읽을 때 확정)"
for _q in A.parts:
    if _q.step.index <= 13: _addhide(_q, [14], "창고 2")
_R3 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # 3번 화면만 전체를 x축 둘레 +90°(관리자 지시 2026-10-10 "3번만")
_C3 = np.array([75.0, 3.5, 0.0])
for _q in A.parts:
    if _q.step.index <= 3:
        _q.extra.setdefault("poseAt", {})["3"] = {"p": rnd(_R3 @ (np.array(_q.p, float) - _C3) + _C3 + np.array([0.0, 0.0, 0.0])), "r": R_to_euler(_R3 @ np.array(_q.R, float))}
for _q in (BO3, NT3): _q.extra["dir"] = rnd(_R3 @ np.array(_q.extra["dir"], float))   # 3번에서 새로 놓이는 부품은 떠 있는 방향도 같이 돌린다
for _q in A.parts:   # 4번도 같은 자세(x축 +90°, 관리자 지시 2026-10-10 "1차시에 4번")
    if _q.step.index <= 4:
        _q.extra.setdefault("poseAt", {})["4"] = {"p": rnd(_R3 @ (np.array(_q.p, float) - _C3) + _C3), "r": R_to_euler(_R3 @ np.array(_q.R, float))}
M4.extra["dir"] = rnd(_R3 @ np.array(M4.extra.get("dir", [0.0, 1.0, 0.0]), float))
A.steps[3].cam = (0.3, 1.25, False, None, None, None); A.steps[3].camSrc = "guess"
A.meta["lift"]["4"] = 35.0   # 4번: 눕힌 자세에서 바닥 아래로 내려가는 부분(모터 −21)을 띄운다
# 5~8번: 책이 "조립품을 뒤집어 보세요"(5번)이고 그림은 판이 서서 카메라를 향한 모양(축이 앞·아래, 부시가 뒤·위)이라 조립품을 뒤집고 세워 놓는다 — 카메라를 땅 밑으로 보내지 않는다(관리자 지시 2026-10-10 "지하에서 보고 있다")
_RF = np.array([[-1.0, 0, 0], [0, 0, -1.0], [0, -1.0, 0]]); _CF = np.array([75.0, 0.0, 0.0]); _SF = np.array([0.0, 40.0, 0.0])   # 책 5번 근접 그림 = 아래에서 본 모습: 27프레임 아래 면(구멍 3칸×2줄, 구멍 속에 모터 십자가 비침)·너트·리벳 끝이 카메라 쪽, 모터는 뒤쪽 왼쪽 끝에서 옆돌기 2개가 위(+y)를 향함. z축 180° 뒤집기 + x축 +90° 세우기(모터 옆돌기 면 +x 는 4번과 같이 위를 향한다)
for _k in (5, 6, 7, 8):
    for _q in A.parts:
        if _q.step.index <= _k:
            _q.extra.setdefault("poseAt", {})[str(_k)] = {"p": rnd(_RF @ (np.array(_q.p, float) - _CF) + _CF + _SF), "r": R_to_euler(_RF @ np.array(_q.R, float))}
        if _q.step.index == _k and "dir" in _q.extra:
            _q.extra["dir"] = rnd(_RF @ np.array(_q.extra["dir"], float))
        if _q.step.index == _k and _q.extra.get("marks"):
            _q.extra["marks"] = [rnd(_RF @ (np.array(m, float) - _CF) + _CF + _SF) for m in _q.extra["marks"]]
for _k in (5, 6, 7, 8): A.steps[_k - 1].cam = (-0.4, 1.3, False, None, None, None); A.steps[_k - 1].camSrc = "guess"
NT3.extra["marks"] = [rnd(np.array(BO3.p, float) + np.array([0.0, -6.9, 0.0]))]; NT3.extra["noMarkCheck"] = True; NT3.extra["loose"] = True   # 축·부시처럼: 너트 화살표는 12볼트 끝(돌린 자세)에 닿는다
A.steps[16].kw["slot"] = 4
A.steps[16].kw["history"] = "📦 몸(1~16번)을 창고 2에 두고, 창고 4에서 39프레임 조립품을 새로 시작"
A.steps[17].kw["history"] = "창고 4의 17번(블록 붙인 39프레임)을 가져와 몸에 합쳐요(그림으로 판단)"
for _q in A.parts:
    if _q.step.index <= 16: _addhide(_q, [17], "창고 2")
A.meta["finalSlot"] = 0

for _k in (6, 7, 8): A.meta["lift"][str(_k)] = 1.0   # 뒤집어 세운 자세(+40)라 따로 띄울 필요 없다 — 바닥 검사가 막으면 다시 올린다
# 9~12번: 책 그림은 215프레임이 서서 카메라를 향한 모양 — 9번부터 전체를 x축 +90° 로 세운다(xform, 둘째 조립품 자리 기준). 13번 이후 자세는 위 13번 블록에서 거꾸로 돌린 좌표로 준다.
A.meta["xform"] = {"at": 9, "m": _RS.tolist(), "t": [round(float(v), 3) for v in _T9S]}
for _k in (9, 10, 11, 12): A.steps[_k - 1].cam = (0.3, 1.25, False, None, None, None); A.steps[_k - 1].camSrc = "eye"
for _k in (6, 7, 8):   # 뒤집어 세운 자세에서 모터(왼쪽 끝)와 축 끝이 화면에 다 들어오게 가운데 점을 준다
    _pts = [np.array(_q.extra["poseAt"][str(_k)]["p"], float) for _q in A.parts if _q.step.index <= _k and str(_k) in (_q.extra.get("poseAt") or {})]
    _lo, _hi = np.min(_pts, axis=0), np.max(_pts, axis=0)
    A.steps[_k - 1].cam = (A.steps[_k - 1].cam[0], A.steps[_k - 1].cam[1], False, [rnd(_lo), rnd(_hi)], None, None)
# 바닥에 닿거나 바닥선 위로 겹쳐 보이는 부품을 전부 띄운다(관리자 지시 2026-10-10 "바닥아래 내려가있는것들도 다 올려") — 번호마다 가장 낮은 점이 12mm 이상 위에 오게 화면 전체를 올린다
_FLOOR_UP = {1: 11.0, 2: 11.0, 6: 2.0, 7: 2.0, 8: 11.5, 13: 68.5, 38: 11.0, **{_k: 23.0 for _k in range(15, 38)}}
for _k, _v in _FLOOR_UP.items(): A.meta["lift"][str(_k)] = _v
for _k in range(1, 15): A.steps[_k - 1].camSrc = "eye"   # 책 1~4번 그림에서 읽은 방향(긴 쪽 가로·칸1 왼쪽·가까운 줄 아래, 오른쪽 끝이 약간 가까움)으로 정한 값 — 화면에서 책 그림과 나란히 확인한 뒤에만 유지
import stepchecks; stepchecks.apply(A, "speedbike")           # 번호마다 한 일을 체크박스로 설명 끝에 적는다(관리자 지시 2026-10-08) — 지금까지 빠뜨렸던 것
A.save_links()                                    # 이번 빌드의 잠금 기록 저장(수정 지시가 있는 빌드는 갱신하지 않는다)
A.check_fixes()                                   # 적용되지 않은 수정 지시가 있으면 경고(번호가 밀렸거나 오타)
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({"steps": steps}, open("speedbike_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    import os
    _df = json.load(open("speedbike_def.json", encoding="utf-8")) if os.path.exists("speedbike_def.json") else {}
    if A.meta.get("lift"): _df["lift"] = A.meta["lift"]            # 화면 전체를 띄우는 높이(검사·화면이 같이 읽음)
    if A.meta.get("xform"): _df["xform"] = A.meta["xform"]
    json.dump(_df, open("speedbike_def.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("speedbike_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
