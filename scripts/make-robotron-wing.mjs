// 에이스랩 날개: 곡면판(둥근 모서리 2.5, 물결 끝, 가운데 짧은 선 5개, 바닥 8×8 사각 홈 1mm)을 기본으로 프레임 부분을 14프레임(구멍 1×4, 길이 40)으로 바꾸고, 전체 길이 70·높이 15 로 완만히 구부린 판. 왼쪽(물결) 끝 15mm 는 구부리지 않고 곧게 이어진다(사용자 2026-10-27 "날개만들자 곡면판을 기본으로", "14프레임부분 => 14프레임", "높이 15mm 전체 70mm", "왼쪽 끝부분 15mm 곧게").
//   node scripts/make-robotron-wing.mjs [--write] [--name=날개B]
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
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8' }
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '날개B'
const SIDE = NAME.endsWith('A') ? -1 : 1 // 날개A: 왼쪽 끝 홀이 1번 구멍 쪽(z=−15), 날개B: 반대쪽(z=+15) — 둘은 거울 짝이다(사용자 2026-10-27 "지금같이 만들면 A인데?")
const ROT = NAME.endsWith('A') ? -1 : 1 // 날개A 는 모양 전체를 세로축(y)으로 180° 돌려 등록한다(사용자 2026-10-27 "날개A 180도 돌려서 등록"): 모든 점·색칠 조각 위치의 x·z 부호를 뒤집는다
const rot = (a) => { if (ROT > 0) return a; const o = new Float32Array(a.length); for (let i = 0; i < a.length; i += 3) { o[i] = -a[i]; o[i + 1] = a[i + 1]; o[i + 2] = -a[i + 2] } return o }
const LETTER = NAME.endsWith('A') ? 'A' : 'B' // 안쪽(윗면)에 표시할 글자(사용자 2026-10-27 "안쪽에 B라고 표시")
const FN = 4 // 프레임 구멍 수(14프레임 = 구멍 1×4, 길이 40)
const PLATE = { w: FN * 10, t: 2 } // 폭 z 40(= 프레임 길이), 두께 y 2 (길이는 아래 곡률로 정해진다)
const X1 = 20, XC = 10 // +x 끝, 구부러지기 시작하는 x(프레임이 덮는 10mm 는 평평하다)
// 프로필(옆모양, 사용자 2026-10-27 "옆에서 봤을때 오른쪽 끝도 평평해야해"): 프레임 쪽 10mm 평평 → 위로 휘는 원호(중심이 위) → 다시 눕는 원호(중심이 아래) → 끝 15mm 평평 — 부드러운 S 자 곡선. 두 원호는 반지름 R·각도 α 가 같다.
// 전체 70(프레임 10 + 구부러지는 구간 수평 60 = 두 원호 2R·sinα + 끝 평평 LST), 전체 높이 15: 끝 평평한 부분 바닥 높이 + 11프레임 두께(FH) = 15.
const RUN = 60, RISE = 15, LST = 15, FH = 5 // 끝 11프레임 두께 FH
const RISE_B = RISE - FH // 끝 평평한 바닥 높이(10)
const alpha = 2 * Math.atan(RISE_B / (RUN - LST)) // 2R(1−cosα) = RISE_B, 2R sinα = RUN − LST  →  tan(α/2) = RISE_B / (RUN − LST)
const BR = (RUN - LST) / (2 * Math.sin(alpha)), LA = BR * alpha, LCREASE = 2 * LA, LRAMP = LST, LARC = LCREASE + LRAMP // LARC: 펼친 판에서 XC 부터 끝까지 길이(두 원호 + 끝 평평)
const PC1 = [0, BR], P1 = [-BR * Math.sin(alpha), BR * (1 - Math.cos(alpha))], PC2 = [P1[0] - BR * Math.sin(alpha), P1[1] - BR * Math.cos(alpha)] // 첫 원호 중심, 첫 원호 끝, 둘째 원호 중심(상대 좌표, XC 기준)
const P2 = [PC2[0], PC2[1] + BR] // 둘째 원호 끝(수평 접선)
// 뷰어는 불러온 모양 파일마다 x·z 가운데를 원점으로 옮겨 놓는다 — 판이 좌우 비대칭(−15~20)이면 프레임(색칠 조각)과 2.5 어긋나 전체 폭이 37.5 로 재진다. 그래서 판·선을 x 로 SHIFT 만큼 미리 옮겨 모양 가운데가 원점이 되게 하고, 프레임 위치도 같이 옮긴다.
const XMIN = XC + P2[0] - LRAMP // 구부린 뒤 바닥 끝점 x (= XC−RUN)
const SHIFT = -(X1 + XMIN) / 2
const bendPt = ([x, y, z]) => { if (x >= XC) return [x + SHIFT, y, z]; const u = XC - x
  if (u <= LA) { const ph = u / BR, rr = BR - y; return [XC - rr * Math.sin(ph) + SHIFT, BR - rr * Math.cos(ph), z] } // 첫 원호(중심 위)
  if (u <= 2 * LA) { const be = (u - LA) / BR, rr = BR + y, ph = alpha - be; return [XC + PC2[0] + rr * Math.sin(ph) + SHIFT, PC2[1] + rr * Math.cos(ph), z] } // 둘째 원호(중심 아래)
  const s2 = u - 2 * LA; return [XC + P2[0] - s2 + SHIFT, P2[1] + y, z] } // 끝 평평한 구간(수평)
