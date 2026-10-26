// 에이스랩 곡면판: 평판(40×30 두께 2, 한쪽 끝 위에 13프레임, 둥근 모서리 2.5, 바닥 8×8 사각 홈 1mm)과 같은 모습에서 프레임 반대쪽(−x)을 자연스럽게(원호) 위로 구부려 끝이 바닥에서 15mm, 좌우 폭 35mm 가 되게 한다. 반대쪽 홀·원통 턱·홈은 없다(사용자 2026-10-27 "곡면판 만들자… 오른쪽 홀부분은 삭제").
//   node scripts/make-robotron-curvedplate.mjs [--write] [--name=곡면판]
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
const PLATE = { w: 30, t: 2 } // 폭 z 30, 두께 y 2 (길이는 아래 곡률로 정해진다)
const X1 = 20, XC = 10 // +x 끝, 구부러지기 시작하는 x(프레임이 덮는 10mm 는 평평하다)
// 구부림: 판 바닥면이 XC 에서 평평한 면에 접하는 원호(반지름 R, 중심은 판 위쪽). 바닥 끝점이 x=XC−25(좌우 폭 35), 판 윗면 끝 모서리 높이가 15 가 되도록 각도 φ 를 푼다.
const RUN = 25, RISE = 15
const sol = (() => { const f = (p) => RUN * Math.tan(p / 2) + PLATE.t * Math.cos(p) - RISE; let lo = 0.3, hi = 1.5; for (let i = 0; i < 80; i++) { const m = (lo + hi) / 2; if (f(m) < 0) lo = m; else hi = m } const phi = (lo + hi) / 2; return { phi, R: RUN / Math.sin(phi) } })()
const BR = sol.R, BPHI = sol.phi, LARC = BR * BPHI // 바닥면 호 길이
// 뷰어는 불러온 모양 파일마다 x·z 가운데를 원점으로 옮겨 놓는다 — 판이 좌우 비대칭(−15~20)이면 프레임(색칠 조각)과 2.5 어긋나 전체 폭이 37.5 로 재진다. 그래서 판·선을 x 로 SHIFT 만큼 미리 옮겨 모양 가운데가 원점이 되게 하고, 프레임 위치도 같이 옮긴다.
const SHIFT = -(X1 + (XC - BR * Math.sin(BPHI))) / 2
const bendPt = ([x, y, z]) => { if (x >= XC) return [x + SHIFT, y, z]; const ph = (XC - x) / BR, rr = BR - y; return [XC - rr * Math.sin(ph) + SHIFT, BR - rr * Math.cos(ph), z] }
const bendTris = (arr) => { const out = new Float32Array(arr.length); for (let i = 0; i < arr.length; i += 3) out.set(bendPt([arr[i], arr[i + 1], arr[i + 2]]), i); return out } // 구부림은 방향을 보존한다(바깥 면은 그대로 바깥)
const HOLE_R = ACELAB_FRAME_STD.boreR, HX = X1 - ACELAB_FRAME_STD.width / 2, HOLES = [-10, 0, 10].map((z) => [HX, z])
const X0 = XC - LARC, [x0, x1, y0, y1, z0, z1] = [X0, X1, 0, PLATE.t, -PLATE.w / 2, PLATE.w / 2]
const kit = makeKit(24), { quad, P } = kit
const RC = 2.5, ARC = 8 // 네 모서리 반지름(사용자 2026-10-27)
const corner = (cx, cz, a0) => Array.from({ length: ARC + 1 }, (_, k) => { const a = (a0 + 90 * k / ARC) * Math.PI / 180; return [cx + RC * Math.cos(a), cz + RC * Math.sin(a)] })
const C0 = corner(x1 - RC, z1 - RC, 0), C1 = corner(x0 + RC, z1 - RC, 90), C2 = corner(x0 + RC, z0 + RC, 180), C3 = corner(x1 - RC, z0 + RC, 270)
const rect = [...C0, ...C1, ...C2, ...C3] // 반시계(x 오른쪽·z 위) 둘레 점(펼친 모양, 끝이 곧은 볼록 모양 — 모서리 칸 자르기용)
// 구부러진 끝(−x)은 물결 모양(사용자 2026-10-27 "끝 부분에 울퉁불퉁? 물결? 모양으로"): 두 모서리 둥근 호 사이를 z 방향으로 코사인 물결(깊이 2·WA, 한 주기 WL)로 잇는다. 물결 끝은 x0 에 닿아 폭 35 는 그대로다.
const WA = 0.75, WL = 5, ZS = z0 + RC, ZE = z1 - RC
const fz = Array.from({ length: 41 }, (_, k) => ZS + k * (ZE - ZS) / 40) // 물결 한 주기를 8칸으로 나눈 z 경계(0.625 간격)
const xw = (z) => x0 + WA * (1 - Math.cos(2 * Math.PI * (z - ZS) / WL))
const outline = [...C0, ...C1, ...fz.slice(1, -1).reverse().map((z) => [xw(z), z]), ...C2, ...C3]
const circles = HOLES.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const POCKET = 8, PD = 1 // 프레임 쪽 홀 아래 8×8 사각 홈 깊이 1
const sq = HOLES.map(([x, z]) => [[x - POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z - POCKET / 2], [x + POCKET / 2, z + POCKET / 2], [x - POCKET / 2, z + POCKET / 2]])
HOLES.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, PD, PLATE.t, -1) // 구멍 벽(홈 바닥~윗면)
  const s4 = sq[i]; for (let k = 0; k < 4; k++) { const a = s4[k], b = s4[(k + 1) % 4]; kit.quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], PD, b[1]), P(a[0], PD, a[1]), x - (a[0] + b[0]) / 2, 0, z - (a[1] + b[1]) / 2) } // 홈 옆벽(홈 가운데를 향한다)
  ringFace(kit, s4, [circles[i]], PD, -1) // 홈 바닥(아래를 본다, 구멍 뚫림)
})
// 구부러지는 구간은 0.5mm 간격(마디 사이 각도 1° 미만 — 뷰어는 1° 넘게 꺾인 모서리에 선을 그려서 줄무늬가 생긴다)으로 잘게 나눈다. 모든 면·옆벽이 같은 경계(x·z)를 써서 이음새가 갈라지지 않는다.
const NSEG = Math.ceil(LARC / 0.5), xs = Array.from({ length: NSEG + 1 }, (_, k) => XC - k * LARC / NSEG)
const xa = HX - POCKET / 2, xb = HX + POCKET / 2
const uniq = (a) => [...new Set(a.map((v) => Math.round(v * 1e6) / 1e6))].sort((m, n) => m - n)
const zb = uniq([z0, z1, ZS, ZE, ...HOLES.flatMap(([, z]) => [z - POCKET / 2, z + POCKET / 2])]) // 칸 나누기 z 경계(성기게). 물결이 있는 끝 가까운 칸만 아래 zfine 으로 촘촘히 나누고, 칸 크기가 다른 이웃 사이 T자 이음은 맨 아래에서 conformTJunctions 가 메운다.
const zfine = uniq([z0, z1, ...fz]) // 물결 칸: 홈 경계 z 는 끼우지 않는다(물결 선의 현이 어긋난다)
const WAVE_X = x0 + 2 * WA + 1e-6 // 이보다 안쪽(−x)에 걸친 칸은 촘촘히
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
const zOf = (xl) => (xl < WAVE_X ? zfine : zb)
for (const [xl, xh, pk] of cols) { const zl = zOf(xl); for (let k = 0; k + 1 < zl.length; k++) if (!inPocket(pk, zl[k], zl[k + 1])) cellFaceW(xl, xh, zl[k], zl[k + 1], 0, -1) }
// 윗면: 평평한 구간(프레임 쪽 구멍 3개 뚫림)은 다각형으로, 구부러진 구간은 같은 칸으로
const flatTop = [[XC, z0]]
rect.filter((p) => p[0] >= XC - 1e-9 && p[1] <= 0).forEach((p) => flatTop.push(p)) // 아래 변 + (+x,−z) 모서리
rect.filter((p) => p[0] > XC && p[1] > 0).forEach((p) => flatTop.push(p)); flatTop.push([XC, z1]); [...zb].reverse().filter((z) => z > z0 + 1e-9 && z < z1 - 1e-9).forEach((z) => flatTop.push([XC, z]))
ringFace(kit, flatTop, circles, PLATE.t, 1)
for (let k = 0; k < NSEG; k++) { const zl = zOf(xs[k + 1]); for (let j = 0; j + 1 < zl.length; j++) cellFaceW(xs[k + 1], xs[k], zl[j], zl[j + 1], PLATE.t, 1) }
// 옆벽: 둘레를 위 경계들로 잘게 나눠 잇는다
// 옆벽: 둘레를 칸 경계(x·z)마다 잘라 칸 하나당 사각형 하나로 만든다. 긴 옆벽 한 장을 그대로 두면 구부릴 때 삼각형이 굽은 곳을 가로질러 옆에서 큰 삼각형 면이 보인다(사용자 2026-10-27 "옆에서 보이는 저 삼각형").
const brkX = [...xs, xa, xb]
const densify = (a, b) => { const ts = [0, 1]; brkX.forEach((bx) => { if ((a[0] - bx) * (b[0] - bx) < 0) ts.push((bx - a[0]) / (b[0] - a[0])) }); zb.forEach((bz) => { if ((a[1] - bz) * (b[1] - bz) < 0) ts.push((bz - a[1]) / (b[1] - a[1])) }); return [...new Set(ts)].sort((m, n) => m - n).map((t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]) }
outline.forEach((a, i) => { const b = outline[(i + 1) % outline.length], d = densify(a, b); for (let k = 0; k + 1 < d.length; k++) { const p = d[k], q = d[k + 1]; if (Math.hypot(q[0] - p[0], q[1] - p[1]) > 1e-9) quad(P(p[0], y0, p[1]), P(q[0], y0, q[1]), P(q[0], y1, q[1]), P(p[0], y1, p[1]), q[1] - p[1], 0, -(q[0] - p[0])) } }) // 옆벽(바깥을 향한다)
const bodyTris = conformTJunctions(kit.result()) // T자 이음 메움(짝 없는 모서리 0)
// 밝은 테두리 선(사용자 2026-10-27 "밝은색으로 라인그려줘, 아무것도 안보인다"): 판·프레임 직육면체의 12개 모서리 띠와, 프레임 구멍 둘레 밝은 고리.
const LINE = { t: LINE_THICKNESS, out: 0.03 }
// 선은 실제 모양의 테두리를 따라 그린다(사용자 2026-10-27 "테두리를 따라 그리라고 누가 모두 사각형으로 그리래?"): 같은 높이 면의 가장자리를 이어 만든 고리 중 바깥 고리와 구멍 고리만 가는 막대로 깐다.
const fxs = X1 - ACELAB_FRAME_STD.width / 2, FX0 = X1 - ACELAB_FRAME_STD.width // 프레임 중심 x, 프레임이 판 위에서 시작하는 x
const toTris = (a, map = (v) => v) => { const T = []; for (let i = 0; i < a.length; i += 9) T.push([0, 3, 6].map((o) => map([a[i + o], a[i + o + 1], a[i + o + 2]]))); return T }
const frameTris = toTris(acelabFrame.straight(3, 1).tris, ([x, y, z]) => [z + fxs, y, -x]) // y 축 90° 돌려 판 위에 놓은 프레임(색칠 조각과 같은 변환)
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
  const bar = (a, b) => { const bent = Math.min(a[0], b[0]) < XC, n = bent ? Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) / 2)) : 1; for (let j = 0; j < n; j++) bar0(a.map((c, i) => c + (b[i] - c) * j / n), a.map((c, i) => c + (b[i] - c) * (j + 1) / n)) } // 구부러진 구간의 긴 선은 2mm 마디로 나눠(구부릴 때 같이 휜다)
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
    for (let k = 1; k < n; k++) { const i = (s0 + k) % n, p = loop[i]; const lim = Math.min(p[0], last[0]) < XC ? 2 : 1e9; if (!col[i] || Math.abs(p[0] - XC) < 1e-6 || Math.hypot(p[0] - last[0], p[1] - last[1], p[2] - last[2]) >= lim - 1e-6) { out.push(p); last = p } }
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
  ring(outline.filter((p, i) => { const n = outline.length, a = outline[(i + n - 1) % n], b = outline[(i + 1) % n]; return Math.abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 1e-9 }), 0)
  sq.forEach((s4) => { ring(s4, 0); ring(s4, PD); s4.forEach((c) => bar([c[0], 0, c[1]], [c[0], PD, c[1]])) })
  faceLoops(plateTris, PD, -1).filter((l) => spanOf(l) <= 5.5).forEach((l) => draw(l))
  // 구부러진 면 윗면·아랫면에 좌우(폭 방향)로 가로지르는 선 5개(사용자 2026-10-27 "둥그런 부분 윗면 아래면 좌우로 라인을 5개정도"): 호를 6등분한 자리
  const EDGE = 10 // 좌우 가장자리 10mm 씩은 선을 빼고(사용자 2026-10-27 "좌우 10mm 빼고") 가운데만 긋는다
  for (let n = 1; n <= 5; n++) { const x = XC - LARC * n / 6; for (const y of [0, PLATE.t]) bar([x, y, z0 + EDGE], [x, y, z1 - EDGE]) }
  return trianglesToStl(bendTris(k.result()))
}
const bentBody = bendTris(bodyTris), stl = trianglesToStl(bentBody), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const frameStl = trianglesToStl(acelabFrame.straight(3, 1).tris) // 13프레임(구멍 3×1, 길이 30·폭 10·두께 5, 가운데가 원점, y 0~5)
if (process.argv.includes('--check')) { console.log('펼친 몸통', JSON.stringify(checkMesh(bodyTris))); const K = (p) => p.map((c) => Math.round(c * 1e4)).join(','), dir = new Map(); for (let i = 0; i < bodyTris.length; i += 9) for (let v = 0; v < 3; v++) { const a = [bodyTris[i + v * 3], bodyTris[i + v * 3 + 1], bodyTris[i + v * 3 + 2]], q = (v + 1) % 3, c = [bodyTris[i + q * 3], bodyTris[i + q * 3 + 1], bodyTris[i + q * 3 + 2]]; dir.set(K(a) + '>' + K(c), [a, c]) }
  let m = 0; for (const [k, [a, c]] of dir) if (!dir.has(K(c) + '>' + K(a)) && m++ < 25) console.log('열림', a.map((x) => x.toFixed(3)).join(','), '->', c.map((x) => x.toFixed(3)).join(',')) }
