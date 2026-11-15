# "2개 만들기" 둘째 벌 검사(hidecheck.twin_built) 시험 — 나란히 새로 만든 둘째 벌은 걸리고, 복사(copy_to_slot)·한 벌 안의 같은 부품 둘·거울 둘째 벌은 안 걸린다.   python test_twin.py
import hidecheck as H
P = lambda n, x, y=0, z=0, r=(0, 0, 0), **e: dict({"n": n, "p": [x, y, z], "r": list(r)}, **e)
def st(note, parts): return {"note": "[교재] …" + chr(10) + "▣ 사용 부품: " + note, "parts": parts}
bad = [st("큰기어 2, T축 4 (2벌)", [P("큰기어", 0), P("T축", 5), P("T축", -5), P("큰기어", 260), P("T축", 265), P("T축", 255)]),
       st("2단블록 4 (2벌)", [P("2단블록", 0, 10), P("2단블록", 0, -10), P("2단블록", 260, 10), P("2단블록", 260, -10)])]
r = H.twin_built(bad); assert [k for k, _, _ in r] == [1, 2] and "copy_to_slot" in r[0][2], r
good = [st("큰기어 2, T축 4 (2벌)", [P("큰기어", 0), P("T축", 5), P("T축", -5)]),                       # 한 벌만 만들고(▣ 는 2배)
        st("2단블록 4 (2벌)", [P("2단블록", 0, 10), P("2단블록", 0, -10), P("큰기어", 260, copyOf="1:0")])]    # 둘째 벌은 복사 — 한 벌 안의 같은 부품 둘(y ±10)은 위반이 아니다
assert H.twin_built(good) == [], H.twin_built(good)
mirror = [st("315프레임 1, DC모터 1 (1~2번 2개 만들기)", [P("315프레임", 0), P("DC모터", 0, 0, 20), P("315프레임", 0, 0, -100), P("DC모터", 0, 0, -120, r=(180, 0, 0))]),
          st("3단블록 1", [P("3단블록", 0, 0, 30), P("3단블록", 0, 0, -130, r=(180, 0, 0))])]                 # 거울로 놓은 둘째 벌 = 평행이동이 아니다
assert H.twin_built(mirror) == [], H.twin_built(mirror)
assert H.twin_ranges(bad) == [(1, 2)] and H.twin_ranges(mirror) == [(1, 2)]
print("OK 2개 만들기 둘째 벌")
