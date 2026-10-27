import pymupdf, os, sys
D = r'C:\Users\user\Downloads\테크닉 교재_LV1-LV7'
want = {1: [3, 4, 10, 11], 2: [2, 3, 6, 7], 3: [2, 6, 7], 4: [2, 6, 7], 5: [2, 6, 7], 6: [2, 6, 7], 7: [4, 5]}
names = {1: '프로보 테크닉 1권_1판7쇄_워터마크_210209.pdf', 2: '프로보 테크닉 2권_1판6쇄_워터마크_210209.pdf', 3: '프로보 테크닉 3권_1판3쇄_워터마크_210209.pdf', 4: '프로보 테크닉 4권_1판2쇄_워터마크_200429.pdf', 5: '프로보 테크닉 5권_1판2쇄_워터마크_210210.pdf', 6: '프로보 테크닉 6권_1판1쇄_워터마크_210210.pdf', 7: '프로보 테크닉 7권_1판1쇄_워터마크_210210.pdf'}
for v in [int(a) for a in sys.argv[1:]]:
    d = pymupdf.open(os.path.join(D, names[v]))
    for p in want[v]:
        print('=== LV', v, 'p', p); print(d[p - 1].get_text().replace('\n', ' | ')[:1100])
