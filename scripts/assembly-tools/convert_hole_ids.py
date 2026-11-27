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
_FMT_CACHE = {}
def formula(part):
    """옛 번호 h{칸}_{줄} -> 새 번호 h{N} 의 계산식. 열 먼저(N=(칸-1)*줄수+줄)·줄 먼저(N=(줄-1)*칸수+칸) 중 부품 전체가 맞는 쪽 -> ("col", 줄수) | ("row", 칸수) | None."""
    if part in _FMT_CACHE: return _FMT_CACHE[part]
    pairs = []; n = new.get(part, {}).get("holes", [])
    for h in old.get(part, {}).get("holes", []):
        m = re.match(r"h(\d+)_(\d+)$", h["id"])
        if not m or not n: continue
        b = min(n, key=lambda x: math.dist(x["pos"], h["pos"]))
        if math.dist(b["pos"], h["pos"]) < 1.5 and re.match(r"h\d+$", b["id"]): pairs.append((int(m.group(1)), int(m.group(2)), int(b["id"][1:])))
    res = None
    if pairs:
        R = max(r for _, r, _ in pairs); C = max(c for c, _, _ in pairs)
        if all(nn == (c - 1) * R + r for c, r, nn in pairs): res = ("col", R)
        elif all(nn == (r - 1) * C + c for c, r, nn in pairs): res = ("row", C)
    _FMT_CACHE[part] = res; return res
