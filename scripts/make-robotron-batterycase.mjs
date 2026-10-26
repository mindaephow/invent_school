// 에이스랩 건전지케이스(그레이): 36×90 두께 5 바닥판(사용자 2026-10-27 "배터리케이스 36,90, 두께 5mm(그레이)") 위에 36×70 높이 13 상자를 가운데 얹는다("위에 36,70,13mm 올려줘"). 바닥판 위·아래 끝에 13프레임 홀 3개씩("바닥판 위아래쪽에 13프레임 홀 뚫어줘"), 홀마다 위·아래 8×8 사각 홈 깊이 1("위아래 1mm 사각홈 파줘"), 모서리는 둥글게("너무 각져있다 모서리들좀 둥그렇게 부드럽게"): 바닥판 네 모서리 반지름 2.5, 상자 세로 모서리 반지름 5, 상자 윗 가장자리 반지름 2 로 굴린다.
//   node scripts/make-robotron-batterycase.mjs [--write] [--name=건전지케이스]
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
const COLOR = '그레이', HEX = '#8c9198'
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '건전지케이스'
const BOX = { l: 36, w: 90, t: 5 } // 바닥판: 길이 x, 폭 z, 두께 y
const TOP = { l: 36, w: 70, h: 13 } // 위 상자(판 가운데에 얹음)
const RC = 2.5, RB = 5, FR = 2, ARC = 8, FN = 10 // 바닥판 모서리·상자 세로 모서리·상자 윗 가장자리 반지름, 호 분할, 윗 가장자리 단계
const [x0, x1, y0, y1, z0, z1] = [-BOX.l / 2, BOX.l / 2, 0, BOX.t, -BOX.w / 2, BOX.w / 2], [tz0, tz1, ty1] = [-TOP.w / 2, TOP.w / 2, BOX.t + TOP.h]
const kit = makeKit(24), { quad, tri, P } = kit
const arc = (cx, cz, r, a0, a1) => Array.from({ length: ARC + 1 }, (_, k) => { const a = (a0 + (a1 - a0) * k / ARC) * Math.PI / 180; return [cx + r * Math.cos(a), cz + r * Math.sin(a)] })
// 13프레임 홀: 위 상자가 없는 양 끝 띠(z ±40)의 가운데에 x −10·0·10, 피치 10, 규격 홀
const HOLE_R = ACELAB_FRAME_STD.boreR, HZ = [(z0 + tz0) / 2, (z1 + tz1) / 2], HOLES = [-10, 0, 10].flatMap((x) => HZ.map((z) => [x, z])), circles = HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const POCKET = 8, PD = 1 // 위·아래 8×8 사각 홈 깊이 1
const sq = HOLES.map(([x, z]) => [[x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2]]) // 반시계
// 바닥판 둘레(반시계, 네 모서리 반지름 RC)
const plate = [...arc(x1 - RC, z1 - RC, RC, 0, 90), ...arc(x0 + RC, z1 - RC, RC, 90, 180), ...arc(x0 + RC, z0 + RC, RC, 180, 270), ...arc(x1 - RC, z0 + RC, RC, 270, 360)]
const wall = (loop, ya, yb, dir = 1) => loop.forEach((a, i) => { const b = loop[(i + 1) % loop.length]; quad(P(a[0], ya, a[1]), P(b[0], ya, b[1]), P(b[0], yb, b[1]), P(a[0], yb, a[1]), dir * (b[1] - a[1]), 0, -dir * (b[0] - a[0])) })
wall(plate, y0, y1) // 바닥판 옆벽(바깥을 향한다)
// 홀: 가운데 좁은 벽 + 위·아래 사각 홈(벽 4면·바닥)
HOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, y0 + PD, y1 - PD, -1)
  for (const [ya, yb, floorY, ny] of [[y0, y0 + PD, y0 + PD, -1], [y1 - PD, y1, y1 - PD, 1]]) {
    const s4 = sq[i]; for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4]; quad(P(a[0], ya, a[1]), P(b[0], ya, b[1]), P(b[0], yb, b[1]), P(a[0], yb, a[1]), x - (a[0] + b[0]) / 2, 0, z - (a[1] + b[1]) / 2) } // 홈 옆벽(홈 가운데를 향한다)
    ringFace(kit, s4, [circles[i]], floorY, ny) // 홈 바닥(구멍 뚫림)
  } })
