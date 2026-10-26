// 로보타미주니어·에이스랩의 직선 프레임(13~513 꼴)을 부품에 등록된 색으로 만들어 부품 DB 에 넣는다. 이미 3D 모양(spec.shapes)이 있는 부품은 건드리지 않는다.
//   node scripts/make-robotron-straight-frames.mjs            → 시험(만들 목록과 모양 검사만)
//   node scripts/make-robotron-straight-frames.mjs --write    → 부품 행을 새 모양·연결점으로 바꿈(권별 수량·이름·색은 그대로)
// 규격: app/lib/junior-frame-mesh.js · acelab-frame-mesh.js. 이름 "NM프레임" = 폭 구멍 N × 길이 구멍 M (첫 숫자가 폭).
import fs from 'node:fs'
import { juniorFrame, JUNIOR_FRAME_STD } from '../app/lib/junior-frame-mesh.js'
import { acelabFrame, ACELAB_FRAME_STD } from '../app/lib/acelab-frame-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const ONLY = (process.argv.find((a) => a.startsWith('--only=')) || '').slice(7).split(',').filter(Boolean) // 이 이름의 부품은 3D 가 이미 있어도 다시 만든다(모양을 고칠 때)
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }

const BRANDS = [
  { label: '로보타미주니어', cat: 'ea24c385-7896-4d40-b343-1cef47e471e7', gen: juniorFrame, std: JUNIOR_FRAME_STD },
  { label: '에이스랩', cat: 'cf342cca-792f-4e70-863b-b12de631f1cc', gen: acelabFrame, std: ACELAB_FRAME_STD },
]
const HEX = { 다홍색: '#f45243', 블랙: '#555555', 그레이: '#9ca5af', 블루: '#0053fa', 스카이블루: '#82d0f8', 레드: '#e1493f', 화이트: '#f2f4f8' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')

// T프레임 = 15프레임 가운데에 13프레임을 직각으로 붙인 모양(칸 8개), V프레임 = 큐보 135도 프레임 꼴로 한 팔 4칸·한 팔 3칸(모서리 칸 공유, 구멍 6개). 사용자 지시 2026-10-26.
const COLOR_OVERRIDE = { '3십자프레임': '그레이' } // 사용자 지시 2026-10-26
const SPECIAL = {
  'V브라켓': (B, r, hex) => finish(B, r, hex, B.gen.vBracket(), 'V자(L브라켓의 안쪽각 90°를 120°로 벌림, 13프레임 판 바깥 35 + 12프레임 판 바깥 25)', false),
  'L브라켓': (B, r, hex) => finish(B, r, hex, B.gen.lBracket(), 'L자(13프레임 판 바깥 35 + 12프레임 판 바깥 25, 직각)', false),
  '3십자프레임': (B, r, hex) => finish(B, r, hex, B.gen.straight(3, 1, [1, 0]), '13프레임의 가운데 구멍만 4×4 십자 축이 들어가는 열십자 구멍(십자 전체 ' + B.std.crossSpan + '·팔 폭 ' + B.std.crossArm + ')', false, 1),
  'T프레임': (B, r, hex) => finish(B, r, hex, B.gen.grid([[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [2, 1], [2, 2]]), 'T자(15프레임 가운데 칸에 13프레임의 한쪽 끝 3칸이 겹침)', true),
  'V프레임': (B, r, hex) => finish(B, r, hex, B.gen.bent(4, 4, 60), 'V자(내측각 120°, 모서리 홀을 낀 한 팔 4홀 + 다른 팔 3홀 = 7홀)', false),
}
async function finish(B, r, hex, { tris, holes, connHoles, size: sz }, note, labeled, crossIdx = -1) {
  const stl = trianglesToStl(tris), P = B.std.pitch
  let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9
  for (let i = 0; i < tris.length; i += 3) { x0 = Math.min(x0, tris[i]); x1 = Math.max(x1, tris[i]); z0 = Math.min(z0, tris[i + 2]); z1 = Math.max(z1, tris[i + 2]) }
  const spec = { pitch: P, margin: B.std.margin, thickness: B.std.thickness, boreRadius: B.std.boreR, maxHolesPerArm: 5,
    shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: r.data.name + '_' + B.label + '.stl', fileDataUrl: toDataUrl(stl), brightness: 100 }], holeCoords: [], holeLabels: [] }
  if (crossIdx >= 0) holes.forEach((q, j) => { const label = 'X1Z' + (j + 1); spec.holeCoords.push({ x: 5, z: 5 + P * j, face: null, label }); spec.holeLabels.push(label) })
  if (labeled) holes.forEach((q) => { const label = `X${Math.round((q.z - holes[0].z) / P) + 1}Z${Math.round((q.x - holes[0].x) / P) + 1}`; spec.holeCoords.push({ x: 5 + (q.z - holes[0].z) + 0, z: 5 + (q.x - holes[0].x), face: null, label }); spec.holeLabels.push(label) })
  const hs = (connHoles || holes.map((q) => ({ pos: [q.x, 0, q.z], dir: [0, -1, 0] }))).map((q, j) => ({ id: 'h' + (j + 1), pos: q.pos.map((v) => +v.toFixed(3)), dir: q.dir, len: B.std.thickness, r: j === crossIdx ? B.std.crossSpan / 2 : B.std.boreR, through: true })) // 열십자 구멍은 축(십자 4×4) 돌기 반지름
  const connectors = { note: '구멍이 두께(y) 방향으로 10mm 격자. through=true 면 양쪽에서 끼울 수 있다.', pegs: [], size: sz || [+(x1 - x0).toFixed(1), B.std.thickness, +(z1 - z0).toFixed(1)], holes: hs, confidence: 'checked' }
  const size = `${connectors.size[0]}×${connectors.size[2]}×${connectors.size[1]}mm (${B.label}·테두리 없음·홀 규격사이즈 ${B.std.boreR * 2}, ${note}, 구멍 ${hs.length}개)`
  const data = { ...r.data, size, spec, connectors, primary_image: 'front' }
  delete data.thumbnail3d; delete data.thumbKey
  console.log(B.label.padEnd(8), r.data.name.padEnd(8), r.data.color, '삼각형', tris.length / 9, '구멍', hs.length, '크기', connectors.size.join('×'))
  if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
}

