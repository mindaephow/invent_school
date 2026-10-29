// 프로보 커넥트 톱니블럭 STL 만들기. 사용: node scripts/make-proboconnect-gear.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30): "톱니블럭 (그레이) 원 46 두께 5 톱니 12", "중심 원 32 두께 10", "1X3블럭처럼 홀이 뚫림", "10짜리 원형과 합치면 중심을 맞춰야지".
// 교재 4권 66쪽 부품표 그림(톱니블럭 4개 / 4권 신규 6개)과 57쪽 7번 단계 그림: 톱니는 끝이 좁아지는 둥근 사다리꼴, 가운데에 허브 테두리가 있고 구멍은 가운데 1개 + 둘레 6개.
// 규격: 톱니 판 두께 5(톱니 끝 지름 46, 톱니 12개, 톱니는 46 원에서 5mm 깊이로 파인다 = 골 지름 36 — 사용자 지시 2026-10-30 "톱니가 5mm정도는 파여야해"), 가운데 허브 지름 32·두께 10(판과 중심이 같아 위·아래로 2.5씩 나온다), 구멍은 프로보 블럭 구멍(proboconnect-block-mesh.js PROBO_STD: 입구 반지름 3.95 + 가운데 띠·사다리꼴 홈)을 허브 두께 10에 맞춰 위·아래 입구로 만든다.
// 구멍 배치: 이웃 구멍 사이가 블럭 간격 10 이 되도록 가운데 1 + 반지름 10 둘레 6(60°). (45° 8개는 간격 7.65 라 구멍 지름 7.9 가 서로 겹쳐서 만들 수 없다.)
// 좌표: 축 y(바닥 0, 위 +10), 판은 y 2.5~7.5.
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, openPts, roundPoly } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-gear.mjs <저장할 파일.stl>'); process.exit(1) }
const G = { rootR: 18, tipR: 23, teeth: 12, hubR: 16, hubH: 10, plateH: 5, ringR: 10, ringN: 6 }
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const deg = (d) => (d * Math.PI) / 180

// 톱니 윤곽(반시계): 톱니마다 뿌리 폭 20° → 끝 폭 10°, 골 폭 10°(톱니 하나 = 30°). 꼭짓점은 둥글게.
const pts = []
for (let k = 0; k < G.teeth; k++) {
  const a = (k * 2 * Math.PI) / G.teeth
  for (const [d, r] of [[-10, G.rootR], [-5, G.tipR], [5, G.tipR], [10, G.rootR]]) pts.push([r * Math.cos(a + deg(d)), r * Math.sin(a + deg(d))])
}
const outline = roundPoly(pts, 1.0, 4, 20)
const H = (y0, y1) => y1 - y0
const extrude = (poly, y0, y1) => M.extrude([poly], H(y0, y1)).rotate([-90, 0, 0]).translate([0, y0, 0])   // 2D 의 y 가 -z 로 간다(대칭이라 상관없다)

const plateY0 = (G.hubH - G.plateH) / 2, plateY1 = plateY0 + G.plateH
let body = M.union([extrude(outline, plateY0, plateY1), M.cylinder(G.hubH, G.hubR, G.hubR, 64, false).rotate([-90, 0, 0])])

// 구멍(프로보 블럭 구멍): 아래·위 둥근 입구 + 가운데 띠(턱 층)의 뚫린 부분. 허브 두께 10 에서는 띠 층을 가운데에 둔다.
const S = PROBO_STD, barY0 = (G.hubH - (S.barY1 - S.barY0)) / 2, barY1 = barY0 + (S.barY1 - S.barY0)
const holes = [[0, 0]]
for (let k = 0; k < G.ringN; k++) holes.push([G.ringR * Math.cos((k * 2 * Math.PI) / G.ringN), G.ringR * Math.sin((k * 2 * Math.PI) / G.ringN)])
const bore = (x, z) => M.cylinder(G.hubH + 2, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([x, -1, z])
for (const [x, z] of holes) {
  const cav = [M.cylinder(barY0 + 1, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([x, -1, z]), M.cylinder(G.hubH - barY1 + 1, S.boreR, S.boreR, 48, false).rotate([-90, 0, 0]).translate([x, barY1, z])]
  const open = roundPoly(openPts(x, z, S), S.round).map(([px, pz]) => [px, -pz]).reverse()   // 2D 의 y 가 -z 로 가므로 미리 뒤집고(뒤집으면 시계 방향이 되니 순서도 되돌린다)
  cav.push(extrude(open, barY0 - 0.01, barY1 + 0.01))
  body = M.difference(body, M.union(cav))
}
const m = body.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`톱니블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기 x,y,z', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), 'y범위', mn[1].toFixed(2), mx[1].toFixed(2), '→', out)
