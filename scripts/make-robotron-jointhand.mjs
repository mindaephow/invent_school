// 에이스랩 관절수(수): 12프레임(10×20×5, 구멍 1×2, 위쪽 8×8 사각 홈 1mm) 한쪽에 8mm 를 더해 팔이 나온 전체 길이 28, 그 부분이 암·수의 '수' — 양쪽 끝(좌우 가장자리)에서 나오는 팔 두 개(ㄷ 모양)이고 팔 끝은 둥글게 마무리한다(사용자 2026-10-27 "팔나왔을때 28", "ㄷ 모양", "오른쪽 끝 마무리가 둥그렇고"). 팔 폭·홈 깊이는 처음 값으로 만든 뒤 사용자와 다듬는다.
//   node scripts/make-robotron-jointhand.mjs [--write] [--name=관절수]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { ACELAB_FRAME_STD } from '../app/lib/acelab-frame-mesh.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { conformTJunctions, checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8', 블랙: '#555555', 그레이: '#9ca5af', 다홍색: '#f45243' }
const HOLES_N = 2, W = 10, T = 5, HOLE_R = ACELAB_FRAME_STD.boreR // 구멍 1×2, 폭 z 10, 두께 y 5, 홀 규격사이즈 5.2
const FRAME_L = 20, ADD = 8, LEN = FRAME_L + ADD // 12프레임 길이 20 + 수 부분 8 = 전체 28
const AW = 2.5, GAP_X = 10, TIP_R = AW / 2, PW = 8, PR = 3, PD = 1 // 팔 폭 2.5(두 팔 사이 틈 5), 틈 바닥 x, 팔 끝 모서리 반지름, 위쪽 홈 8×8(모서리 반지름 3 — 둥근 끝 반지름 5 안에 들어가는 최소 반지름 2.8 이상)·깊이 1
const X_L = -FRAME_L / 2, X_R = FRAME_L / 2 + ADD, HC = [[-5, 0], [5, 0]] // 왼쪽 끝(둥근 끝), 팔 끝(+x), 구멍 가운데
const half = W / 2
// 둘레(반시계, x 오른쪽·z 위): 아래 변 → 아래 팔 끝 → 틈 → 위 팔 끝 → 위 변 → 왼쪽 둥근 끝
const arcL = Array.from({ length: 25 }, (_, j) => { const a = (90 + 180 * j / 24) * Math.PI / 180; return [X_L + half + half * Math.cos(a), half * Math.sin(a)] }) // 왼쪽 반원(위→아래)
// 팔 끝 옆모양(사용자 2026-10-27 스샷 ")" "오른쪽 끝부분을 둥그렇게", "여기가 톱날처럼 보여야 하는데?", "15도씩", "각도 조절"): 위에서 본 모양은 각진 채 두고, 팔 끝 옆모양은 반지름 PRO(두께의 절반 2.5) 반원을 따라 톱날(삼각 톱니)로 만든다.
// 톱니바퀴처럼(사용자 2026-10-27 "톱니바퀴처럼 만들면 되겠네") 반원 끝 전체에 15° 간격: 뾰족한 끝 13개(−90°~+90°), 그 사이 골 12개. 암 부분의 뾰족한 돌기가 골에 꽂혀 각도가 딱딱 걸린다.
const PRO = T / 2, XC2 = X_R - PRO, TD = 0.4, STEP = 7.5 // TD: 톱니 깊이(골에서 뾰족한 끝까지), 7.5° 간격으로 점을 찍는다(뾰족한 끝·골이 번갈아)
const rho = (ph) => { const k = Math.round(ph / STEP); return Math.abs(ph - k * STEP) < 1e-9 && (k % 2 !== 0) ? PRO - TD : PRO } // 홀수 번째(±7.5, ±22.5, ±37.5°)는 골, 나머지는 반원 위
const prof = Array.from({ length: 25 }, (_, j) => { const ph = -90 + j * STEP, r = rho(ph), a = ph * Math.PI / 180; return [XC2 + r * Math.cos(a), PRO + r * Math.sin(a)] }) // 아래(−90°)→끝(0°)→위(+90°) 옆모양 점
const outline = [[XC2, -half], [XC2, -half + AW], [GAP_X, -half + AW], [GAP_X, half - AW], [XC2, half - AW], [XC2, half], ...arcL] // 몸통 둘레(반시계): 팔이 둥글어지기 시작하는 x=XC2 에서 자른다. 아래 팔 단면 → 틈 바닥 → 위 팔 단면 → 위 변 → 왼쪽 둥근 끝
const holes = HC.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const sqr = ([cx, cz]) => { const h = PW / 2 - PR, cs = [[cx + h, cz + h, 0], [cx - h, cz + h, 90], [cx - h, cz - h, 180], [cx + h, cz - h, 270]]; return cs.flatMap(([ax, az, a0]) => Array.from({ length: 7 }, (_, j) => { const a = (a0 + 90 * j / 6) * Math.PI / 180; return [ax + PR * Math.cos(a), az + PR * Math.sin(a)] })) }
const pockets = HC.map(sqr)
const kit = makeKit(24), { quad, P } = kit
outline.forEach((a, i) => { const b = outline[(i + 1) % outline.length]; if (Math.abs(a[0] - XC2) < 1e-9 && Math.abs(b[0] - XC2) < 1e-9) return; if (Math.abs(Math.abs(a[1]) - (half - AW)) < 1e-9 && Math.abs(a[1] - b[1]) < 1e-9 && Math.min(a[0], b[0]) >= GAP_X - 1e-9 && Math.max(a[0], b[0]) <= XC2 + 1e-9) return; // 팔 안쪽 면은 아래에서 볼록 돌기와 함께 따로 만든다
     if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], T, b[1]), P(a[0], T, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) }) // 옆벽(바깥을 향한다)
