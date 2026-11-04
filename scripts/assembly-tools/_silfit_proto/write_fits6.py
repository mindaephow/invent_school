import sys, json, math, shutil
sys.argv = ['x']; sys.path.insert(0, '_silfit_proto'); sys.path.insert(0, '.')
import numpy as np, cv2
import silfit6 as S
from pnp import cam_from, angles
sys.stdout.reconfigure(encoding='utf-8')
D = 'refs/steercar/'
x = list(np.load(S.SP + 'sil6_x.npy')); iou = 1 - S.loss(x); rv, tv, fov = S.parts(x); K = S.K_(fov)
cells = [(c, r) for c in range(1, 16) for r in range(1, 6)]
W = np.array([[(c - 8) * 10.0, 5.0, (r - 3) * 10.0] for c, r in cells])
pr = cv2.projectPoints(W, rv, tv, K, None)[0].reshape(-1, 2)
ms = S.hull_mask(S.SERVO, rv, tv, K, 9)
vis = [[c, r] for (c, r), p in zip(cells, pr) if 0 <= p[0] < S.Ww and 0 <= p[1] < S.Hh and not ms[int(p[1]), int(p[0])]]
C_, fwd, up, right = cam_from(rv, tv); az, el, rad = angles(C_, np.array([0.0, 2.5, 0.0])); th, ph = math.radians(az), math.radians(90 - el)
roll = math.degrees(math.asin(max(-1, min(1, float(right[1])))))
print('IoU %.3f fov %.1f theta %.2f phi %.2f roll %.1f' % (iou, fov, th, ph, roll), '보이는 칸', len(vis))
ev = {'sources': ['책 6번 그림 판(515프레임) 어두운 실루엣 ↔ 모델 판 실루엣 겹침 최대화(자동, 서보·흰 프레임·위 조립·초록 표시는 비교에서 제외, 눈으로 점을 읽지 않음)'], 'iou': round(iou, 3), 'fov': round(fov, 2), 'theta': round(th, 3), 'phi': round(ph, 3), 'roll_deg': round(roll, 1)}
pts = [[c, r, round(float(p[0]), 2), round(float(p[1]), 2)] for (c, r), p in zip(cells, pr)]
pf = {'rows': 5, 'cols': 15, 'tool': 'sil-fit', 'err_px': round(1 - iou, 3), 'max_err_px': None, 'est': [], 'evidence': ev, 'pts': pts,
      'name': 'steercar 6번 P: 515프레임 15칸×5줄 — 판 실루엣 겹침 카메라(IoU %.3f)로 투영 — silfit' % iou, 'origin_cell': [8, 3], 'visible_cells': vis}
json.dump(pf, open(D + 'fits/06_P.json', 'w', encoding='utf-8'), ensure_ascii=False)
P = lambda q: cv2.projectPoints(np.array(q, np.float64).reshape(-1, 3), rv, tv, K, None)[0].reshape(-1, 2)
o = np.array([0.0, 2.5, 0.0]); ax = {}
for k, d in (('X', (1, 0, 0)), ('Y', (0, 1, 0)), ('Z', (0, 0, 1))):
    v = P(o + 20 * np.array(d))[0] - P(o)[0]; v = v / np.linalg.norm(v) * 55; ax[k] = [round(float(v[0]), 1), round(float(v[1]), 1)]
json.dump({'global': ax, 'fit': {'from': '06_P.json', 'err_px': round(1 - iou, 3), 'points': 0, 'theta': round(th, 2), 'phi': round(ph, 2), 'method': '실루엣 겹침 IoU %.3f' % iou, 'origin_world': [11, 2.5, 0]}, 'no_rotate': True}, open(D + '06_axes.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
shutil.copy(D + '03_lv.json', D + '06_lv.json'); print('축', ax)
