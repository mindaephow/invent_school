# 교재 그림 한 장에서 "한 판의 모서리 4점(화면)↔(판 좌표)"로 평면 변환을 만들고, 같은 평면 위의 다른 화면 점(초록 원·다른 판 모서리)을 판 좌표(mm)로 바꾼다.
# 사용: H = homog(px4, world4); to_world(H, [(u,v),...]) -> [(x,z),...]   ; holes(x,z,pitch=10) 로 몇 번째 칸인지.
import numpy as np, cv2
def homog(px4, w4):
    return cv2.getPerspectiveTransform(np.float32(px4), np.float32(w4))
def to_world(H, pts):
    p = np.float32([pts]); q = cv2.perspectiveTransform(p, H)[0]
    return [(round(float(a), 1), round(float(b), 1)) for a, b in q]
