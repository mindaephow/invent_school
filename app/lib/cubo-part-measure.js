// 부품 3D 모델(STL)에서 크기·대칭·돌기·구멍을 재서 등록된 연결점과 대조한다 (MCP measure_part 의 계산 부분).
// 사람이 3D 점 좌표를 SQL 이나 브라우저 캐시로 읽던 일을 서버가 한다. 좌표는 부품 연결점과 같은 "모델 로컬(bbox 가운데 기준, y 위)".
//
// 파이프라인(설계 화면 makeRobotModelMesh 와 같은 규칙):
//   STL 점 (x, y, z) → rotateX(−90°) = (x, z, −y) → 가로·세로(x, z)는 가운데, 높이(y)는 바닥이 0 → 도형 위치·회전(rx, ry, rz 라디안) → bbox 가운데를 원점으로.
// 돌기·구멍은 "둥근 벽"을 찾아서 잰다: 축에 수직인 삼각형(법선이 축과 거의 직각) 가운데 법선이 한 바퀴 돌며 이어진 덩어리 = 원통.
//   벽 법선이 중심에서 바깥으로 향하면 돌기, 안쪽으로 향하면 구멍(소켓). 십자(+) 모양처럼 평평한 벽만 있는 소켓은 못 찾는다.

// ── STL ──
export function parseStl(buf) {
  // 이진 STL: 80바이트 머리 + 삼각형 수(4바이트) + 삼각형 50바이트씩(법선 12, 점 36, 속성 2)
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength)
  const n = dv.getUint32(80, true)
  if (84 + n * 50 !== buf.byteLength) throw new Error('이진 STL 형식이 아니에요(삼각형 수와 파일 크기가 안 맞음).')
  const pos = new Float64Array(n * 9)
  for (let i = 0; i < n; i++) for (let k = 0; k < 9; k++) pos[i * 9 + k] = dv.getFloat32(84 + i * 50 + 12 + k * 4, true)
  return pos
}

export function stlFromDataUrl(url) {
  const m = /^data:[^,]*;base64,(.*)$/s.exec(url || '')
  if (!m) throw new Error('모델 데이터(fileDataUrl)가 base64 형식이 아니에요.')
  return parseStl(Buffer.from(m[1], 'base64'))
}

// ── 좌표 변환: STL → 연결점 기준 좌표 ──
const rotMat = (rx, ry, rz) => { // three.js Euler 'XYZ': R = Rx·Ry·Rz
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry), cz = Math.cos(rz), sz = Math.sin(rz)
  const Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]], Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
  const mul = (a, b) => a.map((_, i) => [0, 1, 2].map((j) => a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]))
  return mul(Rx, mul(Ry, Rz))
}

export function toConnectorFrame(raw, shape = {}) {
  const n = raw.length / 3
  const p = new Float64Array(raw.length)
  for (let i = 0; i < n; i++) { p[i * 3] = raw[i * 3]; p[i * 3 + 1] = raw[i * 3 + 2]; p[i * 3 + 2] = -raw[i * 3 + 1] } // rotateX(-90°)
  const mm = (k) => { let lo = Infinity, hi = -Infinity; for (let i = 0; i < n; i++) { const v = p[i * 3 + k]; if (v < lo) lo = v; if (v > hi) hi = v } return [lo, hi] }
  const bx = mm(0), by = mm(1), bz = mm(2)
  const cx = (bx[0] + bx[1]) / 2, cz = (bz[0] + bz[1]) / 2
  for (let i = 0; i < n; i++) { p[i * 3] -= cx; p[i * 3 + 1] -= by[0]; p[i * 3 + 2] -= cz } // x·z 가운데, 바닥 y=0
  const R = rotMat(shape.rx || 0, shape.ry || 0, shape.rz || 0), t = [shape.x || 0, shape.y || 0, shape.z || 0]
  for (let i = 0; i < n; i++) {
    const v = [p[i * 3], p[i * 3 + 1], p[i * 3 + 2]]
    for (let r = 0; r < 3; r++) p[i * 3 + r] = R[r][0] * v[0] + R[r][1] * v[1] + R[r][2] * v[2] + t[r]
  }
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity]
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) { const v = p[i * 3 + k]; if (v < lo[k]) lo[k] = v; if (v > hi[k]) hi[k] = v }
  const c = [0, 1, 2].map((k) => (lo[k] + hi[k]) / 2)
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) p[i * 3 + k] -= c[k]
  return { pos: p, size: [0, 1, 2].map((k) => hi[k] - lo[k]), shapeCenter: c }
}

