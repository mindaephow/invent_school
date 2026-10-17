# 판 모서리 읽기가 몇 px 어긋나 holefit 가 미달할 때(눈으로 읽은 모서리 ±10px) — 모서리 8개 좌표를 한 개씩 ±step 움직여 holefit(DoG) 평균 오차가 가장 작아지는 모서리를 찾는다
# (모서리는 내가 눈으로 읽은 값이라 고쳐 읽는 것이다. holefit 의 통과 기준·방식은 그대로다 — 마지막에 holefit 를 그 모서리로 한 번 더 돌려 통과하면 fits 가 써진다.)
#   python holesearch.py <이름> <번호> <라벨> <칸> <줄> c1r1x c1r1y cNr1x cNr1y cNrMx cNrMy c1rMx c1rMy [어두운판]
import subprocess, sys, re, os
sys.stdout.reconfigure(encoding="utf-8")
a = sys.argv[1:]
name, step, label, cols, rows = a[0], a[1], a[2], a[3], a[4]
C = [float(v) for v in a[5:13]]; extra = a[13:]
here = os.path.dirname(os.path.abspath(__file__))
def run(c):
    p = subprocess.run([sys.executable, os.path.join(here, "holefit.py"), name, step, label, cols, rows] + [str(int(round(v))) for v in c] + extra, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    out = p.stdout
    m = re.findall(r"\[DoG\][^\n]*?(\d+)개 배정\((\d+)%\) \| 오차 평균 ([\d.]+)px 최대 ([\d.]+)px", out)
    ok = "통과 —" in out
    if not m: return 99.0, 0, ok
    n, pct, mean, mx = m[-1]
    return float(mean) + (0 if int(pct) >= 40 else 50), int(pct), ok
best, pct, ok = run(C); print("시작", round(best, 2), pct, ok)
for dlt in (8, 4, 2, 1):
    improved = True
    while improved and not ok:
        improved = False
        for i in range(8):
            for d in (-dlt, dlt):
                t = list(C); t[i] += d; e, p, o = run(t)
                if e < best - 0.01: best, C, pct, ok, improved = e, t, p, o, True
                if ok: break
            if ok: break
        print("  step", dlt, "→", round(best, 2), pct, [int(v) for v in C])
        if ok: break
    if ok: break
print("최종 모서리:", " ".join(str(int(round(v))) for v in C), "| 오차", round(best, 2), "통과" if ok else "미달")

if not ok:   # 한 개씩 움직여서는 안 풀릴 때: 모서리 둘씩 함께 ±3 움직여 본다
    import itertools
    for i, j in itertools.combinations(range(8), 2):
        for di, dj in ((3, 3), (3, -3), (-3, 3), (-3, -3)):
            t = list(C); t[i] += di; t[j] += dj; e, p, o = run(t)
            if e < best - 0.01: best, C, pct, ok = e, t, p, o
            if ok: break
        if ok: break
    print("쌍 탐색 후 모서리:", " ".join(str(int(round(v))) for v in C), "| 오차", round(best, 2), "통과" if ok else "미달")
