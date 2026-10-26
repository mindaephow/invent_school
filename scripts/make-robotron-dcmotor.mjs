// 에이스랩·로보타미주니어 DC모터를 우선 20×40 직사각 기둥(블랙) + 그 위에 얹은 20×60 두께 5 판, 그 위에 다시 얹은 20×40 두께 6 기둥으로 등록한다(사용자 2026-10-27 "20, 40 직사각 기둥(블랙)", "20,60 두께5mm 사각기둥 얹어줘" — 아래 기둥 높이는 말씀이 없어 20 으로 가정, 판은 기둥 위 가운데(양쪽으로 10 씩 튀어나옴), 나머지 모양은 정해지면 추가).
//   node scripts/make-robotron-dcmotor.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const BODY = { w: 20, l: 40, h: 20, color: '#555555' } // 아래 기둥: 폭 z 20, 길이 x 40, 높이 y 20(말씀이 없어 가정)
const TOPCOL = { w: 20, l: 40, h: 6, color: '#555555' } // 판 위에 더 얹는 기둥: 20×40, 두께(높이) 6(사용자 2026-10-27 "마지막이 두께가 6이야")
const PLATE = { w: 20, l: 60, t: 5, color: '#555555' } // 위에 얹는 판: 폭 20, 길이 60, 두께 5(기둥 위 가운데)
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const box = (l, w, h) => { // 가운데 (x,z), 바닥 y=0 인 직육면체
  const kit = makeKit(24), { quad, P } = kit, [x0, x1, y0, y1, z0, z1] = [-l / 2, l / 2, 0, h, -w / 2, w / 2]
  quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), 0, 0, -1); quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), 0, 0, 1)
  quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0), -1, 0, 0); quad(P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), 1, 0, 0)
  quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1), 0, -1, 0); quad(P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1), 0, 1, 0)
  return trianglesToStl(kit.result())
}
// 너무 검정이면 안 보여서(사용자 2026-10-27) 각 직육면체의 12개 모서리를 따라 밝은 회색 가는 띠(두께 0.5)로 테두리 선을 얹는다. 색칠 조각은 모양 파일 크기가 5mm 이상이어야 해서(뷰어 규칙) 상자 전체 크기로 만든다.
const LINE = { t: 0.5, out: 0.03, color: '#b8c2cc' }
const edgeBars = (l, w, h) => {
  const kit = makeKit(24), { quad, P } = kit, { t, out } = LINE
  const bar = (x0, x1, y0, y1, z0, z1) => { // 겹쳐도 되는 직육면체
    quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), 0, 0, -1); quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), 0, 0, 1)
    quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0), -1, 0, 0); quad(P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), 1, 0, 0)
    quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1), 0, -1, 0); quad(P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1), 0, 1, 0)
  }
  const X0 = -l / 2 - out, X1 = l / 2 + out, Z0 = -w / 2 - out, Z1 = w / 2 + out, Y0 = -out, Y1 = h + out
  for (const [ya, yb] of [[Y0, Y0 + t], [Y1 - t, Y1]]) for (const [za, zb] of [[Z0, Z0 + t], [Z1 - t, Z1]]) bar(X0, X1, ya, yb, za, zb) // x 방향 모서리 4개
  for (const [ya, yb] of [[Y0, Y0 + t], [Y1 - t, Y1]]) for (const [xa, xb] of [[X0, X0 + t], [X1 - t, X1]]) bar(xa, xb, ya, yb, Z0, Z1) // z 방향 모서리 4개
  for (const [xa, xb] of [[X0, X0 + t], [X1 - t, X1]]) for (const [za, zb] of [[Z0, Z0 + t], [Z1 - t, Z1]]) bar(xa, xb, Y0, Y1, za, zb) // 높이 방향 모서리 4개
  return trianglesToStl(kit.result())
}
// 케이블 표시(사용자 2026-10-27 "큐보 모터처럼 케이블 나오는 곳 — 검정선 빨간선 두 개가 붙어서 나오게"): 아래 기둥 +x 쪽 끝면 아래쪽(바닥에서 5, 사용자 "선을 아래쪽으로 내려줘") 높이에서 지름 2 검정·빨강 선 두 가닥이 나란히 붙어 길이 12 로 나온다(안쪽 0.5 걸침).
const CABLE = { r: 1, len: 12, sink: 0.5, y: 5, colors: ['#222222', '#dc2626'] }
const cableStl = () => {
  const kit = makeKit(24), { quad, tri, P } = kit, seg = 20
  for (let k = 0; k < seg; k++) {
    const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2, p = (a, x) => P(x, CABLE.r + CABLE.r * Math.sin(a), CABLE.r * Math.cos(a))
    quad(p(a0, 0), p(a1, 0), p(a1, CABLE.len), p(a0, CABLE.len), 0, Math.sin(am), Math.cos(am))
    tri(P(0, CABLE.r, 0), p(a1, 0), p(a0, 0), -1, 0, 0); tri(P(CABLE.len, CABLE.r, 0), p(a0, CABLE.len), p(a1, CABLE.len), 1, 0, 0)
  }
  return trianglesToStl(kit.result())
}
// 판 양쪽 튀어나온 부분(각 10×20)에 규격 홀(지름 4.5) 2개씩(피치 10, 폭 방향 z ±5, x ±25), 구멍 위·아래에 8×8 깊이 1 사각 홈(사용자 2026-10-27 "양쪽에 피치에 맞춰서 규격홀 2개, 위아래로 1mm 사각홈").
const HOLE_R = 2.25, POCKET = 8, POCKET_D = 1
const PLATE_HOLES = [[-25, -5], [-25, 5], [25, -5], [25, 5]]
const plateSlab = () => {
  const kit = makeKit(24), { quad, P } = kit, { l: L, w: W, t: T } = PLATE
  const poly = [[-L / 2, -W / 2], [L / 2, -W / 2], [L / 2, W / 2], [-L / 2, W / 2]] // 반시계
  poly.forEach((A, i) => { const B = poly[(i + 1) % 4], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], T, B[1]), P(A[0], T, A[1]), dz / l, 0, -dx / l) })
  const circles = PLATE_HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24)), sqs = PLATE_HOLES.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]])
  const wall = (pl, ya, yb) => pl.forEach((A, i) => { const B = pl[(i + 1) % pl.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], ya, A[1]), P(B[0], ya, B[1]), P(B[0], yb, B[1]), P(A[0], yb, A[1]), -dz / l, 0, dx / l) })
  PLATE_HOLES.forEach(([x, z]) => kit.cyl(x, z, HOLE_R, POCKET_D, T - POCKET_D, -1)) // 구멍 벽(홈 바닥 사이)
  sqs.forEach((sq) => { wall(sq, 0, POCKET_D); wall(sq, T - POCKET_D, T) }) // 아래·위 홈 벽
  ringFace(kit, poly, sqs, 0, -1); ringFace(kit, poly, sqs, T, 1) // 아래·윗면(홈 자리 뚫림)
  sqs.forEach((sq, i) => { ringFace(kit, sq, [circles[i]], POCKET_D, -1); ringFace(kit, sq, [circles[i]], T - POCKET_D, 1) }) // 홈 바닥(구멍 뚫림)
  return trianglesToStl(kit.result())
}
// 사각 홈이 같은 블랙이라 안 보여서(사용자 2026-10-27 "얹어줘") 홈 가장자리를 둘러싸는 밝은 회색 사각 테두리 선(바깥 9×9, 안쪽 8×8, 두께 0.15)을 판 윗면과 아랫면에 얹는다.
const POCKET_LINE = { out: 9, t: 0.15 }
const pocketLines = () => {
  const kit = makeKit(24), { quad, P } = kit
  const sq = (x, z, a) => [[x - a / 2, z - a / 2], [x + a / 2, z - a / 2], [x + a / 2, z + a / 2], [x - a / 2, z + a / 2]]
  const wall = (pl, dir) => pl.forEach((A, i) => { const B = pl[(i + 1) % 4], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], POCKET_LINE.t, B[1]), P(A[0], POCKET_LINE.t, A[1]), (dir * dz) / l, 0, (-dir * dx) / l) })
  for (const [x, z] of PLATE_HOLES) { const o = sq(x, z, POCKET_LINE.out), i = sq(x, z, POCKET); wall(o, 1); wall(i, -1); ringFace(kit, o, [i], 0, -1); ringFace(kit, o, [i], POCKET_LINE.t, 1) }
  return trianglesToStl(kit.result())
}
// 홀이 안 보여서(사용자 2026-10-27 "홀에 테두리를 그려줘") 홀 가장자리에 밝은 회색 동그란 테두리 선(안쪽 지름 4.5, 바깥 지름 5.7, 두께 0.15)을 판 윗면·아랫면에 얹는다.
const HOLE_RING = { w: 0.6, t: 0.15 }
const holeRings = () => {
  const kit = makeKit(24), ro = HOLE_R + HOLE_RING.w
  for (const [x, z] of PLATE_HOLES) { kit.cyl(x, z, ro, 0, HOLE_RING.t, 1); kit.cyl(x, z, HOLE_R, 0, HOLE_RING.t, -1); const o = circlePts(x, z, ro, 32), i = circlePts(x, z, HOLE_R, 32); ringFace(kit, o, [i], 0, -1); ringFace(kit, o, [i], HOLE_RING.t, 1) }
  return trianglesToStl(kit.result())
}
// 가장 위 사각기둥 윗면, 전선(+x) 쪽 끝에서 10mm 안쪽 중심에(처음 5 → 사용자 정정 10) 규격 육각(대변 6) 두께 6 을 2mm 깊이로 끼운다(사용자 2026-10-27). 육각은 모터 육각 홈과 같은 대변 6 으로 가정, 색은 밝은 회색.
const HEXPRISM = { flat: 6, h: 6, sink: 1, fromEdge: 10, color: '#9ca5af', screwR: 1 } // screwR: 육각 가운데 지름 2 나사 구멍(깊이 6 = 육각 두께 전체, 사용자 2026-10-27)
const hexPrism = () => {
  const kit = makeKit(24), { quad, P } = kit, R = HEXPRISM.flat / Math.sqrt(3)
  const hex = Array.from({ length: 6 }, (_, k) => [R * Math.cos((Math.PI / 3) * k), R * Math.sin((Math.PI / 3) * k)]) // 반시계
  hex.forEach((A, i) => { const B = hex[(i + 1) % 6], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], HEXPRISM.h, B[1]), P(A[0], HEXPRISM.h, A[1]), dz / l, 0, -dx / l) })
  const hole = circlePts(0, 0, HEXPRISM.screwR, 24)
  kit.cyl(0, 0, HEXPRISM.screwR, 0, HEXPRISM.h, -1) // 나사 구멍 벽(구멍 속을 향함)
  ringFace(kit, hex, [hole], 0, -1); ringFace(kit, hex, [hole], HEXPRISM.h, 1)
  return trianglesToStl(kit.result())
}
// 육각 가운데 구멍을 중심으로 지름 12·높이 5 원통(벽 두께 1, 안쪽 지름 10)을 1mm 깊이로 박는다(사용자 2026-10-27 "육각형 중심구멍을 기준으로"). 색은 육각과 같은 밝은 회색으로 가정.
const TUBE = { r: 6, wall: 1, h: 5, sink: 1, color: '#555555', lineColor: '#b8c2cc', lineW: 0.3, lineT: 0.15 } // 원통은 블랙(사용자 2026-10-27) — 검은 기둥 위에서 안 보여서 윗면 안쪽·바깥 가장자리에 밝은 가는 고리 선을 얹는다
const tubeStl = () => {
  const kit = makeKit(48)
  kit.cyl(0, 0, TUBE.r, 0, TUBE.h, 1); kit.cyl(0, 0, TUBE.r - TUBE.wall, 0, TUBE.h, -1)
  kit.annulus(0, 0, TUBE.r - TUBE.wall, TUBE.r, 0, -1); kit.annulus(0, 0, TUBE.r - TUBE.wall, TUBE.r, TUBE.h, 1)
  return trianglesToStl(kit.result())
}
const tubeLines = () => { // 원통 윗면 바깥·안쪽 가장자리의 밝은 가는 고리 두 줄
  const kit = makeKit(48), ro = TUBE.r, ri = TUBE.r - TUBE.wall, w = TUBE.lineW
  for (const [a, b] of [[ro - w, ro], [ri, ri + w]]) { kit.cyl(0, 0, b, 0, TUBE.lineT, 1); kit.cyl(0, 0, a, 0, TUBE.lineT, -1); kit.annulus(0, 0, a, b, 0, -1); kit.annulus(0, 0, a, b, TUBE.lineT, 1) }
  return trianglesToStl(kit.result())
}
const tubeBaseLines = () => { // 원통 아랫부분(기둥 윗면과 만나는 자리) 바깥·안쪽 둘레에 밝은 가는 고리 두 줄(사용자 2026-10-27 "원통도 아래에 라인")
  const kit = makeKit(48), ro = TUBE.r, ri = TUBE.r - TUBE.wall, w = TUBE.lineW
  for (const [a, b] of [[ro, ro + w], [ri - w, ri]]) { kit.cyl(0, 0, b, 0, TUBE.lineT, 1); kit.cyl(0, 0, a, 0, TUBE.lineT, -1); kit.annulus(0, 0, a, b, 0, -1); kit.annulus(0, 0, a, b, TUBE.lineT, 1) }
  return trianglesToStl(kit.result())
}
const bodyStl = box(BODY.l, BODY.w, BODY.h), plateStl = plateSlab(), topColStl = box(TOPCOL.l, TOPCOL.w, TOPCOL.h)
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('DC모터')}`)) {
    // 부품 하나는 한 색으로 합쳐 그려지므로 위 판은 "색칠 조각"(paint)으로 기둥 위에 얹는다(뷰어가 모양 파일 두 개를 합치는 계산을 못 한다).
    const mk = (st, color, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, fileName: `DC모터_${name}_${label}.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
    // 말씀하신 순서대로(사용자 2026-10-27): ① 20×40 직사각 기둥(아래) ② 그 위에 20×60 두께 5 판 ③ 그 위에 20×40 두께 60 기둥을 추가
    const spec = { shapes: [mk(bodyStl, BODY.color, '기둥'), mk(plateStl, PLATE.color, '판', { paint: true, y: BODY.h }), mk(topColStl, TOPCOL.color, '추가기둥', { paint: true, y: BODY.h + PLATE.t }),
      mk(edgeBars(BODY.l, BODY.w, BODY.h), LINE.color, '기둥선', { paint: true, y: 0 }), mk(edgeBars(PLATE.l, PLATE.w, PLATE.t), LINE.color, '판선', { paint: true, y: BODY.h }), mk(edgeBars(TOPCOL.l, TOPCOL.w, TOPCOL.h), LINE.color, '추가기둥선', { paint: true, y: BODY.h + PLATE.t }),
      mk(holeRings(), LINE.color, '홀선위', { paint: true, y: BODY.h + PLATE.t }), mk(holeRings(), LINE.color, '홀선아래', { paint: true, y: BODY.h - HOLE_RING.t }),
      mk(pocketLines(), LINE.color, '홈선위', { paint: true, y: BODY.h + PLATE.t }), mk(pocketLines(), LINE.color, '홈선아래', { paint: true, y: BODY.h - POCKET_LINE.t }),
      mk(hexPrism(), HEXPRISM.color, '육각', { paint: true, x: TOPCOL.l / 2 - HEXPRISM.fromEdge, y: BODY.h + PLATE.t + TOPCOL.h - HEXPRISM.sink, z: 0 }),
      mk(tubeLines(), TUBE.lineColor, '원통선', { paint: true, x: TOPCOL.l / 2 - HEXPRISM.fromEdge, y: BODY.h + PLATE.t + TOPCOL.h - TUBE.sink + TUBE.h, z: 0 }),
      mk(tubeBaseLines(), TUBE.lineColor, '원통아래선', { paint: true, x: TOPCOL.l / 2 - HEXPRISM.fromEdge, y: BODY.h + PLATE.t + TOPCOL.h, z: 0 }),
      mk(tubeStl(), TUBE.color, '원통', { paint: true, x: TOPCOL.l / 2 - HEXPRISM.fromEdge, y: BODY.h + PLATE.t + TOPCOL.h - TUBE.sink, z: 0 }),
      ...CABLE.colors.map((c, i) => mk(cableStl(), c, i ? '빨강선' : '검정선', { paint: true, x: BODY.l / 2 - CABLE.sink + CABLE.len / 2, y: CABLE.y - CABLE.r, z: (i ? 1 : -1) * CABLE.r }))] }
    const connectors = { note: `DC모터(우선 ${BODY.w}×${BODY.l} 직사각 기둥 블랙, 높이 ${BODY.h}, 그 위 가운데에 ${PLATE.w}×${PLATE.l} 두께 ${PLATE.t} 판, 그 위에 ${TOPCOL.w}×${TOPCOL.l} 두께 ${TOPCOL.h} 기둥 — 나머지 모양·연결점은 정해지면 추가).`, pegs: [], holes: [], size: [PLATE.l, BODY.h + PLATE.t + TOPCOL.h, BODY.w], confidence: 'draft' }
    const data = { ...r.data, size: `${BODY.w}×${PLATE.l}×${BODY.h + PLATE.t + TOPCOL.h}mm (${label}: 직사각 기둥 ${BODY.w}×${BODY.l}×${BODY.h}(높이 가정) 블랙 + 위에 ${PLATE.w}×${PLATE.l} 두께 ${PLATE.t} 판(양쪽 튀어나온 곳에 규격 홀 2개씩, 위·아래 8×8 깊이 1 사각 홈, 홈·홀 둘레 밝은 테두리 선) + 그 위 ${TOPCOL.w}×${TOPCOL.l} 두께 ${TOPCOL.h} 기둥, 아래 기둥 +x 쪽 검정·빨강 케이블 표시, 위 기둥 윗면 전선 쪽 끝에서 10 안쪽 중심에 육각(대변 6, 두께 6, 1 깊이로 끼움 — 처음 2 에서 사용자 "1mm 더 올라와야", 가운데 지름 2 나사 구멍 깊이 6), 육각 중심에 지름 12·높이 5 원통(벽 1) 1 깊이로 박음, 임시)`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, 'KB', Math.round((bodyStl.length + plateStl.length + topColStl.length) / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
