// 에이스랩·로보타미주니어 미니휠(그레이): 지름 15·두께 5 실타래, 가운데 지름 12(얇은 부분), 가운데 규격 홀(지름 4.5). 권별 수량·이름·색은 그대로.
//   node scripts/make-robotron-minwheel.mjs [--write]
import fs from 'node:fs'
import { minWheelTriangles, MINWHEEL_STD as W } from '../app/lib/robotron-minwheel-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 그레이: '#9ca5af', 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = minWheelTriangles(), stl = trianglesToStl(tris)
const unp = (() => { const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(','), e = new Map(); for (let t = 0; t < tris.length / 9; t++) { const v = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]]); for (let i = 0; i < 3; i++) { const a = v[i], b = v[(i + 1) % 3], k1 = key(...a) + '>' + key(...b), k2 = key(...b) + '>' + key(...a); if (e.has(k2)) e.delete(k2); else e.set(k1, 1) } } return e.size })()
console.log('미니휠 메시 짝 없는 모서리', unp, '삼각형', tris.length / 9)
const connectors = { note: `미니휠(지름 ${W.r * 2}·두께 ${W.h} 실타래, 가운데 홈 부분 지름 ${W.grooveR * 2}). 가운데 규격 홀(지름 ${W.boreR * 2}, 프레임 구멍과 같음)이 두께를 관통한다. 위아래가 같다.`, pegs: [], holes: [{ id: 'h1', r: W.boreR, dir: [0, -1, 0], len: W.h, pos: [0, 0, 0], through: true }], size: [W.r * 2, W.h, W.r * 2], confidence: 'checked' }
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('미니휠')}`)) {
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: HEX[r.data.color], fileName: `미니휠_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const data = { ...r.data, size: `Ø${W.r * 2}×${W.h}mm (${label}, 실타래: 가운데 얇은 부분 지름 ${W.grooveR * 2}, 가운데 규격 홀 지름 ${W.boreR * 2})`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
