// 프로보 커넥트 스텝핀 STL 만들기. 사용: node scripts/make-proboconnect-steppin.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30): "스텝핀은 대가리 부분에 톱니에 걸리는 부분이 있다. 길이는 2단핀과 같음(대가리 모습만 다름)".
// = 2단핀(길이 10)과 몸통·다리·발·머리가 같고, 머리 양옆(핀툴 홈 자리)에 뾰족한 걸림 돌기 둘만 더한다(처음 만든 톱니 16개 고리는 "그게 아니고" 로 폐기).
//  · 돌기 끝 반지름은 블럭 톱니 홈(4.3)보다 0.15 작은 4.15, 밑변 반지름 3.4(머리 안쪽), 밑변 폭 1.8, 높이 0.75(머리 아랫반).
// ⚠ 돌기 크기(폭 1.8·높이 0.75)는 추정값이다.
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD } from '../app/lib/proboconnect-block-mesh.js'
import { probo2nPinTriangles } from '../app/lib/proboconnect-pin-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-steppin.mjs <저장할 파일.stl>'); process.exit(1) }
const S = PROBO_STD, wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const solid = (arr) => {
  const t = conformTJunctions(arr), idx = new Map(), verts = [], tri = []
  for (let i = 0; i < t.length; i += 3) { const key = [t[i], t[i + 1], t[i + 2]].map((v) => Math.round(v * 1e4)).join(','); if (!idx.has(key)) { idx.set(key, verts.length / 3); verts.push(t[i], t[i + 1], t[i + 2]) } tri.push(idx.get(key)) }
  return new M(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(verts), triVerts: new Uint32Array(tri) }))
}
const pin = solid(probo2nPinTriangles(2, S, 0))
// 걸림 돌기 둘: 핀툴 홈 자리 양옆(±x)에 시곗바늘처럼 뾰족한 삼각형 하나씩 — 홈 바닥(y −0.75)에 이어 머리 아랫반(y −1.5~−0.75)에 붙고, 끝(반지름 4.15)이 톱니 홈에 걸린다(사용자 지시 2026-10-30 "시곗바늘처럼 양쪽에 두 개만").
const tipR = 4.15, baseR = 3.4, halfW = 0.9
const tri = (s) => [[s * baseR, -halfW], [s * tipR, 0], [s * baseR, halfW]]
const pawl = (s) => M.extrude([s > 0 ? tri(s) : tri(s).reverse()], 0.75).rotate([-90, 0, 0]).translate([0, -1.5, 0])   // 로컬 xy → 핀 좌표(x, z=−y), 높이 0.75 를 y −1.5~−0.75 로
const body = M.union([pin, pawl(1), pawl(-1)])
const m = body.getMesh(), raw = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) raw[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
console.log('합친 직후', JSON.stringify(checkMesh(raw)), '(manifold 결과 자체는 닫힌 몸:', m.numTri, '삼각형)')
const tris = conformTJunctions(raw)
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`스텝핀: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기(x,높이y,z)', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), 'y범위', mn[1], mx[1], '→', out)
