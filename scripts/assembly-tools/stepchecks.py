# 번호마다 한 일을 체크박스로 보여 준다(관리자 지시 2026-10-08) — 허락을 받는 장치가 아니라 "뭐뭐를 했다"를 화면(개발서버 단계 설명)에 ☑/☐ 로 적어 두고 넘어가게 하는 장치다.
# 사용: 조립 스크립트 끝(save_links 앞)에서  import stepchecks; stepchecks.apply(A, "dog")
#   - 번호마다 점검 항목을 계산해 그 번호 설명(note) 끝에 "━ 작업 점검 ━" 블록으로 붙인다(빌드할 때마다 새로 계산).
#   - 막는 항목(blocking)은 <이름>_checks.json 에 적고, build.py 가 --write 때 막는다: 격자 그림 없음, 읽기 표 빈칸, 읽기 표 부품 ≠ 모델 부품, 쓴 부품 합계가 LIST 를 넘음.
#   - 사람이 눈으로 하는 항목(화면 확인·책과 나란히 비교·카메라)은 <이름>_rules.json 의 view/count/camera 목록에 번호가 있으면 ☑.
import json, os, re, collections
MARK = "\n━ 작업 점검 ━"

def _counts(parts):
    c = collections.Counter(p.n for p in parts); return c

def _parse(txt):   # "315프레임 1, 3단블록 1" → Counter (이름에 숫자가 있어도 마지막 숫자가 개수)
    c = collections.Counter()
    for part in re.split(r"[,，]", str(txt)):
        m = re.match(r"\s*(.+?)\s+(\d+)\s*$", part)
        if m: c[m.group(1).strip()] += int(m.group(2))
    return c

