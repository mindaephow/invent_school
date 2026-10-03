# 앞 단계를 고치면 뒤 단계가 따라오는지(수정 지시 fixes + 상대 위치) 작은 조립도로 시험한다.   python test_fixes.py
#   1단계: 315프레임(뿌리)   2단계: 3단블록이 315프레임 끝에 걸쳐 꽂힘   3단계: 35프레임을 그 블록 돌기에 맞춰 놓음(place_by)   4단계: 2단블록이 35프레임에 꽂힘
import io, os, sys, contextlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from asmlib import Asm, orient

R_FLAT = orient("315프레임", {"홀면 +y": "위"})
R_L = orient("3단블록", {"돌기면 +z": "아래", "홀면 +y": "+Z"})

def build(fixes):
    A = Asm("test", "시험", "—"); A.fixes = fixes
    s1 = A.step("1"); s1.place("315프레임", R_FLAT, (0, 2.5, 0))
    s2 = A.step("2")
    s2.attach("3단블록", R_L, {"돌기면 +z 1": ("315프레임 1번", "홀면 +y 열14·줄1"), "돌기면 +z 2": ("315프레임 1번", "홀면 +y 열15·줄1")}, hover=45)
    s3 = A.step("3")
    s3.place_by("35프레임", R_FLAT, {"홀면 +y 열1·줄1": ("3단블록 1번", "돌기면 +z 3")})
    s4 = A.step("4")
    s4.attach("2단블록", R_L, {"돌기면 +z 1": ("35프레임 1번", "홀면 +y 열3·줄2"), "돌기면 +z 2": ("35프레임 1번", "홀면 +y 열4·줄2")}, hover=45)
    return A

def poses(A): return {p.name: np.array(p.p) for p in A.parts}
fails = 0
def check(label, ok, extra=""):
    global fails
    print(("✓ " if ok else "✗ ") + label, extra); fails += 0 if ok else 1

base_A = build([]); base = poses(base_A)
print("기본 위치:", {k: v.round(1).tolist() for k, v in base.items()}, "경고", len(base_A.warn))

# 1) 뿌리 판을 z 로 30 옮기면(shift) 뒤 단계 전부가 같이 30 따라와야 한다
A1 = build([{"type": "shift", "part": "315프레임 1번", "delta": [0, 0, 30]}]); P1 = poses(A1)
ok = all(np.allclose(P1[k] - base[k], [0, 0, 30]) for k in base)
check("뿌리 판을 z+30 옮기면 뒤 단계(블록·35프레임·2단블록)가 모두 따라온다", ok, {k: (P1[k] - base[k]).round(1).tolist() for k in base}); A1.check_fixes()
check("  (경고 없음)", len(A1.warn) == 0, A1.warn)

# 2) 블록을 한 칸(−10 x) 옆으로 꽂도록 join 수정 → 35프레임·2단블록이 따라와야 한다(35프레임은 블록 돌기 3에서 계산되므로)
fx = [{"type": "join", "part": "3단블록 1번", "peg": "돌기면 +z 1", "host": "315프레임 1번", "hole": "홀면 +y 열13·줄1"},
      {"type": "join", "part": "3단블록 1번", "peg": "돌기면 +z 2", "host": "315프레임 1번", "hole": "홀면 +y 열14·줄1"}]
A2 = build(fx); P2 = poses(A2)
ok = all(np.allclose(P2[k] - base[k], [-10, 0, 0]) for k in ("3단블록 1번", "35프레임 1번", "2단블록 1번")) and np.allclose(P2["315프레임 1번"], base["315프레임 1번"])
check("블록을 한 칸(−x) 옆 구멍에 꽂으면 뒤 단계가 같이 −10 따라오고 뿌리 판은 그대로", ok, {k: (P2[k] - base[k]).round(1).tolist() for k in base}); A2.check_fixes()

# 3) 적용되지 않는 지시(번호 오타·밀림)는 조용히 무시되지 않고 경고
A3 = build([{"type": "shift", "part": "315프레임 9번", "delta": [0, 0, 5]}]); bad = A3.check_fixes()
check("없는 부품을 가리키는 수정 지시는 '적용되지 않았다' 경고", len(bad) == 1)
print("실패", fails); sys.exit(1 if fails else 0)
