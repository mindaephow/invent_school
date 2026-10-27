import pymupdf, sys, os
for p in sys.argv[1:]:
    d = pymupdf.open(p); bad = 0
    for i in range(len(d)):
        try: d[i].get_pixmap(dpi=20)
        except Exception as e: bad += 1; print(os.path.basename(p), '쪽', i + 1, '렌더 실패', repr(e)[:60])
    print(os.path.basename(p), len(d), '쪽 중 렌더 실패', bad)
