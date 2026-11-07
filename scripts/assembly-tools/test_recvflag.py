# recv 표시 판정 시험 — guidecheck.receives_by_hole / tail_on_own_peg 가 풍차 12번 315프레임(구멍으로 받음)을 올바로 가르는지.
#   python test_recvflag.py     (통과하면 "OK", 아니면 AssertionError)
import asmpath, runpy, numpy as np, guidecheck as G
g = runpy.run_path("windmill.py", run_name="probe")
A = next(v for v in g.values() if hasattr(v, "steps") and hasattr(v, "parts") and hasattr(v, "meta"))
e = A.steps[11].kw["moveMade"]["11:0"]; q = A.steps[10].parts[0]
q.p, q.R = np.array(e["p"], float), G.euler_to_R(e["r"])
u, hv = G.unit(e["dir"]), float(e["hover"])
for m in e["marks"]:
    assert G.receives_by_hole(q, m, u, hv), "315프레임 안내점은 자기 구멍 중심이어야 한다"
    assert not G.tail_on_own_peg(q, m, u, hv, 5.0), "구멍으로 받는 프레임은 돌기 꼬리가 아니다"
print("OK recv 판정", len(e["marks"]), "점")
