# 조립 스크립트의 구멍 번호(옛 hN_M 등)를 DB 상세내역 번호로 바꾼다 — 구멍 위치로 짝을 지어 바꾸므로 같은 구멍을 가리킨다. 한 번 쓰는 변환 도구.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import ast, json, re, sys, os, math
T = os.path.join(os.environ.get("TEMP", "/tmp"), "conn_old.json")
old = json.load(open(T, encoding="utf-8")); new = json.load(open("conn.json", encoding="utf-8"))
ID = re.compile(r"h\d+(_\d+)?$")
def mapping(part):
    o = {h["id"]: h["pos"] for h in old.get(part, {}).get("holes", [])}; n = new.get(part, {}).get("holes", [])
    m = {}
    for i, p in o.items():
        best = min(n, key=lambda h: math.dist(h["pos"], p)) if n else None
        if best is not None and math.dist(best["pos"], p) < 1.5: m[i] = best["id"]
    return m
def run(path, write):
    src = open(path, encoding="utf-8").read(); tree = ast.parse(src); lines = src.split("\n")
    var = {}; edits = []; unresolved = []
    def part_of(call): return call.args[0].value if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str) else None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr in ("place", "attach", "recv", "place_next", "place_by"):
            p = part_of(node.value)
            if p:
                for t in node.targets:
                    if isinstance(t, ast.Name): var.setdefault(t.id, set()).add(p)
    def fix(const, part):
        if part is None: unresolved.append((const.lineno, const.value)); return
        m = mapping(part); nid = m.get(const.value)
        if nid is None: unresolved.append((const.lineno, f"{part}:{const.value}")); return
        if nid != const.value: edits.append((const.lineno, const.col_offset, const.end_col_offset, const.value, nid))
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("attach", "recv", "place_by", "place_next"):
            own = part_of(node)
            links = None
            for a in node.args[2:3]: links = a
            if node.func.attr == "place_next": continue
            if isinstance(links, ast.Dict):
                for k, v in zip(links.keys, links.values):
                    if node.func.attr == "recv" and isinstance(k, ast.Constant) and isinstance(k.value, str) and ID.match(k.value): fix(k, own); seen.add(id(k))
                    if isinstance(v, ast.Tuple) and len(v.elts) == 2 and isinstance(v.elts[1], ast.Constant) and isinstance(v.elts[1].value, str) and ID.match(v.elts[1].value):
                        n = v.elts[0]; ps = var.get(n.id) if isinstance(n, ast.Name) else None
                        fix(v.elts[1], next(iter(ps)) if ps and len(ps) == 1 else None); seen.add(id(v.elts[1]))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and ID.match(node.value) and id(node) not in seen: unresolved.append((node.lineno, "미처리 " + node.value))
    if write and edits:
        for ln, c0, c1, o, n in sorted(edits, reverse=True):
            L = lines[ln - 1]; b = L.encode("utf-8"); q = b[c0:c1].decode("utf-8")
            lines[ln - 1] = b[:c0].decode("utf-8") + q.replace(o, n) + b[c1:].decode("utf-8")
        open(path, "w", encoding="utf-8").write("\n".join(lines))
    return len(edits), unresolved
if __name__ == "__main__":
    w = "--write" in sys.argv
    for f in [a for a in sys.argv[1:] if not a.startswith("--")]:
        n, u = run(f, w); print(f, "바꿈", n, "| 못 정한", len(u), u[:6])
