"""Claude 메모리 ↔ 저장소 process/메모리_규칙/ 동기화 (어느 PC 에서든 같은 규칙으로 일하게 한다).
  python sync_memory_rules.py --pull     # 저장소 → 메모리 (세션 시작: 다른 PC 의 최신 교정을 이 PC 메모리로)
  python sync_memory_rules.py            # 메모리 → 저장소 + INDEX.md 재생성 (업로드 전·메모리를 고친 뒤마다)
  python sync_memory_rules.py --check    # 메모리→저장소 차이만 보여 줌(아무것도 안 바꿈)
  (--from-repo 는 --pull 과 같다 — 이전 호환)
메모리 폴더는 PC·계정마다 달라서 자동으로 찾는다: ~/.claude/projects/*/memory 중 feedback_ 파일이 있는 곳 전부(원본),
그리고 이 저장소 경로에서 Claude 가 쓰는 폴더(현재 세션용). 환경변수 CLAUDE_MEMORY_DIR 로 고정할 수도 있다.
홍허브·영상 등 조립도와 무관한 메모리는 EXCLUDE 로 뺀다. 푸시는 사용자가 "업로드"라고 할 때만.
"""
import glob, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEST = os.path.join(HERE, "process", "메모리_규칙")
EXCLUDE = {"feedback_add_mcp_with_feature", "feedback_flow_automation_hands_off", "feedback_generate_angle_dont_ask",
           "feedback_mcp_same_project_pattern", "feedback_mlt_position_vs_length", "feedback_plan_doc_structure",
           "feedback_research_always_cite_source", "feedback_reuse_existing_infra", "feedback_scene_prompt_fresh_but_faithful",
           "feedback_script_length_after_content", "feedback_reread_verified_artifacts_after_compaction"}
PATTERNS = ("feedback_*.md", "project_*.md", "reference_user_diffs.md", "reference_invent_school_push_remote.md")


def wanted(name):
    b = name[:-3]
    return b not in EXCLUDE and not b.startswith(("project_flow", "project_honghub"))


def read(p):
    return open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def names(folder):
    out = set()
    for pat in PATTERNS:
        out |= {os.path.basename(p) for p in glob.glob(os.path.join(folder, pat))}
    return {n for n in out if wanted(n)}


def session_dir():
    """이 저장소를 cwd 로 열었을 때 Claude 가 메모리를 두는 폴더(경로의 영숫자 아닌 글자를 - 로)."""
    key = re.sub(r"[^A-Za-z0-9]", "-", ROOT)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", key, "memory")


def source_dirs():
    """읽어 올 메모리 폴더들 — 조립도 메모리가 있는 곳 전부(많은 순)."""
    env = os.environ.get("CLAUDE_MEMORY_DIR")
    if env:
        return [env]
    found = []
    for d in glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", "memory")):
        n = len(names(d))
        if n:
            found.append((n, d))
    return [d for _, d in sorted(found, reverse=True)]


def newest(name, dirs):
    best = None
    for d in dirs:
        p = os.path.join(d, name)
        if os.path.exists(p) and (best is None or os.path.getmtime(p) > os.path.getmtime(best)):
            best = p
    return best


mode = "pull" if ("--pull" in sys.argv or "--from-repo" in sys.argv) else "check" if "--check" in sys.argv else "push"
SRC = source_dirs()
SESSION = os.environ.get("CLAUDE_MEMORY_DIR") or session_dir()
os.makedirs(DEST, exist_ok=True)

if mode == "pull":
    # 저장소 → 메모리. 이 PC 메모리가 더 새로우면(안 올린 교정) 덮지 않고 알린다.
    targets = [SESSION] + [d for d in SRC if os.path.abspath(d) != os.path.abspath(SESSION)]
    new = chg = skip = 0
    for t in targets:
        os.makedirs(t, exist_ok=True)
        for n in sorted(names(DEST)):
            a, b = os.path.join(DEST, n), os.path.join(t, n)
            if not os.path.exists(b):
                shutil.copyfile(a, b); new += 1
            elif read(a) != read(b):
                if os.path.getmtime(b) > os.path.getmtime(a):
                    skip += 1; print("이 PC 메모리가 더 새로움(안 올렸을 수 있음) — 그대로 둠:", n)
                else:
                    shutil.copyfile(a, b); chg += 1; print("갱신", n)
        # 메모리 색인(MEMORY.md): 저장소 색인에 있는데 없는 줄만 덧붙인다(기존 줄·다른 메모리 보존)
        idx_repo = os.path.join(DEST, "INDEX.md")
        idx_mem = os.path.join(t, "MEMORY.md")
        have = read(idx_mem) if os.path.exists(idx_mem) else ""
        add = []
        for line in read(idx_repo).splitlines() if os.path.exists(idx_repo) else []:
            m = re.match(r"^- \[[^\]]*\]\(([^)]*)\)", line)
            if m and m.group(1) not in have:
                add.append(line)
        if add:
            open(idx_mem, "w", encoding="utf-8", newline="\n").write((have.rstrip() + "\n" if have.strip() else "") + "\n".join(add) + "\n")
            print(f"MEMORY.md 에 {len(add)}줄 추가 ({t})")
    print(f"[pull] 새 {new} · 갱신 {chg} · 보존 {skip} → {', '.join(targets)}")
    sys.exit(0)

if not SRC:
    sys.exit("조립도 메모리가 있는 PC 가 아님(feedback_*.md 를 가진 ~/.claude/projects/*/memory 없음). 이 PC 는 --pull 만 쓴다.")

all_names = set()
for d in SRC:
    all_names |= names(d)
new = chg = 0
for n in sorted(all_names):
    a, b = newest(n, SRC), os.path.join(DEST, n)
    if not os.path.exists(b):
        new += 1; print("새 파일", n)
    elif read(a) != read(b):
        chg += 1; print("달라짐", n)
    else:
        continue
    if mode == "push":
        shutil.copyfile(a, b)
for n in sorted(names(DEST) - all_names):
    print("메모리에 없는데 저장소에만 있음(삭제는 손으로):", n)
print(f"[{mode}] 새 {new} · 달라짐 {chg}" + (" (바꾸지 않음)" if mode == "check" else "") + f"  ← {', '.join(SRC)}")

if mode == "push":
    head = read(os.path.join(DEST, "INDEX_head.md")).rstrip() + "\n\n## 전체 색인\n"
    lines, seen = [], set()
    for d in SRC:
        p = os.path.join(d, "MEMORY.md")
        if not os.path.exists(p):
            continue
        for line in read(p).splitlines():
            m = re.match(r"^- \[[^\]]*\]\(([^)]*)\)", line)
            if m and m.group(1) not in seen and os.path.exists(os.path.join(DEST, m.group(1))):
                seen.add(m.group(1)); lines.append(line)
    open(os.path.join(DEST, "INDEX.md"), "w", encoding="utf-8", newline="\n").write(head + "\n".join(lines) + "\n")
    print(f"INDEX.md 재생성 ({len(lines)}줄)")