ringFace(kit, outline, holes, 0, -1) // 아랫면(구멍 뚫림)
ringFace(kit, outline, pockets, T, 1) // 윗면(사각 홈 자리 뚫림)
HC.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, 0, T - PD, -1) // 구멍 벽(아래~홈 바닥)
  const pk = pockets[i], cen = [x, z]; pk.forEach((a, j) => { const b = pk[(j + 1) % pk.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], T - PD, a[1]), P(b[0], T - PD, b[1]), P(b[0], T, b[1]), P(a[0], T, a[1]), cen[0] - (a[0] + b[0]) / 2, 0, cen[1] - (a[1] + b[1]) / 2) }) // 홈 옆벽(홈 가운데를 향한다)
  ringFace(kit, pk, [holes[i]], T - PD, 1) // 홈 바닥(위를 본다, 구멍 뚫림)
})
// 팔 끝: 옆모양(prof)을 팔 폭만큼(z 방향) 밀어낸 모양 — 위에서 보면 각진 끝, 옆에서 보면 톱날 반원. 바깥쪽 면은 옆모양 그대로, 안쪽 면(틈을 보는 면)은 틈 바닥부터 이어 만들고 가운데에 볼록 돌기를 붙인다.
// 안쪽 볼록 돌기(사용자 2026-10-27 "안쪽에 볼록 돌기 만들어줘"): 톱니 반원의 중심 C=(XC2, PRO) 에 두 팔 안쪽 면마다 한 개씩, 틈 쪽으로 BH 만큼 솟은 둥근 돌기(밑 반지름 BA) — 암 부분의 구멍(축)에 꽂혀 각도를 돌릴 때 축이 된다.
const BA = 1.0, BH = 0.6, BK = 4, BSEG = 16
for (const [zlo, zhi, oz, on, iz, inn] of [[-half, -half + AW, -half, -1, -half + AW, 1], [half - AW, half, half, 1, half - AW, -1]]) {
  for (let i = 0; i + 1 < prof.length; i++) { const a = prof[i], b = prof[i + 1]
    quad(P(a[0], a[1], zlo), P(b[0], b[1], zlo), P(b[0], b[1], zhi), P(a[0], a[1], zhi), b[1] - a[1], -(b[0] - a[0]), 0) } // 끝 곡면(바깥을 향한다)
  const cap = (outerPoly, holes, zf, nz) => { const tmp = makeKit(24); ringFace(tmp, outerPoly, holes, 0, 1)
    const r0 = tmp.result(); for (let i = 0; i < r0.length; i += 9) kit.tri(P(r0[i], r0[i + 2], zf), P(r0[i + 3], r0[i + 5], zf), P(r0[i + 6], r0[i + 8], zf), 0, 0, nz) } // (x, 0, y)로 나눈 삼각형을 벽 면(x, y, zf)으로 옮긴다
  cap(prof, [], oz, on) // 바깥쪽 면(옆모양 그대로)
  const base = circlePts(XC2, PRO, BA, BSEG)
  cap([[GAP_X, 0], ...prof, [GAP_X, T]], [base], iz, inn) // 안쪽 면(틈 바닥부터, 돌기 자리는 뚫린다)
  // 돌기: 밑 반지름 BA, 높이 BH 인 구 일부(둥근 지붕). 틈 쪽(inn 방향)으로 솟는다.
  const Rs = (BA * BA + BH * BH) / (2 * BH), b0 = Math.asin(BA / Rs), zs = iz + inn * (BH - Rs) // 구 반지름·밑 각·구 중심 z
  const ring = (k) => { const bt = b0 * (1 - k / BK), rr = Rs * Math.sin(bt), zz = zs + inn * Rs * Math.cos(bt); return Array.from({ length: BSEG }, (_, j) => { const a = 2 * Math.PI * j / BSEG; return P(XC2 + rr * Math.cos(a), PRO + rr * Math.sin(a), zz) }) }
  const hint = (v) => [v[0] - XC2, v[1] - PRO, v[2] - zs]
  for (let k = 0; k < BK; k++) { const r0 = ring(k), r1 = ring(k + 1)
    for (let j = 0; j < BSEG; j++) { const j2 = (j + 1) % BSEG, h = hint(r0[j]); kit.tri(r0[j], r0[j2], r1[j2], h[0], h[1], h[2]); if (k + 1 < BK || true) kit.tri(r0[j], r1[j2], r1[j], h[0], h[1], h[2]) } } } // 돌기 둥근 면(바깥을 향한다)
