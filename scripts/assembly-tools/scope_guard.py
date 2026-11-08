"""작업 범위 관문(사용자 지시 2026-11-08·11-09 — "로봇팽이를 할 때는 로봇팽이만 보라", 5번 넘게 반복): 지금 작업 중인 조립도가 아닌
다른 조립도 이름이 들어간 Bash 명령을 막는다(PreToolUse 훅, exit 2 = 클로드에게 보임). 읽기·쓰기 구분 없이 막는다.
지금 작업 중인 조립도 = scripts/assembly-tools/.active_assembly 의 이름, 없으면 조립도 파일이 가장 최근에 바뀐 것(autocheck.py 와 같은 기준).
다른 조립도로 옮길 때: 사용자가 "<이름> 시작"이라고 말하면 python scripts/assembly-tools/set_active.py <이름> (이 명령은 막지 않는다).
한계: Bash 명령 문자열에 이름이 있는지만 본다 — Read·Grep 같은 다른 도구는 못 막는다."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
try: j = json.load(sys.stdin)
except Exception: sys.exit(0)
if j.get('tool_name') != 'Bash': sys.exit(0)
c = (j.get('tool_input') or {}).get('command') or ''
if 'set_active.py' in c or 'scope_guard.py' in c: sys.exit(0)
names, newest = [], ('', 0)
for py in glob.glob(os.path.join(HERE, '큐보', '조립도', '*', '*', '*.py')):
    n = os.path.basename(py)[:-3]
    if n != os.path.basename(os.path.dirname(py)): continue
    names.append(n)
    fs = [f for f in (py, py[:-3] + '_read.json') if os.path.exists(f)]
    m = max(os.path.getmtime(f) for f in fs)
    if m > newest[1]: newest = (n, m)
try: active = open(os.path.join(HERE, '.active_assembly'), encoding='utf-8').read().strip()
except Exception: active = ''
if active not in names: active = newest[0]
cc = c.replace(chr(92), "/")
hit = [n for n in names if n != active and re.search(r'(?<![\w가-힣])' + re.escape(n) + r'(?![\w가-힣])', cc)]
if not hit: sys.exit(0)
sys.stderr.write('막힘(작업 범위): 지금 작업 중인 조립도는 "%s" 인데 명령에 다른 조립도(%s)가 들어 있습니다. 사용자가 시킨 조립도만 본다(2026-11-09, 5번 넘게 반복된 지시). 사용자가 다른 조립도로 옮기라고 하면 python scripts/assembly-tools/set_active.py <이름> 을 먼저 실행합니다.\n' % (active, ', '.join(hit)))
sys.exit(2)
