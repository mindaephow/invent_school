# 번호를 놓기 전에 "무엇이 어디에 비어 있는지"를 숫자로 읽는다(2026-10-13, 드롭체커 25·26번에서 손으로 짠 탐색 코드를 도구로).
#   조립 프로그램(<이름>.py)을 실행(파일은 쓰지 않는다 — run_name=probe)해 만들어진 모든 부품의 "지금(마지막 번호까지 반영된) 위치"로 계산한다.
#   python pegprobe.py <이름> 위돌기  [--판 x z c0 r0] [--피치 10]            위로 향한 돌기를 높이 순으로(판 칸 좌표로 환산) — 새 판·부품이 얹힐 때 받는 돌기를 찾는다
#   python pegprobe.py <이름> 빈구멍  <칸c> <칸r> [--판 x z c0 r0] [--반경 12]    그 칸 가까이 위·아래로 열린 구멍과 안에 든 돌기(사용중 부품) — 새 리벳·돌기가 꽂힐 빈 구멍을 찾는다
#   python pegprobe.py <이름> 빈돌기  <부품이름 일부>                             그 부품의 돌기 방향·위치와 이미 구멍에 들어갔는지(사용중) — 막대·브래킷이 이어 줄 빈 돌기를 찾는다
#     --판 x z c0 r0  = 판 칸 (c0,r0) 이 놓인 세계 좌표(x,z). 드롭체커 713프레임: x 5 z 5 칸 7 줄 4 (기본값). 칸 +X·줄 +Z, 간격 --피치(기본 10mm).
#   읽는 법: 높이 y 가 같은 돌기들이 한 판에 같이 꽂힌다(드롭체커 25번: y 37.5 의 6개 = 판 구멍 6곳). 구멍의 "사용중:None" 이 빈 구멍. 돌기 길이=판 구멍 길이면 판 중심 y = 돌기 중심 y.
#   함정: 이 도구는 마지막 번호까지 끝난 위치로 계산한다. 어떤 번호 시점의 위치를 보려면 그 번호 코드 앞에서 자른 사본(<이름>.py 를 해당 줄까지)을 따로 실행한다.
import sys, os, runpy
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    name, mode = a[0], a[1]; rest = a[2:]
    px, pz, c0, r0, pitch, rad = 5.0, 5.0, 7.0, 4.0, 10.0, 12.0; pos = []
    i = 0
    while i < len(rest):
        if rest[i] == "--판": px, pz, c0, r0 = [float(v) for v in rest[i + 1:i + 5]]; i += 5
        elif rest[i] == "--피치": pitch = float(rest[i + 1]); i += 2
        elif rest[i] == "--반경": rad = float(rest[i + 1]); i += 2
        else: pos.append(rest[i]); i += 1
    os.chdir(HERE); sys.path.insert(0, HERE)
    g = runpy.run_path(os.path.join(HERE, name + ".py"), run_name="probe"); A = g["A"]
    cell = lambda p: ((p[0] - px) / pitch + c0, (p[2] - pz) / pitch + r0)
    pegs = [(q, c["id"], q.world("peg", c)) for q in A.parts for c in q.conn["pegs"]]
    def pegs_in(hp, hd, hl):   # 구멍(중심 hp, 축 hd, 길이 hl) 안에 들어와 있는 돌기를 가진 부품
        for q, i, w in pegs:
            v = w["pos"] - hp; al = float(v @ hd); lat = float(np.linalg.norm(v - al * hd))
            if lat < 1.5 and abs(al) < hl / 2 + 3 and abs(float(w["dir"] @ hd)) > 0.9: return "%s %s" % (q.name, i)
        return None
    if mode == "위돌기":
        rows = []
        for q, i, w in pegs:
            if w["dir"][1] > 0.9:
                c, r = cell(w["pos"]); rows.append((round(float(w["pos"][1]), 1), q.name, i, round(c, 2), round(r, 2), round(float(w["len"]), 1)))
        rows.sort(reverse=True); print("위로 향한 돌기 %d개 (y 높은 순, 판 칸 좌표 c·r):" % len(rows))
        for r in rows[:60]: print("  y %.1f | %-12s %-4s | 칸 %.2f 줄 %.2f | 돌기길이 %.1f" % r)
    elif mode == "빈구멍":
        if len(pos) < 2: sys.exit("칸 c r 를 준다")
        tc, tr = float(pos[0]), float(pos[1]); out = []
        for q in A.parts:
            for c in q.conn["holes"]:
                w = q.world("hole", c); d = w["dir"]
                if abs(d[1]) < 0.9: continue
                cc, rr = cell(w["pos"])
                if abs(cc - tc) * pitch < rad and abs(rr - tr) * pitch < rad: out.append((round(float(w["pos"][1]), 1), q.name, c["id"], round(cc, 2), round(rr, 2), pegs_in(w["pos"], d, float(w["len"]))))
        out.sort(reverse=True); print("칸 (%g,%g) 근처 위·아래로 열린 구멍(높은 순) — 마지막 칸 = 안에 돌기가 든 부품(None 이 빈 구멍):" % (tc, tr))
        for r in out[:30]: print("  y %.1f | %-12s %-6s | 칸 %.2f 줄 %.2f | 사용중: %s" % r)
    elif mode == "빈돌기":
        if not pos: sys.exit("부품 이름 일부를 준다(예: 3단블록)")
        for q in A.parts:
            if pos[0] not in q.name: continue
            print("==", q.name, "위치", np.round(q.p, 1).tolist(), "(칸 %.2f 줄 %.2f)" % cell(q.p))
            for c in q.conn["pegs"]:
                w = q.world("peg", c); used = None
                for q2 in A.parts:
                    for h in q2.conn["holes"]:
                        hw = q2.world("hole", h)
                        if abs(float(hw["dir"] @ w["dir"])) > 0.9:
                            d = w["pos"] - hw["pos"]; al = float(d @ hw["dir"]); lat = float(np.linalg.norm(d - al * hw["dir"]))
                            if lat < 1.2 and abs(al) < hw["len"] / 2 + w["len"] / 2 + 0.5: used = q2.name
                print("   %-3s 방향 %-14s 위치 %-24s 사용중: %s" % (c["id"], np.round(w["dir"], 1).tolist(), np.round(w["pos"], 1).tolist(), used))
    else: sys.exit("모드는 위돌기·빈구멍·빈돌기")

main()
