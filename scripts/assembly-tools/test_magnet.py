# 자석 결합 점검 시험 — 좌표를 직접 준 부품(asmlib.hand_placed)과 축에 꿴 부품 틈(violations.shaft_gaps)이 잡히는지. 조립도 파일 없이 작은 모형으로 돈다.
#   python test_magnet.py     통과하면 OK
import asmpath, sys
import numpy as np
import asmlib, violations as V
from asmlib import Asm, Part, rot_x
sys.stdout.reconfigure(encoding="utf-8")
A = Asm("cubo-0-test", "시험", "시험")
s1 = A.step("기어 + T축"); s2 = A.step("판 + 부시")
R = rot_x(90)                                                           # 모델 +y → +Z
gear = s1.place("큰기어", R, (0, 50, 0))                                # 앵커(첫 부품)
t = s1.attach("T축", R, {"p1": (gear, "h3")})                           # 머리가 기어 면에 닿는 자리(attach 계산)
pl = s2.recv("315프레임", R, {"홀면 -y 열14·줄2": (t, "p1")}, dir=[0, 0, 1], against=gear)
bu = s2.recv("부시", rot_x(-90), {"h1": (t, "p1")}, dir=[0, 0, 1], against=pl)
assert asmlib.hand_placed(A) == [], asmlib.hand_placed(A)             # 앵커 하나뿐이면 손 배치 0
assert V.shaft_gaps(A, 1) == [] and V.shaft_gaps(A, 2) == [], (V.shaft_gaps(A, 1), V.shaft_gaps(A, 2))   # 결합으로 놓으면 틈 0
pl.p = pl.p + np.array([0, 0, 1.0]); bu.p = bu.p + np.array([0, 0, 1.0])  # 판·부시를 1mm 띄운다 → 판↔기어 틈
g2 = V.shaft_gaps(A, 2); assert len(g2) == 1 and "틈 1.0mm" in g2[0][1] and "315프레임" in g2[0][1], g2
t.p = t.p - np.array([0, 0, 1.5])                                       # T축을 1.5mm 덜 끼운다 → 머리 뜸
g1 = V.shaft_gaps(A, 1); assert len(g1) == 1 and "머리가 큰기어 면에서 1.5mm" in g1[0][1], g1
s2.place("작은기어", R, (30, 50, -6.5)); s2._add(Part("리벳", np.eye(3), (0, 0, 0), s2, {}))   # 앵커가 아닌 place·Part 직접 생성
assert [(k, q.n, how) for k, i, q, how in asmlib.hand_placed(A)] == [(2, "작은기어", "place"), (2, "리벳", "Part")], asmlib.hand_placed(A)
print("OK 자석 결합 점검: 손 배치 2곳·축 틈·T축 머리 뜸")
