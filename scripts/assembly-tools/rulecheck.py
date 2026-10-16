# 규칙 점검 — 번호마다 "규칙을 지켰는가"를 자동으로 판정해 표로 보여 준다(사용자 지시 2026-10-12 "점점 더 규칙을 잘 지키고 기능이 향상되게").
#   python rulecheck.py <이름> [번호 ...]      ❌ 가 하나라도 있으면 종료 코드 1
# 이 점검은 Claude 가 보고 문장으로 규칙 위반을 적고 지나가지 못하게 하려고 만들었다. 규칙을 어기면 이 표에 ❌ 로 남고, number_start 가 다음 번호를 막는다.
#   F 격자  판(프레임) 부품이 들어온 번호의 구멍 점(fits)은 holefit 가 기준(구멍 ≥40%, 평균 ≤2.0px, 최대 ≤4.5px)을 지켜 만든 것이어야 한다.
#           기준 완화 옵션을 쓴 격자(fits 의 "relaxed")·손으로 만든 격자("hand" 이거나 holefit 출처가 아님)는 ❌.
#   C 카메라 axes.json 의 fit.err_px ≤ 2.0, 점 4개 이상, "추정" 이 아니어야 한다. 아니면 ❌.
#   E 증거  사용자 ✓ 이거나 책↔화면 비교 증거의 지문이 지금 내용과 같아야 한다.
#   R 읽기 표 면·링·부품 칸이 채워져 있어야 한다.
#   P 증명  <이름>_rules.json 에 "overlay_proof": true 가 있으면 번호마다 refs/<이름>/NN_3.jpg(overlay_check.py 로 모델을 책 그림에 겹친 증명 그림)이 있어야 한다.
# 예외 승인: <이름>_approvals.json 에 {"<번호>": {"fits": "이유", "camera": "이유", "사용자 말씀": "사용자가 한 말 그대로"}} — "사용자 말씀" 이 없으면 인정하지 않는다. Claude 는 이 파일에 적지 않는다.
# <이름>_rules.json 에 "rulecheck": true 가 있는 조립도만 ❌ 로 막는다(없는 옛 조립도는 ⚠ 로만 표시).
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))

FIX = {
    "격자": "python holefit.py <이름> <번호> <라벨> <칸> <줄> <모서리 8개> [어두운판] 로 규칙대로 다시 만든다(옵션 추가·손으로 만든 격자 금지). 기준 미달(판이 가려 구멍이 일부만 보임)이면 멈추지 말고 python infer_grid.py <이름> <번호> <라벨> <칸> <줄> 모서리8개 --판 <앞번호>:<라벨> --거울 <대칭번호> 줄 --링 'x,y;…' 로 앞·뒤 번호·대칭·링 정보를 모아 유추한다(05_조립 0-1). 유추로도 가설이 하나로 안 갈릴 때만 멈추고 시도·수치·필요한 추가 근거를 보고한다.",
    "카메라": "python axes_fit.py <이름> <번호> <라벨> <칸> <줄> <칸방향> <줄방향> 로 그 번호 격자에서 계산한다(오차 ≤2px, 점 4개 이상). 격자가 ❌ 면 격자부터 해결한다.",
    "증거": "화면에서 책과 나란히 비교한 뒤 python record_check.py <이름> <번호> <캡처.png> \"<비교 결과>\" 로 증거를 남긴다(내용이 바뀌었으면 다시).",
    "증명": "python overlay_check.py <이름> <번호> 로 모델을 책 그림 위에 같은 카메라로 겹쳐 NN_3.jpg 를 만들고(점 오차 px), 부품 상자가 책 부품 위에 올라갔는지 눈으로 본 뒤 읽기 표 판단과정에 한 줄 적고 DB 에 올린다.",
    "읽기": "<이름>_read.json 의 그 번호 면·링·부품을 책에서 읽은 값으로 채운다.",
}

def first_bad(name):
    """규칙 미달(❌)이 있는 가장 앞 번호와 항목 목록 — number_start 가 \"먼저 해결할 일\"로 보여 준다. 없으면 None."""
    res, strict = check(name)
    if not strict: return None
    for k, items in res.items():
        bads = [(t, why) for s, t, why in items if s == "❌"]
        if bads: return k, bads
    return None

def load(p, d):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d