_FMT_TPL = re.compile(r"^h(%[ds]|\d+)_(%[ds]|\d+)$")
def _fmt_nodes(tree):
    """형식 문자열로 옛 번호를 만드는 노드 -> [(노드, 템플릿 "h%d_%d", [자리마다의 식 노드])]. "h%d_%d" % (a, b) · "h%d_1" % c · "h%d_%d" % k · f"h{c}_{r}" 모두."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) and _FMT_TPL.match(node.left.value):
            t = node.left.value; k = len(re.findall(r"%[ds]", t)); r = node.right
            if isinstance(r, ast.Tuple): args = list(r.elts) if not any(isinstance(e, ast.Starred) for e in r.elts) else []
            elif k == 1: args = [r]
            else: args = [ast.Subscript(value=r, slice=ast.Constant(i), ctx=ast.Load()) for i in range(k)]   # "h%d_%d" % _k (_k 가 (칸, 줄) 묶음)
            if len(args) == k: out.append((node, t, args))
        elif isinstance(node, ast.JoinedStr):
            t = ""; args = []; ok = True
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str): t += v.value
                elif isinstance(v, ast.FormattedValue) and not v.format_spec and v.conversion == -1: t += "%d"; args.append(v.value)
                else: ok = False
            if ok and args and _FMT_TPL.match(t): out.append((node, t, args))
    return out
def _base_name(n):
    while isinstance(n, (ast.Subscript, ast.Attribute)): n = n.value
    return n.id if isinstance(n, ast.Name) else None
def _var_parts(tree):
    """변수 이름 -> 그 이름이 가리키는 부품 이름들(place/attach/recv… 결과·별칭·for/컴프리헨션 묶음)."""
    var = {}
    def calls_in(v):
        for c in ast.walk(v):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in ("place", "attach", "recv", "place_next", "place_by") and c.args and isinstance(c.args[0], ast.Constant) and isinstance(c.args[0].value, str): yield c.args[0].value
    def names(t): return [t.id] if isinstance(t, ast.Name) else [x for e in getattr(t, "elts", []) for x in names(e)]
    def add(name, ps):
        if ps: var.setdefault(name, set()).update(ps)
    def of(v):
        b = _base_name(v); return var.get(b, set()) if b else set()
    for _ in range(3):   # 별칭·묶음은 몇 번 되풀이해 퍼뜨린다
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)) and len(node.targets[0].elts) == len(node.value.elts):
                    for t, v in zip(node.targets[0].elts, node.value.elts):
                        if isinstance(t, ast.Name): add(t.id, set(calls_in(v)) | of(v))
                else:
                    ps = set(calls_in(node.value)) | (of(node.value) if isinstance(node.value, ast.Name) else set())
                    for t in node.targets:
                        for nm in names(t): add(nm, ps)
            it = tg = None
            if isinstance(node, (ast.For, ast.comprehension)): it, tg = node.iter, node.target
            if it is not None and isinstance(it, (ast.Tuple, ast.List)):
                for e in it.elts:
                    if isinstance(tg, ast.Name): add(tg.id, of(e))
                    elif isinstance(tg, ast.Tuple) and isinstance(e, (ast.Tuple, ast.List)) and len(e.elts) == len(tg.elts):
                        for t, v in zip(tg.elts, e.elts):
                            if isinstance(t, ast.Name): add(t.id, of(v))
    return var
def format_edits(tree, src, var):
    """형식 문자열 옛 번호 -> 새 번호 식으로 바꾸는 편집 [(줄, 시작, 끝, None, 새 글)]과 못 바꾼 것 [(줄, 이유)]."""
    parent = {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p): parent[c] = p
    def parts_of_ctx(node):
        p = parent.get(node)
        if isinstance(p, ast.Tuple) and len(p.elts) == 2 and p.elts[1] is node:   # (부품 변수, "h..") — attach 의 연결 값·반복 묶음
            b = _base_name(p.elts[0]); return var.get(b) if b else None
        if isinstance(p, ast.Call) and isinstance(p.func, ast.Attribute) and p.func.attr == "hole" and p.args and p.args[0] is node:   # 부품.hole("h..")
            b = _base_name(p.func.value); return var.get(b) if b else None
        if isinstance(p, ast.Call) and isinstance(p.func, ast.Attribute) and any(a is node for a in p.args):   # asmlib._item(P, "h..", "홀") · merge_shift(t, pk, P, "h..") — 같은 호출의 다른 인자 중 부품 변수가 딱 하나일 때
            c = [var[_base_name(a)] for a in p.args if a is not node and _base_name(a) in var]
            if len(c) == 1: return c[0]
        if isinstance(p, (ast.Dict, ast.DictComp)):   # recv 의 받는 쪽 구멍(사전 열쇠)
            d = parent.get(p)
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "recv" and d.args and isinstance(d.args[0], ast.Constant): return {d.args[0].value}
        return None
    ed = []; bad = []
    for node, t, args in _fmt_nodes(tree):
        if node.lineno != node.end_lineno: bad.append((node.lineno, "여러 줄에 걸친 형식 번호")); continue
        p = parent.get(node)
        if isinstance(p, ast.Call) and not isinstance(p.func, ast.Attribute): bad.append((node.lineno, "함수 %s(…) 안 — 그 함수가 옛 번호를 바꿀 수 있어 건드리지 않음" % ast.unparse(p.func)[:20])); continue
        ps = parts_of_ctx(node)
        if not ps: bad.append((node.lineno, "어느 부품의 구멍인지 못 정함")); continue
        fs = {formula(x) for x in ps}
        if len(fs) != 1 or None in fs: bad.append((node.lineno, "부품 %s 의 번호 식을 못 정함" % sorted(ps))); continue
        kind, n = next(iter(fs)); m = _FMT_TPL.match(t); it = iter(args)
        def term(g):
            if g.isdigit(): return ("c", int(g))
            e = next(it)
            if isinstance(e, ast.Constant) and isinstance(e.value, int): return ("c", e.value)
            s_ = ast.get_source_segment(src, e) or ast.unparse(e)
            return ("e", s_ if re.match(r"^[\w.\[\]]+$", s_) else "(%s)" % s_)
        A = term(m.group(1)); B = term(m.group(2))   # 칸, 줄
        big, small = (A, B) if kind == "col" else (B, A)   # col: (칸-1)*줄수+줄 / row: (줄-1)*칸수+칸
        if big[0] == "c" and small[0] == "c": new_txt = '"h%d"' % ((big[1] - 1) * n + small[1])
        else:
            if n == 1:   # 줄이 하나(또는 칸이 하나)라 번호 = 칸 + 줄 - 1
                k = (big[1] if big[0] == "c" else 0) + (small[1] if small[0] == "c" else 0) - 1   # 상수 몫
                ex = [x[1] for x in (big, small) if x[0] == "e"]
                expr = " + ".join(ex) + (" + %d" % k if k > 0 else " - %d" % -k if k < 0 else "")
            else:
                lead = None if (big[0] == "c" and big[1] == 1) else ("%d" % ((big[1] - 1) * n) if big[0] == "c" else "(%s - 1) * %d" % (big[1], n))
                sm = str(small[1])
                expr = sm if lead is None else "%s + %s" % (lead, sm)
            new_txt = ('"h%%d" %% %s' % expr) if re.match(r"^\w+$", expr) else ('"h%%d" %% (%s)' % expr)
        ed.append((node.lineno, node.col_offset, node.end_col_offset, None, new_txt))
    return ed, bad
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
    fe, fbad = format_edits(tree, src, _var_parts(tree))   # 형식 문자열 옛 번호("h%d_1" % c · f"h{c}_{r}")
    edits += fe; unresolved += [(ln, "형식 문자열 — " + why) for ln, why in fbad]
    if write and edits:
        for ln, c0, c1, o, n in sorted(edits, reverse=True):
            L = lines[ln - 1]; b = L.encode("utf-8"); q = b[c0:c1].decode("utf-8")
            lines[ln - 1] = b[:c0].decode("utf-8") + (n if o is None else q.replace(o, n)) + b[c1:].decode("utf-8")
        _nl = "\r\n" if b"\r\n" in open(path, "rb").read() else "\n"   # 줄 끝(CRLF/LF)은 원래대로
        open(path, "w", encoding="utf-8", newline="").write(_nl.join(lines))
    return len(edits), unresolved
FMT_ID = re.compile(r"""["']h(%[ds]|[{][^}"']*[}]|\d+)_(%[ds]|[{][^}"']*[}]|\d+)["']""")   # 형식 문자열로 만든 옛 번호("h%d_%d" % (칸, 줄) · f"h{c}_{r}") — 글자로는 안 보여 needs() 가 못 센다
def format_lines(path):
    """옛 번호를 형식 문자열로 만드는 줄 -> [(줄 번호, 그 줄 앞 90자)]. 실행 KeyError 로만 드러나던 곳(dog 596·709줄)을 줄 번호로 알린다."""
    try: return [(i, L.strip()[:90]) for i, L in enumerate(open(path, encoding="utf-8").read().splitlines(), 1) if FMT_ID.search(L)]
    except OSError: return []
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
        n, u = run(f, w); print(f, "바꿈" if w else "바꿀 것", n, "| 못 정한", len(u), u[:6], "| 옛 번호(hN_M) 남음", needs(f), "| 형식 문자열 의심", [l for l, _ in format_lines(f)][:20])
