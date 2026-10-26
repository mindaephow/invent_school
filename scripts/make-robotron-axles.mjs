// 에이스랩·로보타미주니어의 십자 축(30·50·70mm)을 등록된 색으로 만들어 부품 DB 에 넣는다. 이미 3D 모양(spec.shapes)이 있으면 건드리지 않는다.
//   node scripts/make-robotron-axles.mjs            → 시험
//   node scripts/make-robotron-axles.mjs --write    → 등록(권별 수량·이름·색은 그대로)
import fs from 'node:fs'
import { axleTriangles, AXLE_STD } from '../app/lib/robotron-axle-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const REDO = process.argv.includes('--redo') // 3D 가 이미 있어도 다시 만든다(규격을 고칠 때)
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 블랙: '#555555', 그레이: '#9ca5af' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')

for (const [cat, label] of Object.entries(CATS)) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}`)
  for (const r of rows) {
    const m = r.data.name.match(/^(\d+)mm ?축$/)
    if (!m || (!REDO && r.data.spec?.shapes?.length)) continue
    const L = +m[1], hex = HEX[r.data.color]
    if (!hex) { console.log('색 모름, 건너뜀', label, r.data.name); continue }
    const tris = axleTriangles(L), stl = trianglesToStl(tris)
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `${L}mm축_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const connectors = { note: '십자 단면 축(축 y, 길이 ' + L + '). 축 전체를 긴 돌기 하나로 기록: 기어·바퀴·부시·프레임 열십자 구멍의 가운데 구멍을 지나간다. 양 끝이 같다(머리 없음).', pegs: [{ r: AXLE_STD.span / 2, id: 'p1', dir: [0, 1, 0], len: L, pos: [0, 0, 0] }], size: [AXLE_STD.span, L, AXLE_STD.span], holes: [], confidence: 'checked' }
    const data = { ...r.data, size: `${AXLE_STD.span}×${AXLE_STD.span}×${L}mm (십자단면 ${AXLE_STD.span}×${AXLE_STD.span}, 팔 폭 ${AXLE_STD.arm}, ${label})`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label.padEnd(8), r.data.name.padEnd(8), r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
if (!WRITE) console.log('\n(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)')