const noDegenerate = (arr) => { const out = []; for (let i = 0; i < arr.length; i += 9) { const u = [arr[i + 3] - arr[i], arr[i + 4] - arr[i + 1], arr[i + 5] - arr[i + 2]], v = [arr[i + 6] - arr[i], arr[i + 7] - arr[i + 1], arr[i + 8] - arr[i + 2]], c = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]; if (Math.hypot(...c) > 1e-9) out.push(...arr.slice(i, i + 9)) } return Float32Array.from(out) }
const bodyTris = conformTJunctions(noDegenerate(kit.result())) // 12프레임 몸통 + 수 부분(팔 두 개, 끝 옆모양 둥글게)
const toTris = (a) => { const T3 = []; for (let i = 0; i < a.length; i += 9) T3.push([0, 3, 6].map((o) => [a[i + o], a[i + o + 1], a[i + o + 2]])); return T3 }
if (process.argv.includes('--check')) { const K = (q) => q.map((c) => Math.round(c * 1e4)).join(','), dir = new Map(); for (let i = 0; i < bodyTris.length; i += 9) for (let v = 0; v < 3; v++) { const a = [bodyTris[i + v * 3], bodyTris[i + v * 3 + 1], bodyTris[i + v * 3 + 2]], q = (v + 1) % 3, c = [bodyTris[i + q * 3], bodyTris[i + q * 3 + 1], bodyTris[i + q * 3 + 2]]; dir.set(K(a) + '>' + K(c), [a, c]) }
  let m = 0; for (const [k, [a, c]] of dir) if (!dir.has(K(c) + '>' + K(a)) && m++ < 20) console.log('열림', a.map((x) => x.toFixed(3)).join(','), '->', c.map((x) => x.toFixed(3)).join(',')) }
