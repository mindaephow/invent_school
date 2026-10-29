// 프로보 커넥트 센서 블럭 STL 만들기 + 부품 행에 등록 (스위치센서·LED센서 레드/블루).
//   node scripts/make-proboconnect-sensor.mjs <저장 폴더> <스위치|LED레드|LED블루> [--write]
// 공통 구조(사용자 2026-10-30 "커넥트 센서들은 대부분 이런 모습"): 가로·세로 20 × 높이 20. 아래 2X2블럭 5mm(구멍 4개) + 몸통 + (눌리는 센서만 틈 1mm) + 위 2X2블럭 5mm(구멍 4개).
//   몸통 한쪽 끝면(−x) 높이 5~9mm 가운데에 3핀 소켓 8×4×5 + 금색 핀 3개(지름 1·간격 2.5) + 짙은 안쪽 바닥판·입구 테두리(뷰어가 홈을 한 색으로 칠해서 안 보이므로).
//   소켓 규격 = 에이스랩·주니어 LED센서(make-robotron-led.mjs)가 큐보 LED센서를 따라 만든 값.
// 종류별 값:
//   스위치   : 아래 흰색 5 + 흰 몸통 9 + 틈 1(스위치라 눌려야 한다) + 위 회색 2X2블럭 5 — 사용자 "중간 1mm 간격이 조금 있어야 해 스위치라 눌려야 하거든"
//   LED레드·블루: 아래 15mm(2X2블럭 5 + 몸통 10)가 레드/블루, 위 5mm 는 흰색(뷰어에 투명도가 없어 "불투명/반투명" 대신 흰색으로), 틈 없음 — 사용자 "윗부분 불투명, 아래는 15mm 블루,레드(중간 1mm 눌림공간 없음)"
// 윗면 선(사용자 2026-10-30 "위에 라인좀 그려줘"): 위 블럭 윗면의 바깥 윤곽(둥근 모서리 그대로)과 구멍 4개 테두리를 0.1mm 가는 선으로 긋는다 — 뷰어가 한 색으로 칠해서 흰 윗면이 밋밋해서. 색은 위 블럭 색보다 조금 어둡게(lineColorFor, 로버트론 테두리 선 규칙).
// 두 2X2블럭 = 기존 프로보 2X2블럭 생성기(probo1xNTriangles(2, S, 2)) 그대로. 몸통 윤곽 = 같은 윤곽(roundRectPts).
// 아래 블럭·몸통은 CSG 로 한 몸(첫 도형 색), 위 블럭·소켓 표시·핀은 색칠 조각(paint:true).
// ⚠ 함정: trianglesToStl 은 Uint8Array 를 돌려준다 — base64 는 Buffer.from(...) 으로(06_3D부품_만들기_등록.md 함정).
import fs from 'node:fs'
import path from 'node:path'
import Module from 'manifold-3d'
import { PROBO_STD, probo1xNTriangles, roundRectPts, circlePtsC } from '../app/lib/proboconnect-block-mesh.js'
import { trianglesToStl, makeKit } from '../app/lib/cubo-mesh-kit.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { conformTJunctions, checkMesh } from '../app/lib/cubo-mesh-repair.js'

