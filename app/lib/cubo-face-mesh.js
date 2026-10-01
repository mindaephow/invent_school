// 큐보 부품 메시 공용: 구멍이 여러 개 뚫린 평평한 면을 새 점 없이 삼각형으로 나눈다(귀 자르기).
// 바깥 윤곽과 구멍 윤곽의 점만 쓰므로 이웃 면·벽의 모서리와 정확히 맞아 이음매가 어긋나지 않는다. 면 방향은 kit.tri 가 법선(ny)에 맞춰 정한다.
// 점은 [x, z] 평면 좌표, 높이는 y. 구멍마다 바깥 윤곽과 겹치거나 서로 닿으면 안 된다.
const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
const area = (pp) => pp.reduce((s, q, i) => { const r = pp[(i + 1) % pp.length]; return s + q[0] * r[1] - r[0] * q[1] }, 0) / 2
const cross2 = (a, b, c, d) => { // 두 선분이 끝점 말고 서로 가로지르는가
  const d1 = cross(a, b, c), d2 = cross(a, b, d), d3 = cross(c, d, a), d4 = cross(c, d, b)
  return d1 * d2 < -1e-12 && d3 * d4 < -1e-12
}
function inside(pt, poly) { // 짝홀 규칙
  let c = false
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, zi] = poly[i], [xj, zj] = poly[j]
    if ((zi > pt[1]) !== (zj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - zi)) / (zj - zi) + xi) c = !c
  }
  return c
}

export function ringFace(kit, outerIn, holesIn, y, ny) {
  const { tri, P } = kit
  let ring = (area(outerIn) > 0 ? outerIn.slice() : outerIn.slice().reverse()) // 반시계
  const holes = holesIn.map((h) => (area(h) < 0 ? h.slice() : h.slice().reverse())) // 시계
  const rest = holes.map((h, i) => ({ h, i, mx: Math.max(...h.map((q) => q[0])) })).sort((a, b) => b.mx - a.mx) // x 가 큰 구멍부터 이어 붙인다
  for (let n = 0; n < rest.length; n++) {
    const { h } = rest[n]
    let hi = 0
    for (let k = 1; k < h.length; k++) if (h[k][0] > h[hi][0]) hi = k
    const H = h[hi]
    const others = rest.slice(n + 1).map((r) => r.h)
    const order = ring.map((_, i) => i).sort((i, j) => Math.hypot(ring[i][0] - H[0], ring[i][1] - H[1]) - Math.hypot(ring[j][0] - H[0], ring[j][1] - H[1]))
    let vi = -1
    for (const i of order) {
      const V = ring[i]
      let ok = true
      for (let k = 0; k < ring.length && ok; k++) if (cross2(H, V, ring[k], ring[(k + 1) % ring.length])) ok = false
      for (const o of [h, ...others]) for (let k = 0; k < o.length && ok; k++) if (cross2(H, V, o[k], o[(k + 1) % o.length])) ok = false
      if (!ok) continue
      const mid = [(H[0] + V[0]) / 2, (H[1] + V[1]) / 2]
      if (!inside(mid, ring)) continue
      if (others.some((o) => inside(mid, o)) || inside(mid, h)) continue
      vi = i; break
    }
    if (vi < 0) throw new Error('구멍을 바깥 윤곽에 이을 자리가 없다')
    ring = [...ring.slice(0, vi + 1), ...h.slice(hi), ...h.slice(0, hi), H, ...ring.slice(vi)]
  }
  const idx = ring.map((_, i) => i)
  const same = (a, b) => Math.abs(a[0] - b[0]) < 1e-9 && Math.abs(a[1] - b[1]) < 1e-9
  const inTri = (a, b, c, q) => !(same(q, a) || same(q, b) || same(q, c)) && cross(a, b, q) >= -1e-12 && cross(b, c, q) >= -1e-12 && cross(c, a, q) >= -1e-12
  const emit = (a, b, c) => tri(P(a[0], y, a[1]), P(b[0], y, b[1]), P(c[0], y, c[1]), 0, ny, 0)
  let guard = 0
  while (idx.length > 3 && guard++ < 100000) {
    let cut = false
    for (let k = 0; k < idx.length; k++) {
      const a = ring[idx[(k + idx.length - 1) % idx.length]], b = ring[idx[k]], c = ring[idx[(k + 1) % idx.length]]
      if (cross(a, b, c) <= 1e-12) continue // 볼록한 꼭짓점만
      if (idx.some((m) => inTri(a, b, c, ring[m]))) continue
      emit(a, b, c); idx.splice(k, 1); cut = true; break
    }
    if (!cut) throw new Error('면 나누기 실패(귀를 찾지 못함)')
  }
  if (idx.length === 3) emit(ring[idx[0]], ring[idx[1]], ring[idx[2]])
}

// 중심 (cx,cz) 반지름 r, 둘레 seg 등분 점(구멍 벽 kit.cyl 과 같은 점)
export const circlePts = (cx, cz, r, seg) => Array.from({ length: seg }, (_, k) => [cx + r * Math.cos((2 * Math.PI * k) / seg), cz + r * Math.sin((2 * Math.PI * k) / seg)])
