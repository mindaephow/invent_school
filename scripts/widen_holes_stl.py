# 큐보 프레임 STL 의 구멍 목 지름을 키우고(기본 6.2mm) 입구·테두리도 같은 만큼 같이 키운다 — 프린트용(노즐 0.4·PLA, 2026-10-22).
#   python scripts/widen_holes_stl.py <입력.stl> <출력.stl> [목지름=6.2]
# 방법: 구멍 가운데(목 원통 정점의 지름 쌍 가운데점)를 찾고, 구멍마다 반지름 r 을 r' = r + d (2.75 ≤ r ≤ 4.0: 목·입구·테두리 안/밖 전부 같은 d)로 옮긴다.
#   4.0 보다 바깥 5.0 까지는 d 에서 0 으로 선형으로 줄여(단조) 면이 뒤집히지 않게 하고, 5.0 밖 정점은 그대로 둔다(테두리 폭 0.5 유지, 가장자리 벽은 구멍 곁에서만 살짝 바깥으로 밀린다).
import sys, struct
import numpy as np
from scipy.spatial import cKDTree
def load(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return b[:80], a['v'].astype(np.float64).reshape(-1, 3)
def save(p, head, v):
    t = v.reshape(-1, 3, 3); nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); ln = np.linalg.norm(nrm, axis=1, keepdims=True); nrm = nrm / np.where(ln == 0, 1, ln)
    out = bytearray(head) + struct.pack('<I', len(t))
    for i in range(len(t)): out += struct.pack('<12fH', *nrm[i], *t[i].reshape(-1), 0)
    open(p, 'wb').write(bytes(out))
def main():
    src, dst = sys.argv[1], sys.argv[2]; dia = float(sys.argv[3]) if len(sys.argv) > 3 else 6.2
    head, v = load(src); d = dia / 2 - 2.75
    ext = v.max(0) - v.min(0); ax = int(np.argmin(ext)); o = [i for i in range(3) if i != ax]
    P = v[:, o]; t = v[:, ax] - v[:, ax].min()
    lv = P[(np.abs(t - 1.0) < 0.05) | (np.abs(t - 4.0) < 0.05)]; lv = np.unique(np.round(lv, 3), axis=0)   # 목이 시작·끝나는 높이의 점들
    tree = cKDTree(lv); mids = []
    for i, j in tree.query_pairs(5.5 + 0.03):
        if abs(np.linalg.norm(lv[i] - lv[j]) - 5.5) < 0.03: mids.append((lv[i] + lv[j]) / 2)
    mids = np.array(mids); mt = cKDTree(mids); seen = np.zeros(len(mids), bool); cent = []
    for i in range(len(mids)):   # 가까운 가운데점(0.3 안)을 한 구멍으로 묶고 평균을 구멍 가운데로 쓴다(반올림 안 함 — 135도처럼 칸 사이가 대각선인 프레임도 맞는다)
        if seen[i]: continue
        grp = mt.query_ball_point(mids[i], 0.3); seen[grp] = True
        if len(grp) >= 6: cent.append(mids[grp].mean(axis=0))
    cent = np.array(cent)
    print('구멍', len(cent), '개 찾음', cent.round(2).tolist()[:6], '...')
    ct = cKDTree(cent); dist, idx = ct.query(P); r = dist
    shift = np.where(r < 2.7, 0.0, np.where(r <= 4.05, d, np.where(r < 4.75, d * (4.75 - r) / (4.75 - 4.05), 0.0)))
    dirv = (P - cent[idx]) / np.where(r == 0, 1, r)[:, None]
    P2 = P + dirv * shift[:, None]
    w = v.copy(); w[:, o] = P2
    # 면 뒤집힘 검사
    def nr(x):
        tt = x.reshape(-1, 3, 3); return np.cross(tt[:, 1] - tt[:, 0], tt[:, 2] - tt[:, 0])
    n0, n1 = nr(v), nr(w); dot = np.sum(n0 * n1, axis=1); flipped = int(np.sum(dot < -1e-9)); degen = int(np.sum(np.linalg.norm(n1, axis=1) < 1e-9) - np.sum(np.linalg.norm(n0, axis=1) < 1e-9))
    print('뒤집힌 면', flipped, '새로 납작해진 면', degen)
    if flipped and len(sys.argv) > 4:
        for k in np.where(dot < -1e-9)[0][:8]:
            print('  tri', k, 'r', np.round(r[k*3:k*3+3], 2), 'P', np.round(P[k*3:k*3+3], 2).tolist(), 't', np.round(t[k*3:k*3+3], 2).tolist())
    save(dst, head, w)
main()
