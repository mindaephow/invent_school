# 한 줄짜리 프레임(19프레임·115프레임 등)의 격자 fit 파일(fits/NN_<라벨>.json)을 만든다 — 첫 구멍과 끝 구멍 중심(원본 그림 좌표)만 읽고 사이는 같은 간격으로 채운다.
#   python fit_row.py <이름> <번호> <라벨> <구멍수> x1 y1 xN yN [설명]
# 모든 점은 연장(est)으로 기록한다(눈으로 읽은 두 끝점 + 같은 간격). refs_rect.py 가 이 줄이 수평이 되게 그림을 돌린다.
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
name, step, label, n = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
x1, y1, xn, yn = [float(v) for v in sys.argv[5:9]]
note = sys.argv[9] if len(sys.argv) > 9 else ''
pts = [[i + 1, 1, round(x1 + (xn - x1) * i / (n - 1), 1), round(y1 + (yn - y1) * i / (n - 1), 1)] for i in range(n)]
d = {'cols': n, 'rows': 1, 'pts': pts, 'name': note or '한 줄 프레임 — 첫·끝 구멍에서 읽은 점을 같은 간격으로 채움', 'est': [[p[0], 1] for p in pts]}
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', name, 'fits', '%02d_%s.json' % (step, label))
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('저장', p, n, '점')
