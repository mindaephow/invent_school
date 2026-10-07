# 교재 참고 그림 만들기: 조립도 한 차시의 교재 쪽에서 "완성품 사진"과 단계마다 그림 한 장씩을 잘라 refs/<이름>/ 에 저장한다.
#   python refs_make.py kidknight          (교재 쪽 이미지는 tempfile 폴더의 cubo<권>_p<쪽>.jpg — textbook_view.py 가 쓰는 것과 같은 이름, 없으면 PDF 에서 렌더하거나 서버에서 받는다)
# 만든 것: refs/<이름>/NN.jpg(단계 N 그림, 00 = 교재 맨 앞 완성품 사진), 단계에 따라 NN_k.jpg(돌리거나 확대해서 칸을 센 그림), refs/<이름>/index.json(단계·번호·설명).
# ※ 이 스크립트를 다시 돌리면 refs/<이름>/ 의 격자 그림(NN_2.jpg, refs_grid.py 로 그린 것)과 index.json 의 그 줄이 사라진다 — 다시 돌린 뒤 refs_grid.py 로 격자를 다시 그린다.
# 조립도를 만들 때 앞뒤·정면·뒷면이 헷갈리면 먼저 00.jpg(완성품)와 그 단계 그림을 다시 본다(관리자 지시 2026-10-06).
# 같은 그림을 화면(조립 순서 목록, 관리자 전용)에 올리는 것은 refs_upload.js 설명 참고 — 표 ivs_assembly_refs(supabase/assembly_refs.sql).
import sys, os, json, tempfile, urllib.request
import cv2, numpy as np

K = 2524 / 1430.0   # 교재 쪽 그림(가로 2524px)과 눈으로 읽은 1430px 판의 비율
COL = {"L": (75, 705), "R": (720, 1355)}
ROW = {1: (200, 752), 2: (765, 1313), 3: (1328, 1880)}
def box(c, r): return (COL[c][0], ROW[r][0], COL[c][1], ROW[r][1])
GRID = [("L", 1), ("R", 1), ("L", 2), ("R", 2), ("L", 3), ("R", 3)]   # 쪽마다 그림 6칸(왼쪽→오른쪽, 위→아래)

# 차시 정의: 쪽 → [(단계 번호(0=완성품, 99=완성), 상자(1430px 판 좌표), 설명)]
BOOKS = {
    "formula1": {
        "volume": 1,
        "pages": {
            110: [(0, (130, 490, 1020, 1300), "교재 110쪽 맨 앞 완성품 사진 — 앞·뒤·바퀴·날개 방향은 여기서 확인"), (1, (78, 1324, 706, 1870), ""), (2, (721, 1324, 1355, 1870), "")],
            111: [(3 + i, box(*g), "") for i, g in enumerate(GRID)],
            112: [(9 + i, box(*g), "") for i, g in enumerate(GRID)],
            113: [(15 + i, box(*g), "") for i, g in enumerate(GRID)],
            114: [(21 + i, box(*g), "") for i, g in enumerate(GRID)],
            115: [(27 + i, box(*g), "") for i, g in enumerate(GRID)],
            116: [(33, box("L", 1), ""), (99, box("R", 1), "완성")],
        },
        "extra": [],
    },
    "kidknight": {
        "volume": 1,
        "pages": {
            100: [(0, (60, 515, 1075, 1290), "교재 100쪽 맨 앞 완성품 사진 — 앞(눈·입)과 팔·방패·칼이 어느 쪽인지 여기서 확인"), (1, (75, 1330, 705, 1888), ""), (2, (720, 1330, 1355, 1888), "")],
            101: [(3 + i, box(*g), "") for i, g in enumerate(GRID)],
            102: [(9 + i, box(*g), "") for i, g in enumerate(GRID)],
            103: [(15 + i, box(*g), "") for i, g in enumerate(GRID)],
            104: [(21 + i, box(*g), "") for i, g in enumerate(GRID)],
            105: [(27 + i, box(*g), "") for i, g in enumerate(GRID)],
            106: [(33, box("L", 1), ""), (34, box("R", 1), ""), (35, box("L", 2), ""), (36, box("R", 2), ""), (99, box("L", 3), "완성")],
        },
        # 돌리거나 확대해서 칸을 센 그림: (단계, 번호, 만드는 방법, 설명). level = 판의 긴 방향이 수평이 되게 돌린 각도(자동으로 잰 뒤 눈으로 확인한 값; 서 있는 로봇 16~19는 돌리지 않고 확대만)
        "extra": [(s, 1, {"level": a}, "단계 %d — 판의 긴 방향이 수평이 되게 %d° 돌린 그림(구멍 칸 세기용)" % (s, abs(a))) for s, a in
                  {1: 13, 2: 19, 3: 18, 4: 17, 5: 20, 6: 33, 7: 20, 8: 30, 9: 26, 10: -12, 11: -15, 12: -24, 13: 17, 15: -1, 20: -34}.items()] + [
            (16, 1, {"zoom": (0.40, 0.0, 0.73, 0.80), "scale": 1.6}, "단계 16 — 벽 확대: 리벳 4개는 벽 줄6·줄8(머리 쪽 끝이 줄1)의 바깥 두 칸(칸1·칸3). 37프레임은 오른쪽 끝 칸5·칸7 이 리벳에 끼워지고 왼쪽 4칸이 튀어나온다"),
            (17, 1, {"zoom": (0.18, 0.42, 0.95, 1.0), "scale": 1.4}, "단계 17 — 아래쪽 확대: 큰기어 위 구멍(벽 가운데 칸, 큰기어에서 3칸 위)에 작은기어+T축"),
            (18, 1, {"zoom": (0.18, 0.42, 0.95, 1.0), "scale": 1.4}, "단계 18 — 아래쪽 확대: 반대쪽 벽에도 같은 모양(리벳 4 + 37프레임)"),
            (19, 1, {"zoom": (0.12, 0.40, 0.92, 1.0), "scale": 1.4}, "단계 19 — 아래쪽 확대: 반대쪽 큰기어 위 구멍에 작은기어+T축"),
        ],    },
}

