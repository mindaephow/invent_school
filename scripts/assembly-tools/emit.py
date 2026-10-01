# soccer_entry.js(조립 프로그램이 만든 항목)를 public/design-assemblies.js 에 넣는다. 같은 id 가 이미 있으면 그 항목만 바꾼다.
# 사용: python emit.py soccer_entry.js cubo-1-soccer
import re, sys
entry_file, aid = sys.argv[1], sys.argv[2]
path = "../../public/design-assemblies.js"
entry = open(entry_file, encoding="utf-8").read().rstrip()
src = open(path, encoding="utf-8").read()
pat = re.compile(r'  \{\n      id: "' + re.escape(aid) + r'",.*?\n  \}(?=,?\n\];)', re.S)
m = pat.search(src)
if m:
    src = src[:m.start()] + entry + src[m.end():]
    print("기존 항목을 바꿨다")
else:
    i = src.rindex("\n];")
    # 앞 항목 끝에 쉼표가 있어야 한다
    head = src[:i].rstrip()
    if not head.endswith(","): head += ","
    src = head + "\n" + entry + src[i:]
    print("새 항목을 추가했다")
open(path, "w", encoding="utf-8").write(src)
