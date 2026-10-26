// 에이스랩 이빨: 10×10 두께 5 사각(뒤쪽 두 모서리 둥근 반지름 2.5, 가운데 구멍 1개 지름 4.5)의 양쪽 변에서 한 줄씩 나온 선이 앞에서 만나 뾰족한 이빨 모양, 전체 길이 23(사용자 2026-10-27 "이빨 만들자 10, 10, 두께 5mm", "사각에서 양쪽에서 한줄씩 와서 만나서 뾰족하게 이빨모양 전체길이 23"). 모양은 이후 사용자와 다듬는다.
//   node scripts/make-robotron-tooth.mjs [--write] [--name=이빨]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { ACELAB_FRAME_STD } from '../app/lib/acelab-frame-mesh.js'
import { conformTJunctions, checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8', 블랙: '#555555', 그레이: '#9ca5af' }
const SQ = 10, LEN = 23, W = 10, T = 5, HOLE_R = ACELAB_FRAME_STD.boreR // 사각 10, 전체 길이 23(x), 폭 z 10, 두께 y 5, 구멍 지름 4.5
const [x0, x1, y0, y1, z0, z1] = [-SQ / 2, -SQ / 2 + LEN, 0, T, -W / 2, W / 2] // x0 = 사각 뒤쪽 끝, x1 = 이빨 뾰족한 끝(사각 앞쪽 변은 x=+5)
const kit = makeKit(24), { quad, P } = kit
const RC = 2.5, ARC = 8 // 사각 뒤쪽 모서리 반지름(평판과 같다)
const corner = (cx, cz, a0) => Array.from({ length: ARC + 1 }, (_, j) => { const a = (a0 + 90 * j / ARC) * Math.PI / 180; return [cx + RC * Math.cos(a), cz + RC * Math.sin(a)] })
// 모서리를 반지름 r 로 둥글린 점들: 반시계 다각형의 꼭짓점 V(앞 점 P, 뒤 점 N)
const fillet = (P0, V, N0, r) => { const u = [P0[0] - V[0], P0[1] - V[1]], w = [N0[0] - V[0], N0[1] - V[1]], ul = Math.hypot(...u), wl = Math.hypot(...w); u[0] /= ul; u[1] /= ul; w[0] /= wl; w[1] /= wl
  const th = Math.acos(Math.max(-1, Math.min(1, u[0] * w[0] + u[1] * w[1]))), t = r / Math.tan(th / 2), bis = [u[0] + w[0], u[1] + w[1]], bl = Math.hypot(...bis), C = [V[0] + bis[0] / bl * r / Math.sin(th / 2), V[1] + bis[1] / bl * r / Math.sin(th / 2)]
  const T1 = [V[0] + u[0] * t, V[1] + u[1] * t], T2 = [V[0] + w[0] * t, V[1] + w[1] * t], a1 = Math.atan2(T1[1] - C[1], T1[0] - C[0]), a2 = Math.atan2(T2[1] - C[1], T2[0] - C[0]), da = ((a2 - a1) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI), n = Math.max(2, Math.ceil(da / (Math.PI / 12)))
  return Array.from({ length: n + 1 }, (_, j) => [C[0] + r * Math.cos(a1 + da * j / n), C[1] + r * Math.sin(a1 + da * j / n)]) }
// 이빨 끝 둥글림(사용자 2026-10-27 "너무 뾰족하니 좀 둥그렇게"): 끝 반지름 TR. 둥글려도 전체 길이가 23 이 되게, 두 변이 만나는 가상 끝점 XV 를 그만큼 더 앞에 둔다.
const TR = 2, SHx = x0 + SQ
const tipReach = (xv) => { const sa = z1 / Math.hypot(xv - SHx, z1); return xv - (TR / sa - TR) } // 둥근 끝의 맨 앞 x
let lo = x1, hi = x1 + 30; for (let i = 0; i < 80; i++) { const m = (lo + hi) / 2; if (tipReach(m) < x1) lo = m; else hi = m }
const XV = (lo + hi) / 2
const TIP = [XV, 0], SHOULDER = [x0 + SQ, z1], SHOULDER2 = [x0 + SQ, z0] // 뾰족한 끝, 사각 앞쪽 두 모서리(여기서 두 변이 모여든다)
const rect = [...fillet(SHOULDER2, TIP, SHOULDER, TR), SHOULDER, ...corner(x0 + RC, z1 - RC, 90), ...corner(x0 + RC, z0 + RC, 180), SHOULDER2], hole = circlePts(0, 0, HOLE_R, 24) // 반시계(x 오른쪽·z 위) 둘레: 뾰족한 끝 → 위쪽 변 → 뒤쪽 둥근 두 모서리 → 아래쪽 변
for (let i = 0; i < rect.length; i++) { const a = rect[i], b = rect[(i + 1) % rect.length]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-9) continue; quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), b[1] - a[1], 0, -(b[0] - a[0])) } // 옆벽(바깥을 향한다)
// 규격홀 위·아래 지름 9, 깊이 1 원형 홈(사용자 2026-10-27 "규격홀 위아래에 1mm 홈좀 파줘 지름 9mm짜리"): 구멍 벽은 홈 바닥(y=1)~홈 바닥(y=4) 사이만 남는다.
const PR = 4.5, PD = 1, pocket = circlePts(0, 0, PR, 24)
kit.cyl(0, 0, HOLE_R, y0 + PD, y1 - PD, -1) // 구멍 벽(구멍 가운데를 향한다)
kit.cyl(0, 0, PR, y0, y0 + PD, -1); kit.cyl(0, 0, PR, y1 - PD, y1, -1) // 홈 옆벽(아래·위)
ringFace(kit, pocket, [hole], y0 + PD, -1) // 아래 홈 바닥(아래를 본다, 구멍 뚫림)
ringFace(kit, pocket, [hole], y1 - PD, 1) // 위 홈 바닥(위를 본다, 구멍 뚫림)
// 뾰족한 곳에 삼각형 구멍(사용자 2026-10-27 "뽀족한 곳 삼각형으로 뚫어줘"): 이빨 끝 삼각형을 테두리 두께 TW 만큼 안쪽으로 줄인 닮은 삼각형(밑변은 사각 앞쪽 변에서 TW 앞).
const TW = 2, HR = 0.8, sl = (z1 - 0) / (XV - (x0 + SQ)), norm = Math.sqrt(1 + sl * sl), zTop = (x) => z1 - sl * (x - (x0 + SQ)) - TW * norm // 위쪽 변을 TW 만큼 안으로 민 선
const bx = x0 + SQ + TW, apexX = x0 + SQ + (z1 - TW * norm) / sl
const tri0 = [[apexX, 0], [bx, zTop(bx)], [bx, -zTop(bx)]] // 반시계: 끝 → 위쪽 밑 모서리 → 아래쪽 밑 모서리
const tri = tri0.flatMap((v, i) => fillet(tri0[(i + 2) % 3], v, tri0[(i + 1) % 3], HR)) // 세 모서리 반지름 HR 로 둥글림
const tc = [(tri0[0][0] + tri0[1][0] + tri0[2][0]) / 3, 0]
tri.forEach((a, i) => { const b = tri[(i + 1) % tri.length], mx = (a[0] + b[0]) / 2, mz = (a[1] + b[1]) / 2; quad(P(a[0], y0, a[1]), P(b[0], y0, b[1]), P(b[0], y1, b[1]), P(a[0], y1, a[1]), tc[0] - mx, 0, tc[1] - mz) }) // 삼각형 구멍 벽(구멍 가운데를 향한다)
ringFace(kit, rect, [pocket, tri], y0, -1) // 아랫면(구멍 뚫림)
ringFace(kit, rect, [pocket, tri], y1, 1) // 윗면(구멍 뚫림)
const bodyTris = conformTJunctions(kit.result())

