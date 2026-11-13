# 손 좌표 점검 — 조립 스크립트(<이름>.py)에 부품 위치·안내점·이동량을 숫자로 직접 적은 곳을 찾는다(큐보 부품결합규칙.md 1번 규칙: 손 좌표 금지). 읽기만 한다.
#   python handcheck.py <이름|all>
# 찾는 것(소스를 실행하지 않고 읽는다)
#   place(부품, 자세, (x, y, z))   — 위치를 숫자 3개로 직접 줌. 새 조립(창고)의 바닥 부품은 원점(x=0·z=0)에 두는 것이 규칙(A4)이라 "원점"으로 따로 세고 손 좌표로 치지 않는다
#   p=(…)·p=[…]                    — 결합에 직접 준 위치
#   marks=[[…]]·settleMarks·faceMarks·holeMarks — 안내점을 숫자로 직접 줌(결합·via 로 계산해야 한다)
#   side={…}                       — 옆자리 자세를 숫자로 직접 줌(to_side 로 계산해야 한다)
#   move_made(…, shift=(숫자…))    — 합치는 이동량을 숫자로 직접 줌(합치는 구멍에서 계산해야 한다)
#   to_side(…, (x, y, z), …)       — 옆자리 작업 위치(새 창고): 어디에 둘지는 정하는 값이라 "작업 위치"로 따로 센다
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import ast, os, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)

def _is_num(n): return isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) or (isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and _is_num(n.operand))
def _lit(n):
    """숫자만으로 이루어진 값(숫자·튜플·리스트·중첩)인가 — 계산식(변수·함수)이 하나라도 있으면 손 좌표가 아니다."""
    if _is_num(n): return True
    if isinstance(n, (ast.Tuple, ast.List)): return len(n.elts) > 0 and all(_lit(e) for e in n.elts)
    if isinstance(n, ast.Dict): return all(_lit(k) and _lit(v) if not isinstance(v, (ast.Constant, ast.List, ast.Tuple)) else True for k, v in zip(n.keys, n.values))
    return False

def scan(path):
    src = open(path, encoding="utf-8").read(); tree = ast.parse(src)
    out = {"place": [], "원점": [], "p=": [], "안내점": [], "side": [], "이동량": [], "작업위치": []}
    step_of = {}                                   # 줄 번호 → 몇 번 단계인지(sK. 이름에서)
    first_place = True
    for node in ast.walk(tree):
        # _abs_place(단계, 부품, 자세, (x, y, z)) — 앞 부품 옆 상대 잠금 없이 절대 좌표로 놓는 함수라 손 좌표의 통로다(배틀로봇 2번 받는 블록 (49.5,−65.3) 이 3번 겹침의 원인이었는데 이 점검이 못 셌다, 2026-11-13)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_abs_place" and len(node.args) >= 4:
            _p4 = node.args[3]
            if any(isinstance(n_, ast.Constant) and isinstance(n_.value, (int, float)) for n_ in ast.walk(_p4)):
                out["place"].append((node.lineno, "", ast.get_source_segment(src, node.args[1]), "_abs_place " + ast.get_source_segment(src, _p4)))
            continue
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute): continue
        f = node.func.attr; line = node.lineno
        who = ast.get_source_segment(src, node.args[0]) if node.args else ""
        base = node.func.value.id if isinstance(node.func.value, ast.Name) else ""
        if f == "place" and len(node.args) >= 3 and _lit(node.args[2]):
            xyz = [e.value if isinstance(e, ast.Constant) else (-e.operand.value if isinstance(e, ast.UnaryOp) else None) for e in getattr(node.args[2], "elts", [])]
            if len(xyz) == 3 and xyz[0] == 0 and xyz[2] == 0: out["원점"].append((line, base, who, ast.get_source_segment(src, node.args[2])))   # 새 조립(창고)의 바닥 부품은 원점(x=0·z=0, A4) — 손 좌표가 아니다
            else: out["place"].append((line, base, who, ast.get_source_segment(src, node.args[2])))
        for kw in node.keywords:
            if kw.arg == "p" and _lit(kw.value): out["p="].append((line, base, who, ast.get_source_segment(src, kw.value)))
            elif kw.arg in ("marks", "settleMarks", "faceMarks", "holeMarks") and _lit(kw.value): out["안내점"].append((line, base, who, kw.arg))
            elif kw.arg == "side" and isinstance(kw.value, ast.Dict): out["side"].append((line, base, who, "side={…}"))
            elif kw.arg == "shift" and _lit(kw.value) and f in ("move_made", "move_group", "move_built"): out["이동량"].append((line, base, who, ast.get_source_segment(src, kw.value)))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "to_side" and len(node.args) >= 4 and _lit(node.args[3]):
            out["작업위치"].append((node.lineno, "", "", ast.get_source_segment(src, node.args[3])))
    for k in out: out[k].sort()
    return out

def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = [os.path.basename(p)[:-3] for p in sorted([asmpath.ap(_n, ".py") for _n in asmpath.names()]) if not os.path.basename(p).startswith(("scratch", "new_assembly", "_"))] if want == "all" else [want]
    total = 0
    for nm in names:
        try: path = asmpath.ap(nm, ".py")
        except BaseException as e: print("⚠ %s 건너뜀: %s" % (nm, repr(e)[:60])); continue
        o = scan(path)
        bad = len(o["place"]) + len(o["p="]) + len(o["안내점"]) + len(o["side"]) + len(o["이동량"])
        base = 0
        print("== %s: 손 좌표 %d곳 (place %d·p= %d·안내점 %d·side %d·이동량 %d) · 새 조립 바닥 부품(원점) %d곳 · 옆자리 작업 위치 %d곳" % (nm, bad, len(o["place"]), len(o["p="]), len(o["안내점"]), len(o["side"]), len(o["이동량"]), len(o["원점"]), len(o["작업위치"])))
        for key in ("place", "p=", "안내점", "side", "이동량"):
            for line, b, who, val in o[key][:12]: print("   %s %d행 %s %s %s" % (key, line, b, who, val[:50]))
            if len(o[key]) > 12: print("   %s … 외 %d곳" % (key, len(o[key]) - 12))
        total += bad - base
    print("합계 손 좌표 %d곳" % total)

if __name__ == "__main__": main()
