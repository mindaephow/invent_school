"""사용자 PC 의 Claude 메모리 ↔ 저장소 process/메모리_규칙/ 동기화 (외부 PC 도 같은 규칙으로 일하게 한다).
  python sync_memory_rules.py            # 메모리 → 저장소 복사 + INDEX.md 재생성 (사용자 PC 에서, 메모리를 고친 뒤마다)
  python sync_memory_rules.py --from-repo # 저장소 → 메모리 (외부 PC 에서 고쳐 푸시한 규칙을 사용자 PC 메모리로 가져올 때)
  python sync_memory_rules.py --check     # 차이만 보여 줌(아무것도 안 바꿈)
홍허브·영상 등 조립도와 무관한 메모리는 EXCLUDE 로 뺀다. 푸시는 사용자가 "업로드"라고 할 때만.
"""
import glob, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "process", "메모리_규칙")
MEM = os.path.join(os.path.expanduser("~"), ".claude", "projects", "C--Users-user-Downloads", "memory")
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

mode = "--from-repo" if "--from-repo" in sys.argv else "--check" if "--check" in sys.argv else "to-repo"
if not os.path.isdir(MEM):
    sys.exit(f"메모리 폴더가 없음: {MEM} (사용자 PC 에서만 쓴다)")
os.makedirs(DEST, exist_ok=True)
src, dst = (DEST, MEM) if mode == "--from-repo" else (MEM, DEST)
new = chg = 0
for n in sorted(names(src)):
    a, b = os.path.join(src, n), os.path.join(dst, n)
    if not os.path.exists(b):
        new += 1; print("새 파일", n)
    elif read(a) != read(b):
        chg += 1; print("달라짐", n)
    else:
        continue
    if mode != "--check":
        shutil.copyfile(a, b)
gone = sorted(names(DEST) - names(MEM)) if mode == "to-repo" else []
for n in gone:
    print("메모리에 없는데 저장소에만 있음(삭제는 손으로):", n)
print(f"새 {new} · 달라짐 {chg}" + (" (--check: 바꾸지 않음)" if mode == "--check" else ""))

if mode == "to-repo":
    head = read(os.path.join(DEST, "INDEX_head.md")).rstrip() + "\n\n## 전체 색인\n"
    lines = []
    for line in read(os.path.join(MEM, "MEMORY.md")).splitlines():
        m = re.match(r"^- \[[^\]]*\]\(([^)]*)\)", line)
        if m and os.path.exists(os.path.join(DEST, m.group(1))):
            lines.append(line)
    open(os.path.join(DEST, "INDEX.md"), "w", encoding="utf-8", newline="\n").write(head + "\n".join(lines) + "\n")
    print(f"INDEX.md 재생성 ({len(lines)}줄)")