const bendTris = (arr) => { const out = new Float32Array(arr.length); for (let i = 0; i < arr.length; i += 3) out.set(bendPt([arr[i], arr[i + 1], arr[i + 2]]), i); return out } // 구부림은 방향을 보존한다(바깥 면은 그대로 바깥)
const HOLE_R = ACELAB_FRAME_STD.boreR, HX = X1 - ACELAB_FRAME_STD.width / 2, HOLES = Array.from({ length: FN }, (_, i) => (i - (FN - 1) / 2) * 10).map((z) => [HX, z])
const X0 = XC - LARC, [x0, x1, y0, y1, z0, z1] = [X0, X1, 0, PLATE.t, -PLATE.w / 2, PLATE.w / 2]
const kit = makeKit(24), { quad, P } = kit
const RC = 2.5, ARC = 8 // 네 모서리 반지름(사용자 2026-10-27)
const corner = (cx, cz, a0) => Array.from({ length: ARC + 1 }, (_, k) => { const a = (a0 + 90 * k / ARC) * Math.PI / 180; return [cx + RC * Math.cos(a), cz + RC * Math.sin(a)] })
const C0 = corner(x1 - RC, z1 - RC, 0), C2 = corner(x0 + RC, z0 + RC, 180), C3 = corner(x1 - RC, z0 + RC, 270)
// 대각선 둥근 컷(날개 모양, 사용자 2026-10-27 "대각선으로 둥그렇게 컷팅해서 날개 모양으로 오른쪽 끝이 15mm 사이즈가 되게"): 물결 끝(−x)의 한쪽 모서리를 대각선으로 잘라 끝 폭을 TIPW 로 줄이고, 대각선 두 끝은 반지름 CR 로 둥글린다.
// 컷은 홀이 있는 쪽의 반대쪽(날개A: +z, 날개B: −z). 아래는 날개A 좌표(컷이 +z)로 만들고 날개B 는 z 를 뒤집는다.
const TIPW = 15, CRS = 40, CRT = 8 // 대각선 시작(접히는 곳)·끝 쪽 둥글림 반지름
const fillet = (P0, V, N0, r) => { const u = [P0[0] - V[0], P0[1] - V[1]], w = [N0[0] - V[0], N0[1] - V[1]], ul = Math.hypot(...u), wl = Math.hypot(...w); u[0] /= ul; u[1] /= ul; w[0] /= wl; w[1] /= wl
  const th = Math.acos(Math.max(-1, Math.min(1, u[0] * w[0] + u[1] * w[1]))), t = r / Math.tan(th / 2), bis = [u[0] + w[0], u[1] + w[1]], bl = Math.hypot(...bis), Cc = [V[0] + bis[0] / bl * r / Math.sin(th / 2), V[1] + bis[1] / bl * r / Math.sin(th / 2)]
  const T1 = [V[0] + u[0] * t, V[1] + u[1] * t], T2 = [V[0] + w[0] * t, V[1] + w[1] * t], a1 = Math.atan2(T1[1] - Cc[1], T1[0] - Cc[0]), a2 = Math.atan2(T2[1] - Cc[1], T2[0] - Cc[0]), da = ((a2 - a1) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI), n = Math.max(3, Math.ceil(da / (Math.PI / 24)))
  return { pts: Array.from({ length: n + 1 }, (_, j) => [Cc[0] + r * Math.cos(a1 + da * j / n), Cc[1] + r * Math.sin(a1 + da * j / n)]), t } }
