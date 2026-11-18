# 감독 모드 환경 맞추기(2026-11-18, 사용자 지시 "새 PC 가 아니더라도 발명교실 조립을 시작하면 셋팅이 지금처럼") — 복사만 하고 몇 ms 안에 끝난다.
#   python supervisor_env.py        → 무엇을 맞췄는지 출력
# 하는 일: 저장소 원본을 Claude Code 가 읽는 자리로 복사한다(바뀐 것만).
#   ① Sonnet 작업자 정의  agents/cubo-worker.md        → ~/.claude/agents/cubo-worker.md (PC 전체 — 어느 폴더에서 연 세션이든 쓸 수 있다) · <저장소>/.claude/agents/
#   ② 조립도 입구 스킬    .claude/skills/cubo-assembly/SKILL.md → ~/.claude/skills/cubo-assembly/SKILL.md (PC 전체)
# 부르는 곳: setup_new_pc.py --only-ponytail(세션 시작 때 session_start.py 가 부름) · global_hook.py(다른 폴더에서 연 세션이 조립도 작업을 시작할 때, 세션마다 한 번).
# 주의: Claude Code 는 에이전트·스킬을 세션을 열 때 읽는다 — 처음 복사된 세션에서는 목록에 없을 수 있다. 그때 감독은 감독.md 의 "작업자가 목록에 없으면" 대로 부른다.
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HOME = os.path.join(os.path.expanduser("~"), ".claude")
PAIRS = [
    (os.path.join(HERE, "agents", "cubo-worker.md"), [os.path.join(HOME, "agents", "cubo-worker.md"), os.path.join(ROOT, ".claude", "agents", "cubo-worker.md")]),
    (os.path.join(ROOT, ".claude", "skills", "cubo-assembly", "SKILL.md"), [os.path.join(HOME, "skills", "cubo-assembly", "SKILL.md")]),
]

def install(quiet=False):
    made, bad = [], []
    for src, dsts in PAIRS:
        if not os.path.exists(src): bad.append("원본 없음: " + os.path.relpath(src, ROOT)); continue
        data = open(src, "rb").read()
        for d in dsts:
            try:
                if os.path.exists(d) and open(d, "rb").read() == data: continue
                os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(src, d); made.append(d)
            except OSError as e: bad.append("%s (%s)" % (d, e))
    if not quiet:
        for d in made: print("MADE", d)
        for b in bad: print("FAIL", b)
        if not made and not bad: print("OK   감독 모드 환경(cubo-worker 에이전트·cubo-assembly 스킬) 최신")
    return made, bad

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    _, bad = install(); sys.exit(1 if bad else 0)
