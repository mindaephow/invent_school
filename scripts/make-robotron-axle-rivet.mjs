// 에이스랩·로보타미주니어의 축리벳(리벳 반쪽 + 4×4 십자 축 16mm)을 부품 DB 에 3D 로 등록한다(권별 수량·이름·색은 그대로).
//   node scripts/make-robotron-axle-rivet.mjs [--write]
import fs from 'node:fs'
import { axleRivetTriangles, AXLE_RIVET_STD } from '../app/lib/robotron-axle-rivet-mesh.js'
import { JUNIOR_RIVET_STD } from '../app/lib/junior-rivet-mesh.js'
import { AXLE_STD } from '../app/lib/robotron-axle-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = axleRivetTriangles(), stl = trianglesToStl(tris), L = AXLE_RIVET_STD.axleLen
const connectors = {
  note: `축리벳(리벳 반쪽 + 십자 축 ${L}). 마디(테두리 지름 ${AXLE_RIVET_STD.collarR * 2}, 두께 1)가 y −0.5~0.5, 갈라진 스냅핏 머리가 위(+y, 프레임 구멍에 끼움), 십자 축(${AXLE_STD.span}×${AXLE_STD.span})이 아래(−y)로 ${L} 뻗는다. 축은 열십자 구멍(부시·기어·바퀴 등)을 지나간다.`,
  pegs: [{ r: JUNIOR_RIVET_STD.headR, id: 'p1', dir: [0, 1, 0], len: 4, pos: [0, 3, 0] }, { r: AXLE_STD.span / 2, id: 'p2', dir: [0, -1, 0], len: L, pos: [0, -0.5, 0] }],
  holes: [], size: [AXLE_RIVET_STD.collarR * 2, 5 + 0.5 + L, AXLE_RIVET_STD.collarR * 2], confidence: 'checked',
}
for (const [cat, label] of Object.entries(CATS)) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('축리벳')}`)
  for (const r of rows) {
    const hex = HEX[r.data.color]
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `축리벳_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const data = { ...r.data, size: `리벳 반쪽(머리 지름 ${JUNIOR_RIVET_STD.headR * 2}, 테두리 지름 ${AXLE_RIVET_STD.collarR * 2}) + 십자 축 ${AXLE_STD.span}×${AXLE_STD.span} 길이 ${L}mm`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
