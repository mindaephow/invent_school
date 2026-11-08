# 끝까지 가지 지킴이(2026-11-09, 큐보 부품결합규칙.md B7) — Claude Code Stop hook.
#   "<이름> 완성해/진행해" 같은 지시를 받으면  python finish_guard.py on <이름>  으로 목표를 켠다(.finish_goal).
#   목표가 켜져 있으면 rulecheck 에 ❌ 번호가 남은 동안 턴 종료를 막는다(종료 코드 2 + 안내) — 막혀도 ⚠ 로 적고 계속 만든다.
#   ❌ 가 0개면 목표를 끄고 통과. 4번 연속 ❌ 개수가 안 줄면(진짜 막힘) 통과시키고 알린다. 사용자 질문에 답만 할 때는  python finish_guard.py off.
import asmpath
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, ".finish_goal"); S = os.path.join(HERE, ".finish_goal_state.json")
def bad_count(name):
    p = subprocess.run([sys.executable, os.path.join(HERE, "rulecheck.py"), name], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    m = re.search(r"합계: ❌ (\d+)번", p.stdout)
    return int(m.group(1)) if m else None
def main():
    a = sys.argv[1:]
    if a[:1] == ["on"] and len(a) > 1: open(G, "w", encoding="utf-8").write(a[1]); json.dump({"last": 10**6, "stalls": 0}, open(S, "w")); print("목표 켬:", a[1]); return
    if a[:1] == ["off"]:
        for f in (G, S):
            if os.path.exists(f): os.remove(f)
        print("목표 끔"); return
    if not os.path.exists(G): return
    name = open(G, encoding="utf-8").read().strip(); n = bad_count(name)
    if n is None: print("⚠ rulecheck 결과를 못 읽어 막지 않는다", file=sys.stderr); return
    if n == 0:
        os.remove(G); print("✅ %s 규칙 점검 ❌ 0 — 목표 끝" % name); return
    st = json.load(open(S)) if os.path.exists(S) else {"last": 10**6, "stalls": 0}
    st["stalls"] = 0 if n < st["last"] else st["stalls"] + 1; st["last"] = n; json.dump(st, open(S, "w"))
    if st["stalls"] >= 4: print("⚠ %s ❌ %d번이 4번 연속 안 줄어 막지 않는다 — 막힌 이유를 보고한다" % (name, n), file=sys.stderr); return
    print("❌ %s 규칙 점검에 ❌ %d번이 남았다 — 목표(완성)를 끝내기 전에 턴을 끝내지 않는다(B7). 막히면 읽기 표 판단과정에 ⚠ 로 적고 다음 번호로 계속 만든다. 질문·중간 보고로 끝내지 않는다." % (name, n), file=sys.stderr)
    sys.exit(2)
main()
