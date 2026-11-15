# 조립 스크립트의 구멍 번호(옛 hN_M 등)를 DB 상세내역 번호로 바꾼다 — 구멍 위치로 짝을 지어 바꾸므로 같은 구멍을 가리킨다.
#   python convert_hole_ids.py <이름|스크립트 경로> [--write]     --write 없이 돌리면 바꿀 개수만 보여 준다
#   옛 번호표는 conn_legacy.json(옛 partlib 의 프레임 규칙으로 만든 표, 저장소에 있음), 새 번호표는 conn.json(부품 DB 상세내역).
#   차시를 시작할 때 number_start.py 가 옛 번호(hN_M)를 찾으면 자동으로 부른다(auto) — 바꾸기 전 스크립트는 refs/<이름>/_script_backup/ 에 백업한다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import ast, json, re, sys, os, math, time, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
_T = os.path.join(HERE, "conn_legacy.json")
if not os.path.exists(_T): _T = os.path.join(os.environ.get("TEMP", "/tmp"), "conn_old.json")
old = json.load(open(_T, encoding="utf-8")); new = json.load(open(os.path.join(HERE, "conn.json"), encoding="utf-8"))
OLD_ID = re.compile(r"""["']h\d+_\d+["']""")   # 옛 프레임 구멍 번호(칸_줄) — 새 번호는 h 숫자 하나
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
        _nl = "\r\n" if b"\r\n" in open(path, "rb").read() else "\n"   # 줄 끝(CRLF/LF)은 원래대로
        open(path, "w", encoding="utf-8", newline="").write(_nl.join(lines))
    return len(edits), unresolved
def needs(path):
    """이 스크립트에 옛 구멍 번호(hN_M)가 남아 있는 개수."""
    try: return len(OLD_ID.findall(open(path, encoding="utf-8").read()))
    except OSError: return 0
def auto(name):
    """차시 시작 때 부른다: 옛 번호가 있으면 백업하고 바꾼다 -> (옛 번호 개수, 바꾼 개수, 못 정한 목록, 백업 경로). 옛 번호가 없으면 (0, 0, [], None)."""
    path = asmpath.resolve(name + ".py"); k = needs(path)
    if not k: return 0, 0, [], None
    bd = os.path.join(HERE, "refs", name, "_script_backup"); os.makedirs(bd, exist_ok=True)
    bk = os.path.join(bd, "%s_%s_구멍번호변환전.py" % (name, time.strftime("%Y%m%d_%H%M%S"))); shutil.copy2(path, bk)
    n, u = run(path, True)
    n2, err = by_error(name, path)
    if n + n2 == 0:   # 바꾼 것이 없으면(남은 것은 손으로 바꿀 줄뿐) 백업을 쌓지 않는다
        os.remove(bk); bk = "바꾼 것 없음"
    return k, n + n2, err, bk
def _probe(name):
    """스크립트를 쓰기 없이(probe) 돌려 본다 -> 오류 글(없으면 "")."""
    import subprocess
    p = subprocess.run([sys.executable, "-c", "import runpy,asmpath; runpy.run_path(asmpath.ap(%r, '.py'), run_name='probe')" % name], capture_output=True, text=True, encoding="utf-8", cwd=HERE, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return "" if p.returncode == 0 else (p.stderr or "오류")
def by_error(name, path, limit=400):
    """코드만 읽어서는 어느 부품의 구멍인지 못 정한 옛 번호를, 스크립트를 실제로 돌려 나오는 오류(KeyError: (부품, 옛 번호))와 그 줄 번호로 하나씩 바꾼다.
    -> (바꾼 개수, 남은 오류 한 줄 또는 ""). 옛 번호가 아닌 오류를 만나거나 더 못 바꾸면 멈춘다(그때의 오류를 돌려준다)."""
    done = 0; base = os.path.basename(path)
    for _ in range(limit):
        err = _probe(name)
        if not err: return done, ""
        last = [l for l in err.strip().splitlines() if l.strip()][-1]
        m = re.search(r"KeyError: \('([^']+)', '(h\d+(?:_\d+)?)'\)", last)
        lns = [int(x) for x in re.findall(r'File ".*?%s", line (\d+)' % re.escape(base), err)]
        nid = mapping(m.group(1)).get(m.group(2)) if m else None
        if not (m and lns and nid and nid != m.group(2)): return done, "%s 줄 %s — %s" % (base, lns[-1] if lns else "?", last[:160])
        raw = open(path, "rb").read(); nl = "\r\n" if b"\r\n" in raw else "\n"; lines = raw.decode("utf-8").split(nl)
        pat = re.compile(r"""(["'])%s\1""" % re.escape(m.group(2)))
        hit = next((i for i in range(lns[-1] - 1, min(lns[-1] + 14, len(lines))) if pat.search(lines[i])), None)   # 여러 줄에 걸친 호출은 시작 줄 아래에서 찾는다
        if hit is None: return done, "%s 줄 %s — %s" % (base, lns[-1] if lns else "?", last[:160])
        lines[hit] = pat.sub(lambda g: g.group(1) + nid + g.group(1), lines[hit], count=1)
        open(path, "w", encoding="utf-8", newline="").write(nl.join(lines)); done += 1
    return done, "바꾸기 횟수 한도(%d)에 닿음" % limit
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    w = "--write" in sys.argv
    for f in [a for a in sys.argv[1:] if not a.startswith("--")]:
        if not os.path.exists(f): f = asmpath.resolve(f + ".py")
        n, u = run(f, w); print(f, "바꿈" if w else "바꿀 것", n, "| 못 정한", len(u), u[:6], "| 옛 번호(hN_M) 남음", needs(f))
