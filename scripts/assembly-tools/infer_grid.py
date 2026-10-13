# 유추 격자(2026-10-13, 사용자 지시 "한 번호로 안 풀리면 모든 정보를 모아 유추해서 찾는다 — 모자라면 탈락이 아니다").
#   holefit 가 기준(구멍 ≥40%)을 못 채울 때(판이 다른 부품에 가려 구멍이 일부만 보일 때) 쓴다. 개수 대신 "근거끼리 맞는지"(잔차 px)로 판단한다.
#   python infer_grid.py <이름> <번호> <라벨> <칸> <줄> 모서리8개  [근거 옵션…]
#     모서리 8개 = holefit 와 같은 판 바깥 윤곽(칸1줄1, 칸N줄1, 칸N줄M, 칸1줄M 순서, 원본 그림 좌표) — 보이는 구멍 후보를 찾는 범위와 첫 배정에만 쓴다.
#   근거 옵션(있는 것을 전부 준다 — 많을수록 가설이 하나로 갈린다):
#     --판 NN:라벨        같은 판이 전부 보인 앞 번호의 fits(예: 16:P) — 칸·줄 수가 같은지 확인하고 판 치수(10mm 간격)를 그 판 그대로 쓴다.
#     --거울 NN [줄|칸]   대칭(거울) 쪽: NN번(반대편 유닛)의 끼움 자리(조립 데이터 moveMade 마크 → 칸·높이)를 줄(기본) 또는 칸으로 뒤집은 것이 이 번호의 앵커 칸이다.
#     --링 "x,y;x,y;…"    책 그림 초록 링 중심 픽셀(칸 번호 없이). 어느 링이 어느 칸인지는 거울 앵커 칸과 모든 짝을 맞춰 보고 잔차가 가장 작은 짝을 고른다.
#     --anchor "c,r,x,y,높이;…"  칸을 직접 아는 점(링·읽기 표). --거울/--링 과 함께 써도 된다. 높이 = 판 바닥 0 기준 mm(판 윗면 5, 리벳 윗부분 8~9).
#     --조각높이 2.5      선명한 구멍(흰 조각)이 보이는 높이.   --cam theta phi  참고 카메라(사용자 📷·뒷 번호 카메라) — 비교만 하고 결과는 안 바꾼다.
#   쓰는 근거: ① 판의 3차원 구멍 좌표(10mm 간격) ② 그림에서 선명하게 검출된 구멍(흰 조각) ③ 앵커(칸을 아는 링) ④ 줄·칸 배정 가설과 링 짝 가설을 모두 돌려 잔차가 가장 작은 것
#   출력: 가설별 잔차 표, 1·2등 가설 비교(유일성), 카메라 theta·phi·roll. 가설이 하나로 안 갈리면(2등이 1등의 1.3배 미만) 저장하지 않고 "어떤 추가 근거가 필요한지"를 말한다.
#   저장: refs/<이름>/fits/NN_<라벨>.json (모든 칸을 풀이한 카메라로 투영한 점, tool="infer", evidence 기록) — rulecheck 는 ✅ 가 아니라 ⚠ 로 보고한다(사용자 확인 필요).
import sys, os, json, math, itertools
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from, angles
HERE = os.path.dirname(os.path.abspath(__file__))

def parse():
    a = sys.argv[1:]
    if len(a) < 13: sys.exit(__doc__)
    o = dict(name=a[0], step=int(a[1]), label=a[2], cols=int(a[3]), rows=int(a[4]), C=np.array([float(v) for v in a[5:13]], np.float32).reshape(4, 2),
             anchors=[], ys=2.5, cam=None, plate=None, mirror=None, rings=None)
    i = 13
    while i < len(a):
        k = a[i]
        if k == "--anchor":
            for tok in a[i + 1].split(";"):
                c, r, x, y, h = [float(v) for v in tok.split(",")]; o["anchors"].append(((int(c), int(r)), (x, y), h))
            i += 2
        elif k == "--조각높이": o["ys"] = float(a[i + 1]); i += 2
        elif k == "--cam": o["cam"] = (float(a[i + 1]), float(a[i + 2])); i += 3
        elif k == "--판": o["plate"] = a[i + 1]; i += 2
        elif k == "--거울":
            o["mirror"] = (int(a[i + 1]), "줄"); i += 2
            if i < len(a) and a[i] in ("줄", "칸"): o["mirror"] = (o["mirror"][0], a[i]); i += 1
        elif k == "--링": o["rings"] = [tuple(float(v) for v in t.split(",")) for t in a[i + 1].split(";")]; i += 2
        else: sys.exit("모르는 옵션 " + k)
    return o

