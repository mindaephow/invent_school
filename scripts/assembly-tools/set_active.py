"""지금 작업 중인 조립도를 기록한다(scope_guard.py 가 읽는다). 사용자가 "<이름> 시작"이라고 했을 때만 쓴다. 사용: python set_active.py <이름>"""
import glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
names = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(HERE, '큐보', '조립도', '*', '*', '*.py')) if os.path.basename(p)[:-3] == os.path.basename(os.path.dirname(p))}
if len(sys.argv) != 2 or sys.argv[1] not in names: sys.exit('사용: python set_active.py <이름>  (이름: %s)' % ', '.join(sorted(names)))
open(os.path.join(HERE, '.active_assembly'), 'w', encoding='utf-8').write(sys.argv[1]); print('작업 중인 조립도:', sys.argv[1])
for f in ('.finish_off', '.finish_goal', '.finish_goal_state.json'):   # 조립도를 바꾸면 끝까지 가 지킴이(finish_guard.py)가 새 조립도로 다시 자동 켜진다
    if os.path.exists(os.path.join(HERE, f)): os.remove(os.path.join(HERE, f))