const plateTris = toTris(bodyTris)
const key = (v) => v.map((c) => Math.round(c * 1e4)).join(',')
const faceLoops = (T, y, ny) => { // 높이 y 에서 위(ny=1)/아래(-1)를 보는 면들의 가장자리 → 고리 목록(점 배열)
  const flat = T.filter((t) => t.every((v) => Math.abs(v[1] - y) < 1e-3) && ((t[1][2] - t[0][2]) * (t[2][0] - t[0][0]) - (t[1][0] - t[0][0]) * (t[2][2] - t[0][2])) * ny > 0)
  const cnt = new Map(); const add = (a, b) => { const k = key(a) + '|' + key(b), r = key(b) + '|' + key(a); if (cnt.has(r)) cnt.delete(r); else cnt.set(k, [a, b]) }
  flat.forEach((t) => { add(t[0], t[1]); add(t[1], t[2]); add(t[2], t[0]) })
  const next = new Map(); [...cnt.values()].forEach(([a, b]) => { const k = key(a); (next.get(k) || next.set(k, []).get(k)).push([a, b]) })
  const used = new Set(), loops = []
  for (const [k0, outs] of next) for (const e0 of outs) { const id0 = key(e0[0]) + key(e0[1]); if (used.has(id0)) continue
    const loop = []; let e = e0
    for (let n = 0; e && n < 5000; n++) { used.add(key(e[0]) + key(e[1])); loop.push(e[0]); const cand = (next.get(key(e[1])) || []).filter((c) => !used.has(key(c[0]) + key(c[1]))); e = cand[0] }
    if (loop.length > 2) loops.push(loop) }
  return loops
}
const spanOf = (loop) => { const xs = loop.map((v) => v[0]), zs = loop.map((v) => v[2]); return Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...zs) - Math.min(...zs)) }
const outerAndHoles = (ls) => { const big = Math.max(...ls.map(spanOf)); return ls.filter((l) => spanOf(l) === big || spanOf(l) <= 5.5) }
// 밝은 테두리 선(에이스랩 부품 규칙): 위쪽 바깥 둘레·구멍·사각 홈, 아래쪽 바깥 둘레·구멍. 삼각 기둥(삼각형 6개).
const outlineBars = () => {
  const k = makeKit(24), t = LINE_THICKNESS / 2
  const bar = (a, b) => { // 두 점 사이 가는 사각 막대(양 끝을 반 굵기씩 늘려 이어 붙인다)
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]] // 세 면짜리 가는 막대(삼각 기둥)
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
  }
  const draw = (loop) => loop.forEach((p, i) => { const q = loop[(i + 1) % loop.length]; bar([p[0], p[1], p[2]], [q[0], q[1], q[2]]) })
  outerAndHoles(faceLoops(plateTris, 5, 1)).forEach(draw) // 위쪽: 바깥 둘레(둥근 끝 포함)와 구멍
  faceLoops(plateTris, 4, 1).filter((l) => spanOf(l) <= 5.5).forEach(draw) // 사각 홈 바닥(높이 4)에 뚫린 구멍 둘레
  faceLoops(plateTris, 4, 1).filter((l) => spanOf(l) > 5.5 && spanOf(l) < 9.5).forEach((l) => { draw(l); l.forEach((p, i) => { const q = l[(i + 1) % l.length]; bar([p[0], 5, p[2]], [q[0], 5, q[2]]) }) }) // 사각 홈: 바닥 둘레 + 입구 둘레
  faceLoops(plateTris, 0, -1).forEach(draw) // 아래쪽: 바깥 둘레와 구멍
  return trianglesToStl(k.result())
}
const outlineStl = outlineBars(), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '관절수'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: `${NAME}_에이스랩.stl` }, { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(12프레임 ${W}×${FRAME_L} + 수 부분 ${ADD} = 전체 ${LEN}, 두께 ${T}, 구멍 1×${HOLES_N}, 한쪽 끝에 팔 두 개). 모양은 이후 다듬는다.`, pegs: [], holes: [], size: [LEN, T, W], confidence: 'draft' }
  const data = { ...r.data, size: `${W}×${LEN}×${T}mm (에이스랩: 12프레임 + 한쪽 끝 수 부분 ${ADD}mm = 전체 ${LEN}, 홀 규격사이즈 5.2 구멍 1×${HOLES_N}, 위쪽 8×8 사각 홈 1mm, 끝 양쪽에서 나온 팔 두 개(폭 ${AW}, 끝은 옆에서 볼 때 톱니바퀴 반원(15° 간격 톱니 13개·골 12개), 위에서 볼 때는 각짐, 안쪽 면에 볼록 돌기 한 개씩), 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
