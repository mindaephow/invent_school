// 에이스랩 관절암(암): 관절수(수)와 한 세트 — 12프레임(10×20×5, 구멍 1×2, 위쪽 8×8 사각 홈 1mm) 한쪽에 결합 부분 8mm 를 더해 전체 길이 28(사용자 2026-10-27 "같이 2개의 홀이 있고 결합되는부분까지 하면 28mm야", "니가 생각한데로 우선 그려봐").
// 결합 부분: ① 관절수 틈(폭 5)에 꼭 맞는 혀(폭 4.8, 끝은 옆에서 볼 때 반원, 양쪽 면 가운데에 관절수 볼록 돌기가 들어가는 오목 홈) ② 혀 양옆 몸통 앞면에서 나온 뾰족한 손가락 두 개(관절수 톱니 골에 꽂혀 15° 마다 딱딱 걸린다).
//   혀·손가락은 몸통과 겹치게 끼운 별개 닫힌 모양(색칠 조각)이다 — 뷰어가 모양 파일마다 가운데를 원점으로 옮기므로 위치(x·y·z)를 따로 적는다.
//   node scripts/make-robotron-jointfemale.mjs [--write] [--name=관절암]
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
const W = 10, T = 5, HOLE_R = ACELAB_FRAME_STD.boreR // 폭 z 10, 두께 y 5, 구멍 지름 4.5
const FRAME_L = 20, ADD = 8, LEN = FRAME_L + ADD // 12프레임 길이 20 + 결합 부분 8 = 전체 28
const PW = 8, PR = 3, PD = 1 // 위쪽 홈 8×8(모서리 반지름 3)·깊이 1
const X_L = -FRAME_L / 2, X_B = FRAME_L / 2, HC = [[-5, 0], [5, 0]], half = W / 2 // 몸통 왼쪽 끝(둥근 끝)·몸통 앞면 x, 구멍 가운데
const PIV = X_B + 5.5, PRO = T / 2, X_TIP = PIV + PRO // 관절수 중심(축) x=15.5, 혀 끝 x=18
const TW = 2.4, BA = 1.0, RA = BA + 0.05, BSEG = 16 // 혀 반폭(폭 4.8), 구멍 반지름(관절수 돌기 반지름 1.0 보다 0.05 크게)
const FZ0 = 2.6, FZ1 = 4.9, FB = 9.7, FY0 = 0.8, FY1 = 4.2 // 손가락 z 범위, 몸통 속에 박히는 밑 x, 밑 y 범위
const VAL = 7.5, VR = 2.1, FTR = 0.4, FR = VR + 0.53 * FTR + 0.02 // 손가락 끝이 꽂히는 톱니 골 각도(+7.5°)·골 바닥 반지름(관절수 PRO−TD = 2.1), 끝 둥글림 반지름. 둥근 끝은 V 골 바닥까지 못 들어가고 골 벽에 접하는 자리(바닥에서 FTR×0.53 위)에 얹힌다 — 바닥까지 넣으면 골 벽과 겹친다(숫자 점검 2026-10-27).
const FTIP = [PIV - FR * Math.cos(VAL * Math.PI / 180), PRO + FR * Math.sin(VAL * Math.PI / 180)] // 손가락 뾰족한 끝(x, y)
const arcL = Array.from({ length: 25 }, (_, j) => { const a = (90 + 180 * j / 24) * Math.PI / 180; return [X_L + half + half * Math.cos(a), half * Math.sin(a)] }) // 왼쪽 반원(위→아래)
const outline = [...arcL, [X_B, -half], [X_B, half]] // 몸통 둘레(반시계): 왼쪽 둥근 끝 → 아래 변 → 앞면 → 위 변
const holes = HC.map(([x, z]) => circlePts(x, z, HOLE_R, 24))
const sqr = ([cx, cz]) => { const h = PW / 2 - PR, cs = [[cx + h, cz + h, 0], [cx - h, cz + h, 90], [cx - h, cz - h, 180], [cx + h, cz - h, 270]]; return cs.flatMap(([ax, az, a0]) => Array.from({ length: 7 }, (_, j) => { const a = (a0 + 90 * j / 6) * Math.PI / 180; return [ax + PR * Math.cos(a), az + PR * Math.sin(a)] })) }
const pockets = HC.map(sqr)
const kit = makeKit(24), { quad, P } = kit
outline.forEach((a, i) => { const b = outline[(i + 1) % outline.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], T, b[1]), P(a[0], T, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) }) // 옆벽(바깥을 향한다)
ringFace(kit, outline, holes, 0, -1) // 아랫면(구멍 뚫림)
ringFace(kit, outline, pockets, T, 1) // 윗면(사각 홈 자리 뚫림)
HC.forEach(([x, z], i) => {
  kit.cyl(x, z, HOLE_R, 0, T - PD, -1) // 구멍 벽(아래~홈 바닥)
  const pk = pockets[i], cen = [x, z]; pk.forEach((a, j) => { const b = pk[(j + 1) % pk.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) quad(P(a[0], T - PD, a[1]), P(b[0], T - PD, b[1]), P(b[0], T, b[1]), P(a[0], T, a[1]), cen[0] - (a[0] + b[0]) / 2, 0, cen[1] - (a[1] + b[1]) / 2) }) // 홈 옆벽(홈 가운데를 향한다)
  ringFace(kit, pk, [holes[i]], T - PD, 1) // 홈 바닥(위를 본다, 구멍 뚫림)
})
const noDegenerate = (arr) => { const out = []; for (let i = 0; i < arr.length; i += 9) { const u = [arr[i + 3] - arr[i], arr[i + 4] - arr[i + 1], arr[i + 5] - arr[i + 2]], v = [arr[i + 6] - arr[i], arr[i + 7] - arr[i + 1], arr[i + 8] - arr[i + 2]], c = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]; if (Math.hypot(...c) > 1e-9) out.push(...arr.slice(i, i + 9)) } return Float32Array.from(out) }
const bodyTris = conformTJunctions(noDegenerate(kit.result())) // 12프레임 몸통
// 혀(결합 부분): 옆모양(x–y)을 폭 TW*2 만큼(z 방향) 밀어낸 닫힌 모양. 몸통 앞면 속으로 0.5 끼워 넣는다. 끝은 옆에서 볼 때 반원(중심 = 관절수 축), 양쪽 면 가운데에 돌기 자리 오목 홈.
const TB = X_B - 0.5
const semi = Array.from({ length: 25 }, (_, j) => { const a = (-90 + 7.5 * j) * Math.PI / 180; return [PIV + PRO * Math.cos(a), PRO + PRO * Math.sin(a)] })
const tprof = [[TB, 0], ...semi, [TB, T]] // 반시계(x 오른쪽·y 위)
const tk = makeKit(24), tP = tk.P
const capFace = (k2, poly, holes2, zf, nz) => { const tmp = makeKit(24); ringFace(tmp, poly, holes2, 0, 1); const r0 = tmp.result(); for (let i = 0; i < r0.length; i += 9) k2.tri(k2.P(r0[i], r0[i + 2], zf), k2.P(r0[i + 3], r0[i + 5], zf), k2.P(r0[i + 6], r0[i + 8], zf), 0, 0, nz) } // (x, 0, y)로 나눈 삼각형을 벽 면(x, y, zf)으로 옮긴다
const extrude = (k2, poly, z0, z1) => poly.forEach((a, i) => { const b = poly[(i + 1) % poly.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-9) k2.quad(k2.P(a[0], a[1], z0), k2.P(b[0], b[1], z0), k2.P(b[0], b[1], z1), k2.P(a[0], a[1], z1), b[1] - a[1], -(b[0] - a[0]), 0) }) // 옆면(바깥을 향한다)
extrude(tk, tprof, -TW, TW)
// 가운데 구멍(관통): 관절수 돌기(반지름 1.0, 높이 0.6)가 양쪽에서 꽂힌다(사용자 2026-10-27 "가운데 손가락 부분에 돌기가 끼워질 홀이 있어야 하지?"). 지름 2.1.
const rim = circlePts(PIV, PRO, RA, BSEG)
for (const [zf, out] of [[-TW, -1], [TW, 1]]) capFace(tk, tprof, [rim], zf, out) // 양쪽 면(구멍 뚫림)
rim.forEach((a, j) => { const b = rim[(j + 1) % rim.length]; tk.quad(tP(a[0], a[1], -TW), tP(b[0], b[1], -TW), tP(b[0], b[1], TW), tP(a[0], a[1], TW), PIV - (a[0] + b[0]) / 2, PRO - (a[1] + b[1]) / 2, 0) }) // 구멍 벽(구멍 가운데를 향한다)
const tongueTris = noDegenerate(tk.result())
// 손가락: 몸통 앞면에서 관절수 톱니 골까지 뻗는 쐐기 두 개(z 양쪽). 옆모양 삼각형(끝을 반지름 FTR 로 둥글림 — 사용자 2026-10-27 "너무 뾰족해 살짝 둥그렇게")을 팔 폭만큼 밀어낸 닫힌 모양, 밑은 몸통 속에 박힌다.
const fillet = (P0, V, N0, r) => { const u = [P0[0] - V[0], P0[1] - V[1]], w = [N0[0] - V[0], N0[1] - V[1]], ul = Math.hypot(...u), wl = Math.hypot(...w); u[0] /= ul; u[1] /= ul; w[0] /= wl; w[1] /= wl
  const th = Math.acos(Math.max(-1, Math.min(1, u[0] * w[0] + u[1] * w[1]))), t = r / Math.tan(th / 2), bis = [u[0] + w[0], u[1] + w[1]], bl = Math.hypot(...bis), C = [V[0] + bis[0] / bl * r / Math.sin(th / 2), V[1] + bis[1] / bl * r / Math.sin(th / 2)]
  const T1 = [V[0] + u[0] * t, V[1] + u[1] * t], T2 = [V[0] + w[0] * t, V[1] + w[1] * t], a1 = Math.atan2(T1[1] - C[1], T1[0] - C[0]), a2 = Math.atan2(T2[1] - C[1], T2[0] - C[0]), da = ((a2 - a1) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI), n = Math.max(3, Math.ceil(da / (Math.PI / 12)))
  return Array.from({ length: n + 1 }, (_, j) => [C[0] + r * Math.cos(a1 + da * j / n), C[1] + r * Math.sin(a1 + da * j / n)]) }
