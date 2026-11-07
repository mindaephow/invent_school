# 화면이 그리는 안내 화살표·점의 끝 좌표 점검 — 뷰어(design-assembly.js 536~575줄)의 공식을 그대로 써서 화살표 꼬리·끝이 부품 끝·구멍에 닿는지 숫자로 본다. 읽기만 한다.
#   python guidecheck.py <이름> [번호…]        위반이 있으면 종료코드 1
# 왜 만들었나(2026-11-07 풍차 9번, 사용자 지적): matecheck 는 안내점(marks)이 제자리 구멍에 있는지만 본다. 화면은 거기에 hover·joinOrder 를 더해 화살표 시작·끝을 정하는데
#   그 위치는 아무 도구도 재지 않아, 판의 화살표가 떠 있는 리벳이 아니라 제자리 구멍에서 시작해 리벳 위로 겹쳐 지나가도 "0건" 이었다. 수치는 _asm.json 과 부품 연결점에 다 있다.
# 뷰어 공식(비움직임·비합치기 부품, 새로 놓이는 부품만):
#   hv = hover 또는 (recv 20 / 아니면 22) · depth = pegDepth 또는 5 · 호스트 = 같은 번호의 더 먼저(joinOrder 작음) 끼우는 부품 중 안내점 근처(축 14·옆 4 이내)
#   끼우는 쪽(recv 아님):  꼬리 = m + dir×(hv−depth) → 끝 = m (호스트가 먼저 떠 있으면 m + 호스트 띄움)
#   받는 쪽(recv):         꼬리 = m + 호스트 띄움(호스트 없으면 m) → 끝 = m + dir×hv
# 점검 ① 끼우는 쪽 꼬리가 떠 있는 자기 돌기의 앞서 들어가는 끝에서 3mm 안(긴 축은 안내점이 가운데면 pegDepth = 길이/2 를 준다, G21)  ② 끼우는 쪽 끝이 받는 구멍 축 위(옆 1.5mm, 구멍 길이 안)
#         ③ 받는 쪽 꼬리가 호스트의 떠 있는 위쪽 돌기 끝에서 3mm 안 — 호스트가 있는데 못 찾으면 joinOrder 가 같거나 작아서다(G12)
#         ④ 받는 쪽 끝이 자기 떠 있는 구멍 축 위
# 점검 ⑤ 결합 전 모양(G1): 리벳·T축·부시·볼트·너트가 seated 이거나 dir·marks 가 없으면 위반(noGuide 는 점검 안 됨으로 보고)
# 점검 ⑥ 안내점 자리: marks·settleMarks 가 받는 구멍 축 / 고정된 돌기 끝에서 1.5mm 안(합치는 번호의 settleMarks 는 settle 번호에서 본다)
# 못 보는 것(점검 안 됨으로 따로 보고한다): 합치는 번호(옆자리 settleDir·moveMade), noGuide·seated, dir·marks 없는 부품.
import asmpath  # 조립도 파일 자리 연결
import os, runpy, sys
import numpy as np
from asmlib import euler_to_R
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
FASTENERS = ("리벳", "T축", "부시", "볼트", "너트")
HOVER, HOVER_RECV, DEPTH = 22.0, 20.0, 5.0   # design-assembly.js 상수 — 바뀌면 같이 바꾼다

def unit(v): v = np.array(v, float); return v / (np.linalg.norm(v) or 1.0)

def receives_by_hole(q, m, u, hv, thick=None):
    """안내점 m 이 그 부품 '자기 구멍 중심'에 링으로 붙는가(= 구멍으로 받는 부품, recv 표시 필요). 뷰어 공식: 링 = m + 방향×띄움 − 방향×두께/2 가 띄운 구멍 중심."""
    ring = np.array(m, float) + u * hv - u * float(thick or q.extra.get("thick") or 5) / 2
    return any(float(np.linalg.norm(np.array(q.world("hole", c)["pos"]) + u * hv - ring)) <= 1.5 for c in q.conn["holes"])

