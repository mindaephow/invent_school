// 큐보 직선 프레임을 자르기(CSG) 없이 삼각형으로 바로 짜는 생성기. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD 와 같다.
// 구멍·테두리를 자르는 계산으로 만들면 삼각형이 11배(2.2만 개) 늘어서, 팅커캐드 STL(약 2천 개)처럼 가볍게 직접 만든다.
// 길이 x(가운데 0), 두께 y(바닥 0~5), 폭 z(가운데 0). 좌표 단위 mm.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'

export { trianglesToStl }

const RO = S.rimOuterR - 0.01 // 구멍 테두리 바깥 반지름. 가장자리 테두리와 딱 닿으면(접선) 면 나누기가 깨져서 0.01 줄인다(눈에 안 보임)

// 구멍 n개 직선 프레임의 삼각형 목록: Float32Array(삼각형 수 × 9). seg = 구멍 원 둘레 분할 수.
export function frameTriangles(n, seg = 20) {
  const kit = makeKit(seg)
  const { quad, P } = kit
  const L = n * S.pitch, hx = L / 2, hz = S.width / 2, E = S.edgeWall
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const cxs = Array.from({ length: n }, (_, i) => -hx + S.margin + i * S.pitch)
  const cyl = (cx, r, y0, y1, dir) => kit.cyl(cx, 0, r, y0, y1, dir)
  const annulus = (cx, r0, r1, y, ny) => kit.annulus(cx, 0, r0, r1, y, ny)
  const cell = (cx, xlo, xhi, y, ny) => kit.cell(cx, 0, RO, xlo, xhi, -(hz - E), hz - E, y, ny)

  // ① 바깥 옆면 4개 (바닥~위)
  quad(P(hx, Y0, -hz), P(hx, Y0, hz), P(hx, Y5, hz), P(hx, Y5, -hz), 1, 0, 0)
  quad(P(-hx, Y0, hz), P(-hx, Y0, -hz), P(-hx, Y5, -hz), P(-hx, Y5, hz), -1, 0, 0)
  quad(P(-hx, Y0, hz), P(hx, Y0, hz), P(hx, Y5, hz), P(-hx, Y5, hz), 0, 0, 1)
  quad(P(hx, Y0, -hz), P(-hx, Y0, -hz), P(-hx, Y5, -hz), P(hx, Y5, -hz), 0, 0, -1)
  // ② 가장자리 테두리 맨 바닥·맨 윗면(바깥 사각 − 안쪽 사각)과 안쪽 벽(위·아래 1mm씩)
  const ix = hx - E, iz = hz - E
  for (const [y, ny] of [[Y0, -1], [Y5, 1]]) {
    quad(P(-hx, y, -hz), P(hx, y, -hz), P(ix, y, -iz), P(-ix, y, -iz), 0, ny, 0)
    quad(P(hx, y, -hz), P(hx, y, hz), P(ix, y, iz), P(ix, y, -iz), 0, ny, 0)
    quad(P(hx, y, hz), P(-hx, y, hz), P(-ix, y, iz), P(ix, y, iz), 0, ny, 0)
    quad(P(-hx, y, hz), P(-hx, y, -hz), P(-ix, y, -iz), P(-ix, y, iz), 0, ny, 0)
  }
  for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) {
    quad(P(ix, y0, -iz), P(ix, y0, iz), P(ix, y1, iz), P(ix, y1, -iz), -1, 0, 0)
    quad(P(-ix, y0, iz), P(-ix, y0, -iz), P(-ix, y1, -iz), P(-ix, y1, iz), 1, 0, 0)
    quad(P(ix, y0, iz), P(-ix, y0, iz), P(-ix, y1, iz), P(ix, y1, iz), 0, 0, -1)
    quad(P(-ix, y0, -iz), P(ix, y0, -iz), P(ix, y1, -iz), P(-ix, y1, -iz), 0, 0, 1)
  }
  // ③ 구멍마다: 테두리 고리(맨 바닥·맨 윗면), 테두리 바깥·안쪽 벽, 바닥면의 안쪽 고리, 가장 좁은 구멍 벽
  cxs.forEach((cx, i) => {
    annulus(cx, S.rimInnerR, RO, Y0, -1); annulus(cx, S.rimInnerR, RO, Y5, 1)
    cyl(cx, RO, Y0, Y1, 1); cyl(cx, RO, Y4, Y5, 1)
    cyl(cx, S.rimInnerR, Y0, Y1, -1); cyl(cx, S.rimInnerR, Y4, Y5, -1)
    annulus(cx, S.boreR, S.rimInnerR, Y1, -1); annulus(cx, S.boreR, S.rimInnerR, Y4, 1)
    cyl(cx, S.boreR, Y1, Y4, -1)
    const xlo = i === 0 ? -ix : cx - S.pitch / 2, xhi = i === n - 1 ? ix : cx + S.pitch / 2
    cell(cx, xlo, xhi, Y1, -1); cell(cx, xlo, xhi, Y4, 1)
  })
  return kit.result()
}
