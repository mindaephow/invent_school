"""세션 시작 한 방: 최신 받기 (새 세션·다른 PC 에서 맨 먼저 돌린다).
  cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python session_start.py
1) git fetch → 작업트리가 깨끗하고 뒤처졌으면 fast-forward 로 받는다(더럽거나 갈라졌으면 건드리지 않고 알린다).
2) 현재 커밋을 출력한다. (푸시는 하지 않는다 — 사용자가 "업로드"라 할 때만)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def git(*a):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


_, _rem = git("remote")
_rems = _rem.split()
REMOTE = "newrepo" if "newrepo" in _rems else ("origin" if "origin" in _rems else (_rems[0] if _rems else "origin"))   # 이 저장소의 원격 이름은 PC 마다 다를 수 있다
rc, out = git("fetch", REMOTE)
if rc:
    print("[git] fetch 실패 — 네트워크/원격 확인:", out)
else:
    _, br = git("rev-parse", "--abbrev-ref", "HEAD")
    _, dirty = git("status", "--porcelain")
    _, counts = git("rev-list", "--left-right", "--count", f"HEAD...{REMOTE}/{br}")
    ahead, behind = (int(x) for x in counts.split()) if counts.replace("\t", " ").split()[0].isdigit() else (0, 0)
    if behind == 0:
        print(f"[git] 최신입니다 ({br}, 로컬에만 있는 커밋 {ahead}개)")
    elif dirty or ahead:
        print(f"[git] 원격보다 {behind}커밋 뒤처졌지만 자동으로 안 받음 "
              f"({'작업트리에 변경 있음' if dirty else ''}{' · ' if dirty and ahead else ''}{f'로컬에만 있는 커밋 {ahead}개' if ahead else ''})"
              " → 사용자에게 보고하고 정리 후 받는다")
    else:
        rc, out = git("merge", "--ff-only", f"{REMOTE}/{br}")
        print(f"[git] {behind}커밋 받음 (fast-forward)" if rc == 0 else f"[git] 받기 실패: {out}")

_, last = git("log", "-1", "--format=%h %s")
print("[git] 현재:", last)

# 다른 PC·아이디가 남긴 "마지막 작업"(handoff.py) — 어느 조립도가 어디까지 됐는지 한눈에
import glob
_rows = []
for _f in glob.glob(os.path.join(HERE, "process", "진행기록_*.md")):
    _L = open(_f, encoding="utf-8").read().split("\n")
    _i = next((i for i, l in enumerate(_L[:6]) if l.startswith("## ★ 마지막 작업")), None)
    if _i is None or _i + 3 >= len(_L): continue
    _rows.append((_L[_i + 1], os.path.basename(_f)[5:-3], _L[_i + 2].replace("- 어디까지: ", ""), _L[_i + 3].replace("- 다음: ", "")))
if _rows:
    print()
    print("[마지막 작업] 최근 순 (PC·아이디는 handoff.py 가 적은 것)")
    for _t, _n, _w, _nx in sorted(_rows, reverse=True)[:5]:
        print("  %s  %s" % (_n, _t.lstrip("- ")))
        print("    어디까지: %s" % _w)
        print("    다음: %s" % _nx)
print()
print("다음: process/00_규칙.md 를 처음부터 읽고, 첫 보고에 '이번 번호에서 지킬 규칙 3개'를 적는다.")
sys.exit(0)
