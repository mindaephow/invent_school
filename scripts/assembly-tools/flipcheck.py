# 책에 뒤집기·돌리기 표시("↻", "N ↻", 뒤집어서 …)가 나온 번호에서 "정말 뒤집었나, 같은 조립을 다른 쪽에서 본 건가"를 계산으로 가린다(사용자 지시 2026-11-02, 해머배틀 15번: 뒤집기 가설을 코드에만 넣고 화면·책과 비교하지 않아 몇 시간을 썼다).
#   python flipcheck.py <이름> <번호> <라벨> <칸수> <줄수> --판 <판이름> --부품 <앞번호범위 a-b> --앵커 "부품이름:px,py;부품이름:px,py;…" [--그림]
#     라벨 = fits/NN_<라벨>.json — holefit 가 통과한 판 구멍 격자(원본 그림 좌표). 판이 가려져 보이는 칸만 맞췄어도 된다(칸수 = 맞춘 칸수).
#     --판    모델에서 이 판의 좌표(p)를 판 가운데로 쓴다(예: 515프레임).
#     --부품  앞 번호 모델 부품(조립 데이터 asm.json 의 그 번호 범위, 예 9-14)을 책 위에 투영해 비교한다.
#     --앵커  책 그림에서 눈에 잘 띄는 부품 2~4개의 화면 위치(원본 그림 픽셀) — 같은 이름이 둘이면 가까운 쪽에 짝지어 준다. 앵커가 있어야 순위가 나온다.
#   하는 일: 모델을 판 가운데 기준으로 [그대로 / X축 180° 뒤집기 / Z축 180° 뒤집기] 세 가지로 놓고, 판 구멍 격자의 칸·줄 방향 8가지(±X·±Z)와 보이는 칸이 판의 어느 끝인지(2가지)를 곁들여
#           위에서 내려다보는 카메라 해(phi≤1.55)만 골라 앵커 오차(px)로 순위를 낸다. 1등이 "그대로"면 뒤집은 게 아니라 돌려서 본 것(Y 축 회전은 칸·줄 방향 8가지에 들어 있다), 뒤집기면 뒤집은 것이다.
#           --그림 이면 상위 후보마다 모델 부품 중심을 책 위에 그린 refs/<이름>/cmp/NN_flip_k.png 를 쓴다. 순위 1·2등 오차가 비슷하면(차이 < 3px) 못 가린 것이니 앵커를 더 읽는다.
import sys, os, json, math, itertools
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit, cam_from, angles


def parse(a):
    d = {"앵커": [], "판": None, "부품": None, "그림": False}; pos = []; i = 0
    while i < len(a):
        if a[i] in ("--판", "--부품", "--앵커"):
            d[a[i][2:]] = a[i + 1]; i += 2
        elif a[i] == "--그림":
            d["그림"] = True; i += 1
        else:
            pos.append(a[i]); i += 1
    return pos, d


