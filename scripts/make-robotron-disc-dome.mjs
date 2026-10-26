// 에이스랩 원판(스카이블루): 지름 70 의 둥근 원판을 가운데가 높이 15 가 되게 둥글게 올린 둥근 지붕(돔)이다. 두께 3(사용자 2026-10-27 "원판만들자, 두께3mm 폭30mm 얇은판을 가운데를 높이 15mm 로 올려서 지붕처럼", "지붕이 각이 지면안되고 이름처럼 원판이 되어야해", "둥근원판 둥근지붕이 되어야 함", 크기는 "지름 70 둥근 지붕"으로 답함). 바깥(윗면) 구의 반지름 R = (35²+15²)/(2·15) 에 안쪽(아랫면) 반지름 R−3 인 껍질을 바닥(y 0)에서 수평으로 잘라 바닥에 닿는 고리(안쪽 반지름~35)를 둔다. 높이 15 는 꼭대기 윗면까지. 구멍 등은 정해지면 추가.
//   node scripts/make-robotron-disc.mjs [--write] [--name=원판]
import fs from 'node:fs'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { lineColorFor, LINE_THICKNESS } from '../app/lib/robotron-line-color.js'
import { checkMesh, assertPartMesh } from '../app/lib/cubo-mesh-repair.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const HEX = { 스카이블루: '#82d0f8' }
const NAME = process.argv.find((a) => a.startsWith('--name='))?.slice(7) || '원판'
const T = 3, L = 70, HT = 15 // 두께·지름·전체 높이
const HX = L / 2
const R = (HX ** 2 + HT ** 2) / (2 * HT), CY = HT - R, Ri = R - T // 바깥 반지름·구 중심 높이(중심 x·z 0)·안쪽 반지름
const phiO = Math.asin(HX / R), xi = Math.sqrt(Ri ** 2 - CY ** 2), phiI = Math.asin(xi / Ri) // 바깥 호 끝 각도(높이 0 에서), 안쪽 호가 바닥과 만나는 반지름 xi 와 각도
const NS = 24, M = 48 // 꼭대기→바닥 24 단계(약 4°), 둘레 48 칸(7.5°)
const ringsOf = (r, phi) => Array.from({ length: NS + 1 }, (_, k) => { const th = phi * k / NS; return { rr: r * Math.sin(th), y: CY + r * Math.cos(th) } }) // 꼭대기(k 0)에서 바닥(k NS)까지
const outer = ringsOf(R, phiO), inner = ringsOf(Ri, phiI)
outer[NS].y = 0; inner[NS].y = 0 // 바닥 높이 오차 제거
const kit = makeKit(M), { quad, P } = kit
const at = (rg, j) => { const a = 2 * Math.PI * j / M; return P(rg.rr * Math.cos(a), rg.y, rg.rr * Math.sin(a)) }
for (let k = 0; k < NS; k++) for (let j = 0; j < M; j++) {
  const n = (rg, sgn) => { const a = 2 * Math.PI * (j + 0.5) / M; return [sgn * rg.rr * Math.cos(a), sgn * (rg.y - CY), sgn * rg.rr * Math.sin(a)] } // 구 중심에서 바깥으로
  const no = n(outer[k + 1], 1), ni = n(inner[k + 1], -1)
  quad(at(outer[k], j), at(outer[k + 1], j), at(outer[k + 1], j + 1), at(outer[k], j + 1), no[0], no[1], no[2]) // 윗면(바깥을 본다)
  quad(at(inner[k], j), at(inner[k + 1], j), at(inner[k + 1], j + 1), at(inner[k], j + 1), ni[0], ni[1], ni[2]) // 아랫면(구 중심을 본다)
}
kit.annulus(0, 0, xi, HX, 0, -1) // 바닥에 닿는 고리(아래를 본다)
const bodyTris = kit.result()
// 밝기 대비 테두리 선(0.1mm): 입체의 모든 모서리
const outlineBars = () => {
  const k = makeKit(24), t = LINE_THICKNESS / 2
  const bar = (a, b) => { const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], len = Math.hypot(...d); if (len < 1e-6) return
    const e = d.map((c) => c / len), ref = Math.abs(e[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0]
    const cr = (p, q) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
    let u = cr(e, ref); const ul = Math.hypot(...u); u = u.map((c) => c / ul * t); const v = cr(e, u).map((c) => c / t * t)
    const s0 = a.map((c, i) => c - e[i] * t), s1 = b.map((c, i) => c + e[i] * t)
    const corner = (s, su, sv) => s.map((c, i) => c + su * u[i] + sv * v[i]), C = [[0, 1.2], [-1.04, -0.6], [1.04, -0.6]]
    const Aa = C.map(([su, sv]) => corner(s0, su, sv)), Bb = C.map(([su, sv]) => corner(s1, su, sv))
    const nrm = (su, sv) => [su * u[0] + sv * v[0], su * u[1] + sv * v[1], su * u[2] + sv * v[2]]
    for (let i = 0; i < 3; i++) { const j = (i + 1) % 3, m = nrm((C[i][0] + C[j][0]) / 2, (C[i][1] + C[j][1]) / 2); k.quad(Aa[i], Aa[j], Bb[j], Bb[i], m[0], m[1], m[2]) } }
  const circ = (r, y) => { const n = 96; for (let j = 0; j < n; j++) { const a0 = 2 * Math.PI * j / n, a1 = 2 * Math.PI * (j + 1) / n; bar([r * Math.cos(a0), y, r * Math.sin(a0)], [r * Math.cos(a1), y, r * Math.sin(a1)]) } }
  circ(HX, 0); circ(xi, 0) // 바닥에 닿는 고리의 바깥·안쪽 둘레
  return trianglesToStl(k.result())
}
const stl = trianglesToStl(bodyTris), outlineStl = outlineBars(), toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent(NAME)}`)) {
  const hex = HEX[r.data.color]
  const mk = (st, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${NAME}_${name}_에이스랩.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
  const spec = { shapes: [{ ...mk(stl, '몸통'), fileName: `${NAME}_에이스랩.stl` }, { ...mk(outlineStl, '바깥선', { paint: true, y: 0 }), color: lineColorFor(hex) }] }
  const connectors = { note: `${NAME}(지름 ${L} 둥근 원판을 가운데 높이 ${HT} 로 둥글게 올린 둥근 지붕, 두께 ${T}). 구멍 등은 정해지면 추가.`, pegs: [], holes: [], size: [L, HT, L], confidence: 'draft' }
  const data = { ...r.data, size: `Ø${L}×${HT}mm (에이스랩: 두께 ${T} 둥근 원판을 가운데 높이 ${HT} 로 둥글게(구면, 바깥 반지름 ${R.toFixed(1)}) 올린 둥근 지붕, 밝은 테두리 선)`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  assertPartMesh(NAME, bodyTris, { maxTris: 6000 })
  console.log(NAME, r.data.color, hex, 'KB', Math.round(stl.length / 1024), JSON.stringify(checkMesh(bodyTris)), '바깥선 KB', Math.round(outlineStl.length / 1024), '반지름', R.toFixed(2), '안쪽 바닥 반지름', xi.toFixed(2))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
