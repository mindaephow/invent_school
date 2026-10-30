// 프로보 커넥트 휠블럭 STL 만들기. 사용: node scripts/make-proboconnect-wheel.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30, 한 단계씩): "휠블럭 만들자" → "지름 50, 높이 20 원기둥" → "지름 48, 높이 1mm 위아래 홈" → "지름 46, 높이 24 원기둥 중심에 합쳐" → "지름 35, 높이 25 원기둥 좌우 중심에 합쳐" → "위쪽 가운데 규격 홀 7개" → "지름 40, 높이 20 원기둥 중심에 홈". 지금 모양 = 지름 50 × 높이 20 원기둥 + 위·아래 면 지름 48 깊이 1 홈 + 가운데 지름 46 × 높이 24 원기둥 + 지름 35 × 높이 25 원기둥(나머지는 이어서 지시받는 대로).
// 좌표: 높이 y(바닥 0), 가운데가 x·z 원점. 등록: node scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기> [색]
import fs from 'node:fs'
import Module from 'manifold-3d'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'
import { PROBO_STD, openPts, roundPoly } from '../app/lib/proboconnect-block-mesh.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-wheel.mjs <저장할 파일.stl>'); process.exit(1) }
const D = 50, H = 20
const wasm = await Module(); wasm.setup()
const cylY = (y0, y1, r) => wasm.Manifold.cylinder(y1 - y0, r, r, 96, false).rotate([-90, 0, 0]).translate([0, y0, 0])   // 높이 방향 y
// 위·아래 면 홈(사용자 2026-10-30 "지름 48, 높이 1mm 위아래 홈파줘"): 지름 48 × 깊이 1 원형 홈을 위·아래 면에 하나씩. 바깥 테두리 두께 1.
const GD = 48, GH = 1
// 가운데 원기둥(사용자 2026-10-30 "지름 46, 높이 24 원기둥 좌우위아래 중심에 합쳐줘"): 지름 46 × 높이 24, 휠 가운데(좌우·위아래)에 한 몸으로 — 높이 20 보다 4 커서 위·아래로 2 씩 나온다. 전체 바닥을 y 0 으로 맞추려고 휠 몸통을 2 올린다.
const HUB_D = 46, HUB_H = 24, Y0 = (HUB_H - H) / 2
const body = wasm.Manifold.difference(wasm.Manifold.difference(cylY(Y0, Y0 + H, D / 2), cylY(Y0 - 1, Y0 + GH, GD / 2)), cylY(Y0 + H - GH, Y0 + H + 1, GD / 2))
// 지름 35 × 높이 25 원기둥(사용자 2026-10-30 "지름 35, 높이 25 원기둥, 좌우 중심에 합쳐줘"): 좌우(x·z) 가운데에 한 몸으로. 위아래 위치는 말씀이 없어 바닥(y 0)에 맞췄다 — 위로 1 더 나온다(⚠ 추정).
const AXLE_D = 35, AXLE_H = 25
const solid = wasm.Manifold.union([body, cylY(0, HUB_H, HUB_D / 2), cylY(0, AXLE_H, AXLE_D / 2)])
// 위쪽 가운데 규격 홀(사용자 2026-10-30 "위쪽 중심에 13홀을 45도 간격으로 중심축으로 돌려가면서 그려줘"): 모터(make-proboconnect-motor.mjs)와 같은 구멍 = 프로보 블럭 규격 홀(입구 + 가운데 띠·턱 + 아래 입구).
//   위 면(지름 35 원기둥 윗면 y 25)에서 5mm(블럭 두께) 깊이. 둘레 반지름 10 = 1X3 줄 간격. 
const S = PROBO_STD, BAND = S.thick, RING = 10, TOP = AXLE_H, E = 0.01
const M = wasm.Manifold
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const extrude = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])   // 2D y → −z
const topHole = (x, z, deg = 0) => {   // 위 면에서 판 규격 홀(모터 hole() 의 위 띠 쪽과 같은 구조). deg = 홀의 띠 방향을 (x,z) 평면에서 돌리는 각(2D 는 z 가 뒤집혀 −deg)
  const th = (-deg * Math.PI) / 180, rot = ([px, py]) => [x + (px - x) * Math.cos(th) - (py + z) * Math.sin(th), -z + (px - x) * Math.sin(th) + (py + z) * Math.cos(th)]
  const band = ccw(roundPoly(openPts(x, -z, S).map(rot), S.round))
  return M.union([cylY(TOP - S.barY0 - E, TOP + 1, S.boreR), extrude(band, TOP - S.barY1 - E, TOP - S.barY0 + E), cylY(TOP - BAND, TOP - S.barY1 + E, S.boreR)].map((m, i) => i === 1 ? m : m.translate([x, 0, z])))
}
//   ("홀이 7개가 되는거야", "가운데도 홀이 있어야해" → 가운데 1 + 1X3 줄을 45° 간격으로 세 방향(0°·45°·90°) 돌린 양끝 홀 6 = 7개)
//   ("45도가 아니라 60도씩이다" → 1X3 줄을 0°·60°·120° 로 돌린 양끝 홀 6개 + 가운데 1개 = 7개. 둘레 반지름 = 줄 간격 10 이라 이웃 홀 사이도 모두 10. 홀의 띠·홈 방향도 줄을 따라 돌린다.)
const holesAt = [[0, 0, 0], ...[0, 60, 120].flatMap((d) => [d, d + 180].map((a) => [RING * Math.cos((a * Math.PI) / 180), RING * Math.sin((a * Math.PI) / 180), d]))]
const ring = M.union(holesAt.map(([x, z, d]) => topHole(x, z, d)))
// 가운데 원기둥 홈(사용자 2026-10-30 "지름40, 높이 20의 원기둥을 중심에 넣고 홈을 파줘"): 지름 40 × 높이 20 원기둥 모양 빈 곳을 가운데에. 위 면에는 홀이 있어서 아래(바닥 y 0)에서 위로 판다 — 위쪽 5mm(y 20~25)가 남아 위 규격 홀(깊이 5)이 아래로 열린다(⚠ 파는 쪽은 추정).
const POCKET_D = 40, POCKET_H = 20
const wheel = M.difference(M.difference(solid, ring), cylY(-1, POCKET_H, POCKET_D / 2))   // 바닥 y 0
const m = wheel.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`휠블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '→', out)