// 컷은 접히는 곳(구부러지기 시작하는 x=XC)부터 시작한다(사용자 2026-10-27 "접히는곳부터 컷팅해야해"): 둥글림이 끝나는 접점이 XC 가 되도록 윗변 위 꼭짓점을 그만큼 앞으로 둔다.
const Vtip = [x0, z0 + TIPW]; let Vtop = [XC, z1], f1 = fillet(C0[C0.length - 1], Vtop, Vtip, CRS)
for (let it = 0; it < 12; it++) { Vtop = [XC - f1.t, z1]; f1 = fillet(C0[C0.length - 1], Vtop, Vtip, CRS) }
f1.pts[0] = [XC, z1] // 접점을 접히는 곳 XC 에 정확히 둔다(반복 계산 오차 제거)
const f2 = fillet(Vtop, Vtip, [x0, z0 + RC], CRT)
const WA = 0.75, WL = 5, ZS = z0 + RC, ZE = z1 - RC
const ZEw = ZS + WL * Math.floor((Vtip[1] - f2.t - ZS) / WL) // 물결은 끝 변 곧은 구간(둥글림 시작 위)에서 정수 주기만
const FZN = Math.round((ZEw - ZS) / 0.625), fz = Array.from({ length: FZN + 1 }, (_, k) => ZS + k * (ZEw - ZS) / FZN) // 물결 한 주기를 8칸으로 나눈 z 경계(0.625 간격)
const xw = (z) => x0 + WA * (1 - Math.cos(2 * Math.PI * (z - ZS) / WL))
const flipSide = (pts) => (SIDE < 0 ? pts : pts.map(([x, z]) => [x, -z]).reverse())
const rect = flipSide([...C0, ...f1.pts, ...f2.pts, ...C2, ...C3]) // 반시계 둘레(펼친 모양, 끝이 곧은 볼록 모양 — 칸 자르기용)
const outline = flipSide([...C0, ...f1.pts, ...f2.pts, ...fz.slice().reverse().map((z) => [xw(z), z]).slice(0, -1), ...C2, ...C3])
const circles = HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const POCKET = 8, PD = 1 // 프레임 쪽 홀 아래 8×8 사각 홈 깊이 1
const sq = HOLES.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]])
HOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, PD, PLATE.t, -1) // 구멍 벽(홈 바닥~윗면)
  const s4 = sq[i]; for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4]; kit.quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], PD, b[1]), P(a[0], PD, a[1]), x - (a[0] + b[0]) / 2, 0, z - (a[1] + b[1]) / 2) } // 홈 옆벽(홈 가운데를 향한다)
  ringFace(kit, s4, [circles[i]], PD, -1) // 홈 바닥(아래를 본다, 구멍 뚫림)
})
// 구부러지는 구간은 0.5mm 간격(마디 사이 각도 1° 미만 — 뷰어는 1° 넘게 꺾인 모서리에 선을 그려서 줄무늬가 생긴다)으로 잘게 나눈다. 모든 면·옆벽이 같은 경계(x·z)를 써서 이음새가 갈라지지 않는다.
const XH = x0 + 10 // 왼쪽 끝(물결·둥근 모서리·구멍이 있는 부분)을 따로 면으로 만드는 경계 x
const CN = Math.max(2, Math.ceil(LCREASE / (BR * 0.0165))), xs = [...Array.from({ length: CN + 1 }, (_, k) => XC - k * LCREASE / CN), XH], NSEG = xs.length - 1 // 원호 구간은 반지름×0.0165 간격(마디 사이 각도 1° 미만), 경사면은 곧아서 칸 두 개(긴 칸 + 물결 칸)
const xa = HX - POCKET / 2, xb = HX + POCKET / 2
const uniq = (a) => [...new Set(a.map((v) => Math.round(v * 1e6) / 1e6))].sort((m, n) => m - n)
const zb = uniq([z0, z1, ZS, ZE, ...HOLES.flatMap(([, z]) => [z - POCKET / 2, z + POCKET / 2])]) // 칸 나누기 z 경계(성기게). 물결이 있는 끝 가까운 칸만 아래 zfine 으로 촘촘히 나누고, 칸 크기가 다른 이웃 사이 T자 이음은 맨 아래에서 conformTJunctions 가 메운다.
const zbC = uniq([z0, z1, ZS, ZE]) // 구부러진 구간(물결 칸 제외)은 폭을 세 칸(둥근 모서리·가운데)으로만 나눈다
const zfine = uniq([z0, z1, ...fz]) // 물결 칸: 홈 경계 z 는 끼우지 않는다(물결 선의 현이 어긋난다)
const clipRound = (poly) => { let out = poly; for (let i = 0; i < rect.length && out.length; i++) { const a = rect[i], b = rect[(i + 1) % rect.length], inp = out; out = []
  const side = (q) => (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
  inp.forEach((q, j) => { const r = inp[(j + 1) % inp.length], sq1 = side(q), sr = side(r)
    if (sq1 >= -1e-9) out.push(q)
    if ((sq1 > 1e-9 && sr < -1e-9) || (sq1 < -1e-9 && sr > 1e-9)) { const t = sq1 / (sq1 - sr); out.push([q[0] + (r[0] - q[0]) * t, q[1] + (r[1] - q[1]) * t]) } }) } return out }
const cellFace = (xl, xh, zl, zh, y, ny) => { const poly = clipRound([[xl, zl], [xh, zl], [xh, zh], [xl, zh]]); for (let i = 1; i + 1 < poly.length; i++) kit.tri(P(poly[0][0], y, poly[0][1]), P(poly[i][0], y, poly[i][1]), P(poly[i + 1][0], y, poly[i + 1][1]), 0, ny, 0) } // 둥근 모서리 밖은 잘라 낸다
const clipHalf = (poly, a, b) => { const side = (q) => -((b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])), out = []
  poly.forEach((q, j) => { const r = poly[(j + 1) % poly.length], sq1 = side(q), sr = side(r)
    if (sq1 >= -1e-9) out.push(q)
    if ((sq1 > 1e-9 && sr < -1e-9) || (sq1 < -1e-9 && sr > 1e-9)) { const t = sq1 / (sq1 - sr); out.push([q[0] + (r[0] - q[0]) * t, q[1] + (r[1] - q[1]) * t]) } }); return out }
const cellFaceW = (xl, xh, zl, zh, y, ny) => { // 구부러진 구간의 칸: 가운데 구간은 물결 선(두 점을 잇는 현) 오른쪽만 남기고, 모서리 구간은 둥근 호로 자른다
  if (xh > XC + 1e-9 || zl < ZS - 1e-6 || zh > ZE + 1e-6) return cellFace(xl, xh, zl, zh, y, ny)
  const poly = clipHalf([[xl, zl], [xh, zl], [xh, zh], [xl, zh]], [xw(zl), zl], [xw(zh), zh]); for (let i = 1; i + 1 < poly.length; i++) kit.tri(P(poly[0][0], y, poly[0][1]), P(poly[i][0], y, poly[i][1]), P(poly[i + 1][0], y, poly[i + 1][1]), 0, ny, 0) }
