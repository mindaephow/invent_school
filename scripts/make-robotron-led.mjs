// 에이스랩·로보타미주니어의 LED센서·접촉센서를 등록한다(접촉센서는 LED센서와 같은 모양에서 가운데 구 대신 지름 8·두께 5 원기둥을 1mm 박고 가운데에 깊이 4 열십자 홈 — 사용자 2026-10-26): 아래 20×45×5mm 블랙 판 + 그 위 20×35×10mm 아이보리 덩어리(한쪽 끝에 맞춰 올리고 반대쪽 10mm 는 판이 드러난다). 구멍·세부 모양은 정해지면 추가.
//   node scripts/make-robotron-led.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { roundCorners } from '../app/lib/robotron-frame-mesh.js'

const WRITE = process.argv.includes('--write')
const ONLY = (process.argv.find((a) => a.startsWith('--only=')) || '').slice(7) // 이 이름으로 시작하는 부품만(예: --only=접촉센서)
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const BASE = { L: 45, W: 20, T: 5, color: '#555555' } // 아래 판(블랙)
const TOP = { L: 35, W: 20, T: 10, color: '#f2ead9' } // 위 덩어리(아이보리, 큐보 '자주 쓰는 색'의 아이보리)
const CR = 2 // 모서리 반지름
// 판의 드러난 쪽(+x 끝, 아이보리가 안 덮은 10mm)에 1×2 구멍(피치 10, 프레임 구멍과 같은 지름 4.5) 두 개(사용자 2026-10-26)
// 구멍 위·아래에는 프레임 칸처럼 8×8, 깊이 1 사각 홈(사각 테두리)을 판다(사용자 2026-10-26).
const POCKET = 8, POCKET_D = 1
// 아이보리 덩어리 −x 쪽 끝면에 3핀 케이블 소켓(가로 8 × 세로 4, 깊이 5, 높이·폭 가운데) — 큐보 LED센서의 소켓(끝면에 8×4, 깊이 5, 몸통 가운데)을 따라 함(사용자 2026-10-26).
const SOCKET = { w: 8, h: 4, d: 5 }
const HOLE_R = 2.25, HOLE_X = BASE.L / 2 - (BASE.L - TOP.L) / 2, HOLES = [[HOLE_X, -5], [HOLE_X, 5]]
// 아이보리 덩어리 윗면 가운데에 지름 8 구를 4mm 깊이로 박는다(구 가운데가 윗면 높이 → 반구가 위로 나옴, 사용자 2026-10-26). LED 색은 이름의 색(그린·레드·옐로), 이름에 없으면 초록.
const BALL_R = 4, BALL_SINK = 4
const ballColor = (name) => (/레드/.test(name) ? '#e1493f' : /옐로/.test(name) ? '#fcc419' : '#51cf66')
// 아이보리 윗면의 구 반대쪽(−x 끝 쪽)에 +x(구·구멍 쪽, 화면 아래) 방향 화살표 하나(사용자 2026-10-26 "윗부분에 아래방향 화살표"). 두께 0.4 의 납작한 화살표를 색칠 조각으로 얹는다.
const ARROW = { color: '#555555', t: 0.4, x: -(BASE.L - TOP.L) / 2 - 10.5 } // 가운데 x: 아이보리 −x 끝(−22.5)과 구(−9) 사이의 가운데쯤
const arrowTris = () => {
  const kit = makeKit(24), { quad, P } = kit
  const pl = [[-4, -1], [0, -1], [0, -3], [4, 0], [0, 3], [0, 1], [-4, 1]] // +x 를 가리키는 화살표(길이 8, 머리 폭 6, 몸통 폭 2)
  const area = pl.reduce((a, q, i) => { const r = pl[(i + 1) % pl.length]; return a + q[0] * r[1] - r[0] * q[1] }, 0) / 2
  const poly = area > 0 ? pl : pl.slice().reverse() // 반시계
  poly.forEach((A, i) => { const B = poly[(i + 1) % poly.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], ARROW.t, B[1]), P(A[0], ARROW.t, A[1]), dz / l, 0, -dx / l) })
  ringFace(kit, poly, [], 0, -1); ringFace(kit, poly, [], ARROW.t, 1)
  return kit.result()
}
// 아이보리 윗면 가장자리에 테두리 선(폭 0.6, 두께 0.2, 가장자리에서 0.3 안쪽, 사용자 2026-10-26 "아이보리 부분에 테두리 라인") — 뷰어가 색칠 조각에는 윤곽선을 안 그려서 얇은 띠를 얹는다.
const LINE = { w: 0.6, t: 0.2, inset: 0.3, color: '#555555' }
const lineTris = () => {
  const kit = makeKit(24), { quad, P } = kit
  const rr = (L, W, r) => { const h = [[-L / 2, -W / 2], [L / 2, -W / 2], [L / 2, W / 2], [-L / 2, W / 2]]; return roundCorners(h, h, r, 8) }
  const outer = rr(TOP.L - 2 * LINE.inset, TOP.W - 2 * LINE.inset, CR - LINE.inset), inner = rr(TOP.L - 2 * (LINE.inset + LINE.w), TOP.W - 2 * (LINE.inset + LINE.w), Math.max(0.2, CR - LINE.inset - LINE.w))
  const wall = (pl, dir) => pl.forEach((A, i) => { const B = pl[(i + 1) % pl.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); if (l > 1e-9) quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], LINE.t, B[1]), P(A[0], LINE.t, A[1]), (dir * dz) / l, 0, (-dir * dx) / l) })
  wall(outer, 1); wall(inner, -1)
  ringFace(kit, outer, [inner], 0, -1); ringFace(kit, outer, [inner], LINE.t, 1)
  return kit.result()
}
// 뷰어는 색칠 조각·합친 모양을 음영 없이 한 색으로 칠해서 아이보리에 판 소켓 홈이 안 보인다 → 소켓 안쪽 바닥에 짙은 판을, 소켓 입구 둘레에 짙은 테두리 띠를 색칠 조각으로 얹어 홈이 보이게 한다(사용자 2026-10-26 "3핀소켓홈이 안뚫렸는데?").
const SOCKET_MARK = { color: '#555555', t: 0.2, rim: 0.6 }
function boxes(list) { // [[x0,x1,y0,y1,z0,z1], …] 겹치지 않는 직육면체들을 한 파일로
  const kit = makeKit(24), { quad, P } = kit
  for (const [x0, x1, y0, y1, z0, z1] of list) {
    quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0), 0, 0, -1); quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), 0, 0, 1)
    quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0), -1, 0, 0); quad(P(x1, y0, z0), P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), 1, 0, 0)
    quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1), 0, -1, 0); quad(P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1), 0, 1, 0)
  }
  return kit.result()
}
const backTris = boxes([[0, SOCKET_MARK.t, 0, SOCKET.h, -SOCKET.w / 2, SOCKET.w / 2]]) // 소켓 안쪽 바닥판
const rimW = SOCKET.w / 2 + SOCKET_MARK.rim, rimH = SOCKET.h / 2 + SOCKET_MARK.rim
const rimTris = boxes([ // 입구 둘레 띠(위·아래 + 왼·오른쪽, 겹치지 않게)
  [0, SOCKET_MARK.t, SOCKET.h / 2, rimH, -rimW, rimW], [0, SOCKET_MARK.t, -rimH, -SOCKET.h / 2, -rimW, rimW],
  [0, SOCKET_MARK.t, -SOCKET.h / 2, SOCKET.h / 2, -rimW, -SOCKET.w / 2], [0, SOCKET_MARK.t, -SOCKET.h / 2, SOCKET.h / 2, SOCKET.w / 2, rimW],
].map(([a, b, c, d, e, f]) => [a, b, c + rimH, d + rimH, e, f])) // 바닥을 0 으로 맞춰 둔다(아래 위치에서 가운데 높이를 더한다)
// 소켓 안의 핀 3개: 큐보 LED센서 3D 파일에서 잰 값 — 지름 1(반지름 0.5), 피치 2.5, 소켓 가운데 높이에서 폭 방향으로 가운데·양옆, 길이는 소켓 깊이(안쪽 바닥에서 입구면까지)와 같다.
const PIN = { r: 0.5, pitch: 2.5, color: '#d4af37' } // 핀은 금색(짙은 바닥판 앞에서 보이도록)
function pinsTris() {
  const kit = makeKit(24), { quad, tri, P } = kit, seg = 16, len = SOCKET.d
  for (const cz of [-PIN.pitch, 0, PIN.pitch]) {
    for (let k = 0; k < seg; k++) {
      const a0 = (2 * Math.PI * k) / seg, a1 = (2 * Math.PI * (k + 1)) / seg, am = (a0 + a1) / 2
      const p = (a, x) => P(x, PIN.r + PIN.r * Math.sin(a), cz + PIN.r * Math.cos(a))
      quad(p(a0, 0), p(a1, 0), p(a1, len), p(a0, len), 0, Math.sin(am), Math.cos(am))
      tri(P(0, PIN.r, cz), p(a1, 0), p(a0, 0), -1, 0, 0); tri(P(len, PIN.r, cz), p(a0, len), p(a1, len), 1, 0, 0)
    }
  }
  return kit.result()
}
// 접촉센서 버튼: 지름 8·두께 5 원기둥을 아이보리 윗면에 1mm 깊이로 박고(4mm 나옴), 가운데에 축이 들어가는 4.4×4.4(팔 폭 1.4) 열십자 홈을 깊이 4 로 판다.
const BUTTON = { r: 4, h: 5, sink: 1, crossDepth: 4, span: 4.4, arm: 1.4, color: '#555555', floorColor: '#222222', floorT: 0.2 }
const crossPoly = (span, arm) => { const a = span / 2, w = arm / 2; return [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] }
function buttonTris() {
  const kit = makeKit(48), { quad, tri, P } = kit, cross = crossPoly(BUTTON.span, BUTTON.arm), yFloor = BUTTON.h - BUTTON.crossDepth
  kit.cyl(0, 0, BUTTON.r, 0, BUTTON.h, 1) // 원기둥 옆면
  const disc = circlePts(0, 0, BUTTON.r, 48)
  ringFace(kit, disc, [], 0, -1); ringFace(kit, disc, [cross], BUTTON.h, 1) // 바닥, 윗면(열십자 홈 자리 뚫림)
  cross.forEach((A, i) => { const B = cross[(i + 1) % cross.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], yFloor, A[1]), P(B[0], yFloor, B[1]), P(B[0], BUTTON.h, B[1]), P(A[0], BUTTON.h, A[1]), -dz / l, 0, dx / l) }) // 홈 벽
  cross.forEach((A, i) => { const B = cross[(i + 1) % cross.length]; tri(P(0, yFloor, 0), P(A[0], yFloor, A[1]), P(B[0], yFloor, B[1]), 0, 1, 0) }) // 홈 바닥
  return kit.result()
}
const CROSS_LINE = { w: 0.5, t: 0.15, color: '#9ca5af' } // 열십자 홈 둘레 회색 테두리 선(사용자 2026-10-26 "열십자 안보이니까 회색으로 라인")
const crossLineTris = () => { // 열십자 모양 테두리 띠(안쪽 = 홈 모양, 바깥 = 홈보다 w 만큼 큰 열십자) — 원기둥 윗면에 얹는다
  const kit = makeKit(24), { quad, P } = kit, outer = crossPoly(BUTTON.span + 2 * CROSS_LINE.w, BUTTON.arm + 2 * CROSS_LINE.w), inner = crossPoly(BUTTON.span, BUTTON.arm)
  const wall = (pl, dir) => pl.forEach((A, i) => { const B = pl[(i + 1) % pl.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], CROSS_LINE.t, B[1]), P(A[0], CROSS_LINE.t, A[1]), (dir * dz) / l, 0, (-dir * dx) / l) })
  wall(outer, 1); wall(inner, -1)
  ringFace(kit, outer, [inner], 0, -1); ringFace(kit, outer, [inner], CROSS_LINE.t, 1)
  return kit.result()
}
const crossFloorTris = () => { // 홈 바닥 높이에 깔리는 짙은 얇은 원판(반지름 3.9): 원기둥 몸체 안에 묻혀서 열십자 홈 자리로만 보인다. (뷰어는 크기가 5mm 보다 작은 파일을 미터 단위로 보고 1000배로 키우므로 열십자만 따로 만들면 안 된다.)
  const kit = makeKit(48), r = BUTTON.r - 0.1
  kit.cyl(0, 0, r, 0, BUTTON.floorT, 1)
  const d = circlePts(0, 0, r, 48)
  ringFace(kit, d, [], 0, -1); ringFace(kit, d, [], BUTTON.floorT, 1)
  return kit.result()
}
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')

