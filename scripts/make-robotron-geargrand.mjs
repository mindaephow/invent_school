// 에이스랩 기어(대): 지름 62·두께 5 원 톱니바퀴(모듈 1, 이빨 60개: 이끝원 지름 62·피치원 60·이뿌리원 57.5). 위·아래에 지름 50 고리 홈(깊이 1, 가운데 지름 33 제외)과 가운데 지름 30 홈(깊이 1), 중심에 십자 축이 들어가는 열십자 홀(폭 5·팔 1.4), 그 둘레에 휠가이드와 같은 구멍(열십자 육각 4개 + 사이 둥근 구멍 4개, 피치 10)을 뚫는다(사용자 2026-10-27).
// 이빨은 사다리꼴 직선 옆면으로 우선 만든다 — 모양은 이후 사용자와 다듬는다.
//   node scripts/make-robotron-geargrand.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { conformTJunctions, checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'
import { WHEELGUIDE_STD as W, wheelGuideSpots } from '../app/lib/robotron-wheelguide-mesh.js'
import { ACELAB_FRAME_STD as F } from '../app/lib/acelab-frame-mesh.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8', 블랙: '#555555', 그레이: '#9ca5af' }
const OD = 62, MOD = 1, Z = 60, T = 5 // 이끝원 지름, 모듈, 이빨 수, 두께(에이스랩 프레임과 같은 5)
const RT = OD / 2, RP = MOD * Z / 2, RR = RP - 1.25 * MOD // 이끝원·피치원·이뿌리원 반지름
const TIP_FR = 0.28, ROOT_FR = 0.56 // 이빨 하나가 차지하는 각도 비율: 끝 / 뿌리 (나머지는 이 사이 골)
const y0 = 0, y1 = T
const kit = makeKit(48), { quad, P } = kit // kit.cyl 의 분할 수 = 홈 원 분할 수(48)
const pol = (r, a) => [r * Math.cos(a), r * Math.sin(a)]
const gear = []
for (let i = 0; i < Z; i++) { const c = (2 * Math.PI * i) / Z, p = (2 * Math.PI) / Z; gear.push(pol(RR, c - ROOT_FR * p / 2), pol(RT, c - TIP_FR * p / 2), pol(RT, c + TIP_FR * p / 2), pol(RR, c + ROOT_FR * p / 2)) } // 반시계
const hexPts = (cx, cz, flat, rot = 0) => { const R = flat / Math.sqrt(3); return Array.from({ length: 6 }, (_, k) => [cx + R * Math.cos((Math.PI / 3) * k + rot), cz + R * Math.sin((Math.PI / 3) * k + rot)]) }
const spots = wheelGuideSpots(W), cross = spots.slice(0, 4), diag = spots.slice(4)
const crossHex = cross.map(([x, z]) => hexPts(x, z, W.endHexFlat, x !== 0 ? Math.PI / 2 : 0)) // 휠가이드와 같다(좌·우 육각은 90° 돌림)
const diagRound = diag.map(([x, z]) => circlePts(x, z, W.holeR, 24)), a = F.crossSpan / 2, w = F.crossArm / 2 // 가운데 구멍: 십자 축(4×4)이 들어가는 열십자 홀(3십자프레임·부시와 같은 규격: 전체 폭 crossSpan, 팔 폭 crossArm, 사용자 2026-10-27 "중심에 축 들어갈 규격 열십자 홀")
const screw = [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] // 반시계
const holes = [screw, ...crossHex, ...diagRound]
const wallOut = (poly) => poly.forEach((a, i) => { const b = poly[(i + 1) % poly.length]; quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) }) // 바깥을 향한다
const wallIn = (poly, ya = y0, yb = y1) => poly.forEach((a, i) => { const b = poly[(i + 1) % poly.length]; quad(P(a[0], ya, a[1]), P(b[0], ya, b[1]), P(b[0], yb, b[1]), P(a[0], yb, a[1]), -(b[1] - a[1]), 0, b[0] - a[0]) }) // 구멍 속을 향한다
// 위·아래 홈(사용자 2026-10-27 "지름 50 두께 1mm 위아래 홈 파줘, 지름 33 부분 제외"): 지름 50 원 안을 깊이 1 로 파되 가운데 지름 33 원은 그대로 둔다(고리 모양 홈).
const PR = 25, PIN = 16.5, PC = 15, PD = 1, pocketOut = circlePts(0, 0, PR, 48), pocketIn = circlePts(0, 0, PIN, 48)
// 가운데 지름 30 위·아래 홈(사용자 2026-10-27 "지름 30 위아래 1mm 홈 파줘"): 지름 33 가운데 원 안쪽을 깊이 1 로 더 판다(구멍 9개는 이 안에 있다).
const pocketC = circlePts(0, 0, PC, 48)
wallOut(gear); holes.forEach((h) => wallIn(h, y0 + PD, y1 - PD))
kit.cyl(0, 0, PC, y1 - PD, y1, -1); kit.cyl(0, 0, PC, y0, y0 + PD, -1)
kit.cyl(0, 0, PR, y1 - PD, y1, -1); kit.cyl(0, 0, PIN, y1 - PD, y1, 1); kit.cyl(0, 0, PR, y0, y0 + PD, -1); kit.cyl(0, 0, PIN, y0, y0 + PD, 1) // 홈 바깥벽(속을 향함)·안쪽 기둥 벽(바깥을 향함)
ringFace(kit, gear, [pocketOut], y1, 1); ringFace(kit, pocketIn, [pocketC], y1, 1); ringFace(kit, pocketC, holes, y1 - PD, 1) // 윗면: 바깥 고리 · 지름 33~30 테두리 · 가운데 홈 바닥(구멍 뚫림)
ringFace(kit, pocketOut, [pocketIn], y1 - PD, 1) // 윗 홈 바닥
ringFace(kit, gear, [pocketOut], y0, -1); ringFace(kit, pocketIn, [pocketC], y0, -1); ringFace(kit, pocketC, holes, y0 + PD, -1) // 아랫면
ringFace(kit, pocketOut, [pocketIn], y0 + PD, -1) // 아랫 홈 바닥
const bodyTris = conformTJunctions(kit.result())

