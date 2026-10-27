// 에이스랩 타이어: 바깥 지름 56·안쪽 지름 44(휠 가운데 원기둥)·두께(높이) 10·고무 폭 6 링 시작 모양(사용자 2026-10-27 "이 휠에 맞는 타이어 만들 거야, 타이어 테두리 지름 56", "두께10, 폭 6mm"). 모양은 이후 사용자와 다듬는다.
//   node scripts/make-robotron-geargrand.mjs [--write]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8', 블랙: '#555555', 그레이: '#9ca5af' }
const OUT = 28, IN = 22, W = 10, SEG = 72 // 바깥 반지름(지름 56), 안쪽 반지름(지름 44 = 휠 가운데 원기둥), 두께(높이) 10 → 고무 폭 6 (사용자 2026-10-27 "두께10, 폭 6mm")
// 휠에 끼운다(사용자 2026-10-27 "휠에 끼워져야 하는 거라, 그 홈 부분이 파여 있어야"): 안쪽에 휠 원판(지름 50·높이 1.5~8.5)이 들어가는 홈을 판다(실타래 홈에 들어가는 턱은 없다, 사용자 "실타래에 들어가는 부분은 없어도 돼").
const DR = 25, DY0 = 1.5, DY1 = 8.5 // 원판 반지름·높이 범위
const prof = [[IN, 0], [OUT, 0], [OUT, W], [IN, W], [IN, DY1], [DR, DY1], [DR, DY0], [IN, DY0]] // (반지름, 높이) 반시계 단면
const kit = makeKit(SEG), { quad, P } = kit
for (let k = 0; k < SEG; k++) {
  const t0 = 2 * Math.PI * k / SEG, t1 = 2 * Math.PI * (k + 1) / SEG, tm = (t0 + t1) / 2
  prof.forEach((a, i) => {
    const b = prof[(i + 1) % prof.length], nr = b[1] - a[1], ny = -(b[0] - a[0]) // 단면 바깥 법선 (dy, -dr)
    quad(P(a[0] * Math.cos(t0), a[1], a[0] * Math.sin(t0)), P(a[0] * Math.cos(t1), a[1], a[0] * Math.sin(t1)), P(b[0] * Math.cos(t1), b[1], b[0] * Math.sin(t1)), P(b[0] * Math.cos(t0), b[1], b[0] * Math.sin(t0)), nr * Math.cos(tm), ny, nr * Math.sin(tm))
  })
}
const bodyTris = kit.result()
const circ = (r) => Array.from({ length: SEG }, (_, k) => [r * Math.cos(2 * Math.PI * k / SEG), r * Math.sin(2 * Math.PI * k / SEG)])
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
  ring(circ(OUT), 0); ring(circ(OUT), W); ring(circ(IN), 0); ring(circ(IN), W); for (const y of [DY0, DY1]) { ring(circ(IN), y); ring(circ(DR), y) }
  return trianglesToStl(k.result())
}
const outlineStl = outlineBars(), stl = trianglesToStl(bodyTris), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const NAME = '타이어'
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `타이어_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '본체'), fileName: '타이어_에이스랩.stl' }, { ...mk(outlineStl, '바깥선', { paint: true }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(바깥 지름 ${OUT * 2}·폭 ${W}). 두께(높이) ${W}·고무 폭 ${OUT - IN}(안쪽 지름 ${IN * 2}, 휠 가운데 지름 44 원기둥에 맞춤). 안쪽에 휠 원판(지름 ${DR * 2}, 높이 ${DY0}~${DY1})이 들어가는 홈이 있다. 모양은 이후 다듬는다.`, pegs: [], holes: [], size: [OUT * 2, W, OUT * 2], confidence: 'draft' }
  const data = { ...r.data, size: `Ø${OUT * 2}×${W}mm (에이스랩 타이어: 안쪽 지름 ${IN * 2}, 두께 ${W}, 고무 폭 ${OUT - IN}, 안쪽에 휠 원판 홈(지름 ${DR * 2}·높이 ${DY0}~${DY1}), 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris)
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), '몸통', JSON.stringify(checkMesh(bodyTris)), '삼각형', bodyTris.length / 9, '바깥선 KB', Math.round(outlineStl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
