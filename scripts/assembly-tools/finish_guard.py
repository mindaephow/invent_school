# 끝까지 가지 지킴이(2026-11-09, 큐보 부품결합규칙.md B7) — Claude Code Stop hook.
#   "<이름> 완성해/진행해" 같은 지시를 받으면  python finish_guard.py on <이름>  으로 목표를 켠다(.finish_goal).
#   목표가 켜져 있으면 rulecheck 에 ❌ 번호가 남은 동안 턴 종료를 막는다(종료 코드 2 + 안내) — 막혀도 ⚠ 로 적고 계속 만든다.
#   ❌ 가 0개면 목표를 끄고 통과. 60번 연속 ❌ 개수가 안 줄면(진짜 막힘) 통과시키고 알린다. 사용자 질문에 답만 할 때는  python finish_guard.py off.
#   처음부터 작동(2026-11-10): 목표를 손으로 켜지 않아도 작업 중인 조립도(.active_assembly, set_active.py)가 있으면 그것을 목표로 자동으로 켠다 —
#   목표를 안 켜서 턴이 중간에 끝나던 사고(오토건 2026-11-10)를 막는다. off 는 .finish_off 표시를 남겨 자동 켜짐도 끄고, on·set_active.py 가 지운다.
import asmpath
import sys, os, json, re, subprocess
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(HERE, ".finish_goal"); S = os.path.join(HERE, ".finish_goal_state.json")
OFF = os.path.join(HERE, ".finish_off"); ACTIVE = os.path.join(HERE, ".active_assembly"); UNTIL = os.path.join(HERE, ".finish_until")   # 사용자가 시킨 끝 번호("N번까지")
def bad_count(name):
    p = subprocess.run([sys.executable, os.path.join(HERE, "rulecheck.py"), name], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    m = re.search(r"합계: ❌ (\d+)번", p.stdout)
    return int(m.group(1)) if m else None
def main():
    a = sys.argv[1:]
    if a[:1] == ["on"] and len(a) > 1:
        if os.path.exists(OFF): os.remove(OFF)
        open(G, "w", encoding="utf-8").write(a[1]); json.dump({"last": 10**6, "stalls": 0}, open(S, "w")); print("목표 켬:", a[1]); return
    if a[:1] == ["until"] and len(a) > 1:   # python finish_guard.py until N — "N번까지" 지시: 작업 범위가 N 에 닿고 ❌ 가 0 일 때만 목표가 끝난다(꼬마기사 2026-11-14: 1번도 못 끝낸 채 ❌ 0 이라 멈춘 사고)
        open(UNTIL, "w", encoding="utf-8").write(a[1]); print("끝 번호:", a[1]); return
    if a[:1] == ["off"]:
        for f in (G, S, UNTIL):
            if os.path.exists(f): os.remove(f)
        open(OFF, "w", encoding="utf-8").write("질문 답만 — set_active.py 나 finish_guard.py on 으로 다시 켠다"); print("목표 끔"); return
    if not os.path.exists(G):
        if os.path.exists(OFF) or not os.path.exists(ACTIVE): return
        open(G, "w", encoding="utf-8").write(open(ACTIVE, encoding="utf-8").read().strip()); json.dump({"last": 10**6, "stalls": 0}, open(S, "w"))   # 작업 중인 조립도 = 목표(자동)
    name = open(G, encoding="utf-8").read().strip(); n = bad_count(name)
    if n is None: print("⚠ rulecheck 결과를 못 읽어 막지 않는다", file=sys.stderr); return
    if n == 0:
        try: until = int(open(UNTIL, encoding="utf-8").read().strip()) if os.path.exists(UNTIL) else 0
        except Exception: until = 0
        try: upto = json.load(open(os.path.join(HERE, "refs", name, "_worked_upto.json"), encoding="utf-8")).get("upto", 0)
        except Exception: upto = 0
        if until and upto < until:   # ❌ 가 0 인 것은 아직 시작 안 한 번호를 안 세서다 — 시킨 끝 번호까지 안 갔으면 끝이 아니다
            print("❌ %s 는 지시받은 %d번까지 가지 않았다(지금 %d번까지 시작) — 턴을 끝내지 않는다(B7). 막혀도 보고하지 말고 규칙 순서(C3 사다리)대로 다음 시도를 한다. 못 푼 것은 읽기 표 판단과정에 ⚠ 로 적고 다음 번호로 간다." % (name, until, upto), file=sys.stderr)
            sys.exit(2)
        os.remove(G); print("✅ %s 규칙 점검 ❌ 0 — 목표 끝" % name); return
    st = json.load(open(S)) if os.path.exists(S) else {"last": 10**6, "stalls": 0}
    st["stalls"] = 0 if n < st["last"] else st["stalls"] + 1; st["last"] = n; json.dump(st, open(S, "w"))
    if st["stalls"] >= 60: print("⚠ %s ❌ %d번이 60번 연속 안 줄어 막지 않는다 — 막힌 이유를 보고한다" % (name, n), file=sys.stderr); return
    print("❌ %s 규칙 점검에 ❌ %d번이 남았다 — 목표(완성)를 끝내기 전에 턴을 끝내지 않는다(B7). 막히면 읽기 표 판단과정에 ⚠ 로 적고 다음 번호로 계속 만든다. 질문·중간 보고로 끝내지 않는다." % (name, n), file=sys.stderr)
    sys.exit(2)
main()
