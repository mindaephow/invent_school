# K0 점검 — 물리법칙: 면과 면은 자석처럼 붙는다, 겹침도 틈도 없다(큐보 부품결합규칙.md K0). 겹침과 틈을 한 도구로 잰다(사용자 지시 2026-11-06). 읽기만 한다.
#   python k0_check.py <이름|all> [번호 …]
#   겹침  몸통 겹침(check_local.js: 몸통·홀 테두리 상자, 허용 0.05mm) · 프레임끼리 겹침(K1 규칙3) · 돌기가 구멍 없는 곳을 뚫음·한 구멍에 돌기 둘(joincheck.overlaps)
#   틈    리벳으로 이은 부품 사이(K1 규칙2·8, joincheck) · 돌기로 프레임에 바로 꽂는 부품 몸체↔프레임(규칙13) · 볼트·너트 머리·판 두께(규칙9·14·15)
# 새 계산은 없고 기존 도구의 판정을 한 보고서로 모은다 — 기준을 바꾸려면 원본 도구를 고친다(규칙 C7).
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import os, sys, io, re, json, runpy, tempfile, subprocess, contextlib
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import stepchecks, joincheck, cubo_joint_check as C, asmlib

OVERLAP_RULES = ("규칙3 ",)                                   # cubo_joint_check 결과 중 겹침
GAP_RULES = ("규칙8 ", "규칙13", "규칙9", "규칙14·15")          # cubo_joint_check 결과 중 틈(리벳 틈은 joincheck 와 같은 stepchecks.rivet_gaps 로 따로 잰다)

def body_overlaps(A):
    """check_local.js 의 몸통 겹침 목록 — [(번호 집합, 문장)]. 조립도 전체의 최종 자세로 재므로 번호별이 아니라 쌍으로 나온다."""
    with contextlib.redirect_stdout(io.StringIO()):
        steps = asmlib.export_steps(A)
    tmp = tempfile.NamedTemporaryFile("w", suffix="_asm.json", delete=False, encoding="utf-8")
    try:
        json.dump({"steps": steps}, tmp, ensure_ascii=False); tmp.close()
        out = subprocess.run(["node", "check_local.js", tmp.name], capture_output=True, text=True, encoding="utf-8", cwd=HERE).stdout
    finally:
        try: os.unlink(tmp.name)
        except OSError: pass
    res = []
    for ln in out.splitlines():
        m = re.match(r"\s+겹침 (\d+)\.\d+ (\S+) <> (\d+)\.\d+ (\S+)", ln)
        if m: res.append(({int(m.group(1)), int(m.group(3))}, "몸통 겹침 %s번 %s <> %s번 %s" % (m.group(1), m.group(2), m.group(3), m.group(4))))
    return res

def check_one(nm, want):
    with contextlib.redirect_stdout(io.StringIO()):   # 조립 스크립트가 찍는 [규칙 자동] 같은 안내는 점검 결과가 아니라 뺀다
        A = runpy.run_path(nm + ".py", run_name="probe")["A"]
    ks = want or [i for i, st in enumerate(A.steps, 1) if st.parts or st.kw.get("moveMade")]
    overlap, gap, notes = [], [], []
    for k in ks:
        try:
            for r in C.check(A, k):
                if r.startswith(OVERLAP_RULES): overlap.append("%d번 %s" % (k, r))
                elif r.startswith(GAP_RULES): gap.append("%d번 %s" % (k, r))
        except BaseException as e: notes.append("⚠ %d번 cubo_joint_check 점검 오류: %s" % (k, repr(e)[:70]))
        try:
            for x in stepchecks.rivet_gaps(A, k): gap.append("%d번 리벳 틈: %s (%s↔%s) %.1fmm" % ((k,) + x))
            for x in stepchecks.fastener_protrusion(A, k): gap.append("%d번 볼트·너트가 프레임 면 밖으로 나옴: %s (%s) %.1fmm" % ((k,) + x))
            if A.steps[k - 1].kw.get("moveMade"):
                for m in joincheck.overlaps(A, k): overlap.append("%d번 %s" % (k, m))
        except BaseException as e: notes.append("⚠ %d번 joincheck 점검 오류: %s" % (k, repr(e)[:70]))
    try:
        for ns, s in body_overlaps(A):
            if not want or ns & set(want): overlap.append(s)
    except BaseException as e: notes.append("⚠ 몸통 겹침 점검 오류: %s" % repr(e)[:70])
    return len(ks), overlap, gap, notes

def main():
    want = sys.argv[1:]; name = want[0] if want else "all"; steps = [int(a) for a in want[1:]]
    names = [os.path.basename(p)[:-3] for p in sorted([asmpath.ap(_n, ".py") for _n in asmpath.names()]) if not os.path.basename(p).startswith(("scratch", "new_assembly", "_"))] if name == "all" else [name]
    total = 0; skipped = 0
    for nm in names:
        try: n_k, overlap, gap, notes = check_one(nm, steps)
        except BaseException as e: print("⚠ %s 건너뜀: %s" % (nm, repr(e)[:80])); skipped += 1; continue
        print("== %s: %d개 번호 점검 — 겹침 %d건 · 틈 %d건" % (nm, n_k, len(overlap), len(gap)))
        for tag, lst in (("겹침", overlap), ("틈", gap)):
            for s in dict.fromkeys(lst): print("  ❌ %s %s%s" % (tag, s, " (×%d)" % lst.count(s) if lst.count(s) > 1 else ""))
        for s in notes: print(" ", s)
        total += len(overlap) + len(gap) + len(notes)
    print("합계 %d건%s" % (total, " (건너뜀 %d개 — 점검 안 됨)" % skipped if skipped else ""))

if __name__ == "__main__": main()
