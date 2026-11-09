# 기울어진 판의 카메라 자동 계산 — axes_fit(축에 정렬된 판 전용)이 못 푸는 판(예: 3륜바이크 24번 손잡이 37프레임)용. 읽기만 하고 <번호>_axes.json 만 쓴다.
#   python tiltcam.py <이름> <번호> <라벨> <부품이름> [--그림 NN] [--쓰기]   (--그림 NN: 판 위치는 <번호>(그 부품이 들어간 번호)로 읽고, 구멍 점·그림은 NN 의 것 — 예: 완성 사진 00)
# 하는 일: holefit 가 찾은 구멍 점(fits/NN_<라벨>.json 의 est 아닌 점)과 모델 판 구멍의 3D 좌표(그 번호 자세 + 띄움)를 칸·줄 뒤집기 4가지로 짝지어
#   pnp.fit 으로 카메라를 풀고, 카메라가 바로 서 있는(up.y>0·phi<π/2) 해 중 오차가 가장 작은 것을 고른다. theta=atan2(−fwd.x,−fwd.z), phi=acos(−fwd.y) (뷰어 updateCamera 와 같은 식).
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, math, itertools
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
import violations, stepchecks, pnp
if len(sys.argv) < 5: sys.exit(__doc__)
name, step, label, part = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
A = violations._load(name)
for q in A.parts:
    if q.step.index <= step: q.p, q.R = stepchecks.pose_at(A, q, step)
pl = next(q for st_ in A.steps for q in st_.parts if q.n == part) if "--그림" in sys.argv else next(q for q in A.steps[step - 1].parts if q.n == part)   # 완성 사진처럼 번호 밖이면 그 부품이 처음 나온 곳
R = os.path.join(os.path.dirname(asmpath.resolve(name + ".py")), "..", "..", "..", "..", "refs", name)
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", name))
IMG = int(sys.argv[sys.argv.index("--그림") + 1]) if "--그림" in sys.argv else step   # 구멍 점·그림 번호
fj = json.load(open(os.path.join(R, "fits", "%02d_%s.json" % (IMG, label)), encoding="utf-8"))
est = {tuple(e) for e in fj["est"]} if not isinstance(fj.get("est"), int) else set()
pts = [p for p in fj["pts"] if (p[0], p[1]) not in est]
cols, rows = int(fj["cols"]), int(fj["rows"])
im = cv2.imread(os.path.join(R, "%02d.jpg" % IMG)); H, W = im.shape[:2]
hv = np.array(pl.extra.get("dir") or [0, 1, 0], float) * float(pl.extra.get("hover") or 0)   # 결합 전 모습이면 띄움만큼 떠 있다(판 위치는 평행이동이라 각도엔 영향 없다)
ids = lambda c, r, fc, fr: "h%d" % (rows * ((cols + 1 - c if fc else c) - 1) + (rows + 1 - r if fr else r))
best = None
for fc, fr in itertools.product([0, 1], [0, 1]):
    obj = [np.array(pl.hole(ids(int(c), int(r), fc, fr))["pos"], float) + hv for c, r, x, y in pts]; img = [[x, y] for c, r, x, y in pts]
    for fov in range(20, 71, 5):
        try: res = pnp.fit(obj, img, W, H, fov)
        except Exception: continue
        if res is None: continue
        e, rv, tv, K = res; C, fwd, up, right = pnp.cam_from(rv, tv)
        theta = math.atan2(-fwd[0], -fwd[2]); phi = math.acos(-fwd[1])
        if up[1] <= 0.05 or phi >= math.pi / 2: continue   # 뒤집힌 해(카메라가 아래에서 보는 해) 제외
        if best is None or e < best[0]: best = (float(e), fc, fr, fov, theta, phi, rv, tv, K, np.mean(obj, 0))
if best is None: sys.exit("❌ 바로 선 카메라 해를 못 찾았다 — 구멍 점(fits)·부품 이름을 확인한다")
e, fc, fr, fov, theta, phi, rv, tv, K, ctr = best
g = {}
for ax, v in zip("XYZ", np.eye(3)):
    pp, _ = cv2.projectPoints(np.array([ctr, ctr + v * 50.0]), rv, tv, K, None); d = pp[1, 0] - pp[0, 0]; d = d / (np.linalg.norm(d) or 1) * 55
    g[ax] = [round(float(d[0]), 1), round(float(d[1]), 1)]
out = {"global": g, "fit": {"from": "%02d_%s.json" % (step, label), "err_px": round(e, 2), "points": len(pts), "theta": round(theta, 2), "phi": round(phi, 2), "cols": "기울어진 판(칸 뒤집기 %d)" % fc, "rows": "기울어진 판(줄 뒤집기 %d)" % fr, "tool": "tiltcam", "fov": fov}}
print("✅ %s %d번: 오차 %.2fpx · 점 %d개 · fov %d · theta %.2f · phi %.2f (칸뒤집기 %d·줄뒤집기 %d)" % (name, step, e, len(pts), fov, theta, phi, fc, fr))
if "--쓰기" in sys.argv:
    json.dump(out, open(os.path.join(R, "%02d_axes.json" % step), "w", encoding="utf-8"), ensure_ascii=False); print("→ refs/%s/%02d_axes.json 저장" % (name, step))