const inPocket = (list, zl, zh) => list.some(([, z]) => zl >= z - POCKET / 2 - 1e-9 && zh <= z + POCKET / 2 + 1e-9)
// 아랫면: 평평한 구간은 사각 홈 자리를 비우고, 구부러진 구간은 잘게 나눈 칸으로 채운다
const cols = [[XC, xa, []], [xa, xb, HOLES], [xb, x1, []], ...Array.from({ length: NSEG }, (_, k) => [xs[k + 1], xs[k], []])]
const zOf = (xl) => zbC
for (const [xl, xh, pk] of cols) { const zl = xh <= XC + 1e-9 ? zOf(xl) : zb; for (let k = 0; k + 1 < zl.length; k++) if (!inPocket(pk, zl[k], zl[k + 1])) cellFace(xl, xh, zl[k], zl[k + 1], 0, -1) }
// 윗면: 평평한 구간(프레임 쪽 구멍 3개 뚫림)은 다각형으로, 구부러진 구간은 같은 칸으로
const flatTop = [[XC, z0]]
rect.filter((p) => p[0] >= XC - 1e-9 && p[1] <= 0).forEach((p) => flatTop.push(p)) // 아래 변 + (+x,−z) 모서리
rect.filter((p) => p[0] > XC && p[1] > 0).forEach((p) => flatTop.push(p)); flatTop.push([XC, z1]); [...zb].reverse().filter((z) => z > z0 + 1e-9 && z < z1 - 1e-9).forEach((z) => flatTop.push([XC, z]))
ringFace(kit, flatTop, circles, PLATE.t, 1)
for (let k = 0; k < NSEG; k++) { const zl = zOf(xs[k + 1]); for (let j = 0; j + 1 < zl.length; j++) cellFace(xs[k + 1], xs[k], zl[j], zl[j + 1], PLATE.t, 1) }
// 왼쪽 끝(x ≤ XH): 물결·둥근 모서리가 있는 둘레 그대로 한 면으로 만들고, 프레임 1번 구멍(날개A, z=−15)·4번 구멍(날개B, z=+15)과 대칭인 자리에 규격 홀 1개를 뚫는다(사용자 2026-10-27 "1번 구멍과 대칭되는 위치에 1번 홀 뚫어줘"): 끝에서 5.
const endHole = [x0 + 5, SIDE < 0 ? z0 + 5 : z1 - 5], holeEnd = circlePts(endHole[0], endHole[1], HOLE_R, 24)
const endPoly = clipHalf(outline, [XH, 100], [XH, -100])
ringFace(kit, endPoly, [holeEnd], 0, -1) // 아랫면(구멍 뚫림)
ringFace(kit, endPoly, [holeEnd], PLATE.t, 1) // 윗면(구멍 뚫림)
kit.cyl(endHole[0], endHole[1], HOLE_R, 0, PLATE.t, -1) // 구멍 벽(구멍 가운데를 향한다)
// 옆벽: 둘레를 위 경계들로 잘게 나눠 잇는다
// 옆벽: 둘레를 칸 경계(x·z)마다 잘라 칸 하나당 사각형 하나로 만든다. 긴 옆벽 한 장을 그대로 두면 구부릴 때 삼각형이 굽은 곳을 가로질러 옆에서 큰 삼각형 면이 보인다(사용자 2026-10-27 "옆에서 보이는 저 삼각형").
const brkX = [...xs, xa, xb]
const densify = (a, b) => { const ts = [0, 1]; brkX.forEach((bx) => { if ((a[0] - bx) * (b[0] - bx) < 0) ts.push((bx - a[0]) / (b[0] - a[0])) }); zb.forEach((bz) => { if ((a[1] - bz) * (b[1] - bz) < 0) ts.push((bz - a[1]) / (b[1] - a[1])) }); return [...new Set(ts)].sort((m, n) => m - n).map((t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]) }
outline.forEach((a, i) => { const b = outline[(i + 1) % outline.length], d = densify(a, b); for (let k = 0; k + 1 < d.length; k++) { const p = d[k], q = d[k + 1]; if (Math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-9) quad(P(p[0], y0, p[1]), P(q[0], y0, q[1]), P(q[0], y1, q[1]), P(p[0], y1, p[1]), q[1] - p[1], 0, -(q[0] - p[0])) } }) // 옆벽(바깥을 향한다)
const bodyTris = conformTJunctions(kit.result()) // T자 이음 메움(짝 없는 모서리 0)
if (process.argv.includes('--check')) { const K = (q) => q.map((c) => Math.round(c * 1e4)).join(','), dir = new Map(); for (let i = 0; i < bodyTris.length; i += 9) for (let v = 0; v < 3; v++) { const a = [bodyTris[i + v * 3], bodyTris[i + v * 3 + 1], bodyTris[i + v * 3 + 2]], q = (v + 1) % 3, c = [bodyTris[i + q * 3], bodyTris[i + q * 3 + 1], bodyTris[i + q * 3 + 2]]; dir.set(K(a) + '>' + K(c), [a, c]) }
  let m = 0; for (const [k, [a, c]] of dir) if (!dir.has(K(c) + '>' + K(a)) && m++ < 14) console.log('열림', a.map((x) => x.toFixed(2)).join(','), '->', c.map((x) => x.toFixed(2)).join(',')) }
