// 에이스랩 컨트롤러: 50×80 두께 5 판(네 모서리 반지름 2.5), 위·아래 끝부분(길이 방향 양 끝)에 15프레임과 같은 홀 한 줄씩(5개, 피치 10, 끝에서 5, 지름 5.2 + 위·아래 8×8 깊이 1 사각 홈)을 뚫는다(사용자 2026-10-27 "컨트롤러 만들자, 50,80,두께 5, 위아래 끝부분에 15프레임 홀"). 모양은 이후 사용자와 다듬는다.
//   node scripts/make-robotron-geargrand.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { conformTJunctions, checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'
import { ACELAB_FRAME_STD as F } from '../app/lib/acelab-frame-mesh.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8', 블랙: '#555555', 그레이: '#9ca5af' }
const L = 80, Wd = 50, T = 5, RC = 2.5, ARC = 8, HOLE_R = F.boreR, PK = 8, PD = 1 // 길이(z)·폭(x)·두께(y), 모서리 반지름, 홀 반지름, 사각 홈 8×8·깊이 1
const y0 = 0, y1 = T, x0 = -Wd / 2, x1 = Wd / 2, z0 = -L / 2, z1 = L / 2
const kit = makeKit(24), { quad, P } = kit
const rect = [[x1 - RC, z1 - RC, 0], [x0 + RC, z1 - RC, 90], [x0 + RC, z0 + RC, 180], [x1 - RC, z0 + RC, 270]].flatMap(([cx, cz, a0]) => Array.from({ length: ARC + 1 }, (_, k) => { const a = (a0 + 90 * k / ARC) * Math.PI / 180; return [cx + RC * Math.cos(a), cz + RC * Math.sin(a)] })) // 반시계
rect.forEach((a, i) => { const b = rect[(i + 1) % rect.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) }) // 옆벽(바깥을 향함)
const xs = [-20, -10, 0, 10, 20], zs = [-(L / 2 - F.margin), L / 2 - F.margin] // 15프레임 홀 5개(피치 10) × 위·아래 끝 두 줄(끝에서 5)
const HOLES = zs.flatMap((z) => xs.map((x) => [x, z]))
const circles = HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const sqs = HOLES.map(([x, z]) => [[x - PK / 2, z - PK / 2], [x + PK / 2, z - PK / 2], [x + PK / 2, z + PK / 2], [x - PK / 2, z + PK / 2]])
HOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, y0 + PD, y1 - PD, -1) // 구멍 벽(홈 바닥~홈 바닥)
  const s4 = sqs[i]
  for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4], nx = x - (a[0] + b[0]) / 2, nz = z - (a[1] + b[1]) / 2; quad(P(a[0], y1 - PD, a[1]), P(b[0], y1 - PD, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), nx, 0, nz); quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y0 + PD, b[1]), P(a[0], y0 + PD, a[1]), nx, 0, nz) } // 사각 홈 옆벽(위·아래, 홈 속을 향함)
  ringFace(kit, s4, [circles[i]], y1 - PD, 1); ringFace(kit, s4, [circles[i]], y0 + PD, -1) // 홈 바닥(구멍 뚫림)
})
ringFace(kit, rect, sqs, y1, 1); ringFace(kit, rect, sqs, y0, -1) // 윗면·아랫면(사각 홈 자리 뚫림)
const bodyTris = conformTJunctions(kit.result())
// 윗면 아이보리 상자(사용자 2026-10-27 "60,50,두께 13(아이보리) 얹어줘"): 폭 50(판 폭과 같게)·길이 60·높이 13 직육면체를 판 가운데(z) 위에 얹는다 — 길이 80 중 가운데 60 만 덮어 양 끝 15프레임 홀 줄(z ±35, 홈 ±31~39)은 그대로 드러난다.
const BX = 50, BZ = 60, BH = 13, IVORY = '#f3eedc', by0 = 0, by1 = BH // 상자는 자기 바닥(y=0)에 맞춰 만든다 — 뷰어가 불러온 3D 모양을 바닥(최저점)에 맞춰 놓기 때문에, 판 위로 올리는 건 도형의 y 위치(판 두께 5)로 준다
const bkit = makeKit(24), bq = bkit.quad, BP = bkit.P, bx0 = -BX / 2, bx1 = BX / 2, bz0 = -BZ / 2, bz1 = BZ / 2
// 상자 윗면 홈(사용자 2026-10-27 "아이보리 윗면에서 2mm 파는 거야, 가장 아래쪽에", 50×15): 윗면 한쪽 끝(화면에서 아래쪽 = +z 끝)에 폭 50(상자 폭 전체)·길이 15·깊이 2 로 판다(끝과 양옆이 열린 단).
const NW = 50, NL = 15, ND = 2, nz0 = bz1 - NL
const prof = [[bz0, by0], [bz1, by0], [bz1, by1 - ND], [nz0, by1 - ND], [nz0, by1], [bz0, by1]] // (z, y) 반시계 단면
prof.forEach((a, i) => { if ((i >= 2 && i <= 4) || i === 5) return; const b = prof[(i + 1) % prof.length]; bq(BP(bx0, a[1], a[0]), BP(bx1, a[1], a[0]), BP(bx1, b[1], b[0]), BP(bx0, b[1], b[0]), 0, -(b[0] - a[0]), b[1] - a[1]) }) // 긴 방향 옆벽(바깥을 향함)
for (const [za, zb, ya, yb] of [[bz0, nz0, by0, by1], [nz0, bz1, by0, by1 - ND]]) { // 양 끝(x=±25) 마개
  bq(BP(bx1, ya, za), BP(bx1, ya, zb), BP(bx1, yb, zb), BP(bx1, yb, za), 1, 0, 0); bq(BP(bx0, ya, zb), BP(bx0, ya, za), BP(bx0, yb, za), BP(bx0, yb, zb), -1, 0, 0)
}
// 윗면 가운데 홈(사용자 2026-10-27 "위쪽 중심부분 14, 40, 두께 2 홈 파줘", "아래 계단이랑 붙이면 안 돼"): 계단(+z 끝 15)을 뺀 높은 윗면(z −30~15)에서 위쪽 끝(−z)에 딱 붙여(사용자 "위쪽에 딱 붙여") 폭(x) 14·길이(z) 40·깊이 2 로 판다 — 계단과는 5 떨어지고, 위쪽 끝은 열린 홈.
const PX = 14, PZ = 40, px = PX / 2, pz0 = bz0, pz1 = bz0 + PZ, y13 = by1, y11 = by1 - ND
const upper = [[bx0, bz0], [-px, bz0], [-px, pz1], [px, pz1], [px, bz0], [bx1, bz0], [bx1, nz0], [bx0, nz0]], pocket = [[-px, pz0], [px, pz0], [px, pz1], [-px, pz1]] // 반시계
const stepR = [[bx0, nz0], [bx1, nz0], [bx1, bz1], [bx0, bz1]]
// 실물 사진(사용자 2026-10-27 컨트롤러 사진)에서 잰 위치 — 본체 50×60 이 사진 가로 1170px·세로 1380px 에 해당(23.4px/mm), x 오른쪽 +, z 위쪽(사진 위) −.
const PORT_D = 3 // 포트 홈 깊이
const PORTS = [ // 왼쪽 P1·P3 = 3핀, A = 2핀(모터) / 오른쪽 RC·P2·P4 = 3핀, B = 2핀(모터)
  { n: 'P1', x: -15.5, z: -19.1, w: 8.3, h: 3.0, pins: 3 }, { n: 'P3', x: -15.5, z: -14.1, w: 8.3, h: 3.0, pins: 3 }, { n: 'A', x: -13.9, z: -3.8, w: 5.6, h: 3.2, pins: 2 },
  { n: 'RC', x: 13.5, z: -24.5, w: 8.1, h: 2.7, pins: 3 }, { n: 'P2', x: 13.5, z: -19.8, w: 8.1, h: 2.7, pins: 3 }, { n: 'P4', x: 13.5, z: -14.7, w: 8.1, h: 2.7, pins: 3 }, { n: 'B', x: 15.8, z: -4.4, w: 6.0, h: 3.2, pins: 2 }]
