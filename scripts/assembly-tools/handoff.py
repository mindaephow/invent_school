# 다음 PC·다음 아이디가 이어받을 "마지막 작업" 한 블록을 process/진행기록_<이름>.md 맨 위에 쓴다(있으면 덮어쓴다 — 쌓지 않는다. 이력은 git 커밋이 갖고 있다).
#   python handoff.py <이름> --아이디 <작업한 계정> --어디까지 "15번 완료, 16번 시작" --다음 "USED 4건 고친 뒤 number_start hammerbattle 16"
# PC 이름·날짜·현재 커밋은 자동으로 넣는다. 작업을 끝내거나 멈추기 전에 돌리고 "업로드" 를 요청한다(00_규칙.md I4).
import sys, os, re, socket, subprocess, datetime
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = "## ★ 마지막 작업"

def arg(k):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None

def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--") or not (arg("--아이디") and arg("--어디까지") and arg("--다음")):
        sys.exit(__doc__)
    name = sys.argv[1]
    p = os.path.join(HERE, "process", "진행기록_%s.md" % name)
    if not os.path.exists(p): sys.exit("진행기록 파일이 없다: %s" % p)
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True)
    commit = r.stdout.strip() or "?"
    block = ["%s (이 블록만 덮어쓴다 — 이력은 git)" % HEAD,
             "- %s · PC %s · 아이디 %s · 시작 커밋 %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), socket.gethostname(), arg("--아이디"), commit),
             "- 어디까지: %s" % arg("--어디까지"),
             "- 다음: %s" % arg("--다음"), ""]
    L = open(p, encoding="utf-8").read().split("\n")
    if L and L[0].startswith(HEAD):          # 기존 블록 제거
        i = 1
        while i < len(L) and not L[i].startswith("## "): i += 1
        L = L[i:]
    elif any(l.startswith(HEAD) for l in L):
        a = next(i for i, l in enumerate(L) if l.startswith(HEAD)); b = a + 1
        while b < len(L) and not L[b].startswith("## "): b += 1
        L = L[:a] + L[b:]
    k = 1 if L and L[0].startswith("# ") else 0   # 제목 줄이 있으면 그 아래에
    if k: L = L[:1] + [""] + block + L[1:]
    else: L = block + L
    open(p, "w", encoding="utf-8").write("\n".join(L))
    print("OK  %s 맨 위에 마지막 작업을 적었다 (PC %s · 아이디 %s). 이제 \"업로드\" 를 요청한다." % (os.path.basename(p), socket.gethostname(), arg("--아이디")))

main()
