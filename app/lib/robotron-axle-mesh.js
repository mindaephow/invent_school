// 로버트론 제품(에이스랩·로보타미주니어) 십자 단면 축 생성기. 십자 단면 4×4(팔 폭 1.2, 사용자 2026-10-26), 양 끝은 1 구간에서 폭 2.6 으로 좁아진다. 머리 없이 양 끝이 같다.
// 좌표: 축 방향 y(바닥 0 ~ 길이 L), 단면은 x·z 의 가운데가 (0,0).
import { makeKit } from './cubo-mesh-kit.js'

export const AXLE_STD = { span: 4, arm: 1.2, tipSpan: 2.6, taper: 1 }

// 십자 단면(반시계, x·z 평면). 팔 끝 전체 폭 span, 팔 폭 arm.
const crossPts = (span, arm) => { const a = span / 2, w = arm / 2; return [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] }

export function axleTriangles(L, S = AXLE_STD) {
  const { quad, tri, P, result } = makeKit()
  const tip = crossPts(S.tipSpan, S.arm), full = crossPts(S.span, S.arm)
  const rings = [[0, tip], [S.taper, full], [L - S.taper, full], [L, tip]]
  const n = tip.length
  for (let r = 0; r < rings.length - 1; r++) {
    const [y0, p0] = rings[r], [y1, p1] = rings[r + 1]
    const ny = r === 0 ? -0.5 : r === 2 ? 0.5 : 0 // 끝이 좁아지는 구간은 면이 축 끝 쪽으로 기운다(감김 방향 판정용)
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n, dx = p0[j][0] - p0[i][0], dz = p0[j][1] - p0[i][1], l = Math.hypot(dx, dz)
      quad(P(p0[i][0], y0, p0[i][1]), P(p0[j][0], y0, p0[j][1]), P(p1[j][0], y1, p1[j][1]), P(p1[i][0], y1, p1[i][1]), dz / l, ny, -dx / l) // 반시계 단면의 바깥 법선 = (dz, -dx)
    }
  }
  for (let i = 0; i < n; i++) { // 양 끝 마개(별 모양이라 가운데에서 부채꼴로 이으면 된다)
    const j = (i + 1) % n
    tri(P(0, 0, 0), P(tip[i][0], 0, tip[i][1]), P(tip[j][0], 0, tip[j][1]), 0, -1, 0)
    tri(P(0, L, 0), P(tip[i][0], L, tip[i][1]), P(tip[j][0], L, tip[j][1]), 0, 1, 0)
  }
  return result()
}
