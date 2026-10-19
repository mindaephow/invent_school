# 판 바깥 윤곽 모서리 4곳(TL·TR·BR·BL, holefit 와 같은 순서)의 호모그래피로 구멍 자리를 환산해 fits/NN_P.json 에 쓴다 — holefit(DoG)가 미달(2.0px 초과)인 번호용 대체(⚠ 환산값, fits name·tool 에 기록).
#   python _corner_fit.py <이름> <번호> <칸> <줄> x1 y1 x2 y2 x3 y3 x4 y4
import json, sys, numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
name, N, cols, rows = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); C = np.float32([float(v) for v in sys.argv[5:13]]).reshape(4, 2)
H0 = cv2.getPerspectiveTransform(np.float32([[0, 0], [cols, 0], [cols, rows], [0, rows]]), C)
px = lambda c, r: cv2.perspectiveTransform(np.float32([[[c - 0.5, r - 0.5]]]), H0)[0][0]
pts = [[c, r, round(float(px(c, r)[0]), 1), round(float(px(c, r)[1]), 1)] for r in range(1, rows + 1) for c in range(1, cols + 1)]
f = {"name": "%d번 — 판 바깥 윤곽 모서리 4곳(원본 그림 ±3px)의 호모그래피로 환산한 격자(holefit 가 미달이라 구멍 중심 검출값이 아님, ⚠)" % N, "cols": cols, "rows": rows, "pts": pts, "est": [], "tool": "corner-homography", "fov": 36}
json.dump(f, open("refs/%s/fits/%02d_P.json" % (name, N), "w", encoding="utf-8"), ensure_ascii=False); print("썼다", len(pts), "점")
