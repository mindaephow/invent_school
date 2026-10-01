// 큐보 부품 메시 생성 공용 도구: 삼각형 모으기, 원통 벽, 고리 면, 원이 뚫린 사각 칸 면, 바이너리 STL 변환.
// 좌표 단위 mm. 삼각형은 [x,y,z] 점 3개 배열로 모은다.
export function makeKit(seg = 20) {
  const tris = []
  // 법선 방향(nx,ny,nz)에 맞게 감는 순서를 정해서 삼각형 하나를 넣는다
  const tri = (a, b, c, nx, ny, nz) => {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2]
    const cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx
    if (cx * cx + cy * cy + cz * cz < 1e-12) return
    if (cx * nx + cy * ny + cz * nz >= 0) tris.push(a, b, c); else tris.push(a, c, b)
  }
  const quad = (a, b, c, d, nx, ny, nz) => { tri(a, b, c, nx, ny, nz); tri(a, c, d, nx, ny, nz) }
  // 감는 순서를 그대로 쓰는 삼각형(반시계=바깥쪽). 돌기처럼 방향이 이미 맞춰진 면에 쓴다.
  const raw = (a, b, c) => {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2]
    const cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx
    if (cx * cx + cy * cy + cz * cz < 1e-12) return
    tris.push(a, b, c)
  }
  const P = (x, y, z) => [x, y, z]
  // 원통 벽(축 y): 반지름 r, 높이 y0~y1, dir=+1 바깥쪽 / -1 안쪽(축 쪽)
  const cyl = (cx, cz, r, y0, y1, dir) => {
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2
      const p0 = [cx + r * Math.cos(a0), cz + r * Math.sin(a0)], p1 = [cx + r * Math.cos(a1), cz + r * Math.sin(a1)]
      quad(P(p0[0], y0, p0[1]), P(p1[0], y0, p1[1]), P(p1[0], y1, p1[1]), P(p0[0], y1, p0[1]), dir * Math.cos(am), 0, dir * Math.sin(am))
    }
  }
  // 고리(안쪽 r0, 바깥 r1)를 높이 y에 깐다. ny = 면이 향하는 방향(+1 위 / -1 아래)
  const annulus = (cx, cz, r0, r1, y, ny) => {
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg
      quad(P(cx + r0 * Math.cos(a0), y, cz + r0 * Math.sin(a0)), P(cx + r1 * Math.cos(a0), y, cz + r1 * Math.sin(a0)), P(cx + r1 * Math.cos(a1), y, cz + r1 * Math.sin(a1)), P(cx + r0 * Math.cos(a1), y, cz + r0 * Math.sin(a1)), 0, ny, 0)
    }
  }
  // 사각 칸(xlo~xhi × zlo~zhi)의 높이 y 면에서 중심 (cx,cz) 반지름 R 원을 뺀 면. 칸이 원을 감싸야 한다.
  const cell = (cx, cz, R, xlo, xhi, zlo, zhi, y, ny) => {
    const ray = (a) => { // 중심에서 각도 a 방향 선이 칸 경계와 만나는 점
      const dx = Math.cos(a), dz = Math.sin(a)
      const t = Math.min(dx > 1e-9 ? (xhi - cx) / dx : Infinity, dx < -1e-9 ? (xlo - cx) / dx : Infinity, dz > 1e-9 ? (zhi - cz) / dz : Infinity, dz < -1e-9 ? (zlo - cz) / dz : Infinity)
      return [cx + t * dx, cz + t * dz]
    }
    const corners = [[xhi, zhi], [xlo, zhi], [xlo, zlo], [xhi, zlo]].map(([x, z]) => ({ x, z, a: (Math.atan2(z - cz, x - cx) + 2 * Math.PI) % (2 * Math.PI) }))
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg
      const c0 = P(cx + R * Math.cos(a0), y, cz + R * Math.sin(a0)), c1 = P(cx + R * Math.cos(a1), y, cz + R * Math.sin(a1))
      const path = [ray(a0), ...corners.filter((q) => q.a > a0 + 1e-9 && q.a < a1 - 1e-9).sort((p, q) => p.a - q.a).map((q) => [q.x, q.z]), ray(a1)].map(([x, z]) => P(x, y, z))
      tri(c0, c1, path[path.length - 1], 0, ny, 0)
      for (let j = 0; j < path.length - 1; j++) tri(c0, path[j + 1], path[j], 0, ny, 0)
    }
  }
  const result = () => {
    const out = new Float32Array(tris.length * 3)
    tris.forEach((v, i) => { out[i * 3] = v[0]; out[i * 3 + 1] = v[1]; out[i * 3 + 2] = v[2] })
    return out
  }
  // 다른 키트의 결과(Float32Array)를 점 변환 map([x,y,z])→[x,y,z] 으로 옮겨서 합친다. map 은 회전·이동이어야 한다(거울 반전이면 면이 뒤집힌다).
  const append = (arr, map) => { for (let i = 0; i < arr.length; i += 3) tris.push(map([arr[i], arr[i + 1], arr[i + 2]])) }
  return { seg, tri, quad, raw, P, cyl, annulus, cell, append, result }
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
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx
    const l = Math.hypot(nx, ny, nz) || 1
    dv.setFloat32(o, nx / l, true); dv.setFloat32(o + 4, -nz / l, true); dv.setFloat32(o + 8, ny / l, true)
    for (let v = 0; v < 3; v++) {
      const x = tris[p + v * 3], y = tris[p + v * 3 + 1], z = tris[p + v * 3 + 2]
      dv.setFloat32(o + 12 + v * 12, x, true); dv.setFloat32(o + 16 + v * 12, -z, true); dv.setFloat32(o + 20 + v * 12, y, true)
    }
  }
  return new Uint8Array(buf)
}
