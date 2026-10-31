// 프로보 커넥트 배터리블럭 STL 만들기. 사용: node scripts/make-proboconnect-battery.mjs <저장할 파일.stl> [--column]
// 사용자 지시(2026-10-30): "배터리 블록 만들 거야, 50, 70, 높이 15, 아래 5mm => 57블록 홀". 지금 모양 = 가로 70 × 세로 50 × 높이 15 (--column 이면 위 사각기둥 25×70(전체 20)·50×60(전체 25)을 합쳐 전체 높이 25) —
//   아래 5mm 는 5X7블럭(구멍 5×7 = 35개, probo1xNTriangles(7, S, 5) 그대로) + 위 10mm 는 같은 윤곽(roundRectPts(7, 5))의 몸통. 나머지(윗면 무늬·단자 등)는 이어서 지시받는 대로.
// 좌표: 길이 x 70(가운데 0), 높이 y(바닥 0), 폭 z 50. 아래 블럭·몸통을 manifold-3d 로 한 몸으로 합친다(make-proboconnect-sensor.mjs 의 아래 블럭 + 몸통과 같은 방식).
// 등록: node scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기> [색]
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, probo1xNTriangles, roundRectPts, openPts, roundPoly } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl, makeKit } from '../app/lib/cubo-mesh-kit.js'
import { addBendLines } from '../app/lib/bend-lines.js'
import { conformTJunctions, checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-battery.mjs <저장할 파일.stl> [--column]'); process.exit(1) }
const S = PROBO_STD, BLOCK = S.thick, TOTAL = 15, OVER = process.argv.includes('--shrink') ? 0.02 : 0   // 겹침 0: 층을 줄이지 않을 때는 아래 블럭 안으로 파고들지 않고 면만 맞댄다
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const solid = (arr) => {   // 삼각형 목록 → manifold (꼭짓점 합치기)
  const t = conformTJunctions(arr), idx = new Map(), verts = [], tri = []
  for (let i = 0; i < t.length; i += 3) { const key = [t[i], t[i + 1], t[i + 2]].map((v) => Math.round(v * 1e4)).join(','); if (!idx.has(key)) { idx.set(key, verts.length / 3); verts.push(t[i], t[i + 1], t[i + 2]) } tri.push(idx.get(key)) }
  return new M(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(verts), triVerts: new Uint32Array(tri) }))
}
// 5X7블럭 70 × 50 × 5, 구멍 35개. 아래 블럭도 위 몸통과 같은 윤곽(roundRectPts)을 같은 방법(extrude)으로 만들어 구멍만 판다 — 삼각형 목록(probo1xNTriangles)을 합치면 둥근 모서리 점이 어긋나
//   같은 방향 겹침 25개가 생겼다(사용자 2026-10-31 "결합된 곳에 선이 있다" → 층 사이 계단 없이 벽을 한 면으로 맞추려면 이 겹침을 없애야 한다). 구멍 모양은 make-proboconnect-triangle.mjs 와 같은 구조(아래 둥근 입구 + 가운데 띠 + 위 둥근 입구).
const extrudeY = (poly, y0, y1) => M.extrude([poly], y1 - y0).rotate([-90, 0, 0]).translate([0, y0, 0])
const cylY = (x, z, r, h, y0) => M.cylinder(h, r, r, 24, false).rotate([-90, 0, 0]).translate([x, y0, z])
const cavity = (x, z) => M.union([cylY(x, z, S.boreR, S.barY0 + 1, -1), cylY(x, z, S.boreR, BLOCK - S.barY1 + 1, S.barY1), extrudeY(ccw(roundPoly(openPts(x, -z, S), S.round)), S.barY0 - 0.01, S.barY1 + 0.01)])
const holesAll = []; for (let j = 0; j < 5; j++) for (let i = 0; i < 7; i++) holesAll.push(cavity(-30 + i * 10, -20 + j * 10))
const bottom = process.argv.includes('--shrink') ? solid(probo1xNTriangles(7, S, 5)) : M.difference(extrudeY(ccw(roundRectPts(7, 5, S)), 0, BLOCK), M.union(holesAll))
const upper = M.extrude([ccw(roundRectPts(7, 5, S))], TOTAL - BLOCK + OVER).rotate([-90, 0, 0]).translate([0, BLOCK - OVER, 0])   // 위 몸통(2D y → −z)
// 위 몸통을 0.02% 줄여 아래 블럭과 바깥 벽이 같은 면에 겹치지 않게 한다(그대로 합치면 같은 방향 겹침 25개 — 검사로 확인). 0.007mm 차이라 눈에 안 보인다.
// 사각기둥 둘(사용자 2026-10-30 "25, 70, 20 의 사각기둥 (좌우중심) 합쳐줘" → "50, 60, 25 사각기둥 합쳐줘 위쪽라인맞춰주고", "전체높이가 25"):
//   ① 폭 25 × 길이 70 (좌우 가운데)  ② 폭 50 × 길이 60 — 중심을 맞추라는 말은 없었다(사용자 "누가 중심을 맞추래?" → "한쪽으로 끝라인을 맞추라고"): ②는 +x 쪽 끝 라인(x 35)에 붙인다(⚠ 어느 쪽 끝인지 말씀이 없어 +x 로 정했다).
//   높이(사용자 "높이가 25면 더 올라와야 하는 건데", "아까 껀 전체가 20이었잖아"): ① 는 전체 높이 20 그대로, ② 는 전체 높이 25 — ② 가 ① 보다 5mm 더 올라온다.
//   몸통 윗면(y 15) 위로 10mm 만 올라온다. 바닥 5mm 홀을 메우지 않게 기둥은 몸통 안쪽 y 15 부터 시작한다. 끝면·옆면이 몸통과 같은 평면이라 0.007 줄여 겹침을 피한다.
const COLS = [{ w: 25, l: 70, xc: 0, top: 20 }, { w: 50, l: 60, xc: 5, top: 25 }]   // xc = 길이 방향 가운데 위치(②: 끝라인 x 35 에 붙으려면 가운데 35−60/2 = 5)
// 코너웍(사용자 "이 부분은 코너웍을 맞춰"): 몸통 모서리가 둥근데(반지름 5) 기둥은 각져서 어긋났다 → 기둥을 몸통과 같은 윤곽(roundRectPts(7, 5))으로 잘라 끝라인·모서리가 몸통과 똑같이 둥글게 이어지게 한다.
//   윤곽을 0.04% 줄여(몸통 위 10mm 는 0.02%) 바깥 벽이 같은 면에 겹치지 않게 한다.
// 층 사이 선(사용자 2026-10-31 "결합되어 있는 곳인데 왜 라인이 있는 거야"): 위 층을 줄여 벽을 0.007mm 안쪽에 두면 층마다 작은 계단이 생겨 뷰어가 높이 5·15에 선을 긋는다. 기본은 줄이지 않고 벽을 한 면으로 맞춘다(--shrink 를 주면 예전처럼 줄임).
const SHRINK = process.argv.includes('--shrink'), K_UP = SHRINK ? 0.9998 : 1, K_COL = SHRINK ? 0.9996 : 1
const outlinePrism = M.extrude([ccw(roundRectPts(7, 5, S))], 60).rotate([-90, 0, 0]).scale([K_COL, 1, K_COL])
const columns = COLS.map((c) => M.intersection(M.cube([c.l, c.top - TOTAL + OVER, c.w], false).translate([c.xc - c.l / 2, TOTAL - OVER, -c.w / 2]), outlinePrism))
//   (사용자 "추가로 주는 거면 별도로 해도 되고" → --column 을 주면 사각기둥을 합친 별도 부품, 안 주면 사각기둥 없는 원래 배터리블럭)
const withColumn = process.argv.includes('--column')
const battery = M.union([bottom, upper.scale([K_UP, 1, K_UP]), ...(withColumn ? columns : [])])
const m = battery.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`배터리블럭: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), '→', out)

// 꺾이는 부분 테두리선(사용자 "여기는 꺾이는 부분에 테두리선 그리고"): 기둥 모서리가 둥글어지기 시작하는 곳(평평한 벽 → 둥근 모서리)은 각이 작아 뷰어가 모서리 선을 안 그린다 →
//   그 경계에 세로 0.1mm 선(색칠 조각, 색은 등록 때 lineColorFor)을 긋는다. 폭 50 기둥(②)이 닿는 +x 쪽 두 모서리의 시작·끝 4곳. 별도 STL(<이름>_코너선.stl)과 위치(.json) — register-proboconnect-parts.mjs 가 있으면 붙인다.
const lineFile = out.replace(/\.stl$/, '_코너선.stl')
if (withColumn) {
  // 꺾인 곳 찾기·선 긋기는 공통 도구 app/lib/bend-lines.js (사용자 2026-10-31 "꺾인곳을 찾아서 라인을 그리라고" → "언제든 쓸 수 있게 등록"). 바닥 블럭(높이 0~5) 안쪽 구멍 모서리는 뺀다.
  const kit = makeKit(24)
  const nBend = addBendLines(kit, tris, { skip: (ea, eb) => Math.max(ea[1], eb[1]) <= BLOCK + 0.01 && Math.abs(ea[0]) < 34 && Math.abs(eb[0]) < 34 && Math.abs(ea[2]) < 24 && Math.abs(eb[2]) < 24 })
  console.log(`꺾인 모서리 ${nBend}개 찾음`)
  const lt = kit.result(), lmn = [1e9, 1e9, 1e9], lmx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < lt.length; i += 3) for (let k = 0; k < 3; k++) { lmn[k] = Math.min(lmn[k], lt[i + k]); lmx[k] = Math.max(lmx[k], lt[i + k]) }
  fs.writeFileSync(lineFile, trianglesToStl(lt)); fs.writeFileSync(lineFile.replace(/\.stl$/, '.json'), JSON.stringify({ x: +((lmn[0] + lmx[0]) / 2).toFixed(4), y: +lmn[1].toFixed(4), z: +((lmn[2] + lmx[2]) / 2).toFixed(4) }))
  console.log(`꺾이는 부분 선: 삼각형 ${lt.length / 9}개 →`, lineFile)
} else { for (const f of [lineFile, lineFile.replace(/\.stl$/, '.json')]) if (fs.existsSync(f)) fs.unlinkSync(f) }
