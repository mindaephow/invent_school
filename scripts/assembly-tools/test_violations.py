# 위반 수집 시험 — cubo_joint_check 가 낸 메시지가 겹침·틈·방향으로 분류되고 화면 부품 키가 붙는지(풍차). 실제 위반이 없어도 돌도록 점검기를 대신해 가짜 위반을 낸다.
#   python test_violations.py     통과하면 OK
import asmpath, violations as V, cubo_joint_check as cj
A = V._load("windmill"); real = cj.check
def fake(A_, k):
    out = []
    if k == 12:
        vs = cj.view(A_, k); r = [x for x in vs if x.n == "리벳"][0]; f = [x for x in vs if x.n == "315프레임"][0]
        cj._em(out, "규칙8 리벳 틈: 리벳↔315프레임 +2.0mm", r, f); cj._em(out, "규칙3 315프레임↔315프레임 겹침: 구멍 중심 간격 5.0mm", f)
        cj._em(out, "규칙10 메인보드 방향이 책과 다름", f)
    return out
cj.check = fake
try: r = V.collect("windmill")
finally: cj.check = real
t = {v["type"]: v["keys"] for v in r["12"] if v["type"] in ("gap", "overlap", "orient")}
assert set(t) == {"gap", "overlap", "orient"}, t
assert all(k.count(":") == 1 for ks in t.values() for k in ks) and t["gap"], t
print("OK 위반 수집 분류", {k: len(v) for k, v in t.items()})
