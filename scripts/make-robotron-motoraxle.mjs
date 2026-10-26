// 에이스랩 모터축(그레이): 지름 8·길이 10 원기둥(끝에 깊이 4 모터 육각 홈) + 4×4 십자 축 길이 29. 권별 수량·이름·색은 그대로.
//   node scripts/make-robotron-motoraxle.mjs [--write]
import fs from 'node:fs'
import { motorAxleTriangles, MOTORAXLE_STD as M } from '../app/lib/robotron-motoraxle-mesh.js'
import { AXLE_STD } from '../app/lib/robotron-axle-mesh.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 그레이: '#9ca5af', 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = motorAxleTriangles(), stl = trianglesToStl(tris)
const unp = (() => { const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(','), e = new Map(); for (let t = 0; t < tris.length / 9; t++) { const v = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]]); for (let i = 0; i < 3; i++) { const a = v[i], b = v[(i + 1) % 3], k1 = key(...a) + '>' + key(...b), k2 = key(...b) + '>' + key(...a); if (e.has(k2)) e.delete(k2); else e.set(k1, 1) } } return e.size })()
console.log('모터축 메시 짝 없는 모서리', unp, '삼각형', tris.length / 9)
// 뷰어는 한 부품을 음영 없이 한 색으로 칠해서 육각 홈이 안 보인다 → 홈 바닥에 밝은(흰색) 원판, 홈 입구 둘레에 짙은 육각 띠(선)를 "색칠 조각"(paint)으로 얹는다(사용자 2026-10-26 "안에 파인게 안보이니까 안쪽 라인을 다른색으로").
// 주의: 뷰어는 불러온 모양을 바닥(y 최소)이 0 이 되게 옮기므로 본체(y −29~10)는 y 0~39 로 옮겨진다. 색칠 조각의 y 도 그 기준(+axleLen)이다.
const MARK = { color: '#555555', floorColor: '#f2f4f8', floorR: 3.4, floorT: 0.2, rimOut: 1.0, rimT: 0.15 }
const hexPts = (flat) => { const R = flat / Math.sqrt(3); return Array.from({ length: 6 }, (_, k) => [R * Math.cos((Math.PI / 3) * k), R * Math.sin((Math.PI / 3) * k)]) }
const floorTris = () => { const k = makeKit(48); k.cyl(0, 0, MARK.floorR, 0, MARK.floorT, 1); const d = circlePts(0, 0, MARK.floorR, 48); ringFace(k, d, [], 0, -1); ringFace(k, d, [], MARK.floorT, 1); return k.result() }
const rimTris = () => { const k = makeKit(24), { quad, P } = k, o = hexPts(M.hexFlat + MARK.rimOut), i = hexPts(M.hexFlat)
  const wall = (pl, dir) => pl.forEach((a, n) => { const b = pl[(n + 1) % pl.length], dx = b[0] - a[0], dz = b[1] - a[1], l = Math.hypot(dx, dz); quad(P(a[0], 0, a[1]), P(b[0], 0, b[1]), P(b[0], MARK.rimT, b[1]), P(a[0], MARK.rimT, a[1]), (dir * dz) / l, 0, (-dir * dx) / l) })
  wall(o, 1); wall(i, -1); ringFace(k, o, [i], 0, -1); ringFace(k, o, [i], MARK.rimT, 1); return k.result() }
const connectors = { note: `모터축(원기둥 지름 ${M.cylR * 2}·길이 ${M.cylH} + 4×4 십자 축 ${M.axleLen}). 원기둥 끝(+y)에 대변 ${M.hexFlat}·깊이 ${M.hexDepth} 모터 육각 홈, 반대쪽(−y)으로 십자 축이 뻗는다(열십자 홀에 끼움).`, pegs: [{ r: AXLE_STD.span / 2, id: 'p1', dir: [0, -1, 0], len: M.axleLen, pos: [0, 0, 0] }], holes: [{ id: 'h1', r: M.hexFlat / 2, dir: [0, 1, 0], len: M.hexDepth, pos: [0, M.cylH, 0] }], size: [M.cylR * 2, M.cylH + M.axleLen, M.cylR * 2], confidence: 'checked' }
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('모터축')}`)) {
    const mk = (st, color, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, fileName: `모터축_${name}_${label}.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
    const spec = { shapes: [{ ...mk(stl, HEX[r.data.color], '본체'), fileName: `모터축_${label}.stl` }, mk(trianglesToStl(floorTris()), MARK.floorColor, '홈바닥', { paint: true, y: M.axleLen + M.cylH - M.hexDepth + 0.01 }), mk(trianglesToStl(rimTris()), MARK.color, '홈테두리', { paint: true, y: M.axleLen + M.cylH })] }
    const data = { ...r.data, size: `Ø${M.cylR * 2}×${M.cylH + M.axleLen}mm (${label}: 원기둥 지름 ${M.cylR * 2}·길이 ${M.cylH}, 끝에 모터 육각 홈 대변 ${M.hexFlat}·깊이 ${M.hexDepth} + 4×4 십자 축 길이 ${M.axleLen})`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
