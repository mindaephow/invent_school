# 앞 번호 책 그림과 판 무늬를 맞춰 이번 번호의 판 위 점을 얻는다 (2026-10-13 드롭체커 29번 — 사용자 지시 "28번 책도 있고 28번 조립도 그린 것도 있는데 왜 유추가 안 되냐").
#   python plate_match.py <이름> <앞번호> <번호> <앞 격자 라벨> [--검증 "c,r,h,x,y;…"] [--쓰기 라벨]
# 언제: 판(713프레임 등)이 앞 번호에서는 잘 보여 격자(fits)가 있는데, 이번 번호에서는 부품에 가려지거나 비스듬해 holefit·infer_grid 가 안 될 때.
# 하는 일: ① 앞 번호 격자(fits/NN_<라벨>.json 의 칸 점)로 판 평면(칸 → 앞 그림 픽셀) 호모그래피를 만든다.
#   ② 앞 그림의 판 영역과 이번 그림 전체에서 SIFT 특징점을 찾아 맞추고(비율 검사 0.8) RANSAC 호모그래피로 판 위 점만 남긴다(같은 판이면 평면 하나로 설명됨).
#   ③ 남은 점을 앞 격자로 판 칸 좌표(c,r)로 환산 — 이번 그림 픽셀 ↔ 판 칸 좌표 짝 수십 개.
#   ④ 판 구멍 무늬는 반복이라 칸이 몇 칸 밀려 맞을 수 있다(드롭체커 29번: 칸 −2·줄 +2). 밀림 후보(칸 ±8·줄 ±4)를 모두 PnP 로 풀고, **독립 검증 점**(--검증: 모델 3D 가 확정되고 이번 그림에서 픽셀을 읽은 점, 예: 앞 번호에서 놓은 리벳·블록 돌기)을
#      이 카메라로 순방향 투영해 책 픽셀과 비교(px)해 가장 맞는 밀림을 고른다(역투영 아님 — 사용자 지시). 2등과의 비를 같이 출력한다.
#   ⑤ 출력: 고른 밀림, 판 점 잔차(px), 검증 점별 차이(mm), infer_grid 에 줄 `--anchor` 문자열(파일로도 저장). --쓰기 라벨 을 주면 infer_grid 와 같은 형식의 fits 를 바로 쓰지 않고 명령만 알려 준다(저장은 infer_grid 가 기준 검사 후).
# 한계: 판이 평면이라는 가정(윗면 y 5) — 판에서 튀어나온 부품 위 특징점은 RANSAC 이 걸러낸다. 칸 밀림 검증 점이 없으면 후보가 하나로 안 갈릴 수 있으니 반드시 준다.
import sys, os, json, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit, cam_from, angles