def tail_on_own_peg(q, m, u, hv, dep):
    """안내점 m 에서 시작하는 돌기 쪽 화살표 꼬리가 그 부품 자기 돌기 끝에 닿는가(= 돌기로 꽂는 부품, recv 불필요)."""
    frm = np.array(m, float) + u * (hv - dep)
    tips = [np.array(w["pos"]) + u * hv - u * w["len"] / 2 for w in (q.world("peg", c) for c in q.conn["pegs"]) if abs(float(np.dot(w["dir"], u))) > 0.9]
    return any(float(np.linalg.norm(frm - t)) <= 3 for t in tips)

def run(name, only=None):
    g = runpy.run_path(name + ".py", run_name="probe")
    A = next(v for v in g.values() if hasattr(v, "steps") and hasattr(v, "parts") and hasattr(v, "meta"))
    import stepchecks
    bad, skipped, n = [], [], 0
    for k in range(1, len(A.steps) + 1):
        if only and k not in only: continue
        for q in A.parts:
            if q.step.index <= k: q.p, q.R = stepchecks.pose_at(A, q, k)
        new = [q for q in A.parts if q.step.index == k and q.conn]
        for q in A.parts:   # 뷰어가 그리는 자세로: 옆자리 묶음은 side 자세(placed~until 직전), 이 번호에서만 다른 자세(poseAt)가 있으면 그 자세
            sd = q.extra.get('side'); pa = (q.extra.get('poseAt') or {}).get(str(k))
            if pa and q.step.index <= k: q.p, q.R = np.array(pa['p'], float), euler_to_R(pa['r'])
            elif sd and q.step.index <= k < sd['until']: q.p, q.R = np.array(sd['p'], float), euler_to_R(sd['r'])
        for key_, e_ in (A.steps[k - 1].kw.get("moveMade") or {}).items():   # 옮기는 번호: 안내점이 있는 부품은 화면 공식대로 링이 "움직이는 부품 자기 구멍"에 있어야 한다(G23)
            if not e_.get("marks"): continue
            s_, i_ = map(int, key_.split(":")); q = A.steps[s_ - 1].parts[i_]; u = unit(e_["dir"]); hv = float(e_.get("hover") or HOVER); n += len(e_["marks"])
            for m in e_["marks"]:
                m = np.array(m, float)
                if e_.get("recv"): ring = m + u * hv - u * float(q.extra.get("thick") or 5) / 2   # 뷰어: 받는 쪽 링 = 화살표 끝 − 방향×두께/2
                else: ring = m                                                                  # 뷰어: 돌기 쪽 링은 고정된 구멍 입구(m)
                own = min(float(np.linalg.norm(np.array(q.world("hole", c)["pos"]) + u * hv - ring)) for c in q.conn["holes"]) if e_.get("recv") else 0.0
                if e_.get("recv") and own > 1.5: bad.append((k, "%s(옮김) 링 %s 가 자기 구멍 중심에서 %.1fmm 떨어짐(≤1.5)" % (q.n, np.round(ring, 1).tolist(), own)))
                if not e_.get("recv") and receives_by_hole(q, m, u, hv) and not tail_on_own_peg(q, m, u, hv, float(q.extra.get("pegDepth") or DEPTH)): bad.append((k, "%s(옮김) 구멍으로 받는 부품(안내점이 자기 구멍 중심)인데 recv 표시가 없어 링이 고정된 돌기 끝 %s 에 찍힌다(G23a)" % (q.n, np.round(m, 1).tolist())))
        for q in A.parts:   # 안내점 자리(⑥): marks·settleMarks 가 받는 구멍 축(끼우는 쪽) 또는 고정된 돌기 끝(받는 쪽, recv)에서 1.5mm 안인지
            e2 = q.extra; sets = []
            if q.step.index == k and e2.get("marks") and not e2.get("noGuide") and not e2.get("seated"): sets.append(e2["marks"])
            if (e2.get("side") or {}).get("until") == k and e2.get("settleMarks"): sets.append(e2["settleMarks"])
            for ms in sets:
                for m in ms:
                    m = np.array(m, float); best = 1e9
                    for o in A.parts:
                        if o is q or o.step.index > k or not o.conn: continue
                        if e2.get("recv"):
                            for c in o.conn["pegs"]:
                                w = o.world("peg", c)
                                best = min([best] + [float(np.linalg.norm(m - (np.array(w["pos"]) + np.array(w["dir"]) * w["len"] / 2 * sg))) for sg in (1, -1, 0)])
                        else:
                            for c in o.conn["holes"]:
                                w = o.world("hole", c); uu = unit(w["dir"]); r = m - np.array(w["pos"]); al = float(r @ uu)
                                if abs(al) <= (w.get("len") or 10) / 2 + 3: best = min(best, float(np.linalg.norm(r - uu * al)))
                    n += 1
                    if best > 1.5: bad.append((k, "%s 안내점 %s 가 %s에서 %s떨어져 있다(≤1.5) — 안내점이 자기 자리가 아니다" % (q.n, np.round(m, 1).tolist(), "고정된 돌기 끝" if e2.get("recv") else "받는 구멍 축", ("%.1fmm " % best) if best < 1e8 else "(받는 쪽 없음) ")))
        for q in new:   # 결합 전 모양(G1): 리벳·T축·부시·볼트·너트는 항상 띄워서 화살표로 — seated·방향 없음·안내점 없음이면 위반, noGuide 는 확인 필요
            if q.n in FASTENERS:
                e_ = q.extra
                if e_.get("seated"): bad.append((k, "%s: seated(꽂힌 채)로 그려졌다 — 책이 꽂은 모양이어도 결합 전(띄워서 화살표)으로 만든다(G1)" % q.n))
                elif e_.get("noGuide"): skipped.append((k, "%s: noGuide(안내 없음) — 결합 전 모양인지 화면에서 본다" % q.n))
                elif (not e_.get("dir") and e_.get("settleDir") is None) or not (e_.get("marks") or e_.get("settleMarks")): bad.append((k, "%s: 띄우는 방향(dir)이나 안내점(marks)이 없어 결합 전 모습으로 안 그려진다(G1)" % q.n))
        def info(h):   # 이 번호에서 h 가 그려지는 방식 → (방향, 띄움, 순서, recv, 안내점, 종류) | None  (뷰어 isNew·settling 분기와 같다)
            e = h.extra; side = e.get("side") or {}
            if side.get("until") == k:   # 옆자리에서 이 번호에 합쳐지는 부품: settleDir(없으면 dir)·settleHover·settleMarks·settleOrder
                d = e.get("settleDir") if e.get("settleDir") is not None else e.get("dir")
                if d is None: return None
                return unit(d), float(e.get("settleHover") or HOVER), e.get("settleOrder") or 1, bool(e.get("recv")), e.get("settleMarks") or [], "합치기"
            if h.step.index == k and (not side or k < side.get('until', 0)):   # 옆자리에서 처음 놓이는 번호도 보통 방식(hover·dir·marks)으로 그려진다
                if not e.get("dir"): return None
                rv = bool(e.get("recv")); return unit(e["dir"]), float(e.get("hover") or (HOVER_RECV if rv else HOVER)), e.get("joinOrder") or 1, rv, e.get("marks") or [], "보통"
            return None
        cand = [(h, info(h)) for h in A.parts if h.conn]; cand = [(h, i_) for h, i_ in cand if i_]
        for q, (u, hv, order, recv, m_, kind) in cand:
            ex = q.extra
            if not m_ or ex.get("noGuide") or ex.get("seated"): continue
            dep = float(ex.get("pegDepth") or DEPTH)
            def host_shift(m):
                for h, (hu, hhv, hord, _r, _m, _k) in cand:
                    if h is q or hord >= order: continue
                    d = np.array(h.p, float) - m; al = float(d @ u)
                    if abs(al) < 14 and np.linalg.norm(d - u * al) < 4: return hu * hhv, h
                return None, None
            fm_ = ex.get('faceMarks') or []
            for i_, m in enumerate(m_):
                m = np.array(m, float); n += 1
                sh, host = host_shift(m)
                if not recv:
                    frm = m + u * (hv - dep); to = m + (sh if sh is not None else 0)
                    tips = [np.array(w["pos"]) + u * hv - u * w["len"] / 2 for w in (q.world("peg", c) for c in q.conn["pegs"]) if abs(float(np.dot(w["dir"], u))) > 0.9]   # 끼울 때 앞서 들어가는 끝 = 돌기 중심 − 띄움방향×길이/2 (리벳 p1·긴 축 모두)
                    dist = [(float(abs((frm - t) @ u)), float(np.linalg.norm((frm - t) - u * ((frm - t) @ u)))) for t in tips]
                    if (not tips or min(a + b for a, b in dist) > 3) and receives_by_hole(q, m, u, hv): bad.append((k, "%s 구멍으로 받는 부품(안내점이 자기 구멍 중심)인데 recv 표시가 없다(G23a)" % q.n))
                    if not tips or min(a + b for a, b in dist) > 3: bad.append((k, "%s 화살표 꼬리 %s 가 떠 있는 돌기 끝에서 %s 떨어짐(≤3, %s)" % (q.n, np.round(frm, 1).tolist(), ("%.1fmm" % min(a + b for a, b in dist)) if tips else "받는 쪽을 향한 돌기 없음", kind)))
                    if sh is None:
                        ok = False
                        for o in A.parts:
                            if o is q or o.step.index > k or not o.conn: continue
                            for hc in o.conn["holes"]:
                                h = o.world("hole", hc); r = to - np.array(h["pos"]); al = float(r @ unit(h["dir"]))
                                if np.linalg.norm(r - unit(h["dir"]) * al) <= 1.5 and abs(al) <= (h.get("len") or 10) / 2 + 3: ok = True
                        if not ok: bad.append((k, "%s 화살표 끝 %s 가 받는 구멍 축 위에 없음(%s)" % (q.n, np.round(to, 1).tolist(), kind)))
                else:
                    frm = m + (sh if sh is not None else 0); to = (np.array(fm_[i_], float) if i_ < len(fm_) else m) + u * hv   # 화면: 받는 부품 화살표 끝 = faceMarks(있으면) + 방향×띄움
                    if sh is not None:
                        tips = [np.array(w["pos"]) + sh + np.array(w["dir"]) * w["len"] / 2 for w in (host.world("peg", c) for c in host.conn["pegs"]) if float(np.dot(w["dir"], u)) > 0.9]
                        if not tips or min(float(np.linalg.norm(frm - t)) for t in tips) > 3: bad.append((k, "%s 화살표 꼬리 %s 가 호스트(%s)의 떠 있는 위쪽 돌기 끝에서 3mm 넘게 떨어짐(%s)" % (q.n, np.round(frm, 1).tolist(), host.n, kind)))
                    else:
                        floating = [h for h, (hu, hhv, hord, hr, _m, _k) in cand if h is not q and not hr and h.conn and any(min(float(np.linalg.norm(np.array(w["pos"]) + np.array(w["dir"]) * w["len"] / 2 * sg - m)) for sg in (1, -1)) < 3 for w in (h.world("peg", c) for c in h.conn["pegs"]))]
                        if floating: bad.append((k, "%s 안에 떠 있는 %s 가 있는데 순서(%s)가 그보다 크지 않아 화살표가 리벳 끝이 아니라 제자리 끝 %s 에서 시작한다(G12, %s)" % (q.n, floating[0].n, order, np.round(m, 1).tolist(), kind)))
                    ok = False
                    for hc in q.conn["holes"]:
                        h = q.world("hole", hc); r = to - (np.array(h["pos"]) + u * hv); al = float(r @ unit(h["dir"]))
                        if np.linalg.norm(r - unit(h["dir"]) * al) <= 1.5 and abs(al) <= (h.get("len") or 10) / 2 + 3: ok = True
                    if not ok: bad.append((k, "%s 화살표 끝 %s 가 떠 있는 자기 구멍 축 위에 없음(%s)" % (q.n, np.round(to, 1).tolist(), kind)))
    return bad, n, skipped

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    bad, n, skipped = run(a[0], {int(x) for x in a[1:]} or None)
    print("%s: 안내 화살표 %d개 점검, 위반 %d곳" % (a[0], n, len(bad)))
    for k, m in bad: print("   ❌ %d번 %s" % (k, m))
    if skipped: print("   ⚠ 점검 안 됨: " + ", ".join("%d번(%s)" % t for t in sorted(set(skipped))[:12]))
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
