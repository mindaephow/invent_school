// 로버트론 제품(에이스랩·로보타미주니어) 부시 생성기. 큐보 부시와 달리 지름 8 원통(두께 5)이고 가운데만 지름 7 로 움푹 들어간 실패(스풀) 모양(사용자 2026-10-26).
// 가운데 구멍은 로버트론 십자 축(4×4)이 지나가는 열십자 구멍. 좌표: 축 방향 y(0~5), 위아래가 같다.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const BUSH_STD = { r: 4, grooveR: 3.5, grooveW: 1.5, height: 5, boreSpan: 4.4, boreArm: 1.4, seg: 48 }

export function bushTriangles(S = BUSH_STD) {
  const kit = makeKit(S.seg), { quad } = kit
  const a = S.boreSpan / 2, w = S.boreArm / 2
  const bore = [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] // 열십자 구멍(반시계)
  const y1 = (S.height - S.grooveW) / 2, y2 = y1 + S.grooveW // 홈 아래·위 높이
  const rim = circlePts(0, 0, S.r, S.seg)
  kit.cyl(0, 0, S.r, 0, y1, 1); kit.cyl(0, 0, S.grooveR, y1, y2, 1); kit.cyl(0, 0, S.r, y2, S.height, 1) // 바깥 옆면
  ringFace(kit, rim, [bore], 0, -1); ringFace(kit, rim, [bore], S.height, 1) // 바닥·윗면
  kit.annulus(0, 0, S.grooveR, S.r, y1, 1) // 홈 아래 어깨(위를 향함)
  kit.annulus(0, 0, S.grooveR, S.r, y2, -1) // 홈 위 어깨(아래를 향함)
  for (let i = 0; i < bore.length; i++) { // 구멍 안쪽 벽(구멍 속을 향함)
    const A = bore[i], B = bore[(i + 1) % bore.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz)
    quad([A[0], 0, A[1]], [B[0], 0, B[1]], [B[0], S.height, B[1]], [A[0], S.height, A[1]], -dz / l, 0, dx / l)
  }
  return kit.result()
}
