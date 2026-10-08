# refs-grid MCP 를 못 쓰는 세션(프로젝트 폴더가 아닌 곳에서 시작했거나 MCP 가 안 붙은 세션)에서 같은 일을 명령줄로 한다.
#   python refs_cli.py view   <이름> <단계> [x0 y0 x1 y1] [배율]          눈금 그림(refs_view)
#   python refs_cli.py show   <이름> <단계> <칸> <줄> x1 y1 x2 y2 x3 y3 x4 y4   모서리 4곳으로 격자만 그려서 번호를 본다(맞추기 전 눈 확인용). 출력: 그림 경로
#   python refs_cli.py fit    '<JSON>'   refs_fit 과 같은 입력(+ "label"). 결과를 refs/<이름>/fits/NN_<label>.json 에 저장하고 그림 경로·오차를 출력
#   [철칙 순서(관리자 2026-10-08): ① 잘라내기(crop) → ② 수평선 → ③ 회전 → ④ 격자]
#   python refs_cli.py level  <이름> <단계> x0 y0 x1 y1  x1 y1 x2 y2   [①②③] 먼저 crop(x0 y0 x1 y1 = 부품만 남길 원본 영역, 글씨·테두리 제외)으로 잘라낸 뒤, 그 위에서 수평선 두 점(왼쪽·오른쪽 구멍, 원본 좌표)을 찍어 그 선이 수평이 되게 돌린다 판의 긴 방향 구멍 두 개(왼쪽 점, 오른쪽 점; 원본 좌표)를 찍으면 그 선이 수평이 되게 돌린 그림 refs/<이름>/NN_lv.jpg 를 만들고 파란 수평선을 긋는다(관리자 철칙 2026-10-08: 수평선 → 회전 → 격자). 출력: 그림 경로·돌린 각도
#   python refs_cli.py lshow  <이름> <단계> <칸> <줄> x1 y1 x2 y2 x3 y3 x4 y4   [③] 돌린 그림(NN_lv.jpg) 위에서 모서리 4곳(돌린 그림 좌표)으로 격자만 그려 번호를 본다
#   python refs_cli.py lfit   <이름> <단계> <label> <칸> <줄> x1 y1 … x4 y4   [③] 돌린 그림 위 모서리로 격자를 저장(refs/<이름>/fits/NN_<label>.json, 원본 좌표로 되돌려 저장해 render 가 그대로 쓴다)
#   python refs_cli.py render '<JSON>'   refs_render 와 같은 입력(plates 의 label 로 fits 를 읽는다). NN_1·NN_2 를 만들고 index.json 을 갱신
#   (JSON 은 PowerShell/Git Bash 따옴표 문제를 피하려면 파일로 주고 @파일경로 로 쓴다: python refs_cli.py fit @fit1.json)
import sys, os, json
import cv2, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import refs_auto as R

def jarg(s):
    return json.load(open(s[1:], encoding="utf-8")) if s.startswith("@") else json.loads(s)

def fitfile(name, step, label):
    return os.path.join(R.refs_dir(name), "fits", "%02d_%s.json" % (step, label))

