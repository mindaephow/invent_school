// 프로보 커넥트 삼각블럭 STL 만들기. 사용: node scripts/make-proboconnect-triangle.mjs <저장할 파일.stl>
// 교재 2권 부품 그림(삼각블럭): 파란색 납작한 정삼각형 비슷한 블럭, 모서리는 둥글고, 큰 구멍 6개가 3-2-1 줄로 놓인다(윗줄 3·가운데줄 2·아래 꼭짓점 1).
//   세 모서리 구멍은 톱니 입구(스텝핀이 걸리는 구멍), 나머지 세 구멍(윗줄 가운데·가운데줄 2개)은 둥근 입구. 큰 구멍 사이에 작은 둥근 홈 3개(윗줄 사이 2·가운데줄 사이 1).
// ⚠ 추정(그림에 치수 없음): 구멍 간격 10(프로보 블럭 규격)의 정삼각형 → 구멍 중심 삼각형 한 변 20(높이 17.32), 모서리 구멍 둘레 반지름 5 → 바깥 가로 30 × 앞뒤 27.3, 두께 5. 작은 홈은 반지름 0.6~0.8·깊이 1.
// 좌표: 가로 x, 두께 y(바닥 0~5), 앞뒤 z(꼭짓점이 +z). 구멍 중심: 윗줄 (−10·0·10, −8.66), 가운데줄 (−5·5, 0), 꼭짓점 (0, +8.66).
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, openPts, roundPoly, toothPts } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-triangle.mjs <저장할 파일.stl>'); process.exit(1) }
const S = PROBO_STD, T = S.thick, R = 5, ROW = 10 * Math.sqrt(3) / 2   // 줄 간격 8.66
const CORNERS = [[-10, -ROW], [10, -ROW], [0, ROW]]                     // [x, z] 톱니 구멍(모서리)
const PLAIN = [[0, -ROW], [-5, 0], [5, 0]]                              // 둥근 구멍
const DIMPLES = [[-4.83, -ROW, 0.6], [4.83, -ROW, 0.6], [0, 0, 0.8]]    // 작은 홈 [x, z, 반지름]
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const extrude = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])   // 2D y → −z
const cyl = (x, z, r, h, y0) => M.cylinder(h, r, r, 48, false).rotate([-90, 0, 0]).translate([x, y0, z])
// 몸통: 세 모서리 원판의 볼록 껍질(둥근 모서리의 삼각형)
let body = M.hull(CORNERS.map(([x, z]) => cyl(x, z, R, T, 0)))
const cav = (x, z, tooth) => {                                          // 구멍: 아래 둥근 입구 + 가운데 띠 + 위(톱니 또는 둥근) 입구
  const c2 = [x, -z]
  return M.union([
    cyl(x, z, S.boreR, S.barY0 + 1, -1),
    tooth ? extrude(ccw(toothPts(c2[0], c2[1], S)), S.barY1, T + 1) : cyl(x, z, S.boreR, T - S.barY1 + 1, S.barY1),
    extrude(ccw(roundPoly(openPts(c2[0], c2[1], S), S.round)), S.barY0 - 0.01, S.barY1 + 0.01),
  ])
}
for (const [x, z] of CORNERS) body = M.difference(body, cav(x, z, true))
for (const [x, z] of PLAIN) body = M.difference(body, cav(x, z, false))
for (const [x, z, r] of DIMPLES) body = M.difference(body, cyl(x, z, r, 1.5, T - 1))   // 윗면 작은 홈(깊이 1)
const m = body.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`삼각블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기 x,y,z', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '→', out)
