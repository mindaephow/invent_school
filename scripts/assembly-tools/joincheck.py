# 결합부 틈·겹침 점검(사용자 기본 규칙 2026-10-24): 리벳으로 프레임과 프레임을 이으면 두 프레임은 딱 붙는다(틈 0), 어느 부품도 서로 겹치지 않는다.
#   python joincheck.py <이름> [번호 …]      번호를 안 주면 전부
#   ⓪ 볼트·너트: 가장 큰 부분(머리·너트 몸)이 프레임 구멍 안에 묻혀 프레임 면 밖으로 안 나옴(기본 규칙)
#   ① 리벳 틈: stepchecks.rivet_gaps (build.py 의 '리벳 결합 프레임이 딱 붙음' 점검과 같은 계산) — 틈 0.3 넘게 떠 있거나 1.0 넘게 겹침
#   ② 돌기 충돌: 그 번호 자세(k번까지 옮긴 자세)에서 돌기 끝이 구멍 없는 부품 안에 박히거나 한 구멍에 돌기가 둘 들어간 것(합치는 번호에서 몸통↔조립이 파고드는 것을 잡는다).
#      브라켓(L 자)·상자가 크게 속이 빈 부품은 상자로 못 재서 뺀다. 숨긴(hideMade) 앞 번호는 뺀다.
import sys, os, runpy, itertools
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import stepchecks
from asmlib import euler_to_R, _mate

def overlaps(A, k):
    """k번 자세에서 돌기가 구멍 없는 곳을 뚫거나 한 구멍에 돌기가 둘 들어간 곳을 찾는다(상자 겹침은 돌기 부분이 섞여 오탐이 많아서 돌기 단위로 본다)."""
    dims = stepchecks._dims(); hide = A.steps[k - 1].kw.get("hideMade") or {}
    def pose(q):
        key = "%d:%d" % (q.step.index, q.step.parts.index(q))
        for j in range(k, 0, -1):
            e = (A.steps[j - 1].kw.get("moveMade") or {}).get(key)
            if e: return np.array(e["p"], float), np.array(euler_to_R(e["r"]), float)
        return stepchecks._pose(q, k)
    parts = []
    for k2, st in enumerate(A.steps, 1):
        if k2 > k or str(k2) in hide: continue
        for q in st.parts:
            if q.n in dims and "copyOf" not in q.extra:
                p, R = pose(q); d = np.array(dims[q.n]) / 2
                lo_l, hi_l = -d.copy(), d.copy()   # 몸통 상자: 치수에는 돌기 길이가 들어 있어서 돌기가 나온 쪽 면을 돌기 길이만큼 안으로 줄인다
                for c in q.conn["pegs"]:
                    dl = np.array(c["dir"], float); ax = int(np.argmax(np.abs(dl)))
                    if abs(dl[ax]) > 0.9:
                        if dl[ax] > 0: hi_l[ax] = min(hi_l[ax], max(c["pos"][ax] - c.get("len", 5) / 2, 0.0) if c["pos"][ax] - c.get("len", 5) / 2 > -1e9 else hi_l[ax])
                        else: lo_l[ax] = max(lo_l[ax], min(c["pos"][ax] + c.get("len", 5) / 2, 0.0))
                cl = (lo_l + hi_l) / 2; hl = (hi_l - lo_l) / 2
                c_w = p + R @ cl; e = np.abs(R) @ hl
                p_box = c_w
                pegs = [dict(id=c["id"], pos=p + R @ np.array(c["pos"], float), dir=R @ np.array(c["dir"], float), len=c.get("len", 5)) for c in q.conn["pegs"]]
                holes = [dict(id=c["id"], pos=p + R @ np.array(c["pos"], float), dir=R @ np.array(c["dir"], float), len=c.get("len", 5), through=c.get("through", False)) for c in q.conn["holes"]]
                parts.append(dict(q=q, lo=p_box - e, hi=p_box + e, pegs=pegs, holes=holes))
    out = []
    occupied = {}
    for a in parts:
        for g in a["pegs"]:
            tip = g["pos"] + g["dir"] * g["len"] * 0.45
            for b in parts:
                if b is a: continue
                if np.all(tip >= b["lo"] - 0.01) and np.all(tip <= b["hi"] + 0.01):
                    hs = [h for h in b["holes"] if _mate(g, h)]
                    if not hs and "브라켓" not in b["q"].n: out.append("%s.%s 끝이 %s 안에 구멍 없이 박힘" % (a["q"].name, g["id"], b["q"].name))
                    for h in hs: occupied.setdefault((b["q"].name, h["id"]), []).append((a["q"].name, g["id"], g["dir"], h["through"]))
    for key, lst in occupied.items():
        for (n1, i1, d1, t1), (n2, i2, d2, t2) in itertools.combinations(lst, 2):
            if n1 == n2: continue
            if np.dot(d1, d2) > 0.5 or not t1: out.append("%s 구멍 %s 에 돌기 둘: %s.%s·%s.%s" % (key[0], key[1], n1, i1, n2, i2))
    return sorted(set(out))

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    name = sys.argv[1]; A = runpy.run_path(name + ".py", run_name="probe")["A"]
    ks = [int(v) for v in sys.argv[2:]] or [i for i, st in enumerate(A.steps, 1) if st.parts or st.kw.get("moveMade")]
    bad = 0
    for k in ks:
        g = stepchecks.rivet_gaps(A, k)
        for x in g: print("❌ %d번 리벳 틈: %s (%s↔%s) %.1fmm" % ((k,) + x)); bad += 1
        for x in stepchecks.fastener_protrusion(A, k): print("❌ %d번 볼트·너트가 프레임 면 밖으로 나옴: %s (%s) %.1fmm" % ((k,) + x)); bad += 1
        if A.steps[k - 1].kw.get("moveMade"):   # 합치는·옮기는 번호만 겹침을 본다(그 밖의 번호는 끼운 돌기 상자 겹침이 많아 모델 점검(build)이 본다)
            for m in overlaps(A, k): print("⚠ %d번 %s" % (k, m)); bad += 1
    print("결합부 점검: %s" % ("문제 없음" if not bad else "%d건 — 위 목록을 고친다(리벳 결합 프레임은 딱 붙게, 겹친 부품은 책에서 위치를 다시 읽는다)" % bad))
if __name__ == "__main__": main()
