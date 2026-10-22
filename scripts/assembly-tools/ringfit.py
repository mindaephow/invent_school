# 확실한 3D 점(링·돌기·구멍)과 책 픽셀 짝으로 카메라를 풀어 fits/NN_P.json 에 쓴다 — 판 격자가 없거나 가려진 번호(2026-10-23 트레일러 6번).
#   python ringfit.py <이름> <번호> 점파일.json [--fov a,b] [--dry]   점파일 = [{"xyz":[x,y,z],"px":[u,v]}, …] (모델 좌표 — 띄운 부품 링은 띄움까지 더한 값)
#   fov 를 a~b 에서 찾는다(기본 15,60). 출력: 평균 오차·fov·theta·phi, 점별 오차. 통과 기준 오차 2px — 넘으면 ⚠(쓸 수는 있다).
import sys, os, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
from pnp import fit, cam_from
name, N, pf = sys.argv[1], int(sys.argv[2]), sys.argv[3]; fr = (15, 60); dry = "--dry" in sys.argv
if "--fov" in sys.argv: fr = tuple(int(v) for v in sys.argv[sys.argv.index("--fov") + 1].split(","))
pts = json.load(open(pf, encoding="utf-8")); O = np.array([p["xyz"] for p in pts], float); I = [list(map(float, p["px"])) for p in pts]; c = O.mean(0)
im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; best = None
for fov in range(fr[0], fr[1] + 1):
    r = fit(O - c, I, W, H, fov, None, None)
    if r and (best is None or r[0] < best[0]): best = (r[0], fov, r[1], r[2], r[3])
e, fov, rv, tv, K = best; C, fwd, up, right = cam_from(rv, tv)
pr = cv2.projectPoints(np.float32(O - c), rv, tv, K, None)[0].reshape(-1, 2); res = np.linalg.norm(pr - np.array(I), axis=1)
print("점 %d개 평균 %.2fpx 최대 %.1fpx fov %d theta %.3f phi %.3f" % (len(O), e, res.max(), fov, np.arctan2(-fwd[0], -fwd[2]), np.arccos(-fwd[1]))); print("점별:", np.round(res, 1).tolist())
if not dry:
    out = {"cols": len(O), "rows": 1, "pts": [[i + 1, 1, I[i][0], I[i][1]] for i in range(len(O))], "est": [], "name": "%s %d번: 링·돌기 %d점 PnP 평균 %.2fpx(fov %d) — ringfit.py" % (name, N, len(O), e, fov), "tool": "ringfit", "err_px": round(float(e), 2), "max_err_px": round(float(res.max()), 2), "found": len(O), "found_ratio": 1.0, "mode": "ring+PnP", "xyz3d": [list(map(float, q)) for q in O], "xyz3d_img": I, "fov": fov}
    Pp = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]; g0 = Pp(c); gl = {}
    for k, v in (("X", (50, 0, 0)), ("Y", (0, 50, 0)), ("Z", (0, 0, 50))): d = Pp(c + np.array(v, float)) - g0; gl[k] = [float(d[0]), float(d[1])]
    sc = 55.0 / max(abs(x) for v in gl.values() for x in v); gl = {k: [round(x * sc, 1) for x in v] for k, v in gl.items()}
    ax = {"global": gl, "fit": {"from": "%02d_P.json ringfit 점 %d개 PnP" % (N, len(O)), "err_px": round(float(e), 2), "points": len(O), "theta": round(float(np.arctan2(-fwd[0], -fwd[2])), 2), "phi": round(float(np.arccos(-fwd[1])), 2), "cols": "+X", "rows": "+Y", "fov": fov}, "no_rotate": True, "no_lines": True}
    json.dump(ax, open("refs/%s/%02d_axes.json" % (name, N), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"M": [[1, 0, 0], [0, 1, 0]], "size": [W, H], "angle": 0.0, "crop": [0, 0, W, H], "erase": []}, open("refs/%s/%02d_lv.json" % (name, N), "w"))
    os.makedirs("refs/%s/fits" % name, exist_ok=True); json.dump(out, open("refs/%s/fits/%02d_P.json" % (name, N), "w", encoding="utf-8"), ensure_ascii=False); print("저장: fits/%02d_P.json" % N)
