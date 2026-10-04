# 교재 그림에서 판(프레임)의 구멍 격자를 잡고, 그 위의 리벳·초록 원이 몇 번째 칸인지 계산한다 (눈대중 금지).
#   python textbook_grid.py <권> <쪽> x0 y0 x1 y1 --cols 5 --rows 2 [--out 경로.png]
#   x0 y0 x1 y1 = 판 하나만 들어오게 자른 범위(쪽 전체 0~1 비율). 판이 둘이면 따로 부른다.
# 방법: 흰 구멍(textbook_view.find_holes)의 이웃 간격 벡터 두 개로 격자를 세우고, 구멍·리벳·초록 원 위치를 격자 칸 번호(a, b)로 바꾼다.
#   a = 긴 쪽 방향(열), b = 짧은 쪽 방향(줄). 번호는 격자 안 상대 번호이고, 어느 끝이 열1인지·어느 쪽이 줄1인지는 사람이(또는 조립 방향으로) 정해 준다 — 아래 출력에 방향 벡터를 같이 적는다.
#   리벳은 구멍 위로 솟아 있어서 중심이 구멍보다 위에 보인다 → 리벳마다 같은 높이 보정을 넣어 가장 잘 맞는 값을 고른다.
import sys, os, tempfile
import numpy as np, cv2
from textbook_view import fetch_page, find_holes, find_marks
from textbook_cut import cut

def orange_blobs(img, min_area=350):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] >= 3) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 110) & (hsv[..., 2] > 120)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    return [(float(cen[i][0]), float(cen[i][1]), int(st[i][4])) for i in range(1, n) if st[i][4] >= min_area]

