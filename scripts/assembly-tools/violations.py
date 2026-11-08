# 규칙 위반을 번호별로 모아 화면이 종류마다 다른 색·기호로 칠하게 한다(사용자 지시 2026-11-08). 읽기만 한다.
#   python violations.py <이름>      번호별 위반 목록을 보여 준다(build.py 는 collect() 로 def.violations 를 만든다)
# 종류: floor ▼ 바닥 아래(asmlib.floor_check) · mark ⌖ 안내점이 부품 자기 연결점에 안 맞음(guidecheck: recv 누락·링이 자기 구멍 아님·화살표 끝/꼬리가 구멍·돌기 끝에서 뜸) · link ◎ 그 밖의 안내 문제(안내점·방향 없음 등)
#       store ▣ 다른 창고에 있는 부품이 이 번호 화면에 보임(hidecheck.stray_loc) · overlap ✕ 겹침 · gap ↔ 틈 · orient ↻ 방향(cubo_joint_check 가 메시지와 함께 부품 키 LAST 를 내준다).
# 항목: {"type", "keys": ["만든번호:부품순서"…], "msg"} — 키는 화면 부품 키와 같다(moveMade 키와 같은 모양).
import asmpath
import sys, os, re, runpy
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))

def _load(name):
    os.chdir(HERE)
    g = runpy.run_path(name + ".py", run_name="probe")
    return next(v for v in g.values() if hasattr(v, "steps") and hasattr(v, "parts") and hasattr(v, "meta"))

