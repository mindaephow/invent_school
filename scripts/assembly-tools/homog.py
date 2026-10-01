# 평면 호모그래피: 판의 네 모서리(그림 픽셀)로 그림 속 점(초록 원 등)을 판 위 좌표(mm)로 바꾼다.
import numpy as np, cv2
def plane(pix4, mm4):
    return cv2.getPerspectiveTransform(np.array(pix4, np.float32), np.array(mm4, np.float32))
def to_mm(H, pts):
    p = np.array(pts, np.float32).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(p, H).reshape(-1, 2)
def holes(mm, L, W):
    """mm: (u,v) 판 좌표(u=짧은 쪽 0..W, v=긴 쪽 0..L)를 구멍 번호(j,i)로. 구멍 중심은 5+10k."""
    return [(round((u - 5) / 10, 2), round((v - 5) / 10, 2)) for u, v in mm]
