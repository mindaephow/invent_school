// 에이스랩 2&1 리벳(한쪽은 프레임 한 장에 들어가는 반쪽, 반대쪽은 프레임 두 장을 한 번에 지나는 긴 쪽)을 부품 DB 에 3D 로 등록한다(권별 수량·이름·색은 그대로).
//   node scripts/make-robotron-rivet2in1.mjs [--write]
import fs from 'node:fs'
import { rivet2in1Triangles, RIVET2IN1_STD as S } from '../app/lib/robotron-rivet2in1-mesh.js'
import { JUNIOR_RIVET_STD as R } from '../app/lib/junior-rivet-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc', HEX = { 블랙: '#555555', 그레이: '#9ca5af' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = rivet2in1Triangles(), stl = trianglesToStl(tris)
const T = S.frameT, shortL = S.shortFrames * T, longL = S.longFrames * T
const connectors = {
  note: `2&1 리벳. 마디(두께 1)가 y −0.5~0.5. +y 쪽은 프레임 ${S.shortFrames}장(길이 ${shortL})에 들어가는 반쪽, −y 쪽은 프레임 ${S.longFrames}장(길이 ${longL})을 한 번에 지나 결합하는 긴 쪽. 몸통 지름 ${R.shaftR * 2}·머리 지름 ${R.headR * 2}(스냅핏 십자 홈), 로보타미주니어 리벳과 같은 규격.`,
  pegs: [{ r: R.shaftR, id: 'p1', dir: [0, 1, 0], len: shortL - 1, pos: [0, 0.5 + (shortL - 1) / 2, 0] }, { r: R.shaftR, id: 'p2', dir: [0, -1, 0], len: longL - 1, pos: [0, -(0.5 + (longL - 1) / 2), 0] }],
  holes: [], size: [R.headR * 2, shortL + longL, R.headR * 2], confidence: 'checked',
}
for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent('2&1 리벳')}`)) {
  const spec = { shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: HEX[r.data.color], fileName: '2&1리벳_에이스랩.stl', fileDataUrl: toDataUrl(stl), brightness: 100 }] }
  const data = { ...r.data, size: `${R.headR * 2}×${shortL + longL}mm (에이스랩: 한쪽 프레임 ${S.shortFrames}장 반쪽 ${shortL} + 반대쪽 프레임 ${S.longFrames}장 관통 ${longL}, 몸통 지름 ${R.shaftR * 2}·머리 지름 ${R.headR * 2}, 가운데 마디 지름 ${R.collarR * 2})`, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  console.log(r.data.name, r.data.color, '삼각형', tris.length / 9, 'KB', Math.round(stl.length / 1024))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}
