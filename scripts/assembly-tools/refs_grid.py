# 돌려서 수평으로 맞춘 교재 그림(refs/<이름>/NN_1.jpg) 위에 판의 칸 격자를 그린다 → refs/<이름>/NN_2.jpg (같은 단계의 세 번째 그림).
#   1) 자 그리기:  python refs_grid.py ruler kidknight 20 1           → 그림에 100px 자를 얹은 임시 PNG 를 만든다(모서리 픽셀 좌표를 읽을 때 쓴다)
#   2) 격자 그리기: python refs_grid.py grid kidknight 20 1 --corners "x,y x,y x,y x,y" --cols 9 --rows 3 [--name "39프레임"] [--mark "칸1·줄3=초록원"]
#        corners = 판의 구멍 중심 격자 네 모서리(열1·줄1, 끝 열·줄1, 끝 열·마지막 줄, 열1·마지막 줄)의 그림 속 픽셀 좌표 — 원근 때문에 직사각형이 아니어도 된다(호모그래피). 끝 열이 가려져 안 보이면 보이는 마지막 열을 끝으로 하고 --fit-cols <그 열 번호> 를 준다(나머지 열은 격자를 연장해 그린다).
#      또는 --pts "칸,줄:x,y 칸,줄:x,y …"(4개 이상) — 그림에서 읽은 구멍 중심 좌표를 칸·줄 번호와 짝지어 준다(안내 원 자리처럼 확실한 곳을 쓰면 정확하다).
#        칸 번호는 위쪽 변 위, 줄 번호는 왼쪽 변 밖에 쓴다. 센 근거 = 눈으로 읽은 모서리 4곳이라 "추정"이다 — 격자가 구멍에 안 맞으면 모서리를 다시 읽는다.
import sys, os, json, argparse
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

def load(name, step, idx):   # 돌린 그림이 없는 단계(이미 수평이거나 서 있는 로봇)는 원본(idx 0)을 쓴다
    p = os.path.join(HERE, "refs", name, "%02d_%d.jpg" % (step, idx)); return cv2.imread(p if os.path.exists(p) else os.path.join(HERE, "refs", name, "%02d.jpg" % step))

def ruler(im, every=100):
    o = im.copy(); h, w = o.shape[:2]
    for x in range(0, w, every): cv2.line(o, (x, 0), (x, h), (255, 120, 0), 1); cv2.putText(o, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    for y in range(0, h, every): cv2.line(o, (0, y), (w, y), (255, 120, 0), 1); cv2.putText(o, str(y), (2, y + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
    return o

def grid(im, corners, cols, rows, fit_cols=None, pts=None):
    o = im.copy()
    if pts:   # --pts "칸,줄:x,y …" 4개 이상: 그림에서 읽은 구멍 중심(칸·줄 번호는 1부터)을 모두 써서 맞춘다 — 안내 원·리벳·보이는 모서리 구멍을 같이 쓰면 원근이 더 정확하다
        src = np.array([[c - 1, r - 1] for c, r, _, _ in pts], np.float32); dst = np.array([[x, y] for _, _, x, y in pts], np.float32); H, _ = cv2.findHomography(src, dst, 0)
    else:
        fc = fit_cols or cols; src = np.array([[0, 0], [fc - 1, 0], [fc - 1, rows - 1], [0, rows - 1]], np.float32); dst = np.array(corners, np.float32); H = cv2.getPerspectiveTransform(src, dst)
    def P(c, r):
        v = H @ np.array([c, r, 1.0]); return (int(round(v[0] / v[2])), int(round(v[1] / v[2])))
    for r in range(rows): cv2.line(o, P(0, r), P(cols - 1, r), (0, 0, 255), 1, cv2.LINE_AA)
    for c in range(cols): cv2.line(o, P(c, 0), P(c, rows - 1), (0, 0, 255), 1, cv2.LINE_AA)
    for c in range(cols):
        for r in range(rows): cv2.circle(o, P(c, r), 3, (0, 0, 255), -1)
    for c in range(cols):
        p = P(c, 0); cv2.putText(o, str(c + 1), (p[0] - 6, p[1] - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    for r in range(rows):
        p = P(0, r); cv2.putText(o, str(r + 1), (p[0] - 30, p[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)
    return o

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("name"); ap.add_argument("step", type=int); ap.add_argument("idx", type=int)
    ap.add_argument("--corners"); ap.add_argument("--pts"); ap.add_argument("--cols", type=int); ap.add_argument("--rows", type=int); ap.add_argument("--fit-cols", type=int, dest="fit_cols"); ap.add_argument("--name2", default=""); ap.add_argument("--add", action="store_true"); ap.add_argument("--note", default="")
    a = ap.parse_args(); im = load(a.name, a.step, a.idx)
    if a.cmd == "ruler":
        out = os.path.join(os.environ.get("TEMP", "."), "ruler_%02d_%d.png" % (a.step, a.idx)); cv2.imwrite(out, ruler(im)); print(out); return
    pts = [tuple(float(v) for v in p.split(",")) for p in a.corners.split()] if a.corners else None
    pp = [(int(k.split(":")[0].split(",")[0]), int(k.split(":")[0].split(",")[1]), float(k.split(":")[1].split(",")[0]), float(k.split(":")[1].split(",")[1])) for k in a.pts.split()] if a.pts else None
    out = os.path.join(HERE, "refs", a.name, "%02d_2.jpg" % a.step); base = cv2.imread(out) if (a.add and os.path.exists(out)) else im   # --add: 같은 단계의 다른 판 격자를 이미 그린 그림 위에 덧그린다
    o = grid(base, pts, a.cols, a.rows, a.fit_cols, pp); cv2.imwrite(out, o, [cv2.IMWRITE_JPEG_QUALITY, 80])
    p = os.path.join(HERE, "refs", a.name, "index.json"); idx = json.load(open(p, encoding="utf-8")); prev = [r for r in idx if r["step"] == a.step and r["idx"] == 2]; names = (prev[0].get("names", []) if (a.add and prev) else []) + ["%s %d칸×%d줄" % (a.name2 or "판", a.cols, a.rows)]; idx = [r for r in idx if not (r["step"] == a.step and r["idx"] == 2)]
    idx.append({"step": a.step, "idx": 2, "file": "%02d_2.jpg" % a.step, "names": names, "note": "단계 %d — 수평으로 돌린 그림에 칸 격자(빨강 = 구멍 중심, 위 숫자 = 칸, 왼쪽 숫자 = 줄): %s. 모서리 4곳을 눈으로 읽어 그린 것이라 추정이다. %s" % (a.step, " / ".join(names), a.note)})
    idx.sort(key=lambda r: (r["step"], r["idx"])); json.dump(idx, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(out)

if __name__ == "__main__": main()




