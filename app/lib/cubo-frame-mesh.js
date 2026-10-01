// 큐보 직선 프레임을 자르기(CSG) 없이 삼각형으로 바로 짜는 생성기. 규격은 cubo-part-maker.js 의 CUBO_FRAME_STD 와 같다.
// 구멍·테두리를 자르는 계산으로 만들면 삼각형이 11배(2.2만 개) 늘어서, 팅커캐드 STL(약 2천 개)처럼 가볍게 직접 만든다.
// 길이 x(가운데 0), 두께 y(바닥 0~5), 폭 z(가운데 0). 좌표 단위 mm.
import { CUBO_FRAME_STD as S } from './cubo-part-maker.js'

const RO = S.rimOuterR - 0.01 // 구멍 테두리 바깥 반지름. 가장자리 테두리와 딱 닿으면(접선) 면 나누기가 깨져서 0.01 줄인다(눈에 안 보임)

// 구멍 n개 직선 프레임의 삼각형 목록: Float32Array(삼각형 수 × 9). seg = 구멍 원 둘레 분할 수.
export function frameTriangles(n, seg = 20) {
  const tris = []
  const L = n * S.pitch, hx = L / 2, hz = S.width / 2, E = S.edgeWall
  const Y0 = 0, Y1 = S.rimHeight, Y4 = S.rimHeight + S.plate, Y5 = S.total
  const cxs = Array.from({ length: n }, (_, i) => -hx + S.margin + i * S.pitch)
  // 법선 방향(nx,ny,nz)에 맞게 감는 순서를 정해서 삼각형 하나를 넣는다
  const tri = (a, b, c, nx, ny, nz) => {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2]
    const cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx
    if (cx * cx + cy * cy + cz * cz < 1e-12) return
    if (cx * nx + cy * ny + cz * nz >= 0) tris.push(a, b, c); else tris.push(a, c, b)
  }
  const quad = (a, b, c, d, nx, ny, nz) => { tri(a, b, c, nx, ny, nz); tri(a, c, d, nx, ny, nz) }
  const P = (x, y, z) => [x, y, z]
  // 원통 벽: 반지름 r, 높이 y0~y1, 방향 dir=+1 바깥쪽 / -1 안쪽(축 쪽)
  const cyl = (cx, r, y0, y1, dir) => {
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2
      const p0 = [cx + r * Math.cos(a0), r * Math.sin(a0)], p1 = [cx + r * Math.cos(a1), r * Math.sin(a1)]
      quad(P(p0[0], y0, p0[1]), P(p1[0], y0, p1[1]), P(p1[0], y1, p1[1]), P(p0[0], y1, p0[1]), dir * Math.cos(am), 0, dir * Math.sin(am))
    }
  }
  // 고리(안쪽 반지름 r0, 바깥 r1)를 높이 y에 깐다. ny = 면이 향하는 방향(+1 위 / -1 아래)
  const annulus = (cx, r0, r1, y, ny) => {
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg
      quad(P(cx + r0 * Math.cos(a0), y, r0 * Math.sin(a0)), P(cx + r1 * Math.cos(a0), y, r1 * Math.sin(a0)), P(cx + r1 * Math.cos(a1), y, r1 * Math.sin(a1)), P(cx + r0 * Math.cos(a1), y, r0 * Math.sin(a1)), 0, ny, 0)
    }
  }
  // 직사각형 칸(xlo~xhi × -4~4) 바닥에서 반지름 RO 원을 뺀 면
  const cell = (cx, xlo, xhi, y, ny) => {
    const zlo = -(hz - E), zhi = hz - E
    const ray = (a) => { // 중심에서 각도 a 방향으로 쏜 선이 칸 경계와 만나는 점
      const dx = Math.cos(a), dz = Math.sin(a)
      const t = Math.min(dx > 1e-9 ? (xhi - cx) / dx : Infinity, dx < -1e-9 ? (xlo - cx) / dx : Infinity, dz > 1e-9 ? zhi / dz : Infinity, dz < -1e-9 ? zlo / dz : Infinity)
      return [cx + t * dx, zlo === 0 ? 0 : t * dz]
    }
    const corners = [[xhi, zhi], [xlo, zhi], [xlo, zlo], [xhi, zlo]].map(([x, z]) => ({ x, z, a: (Math.atan2(z, x - cx) + 2 * Math.PI) % (2 * Math.PI) }))
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg
      const c0 = P(cx + RO * Math.cos(a0), y, RO * Math.sin(a0)), c1 = P(cx + RO * Math.cos(a1), y, RO * Math.sin(a1))
      const path = [ray(a0), ...corners.filter((q) => q.a > a0 + 1e-9 && q.a < a1 - 1e-9).sort((p, q) => p.a - q.a).map((q) => [q.x, q.z]), ray(a1)].map(([x, z]) => P(x, y, z))
      tri(c0, c1, path[path.length - 1], 0, ny, 0)
      for (let j = 0; j < path.length - 1; j++) tri(c0, path[j + 1], path[j], 0, ny, 0)
    }
  }

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
  const out = new Float32Array(tris.length * 3)
  tris.forEach((v, i) => { out[i * 3] = v[0]; out[i * 3 + 1] = v[1]; out[i * 3 + 2] = v[2] })
  return out
}

// 삼각형 → 바이너리 STL 바이트(80바이트 머리 + 개수 + 삼각형당 50바이트). 부품 만들기의 가져오기(import)가 읽는 형식.
// STL 은 Z가 위이고 가져오기가 X축으로 -90° 돌려 넣으므로, 여기서는 (x,y,z) → STL (x, -z, y) 로 바꿔 쓴다(등록된 프레임과 같은 방향이 된다).
export function trianglesToStl(tris) {
  const count = tris.length / 9
  const buf = new ArrayBuffer(84 + count * 50)
  const dv = new DataView(buf)
  dv.setUint32(80, count, true)
  for (let t = 0; t < count; t++) {
    const o = 84 + t * 50, p = t * 9
    const ux = tris[p + 3] - tris[p], uy = tris[p + 4] - tris[p + 1], uz = tris[p + 5] - tris[p + 2]
    const vx = tris[p + 6] - tris[p], vy = tris[p + 7] - tris[p + 1], vz = tris[p + 8] - tris[p + 2]
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx
    const l = Math.hypot(nx, ny, nz) || 1
    dv.setFloat32(o, nx / l, true); dv.setFloat32(o + 4, -nz / l, true); dv.setFloat32(o + 8, ny / l, true)
    for (let v = 0; v < 3; v++) {
      const x = tris[p + v * 3], y = tris[p + v * 3 + 1], z = tris[p + v * 3 + 2]
      dv.setFloat32(o + 12 + v * 12, x, true); dv.setFloat32(o + 16 + v * 12, -z, true); dv.setFloat32(o + 20 + v * 12, y, true)
    }
  }
  return new Uint8Array(buf)
}
