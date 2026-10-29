// 프로보 커넥트 변환블럭 STL 만들기. 사용: node scripts/make-proboconnect-converter.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30): "좌우는 30, 뒤아래 20, 두께 5, 홀은 4개, 변환블록 찾아서 이미지 보고 만들어봐".
// 교재 2권 부품 그림(변환블럭): 흰색 납작한 블럭, 구멍 4개가 **십자(마름모)** 로 놓이고(사용자 "구멍 4개가 십자 형태를 이루고 있어"), 구멍 안쪽에 톱니가 보인다 → 프로보 블럭의 톱니 입구 구멍(toothPts)으로 만든다.
// 근거: 그림 속 네 구멍 중심의 두 대각선이 서로 한가운데에서 만나고 길이 비율이 약 2:1 → 가로 대각선 20(왼쪽·오른쪽 구멍), 세로 대각선 10(뒤·앞 구멍). 이때 그림이 가로·세로 축 길이가 비슷한 보통 등각 시점이 된다.
//   (처음에 구멍 4개를 지그재그 "Z"로 읽은 것은 틀렸다 — 같은 네 점이 평행사변형으로 보여서 구분이 안 됐다.)
// 구멍 중심(가운데 0): 왼쪽 (−10, 0)·오른쪽 (+10, 0)·뒤 (0, −5)·앞 (0, +5). 바깥 크기 가로 30 × 앞뒤 20 × 두께 5. 윤곽 = 구멍마다 반지름 5 원판 + 가운데 가로 띠(x ±10, z ±5).
// ⚠ 추정: 가운데 띠의 모양(오목한 모서리)은 그림에서 대략 읽은 것. 구멍 구조는 프로보 블럭 규격(PROBO_STD) 그대로(책에 치수 없음).
// 좌표: 가로 x(가운데 0), 두께 y(바닥 0~5), 앞뒤 z.
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, openPts, roundPoly, toothPts, circlePtsC } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-converter.mjs <저장할 파일.stl>'); process.exit(1) }
const S = PROBO_STD, T = S.thick, R = 5
const HOLES3D = [[-10, 0], [10, 0], [0, -5], [0, 5]]                           // [x, z] — 십자
const H2 = HOLES3D.map(([x, z]) => [x, -z])                                    // 평면 2D 의 y 는 −z 로 간다(extrude 규칙)
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const extrude = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])
const rect = (x0, x1, y0, y1) => extrude(ccw([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]), 0, T)
// 몸통: 구멍마다 원판 + 가운데 가로 띠(왼쪽·오른쪽 구멍 사이를 메우고 뒤·앞 구멍 둘레와 겹친다)
let body = M.union([...H2.map((c) => extrude(ccw(circlePtsC(c[0], c[1], R, 48)), 0, T)), rect(-10, 10, -R, R)])
// 구멍: 아래 둥근 입구 + 가운데 띠 + 위 톱니 입구(프로보 블럭 구멍과 같은 구조)
for (const c of H2) {
  const cav = [
    M.cylinder(S.barY0 + 1, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([c[0], -1, -c[1]]),
    extrude(ccw(toothPts(c[0], c[1], S)), S.barY1, T + 1),
    extrude(ccw(roundPoly(openPts(c[0], c[1], S), S.round)), S.barY0 - 0.01, S.barY1 + 0.01),
  ]
  body = M.difference(body, M.union(cav))
}
const m = body.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`변환블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기 x,y,z', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '범위 x', mn[0].toFixed(1), mx[0].toFixed(1), 'z', mn[2].toFixed(1), mx[2].toFixed(1), '→', out)
