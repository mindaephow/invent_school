// 로보타미주니어 프레임 생성기(로버트론 제품). 공통 틀은 robotron-frame-mesh.js, 규격 값은 여기서만 정한다.
// 큐보와 다른 점(사용자 2026-10-25): 구멍 둘레 테두리·입구 홈 없음(곧은 구멍), 대신 구멍 한 칸마다 가장자리 테두리와 같은 폭·높이(1mm)의 네모 테두리로 둘러 구멍 사이에 선이 생김, 구멍 지름 1mm 작음(큐보 목 지름 5.5 → 4.5), 두께·크기 같음, 팔 끝 모서리 더 둥글게(반지름 4.5, 폭 10 의 끝이 거의 반원).
import { createFrameGenerator } from './robotron-frame-mesh.js'

export const JUNIOR_FRAME_STD = { thickness: 5, rimHeight: 1, edgeWall: 1, boreR: 2.25, cornerR: 4.5, pitch: 10, width: 10, margin: 5, seg: 24, cornerSeg: 10 }
export const juniorFrame = createFrameGenerator(JUNIOR_FRAME_STD)

// 출력용(3D 프린터, 노즐 0.4 PLA): 구멍 목 지름을 프린터 오차만큼 넓히고(큐보 출력용이 5.5 → 6.10, +0.60 이었던 것과 같은 값 — 4.5 → 5.10) 구멍 목에 홈 8곳(폭 0.8·깊이 0.3, 큐보 출력용 "홈8"과 같은 값)을 판다. 나머지 모양은 위와 같다.
export const JUNIOR_PRINT_STD = { ...JUNIOR_FRAME_STD, boreR: 2.55, notch: 8, notchW: 0.8, notchD: 0.3 }
export const juniorPrintFrame = createFrameGenerator(JUNIOR_PRINT_STD)