const KINDS = {
  스위치: { row: '스위치센서', body: '#ffffff', top: '#8c8c8c', gap: 1, label: '스위치블럭', desc: (m, g) => `아래 흰 2X2블럭 5 + 흰 몸통 ${m} + 틈 ${g} + 위 회색 2X2블럭 5` },
  LED레드: { row: 'LED센서 레드', body: '#d62828', top: '#f2f2f2', gap: 0, label: 'LED블럭_레드', desc: (m) => `아래 레드 15(2X2블럭 5 + 몸통 ${m}) + 위 흰색 2X2블럭 5` },
  LED블루: { row: 'LED센서 블루', body: '#1e50b4', top: '#f2f2f2', gap: 0, label: 'LED블럭_블루', desc: (m) => `아래 블루 15(2X2블럭 5 + 몸통 ${m}) + 위 흰색 2X2블럭 5` },
  // 적외선: 교재 2권 부품 그림(적외선블럭) — 전체가 검은색, 윗면은 구멍 없이 평평하고 렌즈(눈) 2개, 아래 5mm 띠가 2X2블럭 모양. 위 블럭이 따로 없어서 top:null(몸통 15mm).
  적외선: { row: '적외선 센서', body: '#7a7a7a', top: null, gap: 0, label: '적외선블럭', lens: { r: 2.2, x: 4.5, z: -3.5, color: '#303030' }, text: { s: 'IR', z: 4.5, color: '#f2f2f2' }, desc: (m) => `아래 그레이 2X2블럭 5 + 그레이 몸통 ${m}(윗면 어두운 렌즈 2개 + 흰 "IR" 글씨)` },
  // FND: 교재 2권 부품 그림(FND블럭) — 검은 둥근 육면체, 윗면 평평, 옆 아래에 소켓 홈. 적외선과 같은 구조에서 윗면에 에이스랩 컨트롤러와 같은 숫자 표시판(사용자 2026-10-30 "에이스랩처럼 숫자표시를 그려줘야지"). 검정은 안 보여서 그레이.
  FND: { row: 'FND센서', body: '#7a7a7a', top: null, gap: 0, label: 'FND블럭', display: true, desc: (m) => `아래 그레이 2X2블럭 5 + 그레이 몸통 ${m}(윗면 숫자 표시판: 검은 판 + 7세그먼트 "88" + 점)` },
}
const dir = process.argv[2], kind = process.argv[3], write = process.argv.includes('--write'), K = KINDS[kind]
if (!dir || !K) { console.error('사용: node scripts/make-proboconnect-sensor.mjs <저장 폴더> <' + Object.keys(KINDS).join('|') + '> [--write]'); process.exit(1) }
fs.mkdirSync(dir, { recursive: true })
const HAS_TOP = K.top !== null
const S = PROBO_STD, BLOCK = S.thick, GAP = K.gap, MID = 20 - (HAS_TOP ? 2 * BLOCK + GAP : BLOCK), OVER = 0.02   // 2X2블럭 5 / 몸통 / 틈 / 2X2블럭 5. OVER = 맞닿는 면이 겹쳐 한 몸이 되게 하는 여유
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const toArr = (mf) => { const m = mf.getMesh(), t = new Float32Array(m.triVerts.length * 3); for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) t[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]; return t }
const ccw = (poly) => (poly.reduce((s, q, i) => { const n = poly[(i + 1) % poly.length]; return s + q[0] * n[1] - n[0] * q[1] }, 0) > 0 ? poly : poly.slice().reverse())
const block = () => conformTJunctions(probo1xNTriangles(2, S, 2))                                  // 2X2블럭 20×20×5, 구멍 4개
const bottom = block(), top = HAS_TOP ? block() : null
const SOCKET = { w: 8, h: 4, d: 5, y0: BLOCK, face: -10, pinR: 0.5, pitch: 2.5 }                  // 소켓 높이 범위 = 아래에서 5~9
const midBody = M.extrude([ccw(roundRectPts(2, 2, S))], MID + OVER).rotate([-90, 0, 0]).translate([0, BLOCK - OVER, 0])   // 월드 y 4.98~
const cut = M.cube([SOCKET.d + 0.1, SOCKET.h, SOCKET.w], false).translate([SOCKET.face - 0.1, SOCKET.y0, -SOCKET.w / 2])
const mid = toArr(M.difference(midBody, cut).translate([0, -(BLOCK - OVER), 0]))                 // 몸통 파일은 바닥 y=0 기준으로 저장(등록 때 y 오프셋을 준다)
const cy = SOCKET.y0 + SOCKET.h / 2, dx0 = SOCKET.face, dx1 = SOCKET.face + SOCKET.d
const pinsM = M.union([-SOCKET.pitch, 0, SOCKET.pitch].map((z) => M.cylinder(SOCKET.d, SOCKET.pinR, SOCKET.pinR, 16, false).rotate([0, 90, 0]).translate([dx0, cy, z])))   // 핀: 입구~안쪽 바닥
const box = (x0, x1, y0, y1, z0, z1) => M.cube([x1 - x0, y1 - y0, z1 - z0], false).translate([x0, y0, z0])
const T = 0.2, R = 0.6, hw = SOCKET.w / 2, yA = SOCKET.y0, yB = SOCKET.y0 + SOCKET.h
const darkM = M.union([box(dx1 - T, dx1, yA, yB, -hw, hw),                                              // 안쪽 바닥판
  box(dx0 - T, dx0, yB, yB + R, -hw - R, hw + R), box(dx0 - T, dx0, yA - R, yA, -hw - R, hw + R), box(dx0 - T, dx0, yA, yB, -hw - R, -hw), box(dx0 - T, dx0, yA, yB, hw, hw + R)])   // 입구 테두리 띠