ringFace(kit, plate, sq, y0, -1) // 아랫면(사각 홈 자리 뚫림)
// 위 상자: 세로 모서리 반지름 RB, 윗 가장자리 반지름 FR 로 굴림. 옆 둘레는 inset 만큼 안쪽으로 줄인 같은 호(중심 같음)라 점 번호가 모두 맞는다.
const boxCx = TOP.l / 2 - RB, boxCz = TOP.w / 2 - RB
const boxLoop = (inset) => [...arc(boxCx, boxCz, RB - inset, 0, 90), ...arc(-boxCx, boxCz, RB - inset, 90, 180), ...arc(-boxCx, -boxCz, RB - inset, 180, 270), ...arc(boxCx, -boxCz, RB - inset, 270, 360)]
const outward = (p, up) => [p[0] - Math.max(-boxCx, Math.min(boxCx, p[0])), up, p[1] - Math.max(-boxCz, Math.min(boxCz, p[1]))]
const levels = Array.from({ length: FN + 1 }, (_, j) => { const th = (90 * j / FN) * Math.PI / 180; return { loop: boxLoop(FR * (1 - Math.cos(th))), y: ty1 - FR + FR * Math.sin(th), th } })
const base = boxLoop(0)
wall(base, y1, ty1 - FR) // 상자 옆벽
for (let j = 0; j < FN; j++) { const A = levels[j], B = levels[j + 1]; A.loop.forEach((a, i) => { const n = (i + 1) % A.loop.length, o = outward(a, Math.tan((A.th + B.th) / 4) * (RB - 0)); quad(P(a[0], A.y, a[1]), P(A.loop[n][0], A.y, A.loop[n][1]), P(B.loop[n][0], B.y, B.loop[n][1]), P(B.loop[i][0], B.y, B.loop[i][1]), o[0], o[1], o[2]) }) } // 윗 가장자리 굴림(바깥·위를 향한다)
{ const top = levels[FN].loop; for (let i = 1; i + 1 < top.length; i++) tri(P(top[0][0], ty1, top[0][1]), P(top[i][0], ty1, top[i][1]), P(top[i + 1][0], ty1, top[i + 1][1]), 0, 1, 0) } // 상자 윗면(볼록 다각형)
// 바닥판 윗면: 상자가 덮는 곳을 뺀 위·아래 두 조각(상자 둘레 호가 판 옆 가장자리와 만나는 곳에서 갈린다), 홀·사각 홈 자리 뚫림
const upper = [[x1, tz1 - RB + 0], ...arc(x1 - RC, z1 - RC, RC, 0, 90).slice(0), ...arc(x0 + RC, z1 - RC, RC, 90, 180), [x0, tz1 - RB], ...arc(-boxCx, boxCz, RB, 180, 90), ...arc(boxCx, boxCz, RB, 90, 0)]
const lower = [[x0, tz0 + RB], ...arc(x0 + RC, z0 + RC, RC, 180, 270), ...arc(x1 - RC, z0 + RC, RC, 270, 360), [x1, tz0 + RB], ...arc(boxCx, -boxCz, RB, 0, -90), ...arc(-boxCx, -boxCz, RB, -90, -180)]
const dedupe = (pts) => pts.filter((p, i) => { const q = pts[(i + 1) % pts.length]; return Math.hypot(p[0] - q[0], p[1] - q[1]) > 1e-6 })
ringFace(kit, dedupe(upper), sq.filter((s, i) => HOLES[i][1] > 0), y1, 1)
ringFace(kit, dedupe(lower), sq.filter((s, i) => HOLES[i][1] < 0), y1, 1)
const bodyTris = conformTJunctions(kit.result()) // T자 이음 메움(짝 없는 모서리 0)
// 윗면 글자 BATTERY(사용자 2026-10-27 "윗면에 battery 적어줘 (대문자)"): 곧은 선분·호로 그린 글자를 윗면에 돋을새김(높이 0.5, 선 폭 1.4)으로 얹고 밝은 선도 따라 긋는다. 글씨는 상자 긴 쪽(z)을 따라 위쪽(+z)으로 읽히게(뷰어에서 위에서 볼 때 +x 가 왼쪽·+z 가 위, 글자 윗부분이 −x(오른쪽) 쪽·글씨가 −z(아래) 쪽으로 읽힌다(사용자 2026-10-27 "글씨 180도 돌려줘": 이전 방향에서 180° 회전)) 가운데 놓는다.
const TXT = 'BATTERY', GH = 14, GW = 8, GAP = 1.2, EYH = 0.5, EWD = 0.7, GR = GH / 4
const arc2 = (cu, cv, r, a0, a1, n = 8) => Array.from({ length: n + 1 }, (_, i) => { const a = (a0 + (a1 - a0) * i / n) * Math.PI / 180; return [cu + r * Math.cos(a), cv + r * Math.sin(a)] })
const GLYPHS = {
  B: [[[0, 0], [0, GH]], [[0, GH], [GW - GR, GH], ...arc2(GW - GR, GH - GR, GR, 90, -90), [0, GH / 2]], [[0, GH / 2], [GW - GR, GH / 2], ...arc2(GW - GR, GR, GR, 90, -90), [0, 0]]],
  A: [[[0, 0], [GW / 2, GH]], [[GW, 0], [GW / 2, GH]], [[GW * 0.22, GH * 0.38], [GW * 0.78, GH * 0.38]]],
  T: [[[0, GH], [GW, GH]], [[GW / 2, GH], [GW / 2, 0]]],
  R: [[[0, 0], [0, GH]], [[0, GH], [GW - GR, GH], ...arc2(GW - GR, GH - GR, GR, 90, -90), [0, GH / 2]], [[GW * 0.4, GH / 2], [GW, 0]]],
  E: [[[GW, GH], [0, GH], [0, 0], [GW, 0]], [[0, GH / 2], [GW * 0.8, GH / 2]]],
  Y: [[[0, GH], [GW / 2, GH / 2]], [[GW, GH], [GW / 2, GH / 2]], [[GW / 2, GH / 2], [GW / 2, 0]]],
}
const TOTAL = TXT.length * GW + (TXT.length - 1) * GAP
const glyphLines = [...TXT].flatMap((ch, i) => GLYPHS[ch].map((pl) => pl.map(([u, v]) => [-(v - GH / 2), TOTAL / 2 - i * (GW + GAP) - u]))) // (x, z)
const EY0 = ty1 - 0.05, EY1 = ty1 + EYH
const ek = makeKit(24), eP = ek.P
for (const pl of glyphLines) for (let i = 0; i + 1 < pl.length; i++) { const a = pl[i], b = pl[i + 1], dl = Math.hypot(b[0] - a[0], b[1] - a[1]); if (dl < 1e-6) continue
  const n = [-(b[1] - a[1]) / dl * EWD, (b[0] - a[0]) / dl * EWD], e = [(b[0] - a[0]) / dl * EWD, (b[1] - a[1]) / dl * EWD] // 선분 옆 방향 n, 앞 방향 e(양 끝을 반 폭 늘려 이어 붙인다)
  const c = [[a[0] - e[0] - n[0], a[1] - e[1] - n[1]], [b[0] + e[0] - n[0], b[1] + e[1] - n[1]], [b[0] + e[0] + n[0], b[1] + e[1] + n[1]], [a[0] - e[0] + n[0], a[1] - e[1] + n[1]]]
  ek.quad(eP(c[0][0], EY1, c[0][1]), eP(c[1][0], EY1, c[1][1]), eP(c[2][0], EY1, c[2][1]), eP(c[3][0], EY1, c[3][1]), 0, 1, 0); ek.quad(eP(c[0][0], EY0, c[0][1]), eP(c[3][0], EY0, c[3][1]), eP(c[2][0], EY0, c[2][1]), eP(c[1][0], EY0, c[1][1]), 0, -1, 0)
  for (let q = 0; q < 4; q++) { const u0 = c[q], u1 = c[(q + 1) % 4], mx = (u0[0] + u1[0]) / 2 - (c[0][0] + c[2][0]) / 2, mz = (u0[1] + u1[1]) / 2 - (c[0][1] + c[2][1]) / 2; ek.quad(eP(u0[0], EY0, u0[1]), eP(u1[0], EY0, u1[1]), eP(u1[0], EY1, u1[1]), eP(u0[0], EY1, u0[1]), mx, 0, mz) } }
