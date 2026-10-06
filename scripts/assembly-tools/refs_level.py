# 수평 기준선에 맞춰 돌리기(관리자 지시 2026-10-06): 판 가운데 줄이 화면 가로선과 나란해질 때까지 그림을 돌리고, 그 가로선(파란 선)을 격자 그림(NN_2)에 같이 그려 눈으로 맞았는지 확인하게 한다.
#   python refs_level.py kidknight            refs/<이름>/grids.json 의 격자 정의(단계·구멍 좌표 짝·칸×줄·이름·ref)를 읽어 단계마다
#     ① ref 판의 가운데 줄(첫 칸 가운데 ~ 끝 칸 가운데)이 가로선이 되도록 NN_1 을 돌리고(남은 기울기만큼, 여러 번 돌려도 결과가 같다)
#     ② 같은 단계의 격자 좌표를 같은 변환으로 옮기고 ③ NN_2(격자 + 파란 가로선)를 다시 그린 뒤 grids.json·index.json 을 갱신한다.
#   grids.json 의 pts = [[칸, 줄, x, y], …] (그림 속 구멍 중심 4개 이상), ref = true 인 판이 그 단계의 수평 기준이다. 서 있는 로봇(16~19번)은 ref 를 안 주면 돌리지 않고 격자만 다시 그린다.
import sys, os, json
import cv2, numpy as np
from refs_grid import grid

HERE = os.path.dirname(os.path.abspath(__file__))

def homography(pts):
    src = np.array([[c - 1, r - 1] for c, r, _, _ in pts], np.float32); dst = np.array([[x, y] for _, _, x, y in pts], np.float32)
    H, _ = cv2.findHomography(src, dst, 0); return H

def P(H, c, r):
    v = H @ np.array([c, r, 1.0]); return np.array([v[0] / v[2], v[1] / v[2]])

PRE = {1: 0.5, 2: -0.1, 3: 0.9, 4: 1.5, 5: 0.2, 6: -0.4, 7: -0.4, 8: -0.4, 10: -0.6, 13: 3.0, 14: -0.9, 20: 1.7}   # 처음 refs_level 을 돌릴 때(2026-10-06) 이미 더 돌린 각도(남은 기울기) — 원본→돌린 그림 변환을 거꾸로 풀 때 쓴다
CIRC = "①②③④"

