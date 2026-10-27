# 프로보 커넥트 교재 PDF 에서 차시(챕터) 첫 쪽의 "필요한 부품을 준비해볼까?" 부품 목록을 뽑는다(텍스트). 결과는 JSON 으로 저장.
#   python -I -X utf8 scripts/extract-proboconnect-chapters.py <출력.json>
import pymupdf, re, json, sys
D = r'C:\Users\user\Downloads\프로보커넥트'
SRC = {1: D + r'\프로보커넥트_LV1\프로보커넥트_LV1.pdf', 2: D + r'\프로보커넥트_LV2\프로보커넥트_LV2.pdf', 3: D + r'\프로보커넥트_LV3\프로보커넥트_LV3.pdf', 4: D + r'\프로보커넥트_LV4\프로보커넥트_LV4.pdf'}
out = {}
for vol, path in SRC.items():
    d = pymupdf.open(path); chs = []
    for i in range(len(d)):
        t = d[i].get_text(); m = re.search(r'(?m)^(\d\d)\s*$', t)
        # 챕터 첫 쪽: 부품 준비 문구가 있는 쪽(LV1 은 번호가 쪽 번호와 섞여 아래에서 따로 처리)
        if '필요한 부품을 준비해볼까?' in t: chs.append((i + 1, t))
    out[vol] = [{'page': p, 'text': t} for p, t in chs]
    print(vol, len(chs), [p for p, _ in chs])
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False)
