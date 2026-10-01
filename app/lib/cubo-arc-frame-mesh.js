// 큐보 반원프레임(구멍 9개)을 자르기 없이 삼각형으로 직접 짠다. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD(판 3·테두리 1·구멍 구조·폭 10) 그대로.
// 구멍 9개는 호 위에서 서로 10mm(현) 간격, 양 끝 두 구멍 중심은 60mm 떨어짐(교재 11번 그림: 가운데 3개가 직선 프레임 10mm 격자에 맞고, 4·6번 구멍에 리벳이 꽂힌다).
// 호 띠 폭 10(구멍 중심 ±5), 양 끝 구멍 아래로 5mm 곧은 발. 판 위에서 보면 x 좌우, z 는 호가 솟는 쪽(+z). 두께 y 는 바닥 0~5. 좌표는 전체 크기의 가운데가 0.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'
import { makeKit, trianglesToStl } from './cubo-mesh-kit.js'

export { trianglesToStl }

// 구멍 9개는 호 위에서 서로 10mm(현) 간격이고 양 끝 두 구멍 중심은 60mm 떨어진다(교재 11번 그림: 4·6번 구멍이 직선 프레임 바깥 열 ±10에 맞는다).
// 호 반지름 R 은 위 두 조건으로 정해진다(약 31.5). 호 띠 폭 10(R±5), 끝 구멍 아래로 5mm 곧은 발.
export const ARC_STD = { holes: 9, chord: 10, endSpan: 60, foot: S.margin }
export function solveArc() {
  const half = (ARC_STD.holes - 1) / 2 // 4
  const f = (R) => R * Math.sin(half * 2 * Math.asin(ARC_STD.chord / 2 / R)) - ARC_STD.endSpan / 2
  let lo = 26, hi = 60 // f(lo)<0<f(hi) 가 아니므로 부호가 바뀌는 곳을 훑어서 찾는다
  let prev = f(lo)
  for (let R = lo; R <= hi; R += 0.01) { const v = f(R); if (prev < 0 && v >= 0) { lo = R - 0.01; hi = R; break } prev = v }
  for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (f(m) < 0) lo = m; else hi = m }
  const R = (lo + hi) / 2
  return { R, delta: 2 * Math.asin(ARC_STD.chord / 2 / R) } // delta: 이웃 구멍 사이 각(라디안)
}
const RO = S.rimOuterR - 0.01
const E = S.edgeWall
const rad = (d) => (d * Math.PI) / 180

// 중심 (cx,cz)에서 각도 a 방향 선이 다각형(평면 점 배열)과 처음 만나는 점
function hit(cx, cz, poly, a) {
  const dx = Math.cos(a), dz = Math.sin(a)
  let best = Infinity
  for (let i = 0; i < poly.length; i++) {
    const [x1, z1] = poly[i], [x2, z2] = poly[(i + 1) % poly.length]
    const ex = x2 - x1, ez = z2 - z1
    const den = dx * ez - dz * ex
    if (Math.abs(den) < 1e-12) continue
    const t = ((x1 - cx) * ez - (z1 - cz) * ex) / den
    const u = ((x1 - cx) * dz - (z1 - cz) * dx) / den
    if (t > 1e-9 && u > -1e-9 && u < 1 + 1e-9 && t < best) best = t
  }
  return [cx + best * dx, cz + best * dz]
}

// 다각형(칸의 안쪽 윤곽)에서 중심 원(반지름 R)을 뺀 면 — kit.cell 의 다각형 버전
function polyCell(kit, cx, cz, R, poly, y, ny) {
  const { tri, P, seg } = kit
  const ang = (x, z) => (Math.atan2(z - cz, x - cx) + 2 * Math.PI) % (2 * Math.PI)
  const verts = poly.map(([x, z]) => ({ x, z, a: ang(x, z) }))
  for (let k = 0; k < seg; k++) {
    const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg
    const c0 = P(cx + R * Math.cos(a0), y, cz + R * Math.sin(a0)), c1 = P(cx + R * Math.cos(a1), y, cz + R * Math.sin(a1))
    const path = [hit(cx, cz, poly, a0), ...verts.filter((q) => q.a > a0 + 1e-9 && q.a < a1 - 1e-9).sort((p, q) => p.a - q.a).map((q) => [q.x, q.z]), hit(cx, cz, poly, a1)].map(([x, z]) => P(x, y, z))
    tri(c0, c1, path[path.length - 1], 0, ny, 0)
    for (let j = 0; j < path.length - 1; j++) tri(c0, path[j + 1], path[j], 0, ny, 0)
  }
}

