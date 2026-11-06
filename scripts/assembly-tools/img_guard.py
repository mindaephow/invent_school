# 그림 DB 업로드 지킴이(2026-11-07, 큐보 부품결합규칙.md I1) — Claude Code Stop hook 용.
#   턴을 끝내기 직전에 "img_db": true 인 조립도의 로컬 그림(refs/<이름>/index.json)이 DB(ivs_assembly_refs)에 다 올라갔는지 보고,
#   안 올린 그림이 있으면 종료 코드 2 + 안내(stderr)로 턴 종료를 막아 올리게 한다(Claude 가 읽고 이어서 올린다).
#   무한 반복을 막으려고 stop_hook_active 면(이미 한 번 막았으면) 막지 않고 알리기만 한다. DB 를 못 읽으면 막지 않고 알린다.
#   직접 실행: python img_guard.py   (stdin 없이도 됨)
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, glob, subprocess
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    active = False
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
            if raw.strip(): active = bool(json.loads(raw).get("stop_hook_active"))
    except Exception:
        pass
    problems = []; notes = []
    for rp in sorted(glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "*_rules.json"))):
        try: rules = json.load(open(rp, encoding="utf-8"))
        except Exception: continue
        if not rules.get("img_db"): continue
        name = os.path.basename(rp)[:-len("_rules.json")]
        p = subprocess.run([sys.executable, os.path.join(HERE, "dbimgcheck.py"), name], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if not p.stdout.startswith("조립도"):
            notes.append("%s: DB 그림 비교를 못 했다(%s)" % (name, (p.stdout + p.stderr).strip()[:100])); continue
        for l in p.stdout.splitlines():
            if l.startswith("❌ 안 올림") and "없음" not in l: problems.append("%s — %s" % (name, l))
    if notes: print("⚠ " + " / ".join(notes), file=sys.stderr)
    if problems:
        msg = ("❌ 그림 DB 업로드가 안 됐다(규칙 I1: 만든 그림은 만든 자리에서 올린다 — 올리지 못한 그림이 남은 채 턴을 끝내지 않는다).\n  " + "\n  ".join(problems) +
               "\n→ refs/<이름>/ 을 public/_refs_tmp/<이름>/ 로 복사 → 로그인된 조립 보기 화면에서 __ivsRefsUpload(viewer_snippets.md 3) → python dbimgcheck.py <이름> 으로 0건 확인 → navigate 로 새로 불러와 🖼 장수 확인 → _refs_tmp 삭제. 로그인이 안 돼 못 올리면 그 사실을 보고에 적는다.")
        print(msg, file=sys.stderr)
        sys.exit(0 if active else 2)
    print("✅ 로컬 그림이 모두 DB 에 있다")

main()