def main():
    o = parse(); name, step, label, cols, rows, C = o["name"], o["step"], o["label"], o["cols"], o["rows"], o["C"]
    D = os.path.join(HERE, "refs", name) + os.sep; evid = []
    im = cv2.imread(D + "%02d.jpg" % step); Hh, Ww = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    # ── 근거 ① 같은 판의 앞 번호 fits ──
    if o["plate"]:
        pn, pl = o["plate"].split(":"); pf = json.load(open(D + "fits/%02d_%s.json" % (int(pn), pl), encoding="utf-8"))
        if (pf["cols"], pf["rows"]) != (cols, rows): sys.exit("판 크기가 다르다: %s번 %s 는 %d×%d, 이 번호는 %d×%d" % (pn, pl, pf["cols"], pf["rows"], cols, rows))
        evid.append("같은 판 %s번 %s(%d×%d, 구멍 %s개 검출 %.0f%%)" % (pn, pl, cols, rows, pf.get("found", "?"), 100 * float(pf.get("found_ratio", 0))))
    # ── 근거 ② 거울(대칭) 쪽의 끼움 자리 → 앵커 칸 후보 ──
    mir_cells = []
    if o["mirror"]:
        mn, how = o["mirror"]; asm = json.load(open(os.path.join(HERE, "%s_asm.json" % name), encoding="utf-8"))["steps"][mn - 1]
        for k, v in (asm.get("moveMade") or {}).items():
            for m in v.get("marks") or []:
                c = (m[0] - 5) / 10.0 + (cols + 1) / 2.0; r = (m[2] - 5) / 10.0 + (rows + 1) / 2.0; h = float(m[1])   # 판 가운데 (x 5, z 5), 10mm 간격 — 713프레임이 원점에서 5mm 어긋나 놓인 값(드롭체커)
                if abs(c - round(c)) < 0.05 and abs(r - round(r)) < 0.05:
                    c, r = int(round(c)), int(round(r))
                    mir_cells.append(((c, rows + 1 - r) if how == "줄" else (cols + 1 - c, r), h))
        if len(mir_cells) < 3: sys.exit("%d번의 끼움 마크에서 칸을 %d개만 읽었다(3개 이상 필요)" % (mn, len(mir_cells)))
        evid.append("%d번 끼움 %d곳을 %s 거울로 뒤집은 칸 %s" % (mn, len(mir_cells), how, [c for c, h in mir_cells]))
    H0, _ = cv2.findHomography(np.array([[0, 0], [cols, 0], [cols, rows], [0, rows]], np.float32), C, 0)
    nodes = lambda H: {(c, r): cv2.perspectiveTransform(np.array([[[c - .5, r - .5]]], np.float32), H)[0][0] for c in range(1, cols + 1) for r in range(1, rows + 1)}
    x0, y0, x1, y1 = int(C[:, 0].min() - 10), int(C[:, 1].min() - 10), int(C[:, 0].max() + 10), int(C[:, 1].max() + 10)
    ins = np.zeros(g.shape, np.uint8); cv2.fillPoly(ins, [C.astype(np.int32).reshape(-1, 1, 2)], 1)
    sub = g[y0:y1, x0:x1]; ie = cv2.erode(ins[y0:y1, x0:x1], np.ones((5, 5), np.uint8))
    m = ((sub > 200) & (ie > 0)).astype(np.uint8) * 255; n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    S = np.array([[cen[i][0] + x0, cen[i][1] + y0] for i in range(1, n) if 15 < st[i][4] < 700 and .3 < st[i][2] / max(1, st[i][3]) < 3.8], float)   # 선명한 흰 조각(구멍 뒤가 비쳐 보이는 곳)
    if len(S) < 8: sys.exit("선명한 구멍 후보가 8개 미만(%d)이라 유추 근거가 모자란다 — 다른 번호·완성 사진에서 앵커를 더 모은다" % len(S))
    pitch = float(np.mean([np.hypot(*(nodes(H0)[(c + 1, r)] - nodes(H0)[(c, r)])) for c in range(1, cols) for r in range(1, rows + 1)])); H = H0; sel = {}
    for it in range(12):   # 흰 조각 첫 배정(모서리 격자 → 반복). 줄·칸 배정이 어긋나 있을 수 있어 아래에서 줄·칸 이동 가설을 모두 돌린다.
        pr = nodes(H); new = {}; used = set(); tol = max(.33, .5 - .04 * it)
        for cr, pos in sorted(pr.items()):
            d = np.hypot(*(S - pos).T); k = int(np.argmin(d))
            if d[k] < tol * pitch and k not in used: new[cr] = k; used.add(k)
        if len(new) < 6: break
        Hn, _ = cv2.findHomography(np.array([[c - .5, r - .5] for c, r in new], np.float32), np.array([S[k] for k in new.values()], np.float32), 0)
        if Hn is None: break
        H = Hn
        if new == sel: break
        sel = new
    P3 = lambda c, r, y: [(c - (cols + 1) / 2.0) * 10.0, y, (r - (rows + 1) / 2.0) * 10.0]   # 판 가운데 원점, 칸 +X·줄 +Z, 높이는 판 바닥 0
    def solve(anchors, fovs):
        out = []
        for dr in range(-3, 5):
            for dc in (-1, 0, 1):
                obj, img = [], []
                for (c, r), k in sel.items():
                    c2, r2 = c + dc, r + dr
                    if 1 <= c2 <= cols and 1 <= r2 <= rows: obj.append(P3(c2, r2, o["ys"])); img.append(S[k])
                nS = len(obj)
                if nS < 8: continue
                for (c, r), px, h in anchors: obj.append(P3(c, r, h)); img.append(px)
                best = None
                for fov in fovs:
                    r_ = fit(obj, img, Ww, Hh, fov)
                    if r_ and (best is None or r_[0] < best[0][0]): best = (r_, fov)
                if not best: continue
                (e, rv, tv, K), fov = best
                pj = cv2.projectPoints(np.float32(obj), rv, tv, K, None)[0].reshape(-1, 2); ee = np.hypot(*(pj - np.array(img)).T)
                Cc, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(Cc, (0, 0, 0))
                if math.radians(90 - el) > 1.55: continue   # 판 아래에서 올려다보는(거울) 해는 쓰지 않는다
                out.append(dict(dr=dr, dc=dc, nS=nS, sm=float(ee[:nS].mean()), sx=float(ee[:nS].max()), am=float(ee[nS:].mean()), ax=float(ee[nS:].max()),
                                score=float(ee[:nS].mean() + .5 * ee[nS:].mean()), fov=fov, rv=rv, tv=tv, K=K, th=math.radians(az), ph=math.radians(90 - el), anchors=anchors,
                                roll=math.degrees(math.asin(max(-1, min(1, float(right[1])))))))
        return out
    # ── 링 ↔ 거울 칸 짝 가설 ──
    hyp = []
    if o["rings"] and mir_cells:
        rg = o["rings"]
        print("링 %d개 ↔ 거울 칸 %d개: 모든 짝을 맞춰 본다" % (len(rg), len(mir_cells)))
        k = min(len(rg), len(mir_cells))
        for rsub in itertools.combinations(range(len(rg)), k):
            for perm in itertools.permutations(range(len(mir_cells)), k):
                anc = [(mir_cells[perm[j]][0], rg[rsub[j]], mir_cells[perm[j]][1]) for j in range(k)] + o["anchors"]
                hyp += solve(anc, (25, 35, 45, 55))
    else:
        anc = list(o["anchors"])
        if len(anc) < 3: sys.exit("앵커(칸을 아는 링)가 3개 이상 필요하다 — --anchor 또는 --거울 + --링")
        hyp = solve(anc, tuple(range(15, 61, 5)))
    if not hyp: sys.exit("풀이 가능한 가설이 없다")
    hyp.sort(key=lambda h: h["score"])
    sig = lambda h: (h["dr"], h["dc"], tuple(sorted((c, round(px[0]), round(px[1])) for c, px, _ in h["anchors"])))
    print("가설별 잔차(근거: 선명한 구멍 %d개 + 앵커 + 판 3차원 좌표 10mm 간격)" % len(S))
    seen = []
    for h in hyp:
        if sig(h) in seen: continue
        seen.append(sig(h))
        if len(seen) > 6: break
        print("  줄 %+d 칸 %+d | 앵커 칸 %s : 구멍 %d개 평균 %.2f·최대 %.2f px | 앵커 평균 %.2f·최대 %.2f px | theta %.2f phi %.2f roll %.1f° fov %d" % (h["dr"], h["dc"], [c for c, px, _ in h["anchors"]], h["nS"], h["sm"], h["sx"], h["am"], h["ax"], h["th"], h["ph"], h["roll"], h["fov"]))
    b = hyp[0]; sec = next((h for h in hyp[1:] if sig(h) != sig(b)), None); ratio = (sec["score"] / b["score"]) if sec else 9.9
    print("1등 가설: 줄 %+d 칸 %+d, 앵커 칸 %s — 2등과 점수 비 %.2f(1.3 이상이어야 유일)" % (b["dr"], b["dc"], [c for c, px, _ in b["anchors"]], ratio))
    if abs(b["roll"]) > 5: print("⚠ 풀이 카메라가 %.1f° 기울어 있다(roll) — 책 그림이 기울어 그려진 번호다. 뷰어 카메라는 기울이지 못하니 비교할 때 그림을 이 각도만큼 돌려 본다. 가설을 거르는 근거로는 쓰지 않는다(축 규칙을 바꿔도 같은 값)." % b["roll"])
    if o["cam"]: print("참고 카메라 theta %.2f phi %.2f ↔ 풀이 theta %.2f phi %.2f (차이 theta %.2f rad)" % (o["cam"][0], o["cam"][1], b["th"], b["ph"], abs(o["cam"][0] - b["th"])))
    if ratio < 1.3 or b["sm"] > 2.5 or b["sx"] > 4.5:
        why = "가설이 하나로 안 갈린다(2등과 %.2f배)" % ratio if ratio < 1.3 else "선명한 구멍 잔차가 크다(평균 %.2f·최대 %.2f px)" % (b["sm"], b["sx"])
        sys.exit("⚠ 저장하지 않는다 — %s. 추가 근거가 필요하다: 뒷 번호 그림(같은 몸체가 보이는 번호)에서 이 판의 칸을 아는 점을 앵커로 더하거나, 완성 사진(00)·사용자에게 칸 한 곳을 묻는다." % why)
    proj = lambda p: cv2.projectPoints(np.float32([p]), b["rv"], b["tv"], b["K"], None)[0][0][0]
    pts = [[c, r, round(float(proj(P3(c, r, 5.0))[0]), 2), round(float(proj(P3(c, r, 5.0))[1]), 2)] for c in range(1, cols + 1) for r in range(1, rows + 1)]   # 구멍 입구(판 윗면 5)
    evid.append("선명한 구멍 %d개 + 앵커 %d곳" % (b["nS"], len(b["anchors"])))
    vis = [(c + b["dc"], r + b["dr"]) for (c, r) in sel if 1 <= c + b["dc"] <= cols and 1 <= r + b["dr"] <= rows]   # 선명하게 검출된(눈에 보이는) 구멍의 칸
    ocell = min(vis, key=lambda cr: (cr[0] - (cols + 1) / 2.0) ** 2 + (cr[1] - (rows + 1) / 2.0) ** 2)   # 판 가운데에 가장 가까운 보이는 구멍 — 축선 원점
    out = {"origin_cell": list(ocell), "visible_cells": [list(cr) for cr in sorted(vis)], "cols": cols, "rows": rows, "pts": pts, "tool": "infer", "err_px": round(b["sm"], 2), "max_err_px": round(b["sx"], 2), "est": [[c, r] for c in range(1, cols + 1) for r in range(1, rows + 1)],
           "name": "%s %d번 %s: 유추 격자 — %s를 합쳐 카메라를 풀고 모든 칸을 투영(구멍 평균 %.2f·최대 %.2f px, 앵커 평균 %.2f px) — infer_grid.py" % (name, step, label, " + ".join(evid), b["sm"], b["sx"], b["am"]),
           "evidence": {"sources": evid, "visible_holes": b["nS"], "anchors": [[list(cr), list(px), h] for cr, px, h in b["anchors"]], "row_shift": b["dr"], "col_shift": b["dc"], "unique_ratio": round(ratio, 2),
                        "roll_deg": round(b["roll"], 1), "anchor_mean_px": round(b["am"], 2), "anchor_max_px": round(b["ax"], 2), "theta": round(b["th"], 2), "phi": round(b["ph"], 2)}}
    os.makedirs(D + "fits", exist_ok=True); json.dump(out, open(D + "fits/%02d_%s.json" % (step, label), "w", encoding="utf-8"), ensure_ascii=False)
    print("축선 원점 = 눈에 보이는 구멍 칸 %s(판 가운데에 가장 가까운 검출 구멍)" % (list(ocell),)); print("✅ 유추 격자 저장 — fits/%02d_%s.json (rulecheck 는 ⚠ 로 보고한다: 사용자 확인 필요)" % (step, label))

main()
