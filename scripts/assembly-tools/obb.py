# 회전한(기울어진) 부품 상자 계산 — 축에 평행한 상자(|R|·반치수)는 90° 단위로 돌린 부품에서만 맞다.
#   45° 처럼 기울어진 부품은 그 상자가 크게 부풀어 틈·겹침·소속 판정이 틀린다(조향자동차 41번: 리벳 틈 −45mm 로 잘못 나옴, 2026-11-01).
#   그래서 틈·소속·돌출 검사는 부품 자기 좌표계의 상자(OBB: 중심 p, 회전 R, 반치수 half)로 재다. 90° 단위 부품에서는 이전 결과와 같다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import itertools
import numpy as np

def corners(p, R, half):
    """상자 모서리 8개(세계 좌표)."""
    h = np.array(half, float); R = np.array(R, float); p = np.array(p, float)
    return [p + R @ (np.array(s, float) * h) for s in itertools.product((-1, 1), repeat=3)]

def span(cs, ax):
    """모서리들을 축 ax 에 투영한 (최소, 최대)."""
    v = [float(np.dot(c, ax)) for c in cs]
    return min(v), max(v)

def contains(pt, p, R, half, tol=0.3):
    """점 pt 가 상자 안인가(부품 좌표로 옮겨 재다)."""
    loc = np.array(R, float).T @ (np.array(pt, float) - np.array(p, float))
    return bool(np.all(np.abs(loc) <= np.array(half, float) + tol))

def gap_along(ax, boxA, boxB):
    """축 ax 방향으로 두 상자 사이 틈(mm). +는 떠 있음, −는 겹침. box = (p, R, half)."""
    ax = np.array(ax, float); ax = ax / np.linalg.norm(ax)
    a = span(corners(*boxA), ax); b = span(corners(*boxB), ax)
    return max(b[0] - a[1], a[0] - b[1])

def is_tilted(R, tol=1e-3):
    """R 의 세 열 중 하나라도 세계 축(±X·±Y·±Z)과 나란하지 않으면 기울어진 자세다."""
    R = np.array(R, float)
    return any(abs(float(np.max(np.abs(R[:, i]))) - 1.0) > tol for i in range(3))

def align_R(local_to_world, roll_local=None, roll_world=None):
    """부품 R 만들기: {로컬 벡터: 세계 벡터} 한두 쌍을 주면 그것을 만족하는 회전 R 을 돌려준다.
    한 쌍이면 그 축만 맞추고(나머지는 가장 작은 회전), 두 쌍이면 두 벡터를 모두 맞춘다(서로 직교여야 한다).
    예: 3단블록 구멍 축(로컬 +y)을 세계 n 으로: align_R({(0,1,0): n})."""
    pairs = [(np.array(l, float) / np.linalg.norm(l), np.array(w, float) / np.linalg.norm(w)) for l, w in local_to_world.items()]
    if len(pairs) == 1:
        a, b = pairs[0]; v = np.cross(a, b); s = np.linalg.norm(v); c = float(np.dot(a, b))
        if s < 1e-9: return np.eye(3) if c > 0 else -np.eye(3)
        K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
    (a1, b1), (a2, b2) = pairs[:2]
    a3 = np.cross(a1, a2); b3 = np.cross(b1, b2)
    return np.column_stack([b1, b2, b3]) @ np.linalg.inv(np.column_stack([a1, a2, a3]))