const pins = toArr(pinsM), dark = toArr(darkM)
const place = (mf) => { const b = mf.boundingBox(); return { x: (b.min[0] + b.max[0]) / 2, y: b.min[1], z: (b.min[2] + b.max[2]) / 2 } }   // 뷰어는 조각마다 x·z 가운데·바닥을 원점에 맞추므로 그 위치를 도형 위치로 준다
const pinsAt = place(pinsM), darkAt = place(darkM)
// 윗면 선: 가는 삼각 기둥 막대를 윤곽 점 사이에 이어 붙인다(make-robotron-flatplate.mjs 의 outlineBars 와 같은 방식)
const TOPY = (HAS_TOP ? 2 * BLOCK : BLOCK) + MID + GAP, LT = LINE_THICKNESS / 2
const lineKit = makeKit(24)
const bar = (a, b) => {
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
  const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
  const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
  let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => (c / ul) * LT); const v = cr(e, u).map((c) => c / LT * LT)
  const s0 = a.map((c, i) => c - e[i] * LT), s1 = b.map((c, i) => c + e[i] * LT)
  const corner = (q, su, sv) => q.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]   // 세 면짜리 가는 막대(삼각 기둥)
  const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
  const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
  for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); lineKit.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
}
const ring3 = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
const LINE_OUT = 0.03                                                                              // 윗면보다 살짝 위로 띄워 면에 묻히지 않게
ring3(roundRectPts(2, 2, S), TOPY + LINE_OUT)                                                       // 바깥 윤곽
if (HAS_TOP) for (const cx of [-5, 5]) for (const cz of [-5, 5]) ring3(circlePtsC(cx, cz, S.boreR, 32), TOPY + LINE_OUT)   // 구멍 4개 입구 테두리(위 2X2블럭이 있을 때)
const lines = lineKit.result()
// 적외선 렌즈(눈) 2개: 윗면에 얇은 원판을 얹는다(색칠 조각). 두 렌즈는 z 방향으로 ±4.5.
const lensM = K.lens ? M.union([-K.lens.x, K.lens.x].map((x) => M.cylinder(0.3, K.lens.r, K.lens.r, 32, false).rotate([-90, 0, 0]).translate([-K.lens.z, TOPY, x]))) : null   // 렌즈·글씨는 FND 숫자와 같이 90° 돌려 놓는다: (x, z) → (−z, x), 소켓(−x) 쪽에서 가로로 보이게(사용자 2026-10-30 "IR도 돌려")
const lens = lensM ? toArr(lensM) : null, lensAt = lensM ? place(lensM) : null
// 글씨(사용자 2026-10-30 "IR이라고 적어줘"): 5×7 점 글꼴을 작은 상자로 쌓아 윗면 위에 0.2mm 올린다(make-robotron-controller.mjs 의 GLYPH 방식). 읽는 방향 +z, 글자 위쪽 +x(소켓 쪽에서 가로로 읽힘).
const GLYPH = { I: '01110,00100,00100,00100,00100,00100,01110', R: '11110,10001,10001,11110,10100,10010,10001', F: '11111,10000,10000,11110,10000,10000,10000', N: '10001,11001,10101,10101,10011,10001,10001', D: '11110,10001,10001,10001,10001,10001,11110' }
const textM = K.text ? (() => { const cell = 0.6, h = 0.2, n = K.text.s.length, boxes = []; let ox = -((n * 5 + (n - 1)) * cell) / 2; const z0 = K.text.z - 3.5 * cell
  for (const ch of K.text.s) { GLYPH[ch].split(',').forEach((row, r) => [...row].forEach((v, c) => { if (v === '1') boxes.push(M.cube([cell, h, cell], false).translate([-(z0 + r * cell + cell), TOPY, ox + c * cell])) })); ox += 6 * cell }
  return M.union(boxes) })() : null
