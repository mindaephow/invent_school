# 격자 fit 파일(fits/NN_<라벨>.json)에서 가려져 못 찾은 칸을, 찾은 점들로 구한 호모그래피로 연장해 채운다(관리자 지시: "가린 칸은 그대로 연장만 한다").
#   python fit_complete.py <이름> <번호> <라벨>
# 찾은 점은 그대로 두고, 빠진 (칸,줄)만 추가한다. 추가한 칸은 파일의 "est" 목록에 적는다(추정 — 보고에 쓴다).
import sys, os, json
import cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
name, step, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', name, 'fits', '%02d_%s.json' % (step, label))
d = json.load(open(p, encoding='utf-8'))
cols, rows = d['cols'], d['rows']
have = {(q[0], q[1]) for q in d['pts']}
src = np.array([[q[0], q[1]] for q in d['pts']], np.float32); dst = np.array([[q[2], q[3]] for q in d['pts']], np.float32)
H, _ = cv2.findHomography(src, dst, 0)
err = np.abs(cv2.perspectiveTransform(src[None], H)[0] - dst).max()
new = []
for c in range(1, cols + 1):
    for r in range(1, rows + 1):
        if (c, r) not in have:
            x, y = cv2.perspectiveTransform(np.array([[[c, r]]], np.float32), H)[0][0]
            new.append([c, r, round(float(x), 1), round(float(y), 1)])
d['pts'] += new
d['est'] = sorted(set(map(tuple, d.get('est', []))) | {(a, b) for a, b, _, _ in new})
d['est'] = [list(t) for t in d['est']]
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('찾은 점 %d, 연장한 점 %d(%s), 호모그래피 최대오차 %.1fpx' % (len(have), len(new), ' '.join('칸%d줄%d' % (a, b) for a, b, _, _ in new), err))
