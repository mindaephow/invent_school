// 휠가이드(DC모터에 결합, 에이스랩·로보타미주니어): 지름 30·두께 4 원판, 가운데 한쪽에 지름 8 돌기(전체 높이 10), 가운데에 지름 2 나사 구멍,
// 나사 구멍을 중심으로 열십자(좌·우·위·아래)로 피치 10 떨어진 프레임 구멍 4개, 그리고 이웃한 두 구멍의 가운데(대각선 ±5,±5)마다 같은 구멍 4개(사용자 2026-10-26).
// 원판 옆면(두께 4)은 1·2·1 로 나뉘어 가운데 2 구간이 깊이 grooveDepth 로 움푹 들어간 실타래(실패) 모양 홈이다(사용자 2026-10-26).
// 위·아래·좌·우 끝 구멍 4개(열십자 구멍)는 육각형(대변 endHexFlat)이고, 가운데에는 돌기 끝에서 깊이 centerHexDepth 의 육각 홈(대변 centerHexFlat)을 파 나사 구멍(지름 2)과 이어진다(사용자 2026-10-26).
// 구멍 9개는 간격 7.07 의 3×3 줄(모델 축에 대해 45°)로 늘어서 있다. 바닥쪽(돌기 반대면)은 프레임처럼 구멍 9개마다 깊이 1 의 사각 홈(사각 테두리)을 파는데, 사각형은 이 3×3 줄에 맞춰 45° 돌려서(모델 축 기준 마름모) 홈끼리 겹치지 않게 한다(사용자 2026-10-26).
// 좌표: 축 y, 원판 아랫면 y=0, 원판 윗면 y=4, 돌기 끝 y=10. 열십자 구멍은 ±x, ±z 방향.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export const WHEELGUIDE_STD = { discR: 15, discH: 4, bossR: 4, totalH: 10, screwR: 1, holeR: 2.25, pitch: 10, pocketSide: 6, pocketDepth: 1, grooveW: 2, grooveDepth: 1, endHexFlat: 4.5, centerHexFlat: 6, centerHexDepth: 4, seg: 64 }

// 구멍 자리: 열십자 4개(+x, −x, +z, −z) 다음에 이웃한 두 구멍의 가운데 4개(+x+z, +x−z, −x+z, −x−z).
export const wheelGuideSpots = (S = WHEELGUIDE_STD) => { const p = S.pitch, h = p / 2; return [[p, 0], [-p, 0], [0, p], [0, -p], [h, h], [h, -h], [-h, h], [-h, -h]] }

const hexPts = (cx, cz, flat, rot = 0) => { const R = flat / Math.sqrt(3); return Array.from({ length: 6 }, (_, k) => [cx + R * Math.cos((Math.PI / 3) * k + rot), cz + R * Math.sin((Math.PI / 3) * k + rot)]) } // 반시계, 기본은 꼭짓점이 x 방향(rot 라디안만큼 돌림)
const endHex = (x, z, S) => hexPts(x, z, S.endHexFlat, x !== 0 ? Math.PI / 2 : 0) // 좌·우(±x) 끝 구멍의 육각은 위·아래(±z)보다 90° 돌려 꼭짓점이 z 방향(사용자 2026-10-26)
const diamondPts = (cx, cz, side) => { const d = side / Math.SQRT2; return [[cx + d, cz], [cx, cz + d], [cx - d, cz], [cx, cz - d]] } // 한 변 side 인 정사각형을 45° 돌린 모양(반시계)

export function wheelGuideTriangles(S = WHEELGUIDE_STD) {
  const kit = makeKit(S.seg)
  const spots = wheelGuideSpots(S), cross = spots.slice(0, 4), diag = spots.slice(4)
  const pockets = [[0, 0], ...cross, ...diag] // 사각 홈이 있는 자리(가운데 나사 구멍 + 나머지 8개)
  const disc = circlePts(0, 0, S.discR, S.seg), boss = circlePts(0, 0, S.bossR, S.seg), screw = circlePts(0, 0, S.screwR, S.seg)
  const D = S.pocketDepth, yHex = S.totalH - S.centerHexDepth
  const wall = (poly, y0, y1) => poly.forEach((A, i) => { // 구멍·홈 옆벽(다각형 속을 향함)
    const B = poly[(i + 1) % poly.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz)
    kit.quad([A[0], y0, A[1]], [B[0], y0, B[1]], [B[0], y1, B[1]], [A[0], y1, A[1]], -dz / l, 0, dx / l)
  })
  const hole = (x, z, r) => (cross.some(([cx, cz]) => cx === x && cz === z) ? endHex(x, z, S) : circlePts(x, z, r, S.seg)) // 끝 구멍 4개는 육각
  const centerHex = hexPts(0, 0, S.centerHexFlat)
  const g0 = (S.discH - S.grooveW) / 2, g1 = g0 + S.grooveW, rg = S.discR - S.grooveDepth
  kit.cyl(0, 0, S.discR, 0, g0, 1); kit.cyl(0, 0, rg, g0, g1, 1); kit.cyl(0, 0, S.discR, g1, S.discH, 1) // 원판 옆면(가운데 실타래 홈)
  kit.annulus(0, 0, rg, S.discR, g0, 1); kit.annulus(0, 0, rg, S.discR, g1, -1) // 홈 위·아래 어깨
  kit.cyl(0, 0, S.bossR, S.discH, S.totalH, 1) // 돌기 옆면
  kit.cyl(0, 0, S.screwR, D, yHex, -1) // 나사 구멍 벽(사각 홈 바닥에서 육각 홈 바닥까지)
  wall(centerHex, yHex, S.totalH) // 가운데 육각 홈 벽(돌기 끝에서 아래로)
  cross.forEach(([x, z]) => wall(endHex(x, z, S), D, S.discH)) // 끝 구멍(육각) 벽
  diag.forEach(([x, z]) => kit.cyl(x, z, S.holeR, D, S.discH, -1)) // 가운데 구멍 벽(둥근)
  const sqs = pockets.map(([x, z]) => diamondPts(x, z, S.pocketSide))
  sqs.forEach((sq) => wall(sq, 0, D)) // 사각 홈 옆벽
  ringFace(kit, disc, sqs, 0, -1) // 바닥(홈 자리 뚫림)
  pockets.forEach(([x, z], i) => ringFace(kit, sqs[i], [hole(x, z, i === 0 ? S.screwR : S.holeR)], D, -1)) // 홈 바닥(구멍 뚫림)
  ringFace(kit, disc, [boss, ...spots.map(([x, z]) => hole(x, z, S.holeR))], S.discH, 1) // 원판 윗면(돌기 자리·구멍 뚫림)
  ringFace(kit, boss, [centerHex], S.totalH, 1) // 돌기 끝면(육각 홈 자리 뚫림)
  ringFace(kit, centerHex, [screw], yHex, 1) // 육각 홈 바닥(나사 구멍 뚫림)
  return kit.result()
}