// ── 대칭: 가운데 면으로 뒤집은 점이 (0.4mm 안에) 짝이 있는 비율 ──
export function mirrorMismatch(pos, size) {
  const n = pos.length / 3, q = 0.5
  const key = (x, y, z) => Math.round(x / q) + ',' + Math.round(y / q) + ',' + Math.round(z / q)
  const set = new Set(); for (let i = 0; i < n; i++) set.add(key(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]))
  const near = (x, y, z) => { // 이웃 칸까지 찾는다
    const a = Math.round(x / q), b = Math.round(y / q), c = Math.round(z / q)
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (let k = -1; k <= 1; k++) if (set.has((a + i) + ',' + (b + j) + ',' + (c + k))) return true
    return false
  }
  return [0, 1, 2].map((ax) => { let miss = 0; for (let i = 0; i < n; i++) { const v = [pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]]; v[ax] = -v[ax]; if (!near(v[0], v[1], v[2])) miss++ } return Math.round((miss / n) * 1000) / 10 })
}

// ── 원통(돌기·구멍) 찾기 ──
const AXN = ['x', 'y', 'z']
export function findCylinders(pos, size) {
  const nT = pos.length / 9
  // 삼각형 법선
  const nor = new Float64Array(nT * 3)
  let vol = 0
  for (let t = 0; t < nT; t++) {
    const a = t * 9
    const ux = pos[a + 3] - pos[a], uy = pos[a + 4] - pos[a + 1], uz = pos[a + 5] - pos[a + 2]
    const vx = pos[a + 6] - pos[a], vy = pos[a + 7] - pos[a + 1], vz = pos[a + 8] - pos[a + 2]
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx
    vol += (pos[a] * (pos[a + 4] * pos[a + 8] - pos[a + 5] * pos[a + 7]) - pos[a + 1] * (pos[a + 3] * pos[a + 8] - pos[a + 5] * pos[a + 6]) + pos[a + 2] * (pos[a + 3] * pos[a + 7] - pos[a + 4] * pos[a + 6])) / 6
    const l = Math.hypot(nx, ny, nz) || 1
    nor[t * 3] = nx / l; nor[t * 3 + 1] = ny / l; nor[t * 3 + 2] = nz / l
  }
  const flip = vol < 0 ? -1 : 1 // 감는 방향이 거꾸로인 모델이면 법선을 뒤집는다
  const out = []
  for (let ax = 0; ax < 3; ax++) {
    const [u, v] = [0, 1, 2].filter((k) => k !== ax)
    const wall = []
    for (let t = 0; t < nT; t++) if (Math.abs(nor[t * 3 + ax]) < 0.2) wall.push(t)
    // 점 이어 붙이기(0.01mm 반올림) — 벽 삼각형끼리 점을 나누면 같은 덩어리
    const parent = new Map()
    const find = (k) => { let r = k; while (parent.get(r) !== r) r = parent.get(r); while (parent.get(k) !== r) { const nx = parent.get(k); parent.set(k, r); k = nx } return r }
    const key = (t, i) => { const a = t * 9 + i * 3; return Math.round(pos[a] * 100) + ',' + Math.round(pos[a + 1] * 100) + ',' + Math.round(pos[a + 2] * 100) }
    wall.forEach((t) => { for (let i = 0; i < 3; i++) { const k = key(t, i); if (!parent.has(k)) parent.set(k, k) } })
    wall.forEach((t) => { const r0 = find(key(t, 0)); for (let i = 1; i < 3; i++) { const r1 = find(key(t, i)); if (r1 !== r0) parent.set(r1, r0) } })
    const groups = new Map()
    wall.forEach((t) => { const r = find(key(t, 0)); if (!groups.has(r)) groups.set(r, []); groups.get(r).push(t) })
    groups.forEach((tris) => {
      if (tris.length < 8) return
      // 원 맞추기: 점들의 (u,v) 평균 = 중심
      let su = 0, sv = 0, cnt = 0, lo = Infinity, hi = -Infinity
      tris.forEach((t) => { for (let i = 0; i < 3; i++) { const a = t * 9 + i * 3; su += pos[a + u]; sv += pos[a + v]; cnt++; const h = pos[a + ax]; if (h < lo) lo = h; if (h > hi) hi = h } })
      const cu = su / cnt, cv = sv / cnt
      let rs = 0, rmin = Infinity, rmax = 0
      const dists = []
      tris.forEach((t) => { for (let i = 0; i < 3; i++) { const a = t * 9 + i * 3; const d = Math.hypot(pos[a + u] - cu, pos[a + v] - cv); dists.push(d); rs += d; if (d < rmin) rmin = d; if (d > rmax) rmax = d } })
      const r = rs / dists.length
      if (r < 0.8 || r > 15 || hi - lo < 0.5) return
      if ((rmax - rmin) > 0.12 * r + 0.15) return // 원이 아님(타원·평평한 벽)
      // 법선이 한 바퀴 도는지(30° 칸 12개 중 8개 이상)
      const bins = new Set(); let outward = 0
      tris.forEach((t) => {
        const nu = nor[t * 3 + u] * flip, nv = nor[t * 3 + v] * flip
        bins.add(Math.floor(((Math.atan2(nv, nu) + Math.PI) / (2 * Math.PI)) * 12) % 12)
        const a = t * 9; const mu = (pos[a + u] + pos[a + 3 + u] + pos[a + 6 + u]) / 3 - cu, mv = (pos[a + v] + pos[a + 3 + v] + pos[a + 6 + v]) / 3 - cv
        outward += Math.sign(nu * mu + nv * mv)
      })
      if (bins.size < 8) return
      const isPeg = outward > 0
      const mid = (lo + hi) / 2
      const sign = mid >= 0 ? 1 : -1 // 부품 가운데에서 먼 쪽
      const dirSign = isPeg ? sign : -sign // 돌기: 바깥으로, 구멍: 안으로 들어가는 방향
      const c3 = [0, 0, 0]; c3[u] = cu; c3[v] = cv; c3[ax] = mid
      const far = sign > 0 ? hi : lo, near = sign > 0 ? lo : hi
      const entrance = [0, 0, 0]; entrance[u] = cu; entrance[v] = cv; entrance[ax] = isPeg ? near : far
      const through = !isPeg && (hi - lo) >= 0.8 * size[ax] // 부품을 끝까지 뚫은 구멍은 어느 쪽에서든 끼울 수 있다(방향 무관)
      out.push({ kind: isPeg ? 'peg' : 'hole', axis: AXN[ax], dir: through ? '±' + AXN[ax] : (dirSign > 0 ? '+' : '-') + AXN[ax], r, len: hi - lo, center: c3, entrance, lo, hi, through })
    })
  }
  // 같은 원통이 두 번 잡힌 것(위·아래 벽이 따로 이어진 경우) 합치기
  const merged = []
  out.forEach((f) => {
    const dup = merged.find((g) => g.kind === f.kind && g.axis === f.axis && Math.hypot(...[0, 1, 2].map((k) => g.center[k] - f.center[k]).filter((_, k) => AXN[k] !== f.axis)) < 0.6 && Math.abs(g.r - f.r) < 0.4 && Math.min(g.hi, f.hi) - Math.max(g.lo, f.lo) > -0.3)
    if (!dup) merged.push(f)
  })
  return merged
}