const textT = textM ? toArr(textM) : null, textAt = textM ? place(textM) : null
// 숫자 표시판(에이스랩 컨트롤러 make-robotron-controller.mjs 의 "LED 표시판"과 같은 치수·색): 검은 판 + 7세그먼트 "8"(폭 4.2·높이 7.8·획 0.7) + 점. 사용자 "8을 2개" → 두 자리(88). 읽는 방향 +z, 글자 위쪽 +x(소켓 쪽에서 가로로 읽힘).
const dispParts = K.display ? (() => {
  // 사용자 2026-10-30 "숫자를 90도 돌려야 할 거 같아": 소켓(−x 끝면) 쪽에서 봤을 때 숫자가 가로로 읽히도록(읽는 방향 +z, 글자 위쪽 +x) 아래 좌표(읽는 방향 x, 위쪽 −z)를 90° 돌려 만든다 — (x, z) → (−z, x).
  const cube = (x0, x1, y0, y1, z0, z1) => M.cube([z1 - z0, y1 - y0, x1 - x0], false).translate([-z1, y0, x0])
  const PT = 0.5, SH = 0.15, sx = 2.1, st = 0.7, z0s = -3.9, z1s = 3.9, zm = 0, y1 = TOPY + PT, y2 = y1 + SH, DIG = [-3.3, 3.3]   // 숫자 가운데 x 두 곳
  const plate = cube(-7.4, 7.4, TOPY, y1, -6.3, 6.3)
  const segs = []
  for (const cx of DIG) {
    segs.push(cube(cx - sx, cx + sx, y1, y2, z0s, z0s + st), cube(cx - sx, cx + sx, y1, y2, zm - st / 2, zm + st / 2), cube(cx - sx, cx + sx, y1, y2, z1s - st, z1s))   // 가로 3개
    for (const xx of [cx - sx, cx + sx - st]) segs.push(cube(xx, xx + st, y1, y2, z0s + st + 0.06, zm - st / 2 - 0.06), cube(xx, xx + st, y1, y2, zm + st / 2 + 0.06, z1s - st - 0.06))   // 세로 4개(가로 조각과 겹치지 않게)
    segs.push(cube(cx + sx + 0.5, cx + sx + 1.1, y1, y2, z1s - 0.6, z1s))   // 점
  }
  return { plate, seg: M.union(segs) } })() : null
