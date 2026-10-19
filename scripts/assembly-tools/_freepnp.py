# 롤(기울기)이 큰 책 그림용: 위쪽이 위인 조건 없이 PnP(fov·주점 격자) — 점 목록 json: {"obj":[[x,y,z]..],"img":[[px,py]..]}  python _freepnp.py <이름> <번호> <json>
import sys, json, math, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N = sys.argv[1], int(sys.argv[2]); a = json.load(open(sys.argv[3], encoding="utf-8")); obj = np.array(a["obj"], float); img = np.array(a["img"], float)
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; cc = obj.mean(0); res = []
for fov in range(14, 71, 4):
    f = (H / 2) / math.tan(math.radians(fov) / 2); K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]], float)
    for ith in np.linspace(-math.pi, math.pi, 9)[:-1]:
        for iph in (0.3, 0.8, 1.3, 1.8, 2.3):
            for roll in (0, 1.57, 3.14, -1.57):
                for dist in (250, 450, 700):
                    d = np.array([math.sin(ith) * math.sin(iph), math.cos(iph), math.cos(ith) * math.sin(iph)]) * dist
                    z = -d / np.linalg.norm(d); x = np.cross([0, 1.0, 0], z); x /= np.linalg.norm(x); y = np.cross(z, x)
                    c, s = math.cos(roll), math.sin(roll); x2 = c * x + s * y; y2 = -s * x + c * y
                    R0 = np.array([x2, y2, z]); rv0, _ = cv2.Rodrigues(R0); tv0 = (-R0 @ d).reshape(3, 1)
                    try: ok, rv, tv = cv2.solvePnP(obj - cc, img, K, None, rvec=rv0.copy(), tvec=tv0.copy(), useExtrinsicGuess=True, flags=cv2.SOLVEPNP_ITERATIVE)
                    except cv2.error: continue
                    if not ok: continue
                    pr = cv2.projectPoints(obj - cc, rv, tv, K, None)[0].reshape(-1, 2); e = np.linalg.norm(pr - img, axis=1)
                    Rm = cv2.Rodrigues(rv)[0]; Cw = -Rm.T @ tv.reshape(3)
                    if (Rm @ (obj - cc).T + tv)[2].min() <= 0: continue
                    res.append((float(e.mean()), fov, rv, tv, e, Cw))
import os
SIDE=os.environ.get('CAMZ')
if SIDE: res=[t for t in res if (t[5][2]+cc[2])*float(SIDE)>0]
res.sort(key=lambda t: t[0])
seen = []
if res:
    _e, _fov, _rv, _tv, _per, _Cw = res[0]; json.dump({"fov": _fov, "rv": _rv.reshape(3).tolist(), "tv": _tv.reshape(3).tolist(), "err": _e, "cc": cc.tolist()}, open("refs/%s/anchors/%02d_free.json" % (name, N), "w"))   # 가장 좋은 풀이를 _anchor_fit(free) 이 읽는다
for e, fov, rv, tv, per, Cw in res[:400]:
    key = (round(Cw[0] / 40), round(Cw[1] / 40), round(Cw[2] / 40))
    if key in seen: continue
    seen.append(key); Rm = cv2.Rodrigues(rv)[0]; up = -Rm.T @ np.array([0, 1.0, 0]) * -1
    th = math.atan2(Cw[0], Cw[2]); ph = math.acos(max(-1, min(1, Cw[1] / np.linalg.norm(Cw))))
    print("오차 %.2fpx fov %d | 카메라 방향 theta %.2f phi %.2f 거리 %.0f | 점별 %s" % (e, fov, th, ph, np.linalg.norm(Cw), per.round(1).tolist()))
    if len(seen) >= 6: break