// 밝은 테두리 선(에이스랩 부품 규칙): 위·아래 바깥 둘레(이빨 포함)와 구멍 둘레.
const outlineBars = () => {
  const k = makeKit(24), t = LINE_THICKNESS / 2
  const bar = (a, b) => {
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
  }
  const ring = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
  ring(gear, y0); ring(gear, y1); holes.forEach((h) => { ring(h, y0 + PD); ring(h, y1 - PD) })
  for (const c of [pocketOut, pocketIn, pocketC]) for (const y of [y0, y0 + PD, y1 - PD, y1]) ring(c, y) // 홈 입구·바닥 가장자리
  return trianglesToStl(k.result())
}
const outlineStl = outlineBars(), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const NAME = '기어(대)'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  r.data.color = '그레이'; const hex = HEX[r.data.color] // 사용자 2026-10-27 "그레이"
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `기어대_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: '기어대_에이스랩.stl' }, { ...mk(outlineStl, '바깥선', { paint: true }), color: lineColorFor(hex) }] }
  const dir = [0, -1, 0]
  const connectors = {
    note: `${NAME}(지름 ${OD}·두께 ${T} 원 톱니바퀴, 모듈 ${MOD}·이빨 ${Z}개: 피치원 지름 ${2 * RP}·이뿌리원 지름 ${2 * RR}). 가운데에 휠가이드와 같은 구멍: 가운데 열십자 축 홀(h1, 전체 폭 ${F.crossSpan}·팔 폭 ${F.crossArm}) + 열십자로 피치 ${W.pitch} 육각 구멍 4개(h2~h5, 대변 ${W.endHexFlat}) + 사이 가운데 둥근 구멍 4개(h6~h9, 지름 ${W.holeR * 2}). 위·아래 면에는 지름 ${PR * 2} 안쪽을 깊이 ${PD} 로 판 홈(가운데 지름 ${PIN * 2} 원은 제외, 고리 모양) + 가운데 지름 ${PC * 2} 안쪽 깊이 ${PD} 홈(구멍 9개는 이 홈 바닥에 뚫림). 이빨 모양은 이후 다듬는다.`,
    pegs: [], holes: [{ id: 'h1', r: F.crossSpan / 2, dir, len: T, pos: [0, 0, 0], through: true }, ...spots.map(([x, z], i) => ({ id: 'h' + (i + 2), r: W.holeR, dir, len: T, pos: [x, 0, z], through: true }))],
    size: [OD, T, OD], confidence: 'draft',
  }
  const data = { ...r.data, size: `Ø${OD}×${T}mm (에이스랩: 모듈 ${MOD} 이빨 ${Z}개 원 톱니바퀴, 가운데에 휠가이드와 같은 구멍 9개 — 가운데 열십자 축 홀(폭 ${F.crossSpan}·팔 ${F.crossArm}) + 열십자 육각 4개(대변 ${W.endHexFlat}, 피치 ${W.pitch}) + 사이 둥근 구멍 4개(지름 ${W.holeR * 2}), 위·아래 고리 홈: 지름 ${PR * 2} 안쪽 깊이 ${PD}, 가운데 지름 ${PIN * 2} 제외 + 가운데 지름 ${PC * 2} 깊이 ${PD} 홈, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '삼각형', bodyTris.length / 9, '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
