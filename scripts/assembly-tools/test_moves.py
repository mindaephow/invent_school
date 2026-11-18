# moves.py(동작 묶음) 검사 — 이미 만든 조립도의 손으로 쓴 줄을 동작 묶음 호출로 바꿔 돌렸을 때, 화면 데이터(export_steps)가 한 글자도 다르지 않은지 본다.
#   python test_moves.py        → 사례마다 "같음 ✅ / 다름 ❌(첫 차이)"
# 파일을 쓰지 않는다: 조립 스크립트를 run_name="probe" 로 돌리고, 끝에서 파일을 쓰는 save_links·stepchecks.apply 는 이 검사 동안만 아무것도 안 하게 바꾼다.
import os, sys, json, runpy, tempfile, shutil
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asmlib, stepchecks, asmpath
asmlib.Asm.save_links = lambda s, *a, **k: None
stepchecks.apply = lambda *a, **k: None

CASES = [
    ("kidknight", "리벳으로 판 잇기(2번)",
     ['rv2 = [s2.attach("리벳", np.eye(3), {"돌기면 -y 1": (PT, "홀면 +y 열%d·줄%d" % cr)}, rivet=True) for cr in ((3, 3), (5, 2), (7, 3))]\n'
      'for _q in rv2: _q.extra["joinOrder"] = 1\n'
      'R_B25 = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)\n'
      'b25 = s2.recv("25프레임", R_B25, {"홀면 -y 열1·줄2": (rv2[0], "돌기면 +y 1"), "홀면 -y 열3·줄1": (rv2[1], "돌기면 +y 1"), "홀면 -y 열5·줄2": (rv2[2], "돌기면 +y 1")}, joinOrder=2, hover=_PLATE_HOVER)\n',
      'import moves as mv\nR_B25 = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)\n'
      'rv2, b25 = mv.rivet_join(s2, PT, [(3, 3), (5, 2), (7, 3)], "25프레임", R_B25, [(1, 2), (3, 1), (5, 2)])\n']),
    ("formula1", "블록 꽂기(1번 2단블록)",
     ['blkB = [s1.attach("2단블록", R_K2B, {"돌기면 +z 1": (PB, "홀면 -y 열%d·줄1" % c), "돌기면 +z 2": (PB, "홀면 -y 열%d·줄2" % c)}) for c in (7, 9)]\n'
      'blkA = [s1.attach("2단블록", R_K2A, {"돌기면 +z 1": (PA, "홀면 +y 열%d·줄1" % c), "돌기면 +z 2": (PA, "홀면 +y 열%d·줄2" % c)}) for c in (7, 9)]\n',
      'import moves as mv\nblkB = [mv.pegs_into(s1, "2단블록", R_K2B, PB, [(c, 1), (c, 2)]) for c in (7, 9)]\n'
      'blkA = [mv.pegs_into(s1, "2단블록", R_K2A, PA, [(c, 1), (c, 2)], hole_face="+y") for c in (7, 9)]\n']),
]

# 줄 단위 사례: (줄 머리, 바꿀 글) — 그 머리로 시작하는 줄 전체를 바꾼다(빈 글이면 그 줄을 지운다)
CASES += [
    ("kidknight", "DC모터 자세를 orient 로 · 모터를 판에 꽂기 · 모터 돌기 위에 판 얹기(1번)", [
        ("R_DCA = np.array(", 'import moves as mv\nR_DCA = orient("DC모터", {"홀면 +y": "-Z", "돌기면 +x": "아래"})'),
        ("R_DCB = np.array(", 'R_DCB = orient("DC모터", {"홀면 +y": "+Z", "돌기면 -x": "아래"})'),
        ("mA = s1.attach(\"DC모터\"", 'mA = mv.pegs_into(s1, "DC모터", R_DCA, PB, [(2, 2), (2, 4)], pegs=["p4", "p3"])'),
        ("mB = s1.attach(\"DC모터\"", 'mB = mv.pegs_into(s1, "DC모터", R_DCB, PB, [(8, 2), (8, 4)], pegs=["p6", "p5"])'),
        ("PT = s1.recv(\"59프레임\"", 'PT = mv.plate_on(s1, "59프레임", R_TOPW, [(mA, "돌기면 -x 열1·줄2", (2, 2)), (mA, "돌기면 -x 열1·줄1", (2, 4)), (mB, "돌기면 +x 열1·줄2", (8, 2)), (mB, "돌기면 +x 열1·줄1", (8, 4))], joinOrder=2, hover=_PLATE_HOVER)'),
        ("                                    \"홀면 -y 열8·줄2\": (mB,", ""),
    ]),
    ("autogun", "축 끝에 부시 끼우기 — 부시 자세 자동(10번)", [
        ("bush_f = s10.recv(\"부시\"", 'import moves as mv\nbush_f = mv.on_shaft(s10, "부시", axle, "+z", against=f27, joinOrder=2, hover=45)'),
        ("bush_b = s10.recv(\"부시\"", 'bush_b = mv.on_shaft(s10, "부시", axle, "-z", against=p37, joinOrder=2, hover=45)'),
    ]),
]

def apply_lines(src, spec):
    lines = src.split("\n"); miss = []
    for head, new in spec:
        idx = [i for i, l in enumerate(lines) if l.startswith(head)]
        if len(idx) != 1: miss.append("%s(%d곳)" % (head.strip()[:30], len(idx))); continue
        lines[idx[0]] = new
    return "\n".join(lines), miss

def build(path):
    cwd = os.getcwd(); os.chdir(os.path.dirname(path))
    try: g = runpy.run_path(path, run_name="probe")
    finally: os.chdir(cwd)
    return json.loads(json.dumps(asmlib.export_steps(g["A"]), ensure_ascii=False, default=str))

def first_diff(a, b, path=""):
    if type(a) != type(b): return path + " 형식 다름"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b: return path + "/" + str(k) + " 한쪽에만 있음"
            d = first_diff(a[k], b[k], path + "/" + str(k))
            if d: return d
    elif isinstance(a, list):
        if len(a) != len(b): return path + " 길이 %d≠%d" % (len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, path + "[%d]" % i)
            if d: return d
    elif a != b: return path + " %r ≠ %r" % (a, b)
    return None

bad = 0
for name, what, spec in CASES:
    src_path = asmpath.resolve(name + ".py"); src = open(src_path, encoding="utf-8").read()
    if isinstance(spec[0], tuple): out, miss = apply_lines(src, spec)
    else:
        old, new = spec; miss = [] if old in src else ["원래 줄"]; out = src.replace(old, new)
    if miss: print("⚠ %s %s: 바꿀 원래 줄을 못 찾음(스크립트가 바뀜) — 사례를 고친다: %s" % (name, what, ", ".join(miss))); bad += 1; continue
    tmp = os.path.join(os.path.dirname(src_path), "_test_moves_%s.py" % name)
    try:
        open(tmp, "w", encoding="utf-8").write(out)
        a, b = build(src_path), build(tmp)
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    d = first_diff(a, b)
    print(("✅ %s %s: 화면 데이터 같음(단계 %d개)" % (name, what, len(a))) if not d else ("❌ %s %s: 다름 — %s" % (name, what, d)))
    bad += bool(d)
sys.exit(1 if bad else 0)
