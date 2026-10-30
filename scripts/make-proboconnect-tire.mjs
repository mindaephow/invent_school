// 프로보 커넥트 타이어 STL 만들기. 사용: node scripts/make-proboconnect-tire.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30): "타이어 먼저 만들자" → "휠블럭에 끼워지는 타이어야" → "타이어(블랙) 지름 53, 두께 24". 지금 모양 = 바깥 지름 53 × 안쪽 지름 46 × 두께(높이) 24 링 + 안쪽 가운데 지름 50 × 높이 20 홈(휠블럭 몸통 자리) + 바깥 가로 홈 무늬 36개.
// 안쪽 지름 46(사용자 "안쪽 지름은 그것보다 안쪽 원이야" → 42 → 마지막에 "46"). 색 블랙 = #555555(로버트론 블랙과 같은 값).
// 좌표: 높이 y(바닥 0), 가운데가 x·z 원점. 등록: node scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기> #555555
import fs from 'node:fs'
import path from 'node:path'
import Module from 'manifold-3d'
import { trianglesToStl, makeKit } from '../app/lib/cubo-mesh-kit.js'
import { LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-tire.mjs <저장할 파일.stl>'); process.exit(1) }
const OUT_D = 53, IN_D = 46, T = 24
const wasm = await Module(); wasm.setup()
const cylY = (y0, y1, r) => wasm.Manifold.cylinder(y1 - y0, r, r, 96, false).rotate([-90, 0, 0]).translate([0, y0, 0])
// 안쪽 홈(사용자 "휠블럭에 들어가려면 안쪽이 파져있어야 하지 않아?"): 휠블럭 몸통(지름 50 × 높이 20)이 들어가도록 안쪽 가운데에 지름 50 × 높이 20 홈을 판다 — 위·아래 (24−20)/2 = 2mm 는 지름 46 입구(휠블럭 가운데 원기둥 지름 46 × 높이 24 에 걸린다). 홈 자리의 벽 두께 (53−50)/2 = 1.5.
const GROOVE_D = 50, GROOVE_H = 20, GZ = (T - GROOVE_H) / 2
const ring = wasm.Manifold.difference(wasm.Manifold.difference(cylY(0, T, OUT_D / 2), cylY(-1, T + 1, IN_D / 2)), cylY(GZ, GZ + GROOVE_H, GROOVE_D / 2))
// 바깥 무늬(사용자 "타이어에 무늬가 아무것도 없어" → "뭐든 넣어봐"): 가로 홈 — 바깥 둘레에 홈 36개(10° 간격), 폭 1 × 깊이 1, 두께(높이) 전체를 가로질러 판다(⚠ 무늬 모양·개수는 추정).
const TREAD_N = 36, TREAD_W = 1, TREAD_DEPTH = 1
const notch = wasm.Manifold.cube([TREAD_DEPTH + 1, T + 2, TREAD_W], false).translate([OUT_D / 2 - TREAD_DEPTH, -1, -TREAD_W / 2])   // +x 쪽 한 개
const tire = wasm.Manifold.difference(ring, wasm.Manifold.union(Array.from({ length: TREAD_N }, (_, k) => notch.rotate([0, (360 / TREAD_N) * k, 0]))))
const m = tire.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`타이어: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '→', out)

// 홈 가장자리 선(사용자 "옆에 아무것도 안 보인다고"): 바퀴처럼 타이어가 색칠 조각(paint)이면 뷰어가 모서리 선을 안 그려서 바깥 홈이 평평한 한 색으로 뭉개진다 →
//   홈마다 양쪽 가장자리를 두께 방향 전체로 0.1mm 선으로 긋는다(make-proboconnect-motor.mjs 와 같은 가는 막대, 밝기 대비 색 lineColorFor). 별도 STL(타이어_선.stl)과 위치(.json) — add-proboconnect-wheel-assembly.mjs 가 쓴다.
{
  const LT = LINE_THICKNESS / 2, kit = makeKit(24)
  const bar = (a, b) => {
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => (c / ul) * LT); const v = cr(e, u).map((c) => c / LT * LT)
    const s0 = a.map((c, i) => c - e[i] * LT), s1 = b.map((c, i) => c + e[i] * LT)
    const corner = (q, su, sv) => q.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, mm = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); kit.quad(A[i], A[j], B[j], B[i], mm[0], mm[1], mm[2]) }
  }
  const R = OUT_D / 2 + 0.03, lx = Math.sqrt(R * R - (TREAD_W / 2) ** 2)
  for (let k = 0; k < TREAD_N; k++) {
    const th = (2 * Math.PI * k) / TREAD_N, c = Math.cos(th), s = Math.sin(th)
    for (const lz of [-TREAD_W / 2, TREAD_W / 2]) { const x = lx * c + lz * s, z = -lx * s + lz * c; bar([x, 0, z], [x, T, z]) }   // manifold rotate([0,deg,0]) 와 같은 방향
  }
  const lt = kit.result(), lmn = [1e9, 1e9, 1e9], lmx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < lt.length; i += 3) for (let k = 0; k < 3; k++) { lmn[k] = Math.min(lmn[k], lt[i + k]); lmx[k] = Math.max(lmx[k], lt[i + k]) }
  const lineFile = path.join(path.dirname(out), '타이어_선.stl')
  fs.writeFileSync(lineFile, trianglesToStl(lt)); fs.writeFileSync(lineFile.replace(/\.stl$/, '.json'), JSON.stringify({ x: +((lmn[0] + lmx[0]) / 2).toFixed(4), y: +lmn[1].toFixed(4), z: +((lmn[2] + lmx[2]) / 2).toFixed(4) }))
  console.log(`타이어 홈 선: 삼각형 ${lt.length / 9}개 →`, lineFile)
}
