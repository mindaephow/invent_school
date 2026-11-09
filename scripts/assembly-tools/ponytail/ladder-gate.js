// 포니테일 사다리 게이트 — PreToolUse 훅. 사다리 기록(.claude/ponytail_ladder.json, 90분)이 없으면 쓰기·삭제·커밋을 막는다.
// 원본은 저장소(scripts/assembly-tools/ponytail/)에 있고, setup_new_pc.py 가 .claude/ponytail/hooks/ 로 복사해 settings.json 에 연결한다.
// 한계: 기록이 있는지만 본다(실제로 찾았는지는 못 본다).
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(process.env.CLAUDE_PROJECT_DIR || path.join(__dirname, "..", "..", ".."));   // 복사본(.claude/ponytail/hooks/) 기준 세 단계 위
const LADDER = path.join(ROOT, ".claude", "ponytail_ladder.json");
const TTL_MS = 90 * 60 * 1000;
const WRITE_CMD = /(\brm\b|\bmv\b|\bcp\b|\bsed\s+-i|\btee\b|\bgit\s+(commit|add|rm|reset|checkout|restore|clean|merge|push)\b|(^|[^>=!<])>{1,2}\s*[^&\s])/;

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let ev = {};
  try { ev = JSON.parse(raw); } catch { process.exit(0); }
  const tool = ev.tool_name || "";
  const input = ev.tool_input || {};
  const inRoot = (p) => {
    const r = path.relative(ROOT, path.resolve(ev.cwd || ROOT, p || ""));
    return r && !r.startsWith("..") && !path.isAbsolute(r) && !r.startsWith(".claude");
  };

  let needs = false;
  if (tool === "Edit" || tool === "Write" || tool === "NotebookEdit") needs = inRoot(input.file_path || input.notebook_path);
  else if (tool === "Bash") {
    const cmd = input.command || "";
    needs = !/ladder\.py|setup_new_pc\.py|session_start\.py/.test(cmd) && WRITE_CMD.test(cmd);
  }
  if (!needs) process.exit(0);

  try {
    const d = JSON.parse(fs.readFileSync(LADDER, "utf8"));
    if (Date.now() - d.ts < TTL_MS && d.need && d.found && d.reuse) process.exit(0);
  } catch {}
  process.stderr.write(
    "포니테일 사다리 기록이 없거나 90분이 지났습니다. 먼저 grep 으로 같은 문제를 푼 곳을 찾고\n" +
      'python scripts/assembly-tools/ladder.py "필요: …" "찾은 곳: …" "재사용: …" 로 기록한 뒤 다시 하세요.\n'
  );
  process.exit(2);
});
