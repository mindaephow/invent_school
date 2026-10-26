// 에이스랩 프레임 생성기(로버트론 제품). 공통 틀은 robotron-frame-mesh.js, 규격 값은 여기서만 정한다(로보타미주니어와 따로 고칠 수 있게 별도 파일).
// 지금은 로보타미주니어와 같은 값이다(사용자 2026-10-25: 큐보보다 홀 테두리 없음·구멍 지름 1mm 작음·두께 같음·끝 더 둥글게). 에이스랩 실측값이 다르면 여기만 고친다.
import { createFrameGenerator } from './robotron-frame-mesh.js'

export const ACELAB_FRAME_STD = { thickness: 5, rimHeight: 1, edgeWall: 1, boreR: 2.6, cornerR: 4.5, pitch: 10, width: 10, margin: 5, seg: 24, cornerSeg: 10, crossSpan: 5, crossArm: 1.4 }
export const acelabFrame = createFrameGenerator(ACELAB_FRAME_STD)

// 출력용(3D 프린터, 노즐 0.4 PLA): 구멍 목 지름을 프린터 오차만큼 넓히고(큐보 출력용이 5.5 → 6.10, +0.60 이었던 것과 같은 값 — 4.5 → 5.10) 구멍 목에 홈 8곳(폭 0.8·깊이 0.3, 큐보 출력용 "홈8"과 같은 값)을 판다. 나머지 모양은 위와 같다.
export const ACELAB_PRINT_STD = { ...ACELAB_FRAME_STD, boreR: 2.55, notch: 8, notchW: 0.8, notchD: 0.3 }
export const acelabPrintFrame = createFrameGenerator(ACELAB_PRINT_STD)