// ── 등록된 연결점과 대조 ──
const dirName = (d) => { const k = [0, 1, 2].reduce((m, i) => (Math.abs(d[i]) > Math.abs(d[m]) ? i : m), 0); return (d[k] >= 0 ? '+' : '-') + AXN[k] }
export function compareWithRegistered(features, conn) {
  const reg = [...(conn?.pegs || []).map((c) => ({ ...c, kind: 'peg' })), ...(conn?.holes || []).map((c) => ({ ...c, kind: 'hole' }))]
  const used = new Set(), lines = [], ok = [], bad = []
  reg.forEach((c) => {
    const dn = dirName(c.dir), ax = dn[1]
    const cand = features.map((f, i) => ({ f, i })).filter(({ f, i }) => !used.has(i) && f.kind === c.kind && f.axis === ax && (f.dir === dn || f.through))
    const dist = (f) => Math.hypot(...[0, 1, 2].filter((k) => AXN[k] !== ax).map((k) => f.center[k] - c.pos[k]))
    cand.sort((a, b) => dist(a.f) - dist(b.f))
    const best = cand[0]
    if (best && dist(best.f) < 2.5) {
      used.add(best.i)
      const f = best.f, notes = []
      const d = dist(f); if (d > 0.6) notes.push('가로 위치 차 ' + d.toFixed(1) + 'mm')
      if (c.r && Math.abs(c.r - f.r) > 0.5) notes.push('반지름 등록 ' + c.r + ' ↔ 실측 ' + f.r.toFixed(2))
      if (c.kind === 'peg' && c.len && Math.abs(c.len - f.len) > 0.7) notes.push('길이 등록 ' + c.len + ' ↔ 실측 ' + f.len.toFixed(1))
      const axialReg = c.pos[AXN.indexOf(ax)], axialMeas = c.kind === 'peg' ? f.center[AXN.indexOf(ax)] : (c.len ? f.center[AXN.indexOf(ax)] : f.entrance[AXN.indexOf(ax)])
      if (Math.abs(axialReg - axialMeas) > 0.8) notes.push('높이 위치 등록 ' + axialReg + ' ↔ 실측 ' + axialMeas.toFixed(1))
      ;(notes.length ? bad : ok).push(c.id)
      lines.push((notes.length ? '△ ' : '✓ ') + c.id + ' (' + (c.kind === 'peg' ? '돌기' : '구멍') + ' ' + dn + ')' + (notes.length ? ' — ' + notes.join(', ') : ' — 실측과 일치'))
    } else { bad.push(c.id); lines.push('✗ ' + c.id + ' (' + (c.kind === 'peg' ? '돌기' : '구멍') + ' ' + dn + ') — 이 자리에서 둥근 ' + (c.kind === 'peg' ? '돌기' : '구멍') + '를 못 찾음(십자·네모 소켓이면 정상)') }
  })
  const extra = features.filter((_, i) => !used.has(i))
  return { lines, extra, matched: ok.length, differ: bad.length }
}

