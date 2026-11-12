// 큐보 "판" 하나(프레임 한 장, 브라켓의 한쪽 팔)를 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD.
// 판은 두께 5(바닥 y=0 ~ 위 y=5): 가운데 판 3mm + 위·아래 면의 가장자리 테두리(폭1·높이1) + 구멍마다 솟은 고리(높이1).
// 길이 방향은 x, 폭 방향은 z. 칸(cell)은 길이×폭 방향으로 10mm 격자이고, 구멍은 칸의 가운데에 둔다.
//   xCells / zCells: [{ lo, hi, c }] — 칸의 시작·끝 좌표와 구멍 중심 c(구멍 없는 칸은 c=null). 판 바깥 크기는 첫·마지막 칸의 끝이다.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { ringFace, circlePts } from './cubo-face-mesh.js'


// 글자 새기기(사용자 지시 2026-11-13, 2열브라켓 긴 쪽 "LONG"): 점 글자를 판 윗면(구멍 없는 칸)에 얕게 판다. 크기·구멍 위치는 그대로(깊이 < 판 두께 3).
const GLYPH = { L: ['1000', '1000', '1000', '1000', '1111'], O: ['1111', '1001', '1001', '1001', '1111'], N: ['1001', '1101', '1111', '1011', '1001'], G: ['1111', '1000', '1011', '1001', '1111'] }   // 대각으로만 닿는 점(나비 모서리)이 없게 모서리를 각지게 — 닿으면 짝 없는 모서리가 생긴다
export const labelWidth = (text, px) => ([...text].reduce((w, ch) => w + (GLYPH[ch] ? GLYPH[ch][0].length + 1 : 0), 0) - 1) * px
// 글자 → (u,v) 사각 목록. 글자 위쪽 = u 가 작은 쪽, 읽는 방향 = v 가 작아지는 쪽(왼쪽→오른쪽이 −v). uTop = 글자 맨 위의 u, vStart = 첫 글자 왼쪽 끝의 v
export function labelRects(text, uTop, vStart, px) {
  const out = []; let at = 0
  for (const ch of text) {
    const g = GLYPH[ch]; if (!g) continue
    for (let r = 0; r < 5; r++) for (let c = 0; c < g[r].length; c++) if (g[r][c] === '1') out.push({ u0: uTop + r * px, u1: uTop + (r + 1) * px, v0: vStart - (at + c + 1) * px, v1: vStart - (at + c) * px })
    at += g[0].length + 1
  }
  return out
}
// 평평한 면 하나(구간 UA~UB × VA~VB, 바깥 법선 n)에서 pockets 사각을 depth 안쪽으로 판다. pt(u, v, d) = 3D 점(d = 안쪽 깊이). 글자 둘레만 칸으로 나누고 나머지는 큰 사각으로 둔다 — 이웃과 생기는 T자 이음은 conformTJunctions 가 메운다.
function engraveFace(kit, pt, n, eU, eV, UA, UB, VA, VB, pockets, depth) {
  const { quad } = kit, q4 = (a, b, c, d, nn) => quad(a, b, c, d, nn[0], nn[1], nn[2]), neg = (v) => v.map((x) => -x)
  const m = 0.6, wu0 = Math.max(UA, Math.min(...pockets.map((p) => p.u0)) - m), wu1 = Math.min(UB, Math.max(...pockets.map((p) => p.u1)) + m)
  const wv0 = Math.max(VA, Math.min(...pockets.map((p) => p.v0)) - m), wv1 = Math.min(VB, Math.max(...pockets.map((p) => p.v1)) + m)
  const flat = (u0, u1, v0, v1) => { if (u1 - u0 > 1e-9 && v1 - v0 > 1e-9) q4(pt(u0, v0, 0), pt(u1, v0, 0), pt(u1, v1, 0), pt(u0, v1, 0), n) }
  flat(UA, wu0, VA, VB); flat(wu1, UB, VA, VB); flat(wu0, wu1, VA, wv0); flat(wu0, wu1, wv1, VB)
  const vs = [...new Set([wv0, wv1, ...pockets.flatMap((p) => [p.v0, p.v1])])].sort((a, b) => a - b)
  const e = 1e-6, inP = (u, v) => pockets.some((p) => u > p.u0 - e && u < p.u1 + e && v > p.v0 - e && v < p.v1 + e)   // 낱 점 사각의 맞닿는 경계 위 점도 구멍 안으로 친다
  const bands = []
  for (let j = 0; j < vs.length - 1; j++) {
    const vm = (vs[j] + vs[j + 1]) / 2
    const us = [...new Set([wu0, wu1, ...pockets.filter((p) => p.v0 < vm && p.v1 > vm).flatMap((p) => [p.u0, p.u1])])].sort((a, b) => a - b)
    const runs = []
    for (let i = 0; i < us.length - 1; i++) { const pk = inP((us[i] + us[i + 1]) / 2, vm); if (runs.length && runs[runs.length - 1].pocket === pk) runs[runs.length - 1].hi = us[i + 1]; else runs.push({ lo: us[i], hi: us[i + 1], pocket: pk }) }
    bands.push(runs)
  }
  for (let j = 0; j < bands.length; j++) {
    const va = vs[j], vb = vs[j + 1]
    for (const r of bands[j]) {
      const d = r.pocket ? depth : 0
      q4(pt(r.lo, va, d), pt(r.hi, va, d), pt(r.hi, vb, d), pt(r.lo, vb, d), n)
      if (r.pocket) { // 좌우 벽(법선은 구멍 안쪽을 향한다)
        q4(pt(r.lo, va, 0), pt(r.lo, vb, 0), pt(r.lo, vb, depth), pt(r.lo, va, depth), eU)
        q4(pt(r.hi, va, 0), pt(r.hi, vb, 0), pt(r.hi, vb, depth), pt(r.hi, va, depth), neg(eU))
      }
    }
    if (j + 1 < bands.length) { // 위쪽 띠와의 경계: 한쪽만 구멍인 구간에 벽
      const cuts = [...new Set([...bands[j], ...bands[j + 1]].flatMap((r) => [r.lo, r.hi]))].sort((a, b) => a - b)
      for (let i = 0; i < cuts.length - 1; i++) {
        const um = (cuts[i] + cuts[i + 1]) / 2, a = inP(um, (va + vb) / 2), b = inP(um, (vb + vs[j + 2]) / 2)
        if (a === b) continue
        q4(pt(cuts[i], vb, 0), pt(cuts[i + 1], vb, 0), pt(cuts[i + 1], vb, depth), pt(cuts[i], vb, depth), a ? neg(eV) : eV) // 아래가 구멍이면 벽 법선은 −v
      }
    }
  }
}

