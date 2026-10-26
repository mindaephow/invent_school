// 모터축(에이스랩, 그레이): 한쪽은 지름 8·길이 10 원기둥(끝에서 깊이 4 의 모터 육각 홈), 반대쪽은 4×4 십자 축 길이 29(사용자 2026-10-26: "29mm + 10mm(원기둥), 원기둥에 깊이 4mm 로 모터 육각형 깊이로 파줘").
// 원기둥 지름 8·육각 대변 6 은 휠가이드의 돌기(지름 8)와 가운데 육각 홈(대변 6, 깊이 4)을 따른 유추 값이다.
// 좌표: 축 y. 원기둥 y 0~10(육각 홈은 y=10 끝에서 아래로 4), 십자 축은 y=0 에서 −y 로 29.
import { makeKit } from './cubo-mesh-kit.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'
import { AXLE_STD } from './robotron-axle-mesh.js'

export const MOTORAXLE_STD = { cylR: 4, cylH: 10, hexFlat: 6, hexDepth: 4, axleLen: 29, seg: 48 }

const crossPts = (span, arm) => { const a = span / 2, w = arm / 2; return [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] }
const hexPts = (flat) => { const R = flat / Math.sqrt(3); return Array.from({ length: 6 }, (_, k) => [R * Math.cos((Math.PI / 3) * k), R * Math.sin((Math.PI / 3) * k)]) } // 반시계

export function motorAxleTriangles(S = MOTORAXLE_STD, A = AXLE_STD) {
  const kit = makeKit(S.seg), { quad, tri, P } = kit
  const hex = hexPts(S.hexFlat), full = crossPts(A.span, A.arm), tip = crossPts(A.tipSpan, A.arm), yHex = S.cylH - S.hexDepth
  kit.cyl(0, 0, S.cylR, 0, S.cylH, 1) // 원기둥 옆면
  const disc = circlePts(0, 0, S.cylR, S.seg)
  ringFace(kit, disc, [full], 0, -1) // 원기둥 아랫면(십자 축 자리 뚫림)
  ringFace(kit, disc, [hex], S.cylH, 1) // 윗면(육각 홈 자리 뚫림)
  hex.forEach((a, i) => { const b = hex[(i + 1) % 6], dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz); quad(P(a[0], yHex, a[1]), P(b[0], yHex, b[1]), P(b[0], S.cylH, b[1]), P(a[0], S.cylH, a[1]), -dz / l, 0, dx / l) }) // 육각 홈 벽
  hex.forEach((a, i) => { const b = hex[(i + 1) % 6]; tri(P(0, yHex, 0), P(a[0], yHex, a[1]), P(b[0], yHex, b[1]), 0, 1, 0) }) // 홈 바닥
  const rings = [[0, full], [-(S.axleLen - A.taper), full], [-S.axleLen, tip]] // 십자 축(아래로)
  for (let r = 0; r < rings.length - 1; r++) {
    const [ya, pa] = rings[r], [yb, pb] = rings[r + 1], ny = r === 1 ? -0.5 : 0
    for (let i = 0; i < pa.length; i++) { const j = (i + 1) % pa.length, dx = pa[j][0] - pa[i][0], dz = pa[j][1] - pa[i][1], l = Math.hypot(dx, dz); quad(P(pa[i][0], ya, pa[i][1]), P(pa[j][0], ya, pa[j][1]), P(pb[j][0], yb, pb[j][1]), P(pb[i][0], yb, pb[i][1]), dz / l, ny, -dx / l) }
  }
  tip.forEach((a, i) => { const b = tip[(i + 1) % tip.length]; tri(P(0, -S.axleLen, 0), P(a[0], -S.axleLen, a[1]), P(b[0], -S.axleLen, b[1]), 0, -1, 0) }) // 축 끝면
  return kit.result()
}
