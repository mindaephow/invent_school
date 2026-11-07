# 창고정리 점검 — 새 창고에서 만드는 번호인데 다른 창고의 앞 번호 부품이 숨겨지지 않은(hideMade 에 없는) 곳을 찾는다. 읽기만 한다.
#   python hidecheck.py <이름|all>
# 왜 만들었나(2026-11-07 풍차 16·17·20번): 13~22번의 hideMade 가 모두 "1~12번" 복사본이라 새 창고(날개 모듈·축 기어)를 만드는 번호에 앞 창고의 허브가 같이 보였다.
#   A3a 는 번호마다 작업장(화면)을 책과 비교해 책에 없는 앞 번호 부품이 보이면 바로 hideMade 를 고치라고 하지만 도구는 slot·history 유무만 봤다.
# 판정(참고용 — 책 그림이 최종): 번호 k 가 부품을 새로 놓고(합치기만 하는 번호 제외) slot 이 앞 번호 slot 과 다를 때, 앞 번호 중 slot 이 k 와 다른 번호가 hideMade 에 없으면 보고한다.
# 둘째 판정(2026-11-08 풍차 18번 — 날개가 4개 보인 사고): 부품마다 지금 있는 창고를 계산한다 = 만든 번호의 창고, 합쳐지는 번호(side.until)가 지났으면 그 번호의 창고, 옮겼으면(moveMade) 옮긴 번호의 창고.
#   번호 k 의 창고가 아닌 곳에 있는 부품이 hideMade 에 없으면(그 번호 화면에 같이 보이면) 보고한다. 같은 slot 이어도 아직 다른 창고에서 기다리는 부품(18번 때 19번에 쓸 모듈)을 잡는다. 책 그림이 최종이다.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))

def stray_prev(steps):
    """첫 판정 -> [(번호, [앞 번호들])]"""
    bad = []
    for k, s in enumerate(steps, 1):
        if k < 2 or not s.get("parts") or s.get("madeNoPart"): continue
        sl = str(s.get("slot", 1)); prev = str(steps[k - 2].get("slot", 1))
        if sl == prev: continue
        hide = s.get("hideMade") or {}
        vis = [j for j in range(1, k) if str(steps[j - 1].get("slot", 1)) != sl and steps[j - 1].get("parts") and str(j) not in hide]
        if vis: bad.append((k, vis))
    return bad

def stray_loc(steps):
    """둘째 판정(부품별 현재 창고) -> [(번호, 만든 번호, [부품 순서들])] — 화면 붉은 표시(violations.py 'store')도 이것을 쓴다"""
    slot_of = lambda n: str(steps[n - 1].get("slot", 1)); out = []
    for k, s in enumerate(steps, 1):
        sl = slot_of(k); hide = s.get("hideMade") or {}; seen = {}
        for m in range(1, k + 1):
            for pi, p in enumerate(steps[m - 1].get("parts") or []):
                if p.get("finalOnly") or p.get("copyOf") or (p.get("hideAt") and k in p["hideAt"]): continue
                u = (p.get("side") or {}).get("until"); at = u if (u and k >= u) else m
                for j in range(m + 1, k + 1):
                    if ((steps[j - 1].get("moveMade") or {}).get("%d:%d" % (m, pi))): at = j
                # 받침(목적지): 같은 번호 m 의 부품 일부가 이미 옮겨져 왔다면(양팔저울 23번: 22번의 오른쪽 판·리벳은 옮겨지고 왼쪽 판·리벳은 그 자리) 옮겨지지 않고 남은 부품은 그 위에 합쳐지는 받침이라 그 번호 화면에 보이는 것이 맞다 — 창고 2 에 있어도 오탐하지 않는다(사용자 지시 2026-11-08)
                if at == m and any(((steps[j - 1].get("moveMade") or {}).get("%d:%d" % (m, pj))) for j in range(m + 1, k + 1) for pj in range(len(steps[m - 1].get("parts") or [])) if pj != pi): continue
                if slot_of(at) != sl and str(m) not in hide and ("%d:%d" % (m, pi)) not in hide: seen.setdefault(m, []).append(pi)
        for m, pis in seen.items(): out.append((k, m, pis))
    return out

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    name = sys.argv[1] if len(sys.argv) > 1 else "all"
    files = sorted(glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "*_asm.json"))) if name == "all" else [asmpath.resolve(name + "_asm.json")]
    total = 0
    for f in files:
        try: steps = json.load(open(f, encoding="utf-8"))["steps"]
        except Exception: continue
        bad, loc2 = stray_prev(steps), stray_loc(steps); nm = os.path.basename(f).replace("_asm.json", "")
        total += len(bad) + len(loc2)
        if loc2: print("%s: 다른 창고에 있는데 이 번호 화면에 보이는 부품 %d곳 %s" % (nm, len(loc2), [(k, "%d번의 %d개" % (m, len(p))) for k, m, p in loc2][:12]))
        if bad or name != "all": print("%s: 앞 창고 부품이 숨겨지지 않은 번호 %d곳 %s" % (nm, len(bad), [(k, "%d~%d번" % (v[0], v[-1])) for k, v in bad][:10]))
    print("합계 %d곳" % total); sys.exit(1 if total else 0)

if __name__ == "__main__": main()
