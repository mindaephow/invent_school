# 검사 파일 감시(CCTV) — 규칙을 지키는 검사 도구가 사용자가 마지막으로 확인한 상태에서 바뀌었는지 보여 준다.
#   python gate_watch.py            바뀐 파일과 바뀐 줄을 모두 보여 준다
#   python gate_watch.py --brief    한 줄 요약(번호 빌드 끝에 자동으로 붙는다)
#   python gate_watch.py --init     기준이 없을 때 마지막 커밋(git HEAD)의 검사 파일을 기준으로 만든다
#   python gate_watch.py --accept   지금 검사 파일을 사용자가 확인한 기준으로 저장한다 — 바뀐 내용을 보고 괜찮을 때 **사용자가** 돌린다
# 막지 않는다. 검사 파일을 고치면 고쳤다는 사실이 보고에 반드시 나오게 하는 것이 목적이다(사용자 지시 2026-10-14: 규칙을 우회하는 것을 CCTV 처럼 지켜본다).
# 한계: 기준 파일(gate_baseline/)도 같은 저장소에 있어 Claude 가 고칠 수 있다 — 기준은 사용자가 --accept 로 직접 저장해야 믿을 수 있다. 검사 결과에 적힌 "내용"이 정직한지는 이 도구로 알 수 없다.
import difflib, hashlib, json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = os.environ.get("GATE_BASELINE_DIR") or os.path.join(HERE, "gate_baseline")
# 규칙·검사를 판정하는 파일(저장소 루트 기준 경로)
GATES = ["scripts/assembly-tools/" + n for n in (
    "build.py", "rulecheck.py", "stepchecks.py", "number_start.py", "matecheck.py", "placecheck.py", "record_check.py",
    "holefit.py", "infer_grid.py", "axes_fit.py", "plate_match.py", "emit.py", "userdone.py", "check_local.js")] + [
    "public/design-verify.js", "public/design-mates.js", "public/design-collision.js", "public/design-faces.js", "public/design-insertion.js"]
flat = lambda rel: rel.replace("/", "__")
def read(path):
    try: return open(path, encoding="utf-8").read()
    except Exception: return None
def sha(t): return hashlib.sha256((t or "").encode("utf-8")).hexdigest()[:12]

def init_from_git():
    os.makedirs(BASE, exist_ok=True); n = 0
    for rel in GATES:
        r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + rel], capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0: open(os.path.join(BASE, flat(rel)), "w", encoding="utf-8", newline="").write(r.stdout); n += 1
    json.dump({"기준": "git HEAD(마지막 커밋)의 검사 파일", "저장": time.strftime("%Y-%m-%d %H:%M"), "개수": n}, open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return n

def accept_current():
    os.makedirs(BASE, exist_ok=True); n = 0
    for rel in GATES:
        t = read(os.path.join(ROOT, rel))
        if t is not None: open(os.path.join(BASE, flat(rel)), "w", encoding="utf-8", newline="").write(t); n += 1
    json.dump({"기준": "사용자가 확인한 현재 검사 파일(--accept)", "저장": time.strftime("%Y-%m-%d %H:%M"), "개수": n}, open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return n

def changes():
    out = []
    for rel in GATES:
        cur = read(os.path.join(ROOT, rel)); old = read(os.path.join(BASE, flat(rel)))
        if cur is None and old is None: continue
        if old is None: out.append((rel, "새 검사 파일(기준에 없음)", [])); continue
        if cur is None: out.append((rel, "검사 파일이 지워짐", [])); continue
        if cur.replace("\r\n", "\n") == old.replace("\r\n", "\n"): continue
        d = [l for l in difflib.unified_diff(old.replace("\r\n", "\n").splitlines(), cur.replace("\r\n", "\n").splitlines(), lineterm="", n=0) if l and l[0] in "+-" and not l.startswith(("+++", "---"))]
        out.append((rel, "%d줄 추가 · %d줄 삭제" % (sum(1 for l in d if l[0] == "+"), sum(1 for l in d if l[0] == "-")), d))
    return out

def main():
    a = sys.argv[1:]
    if "--accept" in a: print("검사 파일 %d개를 사용자가 확인한 기준으로 저장했다." % accept_current()); return
    if "--init" in a or not os.path.exists(os.path.join(BASE, "manifest.json")):
        if not os.path.exists(os.path.join(BASE, "manifest.json")) or "--init" in a:
            print("(기준이 없어 마지막 커밋의 검사 파일 %d개로 만들었다)" % init_from_git())
    mf = json.load(open(os.path.join(BASE, "manifest.json"), encoding="utf-8")); ch = changes()
    if "--brief" in a:
        if not ch: print("🔒 검사 파일 변경 없음 (기준: %s, %s)" % (mf.get("저장", "?"), mf.get("기준", "")))
        else: print("👁 검사 파일이 사용자 확인 기준(%s)에서 바뀌었다 — %d개: %s  ← python gate_watch.py 로 바뀐 줄을 본다" % (mf.get("저장", "?"), len(ch), ", ".join(os.path.basename(r) + "(" + s + ")" for r, s, _ in ch)))
        return
    print("═══ 검사 파일 감시(CCTV) — 기준: %s %s ═══" % (mf.get("저장", "?"), mf.get("기준", "")))
    if not ch: print("검사 파일 변경 없음."); return
    for rel, summ, d in ch:
        print("\n▶ %s — %s" % (rel, summ))
        for l in d[:30]: print("   " + l[:170])
        if len(d) > 30: print("   … 외 %d줄" % (len(d) - 30))
    print("\n바뀐 내용이 괜찮으면 사용자가: python gate_watch.py --accept")

main()
