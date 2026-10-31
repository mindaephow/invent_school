// 꺾인 곳 선 자동 그리기 (사용자 2026-10-31 "꺾인 곳을 찾아서 라인을 그려" → "이 방법 등록해놔 언제든 쓸 수 있게").
// 부품 몸통 삼각형에서 이웃한 두 면이 minAngle(기본 1°) 넘게 꺾이는 모서리를 전부 찾아, 그 모서리 위에 0.1mm 가는 막대로 선을 긋는다.
//   - 위치를 손으로 짐작하지 않는다. 모델이 바뀌어도 다시 돌리면 선이 따라온다.
//   - 벽이 한 면으로 이어진 곳(층 사이·결합된 면)은 꺾이지 않아 모서리가 없으니 선도 없다(사용자 "결합된 곳인데 왜 라인이 있어").
//   - 뷰어가 모서리를 못 그리거나 색으로 구분이 안 될 때 쓴다. 선은 색칠 조각(paint:true)으로 몸통에 얹는다 — 등록 방법은 아래.
//
// 사용(생성기 안에서):
//   import { makeKit } from '../app/lib/cubo-mesh-kit.js'
//   import { addBendLines } from '../app/lib/bend-lines.js'
//   const kit = makeKit(24)
//   const n = addBendLines(kit, tris, { skip: (a, b) => /* 선을 긋지 않을 모서리(예: 안쪽 구멍) */ false })
//   const lineTris = kit.result()           // → STL 로 저장(<이름>_코너선.stl) + 위치 .json {x: 가운데, y: 가장 낮은 곳, z: 가운데}
//   scripts/register-proboconnect-parts.mjs 가 <이름>_코너선.stl/.json 이 있으면 색칠 조각으로 자동으로 붙인다(색은 부품 색 기준 lineColorFor).
// 기준 구현: scripts/make-proboconnect-battery.mjs
import { LINE_THICKNESS } from './robotron-line-color.js'

const key = (p) => p.map((c) => Math.round(c * 1000)).join(',')

// tris: Float32Array(삼각형 수 × 9, 좌표 x·y·z). 반환: [{ a, b, angle }] — 꺾인 모서리(두 삼각형이 만나는 변) 전부.
export function findBendEdges(tris, { minAngle = 1, skip = null } = {}) {
  const edges = new Map(), normals = []
  for (let t = 0; t < tris.length / 9; t++) {
    const q = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]])
    const u = [q[1][0] - q[0][0], q[1][1] - q[0][1], q[1][2] - q[0][2]], w = [q[2][0] - q[0][0], q[2][1] - q[0][1], q[2][2] - q[0][2]]
    let n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
    const nl = Math.hypot(...n) || 1; n = n.map((c) => c / nl); normals.push(n)
    for (let k = 0; k < 3; k++) {
      const a = q[k], b = q[(k + 1) % 3], ka = key(a), kb = key(b), id = ka < kb ? ka + '|' + kb : kb + '|' + ka
      if (!edges.has(id)) edges.set(id, [])
      edges.get(id).push({ t, a, b })
    }
  }
  const out = []
  for (const [, v] of edges) {
    if (v.length !== 2) continue   // 열린 변·겹친 변은 건너뛴다(검사 checkMesh 가 따로 잡는다)
    const n0 = normals[v[0].t], n1 = normals[v[1].t]
    const angle = (Math.acos(Math.max(-1, Math.min(1, n0[0] * n1[0] + n0[1] * n1[1] + n0[2] * n1[2]))) * 180) / Math.PI
    if (angle <= minAngle) continue
    const { a, b } = v[0]
    if (skip && skip(a, b, angle)) continue
    out.push({ a, b, angle })
  }
  return out
}

// 두 점 사이에 가는 삼각 기둥 막대를 kit 에 얹는다(make-robotron-flatplate.mjs 의 outlineBars 와 같은 방식).
export function addBar(kit, a, b, thickness = LINE_THICKNESS) {
  const LT = thickness / 2
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
  const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
  const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
  let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => (c / ul) * LT); const v = cr(e, u)
  const s0 = a.map((c, i) => c - e[i] * LT), s1 = b.map((c, i) => c + e[i] * LT)
  const corner = (q, su, sv) => q.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
  const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
  const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
  for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); kit.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
}

// 꺾인 모서리를 전부 찾아 선을 얹고, 그은 개수를 돌려준다.
export function addBendLines(kit, tris, opts = {}) {
  const edges = findBendEdges(tris, opts)
  for (const { a, b } of edges) addBar(kit, a, b, opts.thickness)
  return edges.length
}
