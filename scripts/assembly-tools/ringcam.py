# 링 짝짓기 카메라 풀이(2026-11-10, 오토건 19번에서 만듦) — 판 격자가 없는 번호의 방향(theta·phi)을 "책 초록 링 ↔ 모델 링 자리(marks)"로 푼다.
#   python ringcam.py <이름> <번호> [--쓰지않음]
# 왜: 책 그림의 초록 링은 모델이 화면에 그리는 링 자리(asm 의 marks)와 1:1 이다 → 링 중심(2D)과 marks(3D)를 짝지으면 카메라가 나온다. 눈대중 모서리·띄움 거리 가정이 필요 없다.
# 방법: ① 책 링 추출(초록 마스크 → 얇은 화살표 열림연산 제거 → 타원 중심, 안쪽 윤곽·겹친 조각 합침)
#       ② marks 3D 를 후보 카메라(theta 전 방위·phi·roll 0)로 투영 → 크기·이동 맞춤 후 헝가리안으로 짝짓기 → 오차 최소 후보들
#       ③ 상위 후보마다 짝지어진 점으로 pnp.fit(fov 15~50) 정밀 풀이 → 평균 오차(px)·theta·phi·1·2등 비
# 판정: 점 4개 이상 · 평균 오차 ≤ 2px 이면 fit, 아니면 ⚠ 후보만 출력(저장 안 함). 1등이 2등의 1.3배 이상 좋아야 유일.
import asmpath  # 조립도 파일 자리
import sys, os, json, math
import numpy as np, cv2
from scipy.optimize import linear_sum_assignment
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
HERE = os.path.dirname(os.path.abspath(__file__))

def book_rings(path):
    """링 = 초록 고리(안쪽 구멍이 있는 닫힌 윤곽). 얇은 링은 팽창으로 이어 붙이고, 책 가장자리 연두 테두리는 잘라 낸다."""
    im = cv2.imread(path); H, W = im.shape[:2]; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (40, 70, 70), (85, 255, 255)); mg = int(0.06 * min(H, W)); m[:mg] = 0; m[-mg:] = 0; m[:, :mg] = 0; m[:, -mg:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cs, h = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE); pts = []
    for i, c in enumerate(cs):
        if h[0][i][3] < 0 or len(c) < 16: continue                     # 안쪽 윤곽(고리의 구멍)만
        ar = cv2.contourArea(c)
        if ar < 60 or ar > 6000: continue
        (x, y), (a, b), _ = cv2.fitEllipse(c)
        if max(a, b) / max(1.0, min(a, b)) > 2.2: continue
        if any(math.hypot(x - u, y - v) < 0.5 * max(a, b) for u, v in pts): continue
        pts.append((x, y))
    return np.array(pts, float), W, H

def basis(theta, phi):
    f = np.array([-math.sin(theta) * math.sin(phi), -math.cos(phi), -math.cos(theta) * math.sin(phi)])
    r = np.cross(f, [0, 1.0, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    return r, u

def score(P, Q, theta, phi):
    r, u = basis(theta, phi); A = np.c_[P @ r, -(P @ u)]
    k = min(len(A), len(Q)); best = (1e18, None, None, None)
    sa = A.std(0).mean() or 1.0; sq = Q.std(0).mean() or 1.0; s = sq / sa
    A2 = (A - A.mean(0)) * s + Q.mean(0)
    D = np.linalg.norm(A2[:, None] - Q[None], axis=2); ri, ci = linear_sum_assignment(D)
    for _ in range(3):   # 크기·이동 다시 맞춤
        a, q = A[ri], Q[ci]; s = (np.sum((a - a.mean(0)) * (q - q.mean(0)))) / max(1e-9, np.sum((a - a.mean(0)) ** 2)); t = q.mean(0) - s * a.mean(0)
        A2 = A * s + t; D = np.linalg.norm(A2[:, None] - Q[None], axis=2); ri, ci = linear_sum_assignment(D)
    return float(D[ri, ci].mean()), ri, ci

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    name, N = a[0], int(a[1])
    steps = json.load(open(asmpath.resolve(name + "_asm.json"), encoding="utf-8"))["steps"]
    M = []
    for p in steps[N - 1]["parts"]:
        for m in p.get("marks") or []: M.append(m)
    P = np.array(M, float); Q, W, H = book_rings(os.path.join(HERE, "refs", name, "%02d.jpg" % N))
    print("모델 링 자리(marks) %d개 · 책 링 %d개" % (len(P), len(Q)))
    if len(P) < 4 or len(Q) < 4: sys.exit("⚠ 점이 4개 미만 — 이 방법은 못 쓴다(윤곽 방법 bookcam.py 를 쓴다)")
    cand = []
    for th in np.arange(-math.pi, math.pi, 0.05):
        for ph in np.arange(0.15, 1.5, 0.05):
            e, ri, ci = score(P, Q, th, ph); cand.append((e, th, ph, ri, ci))
    cand.sort(key=lambda x: x[0]); res = []; seen = []
    for e, th, ph, ri, ci in cand:
        if any(abs(th - t) < 0.3 and abs(ph - p) < 0.3 for t, p in seen): continue
        seen.append((th, ph))
        if len(ri) >= 4:
            obj = [P[i].tolist() for i in ri]; img = [Q[j].tolist() for j in ci]; best = None
            for fv in (15, 20, 25, 30, 40, 50):
                r = fit(obj, img, W, H, fv)
                if r and (best is None or r[0] < best[0][0]): best = (r, fv)
            if best:
                (er, rv, tv, K), fv = best; C, fwd, up, right = cam_from(rv, tv)
                res.append((er, math.atan2(-fwd[0], -fwd[2]), math.acos(-fwd[1]), fv, len(ri)))
        if len(seen) >= 8: break
    res.sort(key=lambda x: x[0])
    for er, th, ph, fv, n in res[:5]: print("오차 %.2fpx  theta %.3f  phi %.3f  fov %d  짝 %d점" % (er, th, ph, fv, n))
    if len(res) >= 2: print("1·2등 비 %.2f (1.3 이상이어야 유일)" % (res[1][0] / max(1e-9, res[0][0])))
    if res and res[0][0] <= 2.0: print("✅ fit 후보(오차 2px 이내)")
    else: print("⚠ 오차 2px 초과 — 후보만 참고(저장 안 함)")

if __name__ == "__main__": main()
