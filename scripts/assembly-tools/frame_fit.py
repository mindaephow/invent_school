# 기준 부품이 "한 줄 구멍·L자 프레임"(135도 프레임·90도 프레임·15프레임 …)이라 N칸×M줄 격자(holefit)가 안 될 때 — 그 부품 모델의 구멍 3차원 좌표 + 책 그림에서 읽은 구멍 중심으로 카메라를 푼다(PnP).
#   2026-10-13 드롭체커 27번(사용자 지시: 기준은 25프레임이 아니라 135도 프레임)에서 손으로 하던 작업을 도구로 만들었다.
#   python frame_fit.py <이름> <번호> <라벨> "<부품이름>" "h1:x,y;h2:x,y;…"  [--빼기 h4,h9] [--원점 h6] [--다듬기] [--fov 70]
#     "<부품이름>"  부품 DB 이름(예: 135도 프레임) — 구멍 id(h1~h9)와 평면 좌표는 부품 모델 연결점에서 읽는다(평면 = 부품 로컬 x·z, 두께 방향 y).
#     "h1:x,y;…"    책 그림에서 읽은 그 구멍의 중심 픽셀(원본 그림 좌표) — crop_ticks.py 로 확대해 읽는다. 4개 이상, 한 직선이 아니어야 한다(L자의 꺾인 팔 구멍을 하나 이상 넣는다).
#     --다듬기       읽은 점을 그 주변(반경 17px)에서 어두운 구멍 안쪽 무게중심으로 옮긴다(눈 읽기 오차 ±5px 줄임).
#     --빼기 ids     맞춤에서 뺄 구멍(모서리·끝 구멍은 모델 좌표 오차가 커서 어긋나는 경우) — 그래도 재투영 오차는 전부 보고한다.
#     --원점 id      축선 원점으로 쓸 구멍(기본 가운데). --fov 시야각(기본: 15~70 을 모두 돌려 정상 해 중 오차 최소).
#   하는 일: ① fov 별 PnP → 위에서 내려다보고 위쪽이 위인 정상 해(phi≤1.55·up_y>0)만 쓴다 ② 재투영 오차(구멍별·평균·최대) ③ fits/NN_<라벨>.json(infer 형식 — rulecheck 는 ⚠ 사용자 확인) ④ NN_axes.json(축선 원점 = 원점 구멍, no_rotate) ⑤ 확인 그림 refs/<이름>/NN_fit_<라벨>.jpg(검출 원=초록·주황, 재투영 +=빨강) — **DB 에 올린다**
#   ★ 한계(2026-10-13, 드롭체커 27번): 이 도구는 부품 평면을 바닥(xz)에 누운 판처럼 놓고 푼다. **서 있는 부품(아치·벽·세운 프레임)은 카메라가 틀리게 나온다**(27번: 이 도구 theta −0.76·phi 0.69 ← 실제 3D 좌표로 푼 −0.67·0.87). 서 있는 부품은 모델의 구멍 세계 좌표(Part.world("hole", c)["pos"])를 cv2.solvePnP 에 그대로 넣어 푼다(pnp.fit(obj3d, img, W, H, fov); 판이 띄워져 있으면 띄운 만큼 옮긴 좌표) — 05_조립.md 함정 참고.
#   주의: 시야각을 크게 해야 풀리면(≥60) 구멍 읽기·모델 좌표 오차를 의심한다. 다른 부품(판 등)으로 푼 카메라와 다르면(드롭체커 27번: 판 theta −0.43·phi 1.10 vs 프레임 −0.76·0.69) 책이 부품을 임의 자세로 그렸을 수 있다 — 기준 부품 값을 쓰고 차이를 읽기 표에 적는다.
import sys, os, json, math
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from pnp import fit, cam_from, angles