def main():
    pos, o = parse(sys.argv[1:])
    if len(pos) < 5 or not o["판"] or not o["부품"] or not o["앵커"]: sys.exit(__doc__)
    name, step, label, cols, rows = pos[0], int(pos[1]), pos[2], int(pos[3]), int(pos[4])
    D = os.path.join(HERE, "refs", name)
    f = json.load(open(os.path.join(D, "fits", "%02d_%s.json" % (step, label)), encoding="utf-8"))
    im = cv2.imread(os.path.join(D, "%02d.jpg" % step)); H, W = im.shape[:2]
    asm = json.load(open(os.path.join(HERE, name + "_asm.json"), encoding="utf-8"))["steps"]
    a0, a1 = [int(v) for v in o["부품"].split("-")]
    sys.path.insert(0, HERE)
    from asmlib import euler_to_R
    # 앞 번호에서 옮겨진 부품(move_made)의 최종 자리는 옮긴 번호의 moveMade("만든번호:부품순서") 에 따로 적혀 있다 — 번호 순서대로 덮어써서 a1 번까지의 최종 자리를 만든다.
    final = {}
    for si in range(0, a1):
        for pi, p in enumerate(asm[si]["parts"]): final[(si + 1, pi)] = np.array(p["p"], float)
        for k_, e_ in (asm[si].get("moveMade") or {}).items():
            sk, pk = [int(v) for v in k_.split(":")]
            if (sk, pk) in final: final[(sk, pk)] = np.array(e_["p"], float)
    parts = []
    for si in range(a0 - 1, a1):
        for pi, p in enumerate(asm[si]["parts"]):
            if p.get("copyOf") or p.get("hidden"): continue
            parts.append((p["n"], final[(si + 1, pi)]))
    plate = [p for n, p in parts if n == o["판"]]
    if not plate: sys.exit("판 %s 을 %s 번 범위에서 못 찾았다" % (o["판"], o["부품"]))
    pc = plate[0]
    anchors = []
    for s in o["앵커"].split(";"):
        n, xy = s.rsplit(":", 1); x, y = [float(v) for v in xy.split(",")]; anchors.append((n.strip(), np.array([x, y])))
    ax = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
    variants = {"그대로": np.eye(3), "X축 180° 뒤집기": np.diag([1.0, -1.0, -1.0]), "Z축 180° 뒤집기": np.diag([-1.0, -1.0, 1.0])}
    pitch = 10.0; res = []
    for cd, rd in itertools.product(ax, ax):
        if abs(np.dot(ax[cd], ax[rd])) == 1: continue
        cvec, rvec = np.array(ax[cd], float), np.array(ax[rd], float)
        obj = []; img = []
        for c, r, x, y in f["pts"]:
            u, v = (c - 1) - (cols - 1) / 2.0, (r - 1) - (rows - 1) / 2.0
            obj.append(list(pitch * (u * cvec + v * rvec))); img.append([x, y])
        obj = np.float32(obj); img = np.float32(img)
        sols = []
        for fov in (20, 30, 40, 50):
            r_ = fit(obj, img, W, H, fov)
            if not r_: continue
            e, rv, tv, K = r_; C, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(C, (0, 0, 0))
            if math.radians(90 - el) <= 1.55 and float(up[1]) > 0 and e <= 3.0: sols.append((e, rv, tv, K, fov))
        if not sols: continue
        e, rv, tv, K, fov = min(sols, key=lambda t: t[0])
        for vn, V in variants.items():
            for end in (+1, -1):   # 보이는 칸 덩어리가 판의 어느 끝인지: 판 길이(칸수 15) 가운데에서 칸 방향으로 (15-cols)/2 칸 떨어진 자리
                off = end * (15 - cols) / 2.0 * pitch * cvec
                pts = [(n, V @ (p - pc) - off) for n, p in parts]   # 판 가운데 기준 → 보이는 칸 덩어리 가운데 기준
                P3 = np.float32([q for n, q in pts])
                pj = cv2.projectPoints(P3, rv, tv, K, None)[0].reshape(-1, 2)
                used = set(); err = []
                for an, apx in anchors:
                    c_ = [(np.linalg.norm(pj[i] - apx), i) for i, (n, q) in enumerate(pts) if n == an and i not in used]
                    if not c_: err.append(999.0); continue
                    d_, i_ = min(c_); used.add(i_); err.append(d_)
                res.append((float(np.mean(err)), vn, cd, rd, end, e, fov, rv, tv, K, pj, pts))
    if not res: sys.exit("위에서 내려다보는 해가 없다 — 격자 점·칸수를 다시 본다")
    res.sort(key=lambda t: t[0])
    print("격자 %s %d×%d · 앵커 %d개 · 후보 %d개 (위에서 보는 해만)" % (label, cols, rows, len(anchors), len(res)))
    print("순위 | 앵커오차px | 모델 자세 | 칸방향 | 줄방향 | 보이는 칸 끝 | 격자오차px")
    seen = set(); k = 0
    for t in res:
        key = (t[1], t[2], t[3], t[4])
        if key in seen: continue
        seen.add(key); k += 1
        print("%3d | %7.1f | %-14s | %s | %s | %s | %.2f" % (k, t[0], t[1], t[2], t[3], "+칸쪽" if t[4] > 0 else "−칸쪽", t[5]))
        if o["그림"] and k <= 3:
            out = im.copy()
            for i, (n, q) in enumerate(t[11]):
                x, y = t[10][i]
                if 0 <= x < W and 0 <= y < H: cv2.circle(out, (int(x), int(y)), 6, (0, 0, 255), -1); cv2.putText(out, n[:4], (int(x) + 6, int(y) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
            for an, apx in anchors: cv2.circle(out, (int(apx[0]), int(apx[1])), 10, (0, 200, 0), 2)
            os.makedirs(os.path.join(D, "cmp"), exist_ok=True)
            cv2.imencode(".png", out)[1].tofile(os.path.join(D, "cmp", "%02d_flip_%d.png" % (step, k)))
        if k >= 8: break
    top = [t for t in res if (t[1], t[2], t[3], t[4]) == (res[0][1], res[0][2], res[0][3], res[0][4])][0]
    nxt = next((t for t in res if t[1] != top[1] or t[2:5] != top[2:5]), None)
    print("→ 1등: %s, 칸 %s·줄 %s (앵커오차 %.1fpx)" % (top[1], top[2], top[3], top[0]))
    if nxt and nxt[0] - top[0] < 3.0: print("⚠ 2등과 차이 %.1fpx 로 작다 — 못 가렸다. 앵커를 더 읽는다(비대칭 부품: 빨간 프레임·ㄷ자·모터)." % (nxt[0] - top[0]))
    else: print("✅ 2등과 %.1fpx 이상 차이 — 가려졌다." % ((nxt[0] - top[0]) if nxt else 0))
    if top[1] == "그대로": print("   뒤집은 게 아니라 같은 조립을 돌려서(Y 축) 본 것이다 — 카메라만 바꾸면 된다.")
    else: print("   %s — 앞 번호 조립 전체를 이 자세로 옮기는 번호다(move_made)." % top[1])


main()