// 밝은 테두리 선(에이스랩 부품 규칙): 위·아래 바깥 둘레(둥근 모서리 포함), 구멍 둘레. 삼각 기둥(삼각형 6개).
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
  ring(rect, y0); ring(rect, y1); ring(pocket, y0); ring(pocket, y1); ring(pocket, y0 + PD); ring(pocket, y1 - PD); ring(hole, y0 + PD); ring(hole, y1 - PD); ring(tri, y0); ring(tri, y1) // 홈 입구·홈 바닥 가장자리·구멍 가장자리
  for (const c of [SHOULDER, SHOULDER2]) bar([c[0], y0, c[1]], [c[0], y1, c[1]]) // 날카로운 모서리(사각 앞쪽 두 모서리) 세로선
  return trianglesToStl(k.result())
}
const outlineStl = outlineBars(), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '이빨'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: `${NAME}_에이스랩.stl` }, { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(${LEN}×${W} 두께 ${T}, 사각 10×10 + 뾰족한 이빨 끝, 가운데 구멍 1개 지름 ${HOLE_R * 2}(위아래 지름 9·깊이 1 홈) + 이빨 끝 삼각형 구멍). 모양은 이후 다듬는다.`, pegs: [], holes: [], size: [LEN, T, W], confidence: 'draft' }
  const data = { ...r.data, size: `${LEN}×${W}×${T}mm (에이스랩: 10×10 사각(뒤쪽 모서리 둥근 반지름 2.5)에서 양쪽 변이 모여 뾰족한 이빨, 가운데 구멍 1개 지름 ${HOLE_R * 2}(위아래 지름 9·깊이 1 홈) + 이빨 끝 삼각형 구멍, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris) // 규격 검사에 실패하면 여기서 멈춘다(등록 안 함)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
