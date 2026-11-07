# 가짜 안내점(허공 화살표) 점검 — 받는 부품(recv)인데 띄우는 방향(dir)만 있고 안내점(marks)이 비었으며 noGuide 도 아닌 부품을 찾는다. 읽기만 한다.
#   python fakeguide_check.py <이름|all>
# 왜 생기나(2026-11-07 풍차 6번에서 찾음): asmlib.recv 는 옆자리에서 합쳐지는 부품(settleDir)의 marks 를 settleMarks 로 옮기고 marks 를 비운다 — dir 은 그대로 둔다.
#   뷰어(design-assembly.js)는 새 부품에 dir 이 있고 marks 가 비면 안내점을 부품 중심([base])으로 대신 써서, 그 부품이 처음 놓이는 번호에 부품 중심에서 위로 점·화살표·점이 생긴다(끝에 구멍 없음).
# 고치는 법: 그 부품을 만든 줄 뒤에 `<부품>.extra.pop('dir', None)`(합치기 번호는 settleDir 을 쓴다)을 쓰고, 점검 때문에 marks 가 필요하면 settleMarks 와 같은 값으로 채운다.
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
    bad = [(k, p["n"]) for k, s in enumerate(steps, 1) for p in s.get("parts", []) if p.get("recv") and p.get("dir") and not p.get("marks") and not p.get("noGuide")]
    total += len(bad)
    if bad or name != "all": print("%s: 가짜 안내점 후보 %d곳 %s" % (os.path.basename(f).replace("_asm.json", ""), len(bad), bad[:8]))
print("합계 %d곳" % total)