def fit_basis(pts):
    """구멍 중심들에서 격자 기저 벡터 a(긴 쪽), b(짧은 쪽)를 구한다: 가까운 이웃 간격 벡터를 모아 두 방향으로 묶는다."""
    P = np.array(pts)
    vecs = []
    for i, p in enumerate(P):
        d = P - p
        dist = np.hypot(d[:, 0], d[:, 1])
        for j in np.argsort(dist)[1:4]:
            v = d[j]
            if v[1] < 0 or (v[1] == 0 and v[0] < 0): v = -v
            vecs.append(v)
    V = np.array(vecs)
    best = None
    # 가장 흔한 방향 둘 찾기: 각도로 묶기
    ang = np.degrees(np.arctan2(V[:, 1], V[:, 0])) % 180
    order = np.argsort(ang)
    groups, cur = [], [order[0]]
    for k in order[1:]:
        if ang[k] - ang[cur[-1]] < 14: cur.append(k)
        else: groups.append(cur); cur = [k]
    groups.append(cur)
    if len(groups) > 1 and (ang[order[0]] + 180 - ang[groups[-1][-1]]) < 14:
        groups[0] = groups[-1] + groups[0]; groups.pop()
    groups.sort(key=len, reverse=True)
    if len(groups) < 2: return None
    a = np.median(V[groups[0]], axis=0); b = np.median(V[groups[1]], axis=0)
    return a, b

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    a = sys.argv[1:]
    out = None; cols = rows = None
    pos, neg = [], []
    for flag, lst in (("--pt", pos), ("--neg", neg)):
        while flag in a:
            i = a.index(flag); xx, yy = a[i + 1].split(","); lst.append((float(xx), float(yy))); del a[i:i + 2]
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    if "--cols" in a: i = a.index("--cols"); cols = int(a[i + 1]); del a[i:i + 2]
    if "--rows" in a: i = a.index("--rows"); rows = int(a[i + 1]); del a[i:i + 2]
    if len(a) < 6 or not cols or not rows:
        print(__doc__); sys.exit(1)
    vol, page = int(a[0]), int(a[1]); box = [float(v) for v in a[2:6]]
    img = fetch_page(vol, page); H, W = img.shape[:2]
    x0, y0, x1, y1 = int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)
    crop = img[y0:y1, x0:x1].copy()
    hs = find_holes(crop)
    rv_all = [(r[0], r[1]) for r in orange_blobs(crop)]
    mask = None
    if pos:   # 가위: 판 위의 점으로 판 하나만 오려 내고, 그 안의 구멍·리벳만 쓴다(라벨 글자·옆 부품 제외)
        mask, iou = cut(crop, [(x - x0, y - y0) for x, y in pos], [(x - x0, y - y0) for x, y in neg])
        mdil = cv2.dilate(mask, np.ones((41, 41), np.uint8))
        hs = [h for h in hs if mask[int(h[1]), int(h[0])] > 0 or mdil[int(h[1]), int(h[0])] > 0 and False]
        rv_all = [r for r in rv_all if mdil[int(r[1]), int(r[0])] > 0]
        print(f"가위로 판을 오려 냄(면적 {int((mask > 0).sum())}px, 확신도 {iou:.2f}) → 판 안의 구멍·리벳만 사용")
    if hs:   # 부품 구멍은 크기가 비슷하다 — 글자 조각 같은 작은 것(크기 중앙값의 70% 미만)은 부품이 아니라서 뺀다
        med = float(np.median([max(h[2], h[3]) for h in hs]))
        dropped = [h for h in hs if max(h[2], h[3]) < 0.7 * med]
        hs = [h for h in hs if max(h[2], h[3]) >= 0.7 * med]
        if dropped: print(f"부품이 아닌 작은 흰 조각 {len(dropped)}개는 뺐어요(글자 등).")
    holes = [(h[0], h[1]) for h in hs]
    rivets = rv_all
    rings = [(m[0], m[1]) for m in find_marks(crop)]
    print(f"흰 구멍 {len(holes)}개 · 주황 리벳 후보 {len(rivets)}개 · 초록 원 {len(rings)}개 (이 범위 안)")
    if len(holes) < 4:
        print("구멍이 4개 미만이라 격자를 못 세워요. 범위를 판 하나에 맞게 조정하세요."); sys.exit(1)
    basis = fit_basis(holes)
    if basis is None:
        print("격자 방향 두 개를 못 찾았어요."); sys.exit(1)
    A, B = basis
    # 긴 쪽을 a 로: 구멍들이 a 방향으로 더 길게 퍼져 있어야 한다 → 퍼짐이 큰 쪽을 a
    M = np.array([A, B]).T
    Minv = np.linalg.inv(M)
    h0 = np.array(holes[0])
    idx = np.array([Minv @ (np.array(h) - h0) for h in holes])
    ij = np.rint(idx).astype(int)
    res = np.hypot(*(idx - ij).T)
    ext = ij.max(0) - ij.min(0) + 1
    if ext[0] < ext[1]:   # a 가 짧은 쪽이면 서로 바꾼다
        A, B = B, A; M = np.array([A, B]).T; Minv = np.linalg.inv(M)
        idx = np.array([Minv @ (np.array(h) - h0) for h in holes]); ij = np.rint(idx).astype(int); res = np.hypot(*(idx - ij).T)
    # 줄 방향 b 는 판의 줄 수(rows)만큼만 퍼지게: B + k*A 중 줄 방향 퍼짐이 가장 작은 것을 고른다(비스듬한 기저 방지)
    bestB = None
    for k in range(-4, 5):
        B2 = B + k * A; M2 = np.array([A, B2]).T
        if abs(np.linalg.det(M2)) < 1e-6: continue
        ix = np.array([np.linalg.inv(M2) @ (np.array(h) - h0) for h in holes]); iq = np.rint(ix).astype(int)
        ex = iq.max(0) - iq.min(0) + 1; rr = float(np.hypot(*(ix - iq).T).mean())
        score = (max(ex[1], rows) - rows, rr, np.hypot(*B2))
        if bestB is None or score < bestB[0]: bestB = (score, B2)
    B = bestB[1]; M = np.array([A, B]).T; Minv = np.linalg.inv(M)
    idx = np.array([Minv @ (np.array(h) - h0) for h in holes]); ij = np.rint(idx).astype(int); res = np.hypot(*(idx - ij).T)
    print(f"격자 방향: a(열 방향)=({A[0]:.0f},{A[1]:.0f})px, b(줄 방향)=({B[0]:.0f},{B[1]:.0f})px · 구멍 격자 어긋남 평균 {res.mean():.2f}칸(0에 가까울수록 좋음)")
    amin, bmin = ij.min(0)
    def cell(p, shift=(0.0, 0.0)):
        c = Minv @ (np.array(p) + np.array(shift) - h0)
        return c
    # 리벳: 같은 높이 보정(s)을 전체에 넣어 칸 중심에 가장 가깝게 맞는 s 를 고른다(0 ~ |a| 의 1.3배, 위로 솟은 만큼 아래로 내려 구멍 자리를 구함)
    results = []
    if rivets:
        best = None
        for s in np.arange(0, np.hypot(*A) * 1.3, 1.5):
            r = []
            for rv in rivets:
                c = cell(rv, (0, s)); r.append(np.hypot(*(c - np.rint(c))))
            tot = float(np.mean(r))
            if best is None or tot < best[0]: best = (tot, s)
        tot, s = best
        print(f"리벳 높이 보정 {s:.0f}px(아래로) · 칸 중심과 어긋남 평균 {tot:.2f}칸")
        for k, rv in enumerate(rivets, 1):
            c = cell(rv, (0, s)); ci = np.rint(c).astype(int)
            results.append(("리벳%d" % k, ci))
    for k, rg in enumerate(rings, 1):
        c = cell(rg); results.append(("초록원 M%d" % k, np.rint(c).astype(int)))
    allcells = [tuple(x) for x in ij] + [tuple(r[1]) for r in results if r[0].startswith("리벳")]
    arr = np.array(allcells); a_lo, b_lo = arr.min(0); a_hi, b_hi = arr.max(0)
    span = (a_hi - a_lo + 1, b_hi - b_lo + 1)
    print(f"격자 범위(구멍+리벳): a 방향 {span[0]}칸, b 방향 {span[1]}칸 (판 크기 {cols}×{rows})")
    if span[0] < cols:
        print(f"※ a 방향이 {cols}칸보다 짧아요 → 한쪽 끝 칸이 구멍도 리벳도 안 보이는 상태(가려짐). 어느 끝인지는 그림으로 확인.")
    print("칸 번호는 (a,b) 상대 번호예요. 열1이 a 의 어느 끝인지, 줄1이 b 의 어느 쪽인지는 조립 방향으로 정해서 아래 번호에 더하세요:")
    for name, ci in results:
        print(f"  {name}: a={ci[0] - a_lo + 1}, b={ci[1] - b_lo + 1}  (격자 상대 번호, 1부터)")
    if out:
        vis = crop.copy()
        for (i, j), h in zip(ij, holes):
            cv2.putText(vis, f"{i - a_lo + 1},{j - b_lo + 1}", (int(h[0]) - 14, int(h[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1, cv2.LINE_AA)
        for name, ci in results:
            pass
        cv2.imencode(".png", vis)[1].tofile(out)
        print("저장:", out)

if __name__ == "__main__":
    main()
