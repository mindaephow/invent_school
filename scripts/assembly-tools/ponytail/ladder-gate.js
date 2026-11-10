// 포니테일 사다리 게이트 — PreToolUse 훅. 사다리 기록(.claude/ponytail_ladder.json, 90분)이 없으면 쓰기·삭제·커밋을 막는다.
// 원본은 저장소(scripts/assembly-tools/ponytail/)에 있고, setup_new_pc.py 가 .claude/ponytail/hooks/ 로 복사해 settings.json 에 연결한다.
// 한계: 기록이 있는지만 본다(실제로 찾았는지는 못 본다).
const fs = require("fs");
const path = require("path");

// 루트는 이 파일 위치로 정한다(복사본 .claude/ponytail/hooks/ 기준 세 단계 위). CLAUDE_PROJECT_DIR 는 세션을 임시 폴더에서 열었다가 옮기면 옛 폴더를 가리켜 프로젝트 안 수정이 "루트 밖"으로 판정돼 게이트가 아무것도 못 막는다(2026-11-10 오토건 — 포니테일 기록 없이 공용 도구를 고쳐도 통과). 복사본이 아닌 원본(scripts/assembly-tools/ponytail/)에서 돌릴 때만 환경 변수를 쓴다.
const _byFile = path.resolve(__dirname, "..", "..", "..");
const ROOT = fs.existsSync(path.join(_byFile, ".claude")) ? _byFile : path.resolve(process.env.CLAUDE_PROJECT_DIR || _byFile);
const LADDER = path.join(ROOT, ".claude", "ponytail_ladder.json");
const TTL_MS = 90 * 60 * 1000;
const WRITE_CMD = /(\brm\b|\bmv\b|\bcp\b|\bsed\s+-i|\btee\b|\bgit\s+(commit|add|rm|reset|checkout|restore|clean|merge|push)\b|(^|[^>=!<])>{1,2}\s*[^&\s])/;

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let ev = {};
  try { ev = JSON.parse(raw); } catch { process.exit(0); }
  const tool = ev.tool_name || "";
  // 작업하는 동안 이어지게(사용자 지시 2026-11-10): 어떤 도구를 쓰든 24시간 안의 기록이 있으면 3분마다 시각을 새로 써서 90분 창이 계속 밀린다.
  try {
    const t = JSON.parse(fs.readFileSync(LADDER, "utf8"));
    const age = Date.now() - t.ts;
    if (t.need && t.found && t.reuse && age > 3 * 60 * 1000 && age < 24 * 60 * 60 * 1000) {
      t.ts = Date.now();
      fs.writeFileSync(LADDER, JSON.stringify(t));
      try {
        const RS0 = path.join(ROOT, "public", "_rule_status.json");
        const rs0 = JSON.parse(fs.readFileSync(RS0, "utf8"));
        rs0.ponytail = Object.assign(rs0.ponytail || {}, { ttlMin: 90, ts: t.ts });
        fs.writeFileSync(RS0, JSON.stringify(rs0));
      } catch {}
    }
  } catch {}
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
  // 조립도 파일(큐보/조립도/<권>/<이름>/ 아래)을 고치려면 그 조립도의 number_start.py 도장(90분)이 있어야 한다 — 앞 번호 기록을 읽지 않고 눈대중으로 고치는 사고 방지(사용자 지시 2026-11-11).
  try {
    const target = tool === "Bash" ? (WRITE_CMD.test(input.command || "") && !/number_start\.py/.test(input.command || "") ? input.command : "") : (input.file_path || "");
    const m = String(target).split("\\").join("/").match(/큐보\/조립도\/[^/\s"']+\/([^/\s"']+)\//);
    if (m) {
      let ok = false;
      try { const st = JSON.parse(fs.readFileSync(path.join(ROOT, ".claude", "number_start_stamp.json"), "utf8")); ok = st.name === m[1] && Date.now() - st.ts < TTL_MS; } catch {}
      if (!ok) {
        process.stderr.write("조립도(" + m[1] + ") 파일을 고치기 전에 python scripts/assembly-tools/number_start.py " + m[1] + " <번호> 를 먼저 돌려 앞 번호 기록(읽기 표·격자·부품 위치)을 읽으세요. 앞 번호에서 이미 조립한 홀 번호를 기준으로 쓰고 눈대중으로 정하지 않습니다.\n");
        process.exit(2);
      }
    }
  } catch {}

  try {
    const d = JSON.parse(fs.readFileSync(LADDER, "utf8"));
    if (d.need && d.found && d.reuse) {
      const age = Date.now() - d.ts;
      if (age < TTL_MS) process.exit(0);
      // 90분이 지나도 같은 날(24시간 안) 쓴 기록이 있으면 시각만 새로 써서 자동 연장한다(사용자 지시 2026-11-10: 0분이 되면 멈추지 말고 이어서 진행).
      //   내용이 바뀌는 새 작업이면 Claude 가 ladder.py 로 새로 쓴다. 24시간이 지난 기록은 연장하지 않고 막는다.
      if (age < 24 * 60 * 60 * 1000) {
        d.ts = Date.now();
        fs.writeFileSync(LADDER, JSON.stringify(d));
        try {   // 화면 아래 규칙 바(public/_rule_status.json)도 같이 새로 쓴다
          const RS = path.join(ROOT, "public", "_rule_status.json");
          const rs = JSON.parse(fs.readFileSync(RS, "utf8"));
          rs.ponytail = Object.assign(rs.ponytail || {}, { ttlMin: 90, ts: d.ts });
          fs.writeFileSync(RS, JSON.stringify(rs));
        } catch {}
        process.stderr.write("포니테일 사다리 기록을 자동 연장했습니다(90분). 새 작업이면 ladder.py 로 다시 쓰세요.\n");
        process.exit(0);
      }
    }
  } catch {}
  process.stderr.write(
    "포니테일 사다리 기록이 없거나 90분이 지났습니다. 먼저 grep 으로 같은 문제를 푼 곳을 찾고\n" +
      'python scripts/assembly-tools/ladder.py "필요: …" "찾은 곳: …" "재사용: …" 로 기록한 뒤 다시 하세요.\n'
  );
  process.exit(2);
});