const embossTris = ek.result()
const embBox = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < embossTris.length; i += 3) for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], embossTris[i + c]); mx[c] = Math.max(mx[c], embossTris[i + c]) } return { x: (mn[0] + mx[0]) / 2, y: mn[1], z: (mn[2] + mx[2]) / 2 } })() // 뷰어가 모양 파일마다 x·z 가운데를 원점·바닥을 y=0 으로 옮기므로 원래 자리로 되돌릴 값
// 밝기 대비 테두리 선(0.1mm): 바닥판 둘레(위·아래)·상자 밑·상자 윗면 가장자리·홀 둘레·사각 홈 둘레
const outlineBars = () => {
  const k = makeKit(24); let t = LINE_THICKNESS / 2
  const bar = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) } }
  const ring = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
  ring(plate, y0); ring(plate, y1); ring(base, y1); ring(base, ty1 - FR); ring(levels[FN].loop, ty1) // 상자 밑 경계·윗 가장자리 굴림 시작 경계·윗면 가장자리(사용자 2026-10-27 "경계선도 표시해줘")
  circles.forEach((c) => { ring(c, y0 + PD); ring(c, y1 - PD) }) // 구멍 둘레(홈 바닥)
  sq.forEach((s4) => { for (const y of [y0, y0 + PD, y1 - PD, y1]) ring(s4, y); s4.forEach((c) => { bar([c[0], y0, c[1]], [c[0], y0 + PD, c[1]]); bar([c[0], y1 - PD, c[1]], [c[0], y1, c[1]]) }) }) // 사각 홈 둘레·모서리 세로선
  t = 0.25 // 글자 선은 굵게(0.5mm) 그어 잘 보이게
  for (const pl of glyphLines) for (let i = 0; i + 1 < pl.length; i++) bar([pl[i][0], EY1 + 0.05, pl[i][1]], [pl[i + 1][0], EY1 + 0.05, pl[i + 1][1]])
  return trianglesToStl(k.result())
}
// 전선 두 가닥(사용자 2026-10-27 "위쪽에 전선 두개 나오게 해줘=>dc모터 참고"): DC모터와 같은 규격(지름 2 검정·빨강 선이 나란히 붙어 길이 12, 안쪽 0.5 걸침)으로 상자 위쪽(+z) 끝면 가운데 높이에서 나온다.
const CABLE = { r: 1, len: 12, sink: 0.5, y: BOX.t + TOP.h / 2, colors: ['#222222', '#dc2626'] }
const cableStl = () => {
  const ck = makeKit(24), seg = 20
  for (let k = 0; k < seg; k++) {
    const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2, p = (a, z) => ck.P(CABLE.r * Math.cos(a), CABLE.r + CABLE.r * Math.sin(a), z)
    ck.quad(p(a0, 0), p(a1, 0), p(a1, CABLE.len), p(a0, CABLE.len), Math.cos(am), Math.sin(am), 0)
    ck.tri(ck.P(0, CABLE.r, 0), p(a1, 0), p(a0, 0), 0, 0, -1); ck.tri(ck.P(0, CABLE.r, CABLE.len), p(a0, CABLE.len), p(a1, CABLE.len), 0, 0, 1)
  }
  return trianglesToStl(ck.result())
}
const stl = trianglesToStl(bodyTris), outlineStl = outlineBars(), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: HEX, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '몸통'), fileName: `${NAME}_에이스랩.stl` }, mk(trianglesToStl(embossTris), '글자', { paint: true, ...embBox }),
    { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(HEX) },
    ...CABLE.colors.map((c, i) => ({ ...mk(cableStl(), i ? '빨강선' : '검정선', { paint: true, x: (i ? 1 : -1) * CABLE.r, y: CABLE.y - CABLE.r, z: tz1 - CABLE.sink + CABLE.len / 2 }), color: c }))] }
  const connectors = { note: `${NAME}(${BOX.l}×${BOX.w} 두께 ${BOX.t} 바닥판 + 위에 ${TOP.l}×${TOP.w} 높이 ${TOP.h} 상자). 구멍 등은 정해지면 추가.`, pegs: [], holes: [], size: [BOX.l, ty1 + EYH, BOX.w], confidence: 'draft' }
  const data = { ...r.data, color: COLOR, size: `${BOX.l}×${BOX.w}×${ty1}mm (에이스랩: 두께 ${BOX.t} 바닥판 + 위에 ${TOP.l}×${TOP.w} 높이 ${TOP.h} 상자(가운데), 바닥판 위·아래 끝에 13프레임 홀 3개씩 6개·홀마다 위아래 8×8 사각 홈 1mm, 모서리 둥글림(판 ${RC}·상자 ${RB}·윗 가장자리 ${FR}), 밝은 테두리 선, 윗면에 글자 BATTERY(돋을새김 0.5), 위쪽(+z)에 검정·빨강 전선 두 가닥 길이 12)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, COLOR, HEX, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
