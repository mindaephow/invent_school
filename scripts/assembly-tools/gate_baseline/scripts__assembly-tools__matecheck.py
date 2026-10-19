# 화살표가 안 나올 때 원인 진단 — 안내점(marks)이 가리키는 구멍·돌기와 새 부품의 돌기가 왜 안 맞물리는지 숫자로 보여 준다 (2026-10-13 드롭체커 27번에서 만듦).
#   python matecheck.py <이름> <번호>
# 배경: 뷰어(design-assembly.js mateGuides)는 "완성(제자리) 자세에서 돌기가 구멍에 들어간 쌍"에만 화살표를 그린다. 맞물림 조건(design-mates.js check)은 세 가지다.
#   ① 방향: 돌기 방향 = 구멍 들어가는 방향(관통 구멍은 반대도 허용)  ② 축 어긋남 ≤ 1.2mm  ③ 깊이: 돌기 끝이 구멍 안으로 ≥1mm, 돌기 뿌리가 구멍 끝을 넘지 않음
# 이 도구는 번호의 marks 마다 그 자리의 구멍(또는 받는 쪽이면 돌기 끝)을 찾아, 새 부품의 모든 돌기를 위 세 조건에 대 보고 어느 조건에서 걸리는지 말한다.
# 읽은 좌표는 스크립트 마지막(모든 이동이 끝난 뒤) 위치다 — 그 번호 시점과 다를 수 있는 번호(옮겨 붙는 부품)는 참고만 한다.
import os, runpy, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
name, k = sys.argv[1], int(sys.argv[2])
g = runpy.run_path(name + ".py", run_name="probe")   # __main__ 으로 돌리면 <이름>_asm.json 을 덮어쓴다
A = next(v for v in g.values() if hasattr(v, "steps") and hasattr(v, "parts") and hasattr(v, "meta"))
rnd = lambda v: [round(float(x), 1) for x in v]

def test(pg, h):
    """돌기 pg 가 구멍 h 에 들어가는가 — (맞물림 여부, 걸린 이유 목록, along, lateral)"""
    al = float(np.dot(pg["dir"], h["dir"])); why = []
    if not (al > 0.98 or (h.get("through") and al < -0.98)): why.append("방향 불일치(aligned %.2f)" % al)
    ax = np.array(h["dir"]) if al > 0 else -np.array(h["dir"])
    rel = pg["pos"] - h["pos"]; a = float(np.dot(rel, ax)); lat = float(np.linalg.norm(rel - ax * a))
    half = h["len"] / 2; tip = a + pg["len"] / 2; base = a - pg["len"] / 2
    if lat > 1.2: why.append("축 어긋남 %.1fmm > 1.2" % lat)
    if tip < -half + 1.0: why.append("돌기 끝이 구멍에 안 들어감(깊이 %.1f — 이만큼 더 가야 한다)" % (tip - (-half + 1.0)))
    if base > half - 0.5 + 1.0: why.append("돌기 뿌리가 구멍 밖(%.1fmm 떨어짐)" % (base - (half + 0.5)))
    return (not why), why, a, lat

parts = [q for q in A.parts if q.step.index == k]
if not parts: sys.exit("❌ %s %d번에 부품이 없다" % (name, k))
print("═══ %s %d번 안내점 맞물림 진단 ═══" % (name, k))
n_bad = 0
for q in parts:
    marks = q.extra.get("marks") or []
    if not marks or q.extra.get("noGuide") or q.extra.get("seated"): continue
    recv = bool(q.extra.get("recv")) or getattr(q, "recv", False)
    for m in marks:
        m = np.array(m, float); found = False
        for o in A.parts:
            if o is q or o.step.index > k or not o.conn: continue
            if recv:   # 구멍을 받는 부품: 안내점은 고정된 돌기 끝 — 그 돌기가 q 의 구멍에 들어가는지
                for c in o.conn["pegs"]:
                    pg = o.world("peg", c)
                    if np.linalg.norm(pg["pos"] + pg["dir"] * pg["len"] / 2 - m) > 3: continue
                    found = True
                    best = min(((test(pg, q.world("hole", hc)), hc["id"]) for hc in q.conn["holes"]), key=lambda t: t[0][3])
                    (ok, why, a, lat), hid = best
                    print("  %s%s 안내점 %s ← %s %s 돌기 ↔ 이 부품 %s 구멍: %s" % (q.n, "", rnd(m), o.n, c["id"], hid, "✅ 맞물림" if ok else "❌ " + "; ".join(why))); n_bad += (not ok)
            else:      # 돌기를 끼우는 부품: 안내점은 받는 구멍 — q 의 돌기 중 그 구멍에 가장 가까운 것
                for hc in o.conn["holes"]:
                    h = o.world("hole", hc); rel = m - h["pos"]; al = float(np.dot(rel, h["dir"]))
                    if np.linalg.norm(rel - np.array(h["dir"]) * al) > 1.8 or abs(al) > h["len"] / 2 + 3: continue
                    found = True
                    res = sorted(((test(q.world("peg", pc), h), pc["id"]) for pc in q.conn["pegs"]), key=lambda t: t[0][3])[:3]
                    for (ok, why, a, lat), pid in res:
                        print("  %s 안내점 %s → %s %s 구멍 ↔ 이 부품 돌기 %s: %s (깊이 %.1f, 축 어긋남 %.1f)" % (q.n, rnd(m), o.n, hc["id"], pid, "✅ 맞물림" if ok else "❌ " + "; ".join(why), a, lat))
                    n_bad += (not res[0][0][0])
        if not found: print("  %s 안내점 %s: 그 자리에 받는 구멍(또는 돌기 끝)이 없음 — 안내점 좌표부터 틀림" % (q.n, rnd(m))); n_bad += 1
print("\n결과: 맞물리지 않는 안내점 %d개 %s" % (n_bad, "→ 제자리 p 를 돌기-구멍 거리 0.0 으로 맞추고, 떨어진 모습은 dir·hover 로 만든다(05_조립.md 예시)" if n_bad else "— 화살표가 나와야 한다"))