export function addPlate(kit, { xCells, zCells, label }) {
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
        if (label && xc === xCells[label.cell] && zc === zCells[0]) { // 바닥면(Y1)에도 같은 글자 — 아래에서 봐도 바로 읽히게 v 방향을 뒤집는다
          const zz0 = Math.max(zCells[0].lo, iz0), zz1 = Math.min(zCells[zCells.length - 1].hi, iz1), W = labelWidth(label.text, label.px), vc = (zz0 + zz1) / 2
          const rr = labelRects(label.text, label.uTop, vc + W / 2, label.px).map((r) => ({ u0: r.u0, u1: r.u1, v0: 2 * vc - r.v1, v1: 2 * vc - r.v0 }))
          engraveFace(kit, (u, v, d) => P(u, Y1 + d, v), [0, -1, 0], [1, 0, 0], [0, 0, 1], xlo, xhi, zz0, zz1, rr, label.depth)
        } else if (!(label && xc === xCells[label.cell])) quad(P(xlo, Y1, zlo), P(xhi, Y1, zlo), P(xhi, Y1, zhi), P(xlo, Y1, zhi), 0, -1, 0)
        if (label && xc === xCells[label.cell] && zc === zCells[0]) { // 글자 칸: 윗면(Y4) 을 두 칸(zCells 전체 폭)을 합쳐 한 면으로 보고 글자를 판다
          const zz0 = Math.max(zCells[0].lo, iz0), zz1 = Math.min(zCells[zCells.length - 1].hi, iz1), W = labelWidth(label.text, label.px)
          engraveFace(kit, (u, v, d) => P(u, Y4 - d, v), [0, 1, 0], [1, 0, 0], [0, 0, 1], xlo, xhi, zz0, zz1, labelRects(label.text, label.uTop, (zz0 + zz1) / 2 + W / 2, label.px), label.depth)
        } else if (!(label && xc === xCells[label.cell])) quad(P(xlo, Y4, zlo), P(xhi, Y4, zlo), P(xhi, Y4, zhi), P(xlo, Y4, zhi), 0, 1, 0)
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
