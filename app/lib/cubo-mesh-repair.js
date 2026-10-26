// 삼각형 목록의 T자 이음(꼭짓점이 이웃 삼각형의 변 한가운데에 놓이는 곳)을 메운다 — 변 위에 놓인 꼭짓점마다 그 삼각형을 쪼개
// 이웃과 변 조각이 정확히 맞게 한다. 면을 칸으로 나눠 만들면 칸 크기가 다른 이웃 사이에 이런 이음이 생겨 "짝 없는 모서리"가
// 남는다(큐보 부품 규격 '만든 뒤 검증' — 짝 없는 모서리 0). 입력·출력: Float32Array(삼각형 수 × 9), 삼각형 방향(바깥 면)은 그대로 둔다.
const Q = 1e4
const keyOf = (x, y, z) => Math.round(x * Q) + ',' + Math.round(y * Q) + ',' + Math.round(z * Q)

// 같은 평면 위 삼각형 하나를 변 위 점들까지 넣어 귀 자르기로 나눈다(변 위 점이 만드는 넓이 0 조각은 만들지 않는다)
function splitTriangle(ring) {
  const n = ring.length
  // 가장 넓게 퍼진 두 축으로 투영
  const axes = [0, 1, 2].map((c) => { const v = ring.map((p) => p[c]); return Math.max(...v) - Math.min(...v) })
  const order = [0, 1, 2].sort((a, b) => axes[b] - axes[a]), u = order[0], w = order[1]
  const pt = (i) => [ring[i][u], ring[i][w]]
  const area2 = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
  let total = 0; for (let i = 0; i < n; i++) total += area2([0, 0], pt(i), pt((i + 1) % n))
  const sign = total >= 0 ? 1 : -1
  const idx = Array.from({ length: n }, (_, i) => i), out = []
  const inside = (p, a, b, c) => { const s1 = area2(a, b, p) * sign, s2 = area2(b, c, p) * sign, s3 = area2(c, a, p) * sign; return s1 >= -1e-12 && s2 >= -1e-12 && s3 >= -1e-12 }
  let guard = 0
  while (idx.length > 3 && guard++ < 10000) {
    let cut = false
    for (let i = 0; i < idx.length; i++) {
      const a = idx[(i + idx.length - 1) % idx.length], b = idx[i], c = idx[(i + 1) % idx.length]
      const ar = area2(pt(a), pt(b), pt(c)) * sign
      if (ar <= 1e-9) continue // 일직선(변 위 점)이거나 오목 — 귀가 아니다
      let ok = true
      for (const d of idx) { if (d === a || d === b || d === c) continue; if (inside(pt(d), pt(a), pt(b), pt(c))) { ok = false; break } }
      if (!ok) continue
      out.push([ring[a], ring[b], ring[c]]); idx.splice(i, 1); cut = true; break
    }
    if (!cut) break
  }
  if (idx.length === 3) out.push([ring[idx[0]], ring[idx[1]], ring[idx[2]]])
  return out
}

export function conformTJunctions(tris, tol = 2e-4) {
  const nT = tris.length / 9
  const verts = new Map() // 키 → 점
  for (let i = 0; i < nT; i++) for (let v = 0; v < 3; v++) { const p = [tris[i * 9 + v * 3], tris[i * 9 + v * 3 + 1], tris[i * 9 + v * 3 + 2]]; const k = keyOf(...p); if (!verts.has(k)) verts.set(k, p) }
  const list = [...verts.values()]
  // 공간 해시(1mm 칸)
  const CS = 1, cell = (p) => [Math.floor(p[0] / CS), Math.floor(p[1] / CS), Math.floor(p[2] / CS)]
  const hash = new Map(); list.forEach((p) => { const c = cell(p).join(','); (hash.get(c) || hash.set(c, []).get(c)).push(p) })
  const onEdge = (a, b) => { // 변 a-b 안쪽(끝점 제외)에 놓인 점들, a 에서 가까운 순
    const lo = [0, 1, 2].map((c) => Math.floor((Math.min(a[c], b[c]) - tol) / CS)), hi = [0, 1, 2].map((c) => Math.floor((Math.max(a[c], b[c]) + tol) / CS))
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2], res = []
    if (len2 < 1e-12) return res
    for (let x = lo[0]; x <= hi[0]; x++) for (let y = lo[1]; y <= hi[1]; y++) for (let z = lo[2]; z <= hi[2]; z++) {
      for (const p of hash.get(x + ',' + y + ',' + z) || []) {
        const t = ((p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1] + (p[2] - a[2]) * d[2]) / len2
        if (t <= 1e-6 || t >= 1 - 1e-6) continue
        const q = [a[0] + d[0] * t - p[0], a[1] + d[1] * t - p[1], a[2] + d[2] * t - p[2]]
        if (q[0] * q[0] + q[1] * q[1] + q[2] * q[2] < tol * tol) res.push([t, p])
      }
    }
    return res.sort((m, n) => m[0] - n[0]).map((m) => m[1])
  }
  const out = []
  for (let i = 0; i < nT; i++) {
    const P3 = [0, 1, 2].map((v) => [tris[i * 9 + v * 3], tris[i * 9 + v * 3 + 1], tris[i * 9 + v * 3 + 2]])
    const ring = []; let extra = 0
    for (let e = 0; e < 3; e++) { const a = P3[e], b = P3[(e + 1) % 3], mid = onEdge(a, b); ring.push(a, ...mid); extra += mid.length }
    if (!extra) { out.push(...P3.flat()); continue }
    for (const t of splitTriangle(ring)) out.push(...t.flat())
  }
  return Float32Array.from(out)
}

// 검사: 짝 없는 모서리·같은 방향 겹친 모서리·부피(양수) — 큐보 부품 규격 '만든 뒤 검증'
export function checkMesh(tris) {
  const nT = tris.length / 9, dir = new Map(); let vol = 0
  for (let i = 0; i < nT; i++) {
    const P3 = [0, 1, 2].map((v) => [tris[i * 9 + v * 3], tris[i * 9 + v * 3 + 1], tris[i * 9 + v * 3 + 2]])
    for (let v = 0; v < 3; v++) { const k = keyOf(...P3[v]) + '>' + keyOf(...P3[(v + 1) % 3]); dir.set(k, (dir.get(k) || 0) + 1) }
    const [a, b, c] = P3; vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
  }
  let open = 0, same = 0
  for (const [k, n] of dir) { const [a, c] = k.split('>'); if (n > 1) same++; if (!dir.has(c + '>' + a)) open++ }
  return { triangles: nT, open, same, volume: vol }
}

// 등록 전 검사: 짝 없는 모서리·같은 방향 겹침·부피(양수)가 하나라도 걸리면 던진다(DB 에 쓰지 않는다). 삼각형이 maxTris 를 넘으면 경고만 한다(곡선처럼 이유가 있는 경우 사용자에게 알린다).
export function assertPartMesh(name, tris, { maxTris = 4000 } = {}) {
  const r = checkMesh(tris)
  if (r.open > 0 || r.same > 0 || !(r.volume > 0)) throw new Error(`${name}: 규격 검사 실패 — 짝 없는 모서리 ${r.open}, 같은 방향 겹침 ${r.same}, 부피 ${r.volume.toFixed(1)} (모두 0/양수여야 한다. app/lib/cubo-part-maker.js '새 3D 부품을 만들거나 고칠 때 지킬 것')`)
  if (r.triangles > maxTris) console.warn(`${name}: 삼각형 ${r.triangles}개 — 기준(2~3천)을 넘는다. 이유를 사용자에게 알린다.`)
  return r
}