// 밝은 테두리 선(사용자 2026-10-27 "밝은색으로 라인그려줘, 아무것도 안보인다"): 판·프레임 직육면체의 12개 모서리 띠와, 프레임 구멍 둘레 밝은 고리.
const LINE = { t: LINE_THICKNESS, out: 0.03 }
// 선은 실제 모양의 테두리를 따라 그린다(사용자 2026-10-27 "테두리를 따라 그리라고 누가 모두 사각형으로 그리래?"): 같은 높이 면의 가장자리를 이어 만든 고리 중 바깥 고리와 구멍 고리만 가는 막대로 깐다.
const fxs = X1 - ACELAB_FRAME_STD.width / 2, FX0 = X1 - ACELAB_FRAME_STD.width // 프레임 중심 x, 프레임이 판 위에서 시작하는 x
const toTris = (a, map = (v) => v) => { const T = []; for (let i = 0; i < a.length; i += 9) T.push([0, 3, 6].map((o) => map([a[i + o], a[i + o + 1], a[i + o + 2]]))); return T }
const frameTris = toTris(acelabFrame.straight(FN, 1).tris, ([x, y, z]) => [z + fxs, y, -x]) // y 축 90° 돌려 판 위에 놓은 프레임(색칠 조각과 같은 변환)
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
  const k = makeKit(24); let t = LINE.t / 2
  const bar = (a, b) => { // 긴 선은 꺾이는 곳(XC ~ XC−LCREASE)의 경계에서 자르고, 꺾이는 구간만 0.25mm 마디로 나눠 굽은 면을 따라간다(곧은 구간은 한 마디 — 안 자르면 굽은 곳을 곧게 가로지르는 선이 허공에 뜬다)
    const ts = new Set([0, 1]); for (const bx of [XC, XC - LCREASE]) if ((a[0] - bx) * (b[0] - bx) < 0) ts.add((bx - a[0]) / (b[0] - a[0]))
    const arr = [...ts].sort((m, o) => m - o), at = (t) => a.map((c, i) => c + (b[i] - c) * t)
    for (let i = 0; i + 1 < arr.length; i++) { const p = at(arr[i]), q = at(arr[i + 1]), mx = (p[0] + q[0]) / 2, inCrease = mx < XC && mx > XC - LCREASE
      const n = inCrease ? Math.max(1, Math.ceil(Math.hypot(q[0] - p[0], q[1] - p[1], q[2] - p[2]) / 2)) : 1
      for (let j = 0; j < n; j++) bar0(p.map((c, k) => c + (q[k] - c) * j / n), p.map((c, k) => c + (q[k] - c) * (j + 1) / n)) } }
  const bar0 = (a, b) => { // 두 점 사이 가는 사각 막대(양 끝을 반 굵기씩 늘려 이어 붙인다)
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]] // 세 면짜리 가는 막대(삼각 기둥, 사각 기둥보다 삼각형 25% 적다)
    const A = C.map(([su, sv]) => corner(s0, su, sv)), B = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(A[i], A[j], B[j], B[i], m[0], m[1], m[2]) }
  }
  const simplify = (loop) => { // 일직선 위 점은 빼고 잇는다(구부러진 구간은 점 사이가 2mm 를 넘지 않게 남긴다)
    const n = loop.length, col = loop.map((p, i) => { const a = loop[(i + n - 1) % n], b = loop[(i + 1) % n], u = [p[0] - a[0], p[1] - a[1], p[2] - a[2]], v = [b[0] - p[0], b[1] - p[1], b[2] - p[2]], c = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]; return Math.hypot(...c) < 1e-6 })
    const st = col.findIndex((c) => !c), s0 = st < 0 ? 0 : st, out = [loop[s0]]; let last = loop[s0]
    for (let k = 1; k < n; k++) { const i = (s0 + k) % n, p = loop[i]; const lim = Math.min(p[0], last[0]) < XC && Math.max(p[0], last[0]) > XC - LCREASE - 0.01 ? 2 : 1e9; if (!col[i] || Math.abs(p[0] - XC) < 1e-6 || Math.abs(p[0] - (XC - LCREASE)) < 1e-6 || Math.hypot(p[0] - last[0], p[1] - last[1], p[2] - last[2]) >= lim - 1e-6) { out.push(p); last = p } }
    return out }
  const draw = (loop, keep = () => true) => { const lp = simplify(loop); lp.forEach((p, i) => { const q = lp[(i + 1) % lp.length]; if (keep(p, q)) bar([p[0], p[1] + 0, p[2]], [q[0], q[1], q[2]]) }) }
  outerAndHoles(faceLoops(frameTris, 5, 1)).forEach((l) => draw(l)) // 프레임 윗면: 바깥 둘레(둥근 모서리 포함)와 구멍 3개
  faceLoops(frameTris, 4, 1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l)) // 8mm 칸 홈 바닥(높이 4)에 뚫린 구멍 3개 둘레
  // 프레임 윗면 8×8 사각 홈 3개: 바닥(높이 4) 둘레 + 입구(높이 5) 둘레 + 네 모서리 세로선(사용자 2026-10-27 "위쪽은 사각형 홈이 안보이는데?")
  const pockets = faceLoops(frameTris, 4, 1).filter((l) => spanOf(l) > 5.5 && spanOf(l) < 9.5)
  pockets.forEach((l) => { draw(l); l.forEach((p) => bar([p[0], 4, p[2]], [p[0], 5, p[2]])); l.forEach((p, i) => { const q = l[(i + 1) % l.length]; bar([p[0], 5, p[2]], [q[0], 5, q[2]]) }) })
  const fl = faceLoops(frameTris, 5, 1), fo = fl.find((l) => spanOf(l) === Math.max(...fl.map(spanOf))) // 프레임 바깥 고리(둥근 모양 그대로)
  fo.forEach((p, i) => { const q = fo[(i + 1) % fo.length]; bar([p[0], PLATE.t, p[2]], [q[0], PLATE.t, q[2]]) }) // 바닥판과 14프레임이 만나는 경계선(판 윗면 높이에서 프레임 바깥 모양 그대로, 사용자 2026-10-27)
  const segD = (pt, a, b) => { const dx = b[0] - a[0], dz = b[2] - a[2], tt = Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[2] - a[2]) * dz) / (dx * dx + dz * dz || 1))); return Math.hypot(pt[0] - a[0] - tt * dx, pt[2] - a[2] - tt * dz) }
  const underFrame = (pt) => { let ins = false, dm = 1e9; fo.forEach((a, i) => { const b = fo[(i + 1) % fo.length]; if ((a[2] > pt[2]) !== (b[2] > pt[2]) && pt[0] < ((b[0] - a[0]) * (pt[2] - a[2])) / (b[2] - a[2]) + a[0]) ins = !ins; dm = Math.min(dm, segD(pt, a, b)) }); return ins || dm < 0.06 }
  faceLoops(plateTris, PLATE.t, 1).filter((l) => spanOf(l) > 5.5).forEach((l) => simplify(l).forEach((p0, i, lp) => { const q0 = lp[(i + 1) % lp.length], lerp = (t) => [0, 1, 2].map((c) => p0[c] + (q0[c] - p0[c]) * t), cuts = [0, 1]
    if ((p0[0] - FX0) * (q0[0] - FX0) < 0) cuts.push((FX0 - p0[0]) / (q0[0] - p0[0]))
    cuts.sort((m, o) => m - o)
    for (let ci = 0; ci + 1 < cuts.length; ci++) { const p = lerp(cuts[ci]), q = lerp(cuts[ci + 1]), n = Math.max(p[0], q[0]) > FX0 + 1e-6 ? Math.max(1, Math.ceil(Math.hypot(q[0] - p[0], q[2] - p[2]) / 0.5)) : 1 // 프레임이 놓인 자리(x≥10)만 잘게 나눠 덮인 부분을 가린다
      for (let j = 0; j < n; j++) { const a = [0, 1, 2].map((c) => p[c] + (q[c] - p[c]) * j / n), b = [0, 1, 2].map((c) => p[c] + (q[c] - p[c]) * (j + 1) / n); if (!underFrame([(a[0] + b[0]) / 2, 0, (a[2] + b[2]) / 2])) bar(a, b) } } })) // 판 윗면 바깥 둘레 중 프레임이 덮지 않은 부분(이음매 선은 없다)
  // 판 아랫면: 바깥 둘레·사각 홈 3개(입구 y=0 와 바닥 y=PD 둘레 + 네 모서리 세로선)·홈 바닥 구멍 3개. 아랫면은 사각 조각들을 이어 붙인 면이라 가장자리 자동 추적이 틀어져(홈이 안 그려짐, 사용자 2026-10-27 "홈 테두리를 안그려서 안보여") 좌표로 직접 그린다.
  const ring = (pts, y) => pts.forEach((p, i) => { const q = pts[(i + 1) % pts.length]; bar([p[0], y, p[1]], [q[0], y, q[1]]) })
  ring(outline.filter((p, i) => { const n = outline.length, a = outline[(i + n - 1) % n], b = outline[(i + 1) % n]; return Math.abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 1e-9 }), 0)
  ring(holeEnd, 0); ring(holeEnd, PLATE.t) // 왼쪽 끝 홀 둘레
  sq.forEach((s4) => { ring(s4, 0); ring(s4, PD); s4.forEach((c) => bar([c[0], 0, c[1]], [c[0], PD, c[1]])) })
  faceLoops(plateTris, PD, -1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l))
  // 구부러진 면 윗면·아랫면에 좌우(폭 방향)로 가로지르는 선 5개(사용자 2026-10-27 "둥그런 부분 윗면 아래면 좌우로 라인을 5개정도"): 호를 6등분한 자리
  const EDGE = 10 // 좌우 가장자리 10mm 씩은 선을 빼고(사용자 2026-10-27 "좌우 10mm 빼고") 가운데만 긋는다
  for (let n = 1; n <= 5; n++) { const x = XC - LARC * n / 6, zhi = Math.min(z1 - EDGE, Vtip[1] + (x - x0) * (z1 - Vtip[1]) / (Vtop[0] - x0) - 6) // 대각선 컷 안쪽에서만(날개A 좌표, 컷 쪽 +z)
    const za = z0 + EDGE, zb2 = zhi; if (zb2 <= za) continue
    for (const y of [0, PLATE.t]) bar(SIDE < 0 ? [x, y, za] : [x, y, -zb2], SIDE < 0 ? [x, y, zb2] : [x, y, -za]) } // 물결 쪽 곧은 선 5개
  // 왼쪽 끝 11프레임 테두리: 위 둘레·구멍·사각 홈, 판 윗면과 만나는 둘레
  const endTris = toTris(endFrameDev)
  outerAndHoles(faceLoops(endTris, 5, 1)).forEach((l) => draw(l))
  faceLoops(endTris, 4, 1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l))
  faceLoops(endTris, 4, 1).filter((l) => spanOf(l) > 5.5 && spanOf(l) < 9.5).forEach((l) => { draw(l); l.forEach((p, i) => { const q = l[(i + 1) % l.length]; bar([p[0], 5, p[2]], [q[0], 5, q[2]]) }) })
  { const fl2 = faceLoops(endTris, 5, 1), fo2 = fl2.find((l) => spanOf(l) === Math.max(...fl2.map(spanOf))); fo2.forEach((p, i) => { const q = fo2[(i + 1) % fo2.length]; bar([p[0], PLATE.t, p[2]], [q[0], PLATE.t, q[2]]) }) }
  t = 0.25 // 글자 선은 굵게(0.5mm) 그어 잘 보이게(사용자 2026-10-27 "글자 잘보이게")
  for (const pl of glyphLines) for (let i = 0; i + 1 < pl.length; i++) bar([pl[i][0], EY1 + 0.05, pl[i][1]], [pl[i + 1][0], EY1 + 0.05, pl[i + 1][1]]) // 글자 위에 선
  t = LINE.t / 2
  return trianglesToStl(rot(bendTris(k.result())))
}
// 안쪽(윗면) 글자 표시: 곧은 선분들로 그린 글자(A·B)를 판 위에 돋을새김(높이 0.5, 선 폭 1.4)으로 얹고, 보이도록 밝은 선도 따라 긋는다. 글자는 위에서 볼 때(프레임이 왼쪽, +z 가 위) 바르게 읽히도록 놓는다.
const GH = 14, GW = 9, GLX = XC - 30, GLZ = 0 // 글자 높이(z)·폭(x), 펼친 판에서 글자 가운데(원호 구간 한가운데)
const arc2 = (cu, cv, r, a0, a1, n = 8) => Array.from({ length: n + 1 }, (_, i) => { const a = (a0 + (a1 - a0) * i / n) * Math.PI / 180; return [cu + r * Math.cos(a), cv + r * Math.sin(a)] })
const glyphs = { B: [[[0, 0], [0, GH]], [[0, GH], [GW * 0.55, GH], ...arc2(GW * 0.55, GH * 0.75, GH * 0.25, 90, -90), [0, GH / 2]], [[0, GH / 2], [GW * 0.65, GH / 2], ...arc2(GW * 0.65, GH * 0.25, GH * 0.25, 90, -90), [0, 0]]],
  A: [[[0, 0], [GW / 2, GH]], [[GW, 0], [GW / 2, GH]], [[GW * 0.22, GH * 0.38], [GW * 0.78, GH * 0.38]]] }
