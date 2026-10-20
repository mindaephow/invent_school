# 조립도 만들 때 쓰는 기능(도구)별 점수 — 그 기능으로 만든 번호가 나중에 사용자 수정요청을 얼마나 받았는지로 매긴다 (2026-10-20 사용자 지시)
#   python feature_score.py [--write]      → 표를 출력, --write 면 feature_score.md 로 저장
# 기능 사용 = 파일 흔적(refs/<이름>/ 의 fits·NN_3·NN_6·cmp·axes·lv, <이름>_via.json) 으로 번호마다 자동 판정한다.
# 수정요청 = user_diffs/요청차이.md 의 "## 날짜 <조립도 이름> N번·M번~K번 — ..." 제목에 든 번호 + user_diffs/수정저장차이.md 의 "조립도 · N번 · 부품" 줄(사용자가 ❄ 자세를 고친 것).
# 점수 = (수정 없는 번호 + 3) / (쓴 번호 + 4) × 100  (표본이 적으면 75 점 쪽으로 당긴다). 수정요청 기록은 일부 조립도·번호만 있어서 "기록된 범위 안의" 점수다.
import sys, os, re, json, glob, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
KO = {"투석기": "catapult", "드롭체커": "dropchecker", "오토타깃": "autotarget", "스피드바이크": "speedbike", "사마귀": "mantis", "어보이더": "avoider", "배틀로봇": "battlerobot2", "강아지": "dog", "꼬마기사": "kidknight", "롤링봇": "rollingbot", "풍차": "windmill", "포뮬러": "formula1", "비행기": "airplane", "오토건": "autogun", "축구로봇": "soccer", "트라이크": "trike"}

def nums_from(txt):
    out = set()
    for a, b in re.findall(r"(\d+)\s*[~∼-]\s*(\d+)\s*번", txt): out.update(range(int(a), int(b) + 1))
    for grp in re.findall(r"((?:\d+\s*[·,]\s*)+\d+)\s*번", txt): out.update(int(x) for x in re.findall(r"\d+", grp))
    for n in re.findall(r"(?<![\d~·,])(\d+)\s*번", txt): out.add(int(n))
    return out

def corrections():
    fix = collections.defaultdict(set)   # 조립도 → 수정요청 받은 번호
    p = os.path.join(HERE, "user_diffs", "요청차이.md")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if not line.startswith("## "): continue
            for ko, en in KO.items():
                if ko in line:
                    seg = line.split(ko, 1)[1].split("—")[0]
                    fix[en] |= nums_from(seg)
    p = os.path.join(HERE, "user_diffs", "수정저장차이.md")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            m = re.match(r"- (\w+) · (\d+)번 · ", line.strip())
            if m: fix[m.group(1)].add(int(m.group(2)))
    return fix

def features_of(name, n):
    R = os.path.join(HERE, "refs", name); f = set()
    for fp in glob.glob(os.path.join(R, "fits", "%02d_*.json" % n)):
        try: tool = json.load(open(fp, encoding="utf-8")).get("tool", "holefit")
        except Exception: continue
        t = str(tool).lower()
        if t.startswith("holefit") or t == "(holefit)": f.add("홀라인 자동(holefit)")
        elif t.startswith("anchor"): f.add("앵커 점 PnP")
        elif t.startswith("ring"): f.add("링 중심 점")
        elif t.startswith("manual"): f.add("손으로 읽은 점(manual)")
        elif t.startswith("infer"): f.add("유추(infer_grid)")
        elif t.startswith("blob") or t.startswith("plate") or t.startswith("hole"): f.add("격자 보조(blob·plate_match)")
    if os.path.exists(os.path.join(R, "%02d_3.jpg" % n)): f.add("겹침 증명(overlay_check)")
    if os.path.exists(os.path.join(R, "%02d_6.jpg" % n)) or os.path.exists(os.path.join(R, "%02d_4.jpg" % n)): f.add("링↔구멍 대조 그림")
    if os.path.exists(os.path.join(R, "cmp", "%02d.png" % n)): f.add("책↔화면 비교 증거(record_check)")
    via = os.path.join(HERE, name + "_via.json")
    if os.path.exists(via):
        try:
            if str(n) in json.load(open(via, encoding="utf-8")): f.add("다음 번호 책 대조(via)")
        except Exception: pass
    ax = os.path.join(R, "%02d_axes.json" % n)
    if os.path.exists(ax):
        try:
            fit = json.load(open(ax, encoding="utf-8")).get("fit") or {}
            if fit: f.add("카메라 fit 오차 ≤2px" if float(fit.get("err_px", 99)) <= 2.0 else "카메라 fit 오차 >2px")
        except Exception: pass
    return f