const BATT = [{ n: 'BATT-L', x: -15, z: 23, w: 7.5, h: 8, pins: 2 }, { n: 'BATT-R', x: 15, z: 23, w: 7.5, h: 8, pins: 2 }] // 아래 계단 좌우 2핀 홈(배터리)
const BATT_D = 3
const rectOf = (c) => [[c.x - c.w / 2, c.z - c.h / 2], [c.x + c.w / 2, c.z - c.h / 2], [c.x + c.w / 2, c.z + c.h / 2], [c.x - c.w / 2, c.z + c.h / 2]]
const portRects = PORTS.map(rectOf), battRects = BATT.map(rectOf)
const holeWalls = (r, ya, yb) => r.forEach((a, i) => { const b = r[(i + 1) % 4], cx = (r[0][0] + r[2][0]) / 2, cz = (r[0][1] + r[2][1]) / 2; bq(BP(a[0], ya, a[1]), BP(b[0], ya, b[1]), BP(b[0], yb, b[1]), BP(a[0], yb, a[1]), cx - (a[0] + b[0]) / 2, 0, cz - (a[1] + b[1]) / 2) }) // 홈 속을 향함
portRects.forEach((r) => { holeWalls(r, y13 - PORT_D, y13); ringFace(bkit, r, [], y13 - PORT_D, 1) })
battRects.forEach((r) => { holeWalls(r, y11 - BATT_D, y11); ringFace(bkit, r, [], y11 - BATT_D, 1) })
// 윗면(높이 13)·계단 바닥(높이 11)은 구멍이 많은 면이라 가로 띠로 잘라 구멍 사이 사각형들로 깐다(삼각분할 한계 때문)
const quadR = (xa, xb, za, zb) => [[xa, za], [xb, za], [xb, zb], [xa, zb]]
const tileFace = (xa, xb, za, zb, holeRects, y) => {
  const zs = [...new Set([za, zb, ...holeRects.flatMap((r) => [r[0][1], r[2][1]])])].sort((m, n) => m - n)
  for (let i = 0; i + 1 < zs.length; i++) {
    const z0 = zs[i], z1 = zs[i + 1]; if (z1 - z0 < 1e-9) continue
    const hs = holeRects.filter((r) => r[0][1] <= z0 + 1e-9 && r[2][1] >= z1 - 1e-9).map((r) => [r[0][0], r[2][0]]).sort((m, n) => m[0] - n[0])
    let cx = xa
    for (const [h0, h1] of [...hs, [xb, xb]]) { if (h0 - cx > 1e-9) bq(BP(cx, y, z0), BP(h0, y, z0), BP(h0, y, z1), BP(cx, y, z1), 0, 1, 0); cx = Math.max(cx, h1) }
  }
}
tileFace(bx0, -px, bz0, nz0, portRects.filter((r) => r[0][0] < 0), y13); tileFace(px, bx1, bz0, nz0, portRects.filter((r) => r[0][0] > 0), y13); tileFace(-px, px, pz1, nz0, [], y13)
tileFace(bx0, bx1, nz0, bz1, battRects, y11)
ringFace(bkit, pocket, [], y11, 1)
const wallV = (xa, za, xb, zb, nx, nz) => bq(BP(xa, y11, za), BP(xb, y11, zb), BP(xb, y13, zb), BP(xa, y13, za), nx, 0, nz)
wallV(bx0, nz0, bx1, nz0, 0, 1) // 계단 턱(+z 쪽을 향함)
wallV(px, pz0, px, pz1, -1, 0); wallV(-px, pz1, -px, pz0, 1, 0); wallV(px, pz1, -px, pz1, 0, -1) // 홈 벽(홈 속을 향함, 위쪽 끝은 열림)
for (const [xa, xb, ya, yb] of [[bx0, -px, by0, y13], [-px, px, by0, y11], [px, bx1, by0, y13]]) bq(BP(xa, ya, bz0), BP(xb, ya, bz0), BP(xb, yb, bz0), BP(xa, yb, bz0), 0, 0, -1) // 위쪽 끝 벽(홈 자리는 낮게)
// 색칠 조각들(뷰어는 불러온 3D 모양의 바닥·가운데를 원점에 맞추므로, 조각마다 자기 중심(x,z)·바닥(y)을 도형 위치로 준다)
const bboxOf = (t) => { const m = [1e9, 1e9, 1e9, -1e9, -1e9, -1e9]; for (let i = 0; i < t.length; i += 3) for (let k = 0; k < 3; k++) { m[k] = Math.min(m[k], t[i + k]); m[k + 3] = Math.max(m[k + 3], t[i + k]) } return m }
const boxMesh = (k, x0, x1, y0, y1, z0, z1) => { const q = k.quad, p = k.P
  q(p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0), 0, 0, -1); q(p(x1, y0, z1), p(x0, y0, z1), p(x0, y1, z1), p(x1, y1, z1), 0, 0, 1)
  q(p(x0, y0, z1), p(x0, y0, z0), p(x0, y1, z0), p(x0, y1, z1), -1, 0, 0); q(p(x1, y0, z0), p(x1, y0, z1), p(x1, y1, z1), p(x1, y1, z0), 1, 0, 0)
  q(p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1), 0, 1, 0); q(p(x0, y0, z1), p(x1, y0, z1), p(x1, y0, z0), p(x0, y0, z0), 0, -1, 0) }
