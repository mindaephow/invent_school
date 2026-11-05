# 큐보 부시(넓은 쪽 = 대가리, 좁은 쪽 = 몸통)의 바깥 지름만 바꿔 DB 의 부시 행에 등록한다. 두께·가운데 열십자 구멍(반지름 3.5 이하)은 그대로.
#   python scripts/resize-cubo-bush.py 10 9            → 시험(DB 는 바꾸지 않음): 큰 쪽 지름 10, 작은 쪽 지름 9 로 만든 모델을 검사만 한다
#   python scripts/resize-cubo-bush.py 10 9 --write    → 행의 모델·크기·부품 상세내역·연결점 size 를 바꾼다
# 현재 모델에서 바깥 반지름(넓은 쪽·좁은 쪽)을 읽어 목표 값으로 선형 매핑하므로 다시 돌려도 안전하다(이미 그 크기면 변화 없음).
# 쓴 뒤에는 부품 관리 → ✅ 골라서 그리기(이 부품 id 만)로 3D 썸네일을 다시 그리고, 상세내역이 남았는지 확인한다(썸네일 저장이 detail 을 지운 적 있다, 2026-11-05).
# 출력용 STL(data.print)은 건드리지 않는다. 사용자 2026-11-05: 큰 쪽 10 · 작은 쪽 9.
import base64, json, sys, urllib.request
import numpy as np
from collections import Counter

BUSH_ID = 'b0a436b3-2ef5-4da6-b33d-a39d67d8f2c1'   # 큐보 · 부시 행
HOLE_R = 3.6                                          # 이보다 안쪽 점은 구멍(열십자) — 크기를 바꾸지 않는다
args = [a for a in sys.argv[1:] if not a.startswith('--')]
WRITE = '--write' in sys.argv
if len(args) != 2: sys.exit(__doc__)
BIG, SMALL = float(args[0]) / 2, float(args[1]) / 2   # 목표 반지름(대가리, 몸통)

env = {}
for l in open(__file__.replace('\\', '/').rsplit('/scripts/', 1)[0] + '/.env.local', encoding='utf-8'):
    if '=' in l:
        k, v = l.rstrip('\n').split('=', 1); env[k.strip()] = v.strip().strip('"')
H = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'], 'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'], 'Content-Type': 'application/json'}
URL = env['SUPABASE_URL'] + '/rest/v1/ivs_part_catalog?id=eq.' + BUSH_ID
row = json.load(urllib.request.urlopen(urllib.request.Request(URL + '&select=data', headers=H)))[0]['data']

raw = base64.b64decode(row['spec']['shapes'][0]['fileDataUrl'].split(',', 1)[1])
n = int(np.frombuffer(raw[80:84], '<u4')[0])
dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
a = np.frombuffer(raw[84:84 + n * 50], dtype=dt).copy()
V = a['v'].astype(float)
P = V.reshape(-1, 3)
cx, cy = (P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2   # 두께 방향이 z, 가운데가 (cx, cy)
r = np.hypot(V[:, :, 0] - cx, V[:, :, 1] - cy)
z = V[:, :, 2]
r_big = float(r.max())
# 좁은 쪽 = 두 끝면(z 최소·최대) 중 바깥 반지름이 더 작은 끝면의 최대 반지름
ends = [float(r[np.abs(z - zz) < 0.01].max()) for zz in (z.min(), z.max())]
r_small = min(ends)
print('현재 바깥 반지름: 큰 쪽 %.3f · 작은 쪽 %.3f' % (r_big, r_small), '→ 목표 %.3f · %.3f' % (BIG, SMALL))
rn = np.interp(r, [0, HOLE_R, r_small, r_big], [0, HOLE_R, SMALL, BIG])
sc = np.where(r > 1e-9, rn / np.maximum(r, 1e-9), 1.0)
V[:, :, 0] = cx + (V[:, :, 0] - cx) * sc
V[:, :, 1] = cy + (V[:, :, 1] - cy) * sc
a['v'] = V.astype(np.float32)
N = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); L = np.linalg.norm(N, axis=1); L[L == 0] = 1
a['n'] = (N / L[:, None]).astype(np.float32)
stl = bytes(raw[:80]) + np.uint32(n).tobytes() + a.tobytes()

q = np.round(V, 3)
c = Counter()
for t in q:
    k = [tuple(x) for x in t]
    for i in range(3): c[(k[i], k[(i + 1) % 3])] += 1
bad = sum(1 for (p1, p2), v in c.items() if c.get((p2, p1), 0) != v)
vol = float(np.sum(np.einsum('ij,ij->i', q[:, 0], np.cross(q[:, 1], q[:, 2]))) / 6)
print('삼각형', n, '| 짝 없는 모서리', bad, '| 부피', round(vol, 2))
if bad or vol <= 0: sys.exit('❌ 모델 검사 실패 — 등록하지 않는다')
if not WRITE: sys.exit('(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)')

d = json.loads(json.dumps(row))
d['spec']['shapes'][0]['fileDataUrl'] = 'data:application/octet-stream;base64,' + base64.b64encode(stl).decode()
t = d['connectors']['size'][1]
d['size'] = '%g×%g×%gmm' % (BIG * 2, BIG * 2, t)
d['connectors']['size'] = [BIG * 2, t, BIG * 2]
det = d.setdefault('detail', {})
det.setdefault('크기_mm', {}).update({'가로(x)': BIG * 2, '세로(z)': BIG * 2, '큰 쪽 지름': BIG * 2, '작은 쪽 지름': SMALL * 2})
det.setdefault('대가리_몸통', {}).update({'대가리 지름_mm': BIG * 2, '몸통 지름_mm': SMALL * 2})
# partlib.py(dims.json)와 부품 DB 상세내역(data.detail 의 크기_mm)은 따로 고친다
req = urllib.request.Request(URL, data=json.dumps({'data': d}).encode(), method='PATCH', headers={**H, 'Prefer': 'return=minimal'})
print('등록', urllib.request.urlopen(req).status)
