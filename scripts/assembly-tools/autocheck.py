"""상시검사(사용자 지시 2026-11-08): 조립도 .py·_read.json 이 바뀌면 build.py(겹침·안내점)·rulecheck.py 를 자동으로 돌려
문제만 짧게 stderr 로 내보낸다(PostToolUse 훅, exit 2 = 클로드에게 보임). 새 검사 로직은 없고 기존 도구를 부르기만 한다."""
import glob, os, re, subprocess, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
STAMP = os.path.join(HERE, '.autocheck_stamp.json')
try: st = json.load(open(STAMP))
except Exception: st = {}
env = dict(os.environ, PYTHONIOENCODING='utf-8')
out = []
# 사용자 지시 2026-11-08: 상시검사는 지금 작업 중인 차시(조립도) 하나에서만 돈다 = 조립도 파일이 가장 최근에 바뀐 것. 다음 차시로 넘어가 그 조립도를 고치면 그쪽으로 옮겨 간다.
cands = []
for py in glob.glob(os.path.join(HERE, '큐보', '조립도', '*', '*', '*.py')):
    name = os.path.basename(py)[:-3]
    if name != os.path.basename(os.path.dirname(py)): continue
    fs = [f for f in (py, py[:-3] + '_read.json') if os.path.exists(f)]
    cands.append((max(os.path.getmtime(f) for f in fs), name, py))
cands.sort(reverse=True)
try:   # 작업 조립도(.active_assembly)가 있으면 그것을 우선한다 — 파일 수정 시각이 아니라 지금 하는 일 기준(scope_guard 와 같은 기준)
    _act = open(os.path.join(HERE, '.active_assembly'), encoding='utf-8').read().strip()
    cands.sort(key=lambda c: c[1] == _act, reverse=True)
except Exception: pass
for m, name, py in cands[:1]:
    if name not in st: st[name] = m; continue   # 처음 보는 조립도는 기준만 기록(전체 조립도를 한꺼번에 돌리지 않는다)
    if m <= st[name]: continue
    st[name] = m
    b = subprocess.run([sys.executable, 'build.py', name], cwd=HERE, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    r = subprocess.run([sys.executable, 'rulecheck.py', name], cwd=HERE, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    bad = [l.strip() for l in (b.stdout + b.stderr).splitlines() if re.search(r'몸통 겹침 [1-9]|안내점 맞물림 없는 부품: [1-9]|Traceback|Error|규칙 위반 표시: [1-9]', l)]
    bad += [l.strip() for l in r.stdout.splitlines() if re.match(r'\s*\d+번 ❌', l) or l.startswith('합계')]
    out.append(f'[상시검사] {name}: ' + (' | '.join(bad) if bad else '이상 없음'))
json.dump(st, open(STAMP, 'w'))
if out:
    print('\n'.join(out), file=sys.stderr)
    sys.exit(2 if any('이상 없음' not in o for o in out) else 0)