def main():
    a = sys.argv[1:]
    if len(a) < 4: sys.exit(__doc__)
    name, prev, cur, lab = a[0], int(a[1]), int(a[2]), a[3]
    ver = []
    if "--검증" in a:
        for tok in a[a.index("--검증") + 1].split(";"):
            c, r, h, x, y = [float(v) for v in tok.split(",")]; ver.append(((c, r, h), (x, y)))
    D = os.path.join(HERE, "refs", name) + os.sep
    pf = json.load(open(D + "fits/%02d_%s.json" % (prev, lab), encoding="utf-8")); cols, rows = pf["cols"], pf["rows"]
    pim = cv2.imread(D + "%02d.jpg" % prev); cim = cv2.imread(D + "%02d.jpg" % cur); Hc, Wc = cim.shape[:2]
    cell = np.float32([[p[0], p[1]] for p in pf["pts"]]); pxp = np.float32([[p[2], p[3]] for p in pf["pts"]])
    Gp, _ = cv2.findHomography(cell, pxp, 0); Gpi = np.linalg.inv(Gp)           # 칸(c,r) ↔ 앞 그림 픽셀
    hull = cv2.convexHull(pxp.astype(np.int32)); mask = np.zeros(pim.shape[:2], np.uint8); cv2.fillConvexPoly(mask, hull, 255)
    sift = cv2.SIFT_create(nfeatures=4000)
    k1, d1 = sift.detectAndCompute(cv2.cvtColor(pim, cv2.COLOR_BGR2GRAY), mask); k2, d2 = sift.detectAndCompute(cv2.cvtColor(cim, cv2.COLOR_BGR2GRAY), None)
    m = cv2.BFMatcher().knnMatch(d1, d2, k=2); good = [x for x, y in m if x.distance < 0.8 * y.distance]
    print("특징점 앞 판 %d · 이번 그림 %d → 비율 검사 통과 매칭 %d" % (len(k1), len(k2), len(good)))
    if len(good) < 12: sys.exit("❌ 매칭이 너무 적다(%d) — 판이 너무 가려졌거나 앞 번호와 판 모양이 다르다" % len(good))
    s = np.float32([k1[x.queryIdx].pt for x in good]); d = np.float32([k2[x.trainIdx].pt for x in good])
    Hm, mk = cv2.findHomography(s, d, cv2.RANSAC, 4.0); inl = mk.ravel() == 1; print("RANSAC 인라이어 %d / %d" % (int(inl.sum()), len(good)))
    if inl.sum() < 12: sys.exit("❌ 판 평면으로 설명되는 인라이어가 너무 적다(%d)" % int(inl.sum()))
    s, d = s[inl], d[inl]
    cr = cv2.perspectiveTransform(s.reshape(-1, 1, 2), Gpi).reshape(-1, 2)      # 판 칸 좌표(c−0.5·r−0.5 틀이 아닌 fits 의 칸 번호 틀)
    P3 = lambda c, r, h: [(c - (cols + 1) / 2.0) * 10.0, h, (r - (rows + 1) / 2.0) * 10.0]
    def solve(obj, img):
        b = None
        for fv in range(10, 71, 5):
            r_ = fit(obj, img, Wc, Hc, fv)
            if r_ and (b is None or r_[0] < b[0][0]): b = (r_, fv)
        return b
    def back(rv, tv, K, px, h):
        R, _ = cv2.Rodrigues(rv); Ri = R.T; cam = -Ri @ tv.reshape(3); ray = Ri @ (np.linalg.inv(K) @ np.array([px[0], px[1], 1.0])); t = (h - cam[1]) / ray[1]; p = cam + t * ray
        return p[0] / 10.0 + (cols + 1) / 2.0, p[2] / 10.0 + (rows + 1) / 2.0
    rowsr = []
    for dc in range(-8, 9):
        for dr in range(-4, 5):
            keep = [i for i, (c, r) in enumerate(cr) if 0.5 <= c + dc <= cols + 0.5 and 0.5 <= r + dr <= rows + 0.5]   # 밀린 칸이 판 바깥이면 그 매칭은 틀린 것(판 위에 없는 구멍)
            if len(keep) < 12: continue
            obj = [P3(cr[i][0] + dc, cr[i][1] + dr, 5.0) for i in keep]; img = [tuple(d[i]) for i in keep]; b = solve(obj, img)
            if not b: continue
            (e, rv, tv, K), fv = b; pj = cv2.projectPoints(np.float32(obj), rv, tv, K, None)[0].reshape(-1, 2); er = np.hypot(*(pj - np.array(img)).T)
            vp = cv2.projectPoints(np.float32([P3(c, r, h) for (c, r, h), px in ver]), rv, tv, K, None)[0].reshape(-1, 2) if ver else None   # 순방향: 모델 3D(칸·높이) → 이 카메라 픽셀
            vd = [float(math.hypot(*(q - np.array(px)))) for q, ((c, r, h), px) in zip(vp, ver)] if ver else [0.0]
            rowsr.append((float(np.mean(vd)), dc, dr, fv, float(er.mean()), float(er.max()), vd, rv, tv, K, keep))
    rowsr.sort(key=lambda t: t[0])
    print("밀림 후보(칸·줄) — 검증 점 순방향 투영 오차(px) 작은 순:")
    for t in rowsr[:5]: print("  칸%+d 줄%+d: 검증 평균 %.1fpx | 판 잔차 평균 %.2f·최대 %.1fpx | fov %d" % (t[1], t[2], t[0], t[4], t[5], t[3]))
    b = rowsr[0]; ratio = rowsr[1][0] / max(b[0], 1e-6) if len(rowsr) > 1 else 9.9
    print("→ 고른 밀림: 칸%+d 줄%+d (2등과 검증 차이 비 %.2f, 1.5 이상이어야 유일)" % (b[1], b[2], ratio))
    if ver: print("검증 점별 순방향 투영 오차(px): %s" % [round(x, 1) for x in b[6]])
    Cc, fwd, up, right = cam_from(b[7], b[8]); az, el, rad = angles(Cc, (0, 0, 0))
    print("카메라 theta %.2f phi %.2f roll %.1f° fov %d" % (math.radians(az), math.radians(90 - el), math.degrees(math.asin(max(-1, min(1, float(right[1]))))), b[3]))
    anc = ";".join("%.3f,%.3f,%.1f,%.1f,5" % (cr[i][0] + b[1], cr[i][1] + b[2], d[i][0], d[i][1]) for i in b[10])
    print("판 안쪽으로 환산된 점 %d / %d 만 쓴다(밀린 칸이 판 바깥인 점은 잘못 맞은 매칭)" % (len(b[10]), len(cr)))
    out = os.path.join(os.environ.get("TEMP", "."), "plate_match_%s_%02d.txt" % (name, cur)); open(out, "w").write(anc)
    print("infer_grid 에 줄 앵커 %d점 → %s" % (len(b[10]), out))
    print('다음: python infer_grid.py %s %d <라벨> %d %d <모서리 8개> --anchor "$(cat %s)"' % (name, cur, cols, rows, out))
main()
