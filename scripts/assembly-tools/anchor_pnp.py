# 앞 번호에서 조립한 모델(3D)로 이번 번호의 격자·카메라를 푼다 — 규칙 C3 ⓪ 의 도구(2026-11-13, 배틀로봇 8번을 링 점으로 풀다 막힌 뒤).
#   python anchor_pnp.py <이름> <번호> <holefit 라벨> <spec.json> [--쓰기 라벨]
#   ① 책 그림에서 구멍이 선명한 판을 holesearch/holefit 로 먼저 잡는다(fits/NN_<라벨>.json — 칸·줄·픽셀).
#   ② spec.json = {"plate": "315프레임", "rowsets": [[1,2],[2,1],[3,2],[2,3]]("책 줄1·줄2 가 모델 판의 몇 줄인가 후보"), "cols_total": 15,
#                  "anchors": [{"step": 4, "part": "15프레임", "n": 2, "holes": ["홀면 +y 1", …], "px": [[148,327], …]}, …]}   (비평면 점 — 거울·옆면 해를 가른다)
#   ③ 판 후보(모델에서 그 이름의 부품들) × 줄 후보 × 칸 방향(정/반대) 을 모두 풀어, 앵커까지 포함한 PnP 오차가 가장 작은 조합을 고른다 → 3D↔픽셀 spec 을 만들어 mkfit3d.py 로
#      fits/NN_<라벨>.json·NN_axes.json 을 쓴다(--쓰기). 안 쓰면 후보 표만 보여 준다.
#   3D 는 모두 앞 번호 모델(이번 번호 자세, stepchecks.pose_at)에서 계산한다 — 손으로 좌표를 적지 않는다.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, math, runpy, subprocess, tempfile
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asmlib as al, stepchecks
from pnp import cam_from, angles
if len(sys.argv) < 5: sys.exit(__doc__)
name, N, label, spec = sys.argv[1], int(sys.argv[2]), sys.argv[3], json.load(open(sys.argv[4], encoding="utf-8"))
write = "--쓰기" in sys.argv; wlabel = sys.argv[sys.argv.index("--쓰기") + 1] if write and len(sys.argv) > sys.argv.index("--쓰기") + 1 else label
g = runpy.run_path(asmpath.ap(name, ".py"), run_name="probe"); A = g["A"]
D = os.path.join(HERE, "refs", name); fp = os.path.join(D, "fits", "%02d_%s.json" % (N, label))
bak = fp.replace(".json", "_holefit.json.bak")
src = bak if os.path.exists(bak) else fp   # 앞서 이 도구가 덮어썼으면 holefit 원본(.bak)을 쓴다
pts = json.load(open(src, encoding="utf-8"))["pts"]; cmax = max(p[0] for p in pts)
def hw(part, lab, sgn=0):
    hid = al._item(part, lab, "홀")[0]; h = [h for h in part.conn["holes"] if h["id"] == hid][0]; pp, RR = stepchecks.pose_at(A, part, N)
    loc = np.array(h["pos"], float) + sgn * np.array(h["dir"], float) * float(h.get("len", 0)) / 2   # sgn: 책에 보이는 면(구멍 축 ±쪽) — 두께 가운데가 아니라 보이는 면의 구멍을 읽었다
    return np.array(pp, float) + np.array(RR, float) @ loc
plates = [p for st in A.steps[:N] for p in st.parts if p.n == spec["plate"]]
anch = []
anch_def = []
for a in spec.get("anchors", []):
    ps = [p for p in A.steps[a["step"] - 1].parts if p.n == a["part"]]; part = ps[a.get("n", 1) - 1]
    for h, px in zip(a["holes"], a["px"]): anch_def.append((part, h, list(px)))
anch = [(hw(pt, h), px) for pt, h, px in anch_def]
H, W = 877, 1000; res = []
face = spec.get("face", "+y"); ctot = spec.get("cols_total", cmax)
for pi, p in enumerate(plates):
    for rs in spec["rowsets"]:
        for flip, sh, sg, sa in [(f_, s_, g_, a_) for f_ in (False, True) for s_ in spec.get("col_shifts", [0]) for g_ in spec.get("faces", [0]) for a_ in (spec.get("faces", [0]) if anch_def else [0])]:   # 칸 밀림(C3 ④): 판 구멍 무늬는 반복이라 한두 칸 밀려 맞을 수 있다
            try:
                if spec.get("transpose"):   # 책 격자의 칸이 모델 판의 줄, 책의 줄이 모델 판의 열(긴 쪽)인 경우 — holesearch 가 칸·줄 수를 바꿔 통과한 번호(배틀로봇 10번)
                    _rt = max(q[1] for q in pts); PG = [hw(p, "홀면 %s 열%d·줄%d" % (face, ((_rt + 1 - r) if flip else r) + sh, rs[c - 1]), sg) for c, r, x, y in pts]
                else: PG = [hw(p, "홀면 %s 열%d·줄%d" % (face, ((ctot + 1 - c) if flip else c) + sh, rs[r - 1]), sg) for c, r, x, y in pts]
            except Exception: continue
            obj = np.array(PG + [hw(pt, h, sa) for pt, h, px in anch_def], float); img = np.array([[x, y] for c, r, x, y in pts] + [a[1] for a in anch], float); oc = obj - obj.mean(0)
            for fov in spec.get("fovs", (8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45)):
                fl = (H / 2) / math.tan(math.radians(fov) / 2); K = np.array([[fl, 0, W / 2], [0, fl, H / 2], [0, 0, 1]], float)
                sols = []
                try:
                    ok, rv, tv = cv2.solvePnP(oc, img, K, None, flags=cv2.SOLVEPNP_EPNP); ok, rv, tv = cv2.solvePnP(oc, img, K, None, rv, tv, True, flags=cv2.SOLVEPNP_ITERATIVE); sols.append((rv, tv))
                except Exception: pass
                if not anch:   # 점이 한 평면(앵커 없음)이면 거울 해가 둘 — IPPE 로 둘 다 구해 위에서 보는 해를 고른다
                    try:
                        n_, rvs_, tvs_, _e = cv2.solvePnPGeneric(oc, img, K, None, flags=cv2.SOLVEPNP_IPPE); sols += list(zip(rvs_, tvs_))
                    except Exception: pass
                for rv, tv in sols:
                    pr, _ = cv2.projectPoints(oc, rv, tv, K, None); e = np.sqrt(((pr.reshape(-1, 2) - img) ** 2).sum(1))
                    C, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(C, (0, 0, 0)); ph = math.radians(90 - el)
                    if ph > 1.55 or up[1] <= 0: continue   # 위에서 보고 위쪽이 위인 해만
                    res.append((float(e.mean()), float(e[len(pts):].mean()) if anch else 0.0, pi, rs, (flip, sh, sg, sa), fov, math.radians(az), ph, obj, img))
