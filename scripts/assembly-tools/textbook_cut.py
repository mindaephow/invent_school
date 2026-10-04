# 교재 그림에서 부품 하나를 가위처럼 오려 낸다 (MobileSAM, 이 컴퓨터 안에서만 처리).
#   python textbook_cut.py <권> <쪽> x0 y0 x1 y1 --pt X,Y [--pt X,Y ...] [--neg X,Y ...] --out 이름.png
#   x0 y0 x1 y1 = 쪽 전체를 0~1 로 본 비율 범위(부품 주변을 넉넉히). --pt = 오려 낼 부품 위의 점(쪽 원본 픽셀 좌표), --neg = 빼고 싶은 곳의 점.
#   결과: <이름>_cut.png(오려 낸 부품만, 바깥은 흰색), <이름>_mask.png(마스크), <이름>_overlay.png(원본 위에 초록으로 칠한 확인용)
# 모델 파일: scripts/assembly-tools/models/ (mobile_sam_image_encoder.onnx, sam_mask_decoder_single.onnx — huggingface.co/Acly/MobileSAM)
import sys, os
import numpy as np, cv2
import onnxruntime as ort
from textbook_view import fetch_page

HERE = os.path.dirname(os.path.abspath(__file__))
_enc = _dec = None

def load():
    global _enc, _dec
    if _enc is None:
        p = ["CPUExecutionProvider"]
        _enc = ort.InferenceSession(os.path.join(HERE, "models", "mobile_sam_image_encoder.onnx"), providers=p)
        _dec = ort.InferenceSession(os.path.join(HERE, "models", "sam_mask_decoder_single.onnx"), providers=p)
    return _enc, _dec

def cut(img_bgr, pos, neg=()):
    """img_bgr 안에서 pos 점들이 가리키는 부품의 마스크(0/255) 를 돌려준다. 점은 img 픽셀 좌표.
    시험으로 알아낸 사용법(2026-10-04): 그림을 긴 변 1024 로 줄여 오른쪽·아래를 0 으로 채운 1024×1024 로 직접 만들어 넣고,
    점 좌표도 같은 비율(1024/긴 변)로 줄이고, 끝에 (0,0) 라벨 -1 채움 점을 붙인다(안 하면 엉뚱한 네모가 나옴)."""
    enc, dec = load()
    H, W = img_bgr.shape[:2]
    s = 1024.0 / max(H, W)
    rs = cv2.resize(img_bgr, (round(W * s), round(H * s)), interpolation=cv2.INTER_AREA)
    pad = np.zeros((1024, 1024, 3), np.uint8); pad[:rs.shape[0], :rs.shape[1]] = rs
    emb = enc.run(None, {"input_image": cv2.cvtColor(pad, cv2.COLOR_BGR2RGB).astype(np.float32)})[0]
    pts = [(x * s, y * s) for x, y in pos] + [(x * s, y * s) for x, y in neg] + [(0.0, 0.0)]
    labels = [1.0] * len(pos) + [0.0] * len(neg) + [-1.0]
    out = dec.run(None, {
        "image_embeddings": emb, "point_coords": np.array(pts, np.float32)[None], "point_labels": np.array(labels, np.float32)[None],
        "mask_input": np.zeros((1, 1, 256, 256), np.float32), "has_mask_input": np.zeros(1, np.float32),
        "orig_im_size": np.array([H, W], np.float32)})
    masks, iou = out[0], out[1]
    k = int(np.argmax(iou.ravel())) if masks.shape[1] > 1 else 0
    m = (masks[0, k] > 0).astype(np.uint8) * 255
    return m, float(iou.max())

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    a = sys.argv[1:]
    pos, neg, out = [], [], None
    def take(flag, lst):
        while flag in a:
            i = a.index(flag); x, y = a[i + 1].split(","); lst.append((float(x), float(y))); del a[i:i + 2]
    take("--pt", pos); take("--neg", neg)
    if "--out" in a: i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    if len(a) < 6 or not pos or not out:
        print(__doc__); sys.exit(1)
    vol, page = int(a[0]), int(a[1]); box = [float(v) for v in a[2:6]]
    img = fetch_page(vol, page); H, W = img.shape[:2]
    x0, y0, x1, y1 = int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)
    crop = img[y0:y1, x0:x1].copy()
    sh = lambda L: [(x - x0, y - y0) for x, y in L]
    m, iou = cut(crop, sh(pos), sh(neg))
    base = os.path.splitext(out)[0]
    cutimg = np.full_like(crop, 255); cutimg[m > 0] = crop[m > 0]
    ov = crop.copy(); ov[m > 0] = (0.5 * ov[m > 0] + 0.5 * np.array([0, 200, 0])).astype(np.uint8)
    cv2.imencode(".png", cutimg)[1].tofile(base + "_cut.png")
    cv2.imencode(".png", m)[1].tofile(base + "_mask.png")
    cv2.imencode(".png", ov)[1].tofile(base + "_overlay.png")
    area = int((m > 0).sum())
    print(f"오려 냄: 부품 면적 {area}px (범위의 {100 * area / m.size:.1f}%), 모델 확신도 {iou:.2f}")
    print("저장:", base + "_cut.png", base + "_overlay.png", base + "_mask.png")

if __name__ == "__main__":
    main()
