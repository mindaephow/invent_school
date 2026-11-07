# 포니테일 사다리 기록 — 공용 뷰어·공용 도구 파일을 고치기 전에 쓴다(.claude/ponytail/hooks/ladder-gate.js 가 이 기록을 본다, 90분 유효).
#   python ladder.py "필요: 왜 꼭 필요한가" "찾은 곳: grep 한 말과 결과(기존 조립도·도구)" "재사용: 그래서 무엇을 그대로 쓰는가(없으면 왜 새로 만드는가)"
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
a = sys.argv[1:]
if len(a) != 3: sys.exit("인자 3개(필요·찾은 곳·재사용)를 따옴표로 묶어 주세요")
d = {"ts": int(time.time() * 1000), "need": a[0], "found": a[1], "reuse": a[2]}
json.dump(d, open(os.path.join(ROOT, ".claude", "ponytail_ladder.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("사다리 기록 저장(90분):", a[0][:40], "|", a[1][:60])