const LFLIP = 1 // 글자를 180° 돌려 놓는다(날개A·B 모두, 사용자 2026-10-27 "B 글자 거꾸로 다시", "a 는 180도 돌려놔줘")
const place = ([u, v]) => [GLX - LFLIP * (u - GW / 2), GLZ + LFLIP * (v - GH / 2)] // 글자 (u 화면 오른쪽, v 화면 위) → 펼친 판 (x, z): 위에서 볼 때 프레임이 화면 왼쪽(+x 가 왼쪽)·+z 가 위로 보이는 자세에서 바로 읽힌다(사용자 2026-10-27 "글자 거꾸로 했는데"); 가운데 정렬
const glyphLines = glyphs[LETTER].map((pl) => pl.map(place))
const ek = makeKit(24), eP = ek.P, EY0 = PLATE.t - 0.05, EY1 = PLATE.t + 0.5, EWD = 0.7
for (const pl of glyphLines) for (let i = 0; i + 1 < pl.length; i++) { const a = pl[i], b = pl[i + 1], len = Math.hypot(b[0] - a[0], b[1] - a[1]); if (len < 1e-6) continue; const m = Math.max(1, Math.ceil(len / 1)) // 1mm 마디로 나눠 구부러진 면을 따라간다
  for (let j = 0; j < m; j++) { const p0 = [a[0] + (b[0] - a[0]) * j / m, a[1] + (b[1] - a[1]) * j / m], q0 = [a[0] + (b[0] - a[0]) * (j + 1) / m, a[1] + (b[1] - a[1]) * (j + 1) / m], dl = Math.hypot(q0[0] - p0[0], q0[1] - p0[1]), n = [-(q0[1] - p0[1]) / dl * EWD, (q0[0] - p0[0]) / dl * EWD], e = [(q0[0] - p0[0]) / dl * EWD, (q0[1] - p0[1]) / dl * EWD] // 선분 옆 방향 n, 앞 방향 e(양 끝을 반 폭 늘려 이어 붙인다)
    const c = [[p0[0] - e[0] - n[0], p0[1] - e[1] - n[1]], [q0[0] + e[0] - n[0], q0[1] + e[1] - n[1]], [q0[0] + e[0] + n[0], q0[1] + e[1] + n[1]], [p0[0] - e[0] + n[0], p0[1] - e[1] + n[1]]]
    ek.quad(eP(c[0][0], EY1, c[0][1]), eP(c[1][0], EY1, c[1][1]), eP(c[2][0], EY1, c[2][1]), eP(c[3][0], EY1, c[3][1]), 0, 1, 0); ek.quad(eP(c[0][0], EY0, c[0][1]), eP(c[3][0], EY0, c[3][1]), eP(c[2][0], EY0, c[2][1]), eP(c[1][0], EY0, c[1][1]), 0, -1, 0)
    for (let q = 0; q < 4; q++) { const u0 = c[q], u1 = c[(q + 1) % 4], mx = (u0[0] + u1[0]) / 2 - (c[0][0] + c[2][0]) / 2, mz = (u0[1] + u1[1]) / 2 - (c[0][1] + c[2][1]) / 2; ek.quad(eP(u0[0], EY0, u0[1]), eP(u1[0], EY0, u1[1]), eP(u1[0], EY1, u1[1]), eP(u0[0], EY1, u0[1]), mx, 0, mz) } } }