// 모서리 둥근 직사각 기둥: 길이 L(x)·폭 W(z)·두께 T, 바닥 y0, x 가운데 cx
function slab({ L, W, T }, y0, cx, holes = [], socket = null) {
  const kit = makeKit(24), { quad, P } = kit
  const rect = [[cx - L / 2, -W / 2], [cx + L / 2, -W / 2], [cx + L / 2, W / 2], [cx - L / 2, W / 2]]
  const poly = roundCorners(rect, rect, CR, 8)
  const xe = cx - L / 2 // −x 쪽 끝면 위치
  const zi = socket ? socket.w / 2 : 0
  if (socket) { // 끝 직선 변에 소켓 모서리 자리(±zi)에 꼭짓점을 넣어 끝면 조각들과 아래·윗면의 모서리가 정확히 맞게 한다
    const k = poly.findIndex((A, i) => { const B = poly[(i + 1) % poly.length]; return Math.abs(A[0] - xe) < 1e-6 && Math.abs(B[0] - xe) < 1e-6 && Math.hypot(B[0] - A[0], B[1] - A[1]) > 5 })
    const A = poly[k], B = poly[(k + 1) % poly.length]
    poly.splice(k + 1, 0, ...(A[1] < B[1] ? [[xe, -zi], [xe, zi]] : [[xe, zi], [xe, -zi]]))
  }
  poly.forEach((A, i) => { const B = poly[(i + 1) % poly.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); if (socket && Math.abs(A[0] - xe) < 1e-6 && Math.abs(B[0] - xe) < 1e-6) return; if (l > 1e-9) quad(P(A[0], y0, A[1]), P(B[0], y0, B[1]), P(B[0], y0 + T, B[1]), P(A[0], y0 + T, A[1]), dz / l, 0, -dx / l) })
  if (socket) { // 끝면(소켓 자리만 뚫린 직사각 틀) + 소켓 안쪽 벽·바닥
    const { tri } = kit, zo = W / 2 - CR, yc = y0 + T / 2, yb = yc - socket.h / 2, yt = yc + socket.h / 2, xb = xe + socket.d, yT = y0 + T
    const n = [-1, 0, 0], V = (z, y) => P(xe, y, z)
    quad(V(-zi, y0), V(zi, y0), V(zi, yb), V(-zi, yb), ...n); quad(V(-zi, yt), V(zi, yt), V(zi, yT), V(-zi, yT), ...n) // 소켓 아래·위 띠
    for (const sg of [-1, 1]) { // 소켓 양옆 조각(바깥 세로 변은 한 줄 그대로, 소켓 쪽 변에만 꼭짓점 yb·yt)
      const o = sg * zo, i = sg * zi
      for (const [p, q, r] of [[V(o, y0), V(i, y0), V(i, yb)], [V(o, y0), V(i, yb), V(i, yt)], [V(o, y0), V(i, yt), V(i, yT)], [V(o, y0), V(i, yT), V(o, yT)]]) tri(p, q, r, ...n)
    }
    quad(P(xe, yb, -zi), P(xb, yb, -zi), P(xb, yb, zi), P(xe, yb, zi), 0, 1, 0); quad(P(xe, yt, -zi), P(xb, yt, -zi), P(xb, yt, zi), P(xe, yt, zi), 0, -1, 0) // 아래·위 벽(소켓 속을 향함)
    quad(P(xe, yb, -zi), P(xb, yb, -zi), P(xb, yt, -zi), P(xe, yt, -zi), 0, 0, 1); quad(P(xe, yb, zi), P(xb, yb, zi), P(xb, yt, zi), P(xe, yt, zi), 0, 0, -1) // 옆 벽
    quad(P(xb, yb, -zi), P(xb, yt, -zi), P(xb, yt, zi), P(xb, yb, zi), -1, 0, 0) // 안쪽 바닥
  }
  const circles = holes.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
  const sqs = holes.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]]) // 반시계
  const wall = (pl, ya, yb) => pl.forEach((A, i) => { const B = pl[(i + 1) % pl.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], ya, A[1]), P(B[0], ya, B[1]), P(B[0], yb, B[1]), P(A[0], yb, A[1]), -dz / l, 0, dx / l) }) // 홈 속을 향함
  holes.forEach(([x, z]) => kit.cyl(x, z, HOLE_R, y0 + POCKET_D, y0 + T - POCKET_D, -1)) // 구멍 벽(홈 바닥 사이)
  sqs.forEach((sq) => { wall(sq, y0, y0 + POCKET_D); wall(sq, y0 + T - POCKET_D, y0 + T) }) // 아래·위 홈 벽
  ringFace(kit, poly, sqs, y0, -1); ringFace(kit, poly, sqs, y0 + T, 1) // 아래·윗면(홈 자리 뚫림)
  sqs.forEach((sq, i) => { ringFace(kit, sq, [circles[i]], y0 + POCKET_D, -1); ringFace(kit, sq, [circles[i]], y0 + T - POCKET_D, 1) }) // 홈 바닥(구멍 뚫림)
  return kit.result()
}
function sphere(r, nLon = 40, nLat = 20) { // 가운데 (0, r, 0) 인 구(뷰어가 바닥을 0 으로 맞춘다)
  const kit = makeKit(24), { tri, P } = kit
  const pt = (i, j) => { const th = (Math.PI * i) / nLat, ph = (2 * Math.PI * j) / nLon; return P(r * Math.sin(th) * Math.cos(ph), r + r * Math.cos(th), r * Math.sin(th) * Math.sin(ph)) }
  const nrm = (p) => [p[0], p[1] - r, p[2]]
  for (let i = 0; i < nLat; i++) for (let j = 0; j < nLon; j++) {
    const a = pt(i, j), b = pt(i, j + 1), c = pt(i + 1, j + 1), d = pt(i + 1, j)
    tri(a, d, c, ...nrm([(a[0] + d[0] + c[0]) / 3, (a[1] + d[1] + c[1]) / 3, (a[2] + d[2] + c[2]) / 3]))
    tri(a, c, b, ...nrm([(a[0] + c[0] + b[0]) / 3, (a[1] + c[1] + b[1]) / 3, (a[2] + c[2] + b[2]) / 3]))
  }
  return kit.result()
}
const ballStl = trianglesToStl(sphere(BALL_R))
const unpaired = (tris) => { const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(','); const e = new Map(); for (let t = 0; t < tris.length / 9; t++) { const v = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]]); for (let i = 0; i < 3; i++) { const a = v[i], b = v[(i + 1) % 3], k1 = key(...a) + '>' + key(...b), k2 = key(...b) + '>' + key(...a); if (e.has(k2)) e.delete(k2); else e.set(k1, 1) } } return e.size } // 모양 검사: 짝 없는 모서리 수(0 이어야 한다)
const lineT = lineTris(), lineStl = trianglesToStl(lineT)
console.log('테두리 선 메시 짝 없는 모서리', unpaired(lineT))
const arrowT = arrowTris(), arrowStl = trianglesToStl(arrowT)
console.log('화살표 메시 짝 없는 모서리', unpaired(arrowT))
const baseTris = slab(BASE, 0, 0, HOLES), baseStl = trianglesToStl(baseTris)
console.log('판 메시 짝 없는 모서리', unpaired(baseTris), '삼각형', baseTris.length / 9)
const topTris = slab(TOP, 0, 0, [], SOCKET), topStl = trianglesToStl(topTris) // 모양 파일은 가운데·바닥 0 기준(뷰어가 불러올 때 다시 가운데로 맞춘다) — 위치는 도형의 x·y 로 준다
console.log('아이보리 메시 짝 없는 모서리', unpaired(topTris))
const buttonT = buttonTris(), floorT = crossFloorTris(), crossLineT = crossLineTris()
console.log('버튼 메시 짝 없는 모서리', unpaired(buttonT), '열십자 바닥판', unpaired(floorT), '열십자 선', unpaired(crossLineT))
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}`)) {
    if (!/^(LED센서|접촉센서)/.test(r.data.name) || (ONLY && !r.data.name.startsWith(ONLY))) continue
    const touch = /^접촉센서/.test(r.data.name)
    const mk = (st, color, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, fileName: `${r.data.name}_${name}_${label}.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
    // 부품 하나는 한 가지 색으로만 합쳐 그려서, 위 아이보리 덩어리는 "색칠 조각"(paint)으로 판 위에 얹는다(뷰어가 모양 두 개를 합치는 계산에서 가져온 STL 두 개를 못 합친다). 판의 −x 쪽 끝에 맞춘다.
    const spec = { shapes: [mk(baseStl, BASE.color, '판'), mk(topStl, TOP.color, '몸통', { paint: true, x: -(BASE.L - TOP.L) / 2, y: BASE.T })] }
    spec.shapes.push(mk(lineStl, LINE.color, '테두리', { paint: true, x: -(BASE.L - TOP.L) / 2, y: BASE.T + TOP.T, z: 0 })) // 아이보리 윗면 가장자리 테두리 선
    const endX = -(BASE.L - TOP.L) / 2 - TOP.L / 2 // 아이보리 −x 끝면(−22.5), 소켓 안쪽 바닥 = 끝면 + 깊이
    const midY = BASE.T + TOP.T / 2
    spec.shapes.push(mk(trianglesToStl(backTris), SOCKET_MARK.color, '소켓바닥', { paint: true, x: endX + SOCKET.d - SOCKET_MARK.t / 2 + 0.01, y: midY - SOCKET.h / 2, z: 0 })) // 소켓 안쪽 바닥판
    spec.shapes.push(mk(trianglesToStl(rimTris), SOCKET_MARK.color, '소켓테두리', { paint: true, x: endX - SOCKET_MARK.t / 2, y: midY - rimH, z: 0 })) // 입구 둘레 띠(끝면 밖으로 0.2)
    spec.shapes.push(mk(trianglesToStl(pinsTris()), PIN.color, '핀', { paint: true, x: endX + SOCKET.d / 2, y: midY - PIN.r, z: 0 })) // 소켓 안 핀 3개(안쪽 바닥에서 입구면까지)
    spec.shapes.push(mk(arrowStl, ARROW.color, '화살표', { paint: true, x: ARROW.x, y: BASE.T + TOP.T, z: 0 })) // 아이보리 윗면 위에 납작하게
    if (touch) { // 접촉센서: 구 대신 버튼(원기둥 1mm 박음) + 열십자 홈 바닥판
      const topY = BASE.T + TOP.T
      spec.shapes.push(mk(trianglesToStl(buttonT), BUTTON.color, '버튼', { paint: true, x: -(BASE.L - TOP.L) / 2, y: topY - BUTTON.sink, z: 0 }))
      spec.shapes.push(mk(trianglesToStl(crossLineT), CROSS_LINE.color, '열십자선', { paint: true, x: -(BASE.L - TOP.L) / 2, y: topY - BUTTON.sink + BUTTON.h, z: 0 })) // 원기둥 윗면의 열십자 둘레 회색 선
      spec.shapes.push(mk(trianglesToStl(floorT), BUTTON.floorColor, '열십자바닥', { paint: true, x: -(BASE.L - TOP.L) / 2, y: topY - BUTTON.sink + (BUTTON.h - BUTTON.crossDepth) + 0.01, z: 0 }))
    } else spec.shapes.push(mk(ballStl, ballColor(r.data.name), '구', { paint: true, x: -(BASE.L - TOP.L) / 2, y: BASE.T + TOP.T - BALL_SINK, z: 0 })) // 구(색칠 조각): 아이보리 윗면 가운데에 지름 8, 4mm 깊이
    const connectors = { note: `LED센서(판 ${BASE.W}×${BASE.L}×${BASE.T} 블랙 + 그 위 ${TOP.W}×${TOP.L}×${TOP.T} 아이보리, 판의 −x 쪽 끝에 맞춤). 아이보리 −x 쪽 끝면에 3핀 케이블 소켓(8×4, 깊이 5, 안에 지름 1 핀 3개 — 큐보 LED센서처럼 연결용 돌기는 아님), 판의 드러난 쪽에 1×2 구멍 2개(피치 10, 지름 ${HOLE_R * 2}). 세부 모양은 정해지면 추가.`, pegs: [], holes: HOLES.map(([x, z], i) => ({ id: 'h' + (i + 1), r: HOLE_R, dir: [0, -1, 0], len: BASE.T, pos: [x, 0, z], through: true })), size: [BASE.L, BASE.T + TOP.T, BASE.W], confidence: 'draft' }
    const data = { ...r.data, size: `${BASE.W}×${BASE.L}×${BASE.T + TOP.T}mm (${label}: 블랙 판 ${BASE.W}×${BASE.L}×${BASE.T}(드러난 쪽 구멍 2개, 구멍 위·아래 8×8 깊이 1 사각 홈) + 아이보리 ${TOP.W}×${TOP.L}×${TOP.T}, 윗면 가장자리 테두리 선, 윗면 끝 쪽에 아래(+x) 방향 화살표 1개, −x 쪽 끝면에 3핀 소켓 홈(8×4×5, 안에 지름 1 핀 3개), 가운데에 지름 ${BALL_R * 2} ${/레드/.test(r.data.name) ? '빨간' : /옐로/.test(r.data.name) ? '노란' : '초록'} 구 ${BALL_SINK}mm 깊이로 박음)`, spec, connectors, primary_image: 'front' }
    if (touch) { const fix = (t) => t.replace(/LED센서/g, '접촉센서').replace(/가운데에 지름 8 [가-힣]+ 구 4mm 깊이로 박음/, `가운데에 지름 ${BUTTON.r * 2}·두께 ${BUTTON.h} 원기둥 ${BUTTON.sink}mm 깊이로 박고 가운데에 열십자 ${BUTTON.span}×${BUTTON.span} 깊이 ${BUTTON.crossDepth} 홈`); data.size = fix(data.size); connectors.note = fix(connectors.note) }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, spec.shapes.map((x) => x.color).join('+'), 'KB', Math.round((baseStl.length + topStl.length) / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
