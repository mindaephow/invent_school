// 미니휠(에이스랩·로보타미주니어, 그레이): 지름 15·두께 5 실타래(실패) 모양 — 위아래 가장자리는 지름 15, 가운데 홈 부분(얇은 부분)은 지름 12 — 가운데는 규격 홀(프레임 구멍과 같은 지름 4.5)(사용자 2026-10-26 "가운데는 홀규격인데").
// 좌표: 축 y(0~5), 위아래 같은 모양, 가운데가 (0,0).
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const MINWHEEL_STD = { r: 7.5, grooveR: 6, h: 5, grooveW: 2, boreR: 2.25, seg: 64 }

export function minWheelTriangles(S = MINWHEEL_STD) {
  const kit = makeKit(S.seg)
  const bore = circlePts(0, 0, S.boreR, S.seg) // 규격 홀(지름 4.5)
  const y1 = (S.h - S.grooveW) / 2, y2 = y1 + S.grooveW
  kit.cyl(0, 0, S.r, 0, y1, 1); kit.cyl(0, 0, S.grooveR, y1, y2, 1); kit.cyl(0, 0, S.r, y2, S.h, 1) // 바깥 옆면(가운데 홈)
  kit.annulus(0, 0, S.grooveR, S.r, y1, 1); kit.annulus(0, 0, S.grooveR, S.r, y2, -1) // 홈 어깨
  const rim = circlePts(0, 0, S.r, S.seg)
  ringFace(kit, rim, [bore], 0, -1); ringFace(kit, rim, [bore], S.h, 1) // 위·아래 면(열십자 홀 뚫림)
  kit.cyl(0, 0, S.boreR, 0, S.h, -1) // 홀 벽(홀 속을 향함)
  return kit.result()
}
