# 조립도 "완성" 일괄 점검 — 작업 도중에는 아무것도 막지 않고, 다 만든 뒤(완성에 갔을 때) 한 번에 빠진 것을 찾아 채운다(관리자 지시 2026-10-16).
#   python final_audit.py <이름> [--fix]
#   · 만든 번호(부품이 있는 번호) 전체를 훑어 번호마다 빠진 것을 표로 보여 준다.
#   · --fix : 자동으로 채울 수 있는 것(홀라인 그림 NN_1·NN_2 다시 만들기, 작업 점검 블록 다시 계산)은 채우고, 사람이 판단해야 하는 것은 목록으로 남긴다.
#   점검 항목: 작업 점검 블록 · 읽기 표 7칸 · 읽기 표 부품 = 모델 부품 · 축 파일(_axes.json)과 fit 오차(2px 초과·옮겨 쓴 값 표시) · 그림 3장(NN·NN_1·NN_2) ·
#            비교 증거(cmp/NN.png) · 카메라 camSrc · 확인 필요(review) 표시 · 추정 표시. 결과는 refs/<이름>/final_audit.md 로도 저장한다.
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "━ 작업 점검 ━"
FIELDS = ["면", "링", "부품", "대조", "방향", "부품방향", "판단과정"]

def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    name = sys.argv[1]; fix = "--fix" in sys.argv
    D = os.path.join(HERE, "refs", name)
    asm = load(os.path.join(HERE, name + "_asm.json"), {"steps": []})["steps"]
    read = load(os.path.join(HERE, name + "_read.json"), {})
    checks = load(os.path.join(HERE, name + "_checks.json"), {})
    index = load(os.path.join(D, "index.json"), [])
    have = {}
    for r in index: have.setdefault(r["step"], set()).add(r["idx"])
    made = [i + 1 for i, s in enumerate(asm) if s.get("parts")]
    if not made: sys.exit("만든 번호가 없다")
    blocking = checks.get("blocking") or []
    rows = []; fixable = {"img": [], "note": False}
    for n in made:
        s = asm[n - 1]; miss = []; warn = []
        if MARK not in s.get("note", ""): miss.append("작업 점검 블록 없음"); fixable["note"] = True
        rd = read.get(str(n))
        if not rd: miss.append("읽기 표 없음")
        else:
            for f in FIELDS:
                if not str(rd.get(f, "")).strip(): miss.append("읽기 표 '%s' 빈칸" % f)
            txt = " ".join(str(rd.get(f, "")) for f in FIELDS)
            if "추정" in txt: warn.append("읽기 표에 '추정' 표시")
        for x in blocking:
            if x.startswith("%d번:" % n): miss.append("점검 미충족 — " + x.split(":", 1)[1].strip())
        ax = load(os.path.join(D, "%02d_axes.json" % n))
        if not ax: miss.append("축 파일(_axes.json) 없음")
        else:
            fit = ax.get("fit") or {}
            if not fit: miss.append("축 파일에 fit(계산 근거) 없음 — 손으로 쓴 값")
            else:
                if fit.get("carried"): warn.append("카메라는 다른 번호 값을 옮김")
                if float(fit.get("err_px", 0)) > 2.0: warn.append("카메라 fit 오차 %.2fpx (상한 2px 초과)" % float(fit["err_px"]))
        idxs = have.get(n, set())
        for k in (0, 1, 2):
            if k not in idxs or not os.path.exists(os.path.join(D, ("%02d.jpg" % n) if k == 0 else ("%02d_%d.jpg" % (n, k)))):
                miss.append("그림 idx%d 없음" % k); fixable["img"].append(n) if k else None
        if not os.path.exists(os.path.join(D, "cmp", "%02d.png" % n)): miss.append("책↔화면 비교 증거(record_check) 없음")
        if s.get("camSrc") != "eye": miss.append("카메라 출처가 eye 가 아님(%s)" % s.get("camSrc"))
        if s.get("review"): warn.append("확인 필요(마무리 안 됨) 표시")
        rows.append((n, miss, warn))
    if fix:
        did = []
        for n in sorted(set(fixable["img"])):
            r = subprocess.run([sys.executable, "refs_rect.py", name, str(n)], cwd=HERE, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            did.append("%d번 홀라인 그림 다시 만듦(%s)" % (n, "성공" if r.returncode == 0 else "실패"))
        if fixable["note"]:
            r = subprocess.run([sys.executable, name + ".py"], cwd=HERE, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            did.append("작업 점검 블록 다시 계산(%s)" % ("성공" if r.returncode == 0 else "실패"))
        print("── 자동으로 채운 것 ──"); print("\n".join("  " + d for d in did) or "  (채울 것 없음)")
        print("  ※ 채운 뒤 `python build.py %s --write` 로 저장하고 이 점검을 다시 돌려 확인한다." % name)
    # 마무리 리마인드(체크리스트) 형식 — 빠진 것은 ☐, 추정/확인 필요 표시는 같은 종류끼리 묶어서 한 줄로
    by = {}
    for n, m, w in rows:
        for x in w: by.setdefault(x if not x.startswith("카메라 fit 오차") else "카메라 fit 오차 상한 초과", []).append((n, x))
    lines = ["━ 완성 마무리 점검 (만든 번호 %d개: %d~%d번) ━" % (len(made), made[0], made[-1])]
    miss_rows = [(n, m) for n, m, _ in rows if m]
    lines.append(("☐ 빠진 것 있음 — " + ", ".join("%d번" % n for n, _ in miss_rows)) if miss_rows else "☑ 빠진 것 없음(작업 점검·읽기 표·축·그림·비교 증거·카메라 출처)")
    for n, m in miss_rows:
        for x in m: lines.append("   ☐ %d번: %s" % (n, x))
    for key, lst in by.items():
        ns = ", ".join("%d" % n for n, _ in lst)
        detail = "" if not key.startswith("카메라 fit") else " (" + "; ".join("%d번 %s" % (n, x.split("오차 ")[1].split(" ")[0]) for n, x in lst) + ")"
        lines.append("⚠ %s — %s번%s" % (key, ns, detail))
    lines.append("※ 마무리한 번호는 번호판 파랑, 확인 필요(review)는 주황. 완료 버튼을 누르면 주황이 파랑으로 바뀐다.")
    out = chr(10).join(lines); print(out)
    with open(os.path.join(D, "final_audit.md"), "w", encoding="utf-8") as f: f.write(out)
    print("저장: refs/%s/final_audit.md" % name)

if __name__ == "__main__": main()
