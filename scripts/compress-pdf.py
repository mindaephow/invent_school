# 큰 교재 PDF 의 그림 해상도를 줄여 50MB 이하로 만든다(원본은 그대로 두고 사본을 저장). 한 번에 못 줄이면 단계적으로 더 줄인다.
#   python -I -X utf8 scripts/compress-pdf.py <원본.pdf> <사본.pdf> [목표MB=48]
import pymupdf, os, sys, time
src, out = sys.argv[1], sys.argv[2]; target = float(sys.argv[3]) if len(sys.argv) > 3 else 48
steps = [(150, 110, 70), (110, 80, 60), (90, 64, 50), (72, 50, 45), (60, 40, 40)]
for thr, tgt, q in steps:
    t = time.time(); d = pymupdf.open(src)
    d.rewrite_images(dpi_threshold=thr, dpi_target=tgt, quality=q)
    d.save(out, garbage=4, deflate=True, clean=True); d.close()
    mb = os.path.getsize(out) / 1048576
    print(os.path.basename(src), f'dpi {tgt} q{q} ->', round(mb, 1), 'MB', round(time.time() - t), 's', flush=True)
    if mb <= target: break
