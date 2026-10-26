// 에이스랩·로보타미주니어의 휠가이드(DC모터에 결합)를 부품 DB 에 3D 로 등록한다(권별 수량·이름·색은 그대로).
//   node scripts/make-robotron-wheelguide.mjs [--write]
import fs from 'node:fs'
import { wheelGuideTriangles, wheelGuideSpots, WHEELGUIDE_STD as W } from '../app/lib/robotron-wheelguide-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 그레이: '#9ca5af', 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = wheelGuideTriangles(), stl = trianglesToStl(tris)
const dir = [0, -1, 0]
const connectors = {
  note: `휠가이드(DC모터에 결합). 지름 ${W.discR * 2}·두께 ${W.discH} 원판, 가운데 한쪽(+y)에 지름 ${W.bossR * 2} 돌기(전체 높이 ${W.totalH}). 가운데 지름 ${W.screwR * 2} 나사 구멍(h1, 돌기까지 관통), 그 주위 열십자로 피치 ${W.pitch} 떨어진 지름 ${W.holeR * 2} 구멍 4개(h2~h5: +x, −x, +z, −z, 육각 구멍 대변 ${W.endHexFlat})와 이웃한 두 구멍의 가운데(대각선 ±${W.pitch / 2}, ±${W.pitch / 2}) 같은 구멍 4개(h6~h9). 원판 옆면 가운데에는 폭 ${W.grooveW}·깊이 ${W.grooveDepth} 실타래 홈이 있다(두께 4 = 1+2+1). 돌기 끝 가운데에는 대변 ${W.centerHexFlat}, 깊이 ${W.centerHexDepth} 육각 홈이 있고 나사 구멍과 이어진다. 바닥쪽(돌기 반대면)은 구멍 9개마다 ${W.pocketSide}×${W.pocketSide}, 깊이 ${W.pocketDepth} 사각 홈(프레임 칸처럼, 구멍 줄에 맞춰 모델 축 기준 45° 돌림)이 있다.`,
  pegs: [],
  holes: [{ id: 'h1', r: W.screwR, dir, len: W.totalH, pos: [0, 0, 0], through: true }, ...wheelGuideSpots().map(([x, z], i) => ({ id: 'h' + (i + 2), r: W.holeR, dir, len: W.discH, pos: [x, 0, z], through: true }))],
  size: [W.discR * 2, W.totalH, W.discR * 2], confidence: 'checked',
}
for (const [cat, label] of Object.entries(CATS)) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('휠가이드')}`)
  for (const r of rows) {
    const hex = HEX[r.data.color]
    const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: `휠가이드_${label}.stl`, fileDataUrl: toDataUrl(stl), brightness: 100 }] }
    const data = { ...r.data, size: `Ø${W.discR * 2}×${W.totalH}mm (${label}, 원판 두께 ${W.discH}, 가운데 돌기 지름 ${W.bossR * 2}, 나사 구멍 지름 ${W.screwR * 2}, 열십자 구멍 4개(육각 대변 ${W.endHexFlat}) 피치 ${W.pitch} + 그 사이 가운데 구멍 4개, 옆면 실타래 홈 폭 ${W.grooveW} 깊이 ${W.grooveDepth}, 바닥쪽 사각 홈 9개 ${W.pocketSide}×${W.pocketSide} 깊이 ${W.pocketDepth}, 돌기 끝 육각 홈 대변 ${W.centerHexFlat} 깊이 ${W.centerHexDepth})`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