const outlineStl = outlineBars()
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '곡면판'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  // 판은 바탕 모양, 13프레임은 색칠 조각(paint)으로 붙인다(뷰어가 모양 파일 두 개를 합치는 계산을 못 한다). 프레임은 길이(30)가 판 폭(z)과 나란하도록 y 축으로 90° 돌려 판 +x 끝에 붙인다.
  const fx = X1 - ACELAB_FRAME_STD.width / 2 + SHIFT // 판 끝에서 안쪽으로 폭 10 만큼 덮는다
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '판'), fileName: `${NAME}_에이스랩.stl` }, mk(frameStl, '13프레임', { paint: true, x: fx, y: 0, z: 0, ry: Math.PI / 2 }),
    { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const W = Math.round((X1 - (XC - BR * Math.sin(BPHI))) * 10) / 10
  const connectors = { note: `${NAME}(두께 ${PLATE.t} 판 + 한쪽(+x) 끝 위에 13프레임을 겹쳐 얹고, 반대쪽을 원호로 구부려 끝이 바닥에서 ${RISE}mm). 구멍 등은 정해지면 추가.`, pegs: [], holes: [], size: [W, RISE, PLATE.w], confidence: 'draft' }
  const data = { ...r.data, size: `${W}×${PLATE.w}×${RISE}mm (에이스랩: 두께 ${PLATE.t} 판, 프레임 쪽 10mm 는 평평하고 13프레임을 얹음(합친 두께 5, 프레임 구멍 3개 판까지 뚫림, 아래 8×8 사각 홈 1mm), 나머지는 반지름 ${BR.toFixed(1)}mm 원호로 구부려 끝이 바닥에서 ${RISE}mm, 네 모서리 둥근, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bentBody) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '판 몸통', JSON.stringify(checkMesh(bentBody)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