export function arcFrameTriangles(seg = 20, sub = 4) {
  const kit = makeKit(seg)
  const { quad, P } = kit
  const n = ARC_STD.holes, W = S.width / 2, F = ARC_STD.foot
  const { R, delta } = solveArc()
  const half = (n - 1) / 2
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const pt = (r, a) => [r * Math.sin(a), r * Math.cos(a)] // 각도 a 는 +z 에서 +x 쪽으로
  const phiEnd = half * delta
  const holeX = R * Math.sin(phiEnd) // 끝 구멍 중심 x (= 30)
  const xo = holeX + W, xi = holeX - W // 발의 곧은 옆면 x: 구멍 중심에서 5mm(직선 프레임의 여백·폭과 같다)
  const zb = R * Math.cos(phiEnd) - F // 발 바닥 z
  // 호 위 각도 표본: 칸 경계(±3.5δ 안쪽)를 잘게 나눈 것 + 양 끝(e)
  const mid = Array.from({ length: (n - 1) * sub + 1 - sub }, (_, j) => (-(half - 0.5) + (j / sub)) * delta)
  const angles = (e) => [-e, ...mid, e]
  // 윤곽(반시계): 오른발 → 바깥 호(오른쪽→왼쪽) → 왼발 → 안쪽 호(왼쪽→오른쪽). d = 안쪽으로 줄이는 양(0 이면 바깥 윤곽, E 면 테두리 안쪽 윤곽)
  const geo = (d) => {
    const ro = R + W - d, ri = R - W + d, xod = xo - d, xid = xi + d, zbd = zb + d
    return { ro, ri, xod, xid, zbd, eo: Math.asin(xod / ro), ei: Math.asin(xid / ri) }
  }
  const loop = (d) => {
    const g = geo(d)
    return [[g.xod, g.zbd], ...angles(g.eo).reverse().map((a) => pt(g.ro, a)), [-g.xod, g.zbd], [-g.xid, g.zbd], ...angles(g.ei).map((a) => pt(g.ri, a)), [g.xid, g.zbd]]
  }
  const O = loop(0), I = loop(E)
  const m = O.length
  const nrm = (A, B) => { const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); return [dz / l, -dx / l] } // 반시계 윤곽의 바깥쪽 법선
  for (let i = 0; i < m; i++) {
    const j = (i + 1) % m
    const [px, pz] = nrm(O[i], O[j])
    quad(P(O[i][0], Y0, O[i][1]), P(O[j][0], Y0, O[j][1]), P(O[j][0], Y5, O[j][1]), P(O[i][0], Y5, O[i][1]), px, 0, pz)
    for (const [y, ny] of [[Y0, -1], [Y5, 1]]) quad(P(O[i][0], y, O[i][1]), P(O[j][0], y, O[j][1]), P(I[j][0], y, I[j][1]), P(I[i][0], y, I[i][1]), 0, ny, 0)
    for (const [y0, y1] of [[Y0, Y1], [Y4, Y5]]) quad(P(I[i][0], y0, I[i][1]), P(I[j][0], y0, I[j][1]), P(I[j][0], y1, I[j][1]), P(I[i][0], y1, I[i][1]), -px, 0, -pz)
  }
  // 칸마다(구멍 하나씩): 안쪽 윤곽 조각 + 구멍 고리·벽
  const g = geo(E), aO = angles(g.eo), aI = angles(g.ei)
  for (let k = 0; k < n; k++) {
    const phi = (k - half) * delta
    const lo = k === 0 ? -Infinity : phi - delta / 2, hi = k === n - 1 ? Infinity : phi + delta / 2
    const inR = (a) => a >= lo - 1e-9 && a <= hi + 1e-9
    const outer = aO.filter(inR).map((a) => pt(g.ro, a)), inner = aI.filter(inR).map((a) => pt(g.ri, a)).reverse()
    const poly = [...outer]
    if (k === n - 1) poly.push([g.xod, g.zbd], [g.xid, g.zbd])
    poly.push(...inner)
    if (k === 0) poly.push([-g.xid, g.zbd], [-g.xod, g.zbd])
    const [cx, cz] = pt(R, phi)
    kit.annulus(cx, cz, S.rimInnerR, RO, Y0, -1); kit.annulus(cx, cz, S.rimInnerR, RO, Y5, 1)
    kit.cyl(cx, cz, RO, Y0, Y1, 1); kit.cyl(cx, cz, RO, Y4, Y5, 1)
    kit.cyl(cx, cz, S.rimInnerR, Y0, Y1, -1); kit.cyl(cx, cz, S.rimInnerR, Y4, Y5, -1)
    kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y1, -1); kit.annulus(cx, cz, S.boreR, S.rimInnerR, Y4, 1)
    kit.cyl(cx, cz, S.boreR, Y1, Y4, -1)
    polyCell(kit, cx, cz, RO, poly, Y1, -1); polyCell(kit, cx, cz, RO, poly, Y4, 1)
  }
  // 전체 크기의 가운데가 (0,0): z 는 발 바닥 ~ 호 꼭대기(R+W)
  const zc = (zb + R + W) / 2
  const out = kit.result()
  for (let i = 2; i < out.length; i += 3) out[i] -= zc
  return out
}
