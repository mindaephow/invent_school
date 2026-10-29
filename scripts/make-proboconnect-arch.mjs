// 프로보 커넥트 아치블럭 STL 만들기. 사용: node scripts/make-proboconnect-arch.mjs <저장할 파일.stl> [ring]   (ring 을 주면 4개를 돌려 붙인 고리도 검사한다)
// 교재 근거: 4권 25~26쪽(버킷굴착기 9번)·2권 85쪽(레이저건 11번) — 아치블럭 4개를 듀얼핀 8개로 이어 고리 하나를 만든다.
// 한 개 = 4분의 1 원호: 구멍 9개(0°~102.9°), 양 끝 두 구멍씩 이웃과 겹친다. 겹치는 끝은 한쪽만 얇게(두께 2.5) 파여서 포개진다 — 시작 쪽은 위 반쪽이, 끝 쪽은 아래 반쪽이 없다(똑같은 부품 4개가 돌려 붙는다).
// ⚠ 추정: 폭 10·두께 5(프로보 블럭과 같음), 끝은 반지름 5 로 둥글게, 구멍은 프로보 블럭 구멍(PROBO_STD)을 중심선 접선 방향 띠로. 책에 치수는 없다.
// 좌표: 위에서 본 평면 x,z(고리 가운데가 원점), 두께 y(바닥 0~5). 구멍 0 번이 +x 축 위.
import fs from 'node:fs'
import Module from 'manifold-3d'
const TOOTH_HOLES = [1, 5, 9]
import { PROBO_STD, openPts, roundPoly, toothPts } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2], ringTest = process.argv[3] === 'ring'
if (!out) { console.error('사용: node scripts/make-proboconnect-arch.mjs <저장할 파일.stl> [ring]'); process.exit(1) }
// 유추(사용자 2026-10-30 "아치블록은 3X8 블록하고 맞춰 본다(80×30)", "홀이 9개이고 1번과 9번 길이가 1X8 과 같음(구멍 중심 70)", "유추를 해보라고"):
const HOLES = 9, OVERLAP = 3
// 3X8 블럭(80×30, 구멍 8열×3줄, 간격 10) 위에 놓았을 때(사용자 "18과 위치 맞춰 결합", "완전 맞추는 게 아니고 조금 아래여야 하는데"):
//  · 1번·9번 구멍 = 맨 아래 줄 양 끝 구멍(직선 거리 70, 1X8 의 끝 구멍과도 같다)
//  · 5번(가운데) 구멍 = 맨 위 줄 구멍 높이보다 조금(SAG 가 20 이면 딱 맞음, 지금 18 → 2mm 아래) 낮게 → 호의 높이 SAG, 현 70 → tan(θ/4) = SAG/35, 반지름 = 35 / sin(θ/2)
// 바깥 크기: 좌우 80 × 앞뒤 SAG+10. 구멍 간격이 곧은 블럭(10)에 가까울수록 좋다(SAG 18 → 직선 10.2).
const SAG = 18
const THETA = 4 * Math.atan(SAG / 35)                                      // 아치 전체 각도(1번~9번)
const STEP = ((THETA * 180) / Math.PI) / (HOLES - 1)
const A = { R: 35 / Math.sin(THETA / 2), width: 10, thick: 5, holes: HOLES, stepDeg: STEP, endR: 5 }
{ const c1 = [A.R, 0], c9 = [A.R * Math.cos(((HOLES - 1) * STEP * Math.PI) / 180), A.R * Math.sin(((HOLES - 1) * STEP * Math.PI) / 180)]; console.log('1번~9번 구멍 중심 직선 거리', Math.hypot(c9[0] - c1[0], c9[1] - c1[1]).toFixed(2), '이웃 구멍 직선 간격', (2 * A.R * Math.sin((STEP * Math.PI) / 360)).toFixed(3), '반지름', A.R.toFixed(2)) }
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const deg = (d) => (d * Math.PI) / 180
const S = PROBO_STD
const at = (r, a) => [r * Math.cos(deg(a)), r * Math.sin(deg(a))]
const lastDeg = (A.holes - 1) * A.stepDeg                                       // 102.86
const extrude = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])   // 평면 2D 의 y → -z (아래에서 구멍 위치도 같은 규칙으로 뒤집는다)
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const flip = (p) => [p[0], -p[1]]
// 원호 띠(안 R−5, 바깥 R+5, a0°~a1°): 바깥 호 → 안쪽 호 거꾸로
const band = (a0, a1, r0, r1, n = 36) => {
  const o = [], i = []
  for (let k = 0; k <= n; k++) { const a = a0 + ((a1 - a0) * k) / n; o.push(at(r1, a)); i.push(at(r0, a)) }
  return o.concat(i.reverse())
}
const ci = (c, r, n = 32) => Array.from({ length: n }, (_, k) => [c[0] + r * Math.cos((2 * Math.PI * k) / n), c[1] + r * Math.sin((2 * Math.PI * k) / n)])
const R0 = A.R - A.width / 2, R1 = A.R + A.width / 2
// 몸통: 원호 띠 + 양 끝 둥근 마개
// 끝은 반지름 5 반원. 가로 79.6(사용자 "좌우 80" 과 맞음), 높이 26.8 — 구멍 9개·간격 10 이면 80 과 30 을 동시에 만족하는 반지름이 없다(가로 80 이면 높이 26.8, 높이 30 이면 가로 약 70).
let body = M.union([extrude(ccw(band(0, lastDeg, R0, R1)), 0, A.thick), extrude(ccw(ci(at(A.R, 0), A.endR)), 0, A.thick), extrude(ccw(ci(at(A.R, lastDeg), A.endR)), 0, A.thick)])
// 포개지는 끝 두 칸: 시작(0°~22.5° 쪽)은 위 반쪽, 끝(82.5°~ 쪽)은 아래 반쪽을 걷어 낸다.
const half = A.thick / 2
const startCut = extrude(ccw(band(-30, (OVERLAP - 0.5) * A.stepDeg, R0 - 2, R1 + 2)), half, A.thick + 1)
const endCut = extrude(ccw(band(lastDeg - (OVERLAP - 0.5) * A.stepDeg, lastDeg + 30, R0 - 2, R1 + 2)), -1, half)
// 사용자 "병신같이 만들었으면 수정해": 양 끝 반쪽 단차는 근거 없이 넣은 것이라 쓰지 않는다 — 전체 두께 5 통짜. (startCut·endCut 은 만들기만 하고 빼지 않는다. 고리 검사의 겹침 부피는 이제 이웃 끝이 겹치는 만큼 나온다.)
void startCut; void endCut
// 구멍: 프로보 블럭 구멍(아래·위 둥근 입구 + 가운데 띠). 띠는 중심선 접선 방향.
const rot = (p, c, a) => { const dx = p[0] - c[0], dz = p[1] - c[1], s = Math.sin(a), co = Math.cos(a); return [c[0] + dx * co - dz * s, c[1] + dx * s + dz * co] }
for (let k = 0; k < A.holes; k++) {
  const ang = k * A.stepDeg, c = at(A.R, ang)
  const cz = flip(c)                                                      // 3D 에서의 (x, z)
  const toothed = TOOTH_HOLES.includes(k + 1)                              // 사용자: 1·5·9번 홀은 톱니 모양 홀(스텝핀이 딸깍딸깍 걸리는 입구, 1XN블럭의 끝 구멍과 같은 모양)
  const cav = [
    M.cylinder(S.barY0 + 1, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([c[0], -1, cz[1]]),
    toothed ? extrude(ccw(toothPts(c[0], c[1], S)), S.barY1, A.thick + 1) : M.cylinder(A.thick - S.barY1 + 1, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([c[0], S.barY1, cz[1]]),
  ]
  const open = roundPoly(openPts(c[0], c[1], S), S.round).map((p) => rot(p, c, deg(ang + 90)))
  cav.push(extrude(ccw(open), S.barY0 - 0.01, S.barY1 + 0.01))
  body = M.difference(body, M.union(cav))
}
const toArr = (mf) => { const m = mf.getMesh(), t = new Float32Array(m.triVerts.length * 3); for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) t[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]; return t }
// 저장은 가운데 구멍(5번)이 +z 쪽 위(화면 위)로 오게 돌려 좌우 대칭으로 놓는다(아치 모양). 고리 검사는 돌리기 전 몸통으로 한다.
// 눕혀서 만든다(사용자 "눕혀서 만들면 되잖아"): 바닥에 평평히 놓고, 위에서 보면 ∩ 모양(좌우 약 76 · 앞뒤 높이 약 29), 두께 5 는 위아래(y).
const placed = body.rotate([0, 90 - lastDeg / 2, 0])
const tris = toArr(placed), stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`아치블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '범위 x', mn[0].toFixed(1), mx[0].toFixed(1), 'y', mn[1].toFixed(1), mx[1].toFixed(1), 'z', mn[2].toFixed(1), mx[2].toFixed(1), '→', out)
if (ringTest) {   // 4개를 90° 씩 돌려 붙여 겹침(부피)과 고리 닫힘을 본다. 평면 2D 의 y 가 -z 이므로 y 축(수직) 둘레로 돌린다.
  const rings = [0, 1, 2, 3].map((k) => body.rotate([0, -90 * k, 0]))
  let overlap = 0
  for (let i = 0; i < 4; i++) for (let j = i + 1; j < 4; j++) overlap += M.intersection(rings[i], rings[j]).volume()
  const total = M.union(rings)
  console.log('고리 검사: 4개 합친 부피', total.volume().toFixed(1), '= 한 개 부피×4 −겹침', (4 * body.volume()).toFixed(1), '겹침 부피(서로 파고듦)', overlap.toFixed(2), '(0 에 가까워야 한다)')
  const bb = total.boundingBox(); console.log('고리 바깥 크기', (bb.max[0] - bb.min[0]).toFixed(1), '×', (bb.max[2] - bb.min[2]).toFixed(1), '높이', (bb.max[1] - bb.min[1]).toFixed(1))
}
