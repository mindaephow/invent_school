"""새 PC(외부 PC) 준비 점검 — git 에 없는 것(.claude/launch.json, .env.local, conn.json/dims.json, 파이썬 라이브러리)을 확인·생성한다.
사용: cd scripts/assembly-tools && PYTHONIOENCODING=utf-8 python setup_new_pc.py
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ok = True

def say(mark, msg):
    print(mark, msg)

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
mem = os.path.join(HERE, "process", "메모리_규칙", "INDEX.md")
say("OK  " if os.path.exists(mem) else "FAIL", "process/메모리_규칙/INDEX.md (git pull 로 최신을 받았는지 확인)")

print()
print("모두 준비됨 — 다음은 CLAUDE.md '이 PC 에 메모리가 없을 때' 와 메모리_규칙/INDEX.md 필독을 읽고 시작" if ok else
      "위 FAIL 을 해결한 뒤 다시 실행")