const dispPlate = dispParts ? toArr(dispParts.plate) : null, dispSeg = dispParts ? toArr(dispParts.seg) : null
const dispPlateAt = dispParts ? place(dispParts.plate) : null, dispSegAt = dispParts ? place(dispParts.seg) : null
const linesBB = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < lines.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], lines[i + k]); mx[k] = Math.max(mx[k], lines[i + k]) } return { x: (mn[0] + mx[0]) / 2, y: mn[1], z: (mn[2] + mx[2]) / 2 } })()
const report = (n, t) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < t.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], t[i + k]); mx[k] = Math.max(mx[k], t[i + k]) } console.log(`${n}: 삼각형 ${t.length / 9}개`, JSON.stringify(checkMesh(t)), '크기', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×')) }
report('아래 블럭(2X2)', bottom); report('몸통', mid); if (top) report('위 블럭(2X2)', top); report('핀 3개(금색)', pins); report('소켓 바닥판·테두리(짙은색)', dark); report('윗면 선', lines); if (lens) report('렌즈 2개', lens); if (textT) report('글씨', textT); if (dispPlate) { report('표시판', dispPlate); report('표시 숫자 88', dispSeg) }
const f = (n) => path.join(dir, `${K.label}_${n}.stl`)
const sB = trianglesToStl(bottom), sM = trianglesToStl(mid), sT = top ? trianglesToStl(top) : null, sP = trianglesToStl(pins), sD = trianglesToStl(dark), sL = trianglesToStl(lines), sLens = lens ? trianglesToStl(lens) : null, sText = textT ? trianglesToStl(textT) : null, sPlate = dispPlate ? trianglesToStl(dispPlate) : null, sSeg = dispSeg ? trianglesToStl(dispSeg) : null
const files = { 아래블럭: sB, 몸통: sM, ...(sT ? { 위블럭: sT } : {}), 핀3: sP, 소켓표시: sD, 윗면선: sL, ...(sLens ? { 렌즈: sLens } : {}), ...(sText ? { 글씨: sText } : {}), ...(sPlate ? { 표시판: sPlate, 표시숫자: sSeg } : {}) }
for (const [n, b] of Object.entries(files)) fs.writeFileSync(f(n), b)
console.log('→', Object.keys(files).map(f).join('\n→ '), '\n높이 ' + [BLOCK, MID, '틈' + GAP, HAS_TOP ? BLOCK : 0].join('+') + '=' + (BLOCK + MID + GAP + (HAS_TOP ? BLOCK : 0)) + ', 가로·세로 20')
if (write) {
  const env = Object.fromEntries(fs.readFileSync('.env.local', 'utf8').split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
  const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`, 'Content-Type': 'application/json' }
  const rest = `${env.SUPABASE_URL}/rest/v1`
  const cat = (await (await fetch(`${rest}/ivs_robot_categories?select=id,data`, { headers: H })).json()).find((c) => c.data.name === '프로보 커넥트')
  const rows = (await (await fetch(`${rest}/ivs_part_catalog?select=id,data&data->>category=eq.${cat.id}&data->>name=eq.${encodeURIComponent(K.row)}`, { headers: H })).json())
  if (rows.length !== 1) { console.log(`"${K.row}" 행이 ${rows.length}개 → 멈춤`); process.exit(1) }
  const row = rows[0]
  const imp = (b, name, color, y, paint, x = 0, z = 0) => ({ x, y, z, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, ...(paint ? { paint: true } : {}), fileName: name, brightness: 100, fileDataUrl: 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64') })
  const shapes = [imp(sB, `${K.label}_아래블럭.stl`, K.body, 0, false), imp(sM, `${K.label}_몸통.stl`, K.body, BLOCK - OVER, false), ...(sT ? [imp(sT, `${K.label}_위블럭.stl`, K.top, BLOCK + MID + GAP, true)] : []),
    imp(sD, `${K.label}_소켓표시.stl`, '#555555', darkAt.y, true, darkAt.x, darkAt.z), imp(sP, `${K.label}_핀3.stl`, '#d4af37', pinsAt.y, true, pinsAt.x, pinsAt.z),
    imp(sL, `${K.label}_윗면선.stl`, lineColorFor(K.top || K.body), linesBB.y, true, linesBB.x, linesBB.z),
    ...(sLens ? [imp(sLens, `${K.label}_렌즈.stl`, K.lens.color, lensAt.y, true, lensAt.x, lensAt.z)] : []),
    ...(sText ? [imp(sText, `${K.label}_글씨.stl`, K.text.color, textAt.y, true, textAt.x, textAt.z)] : []),
    ...(sPlate ? [imp(sPlate, `${K.label}_표시판.stl`, '#26292d', dispPlateAt.y, true, dispPlateAt.x, dispPlateAt.z), imp(sSeg, `${K.label}_표시숫자.stl`, '#d4e0cf', dispSegAt.y, true, dispSegAt.x, dispSegAt.z)] : [])]
  const data = { ...row.data, size: `가로 20 × 세로 20 × 높이 20mm (${K.desc(MID, GAP)}, −x 끝면 3핀 소켓 8×4×5 높이 5~9)`, spec: { ...(row.data.spec || {}), pitch: 10, margin: 5, shapes }, thumbnail3d: null }
  const r = await fetch(`${rest}/ivs_part_catalog?id=eq.${row.id}`, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) })
  console.log(row.data.name, '→', r.status, r.ok ? '등록됨 id ' + row.id : await r.text())
  for (const s of shapes) console.log('  ', s.fileName, 'fileDataUrl 길이', s.fileDataUrl.length, 'y', s.y, s.paint ? '(색칠 조각)' : '')
}
