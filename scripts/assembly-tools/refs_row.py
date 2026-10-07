# 한 줄짜리 프레임(115프레임 등)과 반원프레임처럼 refs_fit 의 사각 격자로 못 하는 부품에 번호를 붙이는 보조 도구(꼬마기사 30번, 2026-10-07).
#   사각 격자(칸×줄)는 줄이 2개 이상이어야 원근을 계산할 수 있다. 한 줄 프레임은 구멍 중심이 일직선이라 번호만 붙이면 충분하다 — 보이는 구멍을 찾아 한 줄로 이어 번호를 매기고, 가려진 칸은 간격으로 연장한다.
#   입력(JSON, 표준입력): {"name","step","crop":[x0,y0,x1,y1],"erase":[[...]],
#       "rows":[{"name":"115프레임","bbox":[...],"lo":90,"hi":200,"amin":250,"count":15,"start_from_first":true|false,"extend_to":15,"flip":false}],
#       "arcs":[{"name":"반원프레임","approx":[[x,y]*9],"snap":12,"lo":60,"hi":215,"amin":150}], "note":""}
#   출력: refs/<이름>/NN_1.jpg (원본 위 번호) · NN_2.jpg (한 줄 프레임이 수평이 되게 돌린 그림 + 파란 수평선) 와 index.json 갱신. DB 등록은 refs_upload.js.
import sys, os, json
import cv2, numpy as np
from refs_auto import detect, load_orig, refs_dir

def label(o, p, text, color=(0, 0, 255)):
    cv2.circle(o, (int(p[0]), int(p[1])), 4, color, -1)
    cv2.putText(o, text, (int(p[0]) - 8, int(p[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)

def main(a):
    name, step = a["name"], int(a["step"]); d = refs_dir(name); im = load_orig(name, step).copy()
    for (x0, y0, x1, y1) in a.get("erase") or []: im[int(y0):int(y1), int(x0):int(x1)] = 255
    cx0, cy0, cx1, cy1 = [int(v) for v in (a.get("crop") or [0, 0, im.shape[1], im.shape[0]])]
    notes = []; marks = []                                     # marks: (x, y, 글자) 원본 좌표
    ref_line = None
    for r in a.get("rows") or []:
        P = detect(im, r["bbox"], r.get("lo", 90), r.get("hi", 200), r.get("amin", 250))
        if len(P) < 3: raise SystemExit("구멍을 못 찾았어요: " + r.get("name", ""))
        k = np.polyfit(P[:, 0], P[:, 1], 1); axis = np.array([1.0, k[0]]); axis /= np.linalg.norm(axis)
        order = np.argsort(P @ axis); P = P[order]
        sp = np.median(np.linalg.norm(np.diff(P, axis=0), axis=1))   # 이웃 간격(원근으로 서서히 변한다)
        pts = [p for p in P]
        n = int(r["count"])
        # 가려진 칸 연장: 끝(큰 x) 쪽, 그리고 필요하면 시작 쪽
        while len(pts) < n:
            v = pts[-1] - pts[-2]; pts.append(pts[-1] + v * 0.97)
        start = int(r.get("first_no", 1))                          # 검출된 첫 구멍의 번호(꼬리 쪽 구멍이 가려졌으면 1 이 아니다)
        for i, p in enumerate(pts[:n - start + 1]): marks.append((float(p[0]), float(p[1]), str(i + start)))
        ref_line = (pts[0], pts[min(len(pts), n - start + 1) - 1])
        notes.append("%s 구멍 %d개(%d번~%d번, 한 줄)" % (r.get("name", "프레임"), n - start + 1, start, n))
    for ar in a.get("arcs") or []:
        P = detect(im, ar.get("bbox") or [0, 0, im.shape[1], im.shape[0]], ar.get("lo", 60), ar.get("hi", 215), ar.get("amin", 150))
        for i, ap in enumerate(ar["approx"]):
            q = np.array(ap, float)
            if len(P):
                dd = np.linalg.norm(P - q, axis=1); j = int(dd.argmin())
                if dd[j] < ar.get("snap", 12): q = P[j].astype(float)
            marks.append((float(q[0]), float(q[1]), "h%d" % (i + 1)))
        notes.append("%s 구멍 9개(h1~h9, 가운데 h5 가 꼭짓점)" % ar.get("name", "반원프레임"))
    crop = im[cy0:cy1, cx0:cx1].copy(); o1 = crop.copy()
    for (x, y, t) in marks: label(o1, (x - cx0, y - cy0), t)
    cv2.imwrite(os.path.join(d, "%02d_1.jpg" % step), o1, [cv2.IMWRITE_JPEG_QUALITY, 82])
    # 2차: 한 줄 프레임이 수평이 되게 돌리기
    h, w = crop.shape[:2]; alpha = 0.0
    if ref_line is not None:
        p0, p1 = ref_line; alpha = float(np.degrees(np.arctan2(-(p1[1] - p0[1]), p1[0] - p0[0])))
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -alpha, 1.0); cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(h * sn + w * cs) + 1, int(h * cs + w * sn) + 1
    M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
    rot = cv2.warpAffine(crop, M, (nw, nh), borderValue=(255, 255, 255)); o2 = rot.copy()
    for (x, y, t) in marks:
        q = M @ np.array([x - cx0, y - cy0, 1.0]); label(o2, q, t)
    if ref_line is not None:
        pa = M @ np.array([ref_line[0][0] - cx0, ref_line[0][1] - cy0, 1.0]); pb = M @ np.array([ref_line[1][0] - cx0, ref_line[1][1] - cy0, 1.0]); y0 = int(round((pa[1] + pb[1]) / 2))
        cv2.line(o2, (0, y0), (nw, y0), (255, 140, 0), 2, cv2.LINE_AA); cv2.putText(o2, "horizontal", (nw - 130, y0 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 140, 0), 2)
    ys, xs = np.where(cv2.cvtColor(rot, cv2.COLOR_BGR2GRAY) < 245); pad = 16
    if len(xs): o2 = o2[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad]
    cv2.imwrite(os.path.join(d, "%02d_2.jpg" % step), o2, [cv2.IMWRITE_JPEG_QUALITY, 82])
    ip = os.path.join(d, "index.json"); index = json.load(open(ip, encoding="utf-8")); index = [r for r in index if not (r["step"] == step and r["idx"] in (1, 2, 3))]
    nm = " / ".join(notes); extra = a.get("note", "")
    index += [{"step": step, "idx": 1, "file": "%02d_1.jpg" % step, "note": "② 단계 %d — 부품만 잘라 낸 원본 그림(돌리기 전, 원근 그대로) 위의 번호(한 줄 프레임은 칸 번호, 반원프레임은 구멍 번호 h1~h9): %s. %s" % (step, nm, extra)},
              {"step": step, "idx": 2, "file": "%02d_2.jpg" % step, "note": "④ 단계 %d — 한 줄 프레임의 긴 방향이 수평이 되게 %.1f° 돌린 그림 위의 번호: %s. 파란 가로선 = 한 줄 프레임의 구멍 줄을 수평으로 맞춘 기준선. %s" % (step, alpha, nm, extra)}]
    index.sort(key=lambda r: (r["step"], r["idx"])); json.dump(index, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return {"rotated_deg": round(alpha, 2), "files": ["%02d_1.jpg" % step, "%02d_2.jpg" % step], "marks": len(marks)}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); print(json.dumps(main(json.loads(sys.stdin.read() or "{}")), ensure_ascii=False))