def apply(A, name):
    here = os.path.dirname(os.path.abspath(__file__))
    lst = json.load(open(os.path.join(here, name + "_list.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_list.json")) else {}
    rd = json.load(open(os.path.join(here, name + "_read.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_read.json")) else {}
    rl = json.load(open(os.path.join(here, name + "_rules.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, name + "_rules.json")) else {}
    ip = os.path.join(here, "refs", name, "index.json")
    idx = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else []
    have = collections.defaultdict(dict)
    for r in idx: have[r["step"]][r["idx"]] = r.get("note", "")
    cum = collections.Counter(); blocking = []; rows = {}
    for k, st in enumerate(A.steps, 1):
        if not st.parts:
            continue
        cnt = _counts(st.parts); cum.update(cnt)
        items = []   # (필수 여부, 통과, 문구)
        h = have.get(k, {})
        plate = any("프레임" in p.n for p in st.parts)
        _fd = os.path.join(here, "refs", name, "fits")   # 격자 점 파일(fits/NN_<라벨>.json)이 있어야 격자를 만든 것이다 — 점 없이 선만 그은 그림을 격자로 세지 않는다(관리자 지적 2026-10-09: 43번에 격자 점이 없는데 ☑ 로 찍혔다)
        _has_fit = (not os.path.isdir(_fd)) or any(f_.startswith("%02d_" % k) and f_.endswith(".json") for f_ in os.listdir(_fd))
        grid_ok = (1 in h and 2 in h) and _has_fit
        items.append((True, grid_ok, ("책 그림 격자(수평선·회전·격자 점) 만듦" if _has_fit else "책 그림 격자 점이 없음(이미지만 있음)") if 2 in h else "책 그림 원본 확인(판이 없는 번호)"))
        r = rd.get(str(k)) or {}
        items.append((True, all(str(r.get(f, "")).strip() for f in ("면", "링", "부품")), "읽기 표(면·링·부품) 적음"))
        rp = _parse(r.get("부품", "")) if r.get("부품") else None
        same = rp is not None and dict(rp) == dict(cnt)
        items.append((True, same, "읽기 표의 부품 = 모델의 부품 (%s)" % ", ".join("%s %d" % kv for kv in cnt.items())))
        _dr = str(r.get("방향", "")).strip()   # 카메라 방향 파악(관리자 지시 2026-10-09: 계산은 못 해도 책 그림의 어느 쪽이 가깝고·오른쪽·위인지는 맞춘다). 25번부터 비어 있으면 막는다
        items.append((k >= 25, len(_dr) >= 12 and not _dr.startswith("미"), "카메라 방향 파악(가까운 쪽·화면 오른쪽·위가 로봇의 어느 쪽인지 읽기 표 '방향')"))
        over = {n: (cum[n], lst[n]) for n in cnt if n in lst and cum[n] > lst[n]}
        items.append((True, not over, "쓴 부품 합계 ≤ 교재 LIST" + ("" if not over else " — 초과: " + ", ".join("%s %d/%d" % (n, a, b) for n, (a, b) in over.items()))))
        _ori = str(r.get("부품방향", "")).strip()   # 부품 방향·제자리 판정(관리자 지시 2026-10-09): 새 부품의 위·바깥 면, 칸1 끝, 줄 방향, 부품 사이 좌우 관계, 그룹이 들어오는 방향·앉는 자세를 책 격자에서 읽어 적는다
        _oex = k in rl.get("orient_exempt", [])   # 면제 번호는 새 순서로 다시 점검할 때까지 통과로 친다(rules 의 orient_exempt 에서 지우면 점검 대상)
        items.append((bool(rl.get("orient_check")) and not _oex, (len(_ori) >= 20 and not _ori.startswith("미")) or _oex or not rl.get("orient_check"), "부품 방향·제자리 판정(읽기 표 '부품방향')" + (" — 면제(재점검 대기)" if _oex and rl.get("orient_check") else "")))
        _cmp = str(r.get("대조", "")).strip()   # 앞·뒤 번호 그림과 완성 사진(00)을 같이 보고 읽은 내용(관리자 지시 2026-10-08: 한 장만 보고 만들어 12번이 틀렸다). 10번부터는 비어 있으면 막는다(1~9번은 아직 안 한 것으로 표시만)
        items.append((k >= 10, len(_cmp) >= 10 and not _cmp.startswith("미"), "앞·뒤 번호 그림·완성 사진(00)과 같이 읽음(읽기 표 '대조')"))
        _strict = bool(rl.get("strict"))   # strict(관리자 지시 2026-10-10 "하지 않은 것을 하지 마"): 눈으로 하는 확인도 안 하면 막는다 — "안 했다고 보고"로 넘어가지 않는다
        items.append((_strict, k in rl.get("view", []), "화면 확대 확인"))
        items.append((_strict, k in rl.get("count", []), "책 그림과 나란히 비교(칸 수 대조)"))
        items.append((_strict, k in rl.get("camera", []), "카메라 책과 대조"))
        items.append((_strict, str(getattr(st, "camSrc", "guess")) != "guess", "카메라가 짐작(guess)이 아님 — 책 그림에서 가까운 쪽·오른쪽·위를 읽고 정한 값(camSrc eye)"))
        rows[k] = items
        for need, ok, txt in items:
            if need and not ok: blocking.append("%d번: %s" % (k, txt))
        last_built = max(i for i, st2 in enumerate(A.steps, 1) if st2.parts)
        if k < last_built:   # 앞 번호의 눈으로 하는 체크(화면 확인·책과 나란히 비교)를 미루고 다음 번호로 가지 못하게 한다(관리자 지시 2026-10-08: 체크를 뒤로 미룬다)
            for need, ok, txt in items:
                if (not need) and (not ok) and "카메라" not in txt and "대조" not in txt: blocking.append("%d번: %s — 다음 번호(%d번 이후)를 만들기 전에 해야 함" % (k, txt, k + 1))
        block = MARK + "\n" + "\n".join(("☑ " if ok else ("☐ " if not need else "☐ ")) + txt + ("" if need else " (눈으로)") for need, ok, txt in items)
        st.note = st.note.split(MARK)[0] + block
    left = {n: lst[n] - cum[n] for n in lst if lst[n] - cum[n] != 0 and n in cum or (n in lst and cum[n] == 0 and False)}
    json.dump({"blocking": blocking, "cum": dict(cum), "list_left": {n: lst[n] - cum.get(n, 0) for n in lst}}, open(os.path.join(here, name + "_checks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return blocking
