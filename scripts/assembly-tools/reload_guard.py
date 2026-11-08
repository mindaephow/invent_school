"""수정 뒤 화면 확인 관문(사용자 지시 2026-11-09 — CLAUDE.md '작업을 했다의 기준: DB 에 등록하고 화면을 새로 불러와(navigate) 스크린샷으로 보여 준 상태'를 문장이 아니라 훅으로 강제).
  python reload_guard.py stamp   : PostToolUse(브라우저 navigate · computer screenshot/zoom) — 마지막 새로고침·스크린샷 시각을 .reload_stamp.json 에 적는다
  python reload_guard.py check   : Stop 훅 — 최근 6시간 안에 바뀐 조립도 .py·_asm.json·_read.json·public/design*.js·design.html·check_local.js 가
                                   마지막 새로고침 또는 스크린샷보다 새것이면 exit 2 로 턴을 못 끝내게 한다(stop_hook_active 면 한 번만 막는다).
한계: 파일이 바뀌었는지 시각만 본다 — 그 화면이 올바른 번호였는지는 못 본다. 화면 영향이 없는 수정(문서·규칙 .md)은 대상이 아니다."""
import glob, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ST = os.path.join(HERE, '.reload_stamp.json')
def load():
    try: return json.load(open(ST, encoding='utf-8'))
    except Exception: return {}
mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
try: j = json.load(sys.stdin)
except Exception: j = {}
if mode == 'stamp':
    tn = j.get('tool_name', ''); act = (j.get('tool_input') or {}).get('action', '')
    s = load()
    if tn.endswith('navigate'): s['nav'] = time.time()
    elif tn.endswith('computer') and act in ('screenshot', 'zoom'): s['shot'] = time.time()
    else: sys.exit(0)
    json.dump(s, open(ST, 'w', encoding='utf-8')); sys.exit(0)
if j.get('stop_hook_active'): sys.exit(0)
s = load(); now = time.time()
if not s: json.dump({'nav': now, 'shot': now}, open(ST, 'w', encoding='utf-8')); sys.exit(0)
seen = min(s.get('nav', 0), s.get('shot', 0))
pats = ['큐보/조립도/*/*/*.py', '큐보/조립도/*/*/*_asm.json', '큐보/조립도/*/*/*_read.json', 'check_local.js']
fs = [f for p in pats for f in glob.glob(os.path.join(HERE, p))] + glob.glob(os.path.join(ROOT, 'public', 'design*.js')) + [os.path.join(ROOT, 'public', 'design.html')]
new = sorted(((os.path.getmtime(f), f) for f in fs if os.path.exists(f) and now - os.path.getmtime(f) < 6 * 3600 and os.path.getmtime(f) > seen + 1), reverse=True)
if not new: sys.exit(0)
miss = [k for k, lab in (('nav', '새로고침(navigate)'), ('shot', '스크린샷')) if s.get(k, 0) < new[0][0]]
sys.stderr.write('막힘(수정 뒤 화면 확인): %s 가 마지막 %s 보다 나중에 바뀌었습니다. 수정한 뒤에는 화면을 새로 불러와(navigate) 그 번호를 열고 스크린샷으로 확인한 다음에 끝냅니다(CLAUDE.md "작업을 했다의 기준"). 화면에 영향이 없으면 그 이유를 보고에 적습니다.\n' % (os.path.basename(new[0][1]), ' · '.join(lab for k, lab in (('nav', '새로고침'), ('shot', '스크린샷')) if s.get(k, 0) < new[0][0]) or '확인'))
sys.exit(2)
