# 조립 스크립트를 저장 없이 한 번 돌려 결과(띄움·화면 올림·내보낼 단계)를 JSON 으로 남긴다 — 도구(moves·asmlib)를 고치기 전/후 비교용.
#   python asm_probe.py <이름> <출력.json> [--스크립트 다른경로.py]
#   python asm_probe.py --비교 <전.json> <후.json>      → 띄움·올림·단계가 달라진 곳만 출력
# 저장(save_links·check_fixes·stepchecks.apply·__main__ 쓰기)은 하지 않는다. 2026-11-20 auto_hover 바닥 처리 수정 때 dog·formula1 영향 확인에 썼다.
import sys, os, runpy, json, glob
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def probe(name, out, script=None):
    if script is None:
        hits = glob.glob(os.path.join(HERE, "큐보", "조립도", "*", name, name + ".py"))
        if not hits: sys.exit("조립 스크립트를 못 찾음: %s" % name)
        script = hits[0]
    script = os.path.abspath(script); folder = os.path.dirname(script)
    real = glob.glob(os.path.join(HERE, "큐보", "조립도", "*", name))
    os.chdir(real[0] if real else folder)
    sys.path.insert(0, HERE); sys.path.insert(0, os.getcwd())
    import asmlib, stepchecks
    asmlib.Asm.save_links = lambda s: None; asmlib.Asm.check_fixes = lambda s: None; stepchecks.apply = lambda A, n: None
    g = runpy.run_path(script, run_name="probe"); A = g["A"]
    res = {"auto_hover": [list(map(str, r)) for r in (g.get("_AH") or [])],
           "hover": {"%d:%d" % (st.index, i): q.extra.get("hover") for st in A.steps for i, q in enumerate(st.parts) if q.extra.get("hover") is not None},
           "lift": A.meta.get("lift") or {},
           "steps": g["export_steps"](A) if "export_steps" in g else None}
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    print("OK", name, "→", out, "| 단계", len(A.steps), "| 띄움", len(res["hover"]), "| 올림", res["lift"])

def compare(a, b):
    A = json.load(open(a, encoding="utf-8")); B = json.load(open(b, encoding="utf-8"))
    hv = {k: (A["hover"].get(k), v) for k, v in B["hover"].items() if A["hover"].get(k) != v}
    hv.update({k: (v, None) for k, v in A["hover"].items() if k not in B["hover"]})
    lf = {k: (A["lift"].get(k), v) for k, v in B["lift"].items() if A["lift"].get(k) != v}
    lf.update({k: (v, None) for k, v in A["lift"].items() if k not in B["lift"]})
    st = [i + 1 for i, (x, y) in enumerate(zip(A["steps"] or [], B["steps"] or [])) if x != y]
    print("띄움 달라짐(번호:순서 → 전, 후):", hv or "없음")
    print("화면 올림 달라짐(번호 → 전, 후):", lf or "없음")
    print("내보낸 단계가 달라진 번호:", st or "없음")

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--비교": compare(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 3: probe(sys.argv[1], sys.argv[2], sys.argv[sys.argv.index("--스크립트") + 1] if "--스크립트" in sys.argv else None)
    else: print(__doc__ or open(__file__, encoding="utf-8").read().split("import")[0])
