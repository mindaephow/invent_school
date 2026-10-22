// 큐보 "판" 하나(프레임 한 장, 브라켓의 한쪽 팔)를 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD.
// 판은 두께 5(바닥 y=0 ~ 위 y=5): 가운데 판 3mm + 위·아래 면의 가장자리 테두리(폭1·높이1) + 구멍마다 솟은 고리(높이1).
// 길이 방향은 x, 폭 방향은 z. 칸(cell)은 길이×폭 방향으로 10mm 격자이고, 구멍은 칸의 가운데에 둔다.
//   xCells / zCells: [{ lo, hi, c }] — 칸의 시작·끝 좌표와 구멍 중심 c(구멍 없는 칸은 c=null). 판 바깥 크기는 첫·마지막 칸의 끝이다.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'


export function addPlate(kit, { xCells, zCells }) {
  const RO = S.rimOuterR - 0.01 // 구멍 테두리 바깥 반지름. 가장자리 테두리와 딱 닿으면(접선) 면 나누기가 깨져서 0.01 줄인다(눈에 안 보임). 호출 때마다 읽는다(프린트용 시험 조각이 규격 값을 바꿔 만들 수 있게)
  const { quad, P } = kit
  const X0 = xCells[0].lo, X1 = xCells[xCells.length - 1].hi
  const Z0 = zCells[0].lo, Z1 = zCells[zCells.length - 1].hi
  const E = S.edgeWall
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const ix0 = X0 + E, ix1 = X1 - E, iz0 = Z0 + E, iz1 = Z1 - E // 안쪽 사각(테두리 안)

  if (S.slab) { // 프린트용(선택): 테두리·고리 없이 통판 — 위·아래 면은 평평하고 구멍은 입구(rimInnerR, 깊이 rimHeight)에서 목(boreR)으로 좁아진다. 겹치는 몸체가 없어 슬라이서가 빼지 않고, 아래 면이 평평해 바닥이 뜨지 않는다.
    quad(P(X1, Y0, Z0), P(X1, Y0, Z1), P(X1, Y5, Z1), P(X1, Y5, Z0), 1, 0, 0)
    quad(P(X0, Y0, Z1), P(X0, Y0, Z0), P(X0, Y5, Z0), P(X0, Y5, Z1), -1, 0, 0)
    quad(P(X0, Y0, Z1), P(X1, Y0, Z1), P(X1, Y5, Z1), P(X0, Y5, Z1), 0, 0, 1)
    quad(P(X1, Y0, Z0), P(X0, Y0, Z0), P(X0, Y5, Z0), P(X1, Y5, Z0), 0, 0, -1)
    const outerPts = [[X0, Z0], [X1, Z0], [X1, Z1], [X0, Z1]], holes = []
    for (const xc of xCells) for (const zc of zCells) {
      if (xc.c == null || zc.c == null) continue
      const cx = xc.c, cz = zc.c, RE = S.rimInnerR
      holes.push(circlePts(cx, cz, RE, kit.seg))
      kit.cyl(cx, cz, RE, Y0, Y1, -1); kit.cyl(cx, cz, RE, Y4, Y5, -1)
      kit.annulus(cx, cz, S.boreR, RE, Y1, -1); kit.annulus(cx, cz, S.boreR, RE, Y4, 1)
      kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
    }
    ringFace(kit, outerPts, holes, Y0, -1); ringFace(kit, outerPts, holes, Y5, 1)
    return
  }
  // ① 바깥 옆면 4개 (바닥~위)
  quad(P(X1, Y0, Z0), P(X1, Y0, Z1), P(X1, Y5, Z1), P(X1, Y5, Z0), 1, 0, 0)
  quad(P(X0, Y0, Z1), P(X0, Y0, Z0), P(X0, Y5, Z0), P(X0, Y5, Z1), -1, 0, 0)
  quad(P(X0, Y0, Z1), P(X1, Y0, Z1), P(X1, Y5, Z1), P(X0, Y5, Z1), 0, 0, 1)
  quad(P(X1, Y0, Z0), P(X0, Y0, Z0), P(X0, Y5, Z0), P(X1, Y5, Z0), 0, 0, -1)
  // ② 가장자리 테두리 맨 바닥·맨 윗면(바깥 사각 − 안쪽 사각)과 안쪽 벽(위·아래 1mm씩)
  for (const [y, ny] of [[Y0, -1], [Y5, 1]]) {
    quad(P(X0, y, Z0), P(X1, y, Z0), P(ix1, y, iz0), P(ix0, y, iz0), 0, ny, 0)
    quad(P(X1, y, Z0), P(X1, y, Z1), P(ix1, y, iz1), P(ix1, y, iz0), 0, ny, 0)
    quad(P(X1, y, Z1), P(X0, y, Z1), P(ix0, y, iz1), P(ix1, y, iz1), 0, ny, 0)
    quad(P(X0, y, Z1), P(X0, y, Z0), P(ix0, y, iz0), P(ix0, y, iz1), 0, ny, 0)
  }
  for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) {
    quad(P(ix1, y0, iz0), P(ix1, y0, iz1), P(ix1, y1, iz1), P(ix1, y1, iz0), -1, 0, 0)
    quad(P(ix0, y0, iz1), P(ix0, y0, iz0), P(ix0, y1, iz0), P(ix0, y1, iz1), 1, 0, 0)
    quad(P(ix1, y0, iz1), P(ix0, y0, iz1), P(ix0, y1, iz1), P(ix1, y1, iz1), 0, 0, -1)
    quad(P(ix0, y0, iz0), P(ix1, y0, iz0), P(ix1, y1, iz0), P(ix0, y1, iz0), 0, 0, 1)
  }
  // ③ 칸마다: 구멍이 있으면 고리·벽·좁은 구멍·바닥면(원이 뚫린 칸), 없으면 평평한 바닥면
  for (const xc of xCells) {
    for (const zc of zCells) {
      const xlo = Math.max(xc.lo, ix0), xhi = Math.min(xc.hi, ix1), zlo = Math.max(zc.lo, iz0), zhi = Math.min(zc.hi, iz1)
      if (xc.c == null || zc.c == null) { // 구멍 없는 칸
        quad(P(xlo, Y1, zlo), P(xhi, Y1, zlo), P(xhi, Y1, zhi), P(xlo, Y1, zhi), 0, -1, 0)
        quad(P(xlo, Y4, zlo), P(xhi, Y4, zlo), P(xhi, Y4, zhi), P(xlo, Y4, zhi), 0, 1, 0)
        continue
      }
      const cx = xc.c, cz = zc.c
      kit.annulus(cx, cz, S.rimInnerR, RO, Y0, -1); kit.annulus(cx, cz, S.rimInnerR, RO, Y5, 1)
      kit.cyl(cx, cz, RO, Y0, Y1, 1); kit.cyl(cx, cz, RO, Y4, Y5, 1)
      kit.cyl(cx, cz, S.rimInnerR, Y0, Y1, -1); kit.cyl(cx, cz, S.rimInnerR, Y4, Y5, -1)
      kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y1, -1); kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y4, 1)
      if (S.ribR) { // 프린트용(선택): 구멍 목 가운데에 얇은 고리(립) — 목은 boreR 로 넓게 두고 가운데 ribH 두께만 ribR 로 좁혀 꽂은 돌기를 잡는다. S.ribR 가 없으면 그대로.
        const Ym = (Y1 + Y4) / 2, Ya = Ym - S.ribH / 2, Yb = Ym + S.ribH / 2
        kit.cyl(cx, cz, S.boreR, Y1, Ya, -1); kit.annulus(cx, cz, S.ribR, S.boreR, Ya, -1); kit.cyl(cx, cz, S.ribR, Ya, Yb, -1); kit.annulus(cx, cz, S.ribR, S.boreR, Yb, 1); kit.cyl(cx, cz, S.boreR, Yb, Y4, -1)
      } else kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
      kit.cell(cx, cz, RO, xlo, xhi, zlo, zhi, Y1, -1); kit.cell(cx, cz, RO, xlo, xhi, zlo, zhi, Y4, 1)
    }
  }
}