def page_image(volume, page):
    p = os.path.join(tempfile.gettempdir(), "cubo%d_p%03d.jpg" % (volume, page))
    if not os.path.exists(p):
        url = "https://brfeszcyjsaprbakqsjl.supabase.co/storage/v1/object/public/textbook-files/pages/cubo%d/p%03d.jpg" % (volume, page)
        urllib.request.urlretrieve(url, p)   # 서버에 올려 둔 쪽(큐보 1권 일부). 없으면 PDF 를 pymupdf 로 렌더해 이 이름으로 저장해 둔다
    return cv2.imread(p)

def crop(im, b, width=1000):
    x0, y0, x1, y1 = [int(v * K) for v in b]
    c = im[y0:y1, x0:x1]
    s = width / c.shape[1]
    return cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)

def save(c, path): cv2.imwrite(path, c, [cv2.IMWRITE_JPEG_QUALITY, 78])

def redo(name, only):   # --only 6,15 : 이미 만든 NN.jpg 에서 그 단계의 돌린 그림(NN_1)만 다시 만든다(격자 NN_2 는 지운다 — refs_grid.py 로 다시 그린다. 다른 단계는 그대로)
    B = BOOKS[name]; out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", name); p = os.path.join(out, "index.json"); index = json.load(open(p, encoding="utf-8"))
    for step, k, how, note in B["extra"]:
        if step not in only: continue
        c = cv2.imread(os.path.join(out, "%02d.jpg" % step)); h, w = c.shape[:2]
        if "level" in how: c = cv2.warpAffine(c, cv2.getRotationMatrix2D((w / 2, h / 2), -how["level"], 1.0), (w, h), borderValue=(255, 255, 255))
        save(c, os.path.join(out, "%02d_%d.jpg" % (step, k)))
        index = [r for r in index if not (r["step"] == step and r["idx"] in (k, 2))] + [{"step": step, "idx": k, "file": "%02d_%d.jpg" % (step, k), "note": note}]
        g = os.path.join(out, "%02d_2.jpg" % step)
        if os.path.exists(g): os.remove(g)
    index.sort(key=lambda r: (r["step"], r["idx"])); json.dump(index, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("다시 만든 단계:", sorted(only))

def main():
    if "--only" in sys.argv: redo(sys.argv[1], {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}); return
    name = sys.argv[1]; B = BOOKS[name]; out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs", name); os.makedirs(out, exist_ok=True)
    index = []; crops = {}
    for page, items in B["pages"].items():
        im = page_image(B["volume"], page)
        for step, b, note in items:
            c = crop(im, b); fn = "%02d.jpg" % step; save(c, os.path.join(out, fn)); crops[step] = c
            index.append({"step": step, "idx": 0, "file": fn, "note": note or ("교재 %d쪽 단계 %s 그림" % (page, "완성" if step == 99 else step))})
    for step, k, how, note in B["extra"]:
        c = crops[step]; h, w = c.shape[:2]
        if "level" in how:   # 수평이 되게: 장면을 −level° 돌린다(cv2 양수 = 반시계)
            M = cv2.getRotationMatrix2D((w / 2, h / 2), -how["level"], 1.0); c = cv2.warpAffine(c, M, (w, h), borderValue=(255, 255, 255))
        if "zoom" in how:
            x0, y0, x1, y1 = how["zoom"]; c = c[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            c = cv2.resize(c, None, fx=how.get("scale", 1.0), fy=how.get("scale", 1.0), interpolation=cv2.INTER_CUBIC)
        fn = "%02d_%d.jpg" % (step, k); save(c, os.path.join(out, fn)); index.append({"step": step, "idx": k, "file": fn, "note": note})
    index.sort(key=lambda r: (r["step"], r["idx"]))
    json.dump(index, open(os.path.join(out, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(os.path.getsize(os.path.join(out, r["file"])) for r in index)
    print("만든 그림 %d장, 합계 %d KB → %s" % (len(index), tot // 1024, out))

if __name__ == "__main__": main()



