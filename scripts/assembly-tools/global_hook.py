"""발명교실 조립도 훅 중계(사용자 지시 2026-11-10 — "발명교실 조립도를 시작하면 적용되게": 폴더 상관없이 어느 세션에서든).
프로젝트 .claude/settings.json 의 훅(종료 지킴이·사다리 관문·범위 관문·자동 점검)은 invent_school 폴더에서 연 세션에만 걸린다.
이 파일은 사용자 전체 설정(~/.claude/settings.json)에 stop|pre|post 로 연결해 두고, 아래 조건일 때만 기존 훅 스크립트를 대신 부른다.
  ① 세션 폴더(cwd)가 invent_school 밖이다(안이면 프로젝트 settings.json 훅이 이미 돈다 — 두 번 돌지 않게 여기서는 건너뛴다).
  ② 이 세션이 실제로 조립도 작업을 하고 있다 — stop: 대화 기록에 assembly-tools 경로가 있다 / pre·post: 이번 도구 호출이 invent_school·assembly-tools 를 건드린다.
  그 밖의 세션(다른 프로젝트)에는 아무 영향이 없다(종료 코드 0).
  GLOBAL_HOOK_DRYRUN=1 이면 부를 훅만 출력하고 실행하지 않는다(검사용)."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_RAW = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.normcase(ROOT_RAW) + os.sep
KIND = sys.argv[1] if len(sys.argv) > 1 else ""
HOOKS = {
    "stop": [[sys.executable, os.path.join(HERE, "finish_guard.py")]],
    "pre": [["node", os.path.join(ROOT_RAW, ".claude", "ponytail", "hooks", "ladder-gate.js")], [sys.executable, os.path.join(HERE, "scope_guard.py")]],
    "post": [[sys.executable, os.path.join(HERE, "autocheck.py")]],
}


def inside(p):
    return bool(p) and (os.path.normcase(os.path.abspath(p)) + os.sep).startswith(ROOT)


def touches(ev):
    if KIND == "stop":
        try:
            return "assembly-tools" in open(ev.get("transcript_path") or "", encoding="utf-8", errors="ignore").read()
        except OSError:
            return False
    s = json.dumps(ev.get("tool_input") or {}, ensure_ascii=False)
    return "invent_school" in s or "assembly-tools" in s


def main():
    raw = sys.stdin.buffer.read()
    try:
        ev = json.loads(raw.decode("utf-8"))
    except ValueError:
        return 0
    if KIND not in HOOKS or inside(ev.get("cwd")) or not touches(ev):
        return 0
    code = 0
    for cmd in HOOKS[KIND]:
        if os.environ.get("GLOBAL_HOOK_DRYRUN"):
            print("실행:", " ".join(cmd))
            continue
        p = subprocess.run(cmd, input=raw, capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        sys.stdout.buffer.write(p.stdout); sys.stderr.buffer.write(p.stderr)
        if p.returncode == 2:
            code = 2   # 막는 훅(종료 코드 2)은 그대로 전달한다
    return code


sys.exit(main())
