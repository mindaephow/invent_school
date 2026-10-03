# orient(면 → 방향)로 만든 자세가 오토건에서 손으로 쓴 자세(R_LIE, R_FLAT …)와 같은지, 모순 조건은 오류가 나는지 확인한다.   python test_orient.py
import io, os, sys, contextlib
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import autogun as G
import partlib, faces
from asmlib import orient

fails = 0
def eq(label, R1, R2):
    global fails
    ok = np.allclose(R1, R2, atol=1e-6)
    print(("✓ " if ok else "✗ ") + label)
    if not ok: print("   손으로 쓴 자세\n", np.round(R2, 3), "\n   orient 결과\n", np.round(R1, 3)); fails += 1

# 눕힌 블록(R_LIE): 돌기면 +z 가 아래, 홀면 +y 가 +Z 쪽(앞에서 본 2단블록 5번과 같다)
for n in ("2단블록", "3단블록"):
    eq(f"{n} 눕힘(R_L): 돌기면 +z → 아래, 홀면 +y → +Z", orient(n, {"돌기면 +z": "아래", "홀면 +y": "+Z"}), G.R_L)
# 평평한 프레임(R_FLAT): 홀면 +y 가 위, 홀면 +x?? 프레임은 홀면만 있어서 +y 하나로 정한다 + 길이 방향 x 는 +X
eq("315프레임 평평(R_FLAT): 홀면 +y → 위", orient("315프레임", {"홀면 +y": "위"}), G.R_FLAT)
# 37프레임을 +z 쪽으로 눕힌 자세(R_Z): 길이(x)가 월드 +Z
eq("37프레임 R_Z: 홀면 +y → 위, 길이 방향(축 +x) → +Z", orient("37프레임", {"홀면 +y": "위", "축 +x": "+Z"}), G.R_Z)

# 한 조건만 주면 결과가 하나로 정해지고(검산용 describe 로 확인)
R = orient("3단블록", {"돌기면 +z": "아래"})
d = faces.describe_orientation(partlib.get("3단블록"), R)
ok = d["돌기면 +z"] == "아래" and d["돌기면 -z"] == "위"
print(("✓ " if ok else "✗ ") + "조건 1개: 돌기면 +z 아래 → 돌기면 -z 는 위", d["돌기면 +z"], d["돌기면 -z"]); fails += 0 if ok else 1

# 모순 조건·같은 축 조건·없는 면·모르는 방향은 오류
for label, f in (("모순(두 면 90°인데 두 방향은 180°)", lambda: orient("3단블록", {"돌기면 +z": "아래", "홀면 +y": "위"})),
                 ("같은 축 두 면", lambda: orient("3단블록", {"홀면 +y": "위", "홀면 -y": "아래"})),
                 ("없는 면", lambda: orient("315프레임", {"돌기면 +z": "위"})),
                 ("모르는 방향", lambda: orient("3단블록", {"돌기면 +z": "왼쪽"}))):
    try: f(); print("✗ " + label + ": 오류가 안 났다"); fails += 1
    except (ValueError, KeyError) as e: print("✓ " + label + " → 오류:", str(e)[:60])
print("실패", fails)
sys.exit(1 if fails else 0)
