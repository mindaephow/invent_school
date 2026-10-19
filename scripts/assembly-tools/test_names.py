# 이름으로 쓴 결합(attach/recv)이 id·좌표로 쓴 결합과 같은 결과를 내는지, 앞뒤를 거꾸로 쓰면 경고가 나는지 확인한다.
# 오토건의 교재 15번(조립도 16단계) 결합을 그대로 가져다 이름 버전으로 다시 만든다.   python test_names.py
import os, sys
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import autogun as G                       # 오토건 전체를 만든다(출력 파일은 쓰지 않는다)

A = G.A
t = A.step("이름 결합 시험")
fails = 0
def same(label, a, b):
    global fails
    ok = np.allclose(a.p, b.p, atol=1e-6) and np.allclose(a.R, b.R) and a.extra["marks"] == b.extra["marks"] and a.extra.get("dir") == b.extra.get("dir")
    print(("✓ " if ok else "✗ ") + label, "" if ok else f" 위치 {a.p} / {b.p}  marks {a.extra['marks']} / {b.extra['marks']}")
    fails += 0 if ok else 1

# 3단블록: id·좌표 방식(G.k4) 대 이름 방식
k4n = t.attach("3단블록", G.R_L, {
    "돌기면 +z 1": ("35프레임 1번", "홀면 +y 열5·줄1"),
    "돌기면 +z 2": ("315프레임 3번", "홀면 +y 열1·줄1"),
    "돌기면 +z 3": ("315프레임 3번", "홀면 +y 열2·줄1")}, hover=45)
same("3단블록 (id ↔ 이름)", G.k4, k4n)
# 2단블록
k5n = t.attach("2단블록", G.R_L, {
    "돌기면 +z 1": ("35프레임 1번", "홀면 +y 열5·줄3"),
    "돌기면 +z 2": ("315프레임 3번", "홀면 +y 열1·줄3")}, hover=45)
same("2단블록 (id ↔ 이름)", G.k5, k5n)

# 앞뒤를 거꾸로 쓰면 경고가 나야 한다(홀면 -y 는 돌기가 들어오는 쪽이 아님)
n0 = len(A.warn)
t.attach("3단블록", G.R_L, {"돌기면 +z 1": ("35프레임 1번", "홀면 -y 열5·줄1")}, hover=45)
warned = len(A.warn) > n0
print(("✓ " if warned else "✗ ") + "앞뒤 반대 면을 쓰면 경고", "" if warned else "(경고가 안 났다)")
fails += 0 if warned else 1

# 없는 이름은 가능한 이름을 알려 주며 오류
try:
    t.attach("3단블록", G.R_L, {"돌기면 +z 9": ("35프레임 1번", "홀면 +y 열5·줄1")}, hover=45)
    print("✗ 없는 번호가 오류를 안 냈다"); fails += 1
except KeyError as e:
    print("✓ 없는 번호는 오류:", str(e)[:70])
print("실패", fails)
sys.exit(1 if fails else 0)