const dark = makeKit(24), gold = makeKit(24), seg = makeKit(24), yel = makeKit(24), red = makeKit(24)
const sockets = [...PORTS.map((c) => ({ ...c, fy: y13 - PORT_D })), ...BATT.map((c) => ({ ...c, fy: y11 - BATT_D }))]
sockets.forEach((c) => { // 포트 바닥 검은 판 + 핀(금색)
  boxMesh(dark, c.x - c.w / 2 + 0.2, c.x + c.w / 2 - 0.2, c.fy, c.fy + 0.15, c.z - c.h / 2 + 0.2, c.z + c.h / 2 - 0.2)
  const gap = c.n.startsWith('BATT') ? 2.4 : 2.5
  for (let i = 0; i < c.pins; i++) { const along = c.n.startsWith('BATT') ? [0, (i - (c.pins - 1) / 2) * gap] : [(i - (c.pins - 1) / 2) * gap, 0]; boxMesh(gold, c.x + along[0] - 0.35, c.x + along[0] + 0.35, c.fy, c.fy + 1.6, c.z + along[1] - 0.35, c.z + along[1] + 0.35) }
})
// LED 표시판(가운데 홈 바닥): 검은 판 + 7세그먼트 "8" + 점
boxMesh(dark, -4.2, 4.2, y11, y11 + 0.5, -21.9, -9.3)
const sy = y11 + 0.5, st = 0.7, sx = 2.1, z0s = -19.5, z1s = -11.7, zm = (z0s + z1s) / 2
boxMesh(seg, -sx, sx, sy, sy + 0.15, z0s, z0s + st); boxMesh(seg, -sx, sx, sy, sy + 0.15, zm - st / 2, zm + st / 2); boxMesh(seg, -sx, sx, sy, sy + 0.15, z1s - st, z1s) // 가로 3개
for (const xx of [-sx, sx - st]) { boxMesh(seg, xx, xx + st, sy, sy + 0.15, z0s + st + 0.06, zm - st / 2 - 0.06); boxMesh(seg, xx, xx + st, sy, sy + 0.15, zm + st / 2 + 0.06, z1s - st - 0.06) } // 세로 4개(가로 조각과 겹치지 않게)
boxMesh(seg, sx + 0.5, sx + 1.1, sy, sy + 0.15, z1s - 0.6, z1s) // 점
boxMesh(dark, -1.8, 1.8, y11, y11 + 1.6, -2.4, 4.4) // ON/OFF 스위치(검은 손잡이)
const btn = (k, x, z, r) => { const c = circlePts(x, z, r, 24); k.cyl(x, z, r, y13, y13 + 1.4, 1); ringFace(k, c, [], y13 + 1.4, 1); ringFace(k, c, [], y13, -1) }
btn(yel, -15.2, 5.9, 3.6); btn(red, 15.0, 5.0, 3.8) // 모드(옐로)·스타트(레드) 버튼
// 글씨(사용자가 알려 준 이름 — 사진의 양각 글씨): 5×7 점 글꼴을 작은 상자로 쌓아 본체 위에 0.25 올린다. 사진 속 글자 크기(높이 약 3mm)에 맞춤. 상자는 서로 닿지 않게 0.04 씩 줄인다.
const GLYPH = { P: '11110,10001,10001,11110,10000,10000,10000', 1: '00100,01100,00100,00100,00100,00100,01110', 3: '11110,00001,00001,01110,00001,00001,11110', 2: '01110,10001,00001,00010,00100,01000,11111', 4: '00010,00110,01010,10010,11111,00010,00010', A: '01110,10001,10001,11111,10001,10001,10001', R: '11110,10001,10001,11110,10100,10010,10001', C: '01110,10001,10000,10000,10000,10001,01110', B: '11110,10001,10001,11110,10001,10001,11110', M: '10001,11011,10101,10101,10001,10001,10001', O: '01110,10001,10001,10001,10001,10001,01110', D: '11110,10001,10001,10001,10001,10001,11110', E: '11111,10000,10000,11110,10000,10000,11111', S: '01111,10000,10000,01110,00001,00001,11110', T: '11111,00100,00100,00100,00100,00100,00100', N: '10001,11001,10101,10101,10011,10001,10001', F: '11111,10000,10000,11110,10000,10000,10000' }
const txt = makeKit(24), TXT_H = 0.25
const label = (str, xc, zc, ps, yb) => { const total = str.length * 6 * ps - ps, x0 = xc - total / 2, zt = zc - 3.5 * ps
  ;[...str].forEach((ch, ci) => GLYPH[ch].split(',').forEach((row, r) => [...row].forEach((v, c) => { if (v === '1') { const x = x0 + ci * 6 * ps + c * ps, z = zt + r * ps; boxMesh(txt, x + 0.04, x + ps - 0.04, yb, yb + TXT_H, z + 0.04, z + ps - 0.04) } }))) }
