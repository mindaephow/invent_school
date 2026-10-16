# 번호 하나의 조립 결과를 "책 그림 위에 겹쳐" 증명한다 — 눈대중으로 "맞다"고 하지 않기 위한 도구(사용자 지시 2026-10-17, 어보이더 18번:
#   "니가 조립한게 맞는지 확인을 안하자나, 책을 다 뒤져서 맞는 이유를 증명해야 한다 — 그걸 이미지 작업에 다 남겨").
#   python overlay_check.py <이름> <번호> [--없이 부품이름 …]
# 하는 일
#   1) refs/<이름>/fits/NN_P.json 의 3D 점(xyz)과 책 그림 점(pts)으로 카메라를 PnP 로 푼다(점마다 오차 px 를 보여 준다).
#      점은 모델에서 3D 가 확정된 것(돌기 끝·판 구멍·리벳 끝)을 확대 눈금 그림에서 읽어 xyz 에 적는다. 평면 점만이면 해가 둘이라 위쪽이 위인 해를 고른다.
#   2) 이 번호까지 만든 모델의 부품 상자(dims.json)를 같은 카메라로 책 그림 위에 겹쳐 refs/<이름>/NN_3.jpg 로 저장한다(index.json 에 idx 3 으로 적는다).
#      이번 번호에서 띄워 놓은 부품(dir·hover)은 책 그림처럼 띄운 자리에 그린다.
#   3) 읽은 점 오차·카메라 값을 그림 아래에 적는다. 가설이 둘이면(예: 안쪽 블록 / 바깥 블록) fits 점의 xyz 만 바꿔 다시 돌려 오차로 가린다.
# 마지막으로 만든 번호만 정확하다(모델 좌표가 그 번호 이후 자세라서). 앞 번호는 그 번호를 만들 때 한 번 돌려 둔다.
# 이 그림과 "무엇을 어떻게 가렸는지 한 줄"을 읽기 표 판단과정에 적고, 올린 뒤 DB 에 올린다(viewer_snippets.md 3). rulecheck 가 NN_3.jpg 가 있는지 본다.
import json, math, os, runpy, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
from pnp import fit, cam_from
from PIL import Image, ImageDraw, ImageFont

here = os.path.dirname(os.path.abspath(__file__))
COLORS = {"315프레임": (255, 0, 0), "DC모터": (0, 160, 0), "37프레임": (0, 0, 255), "27프레임": (0, 128, 255), "29프레임": (255, 0, 255), "2열브라켓": (255, 0, 255),
          "2단블록": (0, 200, 200), "3단블록": (0, 200, 200), "15프레임": (120, 0, 120), "115프레임": (120, 0, 120), "작은바퀴": (0, 255, 255)}

