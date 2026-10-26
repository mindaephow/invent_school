// 에이스랩 평판(블루): 40×30 두께 2 판 + 한쪽 끝(+x)의 판 위에 13프레임(길이 30·폭 10·두께 5)을 판의 폭(30)에 맞춰 얹는다 — 프레임 바닥을 판 바닥에 맞춰 겹쳐서 그 부분 합친 두께가 5(사용자 2026-10-27 "한쪽 끝에 13프레임을 붙여줘, 합쳐서 두께가 5mm", "위에 붙여야해"). 구멍 등 다른 모양은 정해지면 추가. 권별 수량·이름·색은 그대로.
//   node scripts/make-robotron-flatplate.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { acelabFrame, ACELAB_FRAME_STD } from '../app/lib/acelab-frame-mesh.js'
import { conformTJunctions, checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 레드: '#e1493f', 화이트: '#f2f4f8' }
const PLATE = { l: 40, w: 30, t: 2 } // 길이 x 40, 폭 z 30, 두께 y 2
// 판은 프레임 구멍 3개 자리(프레임이 덮는 끝, x=판 끝−5, z −10·0·10, 피치 10)에 규격 홀(지름 4.5)이 판까지 뚫려 있다 — 판이 구멍을 막지 않게(사용자 2026-10-27 "규격홀은 뚫린거야?").
const HOLE_R = ACELAB_FRAME_STD.boreR, HX = PLATE.l / 2 - ACELAB_FRAME_STD.width / 2, HOLES = [-10, 0, 10].map((z) => [HX, z])
const kit = makeKit(24), { quad, P } = kit, [x0, x1, y0, y1, z0, z1] = [-PLATE.l / 2, PLATE.l / 2, 0, PLATE.t, -PLATE.w / 2, PLATE.w / 2]
// 판 네 모서리는 반지름 RC 로 둥글게(사용자 2026-10-27 "전체 바닥 사각형 모서리를 좀 둥그렇게"). 바닥 사각 홈 모서리가 둥근 선 밖으로 나가지 않는 한도(2.5)다.
const RC = 2.5, ARC = 8
const rect = [[x1 - RC, z1 - RC, 0], [x0 + RC, z1 - RC, 90], [x0 + RC, z0 + RC, 180], [x1 - RC, z0 + RC, 270]].flatMap(([cx, cz, a0]) => Array.from({ length: ARC + 1 }, (_, k) => { const a = (a0 + 90 * k / ARC) * Math.PI / 180; return [cx + RC * Math.cos(a), cz + RC * Math.sin(a)] })) // 반시계(x 오른쪽·z 위) 둘레 점
rect.forEach((a, i) => { const b = rect[(i + 1) % rect.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) }) // 옆벽(바깥을 향한다)
const circles = HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
// 아래쪽 8×8 사각 홈 깊이 1: 프레임 윗면 칸 홈(8×8·깊이 1)과 같은 규격, 홀 위아래 양쪽에 홈(사용자 2026-10-27 "홀 위아래 1mm 사각 홈 파줘"). 위쪽 홈은 13프레임이 이미 가지고 있다.
const POCKET = 8, PD = 1
// 반대쪽(−x 끝) 홀: 13프레임 자리의 맞은편에 같은 규격 홀을 판 두께만큼 뚫는다. 3개 중 가운데(z=0)는 안 뚫는다(사용자 2026-10-27).
const MHOLES = [-10, 10].map((z) => [-HX, z]), mcircles = MHOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
// 반대쪽 홀 둘레 턱(사용자 2026-10-27 "두개 홀 위에 2mm정도의 턱", "그냥 원통기둥인데"): 홀마다 벽 두께 1mm 원통 기둥(바깥 지름 6.5)을 판 위로 2mm 올린다(홀은 기둥 윗면까지 뚫림).
const PADR = HOLE_R + 1, PADH = 2, PTOP = PLATE.t + PADH, mpad = MHOLES.map(([x, z]) => circlePts(x, z, PADR, 24))
const msq = MHOLES.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]]) // 바닥 8×8 사각 홈 깊이 1(사용자 2026-10-27 "바닥에 1mm 사각 홈 파줘")
MHOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, PD, PTOP, -1) // 구멍 벽(홈 바닥~기둥 윗면)
  const s4 = msq[i]; for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4]; kit.quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], PD, b[1]), P(a[0], PD, a[1]), x - (a[0] + b[0]) / 2, 0, z - (a[1] + b[1]) / 2) } // 홈 옆벽
  ringFace(kit, s4, [mcircles[i]], PD, -1) // 홈 바닥
  kit.cyl(x, z, PADR, PLATE.t, PTOP, 1) // 기둥 바깥벽
  ringFace(kit, mpad[i], [mcircles[i]], PTOP, 1) // 기둥 윗면(구멍 뚫림)
})
const sq = HOLES.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]])
HOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, PD, PLATE.t, -1) // 구멍 벽(홈 바닥~윗면)
  const s4 = sq[i]; for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4]; kit.quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], PD, b[1]), P(a[0], PD, a[1]), x - (a[0] + b[0]) / 2, 0, z - (a[1] + b[1]) / 2) } // 홈 옆벽(홈 가운데를 향한다)
  ringFace(kit, s4, [circles[i]], PD, -1) // 홈 바닥(아래를 본다, 구멍 뚫림)
})
{ // 아랫면: 사각 홈 자리를 비우고 사각 조각으로 채운다(귀 자르기가 사각 구멍에서 실패해서). 이웃 조각과 꼭짓점이 어긋나면(T자 이음) 이음새가 갈라져 보이므로 모든 칸을 같은 z 경계로 쪼갠다.
  const xa = HX - POCKET / 2, xb = HX + POCKET / 2, xma = -HX - POCKET / 2, xmb = -HX + POCKET / 2
  const zb = [...new Set([z0, z1, ...[...HOLES, ...MHOLES].flatMap(([, z]) => [z - POCKET / 2, z + POCKET / 2])])].sort((m, n) => m - n)
  const inPocket = (list, zl, zh) => list.some(([, z]) => zl >= z - POCKET / 2 - 1e-9 && zh <= z + POCKET / 2 + 1e-9)
  const clipRound = (poly) => { let out = poly; for (let i = 0; i < rect.length && out.length; i++) { const a = rect[i], b = rect[(i + 1) % rect.length], inp = out; out = []
    const side = (q) => (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
    inp.forEach((q, j) => { const r = inp[(j + 1) % inp.length], sq1 = side(q), sr = side(r)
      if (sq1 >= -1e-9) out.push(q)
      if ((sq1 > 1e-9 && sr < -1e-9) || (sq1 < -1e-9 && sr > 1e-9)) { const t = sq1 / (sq1 - sr); out.push([q[0] + (r[0] - q[0]) * t, q[1] + (r[1] - q[1]) * t]) } }) } return out }
  const flat = (xl, xh, zl, zh) => { const poly = clipRound([[xl, zl], [xh, zl], [xh, zh], [xl, zh]]); for (let i = 1; i + 1 < poly.length; i++) kit.tri(P(poly[0][0], 0, poly[0][1]), P(poly[i][0], 0, poly[i][1]), P(poly[i + 1][0], 0, poly[i + 1][1]), 0, -1, 0) } // 둥근 모서리 밖은 잘라 낸다
  for (const [xl, xh, pk] of [[x0, xma, []], [xma, xmb, MHOLES], [xmb, xa, []], [xa, xb, HOLES], [xb, x1, []]])
    for (let k = 0; k + 1 < zb.length; k++) if (!inPocket(pk, zb[k], zb[k + 1])) flat(xl, xh, zb[k], zb[k + 1]) }
ringFace(kit, rect, [...circles, ...mpad], PLATE.t, 1) // 아랫면(사각 홈 자리 뚫림)·윗면(구멍 뚫림)
// 밝은 테두리 선(사용자 2026-10-27 "밝은색으로 라인그려줘, 아무것도 안보인다"): 판·프레임 직육면체의 12개 모서리 띠와, 프레임 구멍 둘레 밝은 고리.
const LINE = { t: LINE_THICKNESS, out: 0.03 }
// 선은 실제 모양의 테두리를 따라 그린다(사용자 2026-10-27 "테두리를 따라 그리라고 누가 모두 사각형으로 그리래?"): 같은 높이 면의 가장자리를 이어 만든 고리 중 바깥 고리와 구멍 고리만 가는 막대로 깐다.
const fxs = PLATE.l / 2 - ACELAB_FRAME_STD.width / 2, FX0 = PLATE.l / 2 - ACELAB_FRAME_STD.width // 프레임 중심 x, 프레임이 판 위에서 시작하는 x
const toTris = (a, map = (v) => v) => { const T = []; for (let i = 0; i < a.length; i += 9) T.push([0, 3, 6].map((o) => map([a[i + o], a[i + o + 1], a[i + o + 2]]))); return T }
const frameTris = toTris(acelabFrame.straight(3, 1).tris, ([x, y, z]) => [z + fxs, y, -x]) // y 축 90° 돌려 판 위에 놓은 프레임(색칠 조각과 같은 변환)
const bodyTris = conformTJunctions(kit.result()) // T자 이음 메움(짝 없는 모서리 0)
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
const outerAndHoles = (loops) => { const big = Math.max(...loops.map(spanOf)); return loops.filter((l) => spanOf(l) === big || spanOf(l) <= 5.5) } // 바깥 고리 + 지름 5 안팎의 구멍 고리(8mm 칸 홈은 뺀다)
const outlineBars = () => {
  const k = makeKit(24), t = LINE.t / 2
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
  const simplify = (loop) => { // 일직선 위 점은 빼고 잇는다
    const n = loop.length, col = loop.map((p, i) => { const a = loop[(i + n - 1) % n], b = loop[(i + 1) % n], u = [p[0] - a[0], p[1] - a[1], p[2] - a[2]], v = [b[0] - p[0], b[1] - p[1], b[2] - p[2]], c = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]; return Math.hypot(...c) < 1e-6 })
    const st = col.findIndex((c) => !c), s0 = st < 0 ? 0 : st, out = [loop[s0]]
    for (let k = 1; k < n; k++) { const i = (s0 + k) % n; if (!col[i]) out.push(loop[i]) }
    return out }
  const draw = (loop, keep = () => true) => { const lp = simplify(loop); lp.forEach((p, i) => { const q = lp[(i + 1) % lp.length]; if (keep(p, q)) bar([p[0], p[1] + 0, p[2]], [q[0], q[1], q[2]]) }) }
  outerAndHoles(faceLoops(frameTris, 5, 1)).forEach((l) => draw(l)) // 프레임 윗면: 바깥 둘레(둥근 모서리 포함)와 구멍 3개
  faceLoops(frameTris, 4, 1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l)) // 8mm 칸 홈 바닥(높이 4)에 뚫린 구멍 3개 둘레
  // 프레임 윗면 8×8 사각 홈 3개: 바닥(높이 4) 둘레 + 입구(높이 5) 둘레 + 네 모서리 세로선(사용자 2026-10-27 "위쪽은 사각형 홈이 안보이는데?")
  const pockets = faceLoops(frameTris, 4, 1).filter((l) => spanOf(l) > 5.5 && spanOf(l) < 9.5)
  pockets.forEach((l) => { draw(l); l.forEach((p) => bar([p[0], 4, p[2]], [p[0], 5, p[2]])); l.forEach((p, i) => { const q = l[(i + 1) % l.length]; bar([p[0], 5, p[2]], [q[0], 5, q[2]]) }) })
  const fl = faceLoops(frameTris, 5, 1), fo = fl.find((l) => spanOf(l) === Math.max(...fl.map(spanOf))) // 프레임 바깥 고리(둥근 모양 그대로)
  fo.forEach((p, i) => { const q = fo[(i + 1) % fo.length]; bar([p[0], PLATE.t, p[2]], [q[0], PLATE.t, q[2]]) }) // 바닥판과 13프레임이 만나는 경계선(판 윗면 높이에서 프레임 바깥 모양 그대로, 사용자 2026-10-27)
  const segD = (pt, a, b) => { const dx = b[0] - a[0], dz = b[2] - a[2], tt = Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[2] - a[2]) * dz) / (dx * dx + dz * dz || 1))); return Math.hypot(pt[0] - a[0] - tt * dx, pt[2] - a[2] - tt * dz) }
  const underFrame = (pt) => { let ins = false, dm = 1e9; fo.forEach((a, i) => { const b = fo[(i + 1) % fo.length]; if ((a[2] > pt[2]) !== (b[2] > pt[2]) && pt[0] < ((b[0] - a[0]) * (pt[2] - a[2])) / (b[2] - a[2]) + a[0]) ins = !ins; dm = Math.min(dm, segD(pt, a, b)) }); return ins || dm < 0.06 }
  faceLoops(plateTris, PLATE.t, 1).filter((l) => spanOf(l) > 5.5).forEach((l) => simplify(l).forEach((p0, i, lp) => { const q0 = lp[(i + 1) % lp.length], lerp = (t) => [0, 1, 2].map((c) => p0[c] + (q0[c] - p0[c]) * t), cuts = [0, 1]
    if ((p0[0] - FX0) * (q0[0] - FX0) < 0) cuts.push((FX0 - p0[0]) / (q0[0] - p0[0]))
    cuts.sort((m, o) => m - o)
    for (let ci = 0; ci + 1 < cuts.length; ci++) { const p = lerp(cuts[ci]), q = lerp(cuts[ci + 1]), n = Math.max(p[0], q[0]) > FX0 + 1e-6 ? Math.max(1, Math.ceil(Math.hypot(q[0] - p[0], q[2] - p[2]) / 0.5)) : 1 // 프레임이 놓인 자리(x≥10)만 잘게 나눠 덮인 부분을 가린다
      for (let j = 0; j < n; j++) { const a = [0, 1, 2].map((c) => p[c] + (q[c] - p[c]) * j / n), b = [0, 1, 2].map((c) => p[c] + (q[c] - p[c]) * (j + 1) / n); if (!underFrame([(a[0] + b[0]) / 2, 0, (a[2] + b[2]) / 2])) bar(a, b) } } })) // 판 윗면 바깥 둘레 중 프레임이 덮지 않은 부분(이음매 선은 없다)
  // 판 아랫면: 바깥 둘레·사각 홈 3개(입구 y=0 와 바닥 y=PD 둘레 + 네 모서리 세로선)·홈 바닥 구멍 3개. 아랫면은 사각 조각들을 이어 붙인 면이라 가장자리 자동 추적이 틀어져(홈이 안 그려짐, 사용자 2026-10-27 "홈 테두리를 안그려서 안보여") 좌표로 직접 그린다.
  const ring = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
  ring(rect, 0)
  sq.forEach((s4) => { ring(s4, 0); ring(s4, PD); s4.forEach((c) => bar([c[0], 0, c[1]], [c[0], PD, c[1]])) })
  faceLoops(plateTris, PD, -1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l))
  mcircles.forEach((c) => { ring(c, PD); ring(c, PTOP) }) // 반대쪽 홀 2개: 홈 바닥·기둥 윗면 둘레
  msq.forEach((s4) => { ring(s4, 0); ring(s4, PD); s4.forEach((c) => bar([c[0], 0, c[1]], [c[0], PD, c[1]])) }) // 반대쪽 사각 홈 둘레
  mpad.forEach((c) => { ring(c, PTOP) }) // (판 윗면과 만나는 둘레는 위의 윗면 바깥 둘레 선이 이미 그린다) // 기둥: 판과 만나는 둘레·윗면 둘레
  return trianglesToStl(k.result())
}
const stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const frameStl = trianglesToStl(acelabFrame.straight(3, 1).tris) // 13프레임(구멍 3×1, 길이 30·폭 10·두께 5, 가운데가 원점, y 0~5)
const outlineStl = outlineBars()
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '평판(블루)'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  // 판은 바탕 모양, 13프레임은 색칠 조각(paint)으로 붙인다(뷰어가 모양 파일 두 개를 합치는 계산을 못 한다). 프레임은 길이(30)가 판 폭(z)과 나란하도록 y 축으로 90° 돌려 판 +x 끝에 붙인다.
  const fx = PLATE.l / 2 - ACELAB_FRAME_STD.width / 2 // 판 끝에서 안쪽으로 폭 10 만큼 덮는다
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '판'), fileName: `${NAME}_에이스랩.stl` }, mk(frameStl, '13프레임', { paint: true, x: fx, y: 0, z: 0, ry: Math.PI / 2 }),
    { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(${PLATE.l}×${PLATE.w} 두께 ${PLATE.t} 판 + 한쪽(+x) 끝 위에 13프레임을 겹쳐 얹음 — 그 부분 합친 두께 5). 구멍 등은 정해지면 추가.`, pegs: [], holes: [], size: [PLATE.l, 5, PLATE.w], confidence: 'draft' }
  const data = { ...r.data, size: `${PLATE.l}×${PLATE.w}×5mm (에이스랩: ${PLATE.l}×${PLATE.w} 두께 ${PLATE.t} 판 + 한쪽 끝 위에 13프레임 10×30×5 얹음, 그 부분 합친 두께 5, 프레임 구멍 3개는 판까지 뚫림, 반대쪽 끝에 같은 규격 홀 2개(가운데 제외) 뚫림·홀마다 벽 두께 1mm 원통 턱 2mm 올림, 홀 아래 8×8 사각 홈 1mm, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '판 몸통', JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