for (const B of BRANDS) {
  const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${B.cat}`)
  for (const r of rows) {
    const m = r.data.name.match(/^(\d)(\d+)프레임(\(.+\))?$/)
    const special = SPECIAL[r.data.name]
    if ((!m && !special) || (ONLY.length ? !ONLY.includes(r.data.name) : r.data.spec?.shapes?.length)) continue
    if (COLOR_OVERRIDE[r.data.name]) r.data.color = COLOR_OVERRIDE[r.data.name]
    const nz = special ? 0 : +m[1], nx = special ? 0 : +m[2], hex = HEX[r.data.color]
    if (!hex) { console.log('색 모름, 건너뜀', B.label, r.data.name, r.data.color); continue }
    if (special) { await special(B, r, hex); continue }
    const { tris, holes } = B.gen.straight(nx, nz)
    const stl = trianglesToStl(tris)
    const P = B.std.pitch
    const spec = {
      pitch: P, margin: B.std.margin, thickness: B.std.thickness, boreRadius: B.std.boreR, maxHolesPerArm: nx,
      shapes: [{ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color: hex, fileName: r.data.name.replace(/\(.+\)/, '') + '_' + B.label + '.stl', fileDataUrl: toDataUrl(stl), brightness: 100 }],
      holeCoords: [], holeLabels: [],
    }
    const hs = []
    for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) {
      const label = `X${k + 1}Z${i + 1}`
      spec.holeCoords.push({ x: 5 + P * k, z: 5 + P * i, face: null, label }); spec.holeLabels.push(label)
      hs.push({ id: 'h' + (hs.length + 1), pos: [i * P - ((nx - 1) * P) / 2, 0, k * P - ((nz - 1) * P) / 2], dir: [0, -1, 0], len: B.std.thickness, r: B.std.boreR, through: true })
    }
    const worst = Math.max(...holes.map((q, j) => Math.hypot(q.x - hs[j].pos[0], q.z - hs[j].pos[2]))) // 모델 구멍 위치와 연결점 위치 차이(0 이어야 한다)
    const connectors = { note: '구멍이 두께(y) 방향으로 10mm 격자. through=true 면 양쪽에서 끼울 수 있다.', pegs: [], size: [nx * P, B.std.thickness, nz * P], holes: hs, confidence: 'checked' }
    const size = `${nz * P}×${nx * P}×${B.std.thickness}mm (${B.label}·테두리 없음·홀 규격사이즈 ${B.std.boreR * 2}, 구멍 ${nz}×${nx}, ${P}mm피치 공식)`
    const data = { ...r.data, size, spec, connectors, primary_image: 'front', thumbKey: null, thumbnail3d: null, snapshot: null, snapshots: null }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(B.label.padEnd(8), r.data.name.padEnd(14), r.data.color.padEnd(5), `${nz}×${nx}`, '삼각형', tris.length / 9, '구멍', hs.length, '위치차', worst.toFixed(3), 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
if (!WRITE) console.log('\n(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)')
