// 에이스랩·로보타미주니어 리벳(몸통 지름 4.2·머리 지름 5.2·가운데 마디 지름 5.4, 길이 10 — 두 브랜드 같은 크기)을 부품 DB 에 3D 로 등록한다(권별 수량·이름·색은 그대로).
//   node scripts/make-robotron-rivet.mjs [--write]
import fs from 'node:fs'
import { juniorRivetTriangles, JUNIOR_RIVET_STD as R } from '../app/lib/junior-rivet-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 블랙: '#555555', 그레이: '#9ca5af' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = juniorRivetTriangles(), stl = trianglesToStl(tris)
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('리벳')}`)) {
    const spec = r.data.spec?.shapes?.length ? JSON.parse(JSON.stringify(r.data.spec)) : { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', brightness: 100 }] }
    Object.assign(spec.shapes[0], { color: HEX[r.data.color], fileName: `리벳_${label}.stl`, fileDataUrl: toDataUrl(stl) })
    const connectors = r.data.connectors || { pegs: [{ r: R.shaftR, id: 'p1', dir: [0, -1, 0], len: 4, pos: [0, -3, 0] }, { r: R.shaftR, id: 'p2', dir: [0, 1, 0], len: 4, pos: [0, 3, 0] }], holes: [], size: [R.headR * 2, 10, R.headR * 2], confidence: 'checked' }
    const data = { ...r.data, size: `6×6×10mm(${label}: 몸통 반지름 ${R.shaftR}·머리 반지름 ${R.headR}, 가운데 마디 반지름 ${R.collarR}(지름 ${R.collarR * 2})), 스냅핏 결합(프레임 두 장 사이 가운데에 놓임)`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
