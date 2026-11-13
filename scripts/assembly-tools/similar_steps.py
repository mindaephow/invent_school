# 이전 조립도(새 규칙으로 다시 만든 기록 작업기록.jsonl 이 있고 현재 조립도보다 먼저 시작한 것)에서 "같은 부품이 새로 들어간 번호"의 이미지 작업을 찾아 보여 준다 (규칙 D15, 사용자 지시 2026-11-13: 비행기 8번이 같은 59프레임 판을 이미 풀어 두었는데 배틀로봇 8번에서 못 찾아 쓰고 격자에 몇 시간을 썼다).
#   python similar_steps.py <이름> <번호> [--부품 59프레임] [--자세히]
#   하는 일: 이 번호에 새로 놓인 부품마다(또는 --부품 으로 고른 부품), 이전 조립도의 번호 중 그 부품이 새로 들어간 번호를 모아 보여 준다 — 59프레임이면 이전 조립도에서 59프레임이 쓰인 곳.
#           각 번호의 같이 들어간 부품·격자 라벨·오차·만든 도구·카메라·격자·축선 그림(NN_1·NN_2)·읽기 표 링/풀이를 보여 준다. 점수·순위 없이 쓰인 번호를 전부 작업한 순서대로 한 줄씩 보여 준다(--자세히 는 링·풀이까지).
#   이전 조립도 = 새 규칙으로 다시 만든 기록(작업기록.jsonl)이 있고 현재 조립도보다 먼저 시작한 것(뒤에 만들 조립도는 아직 새 규칙이 적용되지 않았을 수 있어 보지 않는다).
#   쓰는 법: 같은 판·같은 구도면 그 번호가 쓴 방법(도구·모서리 읽는 법·카메라)을 그대로 따라 한다. 읽기만 하고 아무것도 쓰지 않는다. number_start 가 같은 목록을 보여 준다.
import asmpath  # 조립도 파일 자리 연결
import glob, json, os, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def _load(p, d=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return d

def _new_parts(step):
    return Counter((p.get("name") or p.get("n")) for p in (step.get("parts") or []) if (p.get("name") or p.get("n")))

def _all_assemblies():
    for f in glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "*_asm.json")):
        nm = os.path.basename(f)[:-len("_asm.json")]
        yield nm, f

def _worked_start(asm_file):
    """그 조립도를 새 규칙으로 다시 만들기 시작한 시각 — 작업기록.jsonl 의 가장 이른 기록(YYYY-MM-DD HH:MM). 기록이 없으면 None(아직 새 규칙으로 다시 만들지 않은 조립도)."""
    p = os.path.join(os.path.dirname(asm_file), "작업기록.jsonl"); ts = []
    try:
        for l in open(p, encoding="utf-8"):
            try: ts.append(json.loads(l).get("t"))
            except Exception: pass
    except Exception: return None
    ts = [x for x in ts if x]
    return min(ts) if ts else None

def _jaccard(a, b):
    if not a or not b: return 0.0
    ks = set(a) | set(b)
    inter = sum(min(a[k], b[k]) for k in ks); uni = sum(max(a[k], b[k]) for k in ks)
    return inter / uni if uni else 0.0

def find(name, k, limit=None, only=None):
    """{부품 이름: [(점수, 조립도, 번호, 정보dict)]} — 이 번호에 새로 들어간 부품마다, 그 부품이 새로 들어간 이전 조립도 번호(최대 limit). only 가 있으면 그 부품만."""
    mine = None; my_start = None
    for nm, f in _all_assemblies():
        if nm == name:
            steps = (_load(f, {}) or {}).get("steps", [])
            if 0 < k <= len(steps): mine = _new_parts(steps[k - 1])
            my_start = _worked_start(f)
    if not mine: return {}
    want = [p for p in mine if (not only or p in only)]
    out = {p: [] for p in want}
    for nm, f in _all_assemblies():
        if nm == name: continue
        _ws = _worked_start(f)
        if _ws is None or (my_start is not None and _ws >= my_start): continue   # 이전 조립도만(사용자 지시 2026-11-13): 새 규칙으로 다시 만든 기록(작업기록.jsonl)이 있고 이 조립도보다 먼저 시작한 것
        steps = (_load(f, {}) or {}).get("steps", [])
        read = _load(os.path.join(os.path.dirname(f), nm + "_read.json"), {}) or {}
        R = os.path.join(HERE, "refs", nm)
        for i, st in enumerate(steps, 1):
            np_ = _new_parts(st)
            for p in want:
                if p not in np_: continue
                fits = []
                for g in sorted(glob.glob(os.path.join(R, "fits", "%02d_*.json" % i))):
                    j = _load(g, {}) or {}
                    fits.append((os.path.basename(g)[3:-5], j.get("err_px"), j.get("tool") or "holefit", j.get("cols"), j.get("rows")))
                ax = (_load(os.path.join(R, "%02d_axes.json" % i), {}) or {}).get("fit") or {}
                imgs = [x for x in ("%02d_1.jpg" % i, "%02d_2.jpg" % i) if os.path.exists(os.path.join(R, x))]
                good = bool(fits) and any((e is not None and e <= 2.0) for _, e, *_ in fits)
                r = read.get(str(i)) or {}
                share = len(set(np_) & set(mine)) / max(1, len(set(np_) | set(mine)))   # 같이 새로 들어간 부품이 겹칠수록(같은 장면일수록) 위로
                out[p].append((_ws, nm, i, dict(
                    parts=dict(np_), fits=fits, cam=(ax.get("theta"), ax.get("phi"), ax.get("err_px")), imgs=imgs,
                    ring=str(r.get("링", ""))[:110], why=str(r.get("판단과정", ""))[:160], dir=os.path.relpath(R, HERE))))
    for p in out: out[p].sort(key=lambda x: (x[0], x[2]))   # 점수 없이 — 작업한 순서(조립도 시작 시각)·번호 순으로 전부
    return out

def show(name, k, limit=None, file=sys.stdout, only=None, detail=False):
    res = find(name, k, None, only)
    if not res: print("  (이 번호의 새 부품을 찾지 못했다)", file=file); return
    for p, hits in res.items():
        print("  ■ %s — 이전 조립도에서 이 부품이 새로 들어간 번호 %d개%s" % (p, len(hits), " (없음)" if not hits else " (작업한 순서)"), file=file)
        for _ws, nm, i, d in hits:
            fit = " · ".join("%s %s" % (l, ("%.2fpx" % e) if e is not None else "-") for l, e, t, c, r in d["fits"]) or "격자 없음"
            cam = ("θ%s φ%s" % (d["cam"][0], d["cam"][1])) if d["cam"][0] is not None else "카메라 없음"
            print("    ▸ %s %d번 | 같이 들어간 부품 %s | %s | %s | 그림 %s" % (nm, i, d["parts"], fit, cam, ",".join(x for x in d["imgs"]) or "없음"), file=file)
            if detail:
                if d["ring"]: print("        링: " + d["ring"], file=file)
                if d["why"]: print("        풀이: " + d["why"], file=file)
                print("        파일: %s/" % d["dir"], file=file)

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    only = None
    if "--부품" in sys.argv: only = [sys.argv[sys.argv.index("--부품") + 1]]
    detail = "--자세히" in sys.argv
    print("═══ %s %s번에 새로 들어가는 부품이 이전 조립도에서 쓰인 번호 (이미지 작업 참고 — D15) ═══" % (sys.argv[1], sys.argv[2]))
    show(sys.argv[1], int(sys.argv[2]), only=only, detail=detail)
