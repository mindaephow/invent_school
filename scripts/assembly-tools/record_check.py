# 번호 하나의 "화면 ↔ 책 그림 나란히 비교"를 했다는 증거를 남긴다(관리자 지시 2026-10-11).
#   python record_check.py <이름> <번호> <화면캡처.png> "<비교 결과 한 줄 — 센 개수·맞은 곳·다른 곳을 구체적으로>"
# 하는 일: 화면 캡처와 책 그림(refs/<이름>/NN.jpg)을 나란히 붙인 refs/<이름>/cmp/NN.png 를 만들고, 그 번호의 지금 내용 지문·비교 결과·시각을 <이름>_evidence.json 에 적는다.
# build.py 의 번호별 점검은 이 증거(지문이 지금 내용과 같은 것)가 있어야 그 번호의 눈으로 하는 확인 3개(화면 확대·칸 수 대조·카메라 대조)를 통과시킨다.
# 번호 내용이 바뀌면 지문이 달라져 증거가 무효가 되므로 다시 비교해야 한다. 사용자는 나중에 cmp 이미지를 열어 검토한다.
import sys, os, json, time
try:
    from PIL import Image
except ImportError:   # Pillow 가 없는 PC(2026-10-13): OpenCV 로 같은 동작(캡처 크기 확인·책 그림과 나란히 붙이기)을 한다 — 검사 기준은 그대로
    import cv2, numpy as np
    class _Im:
        def __init__(self, a): self.a = a; self.height, self.width = a.shape[:2]; self.size = (self.width, self.height)
        def convert(self, _): return self
        def resize(self, wh): return _Im(cv2.resize(self.a, tuple(int(v) for v in wh), interpolation=cv2.INTER_AREA))
        def paste(self, other, xy): x, y = xy; self.a[y:y + other.height, x:x + other.width] = other.a
        def save(self, path): cv2.imwrite(path, self.a)
    class Image:
        @staticmethod
        def open(path): return _Im(cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR))
        @staticmethod
        def new(mode, size, color): return _Im(np.full((size[1], size[0], 3), 255, np.uint8))
sys.stdout.reconfigure(encoding="utf-8")
import stepfp

def main():
    if len(sys.argv) != 5: sys.exit(__doc__)
    name, step, shot, note = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4].strip()
    here = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(shot): sys.exit("❌ 화면 캡처 파일이 없다: " + shot)
    if time.time() - os.path.getmtime(shot) > 45 * 60: sys.exit("❌ 화면 캡처가 45분보다 오래됐다 — 지금 화면을 새로 찍어 쓴다")
    im = Image.open(shot).convert("RGB")
    if im.width < 500 or im.height < 350: sys.exit("❌ 화면 캡처가 너무 작다(%dx%d) — 조립 보기 화면 전체를 찍는다" % im.size)
    if len(note) < 30 or not any(ch.isdigit() for ch in note): sys.exit("❌ 비교 결과는 30자 이상이고 센 개수(숫자)가 들어가야 한다 — 무엇을 몇 개 세어 책과 맞았고 어디가 달랐는지 적는다")
    book = os.path.join(here, "refs", name, "%02d.jpg" % step)
    if not os.path.isfile(book): sys.exit("❌ 책 그림이 없다: " + book)
    asm = json.load(open(os.path.join(here, name + "_asm.json"), encoding="utf-8"))["steps"]
    if step < 1 or step > len(asm) or not (asm[step - 1].get("parts") or asm[step - 1].get("moveMade") or asm[step - 1].get("madeNoPart")): sys.exit("❌ 부품이 있거나 앞 번호 부품을 옮기는(합치는) 번호가 아니다(부품 없는 번호는 kw madeNoPart 로 표시 — 어보이더 28·30번)")
    fp = stepfp.fp(asm[step - 1])
    b = Image.open(book).convert("RGB"); h = 760
    a = b.resize((int(b.width * h / b.height), h)); c = im.resize((int(im.width * h / im.height), h))
    side = Image.new("RGB", (a.width + c.width + 6, h), "white"); side.paste(a, (0, 0)); side.paste(c, (a.width + 6, 0))
    out_dir = os.path.join(here, "refs", name, "cmp"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%02d.png" % step); side.save(out)
    ef = os.path.join(here, name + "_evidence.json")
    ev = json.load(open(ef, encoding="utf-8")) if os.path.exists(ef) else {}
    ev[str(step)] = {"fp": fp, "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "cmp": "refs/%s/cmp/%02d.png" % (name, step)}
    json.dump(ev, open(ef, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ %d번 비교 증거 기록: %s" % (step, out)); print("   지문", fp, "| 결과:", note)

if __name__ == "__main__": main()
