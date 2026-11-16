# 증거 모양 지문(stepfp) 시험 — 뒤 번호 자리를 바꿔도 앞 번호 증거는 그대로이고, 그 자리를 쓰는 번호의 증거는 낡아야 한다.   python test_stepfp.py
import copy, stepfp
def steps(mv14=(100, 0, 0), pose3=(5, 0, 0), shift=0):
    P = lambda n, x, **e: dict({"n": n, "p": [x + shift, 0, 0], "r": [0, 0, 0]}, **e)
    return [{"note": "1", "parts": [P("315프레임", 0, move={"at": 3, "p": [mv14[0] + shift, mv14[1], mv14[2]], "r": [0, 0, 0]})]},
            {"note": "2", "parts": [P("리벳", 10, poseAt={"3": {"p": [pose3[0] + shift, 0, 0], "r": [0, 0, 0]}})]},
            {"note": "3", "parts": [P("3단블록", 20)]}]
def ev(st, k): return {"fp": "x", "shape": stepfp.shape_fp(st[k - 1], stepfp.anchor(st), k, st)}
a = steps(); e1, e2, e3 = ev(a, 1), ev(a, 2), ev(a, 3)
b = steps(mv14=(300, 0, 50), pose3=(9, 0, 0))                    # 3번 화면에서의 자리만 바꿈
assert stepfp.same(e1, b[0], b) and stepfp.same(e2, b[1], b), "뒤 번호(3번) 자리를 바꿨는데 1·2번 증거가 낡았다"
assert not stepfp.same(e3, b[2], b), "3번 화면 자리를 바꿨는데 3번 증거가 그대로다"
c = steps(shift=40)                                              # 조립 전체를 같이 옮김 = 모양 같음
assert all(stepfp.same(e, c[k], c) for k, e in enumerate((e1, e2, e3))), "전체 평행이동인데 증거가 낡았다"
d = steps(); d[1]["parts"][0]["p"] = [11, 0, 0]                  # 2번 부품 자리를 바꿈 = 2번 모양이 달라짐
assert not stepfp.same(e2, d[1], d) and stepfp.same(e1, d[0], d)
old = {"fp": "x", "shape": stepfp.shape_fp(a[0], stepfp.anchor(a))}   # 옛 정의로 남긴 증거도 내용이 그대로면 받는다
assert stepfp.same(old, a[0], a) and stepfp.same(old, copy.deepcopy(a[0]), a)
# 동일 확인 재서명(geo·geo_diff): 플래그·설명만 바뀌면 같고, 자리·안내점·들어오는 자리·보는 방향(15° 넘게)이 바뀌면 다르다
G = lambda st, k: stepfp.geo(st[k - 1], stepfp.anchor(st), k, st)
f = steps(); f[2]["parts"][0]["noMarkCheck"] = True; f[2]["note"] = "설명만 바뀜"; f[2]["parts"][0]["p"] = [20.001, 0, 0]
assert not stepfp.same(e3, f[2], f) and stepfp.geo_diff(G(a, 3), G(f, 3))[0], "플래그·설명·0.001mm 차이인데 조립이 다르다고 나왔다"
assert not stepfp.geo_diff(G(a, 3), G(b, 3))[0], "3번 화면에 들어오는 자리가 바뀌었는데 같다고 나왔다"
assert not stepfp.geo_diff(G(a, 2), G(d, 2))[0], "부품 자리가 1mm 바뀌었는데 같다고 나왔다"
h = steps(); h[2]["parts"].append(dict(h[2]["parts"][0])); assert not stepfp.geo_diff(G(a, 3), G(h, 3))[0], "부품이 늘었는데 같다고 나왔다"
c1, c2, c3 = steps(), steps(), steps(); c1[2]["cam"] = {"theta": 0.8, "phi": 1.3}; c2[2]["cam"] = {"theta": 0.95, "phi": 1.3}; c3[2]["cam"] = {"theta": 1.4, "phi": 1.3}
assert stepfp.geo_diff(G(c1, 3), G(c2, 3))[0] and not stepfp.geo_diff(G(c1, 3), G(c3, 3))[0], "보는 방향 허용(15°)이 안 맞는다"
print("OK 증거 모양 지문")
