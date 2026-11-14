# 부품정리·창고정리 배지만 화면 데이터(public/design-assemblies.js)에 올린다 — 사전작업이라 번호 작업(격자·카메라·읽기 표) 산출물과 상관없이 올라가야 한다(사용자 지시 2026-11-14: "미리 하는 작업인데 왜 2번하고 함께 올라가").
#   python prep_badge.py <이름>   build.py 가 --write 를 번호 산출물 때문에 거부하기 직전에 자동으로 부른다. 판정 기준은 build.py 와 같다(A2a·A3a): 모든 번호에 ▣ 사용 부품 + 합계=LIST, 모든 번호에 slot + 바뀌는 번호마다 history.
import asmpath  # 조립도 파일 자리 연결
import sys, os, re, json, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); JS = os.path.join(HERE, "..", "..", "public", "design-assemblies.js")
def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    name = sys.argv[1]
    rl = json.load(open(asmpath.resolve(name + "_rules.json"), encoding="utf-8")) if os.path.exists(asmpath.resolve(name + "_rules.json")) else {}
    if not rl.get("parts_sum"): print("parts_sum 꺼짐 — 배지 안 올림"); return
    steps = json.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"]
    lst = asmpath.list_counts(name); tot = collections.Counter(); all_used = True
    for st in steps:
        m = re.search(r"▣ 사용 부품:\s*(.*)", st.get("note") or "")
        if not m: all_used = False; continue
        for p in re.sub(r"\([^)]*\)", "", m.group(1)).split(","):
            mm = re.match(r"\s*(.+?)\s+(\d+)\s*$", p)
            if mm: tot[mm.group(1).strip()] += int(mm.group(2))
    parts_ok = bool(all_used and all(tot.get(n, 0) == c for n, c in lst.items() if n != "리모컨") and all(n in lst for n in tot))
    sl = [s.get("slot") for s in steps]
    bad = [i for i in range(2, len(steps) + 1) if sl[i - 1] is not None and sl[i - 2] is not None and sl[i - 1] != sl[i - 2] and not steps[i - 1].get("history")]
    slots_ok = any(v is not None for v in sl) and all(v is not None for v in sl) and not bad
    src = open(JS, encoding="utf-8").read(); mid = re.search(r'id: "(cubo-[^"]*%s)"' % re.escape(name), src)
    if not mid: print("화면 데이터에 %s 항목이 없다 — 배지 안 올림" % name); return
    a = mid.start(); b = src.index("      steps: [", a)
    blk = re.sub(r"      prepDone: .*\n", "", src[a:b]) + "      prepDone: %s,\n" % json.dumps({"parts": parts_ok, "slots": slots_ok})
    open(JS, "w", encoding="utf-8").write(src[:a] + blk + src[b:])
    print("부품정리 %s · 창고정리 %s (배지만 올림)" % ("완료" if parts_ok else "미완", "완료" if slots_ok else "미완"))
main()
