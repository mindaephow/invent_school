# PDF 한 개를 단계적으로 줄인다(닫을 때 나는 오류는 무시, 저장 결과로 판단). python -I -X utf8 scripts/compress-one.py <원본> <사본> [시작단계=0]
import pymupdf, os, sys, time
src, out = sys.argv[1], sys.argv[2]; start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
steps = [(150, 110, 70), (110, 80, 60), (90, 64, 50), (72, 50, 45), (60, 40, 40)]
for thr, tgt, q in steps[start:]:
    t = time.time(); d = pymupdf.open(src)
    try:
        d.rewrite_images(dpi_threshold=thr, dpi_target=tgt, quality=q); d.save(out, garbage=4, deflate=True, clean=True)
    except Exception as e: print('저장 오류', repr(e)[:120], flush=True)
    try: d.close()
    except Exception as e: print('닫기 오류(무시)', flush=True)
    mb = os.path.getsize(out) / 1048576 if os.path.exists(out) else 0
    print(f'dpi {tgt} q{q} ->', round(mb, 1), 'MB', round(time.time() - t), 's', flush=True)
    if 0 < mb <= 48:
        try:
            c = pymupdf.open(out); print('열기 확인', len(c), '쪽', flush=True)
            break
        except Exception as e: print('결과 열기 실패', repr(e)[:80], flush=True)
print('끝', flush=True)
