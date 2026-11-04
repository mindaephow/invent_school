# 8번(5번의 거울 쪽): 7번 조립(블록 둘) + 단독 블록 + 135도 프레임 실루엣 겹침으로 배치 가설과 카메라를 푼다
import sys, math, os
os.environ["STEP"] = "8"
sys.path.insert(0, "."); sys.path.insert(0, "C:/Users/user/Downloads/invent_school/scripts/assembly-tools")
import numpy as np, cv2
from scipy.optimize import minimize
import silfit7 as S7
sys.stdout.reconfigure(encoding="utf-8")
HF = {"h%d" % i: v for i, v in enumerate([(-34.5, -9.5), (-27.5, -2.5), (-20.5, 4.5), (-13.5, 11.5), (-3.5, 11.5), (6.5, 11.5), (16.5, 11.5), (26.5, 11.5), (36.5, 11.5)], 1)}
def frame_pieces(hw=5.0, ext=5.0, es=6.15, ee=6.15):
    hs = [HF["h%d" % i] for i in range(1, 10)]; P = []
    for (x0, z0), (x1, z1) in zip(hs[:-1], hs[1:]):
        d = np.array([x1 - x0, z1 - z0]); L = np.linalg.norm(d); d /= L; n = np.array([-d[1], d[0]]); pts = []
        e0 = es if (x0, z0) == HF["h1"] else ext; e1 = ee if (x1, z1) == HF["h9"] else ext
        for e in ((x0, z0, -e0), (x1, z1, e1)):
            for sn in (-hw, hw):
                for sy in (-2.5, 2.5): pts.append([e[0] + n[0] * sn + d[0] * e[2], sy, e[1] + n[1] * sn + d[1] * e[2]])
        P.append(np.array(pts, float))
    return P
# 책 마스크의 구멍(프레임 구멍·링 속 흰 곳)은 모델 실루엣(속이 찬 볼록 조각)과 비교하려고 메운다
_c, _ = cv2.findContours(S7.book, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); _f = np.zeros_like(S7.book); cv2.drawContours(_f, _c, -1, 1, -1); S7.book = _f; S7.noign = (S7.noign & (np.arange(S7.Ww)[None, :] + 0 * np.arange(S7.Hh)[:, None] < 840) | (np.zeros_like(S7.noign, bool))) if False else S7.noign.copy(); S7.noign[600:, 840:] = False   # 쪽 번호 '8' 은 부품이 아니다
FP = frame_pieces()
RF_A = np.array([[0, 0, -1.0], [0, 1.0, 0], [1.0, 0, 0]])    # 가설 a: x̂→+Z, ŷ→+Y, ẑ→−X (비스듬한 팔이 +X 쪽으로 — 5번의 거울)
RF_B = np.array([[0, 0, 1.0], [0, -1.0, 0], [1.0, 0, 0]])    # 가설 b: 5번과 같은 프레임 자세
RS_A = np.array([[-0.70710678, 0.70710678, 0.0], [0, 0, 1.0], [0.70710678, 0.70710678, 0.0]])
RS_B = np.array([[0.70710678, 0.70710678, 0.0], [0, 0, 1.0], [0.70710678, -0.70710678, 0.0]])
def scene(hyp, hover, hw=5.0, es=6.15, ee=6.15):
    RF = RF_A if hyp == "a" else RF_B; RS = RS_A if hyp == "a" else RS_B
    h9 = np.array([-10.0, 17.5 + hover, -5.0]); org = h9 - RF @ np.array([HF["h9"][0], 0.0, HF["h9"][1]])
    out = [(RF @ pc.T).T + org for pc in frame_pieces(hw, 5.0, es, ee)]
    h2 = org + RF @ np.array([HF["h2"][0], 0.0, HF["h2"][1]]); cS = np.array([h2[0], 10.0, h2[2]])
    out += [(RS @ pc.T).T + cS for pc in S7.PIECES]
    out += [(S7.RB @ pc.T).T + np.array([0, 10.0, -5.0]) for pc in S7.PIECES]
    out += [(S7.RA @ pc.T).T + np.array([-10.0, 10.0, -25.0]) for pc in S7.PIECES]
    return out
