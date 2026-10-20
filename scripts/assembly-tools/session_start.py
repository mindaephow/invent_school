"""세션 시작 한 방: 최신 받기 + 메모리 규칙 맞추기 (새 세션·다른 PC 에서 맨 먼저 돌린다).
  cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python session_start.py
1) git fetch → 작업트리가 깨끗하고 뒤처졌으면 fast-forward 로 받는다(더럽거나 갈라졌으면 건드리지 않고 알린다).
2) sync_memory_rules.py --pull 로 저장소의 메모리 규칙을 이 PC 메모리에 반영한다.
3) 현재 커밋과 필독 목록 위치를 출력한다. (푸시는 하지 않는다 — 사용자가 "업로드"라 할 때만)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def git(*a):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


rc, out = git("fetch", "origin")
if rc:
    print("[git] fetch 실패 — 네트워크/원격 확인:", out)
else:
    _, br = git("rev-parse", "--abbrev-ref", "HEAD")
    _, dirty = git("status", "--porcelain")
    _, counts = git("rev-list", "--left-right", "--count", f"HEAD...origin/{br}")
    ahead, behind = (int(x) for x in counts.split()) if counts.replace("\t", " ").split()[0].isdigit() else (0, 0)
    if behind == 0:
        print(f"[git] 최신입니다 ({br}, 로컬에만 있는 커밋 {ahead}개)")
    elif dirty or ahead:
        print(f"[git] 원격보다 {behind}커밋 뒤처졌지만 자동으로 안 받음 "
              f"({'작업트리에 변경 있음' if dirty else ''}{' · ' if dirty and ahead else ''}{f'로컬에만 있는 커밋 {ahead}개' if ahead else ''})"
              " → 사용자에게 보고하고 정리 후 받는다")
    else:
        rc, out = git("merge", "--ff-only", f"origin/{br}")
        print(f"[git] {behind}커밋 받음 (fast-forward)" if rc == 0 else f"[git] 받기 실패: {out}")

_, last = git("log", "-1", "--format=%h %s")
print("[git] 현재:", last)

r = subprocess.run([sys.executable, os.path.join(HERE, "sync_memory_rules.py"), "--pull"],
                   cwd=HERE, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
print()
print("다음: process/메모리_규칙/INDEX.md 의 '필독' 파일을 읽고, 첫 보고에 '이번 번호에서 지킬 규칙 3개'를 적는다.")
sys.exit(r.returncode)
