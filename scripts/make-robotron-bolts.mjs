// 에이스랩·로보타미주니어의 12볼트·16볼트·너트를 부품 DB 에 3D 로 등록한다(권별 수량·이름·색은 그대로).
//   node scripts/make-robotron-bolts.mjs            → 시험
//   node scripts/make-robotron-bolts.mjs --write    → 등록
// 규격: app/lib/robotron-bolt-mesh.js (나사선 지름 4, 너트 구멍 지름 4 는 사용자 값, 머리·너트 바깥 크기는 유추).
import fs from 'node:fs'
import { boltTriangles, nutTriangles, BOLT_STD, NUT_STD } from '../app/lib/robotron-bolt-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const bolt = (L) => ({
  tris: boltTriangles(L), size: `길이 ${L}mm, 나사선 지름 ${BOLT_STD.threadR * 2}, 머리 지름 ${BOLT_STD.headR * 2}·높이 ${BOLT_STD.headH}(육각 홈)`,
  connectors: { note: `${L}볼트(길이 ${L}, 나사선 지름 ${BOLT_STD.threadR * 2}). 머리 아랫면이 y=0, 나사선이 아래(−y)로 뻗어 프레임 구멍을 지나 너트에 물린다. 머리(지름 ${BOLT_STD.headR * 2})는 프레임 칸(주머니) 안에 얹힌다.`, pegs: [{ r: BOLT_STD.threadR, id: 'p1', dir: [0, -1, 0], len: L, pos: [0, 0, 0] }], holes: [], size: [BOLT_STD.headR * 2, L + BOLT_STD.headH, BOLT_STD.headR * 2], confidence: 'checked' },
})
const nut = () => ({
  tris: nutTriangles(), size: `육각 대변 ${NUT_STD.flat}·두께 ${NUT_STD.height}, 가운데 구멍 지름 ${NUT_STD.boreR * 2}`,
  connectors: { note: `너트(육각 대변 ${NUT_STD.flat}, 두께 ${NUT_STD.height}). 가운데 구멍 지름 ${NUT_STD.boreR * 2}에 볼트(나사선 지름 4)가 위에서 물린다. 구멍 len 은 실제 두께가 아니라 볼트(12·16볼트)가 위에서 물리는 범위(18)로 기록했다(큐보 너트와 같은 방식).`, pegs: [], holes: [{ r: NUT_STD.boreR, id: 'h1', dir: [0, -1, 0], len: 18, pos: [0, 0, 0], through: true }], size: [7.5, NUT_STD.height, NUT_STD.flat], confidence: 'checked' },
})
const MAKE = { '12볼트': () => bolt(12), '16볼트': () => bolt(16), 너트: nut }

for (const [cat, label] of Object.entries(CATS)) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}`)
  for (const r of rows) {
    const mk = MAKE[r.data.name]
    if (!mk) continue
    const hex = HEX[r.data.color]
    if (!hex) { console.log('색 모름', label, r.data.name); continue }
    const { tris, size, connectors } = mk(), stl = trianglesToStl(tris)
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${r.data.name}_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const data = { ...r.data, size, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label.padEnd(8), r.data.name.padEnd(6), r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
if (!WRITE) console.log('\n(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)')