def main():
    c = sys.argv[1]
    if c == "view":
        name, step = sys.argv[2], int(sys.argv[3]); rest = sys.argv[4:]
        a = {"name": name, "step": step}
        if len(rest) >= 4: a["bbox"] = [float(v) for v in rest[:4]]
        if len(rest) >= 5: a["scale"] = float(rest[4])
        print(json.dumps(R.cmd_view(a), ensure_ascii=False))
    elif c == "show":
        name, step, cols, rows = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); v = [float(x) for x in sys.argv[6:14]]
        corners = [[v[0], v[1]], [v[2], v[3]], [v[4], v[5]], [v[6], v[7]]]
        im = R.load_orig(name, step).copy()
        src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32); H = cv2.getPerspectiveTransform(src, np.array(corners, np.float32))
        P = R.project(H, cols, rows)
        for (cc, rr), p in zip(R.lattice(cols, rows).astype(int), P):
            cv2.circle(im, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)
            if rr == 0: cv2.putText(im, str(cc + 1), (int(p[0]) - 6, int(p[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            if cc == 0: cv2.putText(im, "r%d" % (rr + 1), (int(p[0]) + 6, int(p[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 140, 0), 1)
        print(R.save_png(im, "show_%02d" % step))
    elif c == "fit":
        a = jarg(sys.argv[2]); label = a.pop("label"); r = R.cmd_fit(a)
        if r.get("ok") is False: print(json.dumps({k: v for k, v in r.items() if k != "pts"}, ensure_ascii=False)); sys.exit(1)
        os.makedirs(os.path.dirname(fitfile(a["name"], a["step"], label)), exist_ok=True)
        json.dump({"cols": a["cols"], "rows": a["rows"], "pts": r["pts"], "corners": r["corners"]}, open(fitfile(a["name"], a["step"], label), "w"))
        print(json.dumps({k: v for k, v in r.items() if k != "pts"}, ensure_ascii=False))
    elif c == "render":
        a = jarg(sys.argv[2]); plates = []
        _lv = os.path.join(R.refs_dir(a["name"]), "%02d_lv.json" % int(a["step"]))   # 철칙 순서(level 로 잘라내고 돌린 그림)가 있으면 그 그림으로 NN_1(수평선만)·NN_2(수평선+격자)를 만든다
        _new = os.path.exists(_lv)
        for p in a["plates"]:
            j = json.load(open(fitfile(a["name"], a["step"], p["label"]), encoding="utf-8")); plates.append({"name": p.get("name") or p["label"], "cols": j["cols"], "rows": j["rows"], "pts": j["pts"], "ref": bool(p.get("ref"))})
        a["plates"] = plates; print(json.dumps((R.render_lv if _new else R.cmd_render)(a), ensure_ascii=False))
    elif c == "level":
        name, step = sys.argv[2], int(sys.argv[3]); cx0, cy0, cx1, cy1 = [int(float(v)) for v in sys.argv[4:8]]; x1, y1, x2, y2 = [float(v) for v in sys.argv[8:12]]
        full = R.load_orig(name, step).copy(); H0, W0 = full.shape[:2]; cx0, cy0, cx1, cy1 = max(0, cx0), max(0, cy0), min(W0, cx1), min(H0, cy1)
        im = full[cy0:cy1, cx0:cx1].copy(); h, w = im.shape[:2]                      # ① 잘라내기: 부품만 남김
        x1, y1, x2, y2 = x1 - cx0, y1 - cy0, x2 - cx0, y2 - cy0                       # ② 수평선 두 점(잘라낸 그림 좌표)
        ang = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        M = cv2.getRotationMatrix2D(((x1 + x2) / 2, (y1 + y2) / 2), ang, 1.0)          # ③ 회전
        cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * sn + w * cs) + 1, int(h * cs + w * sn) + 1
        _cc = M @ np.array([w / 2.0, h / 2.0, 1.0]); M[0, 2] += nw / 2 - _cc[0]; M[1, 2] += nh / 2 - _cc[1]   # 잘라낸 그림 가운데를 캔버스 가운데로(수평선 중점을 가운데로 옮기면 한쪽이 잘렸다 — 강아지로봇 30번, 2026-10-09)
        rot = cv2.warpAffine(im, M, (nw, nh), borderValue=(255, 255, 255))
        p1 = M @ np.array([x1, y1, 1.0]); p2 = M @ np.array([x2, y2, 1.0]); y0 = int(round((p1[1] + p2[1]) / 2))
        o = rot.copy(); cv2.line(o, (0, y0), (nw, y0), (255, 140, 0), 2, cv2.LINE_AA); cv2.putText(o, "horizontal", (nw - 130, y0 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 140, 0), 2)
        base = os.path.join(R.refs_dir(name), "%02d_lv" % step)
        cv2.imwrite(base + ".jpg", rot, [cv2.IMWRITE_JPEG_QUALITY, 90]); cv2.imwrite(base + "_line.jpg", o, [cv2.IMWRITE_JPEG_QUALITY, 90])
        json.dump({"M": M.tolist(), "size": [nw, nh], "angle": ang, "crop": [cx0, cy0, cx1, cy1]}, open(base + ".json", "w"))
        print(json.dumps({"rotated_deg": round(-ang, 2), "image": base + "_line.jpg", "size": [nw, nh], "crop": [cx0, cy0, cx1, cy1]}, ensure_ascii=False))
    elif c in ("lshow", "lfit"):
        name, step = sys.argv[2], int(sys.argv[3]); label = sys.argv[4] if c == "lfit" else None; off = 5 if c == "lfit" else 4
        cols, rows = int(sys.argv[off]), int(sys.argv[off + 1]); v = [float(x) for x in sys.argv[off + 2:off + 10]]
        corners = np.array([[v[0], v[1]], [v[2], v[3]], [v[4], v[5]], [v[6], v[7]]], np.float32)
        base = os.path.join(R.refs_dir(name), "%02d_lv" % step); rot = cv2.imread(base + ".jpg"); Mj = json.load(open(base + ".json"))
        src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32); H = cv2.getPerspectiveTransform(src, corners)
        P = R.project(H, cols, rows); L = R.lattice(cols, rows).astype(int)
        if c == "lshow":
            im = rot.copy()
            for (cc, rr), p in zip(L, P):
                cv2.circle(im, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)
                if rr == 0: cv2.putText(im, str(cc + 1), (int(p[0]) - 6, int(p[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                if cc == 0: cv2.putText(im, "r%d" % (rr + 1), (int(p[0]) + 6, int(p[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 140, 0), 1)
            print(R.save_png(im, "lshow_%02d" % step))
        else:   # 돌린 그림 좌표 → 원본 좌표로 되돌려 저장(render 는 원본 좌표를 받는다)
            Minv = cv2.invertAffineTransform(np.array(Mj["M"], np.float64)); ox, oy = Mj["crop"][0], Mj["crop"][1]
            pts = [[int(cc) + 1, int(rr) + 1, round(float(Minv[0, 0] * p[0] + Minv[0, 1] * p[1] + Minv[0, 2]) + ox, 1), round(float(Minv[1, 0] * p[0] + Minv[1, 1] * p[1] + Minv[1, 2]) + oy, 1)] for (cc, rr), p in zip(L, P)]
            fp = fitfile(name, step, label); os.makedirs(os.path.dirname(fp), exist_ok=True)
            json.dump({"cols": cols, "rows": rows, "pts": pts, "corners": [pts[0][2:], pts[(cols - 1) * rows][2:], pts[cols * rows - 1][2:], pts[rows - 1][2:]]}, open(fp, "w")); print("saved", len(pts), fp)
    else:
        print(__doc__)

if __name__ == "__main__": main()
