# 감독 모드 도구(2026-11-18) — Sonnet 작업자(cubo-worker)에게 줄 지시문을 만들고, 번호마다 감독 결과를 기록하고, 좋아지는지 추세를 본다. 규칙은 큐보/규칙/감독.md.
#   python supervise.py brief <이름> <번호> [--포트 3180] [--아이디 minsiljang0] [--메모 "…"]   작업자 지시문(감독이 Agent 호출에 그대로 넣는다)
#   python supervise.py add <이름> <번호> --판정 맞음|다름|못함 [--분 24] [--호출 90] [--저장 3] [--막힘 9] [--고침 "…"] [--메모 "…"]
#   python supervise.py show [<이름>]                                         번호별 기록과 추세(최근 5번호 vs 그 전)
# 기록은 저장소 큐보/규칙/감독기록.jsonl 에 쌓인다(git 으로 모든 PC 가 같이 본다).
import json, os, sys, time, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "큐보", "규칙", "감독기록.jsonl")

def opt(a, k, d=None):
    return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d

def load():
    if not os.path.exists(LOG): return []
    return [json.loads(l) for l in open(LOG, encoding="utf-8") if l.strip()]

def brief(name, n, a):
    import asmpath
    up = 0
    try: up = json.load(open(os.path.join(HERE, "refs", name, "_worked_upto.json"), encoding="utf-8")).get("upto", 0)
    except Exception: pass
    port = opt(a, "--포트", "3180"); uid = opt(a, "--아이디", "minsiljang0"); memo = opt(a, "--메모", "")
    try: prog = os.path.relpath(os.path.join(os.path.dirname(asmpath.resolve(name + ".py")), "진행기록.md"), HERE)
    except Exception: prog = "큐보/조립도/<권>권/%s/진행기록.md" % name
    lines = [
        "감독 지시: **%s %s번** 하나를 `3_번호하나.md` 대로 1~9단계 끝까지 만들고 멈춘 뒤 보고한다(cubo-worker 정의대로)." % (name, n),
        "- 저장소 C:\\Users\\user\\Downloads\\invent_school, 명령은 scripts/assembly-tools 에서. 인수인계 아이디: %s" % uid,
        "- 이 조립도는 %s — `handoff.py --시작` 은 돌리지 않는다(이미 진행 중이면 ✓·📷·❄ 가 지워진다). `set_active.py %s` 는 감독이 돌렸다. finish_guard 는 감독이 관리한다." % ("이미 진행 중(작업 범위 %d번까지)" % up if up else "처음 시작이다 — 그래도 `--시작` 은 감독이 돌린다", name),
        "- 화면: 사용자가 로그인한 브라우저 패널 탭 **http://localhost:%s** 만 쓴다(다른 포트로 옮기지 않는다)." % port,
        "- `number_start.py %s %s` 가 앞 번호 증거 때문에만 막히면 `--연속`." % (name, n),
        "- 진행기록: %s · 인수인계: 큐보/인수인계.md" % prog,
    ]
    if memo: lines.append("- 감독 메모: " + memo)
    lines.append("- 끝나면 cubo-worker 정의의 '최종 보고' 6가지 형식으로, 막힘 기록은 빠짐없이.")
    print("\n".join(lines))

def add(name, n, a):
    j = opt(a, "--판정")
    if j not in ("맞음", "다름", "못함"): sys.exit("--판정 은 맞음|다름|못함 중 하나")
    num = lambda k: (float(opt(a, k)) if opt(a, k) not in (None, "") else None)
    r = {"t": time.strftime("%Y-%m-%d %H:%M"), "조립도": name, "번호": int(n), "판정": j, "분": num("--분"), "호출": num("--호출"),
         "저장": num("--저장"), "막힘": num("--막힘"), "고침": opt(a, "--고침", ""), "메모": opt(a, "--메모", "")}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
    print("기록:", json.dumps(r, ensure_ascii=False))

def show(name):
    rows = [r for r in load() if not name or r["조립도"] == name]
    if not rows: print("기록 없음 — python supervise.py add … 로 번호마다 남긴다"); return
    print("%-10s %4s %4s %5s %5s %4s %4s  %s" % ("조립도", "번호", "판정", "분", "호출", "저장", "막힘", "고침"))
    for r in rows:
        f = lambda v: "-" if v is None else ("%g" % v)
        print("%-10s %4d %4s %5s %5s %4s %4s  %s" % (r["조립도"], r["번호"], r["판정"], f(r["분"]), f(r["호출"]), f(r["저장"]), f(r["막힘"]), r["고침"][:60]))
    def avg(rs, k):
        v = [r[k] for r in rs if r.get(k) is not None]; return ("%.1f" % st.mean(v)) if v else "-"
    last, prev = rows[-5:], rows[:-5]
    print("\n추세(최근 %d번호 / 그 전 %d번호): 분 %s / %s · 막힘 %s / %s · 저장 %s / %s · '다름' %d / %d" % (
        len(last), len(prev), avg(last, "분"), avg(prev, "분"), avg(last, "막힘"), avg(prev, "막힘"), avg(last, "저장"), avg(prev, "저장"),
        sum(r["판정"] == "다름" for r in last), sum(r["판정"] == "다름" for r in prev)))
    if len(last) >= 5 and all((r.get("막힘") or 0) <= 1 for r in last) and not any(r["판정"] != "맞음" for r in last):
        print("→ 최근 5번호가 막힘 ≤1·모두 맞음: 감독 간격을 늘릴지 사용자에게 제안할 때다(감독.md '사이클 줄이기').")

a = sys.argv[1:]
if not a: sys.exit(__doc__ if __doc__ else open(__file__, encoding="utf-8").read().split("\nimport")[0])
cmd = a[0]
if cmd == "brief" and len(a) >= 3: brief(a[1], a[2], a)
elif cmd == "add" and len(a) >= 3: add(a[1], a[2], a)
elif cmd == "show": show(a[1] if len(a) > 1 and not a[1].startswith("--") else None)
else: sys.exit(open(__file__, encoding="utf-8").read().split("\nimport")[0])