label('P1', -22.4, -19.1, 0.36, y13); label('P3', -22.4, -14.1, 0.36, y13); label('A', -22.6, -3.8, 0.36, y13)
label('RC', 21.0, -24.5, 0.36, y13); label('P2', 21.0, -19.8, 0.36, y13); label('P4', 21.0, -14.7, 0.36, y13); label('B', 21.6, -4.4, 0.36, y13)
label('MODE', -16.2, 13.2, 0.4, y13); label('START', 15.7, 13.2, 0.4, y13)
label('ON', 4.2, -1.6, 0.33, y11); label('OFF', 4.6, 3.5, 0.33, y11)
label('BATT', 0, 22.6, 0.4, y11)
const featShapes = [[txt, '글씨', '#8a8369'], [dark, '검은부분', '#26292d'], [gold, '핀', '#c9a227'], [seg, '표시숫자', '#d4e0cf'], [yel, '모드버튼', '#e8b923'], [red, '스타트버튼', '#d22b2b']].map(([k, nm, col]) => { const t = k.result(), m = bboxOf(t); return { t, nm, col, x: (m[0] + m[3]) / 2, y: T + m[1], z: (m[2] + m[5]) / 2 } })
const boxTris = conformTJunctions(bkit.result()), boxRect = [[bx0, bz0], [bx1, bz0], [bx1, bz1], [bx0, bz1]]
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
  ring(rect, y0); ring(rect, y1); circles.forEach((c) => { ring(c, y0 + PD); ring(c, y1 - PD) }); sqs.forEach((s) => { for (const y of [y0, y0 + PD, y1 - PD, y1]) ring(s, y) })
  return trianglesToStl(k.result())
}
const boxOutline = () => { // 상자 가장자리 선(꼭짓점 4개 위·아래 사각 + 세로 4개)
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
  ring(upper, y13); ring(pocket, y11); ring(stepR, y11); ring(boxRect, by0); boxRect.forEach(([x, z]) => bar([x, by0, z], [x, z > nz0 ? y11 : y13, z])); [[bx0, nz0], [bx1, nz0]].forEach(([x, z]) => bar([x, y11, z], [x, y13, z])); pocket.forEach(([x, z]) => { if (z !== bz0) bar([x, y11, z], [x, y13, z]) }) // 위 사각·홈 사각 위아래·계단 바닥·세로선
  return trianglesToStl(k.result())
}
const boxLineStl = boxOutline(), outlineStl = outlineBars(), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const NAME = '컨트롤러'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const color = r.data.color || '블랙', hex = HEX[color] // 색이 비어 있으면 블랙(#555555)
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `컨트롤러_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: '컨트롤러_에이스랩.stl' }, { ...mk(outlineStl, '바깥선', { paint: true }), color: lineColorFor(hex) }, { ...mk(trianglesToStl(boxTris), '상자', { paint: true, y: T }), color: IVORY }, { ...mk(boxLineStl, '상자선', { paint: true, y: T }), color: lineColorFor(IVORY) }, ...featShapes.map((f) => ({ ...mk(trianglesToStl(f.t), f.nm, { paint: true, x: f.x, y: f.y, z: f.z }), color: f.col }))] }
  const dir = [0, -1, 0]
  const connectors = { note: `${NAME}(폭 ${Wd}·길이 ${L}·두께 ${T}, 모서리 반지름 ${RC}). 위·아래 끝(길이 방향 양 끝, 끝에서 ${F.margin})에 15프레임과 같은 홀 5개(피치 ${F.pitch}, 지름 ${HOLE_R * 2}, 위·아래 ${PK}×${PK}·깊이 ${PD} 사각 홈)씩 모두 10개. 위 가운데에 아이보리 상자 ${BX}×${BZ}×${BH}(폭×길이×높이)를 얹음(양 끝 홀 줄은 드러남). 윗면 높은 쪽 가운데에 폭 ${PX}·길이 ${PZ}·깊이 ${ND} 홈(위쪽 끝에 붙고 열림, 계단과 5 떨어짐). 윗면: 왼쪽 P1·P3(3핀)·A(2핀 모터)·옐로 모드 버튼, 오른쪽 RC·P2·P4(3핀)·B(2핀 모터)·레드 스타트 버튼, 가운데 홈 위 LED 표시판과 그 아래 ON/OFF 스위치, 아래 계단 좌우 2핀 배터리 홈(BATT). 상자 윗면 +z 끝에 폭 ${NW}·길이 ${NL}·깊이 ${ND} 홈(끝·양옆 열린 단). 모양은 이후 다듬는다.`, pegs: [], holes: HOLES.map(([x, z], i) => ({ id: 'h' + (i + 1), r: HOLE_R, dir, len: T, pos: [x, 0, z], through: true })), size: [Wd, T + BH, L], confidence: 'draft' }
  const data = { ...r.data, color, size: `${Wd}×${L}×${T}mm (에이스랩 컨트롤러: 판 모서리 반지름 ${RC}, 위·아래 끝 15프레임 홀 5개씩 10개 — 피치 ${F.pitch}·지름 ${HOLE_R * 2}·${PK}×${PK} 깊이 ${PD} 사각 홈, 밝은 테두리 선, 윗면 가운데에 아이보리 상자 ${BX}×${BZ}×${BH} 얹음, 상자 윗면 끝 홈 ${NW}×${NL} 깊이 ${ND} + 가운데 홈 ${PX}×${PZ} 깊이 ${ND} → 전체 높이 ${T + BH})`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris); assertPartMesh('컨트롤러 상자', boxTris); featShapes.forEach((f) => assertPartMesh('컨트롤러 ' + f.nm, f.t))
  console.log(NAME, color, hex, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '삼각형', bodyTris.length / 9, '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
