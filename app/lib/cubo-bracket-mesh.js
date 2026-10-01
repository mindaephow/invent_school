// 큐보 ㄴ자 브라켓(1열·2열)을 판 두 장(바닥 팔 + 세운 팔)으로 짠다. 판 규격은 프레임과 같다(cubo-plate-mesh.js).
// 좌표: 폭 x(가운데 0), 높이 y(바닥 0), 길이 z. 세운 팔은 z -15~-10 에 서고, 바닥 팔은 z -15~15 로 깔린다.
//  - 바닥 팔: 길이 30(3칸). 모서리 칸(z -15~-5)은 구멍 없음, 나머지 두 칸에 구멍(z 0, 10).
//  - 세운 팔: 높이 = 1열 30 / 2열 25. 바닥에서 올라가며 구멍이 10mm 간격, 맨 끝 구멍은 끝에서 5.
//  - 1열은 폭 10(구멍 한 줄), 2열은 폭 20(구멍 두 줄, x ±5).
// 두 판은 모서리에서 서로 겹쳐서 이어진다(겹친 속은 보이지 않는다).
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit } from './cubo-mesh-kit.js'
import { addPlate } from './cubo-plate-mesh.js'

export const CUBO_BRACKET_STD = {
  armLength: 30,    // 바닥 팔 길이
  heights: { 1: 30, 2: 25 }, // 세운 팔 높이(열 수별)
}

// rows = 열 수(1 또는 2). 폭 = 10 × rows.
export function bracketTriangles(rows, seg = 16) {
  const Hv = CUBO_BRACKET_STD.heights[rows]
  const W = S.width * rows, hw = W / 2
  const zCells = Array.from({ length: rows }, (_, j) => ({ lo: -hw + j * S.pitch, hi: -hw + (j + 1) * S.pitch, c: -hw + S.pitch / 2 + j * S.pitch }))
  // 판 하나를 (길이 u, 두께 v, 폭 t) 좌표로 만든다
  const plate = (cellsU) => {
    const k = makeKit(seg)
    addPlate(k, { xCells: cellsU, zCells })
    return k.result()
  }
  const kit = makeKit(seg)
  // 바닥 팔: 길이 방향 u = 월드 z (-15..15), 두께 v = y, 폭 t = x. (x,y,z)=(−t, v, u)
  const A = plate([{ lo: -15, hi: -5, c: null }, { lo: -5, hi: 5, c: 0 }, { lo: 5, hi: 15, c: 10 }])
  kit.append(A, ([u, v, t]) => [-t, v, u])
  // 세운 팔: 길이 방향 u = 월드 y (0..Hv), 두께 v = z (-15..-10), 폭 t = x. (x,y,z)=(t, u, v-15)
  const holes = [Hv - S.margin - S.pitch, Hv - S.margin] // 맨 끝 구멍은 끝에서 5, 그 아래 구멍은 10 더 아래
  const cellsB = [{ lo: 0, hi: holes[0] - S.pitch / 2, c: null }, ...holes.map((c) => ({ lo: c - S.pitch / 2, hi: c + S.pitch / 2, c }))]
  const B = plate(cellsB)
  kit.append(B, ([u, v, t]) => [t, u, v - 15])
  return kit.result()
}
