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
# 모든 조립도를 같은 기준으로 ❌ 로 막는다(옛 조립도 구분 삭제 2026-11-04).
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import json, os, re, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
here = os.path.dirname(os.path.abspath(__file__))

FIX = {
    "격자": "python holefit.py <이름> <번호> <라벨> <칸> <줄> <모서리 8개> [어두운판] 로 규칙대로 다시 만든다(옵션 추가·손으로 만든 격자 금지). 기준 미달(판이 가려 구멍이 일부만 보임)이면 멈추지 말고 python infer_grid.py <이름> <번호> <라벨> <칸> <줄> 모서리8개 --판 <앞번호>:<라벨> --거울 <대칭번호> 줄 --링 'x,y;…' 로 앞·뒤 번호·대칭·링 정보를 모아 유추한다(05_조립 0-1). 유추로도 가설이 하나로 안 갈리면 멈추지 말고 시도·수치를 읽기 표 판단과정에 ⚠ 로 적고 다음 번호로 간다(마지막 보고에서 모아 알린다).",
    "카메라": "python axes_fit.py <이름> <번호> <라벨> <칸> <줄> <칸방향> <줄방향> 로 그 번호 격자에서 계산한다(오차 ≤2px, 점 4개 이상). 격자가 ❌ 면 격자부터 해결한다.",
    "증거": "화면에서 책과 나란히 비교한 뒤 python record_check.py <이름> <번호> <캡처.png> \"<비교 결과>\" 로 증거를 남긴다(내용이 바뀌었으면 다시).",
    "증명": "python overlay_check.py <이름> <번호> 로 모델을 책 그림 위에 같은 카메라로 겹쳐 NN_3.jpg 를 만들고(점 오차 px), 부품 상자가 책 부품 위에 올라갔는지 눈으로 본 뒤 읽기 표 판단과정에 한 줄 적고 DB 에 올린다.",
    "읽기": "<이름>_read.json 의 그 번호 면·링·부품을 책에서 읽은 값으로 채운다.",
}

# 필수 산출물(D14) — 번호를 끝내려면 모두 ✅(또는 사유 있는 ⚠)여야 하는 항목. number_start(앞 번호 게이트)·record_check(증거 받기 전)·build(--write 게이트·끝 요약)·quick_obs 가 이 정의 하나만 쓴다.
ARTIFACTS = ("격자", "양쪽 홀라인", "홀라인 그림", "링 대조", "카메라", "읽기 표", "그림DB")   # 증거·점검 칩은 산출물이 아니라 산출물 위에서 남기는 확인이라 뺀다

def is_artifact(item):
    return any(item == a or item.startswith(a + " ") for a in ARTIFACTS)   # "격자 08_B.json" 처럼 뒤에 파일 이름이 붙은 항목도 포함