export function measureModel(raw, shape, conn) {
  const { pos, size } = toConnectorFrame(raw, shape)
  const sym = mirrorMismatch(pos, size)
  const features = findCylinders(pos, size).sort((a, b) => a.axis.localeCompare(b.axis) || a.dir.localeCompare(b.dir) || a.center[0] - b.center[0] || a.center[2] - b.center[2])
  const cmp = compareWithRegistered(features, conn)
  return { size, sym, features, cmp, triangles: pos.length / 9 }
}

export function formatMeasure(name, m, hasConn) {
  const r1 = (v) => Math.round(v * 10) / 10
  const L = []
  L.push('■ ' + name + ' 실측 (삼각형 ' + m.triangles + '개)')
  L.push('크기 x ' + r1(m.size[0]) + ' × y ' + r1(m.size[1]) + ' × z ' + r1(m.size[2]) + ' mm  (좌표는 bbox 가운데 기준, y 위)')
  L.push('대칭(가운데 면으로 뒤집었을 때 짝 없는 점 %): x ' + m.sym[0] + ' / y ' + m.sym[1] + ' / z ' + m.sym[2] + '   ← 2% 이하면 그 방향 대칭, 클수록 앞뒤·좌우가 다른 모양')
  L.push('')
  L.push('둥근 돌기·구멍 ' + m.features.length + '개 (십자·네모 소켓은 못 찾음):')
  m.features.forEach((f) => L.push('  ' + (f.kind === 'peg' ? '돌기' : '구멍') + (f.through ? '(관통)' : '') + ' ' + f.dir + '  위치 [' + f.center.map(r1).join(', ') + ']  반지름 ' + r1(f.r) + '  ' + (f.kind === 'peg' ? '길이' : '깊이') + ' ' + r1(f.len) + (f.kind === 'hole' ? '  (입구 ' + f.entrance.map(r1).join(', ') + ')' : '')))
  if (hasConn) {
    L.push('')
    L.push('등록된 연결점과 대조: 일치 ' + m.cmp.matched + ' / 차이·없음 ' + m.cmp.differ)
    m.cmp.lines.forEach((l) => L.push('  ' + l))
    if (m.cmp.extra.length) { L.push('  ➕ 실측에는 있는데 등록 안 된 것 ' + m.cmp.extra.length + '개 (장식이면 무시):'); m.cmp.extra.forEach((f) => L.push('     ' + (f.kind === 'peg' ? '돌기' : '구멍') + ' ' + f.dir + ' [' + f.center.map(r1).join(', ') + '] r' + r1(f.r) + ' ' + (f.kind === 'peg' ? '길이' : '깊이') + ' ' + r1(f.len))) }
  } else L.push('\n(등록된 연결점이 없어요 — 위 실측을 보고 set_part_connectors 로 등록)')
  return L.join('\n')
}
