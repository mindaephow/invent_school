import pymupdf, sys, os
for p in sys.argv[1:]:
    try:
        d = pymupdf.open(p); n = len(d); d[0].get_pixmap(dpi=30); d[n - 1].get_pixmap(dpi=30)
        print(os.path.basename(p), round(os.path.getsize(p) / 1048576, 1), 'MB', n, 'pages OK')
    except Exception as e: print(os.path.basename(p), '열기 실패', repr(e)[:100])