def main():
    a = sys.argv[1:]
    if len(a) < 5: sys.exit(__doc__)
    name, step, label, part, spec = a[0], int(a[1]), a[2], a[3], a[4]
    drop, origin, refine, fovs = set(), None, False, tuple(range(15, 71, 5)); i = 5
    while i < len(a):
        if a[i] == "--빼기": drop = set(a[i + 1].split(",")); i += 2
        elif a[i] == "--원점": origin = a[i + 1]; i += 2
        elif a[i] == "--다듬기": refine = True; i += 1
        elif a[i] == "--fov": fovs = (int(a[i + 1]),); i += 2
        else: sys.exit("모르는 옵션 " + a[i])
    D = os.path.join(HERE, "refs", name) + os.sep
    im = cv2.imread(D + "%02d.jpg" % step); H, W = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    import asmlib
    P = asmlib.Part(part, np.eye(3), (0, 0, 0), None)
    plane = {h["id"]: (float(h["pos"][0]), float(h["pos"][2])) for h in P.conn["holes"]}   # 평면 좌표(로컬 x·z)
    pix = {}
    for tok in spec.split(";"):
        hid, xy = tok.split(":"); x, y = [float(v) for v in xy.split(",")]
        if hid not in plane: sys.exit("부품에 없는 구멍 id: " + hid + " (있는 것: %s)" % ", ".join(plane))
        pix[hid] = (x, y)
    if refine:
        def ref(x, y, r=17):
            x0, y0 = int(x - r), int(y - r); win = g[y0:y0 + 2 * r, x0:x0 + 2 * r].astype(np.float32); m = (win < 150).astype(np.float32); w = m * (150 - win); s = w.sum()
            if s < 50: return (x, y)
            ys, xs = np.mgrid[0:win.shape[0], 0:win.shape[1]]; return (float((w * xs).sum() / s + x0), float((w * ys).sum() / s + y0))
        pix = {h: ref(*p) for h, p in pix.items()}
    use = [h for h in pix if h not in drop]
    if len(use) < 4: sys.exit("맞춤에 쓸 구멍이 4개 미만이다")
    pts_use = np.array([plane[h] for h in use]);
    if np.linalg.matrix_rank(pts_use - pts_use.mean(0), tol=1.0) < 2: sys.exit("쓰는 구멍이 한 직선이다 — 꺾인 팔 구멍을 하나 이상 넣는다")
    obj = [(plane[h][0], plane[h][1], 0.0) for h in use]; img = [pix[h] for h in use]
    cands = []
    for fov in fovs:
        r = fit(obj, img, W, H, fov)
        if r:
            e, rv, tv, K = r; C, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(C, (0, 0, 0))
            cands.append(dict(e=e, fov=fov, rv=rv, tv=tv, K=K, th=math.radians(az), ph=math.radians(90 - el), up=float(up[1]), roll=math.degrees(math.asin(max(-1, min(1, float(right[1])))))))
    good = sorted([c for c in cands if c["ph"] <= 1.55 and c["up"] > 0], key=lambda c: c["e"])
    print("fov별 정상 해: " + ", ".join("fov %d %.2fpx(theta %.2f phi %.2f)" % (c["fov"], c["e"], c["th"], c["ph"]) for c in good[:5]))
    if not good: sys.exit("정상 해(위에서 내려다봄)가 없다 — 구멍 번호·읽은 점을 다시 본다")
    b = good[0]
    allh = list(plane)
    pj = {h: cv2.projectPoints(np.float32([(plane[h][0], plane[h][1], 0)]), b["rv"], b["tv"], b["K"], None)[0][0][0] for h in allh}
    err = {h: float(np.hypot(*(pj[h] - np.array(pix[h])))) for h in pix}
    eu = [err[h] for h in use]; mean_e, max_e = float(np.mean(eu)), float(max(eu))
    print("카메라 theta %.2f phi %.2f roll %.1f° fov %d | 맞춤 %d점 평균 %.2f·최대 %.2f px | 구멍별 %s" % (b["th"], b["ph"], b["roll"], b["fov"], len(use), mean_e, max_e, {h: round(v, 1) for h, v in err.items()}))
    if b["fov"] >= 60: print("⚠ 시야각 %d 까지 키워야 풀렸다 — 구멍 읽기·모델 좌표 오차를 의심한다" % b["fov"])
    if mean_e > 2.0: print("⚠ 평균 오차 2px 초과 — 이 값을 그대로 쓰지 않는다(구멍을 다시 읽거나 --빼기)")
    org = origin if origin in plane else sorted(use, key=lambda h: plane[h][0])[len(use) // 2]
    Pr = lambda v: cv2.projectPoints(np.float32([v]), b["rv"], b["tv"], b["K"], None)[0][0][0]
    o = Pr([plane[org][0], plane[org][1], 0]); d = {}
    for k, v in (("X", [10, 0, 0]), ("Y", [0, 10, 0]), ("Z", [0, 0, 10])):
        w = Pr(np.array([plane[org][0], plane[org][1], 0]) + np.array(v, float)) - o; s = 55.0 / max(abs(w[0]), abs(w[1]), 1e-6) if k != "Y" else 55.0 / max(abs(w[1]), 1e-6)
        d[k] = [round(float(w[0] * s), 1), round(float(w[1] * s), 1)]
    order = sorted(plane, key=lambda h: int(h[1:].split("_")[0]) if h[1:].split("_")[0].isdigit() else 0)
    pts = [[k + 1, 1, round(pix[h][0], 2), round(pix[h][1], 2)] for k, h in enumerate(order) if h in pix]
    ev = {"sources": ["%s 구멍 %d개 중심을 책 그림에서 읽음(%s)" % (part, len(pix), "어두운 구멍 무게중심으로 다듬음" if refine else "눈 읽기"), "부품 모델 구멍 3차원 좌표로 PnP — 쓴 점 %d개(뺀 구멍: %s)" % (len(use), ",".join(sorted(drop)) or "없음")],
          "visible_holes": len(pix), "anchors": [[[k + 1, 1], list(pix[h]), 0] for k, h in enumerate(order) if h in pix], "row_shift": 0, "col_shift": 0, "unique_ratio": 9.9,
          "roll_deg": round(b["roll"], 1), "anchor_mean_px": round(float(np.mean(list(err.values()))), 2), "anchor_max_px": round(max(err.values()), 2), "theta": round(b["th"], 2), "phi": round(b["ph"], 2), "fov": b["fov"]}
    os.makedirs(D + "fits", exist_ok=True)
    json.dump({"cols": len(order), "rows": 1, "pts": pts, "tool": "infer", "err_px": round(mean_e, 2), "max_err_px": round(max_e, 2), "est": [], "origin_cell": [order.index(org) + 1, 1],
               "visible_cells": [[k + 1, 1] for k, h in enumerate(order) if h in pix], "name": "%s %d번 %s: 기준 부품 %s 구멍 %d개(관측) + 부품 모델 3차원 좌표 PnP(%d점 평균 %.2f·최대 %.2f px) — frame_fit.py" % (name, step, label, part, len(pix), len(use), mean_e, max_e), "evidence": ev},
              open(D + "fits/%02d_%s.json" % (step, label), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"global": d, "replace_lines": True, "fit": {"from": "%02d_%s.json" % (step, label), "err_px": round(mean_e, 2), "points": len(use), "theta": round(b["th"], 2), "phi": round(b["ph"], 2), "cols": "+X", "rows": "+Y"}, "no_rotate": True},
              open(D + "%02d_axes.json" % step, "w", encoding="utf-8"), ensure_ascii=False)
    ov = im.copy()
    for h in pix:
        used = h in use; cv2.circle(ov, (int(pix[h][0]), int(pix[h][1])), 7, (0, 200, 0) if used else (0, 140, 255), 2)
        cv2.drawMarker(ov, (int(pj[h][0]), int(pj[h][1])), (0, 0, 255), cv2.MARKER_CROSS, 14, 2); cv2.putText(ov, h, (int(pix[h][0]) - 8, int(pix[h][1]) - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    path = D + "%02d_fit_%s.jpg" % (step, label); ok, buf = cv2.imencode(".jpg", ov, [cv2.IMWRITE_JPEG_QUALITY, 92]); buf.tofile(path)
    print("✅ fits/%02d_%s.json·%02d_axes.json·%s 저장 — python refs_rect.py %s %d 로 그림을 그리고, 확인 그림을 DB 에 올린다" % (step, label, step, os.path.basename(path), name, step))

main()