def render(p, hyp):
    az, el, dist, fov, ox, oy, hover = p[:7]; hw = p[7] if len(p) > 7 else 5.0; es = p[8] if len(p) > 8 else 6.15; ee = p[9] if len(p) > 9 else 6.15; rv, tv, K = S7.mk_cam(az, el, dist, fov, ox, oy); m = np.zeros((S7.Hh, S7.Ww), np.uint8)
    for pc in scene(hyp, hover, hw, es, ee):
        q = cv2.projectPoints(pc, rv, tv, K, None)[0].reshape(-1, 2)
        if not np.all(np.isfinite(q)) or np.abs(q).max() > 1e5: return None
        cv2.fillConvexPoly(m, cv2.convexHull(q.astype(np.float32)).astype(np.int32), 1)
    return m
def loss(p, hyp):
    if p[3] < 8 or p[3] > 60 or p[6] < 0 or p[6] > 120 or p[2] < 50 or p[2] > 3000 or p[1] < 5 or p[1] > 85 or (len(p) > 7 and not 4.0 <= p[7] <= 8.0) or (len(p) > 9 and not (0.0 <= p[8] <= 14.0 and 0.0 <= p[9] <= 14.0)): return 9.0
    m = render(p, hyp)
    if m is None: return 9.0
    a = m & S7.noign.astype(np.uint8); b = S7.book & S7.noign.astype(np.uint8)
    return 1.0 - int((a & b).sum()) / max(1, int((a | b).sum()))
if __name__ == "__main__":
    import pickle; res = []; pk = pickle.load(open(S7.SP + "sil8_res.pkl", "rb")); pa = [t for t in pk if t[1] == "a"][0][2]
    HWF = 4.8
    r = minimize(loss, list(pa)[:7], args=("a",), method="Powell", options={"maxiter": 8, "xtol": 1e-2, "ftol": 1e-6}); r = minimize(loss, r.x, args=("a",), method="Powell", options={"maxiter": 8, "xtol": 1e-2, "ftol": 1e-6})
    print("가설 a → IoU %.3f 띄움 %.1f fov %.1f (프레임 반폭 5·끝 7.2/5.2 고정)" % (1 - r.fun, r.x[6], r.x[3]))
    pb = [t for t in pk if t[1] == "b"][0]; pickle.dump([(r.fun, "a", list(r.x)), pb], open(S7.SP + "sil8_res.pkl", "wb"))
    f, hyp, p = r.fun, "a", list(r.x); m = render(p, hyp); ov = S7.im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/cubo_crops/sil8.png"); sys.exit()
    for hyp in ("a", "b"):
        best = None
        for az in range(0, 360, 30):
            for el in (25, 40, 55):
                p0 = [az, el, 330.0, 22.0, 0.0, 0.0, 30.0]; l = loss(p0, hyp)
                if best is None or l < best[0]: best = (l, p0)
        p = best[1]
        for rnd in range(3):
            r = minimize(loss, p, args=(hyp,), method="Powell", options={"maxiter": 6, "xtol": 1e-2, "ftol": 1e-5}); p = list(r.x)
        print("가설 %s → IoU %.3f az %.0f el %.0f fov %.1f 띄움 %.1f" % (hyp, 1 - r.fun, p[0], p[1], p[3], p[6])); res.append((r.fun, hyp, p))
    res.sort(key=lambda t: t[0]); print("1등", res[0][1], "비 %.2f" % (res[1][0] / max(res[0][0], 1e-6)))
    pickle.dump(res, open(S7.SP + "sil8_res.pkl", "wb"))
    f, hyp, p = res[0]; m = render(p, hyp); ov = S7.im.copy(); ov[m > 0] = (0.55 * ov[m > 0] + 0.45 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.imencode(".png", ov)[1].tofile("C:/Users/user/AppData/Local/Temp/cubo_crops/sil8.png")
