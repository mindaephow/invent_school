// 프로보 커넥트 배터리블럭 STL 만들기. 사용: node scripts/make-proboconnect-battery.mjs <저장할 파일.stl> [--column]
// 사용자 지시(2026-10-30): "배터리 블록 만들 거야, 50, 70, 높이 15, 아래 5mm => 57블록 홀". 지금 모양 = 가로 70 × 세로 50 × 높이 15 (--column 이면 위 사각기둥 25×70(전체 20)·50×60(전체 25)을 합쳐 전체 높이 25) —
//   아래 5mm 는 5X7블럭(구멍 5×7 = 35개, probo1xNTriangles(7, S, 5) 그대로) + 위 10mm 는 같은 윤곽(roundRectPts(7, 5))의 몸통. 나머지(윗면 무늬·단자 등)는 이어서 지시받는 대로.
// 좌표: 길이 x 70(가운데 0), 높이 y(바닥 0), 폭 z 50. 아래 블럭·몸통을 manifold-3d 로 한 몸으로 합친다(make-proboconnect-sensor.mjs 의 아래 블럭 + 몸통과 같은 방식).
// 등록: node scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기> [색]
import fs from 'node:fs'
import Module from 'manifold-3d'
import { PROBO_STD, probo1xNTriangles, roundRectPts } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl, makeKit } from '../app/lib/cubo-mesh-kit.js'
import { LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { conformTJunctions, checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-battery.mjs <저장할 파일.stl> [--column]'); process.exit(1) }
const S = PROBO_STD, BLOCK = S.thick, TOTAL = 15, OVER = 0.02
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const solid = (arr) => {   // 삼각형 목록 → manifold (꼭짓점 합치기)
  const t = conformTJunctions(arr), idx = new Map(), verts = [], tri = []
  for (let i = 0; i < t.length; i += 3) { const key = [t[i], t[i + 1], t[i + 2]].map((v) => Math.round(v * 1e4)).join(','); if (!idx.has(key)) { idx.set(key, verts.length / 3); verts.push(t[i], t[i + 1], t[i + 2]) } tri.push(idx.get(key)) }
  return new M(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(verts), triVerts: new Uint32Array(tri) }))
}
const bottom = solid(probo1xNTriangles(7, S, 5))   // 5X7블럭 70 × 50 × 5, 구멍 35개
const upper = M.extrude([ccw(roundRectPts(7, 5, S))], TOTAL - BLOCK + OVER).rotate([-90, 0, 0]).translate([0, BLOCK - OVER, 0])   // 위 몸통(2D y → −z)
// 위 몸통을 0.02% 줄여 아래 블럭과 바깥 벽이 같은 면에 겹치지 않게 한다(그대로 합치면 같은 방향 겹침 25개 — 검사로 확인). 0.007mm 차이라 눈에 안 보인다.
// 사각기둥 둘(사용자 2026-10-30 "25, 70, 20 의 사각기둥 (좌우중심) 합쳐줘" → "50, 60, 25 사각기둥 합쳐줘 위쪽라인맞춰주고", "전체높이가 25"):
//   ① 폭 25 × 길이 70 (좌우 가운데)  ② 폭 50 × 길이 60 — 중심을 맞추라는 말은 없었다(사용자 "누가 중심을 맞추래?" → "한쪽으로 끝라인을 맞추라고"): ②는 +x 쪽 끝 라인(x 35)에 붙인다(⚠ 어느 쪽 끝인지 말씀이 없어 +x 로 정했다).
//   높이(사용자 "높이가 25면 더 올라와야 하는 건데", "아까 껀 전체가 20이었잖아"): ① 는 전체 높이 20 그대로, ② 는 전체 높이 25 — ② 가 ① 보다 5mm 더 올라온다.
//   몸통 윗면(y 15) 위로 10mm 만 올라온다. 바닥 5mm 홀을 메우지 않게 기둥은 몸통 안쪽 y 15 부터 시작한다. 끝면·옆면이 몸통과 같은 평면이라 0.007 줄여 겹침을 피한다.
const COLS = [{ w: 25, l: 70, xc: 0, top: 20 }, { w: 50, l: 60, xc: 5, top: 25 }]   // xc = 길이 방향 가운데 위치(②: 끝라인 x 35 에 붙으려면 가운데 35−60/2 = 5)
// 코너웍(사용자 "이 부분은 코너웍을 맞춰"): 몸통 모서리가 둥근데(반지름 5) 기둥은 각져서 어긋났다 → 기둥을 몸통과 같은 윤곽(roundRectPts(7, 5))으로 잘라 끝라인·모서리가 몸통과 똑같이 둥글게 이어지게 한다.
//   윤곽을 0.04% 줄여(몸통 위 10mm 는 0.02%) 바깥 벽이 같은 면에 겹치지 않게 한다.
const outlinePrism = M.extrude([ccw(roundRectPts(7, 5, S))], 60).rotate([-90, 0, 0]).scale([0.9996, 1, 0.9996])
const columns = COLS.map((c) => M.intersection(M.cube([c.l, c.top - TOTAL + OVER, c.w], false).translate([c.xc - c.l / 2, TOTAL - OVER, -c.w / 2]), outlinePrism))
//   (사용자 "추가로 주는 거면 별도로 해도 되고" → --column 을 주면 사각기둥을 합친 별도 부품, 안 주면 사각기둥 없는 원래 배터리블럭)
const withColumn = process.argv.includes('--column')
const battery = M.union([bottom, upper.scale([0.9998, 1, 0.9998]), ...(withColumn ? columns : [])])
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
  const LT = LINE_THICKNESS / 2, kit = makeKit(24)
  const bar = (a, b) => {
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => (c / ul) * LT); const v = cr(e, u).map((c) => c / LT * LT)
    const s0 = a.map((c, i) => c - e[i] * LT), s1 = b.map((c, i) => c + e[i] * LT)
    const corner = (q, su, sv) => q.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, mm = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); kit.quad(A[i], A[j], B[j], B[i], mm[0], mm[1], mm[2]) }
  }
  const r = S.endR, hx = 35, hz = 25, sc = 0.9998, OUT = 0.03, y0 = TOTAL, y1 = COLS[1].top   // ②(폭 50)가 +x 끝에 붙은 부분: 높이 15~25
  // ① 둥근 모서리가 시작되는 곳 세로선 4개(평평한 벽 → 둥근 모서리)
  for (const sg of [-1, 1]) {
    bar([(hx * sc) + OUT, y0, sg * (hz - r) * sc], [(hx * sc) + OUT, y1, sg * (hz - r) * sc])
    bar([(hx - r) * sc, y0, sg * (hz * sc + OUT)], [(hx - r) * sc, y1, sg * (hz * sc + OUT)])
  }
  // ② 3층 경계선(사용자 "1층2층처럼 꺾이는 부분 표시가 안되어있는데"): 몸통 윗면 높이(y 15)에서 기둥 둘레를 한 바퀴 — 기둥 벽이 몸통 벽과 같은 면으로 이어져 뷰어가 선을 안 그리므로 직접 긋는다.
  //   ②(폭 50): +x 끝 벽·둥근 모서리 둘·옆 벽(기둥 끝 x −25 까지). ①(폭 25): 양 끝면(x ±35).
  const arc = (cx, cz, a0) => Array.from({ length: 9 }, (_, i) => { const a = a0 + (Math.PI / 2) * (i / 8); return [(cx + r * Math.cos(a)) * sc + OUT * Math.cos(a), (cz + r * Math.sin(a)) * sc + OUT * Math.sin(a)] })
  const loop = [[-25, -hz * sc - OUT], [(hx - r) * sc, -hz * sc - OUT], ...arc(hx - r, -(hz - r), -Math.PI / 2), ...arc(hx - r, hz - r, 0), [(hx - r) * sc, hz * sc + OUT], [-25, hz * sc + OUT]]
  for (let i = 0; i < loop.length - 1; i++) bar([loop[i][0], y0 + 0.02, loop[i][1]], [loop[i + 1][0], y0 + 0.02, loop[i + 1][1]])
  for (const sg of [-1, 1]) bar([sg * (hx * sc + OUT), y0 + 0.02, -12.5], [sg * (hx * sc + OUT), y0 + 0.02, 12.5])
  const lt = kit.result(), lmn = [1e9, 1e9, 1e9], lmx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < lt.length; i += 3) for (let k = 0; k < 3; k++) { lmn[k] = Math.min(lmn[k], lt[i + k]); lmx[k] = Math.max(lmx[k], lt[i + k]) }
  fs.writeFileSync(lineFile, trianglesToStl(lt)); fs.writeFileSync(lineFile.replace(/\.stl$/, '.json'), JSON.stringify({ x: +((lmn[0] + lmx[0]) / 2).toFixed(4), y: +lmn[1].toFixed(4), z: +((lmn[2] + lmx[2]) / 2).toFixed(4) }))
  console.log(`꺾이는 부분 선: 삼각형 ${lt.length / 9}개 →`, lineFile)
} else { for (const f of [lineFile, lineFile.replace(/\.stl$/, '.json')]) if (fs.existsSync(f)) fs.unlinkSync(f) }
