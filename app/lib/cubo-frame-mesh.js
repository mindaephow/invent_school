// 큐보 직선 프레임을 자르기(CSG) 없이 삼각형으로 바로 짜는 생성기. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD 와 같다.
// 구멍·테두리를 자르는 계산으로 만들면 삼각형이 11배(2.2만 개) 늘어서, 팅커캐드 STL(약 2천 개)처럼 가볍게 직접 만든다.
// 길이 x(가운데 0), 두께 y(바닥 0~5), 폭 z(가운데 0). 좌표 단위 mm.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'
import { addPlate } from './cubo-plate-mesh.js'

export { trianglesToStl }

// 구멍 n개 직선 프레임의 삼각형 목록: Float32Array(삼각형 수 × 9). seg = 구멍 원 둘레 분할 수.
export function frameTriangles(n, seg = 20) {
  const kit = makeKit(seg)
  const hx = (n * S.pitch) / 2, hz = S.width / 2
  const xCells = Array.from({ length: n }, (_, i) => ({ lo: -hx + i * S.pitch, hi: -hx + (i + 1) * S.pitch, c: -hx + S.margin + i * S.pitch }))
  addPlate(kit, { xCells, zCells: [{ lo: -hz, hi: hz, c: 0 }] })
  return kit.result()
}
