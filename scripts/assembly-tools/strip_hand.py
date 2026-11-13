# 조립 스크립트(<이름>.py)의 손 좌표를 백업하고 지운다 — 조립도 작업을 시작할 때 한 번(release_start.py 가 부른다, 규칙 00-1 ③, 사용자 지시 2026-11-13: "손좌표가 방해가 된다").
#   python strip_hand.py <이름>            → 백업(refs/<이름>/_script_backup/<시각>.py) 후 지운다
#   python strip_hand.py <이름> --보기     → 지울 곳만 보여 준다(파일을 안 쓴다)
#   python strip_hand.py <이름> --복원 <백업파일>
# 지우는 것(handcheck.py 가 세는 것과 같다)
#   키워드: p=(숫자…) · marks/settleMarks/faceMarks/holeMarks=[[숫자…]] · side={…} · shift=(숫자…)(move_made 류)  → 그 인자를 뺀다(도구가 결합·구멍에서 다시 계산한다)
#   위치:   place(부품, 자세, (x, y, z)) · _abs_place(단계, 부품, 자세, (…숫자 포함…))  → 위치를 (0, 0, 0) 미배치 자리로 되돌린다(새 창고 바닥 부품은 원래 원점이라 그대로 둔다)
#           → 부품이 겹쳐 보이는 것이 정상이다. 번호를 만들 때 그 부품을 attach/recv 규칙 좌표로 다시 놓는다(위반 표시가 어디를 놓아야 하는지 알려 준다).
# 안전장치: 지운 결과가 파이썬 문법으로 읽히지 않으면 쓰지 않는다. 옆자리 작업 위치(to_side)는 "어디에 둘지 정하는 값"이라 건드리지 않는다.
import asmpath  # 조립도 파일 자리 연결
import ast, os, re, shutil, sys, time
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import handcheck as H   # _lit·_is_num 재사용(같은 기준으로 센다)

def _off(lines, line, col): return sum(len(l) for l in lines[:line - 1]) + len(lines[line - 1].encode("utf-8")[:col].decode("utf-8", "ignore"))

def plan(src):
    """지울 곳 목록: [(시작, 끝, 바꿀 글, 설명)] — 겹치지 않게 바깥 것만."""
    tree = ast.parse(src); lines = src.splitlines(keepends=True); edits = []
    def span(n): return _off(lines, n.lineno, n.col_offset), _off(lines, n.end_lineno, n.end_col_offset)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        if isinstance(node.func, ast.Name) and node.func.id == "_abs_place" and len(node.args) >= 4:
            a = node.args[3]
            if any(isinstance(n_, ast.Constant) and isinstance(n_.value, (int, float)) for n_ in ast.walk(a)): s, e = span(a); edits.append((s, e, "(0, 0, 0)", "_abs_place 위치 → 원점", node.lineno))
        if isinstance(node.func, ast.Attribute) and node.func.attr == "place" and len(node.args) >= 3 and H._lit(node.args[2]):
            xyz = [x.value if isinstance(x, ast.Constant) else (-x.operand.value if isinstance(x, ast.UnaryOp) else None) for x in getattr(node.args[2], "elts", [])]
            if not (len(xyz) == 3 and xyz[0] == 0 and xyz[2] == 0): s, e = span(node.args[2]); edits.append((s, e, "(0, 0, 0)", "place 위치 → 원점", node.lineno))   # 원점(x=0·z=0)은 규칙(A4)이라 둔다
        for kw in node.keywords:
            f = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            hit = (kw.arg == "p" and H._lit(kw.value)) or (kw.arg in ("marks", "settleMarks", "faceMarks", "holeMarks") and H._lit(kw.value)) or (kw.arg == "side" and isinstance(kw.value, ast.Dict)) or (kw.arg == "shift" and H._lit(kw.value) and f in ("move_made", "move_group", "move_built"))
            if hit:
                s = _off(lines, kw.value.lineno, kw.value.col_offset); e = _off(lines, kw.value.end_lineno, kw.value.end_col_offset)
                k0 = src.rfind(kw.arg, 0, s); s = k0   # 'p=' 앞까지(키워드 이름 시작)
                edits.append((s, e, "", "%s= 인자 삭제" % kw.arg, kw.value.lineno))
    edits.sort(key=lambda x: (x[0], -x[1])); out = []; last = -1
    for ed in edits:
        if ed[0] >= last: out.append(ed); last = ed[1]
    return out

def apply(src, edits):
    for s, e, new, _w, _l in sorted(edits, key=lambda x: -x[0]):
        if new == "":   # 키워드 삭제: 앞 쉼표(없으면 뒤 쉼표)까지 같이 뺀다
            b = s
            while b > 0 and src[b - 1] in " \t\n": b -= 1
            if b > 0 and src[b - 1] == ",": s = b - 1
            else:
                m = re.match(r"\s*,\s*", src[e:]); e = e + (m.end() if m else 0)
        src = src[:s] + new + src[e:]
    return src

def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"): sys.exit(__doc__)
    name = sys.argv[1]; view = "--보기" in sys.argv
    sf = asmpath.ap(name, ".py"); sb = os.path.join(HERE, "refs", name, "_script_backup")
    if "--복원" in sys.argv:
        bf = sys.argv[sys.argv.index("--복원") + 1]; shutil.copy2(bf, sf); print("복원:", bf); return
    src = open(sf, encoding="utf-8").read(); edits = plan(src)
    print("%s: 지울 손 좌표 %d곳" % (name, len(edits)))
    for s, e, new, why, line in edits[:40]: print("  %4d행 %s  [%s]" % (line, why, src[s:e].replace("\n", " ")[:60]))
    if view or not edits: return
    out = apply(src, edits)
    try: ast.parse(out)
    except SyntaxError as ex: sys.exit("❌ 지운 결과가 문법으로 안 읽힌다(%s) — 파일을 쓰지 않았다." % ex)
    os.makedirs(sb, exist_ok=True); bf = os.path.join(sb, time.strftime("%Y%m%d_%H%M%S") + ".py"); shutil.copy2(sf, bf)
    open(sf, "w", encoding="utf-8", newline="").write(out)
    print("백업:", os.path.relpath(bf, HERE), "→ 지웠다. 복원: python strip_hand.py %s --복원 <백업>" % name)
    print("→ 부품이 원점에 겹쳐 보이는 것이 정상이다. 번호를 만들 때 attach/recv 규칙 좌표로 다시 놓는다.")

main()