def main():
    name = sys.argv[1]; d = os.path.join(HERE, "refs", name); gp = os.path.join(d, "grids.json"); G = json.load(open(gp, encoding="utf-8")); index = json.load(open(os.path.join(d, "index.json"), encoding="utf-8"))
    steps = sorted({g["step"] for g in G}); report = []; g_first_run = False   # 보정각은 PRE 에 이미 합쳐 두었다(다시 돌려도 남은 기울기 ≈ 0)
    for s in steps:
        gs = [g for g in G if g["step"] == s]; ref = next((g for g in gs if g.get("ref")), None); base_idx = gs[0].get("idx", 1)
        f1 = os.path.join(d, "%02d_%d.jpg" % (s, base_idx)); im = cv2.imread(f1 if os.path.exists(f1) else os.path.join(d, "%02d.jpg" % s)); h, w = im.shape[:2]
        alpha = 0.0; M = np.array([[1, 0, 0], [0, 1, 0]], np.float64)
        if ref:
            H = homography(ref["pts"]); rm = (ref["rows"] + 1) / 2.0; a, b = P(H, 1, rm), P(H, ref["cols"], rm)
            if b[0] < a[0]: a, b = b, a   # 15번처럼 칸 번호가 오른쪽에서 왼쪽으로 늘어나는 판도 왼쪽→오른쪽 방향으로 잰다
            alpha = float(np.degrees(np.arctan2(-(b[1] - a[1]), b[0] - a[0])))   # 가운데 줄이 오른쪽으로 올라가는 각도(+)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), -alpha, 1.0)
            if os.path.exists(f1) or True:
                rot = cv2.warpAffine(im, M, (w, h), borderValue=(255, 255, 255)); cv2.imwrite(os.path.join(d, "%02d_%d.jpg" % (s, base_idx)), rot, [cv2.IMWRITE_JPEG_QUALITY, 78]); im = rot
            for g in G:
                if g["step"] == s: g["pts"] = [[c, r, float(M[0, 0] * x + M[0, 1] * y + M[0, 2]), float(M[1, 0] * x + M[1, 1] * y + M[1, 2])] for c, r, x, y in g["pts"]]
        # NN_2: 격자 + 파란 가로선(ref 판 가운데 줄의 높이)
        o = im.copy(); names = []
        for g in [g for g in G if g["step"] == s]:
            o = grid(o, None, g["cols"], g["rows"], None, [tuple(p) for p in g["pts"]]); names.append("%s %d칸×%d줄" % (g["name"], g["cols"], g["rows"]))
        if ref:
            H = homography(ref["pts"]); rm = (ref["rows"] + 1) / 2.0; y0 = int(round((P(H, 1, rm)[1] + P(H, ref["cols"], rm)[1]) / 2))
            cv2.line(o, (0, y0), (w, y0), (255, 140, 0), 2, cv2.LINE_AA); cv2.putText(o, "horizontal", (w - 130, y0 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 140, 0), 2)
        cv2.imwrite(os.path.join(d, "%02d_2.jpg" % s), o, [cv2.IMWRITE_JPEG_QUALITY, 80])
        index = [r for r in index if not (r["step"] == s and r["idx"] == 2)] + [{"step": s, "idx": 2, "file": "%02d_2.jpg" % s, "names": names, "note": "단계 %d — 칸 격자(빨강 = 구멍 중심, 위 숫자 = 칸, 왼쪽 숫자 = 줄): %s.%s 눈으로 읽은 좌표라 추정이다." % (s, " / ".join(names), (" 파란 가로선 = 판 가운데 줄을 수평으로 맞춘 기준선(이번에 %+.1f° 더 돌림)." % -alpha) if ref else "")}]
        # 1차 격자: 같은 구멍 좌표를 돌리기 전 원본 그림에 그린다(원근 그대로) → NN_3.jpg. 원본→돌린 그림 변환 = 처음 돌린 각도(refs_make 의 level) + 이후 보정각
        from refs_make import BOOKS
        a0 = next((how.get("level", 0) for st, k, how, _ in BOOKS[name]["extra"] if st == s and "level" in how), 0.0)
        th = -a0 - PRE.get(s, 0.0) - (alpha if ref and g_first_run else 0.0)
        Mt = cv2.getRotationMatrix2D((w / 2, h / 2), th, 1.0) if (a0 or s in PRE) else np.array([[1, 0, 0], [0, 1, 0]], np.float64); Mi = cv2.invertAffineTransform(Mt)
        raw = cv2.imread(os.path.join(d, "%02d.jpg" % s)); ro = raw.copy()
        for g in [g for g in G if g["step"] == s]:
            ptr = [(c, r, float(Mi[0, 0] * x + Mi[0, 1] * y + Mi[0, 2]), float(Mi[1, 0] * x + Mi[1, 1] * y + Mi[1, 2])) for c, r, x, y in g["pts"]] if (a0 or s in PRE) else [tuple(p) for p in g["pts"]]
            ro = grid(ro, None, g["cols"], g["rows"], None, ptr)
        cv2.imwrite(os.path.join(d, "%02d_3.jpg" % s), ro, [cv2.IMWRITE_JPEG_QUALITY, 80])
        index = [r for r in index if not (r["step"] == s and r["idx"] == 3)] + [{"step": s, "idx": 3, "file": "%02d_3.jpg" % s, "note": "단계 %d — 원본 그림(돌리기 전, 원근 그대로) 위에 같은 칸 격자를 그린 1차 격자. 구멍 좌표를 돌린 그림에서 읽어 거꾸로 옮긴 것이라 추정이다." % s}]
        report.append((s, round(alpha, 1)))
    has_lvl = {s for s in steps if any(g.get("ref") for g in G if g["step"] == s)}
    for r in index:
        txt = r["note"].lstrip(CIRC + " ")
        r["note"] = ("①" if r["idx"] == 0 else "②" if r["idx"] == 3 else ("④" if r["step"] in has_lvl else "②") if r["idx"] == 2 else "③") + " " + txt
    index.sort(key=lambda r: (r["step"], r["idx"])); json.dump(index, open(os.path.join(d, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(G, open(gp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("단계별 남은 기울기(보정 전):", report)

if __name__ == "__main__": main()


