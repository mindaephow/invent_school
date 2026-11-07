# 창고정리 점검 — 새 창고에서 만드는 번호인데 다른 창고의 앞 번호 부품이 숨겨지지 않은(hideMade 에 없는) 곳을 찾는다. 읽기만 한다.
#   python hidecheck.py <이름|all>
# 왜 만들었나(2026-11-07 풍차 16·17·20번): 13~22번의 hideMade 가 모두 "1~12번" 복사본이라 새 창고(날개 모듈·축 기어)를 만드는 번호에 앞 창고의 허브가 같이 보였다.
#   A3a 는 번호마다 작업장(화면)을 책과 비교해 책에 없는 앞 번호 부품이 보이면 바로 hideMade 를 고치라고 하지만 도구는 slot·history 유무만 봤다.
# 판정(참고용 — 책 그림이 최종): 번호 k 가 부품을 새로 놓고(합치기만 하는 번호 제외) slot 이 앞 번호 slot 과 다를 때, 앞 번호 중 slot 이 k 와 다른 번호가 hideMade 에 없으면 보고한다.
#   같은 slot 이어도 이미 다른 창고로 합쳐 간 번호(풍차 16·17 → 18·19)는 이 도구가 못 잡는다 — 책 그림으로 본다.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, glob
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1] if len(sys.argv) > 1 else "all"
files = sorted(glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "*_asm.json"))) if name == "all" else [asmpath.resolve(name + "_asm.json")]
total = 0
for f in files:
    try: steps = json.load(open(f, encoding="utf-8"))["steps"]
    except Exception: continue
    bad = []
    for k, s in enumerate(steps, 1):
        if k < 2 or not s.get("parts") or s.get("madeNoPart"): continue
        sl = str(s.get("slot", 1)); prev = str(steps[k - 2].get("slot", 1))
        if sl == prev: continue
        hide = s.get("hideMade") or {}
        vis = [j for j in range(1, k) if str(steps[j - 1].get("slot", 1)) != sl and steps[j - 1].get("parts") and str(j) not in hide]
        if vis: bad.append((k, vis))
    total += len(bad)
    if bad or name != "all": print("%s: 앞 창고 부품이 숨겨지지 않은 번호 %d곳 %s" % (os.path.basename(f).replace("_asm.json", ""), len(bad), [(k, "%d~%d번" % (v[0], v[-1])) for k, v in bad][:10]))
print("합계 %d곳" % total)