def missing_artifacts(name, k, res=None):
    """번호 k 의 빠진 필수 산출물 [(항목, 이유)] — ❌ 인 것만(⚠ 는 사유가 적힌 미달이라 빠진 것이 아니다)."""
    res = res if res is not None else check(name, only=[k])[0]
    return [(t, why) for s, t, why in res.get(k, []) if s == "❌" and is_artifact(t)]

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
    strict = True
    _dbmiss = {}   # 번호 → 안 올린 그림 목록(None = 점검 실패). img_db 를 켠 조립도만 본다.
    if rules.get("img_db"):
        import subprocess, re
        _p = subprocess.run([sys.executable, os.path.join(here, "dbimgcheck.py"), name], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if not _p.stdout.startswith("조립도"): _dbmiss = None
        else:
            for _l in _p.stdout.splitlines():
                if _l.startswith("❌ 안 올림") and "없음" not in _l:
                    for _m in re.findall(r"(\d+)_(\d+)", _l.split(":", 1)[1]): _dbmiss.setdefault(int(_m[0]), set()).add("%s_%s" % _m)
    approvals = load(os.path.join(here, name + "_approvals.json"), {})
    evid = load(os.path.join(here, name + "_evidence.json"), {})
    read = load(os.path.join(here, name + "_read.json"), {})
    verif = load(os.path.join(here, name + "_verify.json"), {})   # 왼쪽 점검 칩 기록(verify_step.py, record_check.py 가 자동으로 돌린다)
    try:
        import stepfp; fp = stepfp.fp; same_ev = lambda e, st: stepfp.same(e, st, asm)
    except Exception: fp = lambda st: None; same_ev = lambda e, st: False
    done = set()
    try:
        import userdone, re as _re
        src = open(os.path.join(here, name + ".py"), encoding="utf-8").read()
        m = _re.search(r'''Asm\(\s*["']([^"']+)["']''', src); done = set(userdone.user_done(m.group(1))) if m else set()
    except (SystemExit, Exception): pass
    R = os.path.join(here, "refs", name); out = {}
    _imgidx = {}   # 번호 → 그림 목록 idx 집합(refs/<이름>/index.json) — 홀라인 그림(1·2번) 확인용
    try:
        for _r in load(os.path.join(R, "index.json"), []): _imgidx.setdefault(int(_r["step"]), set()).add(int(_r["idx"]))
    except Exception: pass
    bad = "❌" if strict else "⚠"
    for k, st in enumerate(asm, 1):
        if only and k not in only: continue
        parts = st.get("parts") or []
        _worked = bool(st.get("madeNoPart")) and (str(k) in evid or any(re.match(r"%02d_[A-Za-z0-9]+\.json$" % k, x) for x in (os.listdir(os.path.join(R, "fits")) if os.path.isdir(os.path.join(R, "fits")) else [])))   # 합치는 번호(새 부품 없음)도 작업을 시작했으면(격자·증거 있음) 같은 점검 대상 — 안 시작한 번호는 새로 막지 않는다(2026-11-09 3륜바이크 4·7번 증거 ❌ 가 verify_step 에서 안 풀림)
        if st.get("noPart") or not (parts or st.get("moveMade") or _worked): continue
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
                if fj.get("tool") == "sil-fit":   # 어두운 블록·막대만 있는 번호(2026-10-31 steercar 4번): 눈으로 점을 읽으면 평균 6px 로 흔들려 mkfit3d 기준(2.5px)을 못 채우므로, 책 그림의 부품 실루엣과 모델 실루엣의 겹침(IoU)을 최대로 하는 카메라를 자동으로 푼다(점을 읽지 않는다). 기준 IoU ≥0.85, 통과해도 사용자 확인 권장 ⚠.
                    ev = fj.get("evidence") or {}; iou = ev.get("iou")
                    good = iou is not None and iou >= 0.85
                    why = ("실루엣 겹침 격자(silfit): 책 그림↔모델 실루엣 IoU %s(자동, 눈으로 점을 읽지 않음) — 사용자 확인 권장" % iou) if good else ("실루엣 겹침 격자 근거 부족(IoU %s < 0.85)" % iou)
                    items.append(("⚠" if good else bad, "격자 " + fn, why)); continue
                if fj.get("tool") == "infer3d":   # 판이 없는 번호(블록·막대만 있는 번호)의 격자(2026-10-31 사용자 "문제가 해결 안 되게 만든 규칙은 바꿔라"): 격자를 만들 판이 없어 mkfit3d.py 가 모델에서 3D 가 확정된 점(돌기 끝·구멍·리벳 끝)을 책 픽셀과 짝지어 PnP 로 푼다. holefit 가 아니라는 이유로 막던 것을 infer 앵커와 같은 기준으로 인정한다(3D 점 ≥6·평균 ≤2.5·최대 ≤4.5px) — 통과해도 사용자 확인 권장 ⚠.
                    n3 = len(fj.get("xyz3d") or []); mean = fj.get("err_px"); mx = fj.get("max_err_px")
                    good = (n3 >= 6 and mean is not None and mean <= 2.5 and mx is not None and mx <= 4.5)
                    soft = (not good) and (not needs_grid) and n3 >= 4 and mean is not None and mx is not None   # 판(프레임)이 없는 번호는 같은 평면에서 잴 수 있는 점이 4~5개뿐일 수 있다 — ❌ 가 아니라 ⚠(화면 비교로 확인, 사용자 지시 2026-11-08)
                    if soft: good = True
                    why = ("3D 점 PnP 격자(mkfit3d.py): 3D 확정 점 %d개 평균 %s·최대 %s px — 사용자 확인 권장%s" % (n3, mean, mx, "(판 없는 번호라 점 %d개뿐 — 화면 비교로 확인)" % n3 if soft else "")) if good else ("3D 점 PnP 격자 근거 부족(3D 점 %d개·평균 %s·최대 %s px — 점 ≥6·평균 ≤2.5·최대 ≤4.5 필요)" % (n3, mean, mx))
                    items.append(("⚠" if good else bad, "격자 " + fn, why)); continue
                if fj.get("tool") == "line-fit":   # 한 줄 부품(1×N 막대) 격자(2026-10-31 사용자 "한 줄 부품이 많은데 통과 못 하게 만든 규칙부터 잘못"): holefit 는 한 줄이면 호모그래피를 못 구한다 → line_fit.py 가 같은 번호 판 격자의 카메라로 막대 위치를 풀어 만든다. 기준은 infer 앵커와 같은 값(읽은 구멍 ≥6·평균 ≤2.5·최대 ≤4.5px·기준 격자 ≤2.5px) — 통과해도 사용자 확인 권장 ⚠.
                    ev = fj.get("evidence") or {}; mean = fj.get("err_px"); mx = fj.get("max_err_px")
                    good = (ev.get("readings", 0) >= 6 and mean is not None and mean <= 2.5 and mx is not None and mx <= 4.5 and ev.get("camera_err_px", 99) <= 2.5)
                    why = ("한 줄 부품 격자(line_fit.py): 읽은 구멍 %s개 평균 %s·최대 %s px, 카메라 = %s(오차 %s px) — 사용자 확인 권장" % (ev.get("readings"), mean, mx, ev.get("camera_from"), ev.get("camera_err_px"))) if good else ("한 줄 부품 격자 근거 부족(읽은 구멍 %s개·평균 %s·최대 %s px·카메라 오차 %s px — 읽은 구멍 ≥6·평균 ≤2.5·최대 ≤4.5·카메라 ≤2.5 필요)" % (ev.get("readings"), mean, mx, ev.get("camera_err_px")))
                    items.append(("⚠" if good else bad, "격자 " + fn, why)); continue
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
            _sil = None   # 실루엣 겹침으로 푼 카메라(2026-10-31, silfit): 점을 읽지 않으므로 점 수·px 오차 대신 겹침 IoU ≥0.85 로 본다
            try:
                _gf = load(os.path.join(R, "fits", fit.get("from", "")), {}) if fit.get("from") else {}
                if _gf.get("tool") == "sil-fit": _sil = (_gf.get("evidence") or {}).get("iou")
            except Exception: _sil = None
            guess = ("추정" in json.dumps(fit, ensure_ascii=False)) or e is None or pts < 4
            if _sil is not None:
                items.append(("✅" if _sil >= 0.85 else bad, "카메라", "실루엣 겹침 IoU %.3f(기준 ≥0.85, 자동 — 점을 읽지 않음)" % _sil))
            elif guess or (e is not None and e > 2.0):
                why = "카메라 값이 추정이거나 점이 4개 미만(점 %s, 오차 %s)" % (pts, e) if guess else "카메라 맞춘 오차 %.2fpx > 2.0px(축 계산 기준)" % e
                if not guess and pts >= 4: items.append(("⚠", "카메라", why + " — 사진 구도 맞추기(규칙 E11, 사용자 지시 2026-11-11): px 오차로 막지 않는다. 구도만 비슷하면 되고 화면 비교(record_check 증거)로 확인"))
                else: items.append(("⚠", "카메라", "승인됨(사용자): " + str(ap["camera"]) + " — " + why) if ap.get("camera") else (bad, "카메라", why))
            else: items.append(("✅", "카메라", "오차 %.2fpx, 점 %d개" % (e, pts)))
        # E 증거 ───────────────
        ev = evid.get(str(k))
        if k in done: items.append(("✅", "증거", "사용자 ✓"))
        elif ev and same_ev(ev, st): items.append(("✅", "증거", "책↔화면 비교 증거(지문 일치)"))
        elif ev: items.append((bad, "증거", "비교 뒤 내용이 바뀜 — 다시 비교한다"))
        else: items.append((bad, "증거", "비교 증거도 사용자 ✓ 도 없음"))
        # R 읽기 표 ───────────────
        try:   # H 결합 전 높이 — 리벳이 받는 판보다 가까이 떠야 한다(G12). 저장된 hover 수치로 계산한다(hovercheck.py)
            import hovercheck; _hb, _hp, _hs = hovercheck.check_steps(asm, {k})
            if _hb: items.append((bad, "결합전 높이", "; ".join(m for _, m in _hb)))
            elif _hp: items.append(("✅", "결합전 높이", "리벳↔판 %d쌍 hover 순서 맞음" % _hp))
            elif _hs: items.append(("⚠", "결합전 높이", "점검 안 됨 — " + _hs[0][1] + "(화면에서 직접 본다)"))
        except Exception as _e: items.append(("⚠", "결합전 높이", "점검 실패: %s" % _e))
        try:   # G 화살표 끝점 — 화면이 그리는 화살표 꼬리·끝이 부품 끝·구멍에 닿는지(guidecheck.py, 뷰어 공식 그대로)
            if "_gc" not in globals() or _gc[0] != name:
                import guidecheck; globals()["_gc"] = (name, guidecheck.run(name))
            _gb, _gn, _gs = _gc[1]; _mine = [m for kk, m in _gb if kk == k]
            if _mine: items.append((bad, "화살표 끝점", "; ".join(_mine[:3])))
            elif any(kk == k for kk, _ in _gs): items.append(("⚠", "화살표 끝점", "점검 안 됨 — " + next(w for kk, w in _gs if kk == k) + "(화면에서 직접 본다)"))
            else: items.append(("✅", "화살표 끝점", "뷰어 공식으로 계산해 맞음"))
        except Exception as _e: items.append(("⚠", "화살표 끝점", "점검 실패: %s" % _e))
        r = read.get(str(k), {}); miss = [f for f in ("면", "링", "부품") if not str(r.get(f, "")).strip()]
        items.append(("✅", "읽기 표", "채워짐") if not miss else (bad, "읽기 표", "빈 칸: " + ", ".join(miss)))
        if rules.get("holeline_img") and fs:   # D14 홀라인 그림 — 격자(fits)가 있으면 격자·축선 그림(1·2번, refs_rect)을 만들어 DB 에 올려야 끝난 것이다(2026-11-13 배틀로봇 13~22번이 이 그림 없이 ✅ 로 보고됨)
            _need = [i for i in (1, 2) if i not in _imgidx.get(k, set())]
            items.append(("✅", "홀라인 그림", "격자·축선 그림 1·2번 있음") if not _need else (bad, "홀라인 그림", "격자(fits)는 있는데 격자·축선 그림 %s번이 없음 — python refs_rect.py %s %d 로 만들고 DB 에 올린다(D14)" % ("·".join(map(str, _need)), name, k)))
        if rules.get("img_db"):   # I 그림 DB — 만든 그림은 만든 자리에서 올린다(큐보 부품결합규칙.md I1). 점검이 실패하면 ✅ 로 두지 않는다.
            if _dbmiss is None: items.append(("⚠", "그림DB", "DB 그림 비교를 못 했다(dbimgcheck 실패) — python dbimgcheck.py %s 로 직접 본다" % name))
            elif k in _dbmiss: items.append((bad, "그림DB", "로컬 그림이 DB 에 없음: %s — 올리고(viewer_snippets.md 3) 화면을 새로 불러와 🖼 장수를 확인한다" % ", ".join(sorted(_dbmiss[k]))))
            else: items.append(("✅", "그림DB", "로컬 그림이 모두 DB 에 있음"))
        if rules.get("ring_cells") and glob.glob(os.path.join(R, "fits", "%02d_*.json" % k)):   # 책 링 ↔ 칸·줄 대조(cellmap.py, 사용자 지시 2026-11-10): 격자는 카메라만 풀려는 것이 아니라 링이 몇 칸·몇 줄 구멍인지 정해 모델의 결합 구멍과 맞추려는 것이다(D2·D4·D8)
            items.append(("✅", "링 대조", "책 링↔칸·줄 대조 그림 있음(NN_4)") if os.path.exists(os.path.join(R, "%02d_4.jpg" % k)) else (bad, "링 대조", "책 링↔칸·줄 대조 그림(NN_4.jpg)이 없음 — python cellmap.py %s %d 로 만들어 읽기 표 '링'·모델 결합 구멍과 맞춘다(record_check.py 가 자동으로 돌린다)" % (name, k)))
        if rules.get("both_holelines") and k >= int(rules.get("both_holelines_from", 1)) and glob.glob(os.path.join(R, "fits", "%02d_*.json" % k)):   # 양쪽 홀라인(규칙 0번 체크리스트 3, D2, 사용자 지시 2026-11-10): 받는 쪽·끼우는 쪽 구멍 격자를 모두 만든다 — 한쪽뿐이면 ❌, 못 만든 이유를 판단과정에 "⚠ 양쪽" 으로 적으면 ⚠
            _nf = len(glob.glob(os.path.join(R, "fits", "%02d_*.json" % k)))
            _why = str((read.get(str(k)) or {}).get("판단과정", ""))
            if _nf >= 2: items.append(("✅", "양쪽 홀라인", "격자 %d개" % _nf))
            elif "⚠ 양쪽" in _why: items.append(("⚠", "양쪽 홀라인", "격자 1개뿐 — 판단과정에 사유 있음"))
            else: items.append((bad, "양쪽 홀라인", "격자가 1개뿐 — 받는 쪽과 끼우는 쪽 둘 다 crop_ticks→holefit 로 만든다(D2). 가려져 못 만들면 시도·수치를 읽기 표 판단과정에 '⚠ 양쪽 …' 으로 적는다"))
        if rules.get("chips_verify"):   # 왼쪽 점검 칩(규칙 가-0 다-3, 사용자 지시 2026-11-10) — 칩 기록이 없거나 번호를 고친 뒤 안 돌렸으면 ❌: 그 번호는 끝난 것이 아니다
            _vr = verif.get(str(k)) if isinstance(verif, dict) else None
            if not _vr: items.append((bad, "점검 칩", "verify_step 기록 없음(왼쪽 칩이 회색) — python verify_step.py %s %d (record_check.py 가 자동으로 돌린다)" % (name, k)))
            elif fp(st) is not None and _vr.get("지문") != fp(st): items.append((bad, "점검 칩", "점검 뒤 번호 내용이 바뀜(낡음) — python verify_step.py %s %d 를 다시 돌린다" % (name, k)))
            else: items.append(("✅" if _vr.get("상태") == "통과" else "⚠", "점검 칩", "상태 %s — %s" % (_vr.get("상태"), ", ".join("%s %s" % (a, {"ok": "✅", "warn": "⚠", "fail": "❌"}.get(b, b)) for a, b in (_vr.get("항목") or {}).items() if b != "ok") or "전부 ✅")))
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
    print("═══ %s 규칙 점검 (%s) ═══" % (name, "❌ 로 막는 조립도"))
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