def check(name, only=None):
    asm = load(os.path.join(here, name + "_asm.json"), {"steps": []})["steps"]
    rules = load(os.path.join(here, name + "_rules.json"), {})
    strict = bool(rules.get("rulecheck"))
    approvals = load(os.path.join(here, name + "_approvals.json"), {})
    evid = load(os.path.join(here, name + "_evidence.json"), {})
    read = load(os.path.join(here, name + "_read.json"), {})
    try:
        import stepfp; fp = stepfp.fp
    except Exception: fp = lambda st: None
    done = set()
    try:
        import userdone, re as _re
        src = open(os.path.join(here, name + ".py"), encoding="utf-8").read()
        m = _re.search(r'Asm\("([^"]+)"', src); done = set(userdone.user_done(m.group(1))) if m else set()
    except (SystemExit, Exception): pass
    R = os.path.join(here, "refs", name); out = {}
    bad = "❌" if strict else "⚠"
    for k, st in enumerate(asm, 1):
        if only and k not in only: continue
        parts = st.get("parts") or []
        if st.get("noPart") or not (parts or st.get("moveMade")): continue
        items = []   # (기호, 항목, 이유)
        ap = approvals.get(str(k), {}) if isinstance(approvals.get(str(k), {}), dict) else {}
        if len(str(ap.get("사용자 말씀", "")).strip()) < 5: ap = {}   # 사용자 말씀(인용) 없는 승인은 인정하지 않는다
        # F 격자 ───────────────
        needs_grid = any("프레임" in (p.get("n") or "") for p in parts)
        fd = os.path.join(R, "fits"); fs = []
        if os.path.isdir(fd):
            for f in sorted(os.listdir(fd)):
                if f.startswith("%02d_" % k) and f.endswith(".json"): fs.append((f, load(os.path.join(fd, f), {})))
        if not needs_grid and not fs:
            items.append(("✅", "격자", "판 부품이 새로 들어오지 않음(해당 없음)"))
        elif not fs:
            items.append((bad, "격자", "판 부품이 있는데 구멍 점(fits)이 없음"))
        else:
            for fn, fj in fs:
                nm = str(fj.get("name", ""))
                if fj.get("tool") == "infer":   # 유추 격자(2026-10-13): 판이 가려져 holefit 기준(구멍 40%)을 못 채울 때 모든 근거를 합쳐 푼 격자 — 개수가 아니라 근거 일치도로 본다. ✅ 는 아니고 사용자 확인이 필요한 ⚠.
                    ev = fj.get("evidence") or {}; mean = fj.get("err_px"); mx = fj.get("max_err_px")
                    good = (ev.get("unique_ratio", 0) >= 1.3 and ev.get("visible_holes", 0) >= 8 and len(ev.get("anchors", [])) >= 3 and mean is not None and mean <= 2.5 and mx is not None and mx <= 4.5)
                    anc_only = ev.get("visible_holes", 0) == 0 and len(ev.get("anchors", [])) >= 6   # 앵커만 유추(사용자 지시 2026-10-13 "내가 체크한 거 필요 없다"): 선명한 구멍 없이 칸이 확정된 앵커 6곳 이상으로 푼 격자 — 앵커 잔차와 안정성(하나씩 빼도 theta·phi 변화 ≤0.05rad)으로 본다. 기준을 넘으면 ⚠(사용자 확인 권장, 진행은 막지 않음)
                    if anc_only:
                        stable = ev.get("loo_dtheta") is None or (ev.get("loo_dtheta", 9) <= 0.05 and ev.get("loo_dphi", 9) <= 0.05)   # 안정성 기록이 없는 옛 격자(28·29번)는 앵커 잔차만
                        good = ev.get("anchor_mean_px") is not None and ev["anchor_mean_px"] <= 2.5 and ev.get("anchor_max_px", 99) <= 4.5 and stable
                        why = "앵커만 유추 격자: 앵커 %d곳 평균 %s·최대 %s px, 하나씩 빼도 theta 변화 %s·phi 변화 %s rad, roll %s° — 사용자 확인 권장(진행은 막지 않음)" % (len(ev.get("anchors", [])), ev.get("anchor_mean_px"), ev.get("anchor_max_px"), ev.get("loo_dtheta"), ev.get("loo_dphi"), ev.get("roll_deg")) if good else "앵커만 유추 격자 근거 부족(앵커 %d곳 평균 %s·최대 %s px, 하나씩 빼면 theta 변화 %s·phi 변화 %s rad) — 앵커를 더 모은다" % (len(ev.get("anchors", [])), ev.get("anchor_mean_px"), ev.get("anchor_max_px"), ev.get("loo_dtheta"), ev.get("loo_dphi"))
                        items.append(("⚠" if good else bad, "격자 " + fn, why)); continue
                    why = "유추 격자(infer_grid): 선명한 구멍 %s개 평균 %s·최대 %s px, 앵커 %d곳 평균 %s px, 가설 유일 %s배, roll %s° — 사용자 확인 필요" % (ev.get("visible_holes"), mean, mx, len(ev.get("anchors", [])), ev.get("anchor_mean_px"), ev.get("unique_ratio"), ev.get("roll_deg")) if good else "유추 격자 근거 부족(유일성 %s·구멍 %s개·앵커 %d곳·평균 %s·최대 %s px) — 앵커·근거를 더 모은다" % (ev.get("unique_ratio"), ev.get("visible_holes"), len(ev.get("anchors", [])), mean, mx)
                    items.append(("⚠" if good else bad, "격자 " + fn, why)); continue
                if fj.get("relaxed"): why = "기준 완화 옵션(%s)으로 만든 격자 — holefit 기준을 그대로 지킨 것이 아님" % ", ".join(fj["relaxed"]); ok = False
                elif fj.get("hand") or ("holefit.py" not in nm and fj.get("tool") != "holefit"): why = "holefit 가 만든 격자가 아님(손으로 읽은 점·다른 도구) — 규칙 0번 위반"; ok = False
                else:
                    mean = fj.get("err_px"); mx = fj.get("max_err_px")
                    if mean is None:
                        mm = re.search(r"평균 ([\d.]+)px·최대 ([\d.]+)px", nm); mean, mx = (float(mm.group(1)), float(mm.group(2))) if mm else (None, None)
                    cells = max(1, int(fj.get("cols", 1)) * int(fj.get("rows", 1))); ratio = 1 - len(fj.get("est", [])) / cells
                    ok = mean is not None and mean <= 2.0 and mx <= 4.5 and ratio >= 0.4
                    why = "holefit 통과 격자(평균 %s·최대 %s px, 구멍 %d%%)" % (mean, mx, round(ratio * 100)) if ok else "holefit 기준 미달 또는 기록 없음(평균 %s·최대 %s px, 구멍 %d%%)" % (mean, mx, round(ratio * 100))
                if ok: items.append(("✅", "격자 " + fn, why))
                elif ap.get("fits"): items.append(("⚠", "격자 " + fn, "승인됨(사용자): " + str(ap["fits"]) + " — " + why))
                else: items.append((bad, "격자 " + fn, why))
        # C 카메라 ───────────────
        ax = load(os.path.join(R, "%02d_axes.json" % k), None)
        if ax is None: items.append((bad, "카메라", "축 파일(_axes.json)이 없음"))
        else:
            fit = ax.get("fit") or {}; e = fit.get("err_px"); pts = fit.get("points") or 0
            guess = ("추정" in json.dumps(fit, ensure_ascii=False)) or e is None or pts < 4
            if guess or (e is not None and e > 2.0):
                why = "카메라 값이 추정이거나 점이 4개 미만(점 %s, 오차 %s)" % (pts, e) if guess else "카메라 맞춘 오차 %.2fpx > 2.0px(축 계산 기준)" % e
                items.append(("⚠", "카메라", "승인됨(사용자): " + str(ap["camera"]) + " — " + why) if ap.get("camera") else (bad, "카메라", why))
            else: items.append(("✅", "카메라", "오차 %.2fpx, 점 %d개" % (e, pts)))
        # E 증거 ───────────────
        ev = evid.get(str(k))
        if k in done: items.append(("✅", "증거", "사용자 ✓"))
        elif ev and ev.get("fp") == fp(st): items.append(("✅", "증거", "책↔화면 비교 증거(지문 일치)"))
        elif ev: items.append((bad, "증거", "비교 뒤 내용이 바뀜 — 다시 비교한다"))
        else: items.append((bad, "증거", "비교 증거도 사용자 ✓ 도 없음"))
        # R 읽기 표 ───────────────
        r = read.get(str(k), {}); miss = [f for f in ("면", "링", "부품") if not str(r.get(f, "")).strip()]
        items.append(("✅", "읽기 표", "채워짐") if not miss else (bad, "읽기 표", "빈 칸: " + ", ".join(miss)))
        if rules.get("overlay_proof"):   # P 증명 — 책 그림 위 겹침 그림(NN_3.jpg)
            items.append(("✅", "증명", "겹침 그림 있음(NN_3.jpg)") if os.path.exists(os.path.join(R, "%02d_3.jpg" % k)) else (bad, "증명", "책 그림 위 겹침 그림(NN_3.jpg)이 없음 — overlay_check.py 로 만든다"))
        if k in done:   # 사용자가 화면에서 직접 ✓ 한 번호는 사용자 승인으로 본다(❌ → ⚠)
            items = [("⚠" if sym == "❌" else sym, t, ("사용자 ✓ 로 승인됨 — " + why) if sym == "❌" else why) for sym, t, why in items]
        out[k] = items
    return out, strict

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    name = sys.argv[1]; only = {int(a) for a in sys.argv[2:]} or None
    res, strict = check(name, only)
    nb = 0
    print("═══ %s 규칙 점검 (%s) ═══" % (name, "❌ 로 막는 조립도" if strict else "옛 조립도 — ⚠ 로만 표시"))
    for k, items in res.items():
        sym = "❌" if any(s == "❌" for s, _, _ in items) else ("⚠" if any(s == "⚠" for s, _, _ in items) else "✅")
        nb += sym == "❌"
        print("%2d번 %s  %s" % (k, sym, " · ".join("%s%s" % (s, t) for s, t, _ in items)))
        for s, t, why in items:
            if s != "✅":
                print("       %s %s — %s" % (s, t, why))
                if s == "❌": print("         → 해결: %s" % FIX.get(t.split()[0], "규칙 문서(05_조립.md)를 읽고 그 항목을 규칙대로 한다"))
    print("합계: ❌ %d번 / ⚠ %d번 / ✅ %d번" % (nb, sum(1 for it in res.values() if not any(s == "❌" for s, _, _ in it) and any(s == "⚠" for s, _, _ in it)), sum(1 for it in res.values() if all(s == "✅" for s, _, _ in it))))
    sys.exit(1 if nb else 0)

if __name__ == "__main__":
    main()