def main():
    fix = corrections(); use = collections.defaultdict(lambda: [0, 0, []])   # 기능 → [쓴 번호, 수정 받은 번호, 수정 받은 목록]
    names = sorted(d for d in os.listdir(os.path.join(HERE, "refs")) if os.path.isdir(os.path.join(HERE, "refs", d)))
    for name in names:
        for fp in glob.glob(os.path.join(HERE, "refs", name, "[0-9][0-9]_axes.json")):
            n = int(os.path.basename(fp)[:2])
            for ft in features_of(name, n):
                u = use[ft]; u[0] += 1
                if n in fix.get(name, ()): u[1] += 1; u[2].append("%s %d" % (name, n))
    # 빠뜨렸을 때: 그 기능을 안 쓴 번호의 수정요청 비율(쓴 번호 비율과 비교) — 어떤 기능을 빠뜨리면 수정요청이 늘어나는지
    allnum = collections.defaultdict(set)
    for name in names:
        for fp in glob.glob(os.path.join(HERE, "refs", name, "[0-9][0-9]_axes.json")): allnum[name].add(int(os.path.basename(fp)[:2]))
    total = sum(len(v) for v in allnum.values()); total_bad = sum(len(fix.get(nm, set()) & v) for nm, v in allnum.items())
    miss = []
    for ft, (k, bad, lst) in use.items():
        wo, wo_bad = total - k, total_bad - bad
        miss.append((ft, bad / k * 100 if k else 0, wo_bad / wo * 100 if wo else 0, wo, wo_bad))
    rows = []
    for ft, (k, bad, lst) in use.items():
        rows.append(((k - bad + 3) / (k + 4) * 100, ft, k, bad, lst))
    rows.sort(reverse=True)
    out = ["# 조립도 기능 점수 (수정요청 기반, 기록된 범위 안)", "", "| 점수 | 기능 | 쓴 번호 | 수정요청 받은 번호 |", "|---|---|---|---|"]
    for sc, ft, k, bad, lst in rows: out.append("| %.0f | %s | %d | %d%s |" % (sc, ft, k, bad, (" — " + ", ".join(lst[:6]) + (" …" if len(lst) > 6 else "")) if lst else ""))
    out += ["", "수정요청이 기록된 조립도: " + ", ".join("%s(%d번)" % (k, len(v)) for k, v in sorted(fix.items())), "※ 점수 = (수정 없는 번호+3)/(쓴 번호+4)×100. 요청차이·수정저장차이 에 적힌 것만 수정요청으로 센다 — 기록이 없는 번호는 '문제 없음'으로 보인다(기록 범위의 한계)."]
    out += ["", "## 빠뜨리면 어떻게 되나 (쓴 번호 대비 안 쓴 번호의 수정요청 비율)", "", "| 기능 | 쓴 번호 수정률 | 안 쓴 번호 수정률 | 안 쓴 번호 수 | 차이 |", "|---|---|---|---|---|"]
    for ft, a, b, wo, wo_bad in sorted(miss, key=lambda t: t[2] - t[1], reverse=True): out.append("| %s | %.0f%% | %.0f%% (%d/%d) | %d | %+.0f%%p |" % (ft, a, b, wo_bad, wo, wo, b - a))
    # 어긴 규칙 유형(요청차이 항목 본문 키워드)
    TY = {"도구·절차를 건너뜀(눈대중·우회)": r"건너뛰|눈대중|눈으로|우회|도구를 바꿔", "확인 없이 맞다고 단정": r"단정|확인 없이|안 보고|짐작", "알고도 반영 안 함(앞뒤 번호·이미 있는 정보를 읽고도 적용 못 함 — 기능 미사용이 아님)": r"앞 번호|뒤 번호|다음 번호|앞뒤", "사용자 지정값 어김(되돌리기·덮어쓰기)": r"❄|📷|되돌리|덮어", "방향·기준 판독 오류": r"방향|거울|반대|뒤집|각도", "결합 상태(끝까지 안 꽂음·떨어짐)": r"끝까지|결합|헤드|떨어"}
    cnt = collections.Counter(); pth = os.path.join(HERE, "user_diffs", "요청차이.md"); body = open(pth, encoding="utf-8").read() if os.path.exists(pth) else ""
    for sec in re.split(r"(?m)^## ", body)[1:]:
        for t, rx in TY.items():
            if re.search(rx, sec): cnt[t] += 1
    out += ["", "## 어긴 규칙 유형 (요청차이 항목 수, 한 항목이 여러 유형에 걸칠 수 있음)", ""] + ["- %s: %d건" % (t, c) for t, c in cnt.most_common()]
    txt = "\n".join(out); print(txt)
    if "--write" in sys.argv: open(os.path.join(HERE, "feature_score.md"), "w", encoding="utf-8").write(txt + "\n"); print("\n저장: feature_score.md")

main()
