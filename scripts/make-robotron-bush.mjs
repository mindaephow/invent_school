// 에이스랩·로보타미주니어 부시를 다시 만들어 등록한다: 지름 8·두께 5 원통, 가운데만 지름 7 로 움푹 들어간 실패 모양, 가운데 구멍은 4×4 십자 축용 열십자(4.4·팔 폭 1.4). 큐보는 건드리지 않는다.
//   node scripts/make-robotron-bush.mjs            → 시험
//   node scripts/make-robotron-bush.mjs --write    → 같은 이름의 행을 새 모양·연결점으로 바꿈(권별 수량·이름·색은 그대로)
import fs from 'node:fs'
import { bushTriangles, BUSH_STD } from '../app/lib/robotron-bush-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CUBO = '6fa8abd9-7684-47a2-bd7f-2bc9a6e3fbe6'
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 블랙: '#555555', 그레이: '#9ca5af' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const cubo = (await rest(`ivs_part_catalog?select=data&data->>category=eq.${CUBO}&data->>name=eq.${encodeURIComponent('부시')}`))[0].data
const tris = bushTriangles(), stl = trianglesToStl(tris)
console.log('부시 삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
for (const [cat, label] of Object.entries(CATS)) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('부시')}`)
  for (const r of rows) {
    const hex = HEX[r.data.color]
    const connectors = JSON.parse(JSON.stringify(cubo.connectors))
    connectors.note = '스페이서(실패 모양: 지름 8 원통 두께 5, 가운데만 지름 7). 위아래가 같다. 가운데 열십자 구멍(4.4×4.4)에 십자 축이 지나간다.'
    connectors.size = [BUSH_STD.r * 2, BUSH_STD.height, BUSH_STD.r * 2]
    connectors.holes.forEach((h) => { h.r = BUSH_STD.boreSpan / 2; h.len = BUSH_STD.height; h.pos = [0, 0, 0] }) // 가운데 열십자 구멍(축이 지나감)
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `부시_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const data = { ...r.data, size: `Ø${BUSH_STD.r * 2}×${BUSH_STD.height}mm (${label}, 가운데 지름 ${BUSH_STD.grooveR * 2} 홈 폭 ${BUSH_STD.grooveW}, 열십자 구멍 ${BUSH_STD.boreSpan}×${BUSH_STD.boreSpan}·팔 폭 ${BUSH_STD.boreArm})`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, '구멍 r', connectors.holes.map((h) => h.r).join(','))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
if (!WRITE) console.log('\n(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)')
