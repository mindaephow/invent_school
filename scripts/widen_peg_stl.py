# 눈블록처럼 한쪽 면에 돌기(몸통 반지름 2.9·밑동 3.4·끝 2.4)가 달린 STL 의 돌기를 구멍이 6.2 로 커진 프레임에 맞춰 키운다 — 반지름 +0.35(프레임 구멍과 같은 만큼, 원래 여유 0.15 유지).
#   python scripts/widen_peg_stl.py <입력.stl> <출력.stl> [더할 반지름=0.35]
# 가장 작은 두께 축의 가운데를 돌기 가운데로 보고, 반지름 2.3~4.1 정점(돌기 둘레·밑동·끝 둥근 부분)만 바깥으로 옮긴다. 십자 홈(반지름 2 안쪽)과 몸통 원판(반지름 8.5)은 그대로.
import sys, struct
import numpy as np
b = open(sys.argv[1], 'rb').read(); n = struct.unpack('<I', b[80:84])[0]; add = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])); v = a['v'].astype(np.float64).reshape(-1, 3)
ext = v.max(0) - v.min(0); ax = int(np.argmin(ext)); o = [i for i in range(3) if i != ax]; c = (v.max(0) + v.min(0)) / 2
d = v[:, o] - c[o]; r = np.hypot(d[:, 0], d[:, 1]); m = (r >= 2.3) & (r <= 4.1)
w = v.copy(); w[m, o[0]] += d[m, 0] / r[m] * add; w[m, o[1]] += d[m, 1] / r[m] * add
t0 = v.reshape(-1, 3, 3); t1 = w.reshape(-1, 3, 3); n0 = np.cross(t0[:, 1] - t0[:, 0], t0[:, 2] - t0[:, 0]); n1 = np.cross(t1[:, 1] - t1[:, 0], t1[:, 2] - t1[:, 0])
print('옮긴 정점', int(m.sum()), '뒤집힌 면', int(np.sum(np.sum(n0 * n1, axis=1) < -1e-9)))
nrm = n1 / np.where(np.linalg.norm(n1, axis=1, keepdims=True) == 0, 1, np.linalg.norm(n1, axis=1, keepdims=True))
out = bytearray(b[:80]) + struct.pack('<I', n)
for i in range(n): out += struct.pack('<12fH', *nrm[i], *t1[i].reshape(-1), 0)
open(sys.argv[2], 'wb').write(bytes(out))
