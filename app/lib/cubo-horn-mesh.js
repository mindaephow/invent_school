// 큐보 서보혼(막대형)과 둥근서보혼을 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD(판 3·테두리 1·구멍 구조·간격 10).
// 구멍 종류:
//  - through : 프레임 구멍 그대로(입구 반지름 3.5 깊이 1 → 가장 좁은 곳 2.75)
//  - pilot   : 가장 좁은 곳만 반지름 1.1 인 작은 구멍(교재 3쪽 서보혼 3·4번째 구멍)
//  - hex     : 육각큰기어 가운데 구멍 구조(등록된 육각큰기어 3D 를 직접 쟀다): 아래 면에 꼭짓점 반지름 2.5 정육각형 구멍(깊이 3),
//              그 위로 반지름 2.75 구멍(1mm), 맨 위 입구 반지름 3.5(깊이 1). 판 두께 5 에 맞춰 같은 순서로 쌓았다.
// 좌표: x·z 가운데가 0, 높이 y 는 바닥 0~5(프레임과 같은 방향).
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'

export { trianglesToStl }

export const HORN_STD = { pilotR: 1.1, hexR: 2.5, hexDepth: 3, hexAngle: 30 } // 육각 꼭짓점 반지름·깊이·첫 꼭짓점 각도(도)

const RO = S.rimOuterR - 0.01
const E = S.edgeWall
const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total

function hexPts(cx, cz) {
  return Array.from({ length: 6 }, (_, k) => {
    const a = ((HORN_STD.hexAngle + 60 * k) * Math.PI) / 180
    return [cx + HORN_STD.hexR * Math.cos(a), cz + HORN_STD.hexR * Math.sin(a)]
  })
}

// 구멍 하나(테두리 고리·벽·좁은 구멍). 판 바깥 윤곽과 안쪽 면은 buildPlate 가 그린다.
function addHole(kit, cx, cz, type) {
  const { quad, P, seg } = kit
  kit.annulus(cx, cz, S.rimInnerR, RO, Y5, 1)
  kit.cyl(cx, cz, RO, Y4, Y5, 1); kit.cyl(cx, cz, RO, Y0, Y1, 1)
  kit.cyl(cx, cz, S.rimInnerR, Y4, Y5, -1)
  if (type === 'hex') {
    const neck = S.boreR, hex = hexPts(cx, cz), Y3 = Y0 + HORN_STD.hexDepth
    ringFace(kit, circlePts(cx, cz, RO, seg), [hex], Y0, -1) // 아래 면: 정육각형 구멍 둘레
    for (let k = 0; k < 6; k++) { // 육각 구멍 벽(구멍 안쪽을 향함)
      const a = hex[k], b = hex[(k + 1) % 6]
      const nx = cx - (a[0] + b[0]) / 2, nz = cz - (a[1] + b[1]) / 2
      quad(P(a[0], Y0, a[1]), P(b[0], Y0, b[1]), P(b[0], Y3, b[1]), P(a[0], Y3, a[1]), nx, 0, nz)
    }
    ringFace(kit, circlePts(cx, cz, neck, seg), [hex], Y3, 1) // 육각 구멍 위 단(반지름 2.75 구멍 바닥)
    kit.cyl(cx, cz, neck, Y3, Y4, -1)
    kit.annulus(cx, cz, neck, S.rimInnerR, Y4, 1)
    return
  }
  const neck = type === 'pilot' ? HORN_STD.pilotR : S.boreR
  kit.annulus(cx, cz, S.rimInnerR, RO, Y0, -1)
  kit.cyl(cx, cz, S.rimInnerR, Y0, Y1, -1)
  kit.annulus(cx, cz, neck, S.rimInnerR, Y1, -1)
  kit.annulus(cx, cz, neck, S.rimInnerR, Y4, 1)
  kit.cyl(cx, cz, neck, Y1, Y4, -1)
}

// 반시계 윤곽 O(바깥)·I(테두리 안쪽, 같은 점 수)로 판을 짠다: 바깥 옆벽, 위·아래 테두리 면, 테두리 안쪽 벽, 구멍 둘레 면.
function buildPlate(kit, O, I, holes) {
  const { quad, P, seg } = kit
  const m = O.length
  for (let i = 0; i < m; i++) {
    const j = (i + 1) % m
    const dx = O[j][0] - O[i][0], dz = O[j][1] - O[i][1], l = Math.hypot(dx, dz)
    const px = dz / l, pz = -dx / l // 바깥쪽 법선
    quad(P(O[i][0], Y0, O[i][1]), P(O[j][0], Y0, O[j][1]), P(O[j][0], Y5, O[j][1]), P(O[i][0], Y5, O[i][1]), px, 0, pz)
    for (const [y, ny] of [[Y0, -1], [Y5, 1]]) quad(P(O[i][0], y, O[i][1]), P(O[j][0], y, O[j][1]), P(I[j][0], y, I[j][1]), P(I[i][0], y, I[i][1]), 0, ny, 0)
    for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) quad(P(I[i][0], y0, I[i][1]), P(I[j][0], y0, I[j][1]), P(I[j][0], y1, I[j][1]), P(I[i][0], y1, I[i][1]), -px, 0, -pz)
  }
  const rims = holes.map((h) => circlePts(h.cx, h.cz, RO, seg))
  ringFace(kit, I, rims, Y1, -1); ringFace(kit, I, rims, Y4, 1)
  for (const h of holes) addHole(kit, h.cx, h.cz, h.type)
}

// 서보혼(막대형): 15프레임과 같은 크기(50×10), 구멍 5개. 한쪽 끝부터 보통 구멍 2개 · 작은 구멍 2개 · 육각 구멍 1개(교재 3권 3쪽).
export function servoHornTriangles(seg = 20) {
  const kit = makeKit(seg)
  const hx = (5 * S.pitch) / 2, hz = S.width / 2
  const rect = (a, b) => [[-a, -b], [a, -b], [a, b], [-a, b]]
  const types = ['through', 'through', 'pilot', 'pilot', 'hex']
  buildPlate(kit, rect(hx, hz), rect(hx - E, hz - E), types.map((type, i) => ({ cx: -hx + S.margin + i * S.pitch, cz: 0, type })))
  return kit.result()
}

// 둥근서보혼: 지름 30 원판(구멍 중심에서 가장자리까지 5), 가운데 육각 구멍 + 둘레 보통 구멍 4개(가운데에서 10mm, 육각큰기어와 같은 배치).
export function roundHornTriangles(seg = 20, n = 96) {
  const kit = makeKit(seg)
  const R = 15
  const O = circlePts(0, 0, R, n), I = circlePts(0, 0, R - E, n)
  const holes = [{ cx: 0, cz: 0, type: 'hex' }, ...[[10, 0], [0, 10], [-10, 0], [0, -10]].map(([cx, cz]) => ({ cx, cz, type: 'through' }))]
  buildPlate(kit, O, I, holes)
  return kit.result()
}
