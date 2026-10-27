# 프로보 테크닉 1~6권 PDF 를 50MB 이하 사본으로 줄인다(7권 본문·표지는 이미 50MB 미만이라 그대로 올린다). 사본은 scratchpad/tq 에 저장.
#   python -I -X utf8 scripts/compress-techniq.py <사본폴더>
import pymupdf, os, sys, time, glob
D = r'C:\Users\user\Downloads\테크닉 교재_LV1-LV7'; OUT = sys.argv[1]
steps = [(150, 110, 70), (110, 80, 60), (90, 64, 50), (72, 50, 45), (60, 40, 40)]
for n in (5, 6, 2, 1, 3, 4):
    src = glob.glob(os.path.join(D, f'프로보 테크닉 {n}권_*.pdf'))[0]; out = os.path.join(OUT, f'techniq_{n}.pdf')
    for thr, tgt, q in steps:
        t = time.time()
        try:
            d = pymupdf.open(src); d.rewrite_images(dpi_threshold=thr, dpi_target=tgt, quality=q); d.save(out, garbage=4, deflate=True, clean=True); d.close()
        except Exception as e:
            print(n, '오류', repr(e)[:200], flush=True); break
        mb = os.path.getsize(out) / 1048576
        print(n, f'dpi {tgt} q{q} ->', round(mb, 1), 'MB', round(time.time() - t), 's', flush=True)
        if mb <= 48: break
print('끝', flush=True)
