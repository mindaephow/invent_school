# 큐보 작업의 "마지막 작업" 한 블록을 큐보/인수인계.md 에 쓴다(하나뿐 — 있으면 덮어쓴다, 쌓지 않는다. 이력은 git).
#   (끝낼 때) python handoff.py <작업 이름> --아이디 <작업한 계정> --어디까지 "15번 완료, 16번 시작" --다음 "USED 4건 고친 뒤 number_start hammerbattle 16"
#   (시작할 때) python handoff.py <작업 이름> --아이디 <내 계정> --시작     → "- 이어받음: 날짜 · PC · 아이디" 한 줄을 적는다(마지막 작업 줄은 그대로)
# <작업 이름> = 조립도 이름(balance) 또는 규칙 정리 같은 작업 이름. PC 이름·날짜·현재 커밋은 자동. 작업을 끝내거나 멈추기 전에 돌린다(큐보 부품결합규칙.md I4). 푸시는 사용자가 "업로드"라고 할 때만 한다.
import sys, os, socket, subprocess, datetime
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "큐보", "인수인계.md")
HEADER = [
    "# 큐보 작업 인수인계 (하나뿐)", "",
    "큐보 작업 전체에서 마지막으로 한 일 하나만 적는다 — 어느 조립도·규칙 정리를 어디까지 했고 다음에 뭘 하는지. `handoff.py` 가 이 파일의 `- …` 줄만 덮어쓴다(이력은 git). 조립도별 진행 내용은 `큐보/조립도/<권>권/<이름>/진행기록.md`. 쓰는 법은 `큐보/규칙/큐보 부품결합규칙.md` I4.", ""]


def arg(k):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None


def bullets():
    if not os.path.exists(FILE):
        return []
    return [l for l in open(FILE, encoding="utf-8").read().splitlines() if l.startswith("- ")]


def save(b):
    open(FILE, "w", encoding="utf-8", newline="\n").write("\n".join(HEADER + b) + "\n")


def start():
    b = bullets()
    if not b:
        sys.exit("마지막 작업 줄이 아직 없다 — 끝낼 때 handoff.py 로 먼저 적는다")
    line = "- 이어받음: %s · PC %s · 아이디 %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), socket.gethostname(), arg("--아이디"))
    k = next((i for i, l in enumerate(b) if l.startswith("- 이어받음:")), None)
    if k is None:
        b.append(line)
    else:
        b[k] = line
    save(b)
    print("OK  %s" % line)


def main():
    if "--시작" in sys.argv and len(sys.argv) > 2 and not sys.argv[1].startswith("--") and arg("--아이디"):
        return start()
    if len(sys.argv) < 2 or sys.argv[1].startswith("--") or not (arg("--아이디") and arg("--어디까지") and arg("--다음")):
        sys.exit(__doc__)
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True)
    commit = r.stdout.strip() or "?"
    save(["- %s · PC %s · 아이디 %s · 시작 커밋 %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), socket.gethostname(), arg("--아이디"), commit),
          "- 작업: %s" % sys.argv[1], "- 어디까지: %s" % arg("--어디까지"), "- 다음: %s" % arg("--다음")])
    print("OK  큐보/인수인계.md 에 마지막 작업을 적었다 (작업 %s · PC %s · 아이디 %s)." % (sys.argv[1], socket.gethostname(), arg("--아이디")))


main()