def wrap(d, text, font, maxw):
    out, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > maxw: out.append(cur); cur = ch
        else: cur += ch
    out.append(cur); return out

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    name, N = sys.argv[1], int(sys.argv[2])
    skip = set(sys.argv[sys.argv.index("--없이") + 1:]) if "--없이" in sys.argv else set()
    R = os.path.join(here, "refs", name)
    f = json.load(open(os.path.join(R, "fits", "%02d_P.json" % N), encoding="utf-8"))
    if not f.get("xyz"): sys.exit("fits/%02d_P.json 에 xyz(3D 점)가 없다 — 모델에서 3D 가 확정된 점의 xyz 를 적고 pts 에 책 그림 픽셀을 적는다." % N)
    obj = np.array(f["xyz"], float); img = [[p[2], p[3]] for p in f["pts"]]
    im = cv2.imread(os.path.join(R, "%02d.jpg" % N)); H, W = im.shape[:2]; c = obj.mean(0)
    best = None
    for fov in range(15, 61):
        r = fit(obj - c, img, W, H, fov)
        if r:
            e, rv, tv, K = r; C, fwd, up, right = cam_from(rv, tv)
            if up[1] > 0 and (best is None or e < best[0]): best = (e, fov, rv, tv, K)
    if not best: sys.exit("카메라를 못 풀었다(점이 너무 적거나 한 줄)")
    e, fov, rv, tv, K = best
    P = lambda q: cv2.projectPoints(np.float32([np.array(q, float) - c]), rv, tv, K, None)[0][0][0]
    proj = np.array([P(q) for q in obj]); errs = np.linalg.norm(proj - np.array(img), axis=1)
    print("카메라 오차 평균 %.2fpx · 최대 %.1fpx · 점 %d개 · fov %d" % (e, errs.max(), len(obj), fov))
    print("점별 오차(px):", [round(float(v), 1) for v in errs])
    g = runpy.run_path(os.path.join(here, name + ".py"), run_name="probe"); A = g["A"]
    dims = json.load(open(os.path.join(here, "dims.json"), encoding="utf-8"))
    if N != max([i for i, st in enumerate(A.steps, 1) if st.parts or st.kw.get("moveMade")] or [0]):
        print("⚠ 마지막으로 만든 번호가 아니다 — 모델 좌표는 그 번호 이후 자세라서 겹침이 어긋날 수 있다.")
    hover = {}   # id(part) → 띄운 만큼 옮길 벡터
    st = A.steps[N - 1]
    for q in A.parts:
        if q.step.index == N and hasattr(q, "extra"):
            ex = q.extra or {}; h = ex.get("hover"); d = ex.get("dir")
            if h and d: hover[id(q)] = np.array(d, float) * float(h)
    for key, ent in (st.kw.get("moveMade") or {}).items():
        si, pi = [int(v) for v in key.split(":")]; q = A.steps[si - 1].parts[pi]
        if ent.get("hover") and ent.get("hover") > 1: hover[id(q)] = np.array(ent.get("dir", [0, 1, 0]), float) * float(ent["hover"])
    def box(Rm, p, d, col):
        Rm = np.array(Rm, float); half = np.array(d) / 2
        pts = [Rm @ (np.array([sx, sy, sz]) * half) + np.array(p) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        for a in range(8):
            for b in range(a + 1, 8):
                if bin(a ^ b).count("1") == 1: cv2.line(im, tuple(int(v) for v in P(pts[a])), tuple(int(v) for v in P(pts[b])), col, 1)
    for q in A.parts:
        nm = q.name.split(" ")[0]
        if q.step.index > N or nm in skip or nm not in COLORS or nm not in dims: continue
        p = np.array(q.p, float) + hover.get(id(q), 0)
        box(q.R, p, dims[nm], COLORS[nm])
    for p in img: cv2.circle(im, (int(p[0]), int(p[1])), 4, (255, 255, 0), 1)
    lines = ["증명 — %d번 책 그림 위에 모델(1~%d번)을 같은 카메라로 겹침. 카메라 = 점 %d개 PnP 평균 %.2fpx·최대 %.1fpx (하늘색 동그라미 = 읽은 점). 빨강=315프레임 파랑 계열=판·블록 보라=팔 판 노랑=바퀴 등." % (N, N, len(obj), e, errs.max()),
             "읽은 점: " + str(f.get("name", ""))]
    fnt = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 17); tmp = ImageDraw.Draw(Image.new("RGB", (W, 10)))
    wl = [];  [wl.extend(wrap(tmp, ln, fnt, W - 24)) for ln in lines]
    band = len(wl) * 26 + 24
    rgb = Image.fromarray(cv2.cvtColor(np.vstack([im, np.full((band, W, 3), 255, np.uint8)]), cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(rgb); y = H + 12
    for ln in wl: d.text((12, y), ln, fill=(20, 20, 20), font=fnt); y += 26
    outp = os.path.join(R, "%02d_3.jpg" % N); cv2.imwrite(outp, cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    ip = os.path.join(R, "index.json"); idx = json.load(open(ip, encoding="utf-8"))
    idx = [r for r in idx if not (int(r["step"]) == N and int(r["idx"]) == 3)]
    idx.append({"step": N, "idx": 3, "file": "%02d_3.jpg" % N, "note": "⑤ 단계 %d — 증명: 모델을 책 그림 위에 같은 카메라(점 %d개 PnP 평균 %.2fpx)로 겹침(overlay_check.py)." % (N, len(obj), e)})
    idx.sort(key=lambda r: (int(r["step"]), int(r["idx"]))); json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", outp, "— 눈으로 부품 상자가 책 그림 부품 위에 올라갔는지 보고, 판단과정에 한 줄 적고, DB 에 올린다.")

if __name__ == "__main__": main()
