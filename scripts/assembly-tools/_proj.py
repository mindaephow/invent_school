# 번호의 앵커 풀이 카메라로 3D 점을 책 그림 픽셀로 투영한다 / 픽셀을 한 평면에 되투영한다 (2026-10-19)
#   python _proj.py <이름> <번호> "x,y,z;x,y,z"            → 픽셀
#   python _proj.py <이름> <번호> --평면 y "px,py;px,py"   → 그 높이 평면(y=값) 위 3D 좌표
import sys, json, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
name, N = sys.argv[1], int(sys.argv[2]); a = json.load(open("refs/%s/anchors/%02d.json" % (name, N), encoding="utf-8"))
obj = np.array(a["obj"], float); img = np.array(a["img"], float); im = cv2.imread("refs/%s/%02d.jpg" % (name, N)); H, W = im.shape[:2]; cc = obj.mean(0)
e, rv, tv, K = fit(obj - cc, img, W, H, int(a["fov"]), a.get("cx"), a.get("cy"))
P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - cc]), rv, tv, K, None)[0][0][0]
if sys.argv[3] == "--평면":
    y0 = float(sys.argv[4]); R_, _ = cv2.Rodrigues(rv); Ci = np.linalg.inv(K)
    for t in sys.argv[5].split(";"):
        u, v = [float(x) for x in t.split(",")]; d = R_.T @ (Ci @ np.array([u, v, 1.0])); o = -R_.T @ np.array(tv).reshape(3)
        s = (y0 - cc[1] - o[1]) / d[1]; q = o + s * d + cc; print("(%g,%g) → x %.1f z %.1f" % (u, v, q[0], q[2]))
else:
    for t in sys.argv[3].split(";"):
        q = [float(x) for x in t.split(",")]; p = P(q); print("%s → (%.0f, %.0f)" % (q, p[0], p[1]))
print("오차 %.2fpx" % e)
