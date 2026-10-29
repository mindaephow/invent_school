// 프로보 커넥트 힌지블럭A STL 만들기. 사용: node scripts/make-proboconnect-hinge.mjs <저장할 파일.stl>
// 책 핀 조립법4(17쪽)·조립미션4(18쪽) 그림 + 사용자 지시(2026-10-30): 힌지블럭 두 개를 고리끼리 스텝핀으로 이으면 길이가 15블록(50)과 같다.
//  · 한쪽 끝 구멍(x 5)은 톱니 구멍, 가운데(x 15)는 둥근 구멍, 반대쪽(x 25)에 세운 고리(지름 10, 폭 5)가 있고 고리 옆면에 톱니 구멍이 뚫려 있다.
//  · 두 개를 고리 자리(x 25)에서 맞추면 한 개는 x 0~30, 다른 하나는 x 20~50 → 합쳐서 50.
// 좌표: 길이 x, 높이(두께) y(바닥 0), 폭 z(가운데 0). 판 두께 5, 폭 10. 고리는 z 0~5 쪽(반폭), 판은 고리 쪽에서 반폭(z 0~5)으로 이어진다.
// ⚠ 고리 높이·위치(고리 가운데 y 5)는 그림에서 비율만 읽은 추정이다.
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, plateTriangles } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-hinge.mjs <저장할 파일.stl>'); process.exit(1) }
const S = PROBO_STD, wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const solid = (arr) => {
  const t = conformTJunctions(arr), idx = new Map(), verts = [], tri = []
  for (let i = 0; i < t.length; i += 3) { const key = [t[i], t[i + 1], t[i + 2]].map((v) => Math.round(v * 1e4)).join(','); if (!idx.has(key)) { idx.set(key, verts.length / 3); verts.push(t[i], t[i + 1], t[i + 2]) } tri.push(idx.get(key)) }
  return new M(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(verts), triVerts: new Uint32Array(tri) }))
}
// 판(x 0~20, 폭 10): 왼쪽 끝은 반지름 5 로 둥글게(구멍 가운데 x 5), 오른쪽은 각지게(고리 쪽 반폭 판과 이어짐)
const outline = [[20, -5], [20, 5]]
for (let i = 0; i <= 12; i++) { const a = Math.PI / 2 + (Math.PI * i) / 12; outline.push([5 + 5 * Math.cos(a), 5 * Math.sin(a)]) }
const plate = solid(plateTriangles(outline, [{ c: 5, z: 0, tooth: true }, { c: 15, z: 0 }], S))
// 고리 쪽 반폭 판(x 20~25, z 0~5, 두께 5)과 고리(가운데 x 25 y 5, 반지름 5, 폭 z 0~5, 축 z)
const half = M.cube([5, 5, 5], false).translate([20, 0, 0])
const ring = M.cylinder(5, 5, 5, 48, true).translate([25, 5, 2.5])   // manifold 기둥은 축이 z — 폭 z 0~5
// 고리 옆면 구멍(스텝핀 자리) = 1번 홀(톱니 구멍)과 똑같은 구조(톱니 입구 → 턱 → 아래 빈 곳): 10×10×5 판에 톱니 구멍을 하나 뚫고 그 빈 공간을 뽑아서(상자 − 판), 고리 가운데에 축이 z 가 되게 눕혀 뺀다. 입구(톱니)는 바깥 면 z=5, 반대쪽 z=0 은 뚫림.
const cell = plateTriangles([[-5, -5], [5, -5], [5, 5], [-5, 5]], [{ c: 0, z: 0, tooth: true }], S)
const cavity = M.difference(M.cube([10, 5, 10], false).translate([-5, 0, -5]), solid(cell))
const hole = cavity.transform([1, 0, 0, 0,  0, 0, 1, 0,  0, -1, 0, 0,  25, 5, 0, 1])   // (u,v,t) → (x=u+25, y=5−t, z=v), 4×4 열 우선
let body = M.difference(M.union([plate, half, ring]), hole)
if (process.argv[3] === 'mirror') body = body.mirror([0, 0, 1])   // 폭 방향(z)을 뒤집어 반대쪽 고리
const m = body.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`힌지블럭${process.argv[3] === 'mirror' ? 'A' : 'B'}: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기(길이,높이,폭)', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '→', out)