const fbase = [FB, (FY0 + FY1) / 2], fd = [FTIP[0] - fbase[0], FTIP[1] - fbase[1]], fl = Math.hypot(...fd), fsin = ((FY1 - FY0) / 2) / Math.hypot(fl, (FY1 - FY0) / 2) // 쐐기 반각의 sin
const fextra = FTR / fsin - FTR // 둥글리면 끝이 이만큼 짧아지므로 가상 끝점을 그만큼 앞으로 둔다(둥근 끝 맨 앞이 골 반지름 FR 에 닿는다)
const FAPEX = [FTIP[0] + fd[0] / fl * fextra, FTIP[1] + fd[1] / fl * fextra]
const fprof = [[FB, FY0], ...fillet([FB, FY0], FAPEX, [FB, FY1], FTR), [FB, FY1]] // 반시계
const fk = makeKit(24)
for (const sg of [1, -1]) { const z0 = sg > 0 ? FZ0 : -FZ1, z1 = sg > 0 ? FZ1 : -FZ0
  extrude(fk, fprof, z0, z1); capFace(fk, fprof, [], z0, -1); capFace(fk, fprof, [], z1, 1) } // 옆면 + 양옆 면
const fingerTris = noDegenerate(fk.result())
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
  // 혀·손가락 테두리(사용자 2026-10-27 "테두리가 안보임"): 혀 양쪽 면 둘레(앞면 x=X_B 부터)와 가운데 구멍 둘레, 손가락 삼각형 둘레. 색칠 조각은 선이 없으면 같은 색이라 윤곽·구멍이 안 보인다.
  const polyline = (pts, z) => { for (let i = 0; i + 1 < pts.length; i++) bar([pts[i][0], pts[i][1], z], [pts[i + 1][0], pts[i + 1][1], z]) }
  const tOut = [[X_B, 0], ...semi, [X_B, T]]
  for (const z of [-TW, TW]) { polyline(tOut, z); rim.forEach((a, j) => { const b2 = rim[(j + 1) % rim.length]; bar([a[0], a[1], z], [b2[0], b2[1], z]) }) }
  for (const sg of [1, -1]) for (const z of sg > 0 ? [FZ0, FZ1] : [-FZ1, -FZ0]) polyline([...fprof, fprof[0]], z)
  return k.result()
}
const bbox = (arr) => { const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < arr.length; i += 3) for (let c = 0; c < 3; c++) { mn[c] = Math.min(mn[c], arr[i + c]); mx[c] = Math.max(mx[c], arr[i + c]) } return { mn, mx, cx: (mn[0] + mx[0]) / 2, cz: (mn[2] + mx[2]) / 2 } }
const outlineTris = outlineBars(), outlineStl = trianglesToStl(outlineTris), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const bb = bbox(bodyTris), bt = bbox(tongueTris), bf = bbox(fingerTris), bo = bbox(outlineTris)
const off = (b2) => ({ x: b2.cx - bb.cx, y: b2.mn[1] - bb.mn[1], z: b2.cz - bb.cz }) // 뷰어가 모양 파일마다 x·z 가운데를 원점·바닥을 y=0 으로 옮기므로 원래 자리로 되돌릴 값
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '관절암'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: `${NAME}_에이스랩.stl` }, mk(trianglesToStl(tongueTris), '혀', { paint: true, ...off(bt) }), mk(trianglesToStl(fingerTris), '손가락', { paint: true, ...off(bf) }), { ...mk(outlineStl, '바깥선', { paint: true, ...off(bo) }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(12프레임 ${W}×${FRAME_L} + 결합 부분 ${ADD} = 전체 ${LEN}, 두께 ${T}, 구멍 1×2). 관절수 틈에 끼우는 혀(가운데 관통 구멍)와 톱니 골에 꽂히는 손가락 두 개. 모양은 이후 다듬는다.`, pegs: [], holes: [], size: [LEN, T, W], confidence: 'draft' }
  const data = { ...r.data, size: `${W}×${LEN}×${T}mm (에이스랩: 12프레임 + 결합 부분 ${ADD}mm = 전체 ${LEN}, 구멍 지름 4.5 구멍 1×2, 위쪽 8×8 사각 홈 1mm, 혀 폭 ${TW * 2}(끝은 옆에서 볼 때 반원, 가운데 관통 구멍 지름 2.1), 뾰족한 손가락 두 개, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  for (const [n2, t2] of [['본체', bodyTris], ['혀', tongueTris], ['손가락', fingerTris]]) assertPartMesh(`${NAME} ${n2}`, t2) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, r.data.color, hex, '본체 KB', Math.round(stl.length / 1024), JSON.stringify(checkMesh(bodyTris)), '| 혀', JSON.stringify(checkMesh(tongueTris)), '| 손가락', JSON.stringify(checkMesh(fingerTris)), '| 바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