res.sort(key=lambda r: r[0])
print("후보(앵커 %d개 포함, 오차 낮은 순) — 평균px · 앵커px · 판# · 줄 · (칸반대, 칸밀림, 판면, 앵커면) · fov · θ · φ" % len(anch))
for r in res[:int(spec.get("show", 6))]: print("  %.1f · %.1f · %d · %s · %s · %d · %.2f · %.2f" % r[:8])
if not res: sys.exit("❌ 맞는 후보가 없다 — plate 이름·줄 후보·holefit 점을 다시 본다")
if len(res) > 1 and res[1][0] < res[0][0] * 1.5 and (res[1][2:5] != res[0][2:5]): print("⚠ 1등과 2등의 오차가 비슷하다(비 %.2f) — 앵커를 더 읽어 가른다" % (res[1][0] / max(res[0][0], 1e-6)))
if not write: sys.exit(0)
b = res[0]; obj, img = b[8], b[9]; p = plates[b[2]]; rs, (flip, sh, sg, sa) = b[3], b[4]
if not os.path.exists(bak): open(bak, "w", encoding="utf-8").write(open(fp, encoding="utf-8").read())
o = hw(p, "홀면 %s 열%d·줄%d" % (face, (ctot if flip else 1) + sh, rs[0])); c2 = hw(p, "홀면 %s 열%d·줄%d" % (face, (ctot - 1 if flip else 2) + sh, rs[0])) - o; r2 = hw(p, "홀면 %s 열%d·줄%d" % (face, (ctot if flip else 1) + sh, rs[1])) - o
_keep = list(range(len(obj)))
if spec.get("drop"):   # 모서리 구멍처럼 읽기가 거친 점은 잔차가 큰 순서로 몇 개 뺀다(규칙 D11 ⑤ holefit 점 버리기) — 뺀 점은 출력에 적는다
    _fl = (H / 2) / math.tan(math.radians(b[5]) / 2); _K = np.array([[_fl, 0, W / 2], [0, _fl, H / 2], [0, 0, 1]], float); _oc = obj - obj.mean(0)
    _ok, _rv, _tv = cv2.solvePnP(_oc, img, _K, None, flags=cv2.SOLVEPNP_EPNP); _ok, _rv, _tv = cv2.solvePnP(_oc, img, _K, None, _rv, _tv, True, flags=cv2.SOLVEPNP_ITERATIVE)
    _pr, _ = cv2.projectPoints(_oc, _rv, _tv, _K, None); _e = np.sqrt(((_pr.reshape(-1, 2) - img) ** 2).sum(1)); _bad = list(np.argsort(-_e)[:int(spec["drop"])])
    print("뺀 점(잔차 큰 순):", [(int(i), round(float(_e[i]), 1)) for i in _bad]); _keep = [i for i in _keep if i not in _bad]
obj = obj[_keep]; img = img[_keep]
out = {"pts": [[[round(float(x), 3) for x in P], [float(q[0]), float(q[1])]] for P, q in zip(obj, img)], "grid": {"origin": [round(float(x), 3) for x in o], "col": [round(float(x), 3) for x in c2], "row": [round(float(x), 3) for x in r2]},
       "note": "앞 번호 모델 3D(앵커 %d개 포함) ↔ 책 holefit 점: 판#%d 줄%s 칸반대=%s 칸밀림=%d — anchor_pnp.py" % (len(anch), b[2], rs, flip, sh)}
tf = os.path.join(tempfile.gettempdir(), "anchor_pnp_%s_%02d.json" % (name, N)); json.dump(out, open(tf, "w", encoding="utf-8"), ensure_ascii=False)
r = subprocess.run([sys.executable, os.path.join(HERE, "mkfit3d.py"), name, str(N), wlabel, str(spec.get("cols_total", cmax)), str(max(p[1] for p in pts)), tf, "--허용", str(spec.get("tol", 9))], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
print(r.stdout.strip()[-500:], r.stderr.strip()[-200:])