const embossTris = rot(bendTris(ek.result()))
// 왼쪽 끝 홀 자리는 11프레임(구멍 1개, 지름 10·두께 5)처럼 두껍게(사용자 2026-10-27 "이 부분을 11프레임처럼 만들어줘야해 두께를"): 오른쪽 14프레임처럼 판 바닥에 맞춰 얹은 닫힌 모양(색칠 조각)으로, 곧은 구간 위라 판 기울기를 그대로 따라 놓인다.
const endFrameRaw = Float32Array.from(acelabFrame.straight(1, 1).tris)
const endFrameDev = new Float32Array(endFrameRaw.length); for (let i = 0; i < endFrameRaw.length; i += 3) { endFrameDev[i] = endFrameRaw[i] + endHole[0]; endFrameDev[i + 1] = endFrameRaw[i + 1]; endFrameDev[i + 2] = endFrameRaw[i + 2] + endHole[1] }
const endFrameBent = rot(bendTris(endFrameDev))
const bboxOf = (arr) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < arr.length; i += 3) for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], arr[i + c]); mx[c] = Math.max(mx[c], arr[i + c]) } return { cx: (mn[0] + mx[0]) / 2, cz: (mn[2] + mx[2]) / 2, y0: mn[1] } }
const bentBody = bendTris(bodyTris), stl = trianglesToStl(rot(bentBody)), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const frameStl = trianglesToStl(acelabFrame.straight(FN, 1).tris) // 14프레임(구멍 4×1, 길이 40·폭 10·두께 5, 가운데가 원점, y 0~5)
if (process.argv.includes('--check')) { console.log('펼친 몸통', JSON.stringify(checkMesh(bodyTris))); const K = (p) => p.map((c) => Math.round(c * 1e4)).join(','), dir = new Map(); for (let i = 0; i < bodyTris.length; i += 9) for (let v = 0; v < 3; v++) { const a = [bodyTris[i + v * 3], bodyTris[i + v * 3 + 1], bodyTris[i + v * 3 + 2]], q = (v + 1) % 3, c = [bodyTris[i + q * 3], bodyTris[i + q * 3 + 1], bodyTris[i + q * 3 + 2]]; dir.set(K(a) + '>' + K(c), [a, c]) }
  let m = 0; for (const [k, [a, c]] of dir) if (!dir.has(K(c) + '>' + K(a)) && m++ < 25) console.log('열림', a.map((x) => x.toFixed(3)).join(','), '->', c.map((x) => x.toFixed(3)).join(',')) }
