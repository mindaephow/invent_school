"""새 PC(외부 PC) 준비 점검 — git 에 없는 것(.claude/launch.json, .env.local, conn.json/dims.json, 파이썬 라이브러리)을 확인·생성한다.
사용: cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python setup_new_pc.py
  --only-ponytail : 7번(포니테일 스킬·훅)만 점검·생성 (session_start.py 가 부른다)
"""
import json, os, shutil, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ok = True

def say(mark, msg):
    print(mark, msg)

def ponytail():
    """7. 포니테일 스킬(SKILL.md)·사다리 훅 — .claude/ 는 git 에 없으므로 PC 마다 받아서 만든다."""
    global ok
    skill = os.path.join(ROOT, ".claude", "skills", "ponytail", "SKILL.md")
    if os.path.exists(skill):
        say("OK  ", ".claude/skills/ponytail/SKILL.md")
    else:
        url = "https://raw.githubusercontent.com/DietrichGebert/ponytail/HEAD/skills/ponytail/SKILL.md"
        try:
            os.makedirs(os.path.dirname(skill), exist_ok=True)
            with urllib.request.urlopen(url, timeout=20) as r, open(skill, "wb") as f:
                f.write(r.read())
            say("MADE", ".claude/skills/ponytail/SKILL.md 받음(DietrichGebert/ponytail)")
        except Exception as e:
            ok = False; say("FAIL", f"포니테일 SKILL.md 받기 실패({e}) → 네트워크 확인 후 다시 실행")
    src = os.path.join(HERE, "ponytail", "ladder-gate.js")
    dst = os.path.join(ROOT, ".claude", "ponytail", "hooks", "ladder-gate.js")
    if not os.path.exists(src):
        ok = False; say("FAIL", "ponytail/ladder-gate.js 원본 없음 → git pull 로 최신을 받았는지 확인"); return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read():
        shutil.copyfile(src, dst); say("MADE", ".claude/ponytail/hooks/ladder-gate.js 복사")
    else:
        say("OK  ", ".claude/ponytail/hooks/ladder-gate.js")
    sj = os.path.join(ROOT, ".claude", "settings.json")
    cfg = json.load(open(sj, encoding="utf-8")) if os.path.exists(sj) else {}
    pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if any("ladder-gate.js" in h.get("command", "") for e in pre for h in e.get("hooks", [])):
        say("OK  ", ".claude/settings.json 에 사다리 훅 연결됨")
    else:
        pre.append({"matcher": "Edit|Write|NotebookEdit|Bash", "hooks": [{"type": "command", "command": 'node "$CLAUDE_PROJECT_DIR/.claude/ponytail/hooks/ladder-gate.js"'}]})
        json.dump(cfg, open(sj, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        say("MADE", ".claude/settings.json 에 사다리 훅 연결(Claude 를 다시 열어야 적용)")
    if not shutil.which("node"):
        ok = False; say("FAIL", "node 없음 → 사다리 훅이 못 돈다(Node 설치)")

if "--only-ponytail" in sys.argv:
    ponytail(); sys.exit(0 if ok else 1)

# 1. 파이썬 라이브러리
for mod in ("numpy", "cv2"):
    try:
        __import__(mod); say("OK  ", f"python 라이브러리 {mod}")
    except ImportError:
        ok = False; say("FAIL", f"{mod} 없음 → pip install numpy opencv-python")

# 2. node_modules
if os.path.isdir(os.path.join(ROOT, "node_modules")):
    say("OK  ", "node_modules")
else:
    ok = False; say("FAIL", f"node_modules 없음 → {ROOT} 에서 npm install")

# 3. .claude/launch.json (git 에 없음 → 만든다)
lj = os.path.join(ROOT, ".claude", "launch.json")
if os.path.exists(lj):
    say("OK  ", ".claude/launch.json")
else:
    os.makedirs(os.path.dirname(lj), exist_ok=True)
    with open(lj, "w", encoding="utf-8") as f:
        json.dump({"version": "0.0.1", "configurations": [{
            "name": "invent-school-dev", "runtimeExecutable": "npm",
            "runtimeArgs": ["run", "dev", "--", "-p", "3178"], "port": 3178}]}, f, indent=2)
    say("MADE", ".claude/launch.json 생성(invent-school-dev, 포트 3178)")

# 4. .env.local (사용자가 줘야 함)
env = os.path.join(ROOT, ".env.local")
txt = open(env, encoding="utf-8").read() if os.path.exists(env) else ""
for key in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
    if key in txt:
        say("OK  ", f".env.local {key}")
    else:
        ok = False; say("FAIL", f".env.local 에 {key} 없음 → 사용자에게 요청(Vercel 환경변수에 있음). 사용자 ✓·❄·📷 를 DB 에서 읽는 데 필요")

# 5. conn.json / dims.json (partlib.py 가 만든다)
if not all(os.path.exists(os.path.join(HERE, n)) for n in ("conn.json", "dims.json")):
    say("INFO", "conn.json/dims.json 없음 → python partlib.py 실행 시도")
    r = subprocess.run([sys.executable, os.path.join(HERE, "partlib.py")], cwd=HERE)
    if r.returncode != 0:
        ok = False; say("FAIL", "partlib.py 실패 — 위 출력 확인")
else:
    say("OK  ", "conn.json, dims.json")

# 6. 규칙 문서
rules = os.path.join(HERE, "큐보", "규칙", "큐보 부품결합규칙.md")
say("OK  " if os.path.exists(rules) else "FAIL", "큐보/규칙/큐보 부품결합규칙.md (git pull 로 최신을 받았는지 확인)")

# 7. 포니테일 스킬·사다리 훅
ponytail()

print()
print("모두 준비됨 — 다음은 CLAUDE.md '세션을 시작할 때' 와 큐보/규칙/큐보 부품결합규칙.md 를 읽고 시작" if ok else
      "위 FAIL 을 해결한 뒤 다시 실행")
