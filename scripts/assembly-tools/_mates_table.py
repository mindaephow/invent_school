# 번호의 새 부품·옮긴 부품마다 돌기(peg)↔구멍(hole) 대응표를 뽑는다: 가까운 구멍까지 옆 거리·깊이, 짝 없는 돌기 목록 (2026-10-18 — 번호마다 돌기↔구멍을 확인하라는 사용자 지시)
#   python _mates_table.py <이름> <번호> [<번호>…]   ※ 스크립트 끝 최종 자세로 잰다(옮겨진 번호는 옮긴 뒤 자세)
import sys, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
name = sys.argv[1]; steps = [int(a) for a in sys.argv[2:]]
src = open(name + ".py", encoding="utf-8").read(); cut = src.index("# ── 부품 체크")
g = {"__name__": "x", "__file__": name + ".py"}; exec(compile(src[:cut], name + ".py", "exec"), g); A = g["A"]
def hole_world(P):
    return [(h["id"], np.array(P.hole(h["id"])["pos"], float), np.array(P.hole(h["id"])["dir"], float), h.get("len", 5)) for h in P.conn.get("holes", [])]
def peg_world(P):
    out = []
    for h in P.conn.get("pegs", []):
        w = P.world("peg", h); out.append((h["id"], np.array(w["pos"], float), np.array(w["dir"], float), h.get("len", 5)))
    return out
allp = list(A.parts)
def hidden_at_final(P):
    """P 를 마지막으로 옮긴 번호(moveMade)에서 숨겨 둔 번호의 부품 — 그 번호 화면에 없는 부품이라 같은 좌표에 있어도 결합 후보로 세지 않는다(바이킹 17번: 새 창고 판이 몸통과 같은 좌표계라 우연히 겹침)."""
    key = "%d:%d" % (P.step.index, P.step.parts.index(P)); last = None
    for i, st in enumerate(A.steps, 1):
        if key in (st.kw.get("moveMade") or {}): last = i
    if last is None: return set()
    return {int(k) for k in (A.steps[last - 1].kw.get("hideMade") or {}) if str(k).isdigit()}
for N in steps:
    print("═══ %d번 ═══" % N)
    mine = [P for P in allp if P.step.index == N]
    for P in mine:
        print(" ●", P.n, "중심", np.round(P.p, 1).tolist()); hid_ = hidden_at_final(P)
        for pid, pp, pd, pl in peg_world(P):
            best = None
            for Q in allp:
                if Q is P or Q.step.index in hid_: continue
                for hid, hp, hd, hl in hole_world(Q):
                    rel = pp - hp; along = float(rel @ hd); lat = float(np.linalg.norm(rel - along * hd))
                    if abs(float(pd @ hd)) < 0.9: continue
                    if lat < 8 and abs(along) < hl / 2 + pl + 6:
                        if best is None or lat < best[0]: best = (lat, along, Q, hid)
            if best: print("    돌기 %s → %s %s 구멍 %s : 옆 %.1fmm 깊이 %.1f %s" % (pid, best[2].n, np.round(best[2].p, 0).astype(int).tolist(), best[3], best[0], best[1], "✅" if best[0] <= 1.2 else "⚠"))
        for hid, hp, hd, hl in hole_world(P):
            best = None
            for Q in allp:
                if Q is P or Q.step.index in hid_: continue
                for pid, pp, pd, pl in peg_world(Q):
                    rel = pp - hp; along = float(rel @ hd); lat = float(np.linalg.norm(rel - along * hd))
                    if abs(float(pd @ hd)) < 0.9: continue
                    if lat < 1.5 and abs(along) < hl / 2 + pl:
                        if best is None or lat < best[0]: best = (lat, Q, pid)
            if best: print("    구멍 %s ← %s 돌기 %s : 옆 %.1fmm ✅" % (hid, best[1].n, best[2], best[0]))
