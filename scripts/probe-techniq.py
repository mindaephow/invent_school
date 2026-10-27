# 프로보 테크닉 교재 PDF 구조 살펴보기: 쪽 수, 차례, "부품" 쪽 후보
import pymupdf, re, glob, os
D = r'C:\Users\user\Downloads\테크닉 교재_LV1-LV7'
for f in sorted(glob.glob(os.path.join(D, '*.pdf'))):
    d = pymupdf.open(f); L = len(d)
    print('==', os.path.basename(f), 'pages', L, d[0].rect)
    hits = []
    for i in range(L):
        t = d[i].get_text()
        if re.search(r'필요한 부품|부품 리스트|부품리스트|부품수량|부품 수량|수량 확인|부품 목록|차\s*례|CONTENTS', t): hits.append((i + 1, t.replace('\n', ' | ')[:70]))
    for h in hits[:30]: print('  ', h)
