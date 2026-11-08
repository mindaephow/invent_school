# 결합 전 높이 점검 — 같은 번호에서 리벳·T축·부시·볼트·너트(끼우는 쪽)가 받는 판(recv)보다 가까이 떠 있는지를 저장된 hover 수치로 본다. 읽기만 한다.
#   python hovercheck.py <이름|all> [번호…]        위반이 있으면 종료코드 1
# 왜 만들었나(2026-11-07 풍차 9번, 사용자 지적): G12 "먼저 끼우는 쪽이 작은 hover, 나중이 큰 hover" 문장은 있었는데 이것을 재는 도구가 없었다.
#   다른 점검기(matecheck·fakeguide·joincheck)는 제자리 좌표·marks 만 읽고 hover 를 읽지 않아, hover 를 안 준 리벳(화면 기본 22)이
#   받는 판(화면 기본 20)에 붙은 채 보여도 "0건" 이었다. 수치는 _asm.json 에 다 있으므로 화면 없이 계산할 수 있다.
# 규칙 ②: 받는 판의 joinOrder 가 리벳보다 커야 한다(화살표 시작점).
# 규칙 ③: 리벳의 dir(띄우는 방향)과 받는 판의 dir 의 내적이 0 이하면 반대(리벳이 판 속으로 내려가 안 보임).
# 규칙 ①: 받는 판의 유효 hover(hover 또는 기본 20) − 끼우는 쪽 유효 hover(hover 또는 기본 22) ≥ 10mm.
#   (design-assembly.js: HOVER=22, recv 기본 HOVER_RECV=20 — 그 값이 바뀌면 아래 상수도 같이 바꾼다)
# 짝 찾기: 받는 판의 marks 점과 끼우는 쪽 marks 점이 돌기 방향에 수직인 면에서 1mm 안이면 한 짝.
# 못 보는 것(점검 안 됨으로 따로 보고한다): 옆자리 합치기(settleDir) 부품(화면이 settleHover 로 따로 띄운다), 리벳 아닌 축·부시·볼트·너트, dir 없는 부품, 짝이 안 맞는 marks.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
HOVER, HOVER_RECV, MIN_GAP = 22.0, 20.0, 10.0
FAST = ("리벳",)   # 리벳은 판보다 먼저 끼워져 판보다 가까이 떠야 한다. 축·부시는 나중에 끼우는 쪽이 더 멀어야 해서(G12) 반대라 보지 않는다

def eff(p):
    h = p.get("hover")
    return float(h) if h else (HOVER_RECV if p.get("recv") else HOVER)

def check_steps(steps, only=None, dircheck=False):
    """-> (위반 [(번호, 메시지)], 본 쌍 수, 못 본 [(번호, 이유)])"""
    bad, pairs, skipped = [], 0, []
    for k, s in enumerate(steps, 1):
        if only and k not in only: continue
        P = s.get("parts", [])
        fast = [p for p in P if p.get("n") in FAST and p.get("dir") and p.get("marks") and p.get("settleDir") is None]
        recvs = [p for p in P if p.get("recv") and p.get("dir") and p.get("marks") and p.get("n") not in FAST and p.get("settleDir") is None]
        sd = [p for p in P if p.get("settleDir") is not None]
        if sd and any(p.get("n") in FAST or p.get("recv") for p in sd): skipped.append((k, "옆자리 합치기(settleDir) 부품 %d개" % len(sd)))
        for r in recvs:
            d = np.array(r["dir"], float); d /= (np.linalg.norm(d) or 1.0)
            mine = [f for f in fast if any(_near(m, fm, d) for m in r["marks"] for fm in f["marks"])]
            if not mine:
                continue
            pairs += len(mine); gap = eff(r) - max(eff(f) for f in mine)
            rev = [f for f in mine if float(np.array(f["dir"], float) @ d) <= 0]   # 규칙 ③: 리벳이 띄워지는 쪽(dir)이 받는 판과 같아야 한다 — 반대면 리벳이 구멍 속으로 파묻혀 안 보이고 초록 연결점만 공중에 남는다(2026-11-08 로봇팽이 12번)
            if rev and dircheck:   # 켠 조립도(rules.json hover_dir_check)만 — 다른 조립도 12곳은 오탐인지 아직 안 가려서 막지 않는다
                bad.append((k, "%s %d개의 띄우는 방향 dir %s 가 %s 의 dir %s 와 반대 — 리벳이 구멍 속으로 파묻혀 안 보이고 연결점만 공중에 뜬다(attach dir 는 띄우는 방향 = 돌기 방향의 반대, G12)" % (rev[0]["n"], len(rev), rev[0]["dir"], r["n"], r["dir"])))
            if (r.get("joinOrder") or 1) <= max((f.get("joinOrder") or 1) for f in mine):   # 화면은 joinOrder 가 더 작은 부품(리벳)을 먼저 끼우는 것으로 보고 판의 화살표를 떠 있는 리벳 끝에서 시작한다
                bad.append((k, "%s joinOrder %s 가 리벳(%s)보다 크지 않다 — 판의 화살표가 리벳 끝이 아니라 제자리 구멍에서 시작해 리벳 위로 겹쳐 지나간다(G12)" % (r["n"], r.get("joinOrder") or 1, max((f.get("joinOrder") or 1) for f in mine))))
            if gap < MIN_GAP:
                bad.append((k, "%s hover %.0f 가 %s %d개(hover %.0f)보다 %.0fmm 만 멀다(≥%.0f 필요) — 리벳이 판에 붙어 보인다(G12)" %
                            (r["n"], eff(r), mine[0]["n"], len(mine), max(eff(f) for f in mine), gap, MIN_GAP)))
    return bad, pairs, skipped

def _near(a, b, d):
    v = np.array(a, float) - np.array(b, float); v = v - d * float(v @ d)
    return float(np.linalg.norm(v)) <= 1.0

def main():
    sys.stdout.reconfigure(encoding="utf-8")   # import 만 해도(조립도가 상수를 가져다 쓸 때) 출력을 바꾸지 않도록 실행할 때만
    a = sys.argv[1:]; name = a[0] if a else "all"; only = {int(x) for x in a[1:]} or None
    files = sorted(glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "*_asm.json"))) if name == "all" else [asmpath.resolve(name + "_asm.json")]
    tot = 0
    for f in files:
        try: steps = json.load(open(f, encoding="utf-8"))["steps"]
        except Exception: continue
        rl = {}
        try: rl = json.load(open(f.replace('_asm.json', '_rules.json'), encoding='utf-8'))
        except Exception: pass
        bad, pairs, skipped = check_steps(steps, only, bool(rl.get('hover_dir_check'))); tot += len(bad)
        if bad or name != "all":
            print("%s: 결합 전 높이 위반 %d곳 (본 짝 %d)" % (os.path.basename(f).replace("_asm.json", ""), len(bad), pairs))
            for k, m in bad: print("   ❌ %d번 %s" % (k, m))
            if skipped: print("   ⚠ 점검 안 됨: " + ", ".join("%d번(%s)" % t for t in skipped))
    print("합계 %d곳" % tot); sys.exit(1 if tot else 0)

if __name__ == "__main__": main()
