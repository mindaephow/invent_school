// 프로보 커넥트 1XN블럭 STL 만들기(삼각형 직접 짜기). 사용: node scripts/make-proboconnect-block.mjs <구멍 수> <저장할 파일.stl>
//   1X5블럭 = 구멍 5개(길이 50 × 폭 10 × 두께 5). 만든 뒤 짝 없는 모서리·부피·삼각형 수를 보고한다(규격: get_part_standard '새 3D 부품을 만들거나 고칠 때 지킬 것').
import fs from 'node:fs'
import Module from 'manifold-3d'
import { probo1xNTriangles, proboBracketPieces } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'

const BR = { L2X2: [2, 1, 1], L2X4: [2, 2, 1], L6X9: [3, 3, 2] }, isL = !!BR[process.argv[2]]
const n = isL ? 0 : Number(process.argv[2]), out = process.argv[3], rows = Number(process.argv[4] || 1)
if (!out || (!isL && (!Number.isInteger(n) || n < 1 || n > 19))) { console.error('사용: node scripts/make-proboconnect-block.mjs <구멍 수 1~19> <저장할 파일.stl> [줄 수=1]'); process.exit(1) }
// 꺽쇠: 바닥 판·세운 판·모서리 칸 상자를 합치고, 모서리 칸의 두 블라인드 홀(빈 공간)을 빼서 한 몸으로 만든다(이음매·겹침 없음).
async function mergeBracket(P) {
  const wasm = await Module(); wasm.setup()
  const solid = (arr) => {
    const t = conformTJunctions(arr), idx = new Map(), verts = [], tri = []
    for (let i = 0; i < t.length; i += 3) { const key = [t[i], t[i + 1], t[i + 2]].map((v) => Math.round(v * 1e4)).join(','); if (!idx.has(key)) { idx.set(key, verts.length / 3); verts.push(t[i], t[i + 1], t[i + 2]) } tri.push(idx.get(key)) }
    return new wasm.Manifold(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(verts), triVerts: new Uint32Array(tri) }))
  }
  const W = P.width, M = wasm.Manifold
  const kBack = M.cube([W, 10, 5], false).translate([-W / 2, 0, 0]), kBottom = M.cube([W, 5, 10], false).translate([-W / 2, 0, 0])
  const cavBack0 = M.difference(kBack, solid(P.back)), cavBottom0 = M.difference(kBottom, solid(P.bottom))   // 블라인드 홀의 빈 공간(둘 다 온전한 둥근 구멍)
  // 두 홀은 모서리 칸 안에서 겹치므로, 안쪽을 대각선(y=z)으로 갈라 얇은 벽(두께 0.57)을 남긴다 — 입구는 둘 다 온전한 원이고 서로 뚫리지 않는다(사용자 지시: 바닥도 뒤쪽과 동일하게, 안 뚫리게).
  const side = (rotX) => M.cube([W + 4, 40, 20], false).translate([-W / 2 - 2, -20, 0.2828]).rotate([rotX, 0, 0])
  const cavBottom = M.intersection(cavBottom0, side(45)), cavBack = M.intersection(cavBack0, side(-135))
  const body = M.union([solid(P.base), solid(P.wall), kBack, kBottom])
  const merged = M.difference(M.difference(body, cavBack), cavBottom), m = merged.getMesh(), out = new Float32Array(m.triVerts.length * 3)
  for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) out[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
  return out
}
const tris = isL ? await mergeBracket(proboBracketPieces(...BR[process.argv[2]])) : conformTJunctions(probo1xNTriangles(n, undefined, rows))
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
console.log(`${isL ? process.argv[2] : rows + 'X' + n}블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '→', out)
