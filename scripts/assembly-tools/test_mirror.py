# 거울 해 가르기(pnp.planar_pair·check_err) 시험 — 서 있는 판(z 일정)의 점만으로는 두 해가 같이 맞고, 평면 밖 단서 점 하나가 책과 같은 쪽을 고른다.   python test_mirror.py
import math, numpy as np, cv2
from pnp import planar_pair, check_err, cam_from
W, H, fov = 1000, 800, 30; f = (H / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]], float)
def look(C, T):
    z = (np.array(T, float) - C); z /= np.linalg.norm(z); x = np.cross(z, [0, 1.0, 0]); x /= np.linalg.norm(x); y = np.cross(z, x)
    R = np.array([x, y, z]); return cv2.Rodrigues(R)[0], (-R @ np.array(C, float)).reshape(3, 1)
for plane, C in (("z", (250.0, 180.0, 420.0)), ("y", (200.0, 400.0, 300.0)), ("x", (450.0, 150.0, 200.0))):
    g = [(a, b) for a in (0, 10, 40, 70) for b in (0, 10, 30)]
    obj = [{"z": (a, b + 20, 5.0), "y": (a, 5.0, b), "x": (5.0, b + 20, a)}[plane] for a, b in g]
    off = {"z": (20.0, 30.0, 45.0), "y": (20.0, 45.0, 10.0), "x": (45.0, 30.0, 20.0)}[plane]      # 평면에서 40mm 나온 단서 점(T축 끝 같은 것)
    rv, tv = look(np.array(C), (35, 20, 5))
    P = lambda q: cv2.projectPoints(np.float64([q]), rv, tv, K, None)[0][0][0]
    img = [P(q) for q in obj]; chk = [[list(off), [float(v) for v in P(off)]]]
    pair = planar_pair(obj, img, K)
    assert len(pair) == 2 and all(e < 3.0 for e, _, _ in pair), (plane, [e for e, _, _ in pair])      # 두 해 모두 mkfit3d 통과 기준(평균 3px) 안 — 오차만으로는 거울 해도 통과한다
    best = min(pair, key=lambda t: check_err(t[1], t[2], K, chk)); other = max(pair, key=lambda t: check_err(t[1], t[2], K, chk))
    assert np.linalg.norm(cam_from(best[1], best[2])[0] - np.array(C)) < 2, (plane, cam_from(best[1], best[2])[0])
    assert check_err(best[1], best[2], K, chk) < 1 and check_err(other[1], other[2], K, chk) > 5, plane
assert planar_pair([(0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10), (10, 10, 10)], [(0, 0)] * 5, K) == []   # 평면이 아닌 점은 거울 해가 없다
print("OK 거울 해 가르기(서 있는 판 z·누운 판 y·옆 판 x)")