def collect(name):
    import asmlib, guidecheck
    A = _load(name); out = {}
    def add(k, type_, keys, msg):
        out.setdefault(str(k), []).append({"type": type_, "keys": sorted(set(keys)), "msg": msg[:120]})
    fl = {}
    for k, nm, y, where, key in asmlib.floor_check(A, keys=True): fl.setdefault((k, where), []).append((nm, y, key))
    for (k, where), v in fl.items():
        add(k, "floor", [x[2] for x in v], "%s %d개 가장 낮은 y %.1f (%s)" % ("·".join(sorted({x[0].rsplit(" ", 1)[0] for x in v})), len(v), min(x[1] for x in v), where))
    try:   # 창고: 다른 창고에 있는 부품이 이 번호 화면에 보이면 그 부품을 붉게 칠한다(2026-11-08 풍차 18번 날개 4개 사고)
        import hidecheck, json as _j
        for k, m, pis in hidecheck.stray_loc(_j.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"]):
            add(k, "store", ["%d:%d" % (m, pi) for pi in pis], "%d번의 부품 %d개가 다른 창고에 있는데 보임(hideMade 에 없음)" % (m, len(pis)))
    except Exception as e_:
        print("violations: 창고 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    bad, _n, _sk = guidecheck.run(name)
    for k, msg in bad:
        nm = re.match(r"(\S+?)(?:\(옮김\))?\s", msg + " ")
        keys = []
        if nm:
            mm = (A.steps[k - 1].kw.get("moveMade") or {})
            for key in mm:
                si, pi = (int(x) for x in key.split(":"))
                if A.steps[si - 1].parts[pi].n == nm.group(1) and mm[key].get("marks"): keys.append(key)
            if not keys:
                keys = ["%d:%d" % (k, i) for i, p in enumerate(A.steps[k - 1].parts) if p.n == nm.group(1)]
        _mark = re.search(r"자기 구멍|자기 자리가 아니다|구멍 축 위에 없|돌기 끝에서 .{0,12}떨어|recv 표시가 없|돌기 끝에 찍힌", msg)   # 안내점·링·화살표 끝이 부품 자기 연결점(구멍·돌기)에 안 맞는 것은 따로 칠한다(2026-11-08)
        add(k, "mark" if _mark else "link", keys, msg)
    try:   # 겹침·틈·방향: cubo_joint_check 가 메시지와 함께 화면 부품 키를 내준다(LAST) — 틈·피치는 ↔, 방향은 ↻, 나머지(겹침·구조)는 ✕
        import cubo_joint_check as cj
        for k in range(1, len(A.steps) + 1):
            for msg in cj.check(A, k):
                t = "orient" if msg.startswith("규칙10") else "gap" if re.search(r"틈|피치", msg) else "overlap"
                add(k, t, cj.LAST.get(msg, []), msg)
    except Exception as e_:
        print("violations: 겹침·틈·방향 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 몸통 겹침(node check_local.js 의 '겹침 k.i 이름 <> k.i 이름'): 부품이 서로 뚫고 들어간 것 — 터미널 숫자로만 끝나던 것을 화면 ✕ 로 보이게(사용자 지적 2026-11-08 로봇팽이 15번 큰기어가 판을 뚫음)
        import subprocess, json as _j
        _ap = str(asmpath.resolve(name + "_asm.json")); _st = _j.load(open(_ap, encoding="utf-8"))["steps"]
        _o = subprocess.run(["node", "check_local.js", _ap], capture_output=True, text=True, encoding="utf-8", cwd=HERE).stdout
        def _at(k_, i_):   # 그 부품이 마지막으로 놓이거나 옮겨지는 번호
            key_ = "%d:%d" % (k_, i_); return max([k_] + [n_ + 1 for n_, s_ in enumerate(_st) if key_ in (s_.get("moveMade") or {})])
        for m_ in re.finditer(r"겹침\s+(\d+)\.(\d+)\s+(\S+)\s+<>\s+(\d+)\.(\d+)\s+(\S+)", _o):
            ka, ia, na, kb, ib, nb = int(m_.group(1)), int(m_.group(2)), m_.group(3), int(m_.group(4)), int(m_.group(5)), m_.group(6)
            gear = ("기어" in na) or ("기어" in nb)
            add(max(_at(ka, ia), _at(kb, ib)), "overlap", ["%d:%d" % (ka, ia), "%d:%d" % (kb, ib)], "%s ↔ %s 몸통이 겹침(뚫고 들어감)%s" % (na, nb, " — 기어는 상자 근사라 모서리 오탐일 수 있음, 중심 거리로 확인" if gear else ""))
    except Exception as e_:
        print("violations: 몸통 겹침을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    try:   # 손값 경고(사용자 지시 2026-11-08): 조립도 .py 에 손으로 적은 hover=숫자·marks=[[…]]·offset=[…] 는 부품 자리에서 계산된 값이 아니다 → 그 번호·부품을 ✋ 로 경고한다(막지는 않는다)
        _src = open(str(asmpath.resolve(name + ".py")), encoding="utf-8").read()
        for ln in _src.splitlines():
            m_ = re.match(r"\s*(v\d+_\d+)\s*=\s*s(\d+)\.\w+\(\s*'([^']+)'", ln)
            if not m_: continue
            code = ln.split("   #")[0]
            hv = []; mk = re.search(r"\b(marks|settleMarks|faceMarks|offset)=\[\[?-?[0-9]", code)   # 연결점(부품 리스트)이 아닌 숫자는 전부 경고
            if not (hv or mk): continue
            k = int(m_.group(2)); keys = ["%d:%d" % (k, i) for i, p in enumerate(A.steps[k - 1].parts) if p.n == m_.group(3)]
            what = ", ".join(["%s=%s" % h for h in hv] + (["%s 숫자 직접 입력" % mk.group(1)] if mk else []))
            if any(x["type"] == "hand" and x["msg"].startswith(m_.group(3)) for x in out.get(str(k), [])): continue   # 같은 번호에 같은 부품 이름이 여러 줄이면 한 번만
            add(k, "hand", keys, "%s 연결점이 아닌 숫자를 씀(%s) — 부품 리스트의 구멍·돌기 연결점에서 계산해야 한다" % (m_.group(3), what))
    except Exception as e_:
        print("violations: 손값 점검을 못 붙임 —", str(e_)[:100], file=sys.stderr)
    return out

def write_entry(name):
    """모은 위반을 항목 파일(<이름>_entry.js)의 def.violations 로 쓴다(번호 지문에 안 들어간다). 바뀐 것이 없으면 쓰지 않는다. -> (위반 번호 수, 종류들, 바뀜 여부)"""
    import json
    vd = collect(name); ef = os.path.join(os.path.dirname(asmpath.resolve(name + "_entry.js")), name + "_entry.js") if False else asmpath.resolve(name + "_entry.js")
    old = open(ef, encoding="utf-8").read()
    new = re.sub(r"      violations: .*\n", "", old)
    if vd: new = new.replace("      steps: [", "      violations: %s,\n      steps: [" % json.dumps(vd, ensure_ascii=False), 1)
    if new != old: open(ef, "w", encoding="utf-8").write(new)
    return len(vd), sorted({v["type"] for l_ in vd.values() for v in l_}), new != old

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if "--write" in sys.argv:   # 화면 데이터에 위반만 반영한다(빌드가 경고로 막혀도 화면에서 위반을 보기 위해): 항목 파일에 쓰고 emit.py 로 화면 파일을 갱신
        import subprocess, json as _j
        n_, ts_, ch_ = write_entry(sys.argv[1]); ef_ = asmpath.resolve(sys.argv[1] + "_entry.js")
        m_ = re.search(r'id: "(cubo-\d+-[A-Za-z0-9_]+)"', open(ef_, encoding="utf-8").read())
        r_ = subprocess.run([sys.executable, "emit.py", ef_ if False else sys.argv[1] + "_entry.js", m_.group(1) if m_ else "cubo-1-" + sys.argv[1]], capture_output=True, text=True, encoding="utf-8")
        print("위반 표시 반영: %d번 (%s)" % (n_, ", ".join(ts_) or "없음"), "· 항목 파일 바뀜" if ch_ else "· 변화 없음"); print((r_.stdout or r_.stderr).strip()[-200:]); sys.exit(0)
    r = collect(sys.argv[1])
    for k in sorted(r, key=int):
        for v in r[k]: print("%s번 %s %s 부품 %d개 — %s" % (k, v["type"], "", len(v["keys"]), v["msg"]))
    print("위반 번호 %d개" % len(r))