const outlineStl = outlineBars()
const emb = (() => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < embossTris.length; i += 3) for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], embossTris[i + c]); mx[c] = Math.max(mx[c], embossTris[i + c]) } return { cx: (mn[0] + mx[0]) / 2, cz: (mn[2] + mx[2]) / 2, y0: mn[1] } })()
const ef = bboxOf(endFrameBent), efOff = { x: ef.cx, y: ef.y0, z: ef.cz }
const embOff = { x: emb.cx, y: emb.y0, z: emb.cz } // 뷰어가 모양 파일마다 x·z 가운데를 원점·바닥을 y=0 으로 옮기므로 원래 자리로 되돌릴 값(판은 가운데가 원점)
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  // 판은 바탕 모양, 14프레임은 색칠 조각(paint)으로 붙인다(뷰어가 모양 파일 두 개를 합치는 계산을 못 한다). 프레임은 길이(30)가 판 폭(z)과 나란하도록 y 축으로 90° 돌려 판 +x 끝에 붙인다.
  const fx = X1 - ACELAB_FRAME_STD.width / 2 + SHIFT // 판 끝에서 안쪽으로 폭 10 만큼 덮는다
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '판'), fileName: `${NAME}_에이스랩.stl` }, mk(frameStl, '14프레임', { paint: true, x: ROT * fx, y: 0, z: 0, ry: ROT * Math.PI / 2 }),
    mk(trianglesToStl(embossTris), `표시${LETTER}`, { paint: true, ...embOff }), // 안쪽 글자(돋을새김)
    mk(trianglesToStl(endFrameBent), '11프레임', { paint: true, ...efOff }), // 왼쪽 끝 11프레임(두께 5)
    { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const W = Math.round((X1 - XMIN) * 10) / 10
  const connectors = { note: `${NAME}(두께 ${PLATE.t} 판 + 한쪽(+x) 끝 위에 14프레임을 겹쳐 얹고, 반대쪽을 S 자 곡선으로 올리고 끝 15mm 는 수평으로 두며 끝이 바닥에서 ${RISE}mm). 구멍 등은 정해지면 추가.`, pegs: [], holes: [], size: [W, RISE, PLATE.w], confidence: 'draft' }
  const data = { ...r.data, size: `${W}×${PLATE.w}×${RISE}mm (에이스랩: 두께 ${PLATE.t} 판, 프레임 쪽 10mm 는 평평하고 14프레임을 얹음(합친 두께 5, 프레임 구멍 4개 판까지 뚫림, 아래 8×8 사각 홈 1mm), 나머지 구부러지는 구간은 반지름 ${BR.toFixed(0)}mm 원호 두 개의 S 자 곡선으로 올라가 끝 ${LRAMP}mm 는 수평으로 평평(끝 바닥 높이 ${RISE_B} + 11프레임 ${FH} = 전체 높이 ${RISE}), 끝 한쪽을 대각선으로 둥글게 잘라 끝 폭 ${TIPW}mm 의 날개 모양, 네 모서리 둥근, 왼쪽 끝에 11프레임(두께 5)과 규격 홀 1개(${SIDE < 0 ? '1번' : '4번'} 구멍 쪽 대칭), 안쪽에 글자 ${LETTER} 표시, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bentBody) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log('높이(y 최대)', Math.max(...[bentBody, endFrameBent, embossTris].map((t) => { let m = -1e9; for (let i = 1; i < t.length; i += 3) m = Math.max(m, t[i]); return m })).toFixed(2))
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '판 몸통', JSON.stringify(checkMesh(bentBody)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
