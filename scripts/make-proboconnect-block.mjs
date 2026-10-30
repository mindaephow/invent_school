// 프로보 커넥트 1XN블럭 STL 만들기(삼각형 직접 짜기). 사용: node scripts/make-proboconnect-block.mjs <구멍 수> <저장할 파일.stl>
//   1X5블럭 = 구멍 5개(길이 50 × 폭 10 × 두께 5). 만든 뒤 짝 없는 모서리·부피·삼각형 수를 보고한다(규격: get_part_standard '새 3D 부품을 만들거나 고칠 때 지킬 것').
import fs from 'node:fs'
import Module from 'manifold-3d'
import { probo1xNTriangles, proboBracketPieces } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'

const BR = { L2X2: [2, 1, 1], L2X4: [2, 2, 1, undefined, 15], L6X9: [3, 3, 2, undefined, null, 35], L1X3: [1, 3, 1, undefined, 10, 35, true] }, isL = !!BR[process.argv[2]]   // [줄 수, 바닥 구멍 칸, 벽 구멍 칸, -, 세운 팔 높이(사용자 지시 2026-10-29 "높이 15야", L2X4), 바닥 팔 길이("40이 아니고 35", L6X9)] — L1X3(2026-10-30 "40이 아니고 35", "높이 10", "홀은 왜 없앴어"): 세운 팔 높이 10 에도 벽 구멍 1개는 그대로, 바닥 팔 35
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
  // 모서리 칸이 10 보다 짧아진 쪽(L6X9 바닥 35, L2X4 벽 높이 15)은 블라인드 홀을 반원으로 둔다 — 구멍 중심을 모서리 바깥면(깊이 0 / 높이 0)에 옮기고 바깥으로 나간 반쪽은 잘려, 평평한 면이 바깥면에 오고 둥근 쪽이 안쪽을 향한다(사용자 지시 2026-10-29 "반만 표시", "반대로").
  const inB = M.cube([W + 2, 12, 12], false).translate([-W / 2 - 1, -1, 0]), inK = M.cube([W + 2, 12, 12], false).translate([-W / 2 - 1, 0, -1])   // 깊이 z ≥ 0 / 높이 y ≥ 0 만 남김
  const cavBottomF = M.intersection(P.bottomScale < 1 ? M.intersection(cavBottom0.translate([0, 0, -5]), inB) : cavBottom0, side(45))
  const cavBackF = M.intersection(P.backScale < 1 ? M.intersection(cavBack0.translate([0, -5, 0]), inK) : cavBack0, side(-135))
  // 세운 팔 길이가 10 이하(L1X3)면 팔의 구멍이 블라인드 홀이 아니라 그냥 규격 홀(사용자 2026-10-30 "블라인드 홀이 아니고 그냥 규격홀") — 모서리 블라인드 홀을 넣지 않는다.
  //   이때 바닥 쪽 모서리 블라인드 홀도 같은 칸에서 규격 홀과 겹쳐 같은 방향 겹침 20개가 생기므로(검사로 확인) 함께 뺀다.
  const cavBottom = P.backScale > 0 ? cavBottomF : null, cavBack = P.backScale > 0 ? cavBackF : null
  const cavBase = M.difference(solid(P.baseO), solid(P.base)), cavWall = M.difference(solid(P.wallO), solid(P.wall))   // 뚫린 구멍의 빈 공간
  const body = M.union([solid(P.baseO), solid(P.wallO)])
  let merged = M.difference(M.difference(body, cavBase), cavWall)
  for (const c of [cavBack, cavBottom]) if (c) merged = M.difference(merged, c)
  const toArr = (mf) => { const m = mf.getMesh(), out = new Float32Array(m.triVerts.length * 3); for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) out[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]; return out }
  // 블라인드 홀 안쪽 면(색칠 조각용): 빈 공간 덩어리마다 입구 뚜껑(z=0 또는 y=0 평면의 면)을 빼고, 면 방향을 안쪽(빈 공간 쪽)으로 뒤집고, 덩어리 가운데로 1.5% 줄여 벽에서 살짝 안으로 띄운다.
  const liner = []
  for (const comp of [...(cavBack ? cavBack.decompose() : []), ...(cavBottom ? cavBottom.decompose() : [])]) {
    const t = toArr(comp), bb = comp.boundingBox(), c = [(bb.min[0] + bb.max[0]) / 2, (bb.min[1] + bb.max[1]) / 2, (bb.min[2] + bb.max[2]) / 2]
    for (let i = 0; i < t.length; i += 9) {
      const onPlane = (ax) => Math.abs(t[i + ax]) < 1e-4 && Math.abs(t[i + 3 + ax]) < 1e-4 && Math.abs(t[i + 6 + ax]) < 1e-4
      if (onPlane(2) || onPlane(1)) continue   // 입구 뚜껑(뒤쪽 z=0 / 바닥 y=0)
      const v = (k) => [0, 1, 2].map((a) => c[a] + (t[i + k * 3 + a] - c[a]) * 0.985)
      const [a, b, d] = [v(0), v(2), v(1)]   // 두 점을 맞바꿔 방향 뒤집기
      liner.push(...a, ...b, ...d)
    }
  }
  return { body: toArr(merged), liner: new Float32Array(liner) }
}
const merged = isL ? await mergeBracket(proboBracketPieces(...BR[process.argv[2]])) : null
const tris = isL ? merged.body : conformTJunctions(probo1xNTriangles(n, undefined, rows))
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
console.log(`${isL ? process.argv[2] : rows + 'X' + n}블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '→', out)

if (isL && merged.liner.length) {   // (블라인드 홀이 없는 L1X3 은 안쪽 조각이 없다) 블라인드 홀 안쪽 회색 조각 STL 과, 뷰어가 STL 마다 x·z 가운데·바닥 y=0 으로 옮기는 것을 맞추는 위치(몸통 기준 차이)를 알려 준다.
  const bbox = (a) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < a.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], a[i + k]); mx[k] = Math.max(mx[k], a[i + k]) } return [mn, mx] }
  const [bm, bx] = bbox(tris), [gm, gx] = bbox(merged.liner), dir = out.replace(/[^\/]+$/, '') + '블라인드안쪽/', base = out.split(/[\/]/).pop().replace(/\.stl$/, '')
  fs.mkdirSync(dir, { recursive: true })
  const off = { x: +((gm[0] + gx[0]) / 2 - (bm[0] + bx[0]) / 2).toFixed(4), y: +(gm[1] - bm[1]).toFixed(4), z: +((gm[2] + gx[2]) / 2 - (bm[2] + bx[2]) / 2).toFixed(4) }
  fs.writeFileSync(dir + base + '_블라인드안쪽.stl', trianglesToStl(merged.liner)); fs.writeFileSync(dir + base + '_블라인드안쪽.json', JSON.stringify(off))
  console.log('블라인드 안쪽 조각', merged.liner.length / 9, '삼각형 →', dir + base + '_블라인드안쪽.stl', '위치', JSON.stringify(off))
}
