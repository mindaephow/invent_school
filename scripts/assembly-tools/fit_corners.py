# 모서리 4곳(칸1줄1, 칸N줄1, 칸N줄M, 칸1줄M — 원본 그림 좌표)만으로 격자 fit 파일(fits/NN_<라벨>.json)을 만든다.
# 구멍이 안 비쳐 blobfit 이 못 잡는 판(아래 판이 비쳐 회색인 구멍, 리벳·블록이 가린 판)에 쓴다. 점은 모두 연장(est)으로 기록한다.
#   python fit_corners.py <이름> <번호> <라벨> <칸> <줄> c1r1x c1r1y cNr1x cNr1y cNrMx cNrMy c1rMx c1rMy [설명]
import sys, os, json
import cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
name, step, label, cols, rows = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
cr = [float(v) for v in sys.argv[6:14]]
note = sys.argv[14] if len(sys.argv) > 14 else ''
src = np.array([[1, 1], [cols, 1], [cols, rows], [1, rows]], np.float32); dst = np.array(cr, np.float32).reshape(4, 2)
H = cv2.getPerspectiveTransform(src, dst)
pts = []
for c in range(1, cols + 1):
    for r in range(1, rows + 1):
        x, y = cv2.perspectiveTransform(np.array([[[c, r]]], np.float32), H)[0][0]
        pts.append([c, r, round(float(x), 1), round(float(y), 1)])
d = {'cols': cols, 'rows': rows, 'pts': pts, 'name': note or '모서리 4곳으로 만든 격자(전부 연장)', 'corners': dst.tolist(), 'est': [[p[0], p[1]] for p in pts]}
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', name, 'fits', '%02d_%s.json' % (step, label))
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
print('저장', p, len(pts), '점')
