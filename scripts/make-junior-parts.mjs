// 로보타미주니어(로버트론 제품) 부품 만들기: 큐보 프레임 전체·리벳을 로버트론 규격으로 다시 만들고, 부시·축은 색만 바꿔 복사해 부품 DB 에 등록한다.
//   node scripts/make-junior-parts.mjs            → 시험(STL 만들고 검사만, DB 는 안 건드림)
//   node scripts/make-junior-parts.mjs --write    → 부품 DB(ivs_part_catalog)에 새 행으로 등록(이미 등록된 이름은 같은 행을 새 모양으로 바꿈)
// 규격: app/lib/junior-frame-mesh.js · junior-rivet-mesh.js. 에이스랩은 acelab-frame-mesh.js 로 따로 둔다.
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { randomUUID } from 'node:crypto'
import { juniorFrame, JUNIOR_FRAME_STD } from '../app/lib/junior-frame-mesh.js'
import { juniorRivetTriangles } from '../app/lib/junior-rivet-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const WRITE = process.argv.includes('--write')
const OUT = path.join(os.tmpdir(), 'robotron_junior_parts_stl') // 확인용 사본은 임시 폴더에만 둔다(다운로드 폴더에는 출력용만 전달 — 사용자 2026-10-25)
fs.mkdirSync(OUT, { recursive: true })
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }

const CUBO = '6fa8abd9-7684-47a2-bd7f-2bc9a6e3fbe6' // 큐보 카테고리
const JUNIOR = 'ea24c385-7896-4d40-b343-1cef47e471e7' // 로보타미주니어 카테고리
const COLORS = { 다홍색: '#f45243', 블랙: '#26282c' }

// 만들 프레임: 이름 → 만드는 법. 직선 프레임은 [길이 방향 구멍 수, 폭 방향 구멍 수].
const FRAMES = {
  '115프레임': () => juniorFrame.straight(15, 1), '15프레임': () => juniorFrame.straight(5, 1), '17프레임': () => juniorFrame.straight(7, 1), '19프레임': () => juniorFrame.straight(9, 1),
  '215프레임': () => juniorFrame.straight(15, 2), '25프레임': () => juniorFrame.straight(5, 2), '27프레임': () => juniorFrame.straight(7, 2), '29프레임': () => juniorFrame.straight(9, 2),
  '315프레임': () => juniorFrame.straight(15, 3), '35프레임': () => juniorFrame.straight(5, 3), '37프레임': () => juniorFrame.straight(7, 3), '39프레임': () => juniorFrame.straight(9, 3),
  '515프레임': () => juniorFrame.straight(15, 5), '59프레임': () => juniorFrame.straight(9, 5), '713프레임': () => juniorFrame.straight(13, 7),
  '135도 프레임': () => juniorFrame.bent(6, 4, 45), '90도 프레임': () => juniorFrame.bent(3, 3, 90), '반원프레임': () => juniorFrame.arc(),
}

// 메시 검사: 짝 없는 모서리, 부피 부호, 크기
function check(tris) {
  const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(',')
  const edges = new Map()
  const n = tris.length / 9
  let vol = 0
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let t = 0; t < n; t++) {
    const p = (k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]]
    const v = [p(0), p(1), p(2)]
    for (const q of v) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], q[k]); mx[k] = Math.max(mx[k], q[k]) }
    vol += (v[0][0] * (v[1][1] * v[2][2] - v[1][2] * v[2][1]) - v[0][1] * (v[1][0] * v[2][2] - v[1][2] * v[2][0]) + v[0][2] * (v[1][0] * v[2][1] - v[1][1] * v[2][0])) / 6
    for (let e = 0; e < 3; e++) {
      const a = v[e], b = v[(e + 1) % 3], ka = key(...a), kb = key(...b)
      const k1 = ka + '>' + kb, k2 = kb + '>' + ka
      if (edges.has(k2)) { edges.delete(k2) } else edges.set(k1, 1)
    }
  }
  return { tris: n, unpaired: edges.size, volume: +vol.toFixed(1), size: mx.map((m, k) => +(m - mn[k]).toFixed(2)), min: mn.map((v) => +v.toFixed(2)), max: mx.map((v) => +v.toFixed(2)) }
}

const toDataUrl = (stlBytes) => 'data:application/octet-stream;base64,' + Buffer.from(stlBytes).toString('base64')
const orig = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CUBO}`)
const byName = Object.fromEntries(orig.map((r) => [r.data.name, r]))
const existingRows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${JUNIOR}`)
const existing = new Map(existingRows.map((r) => [r.data.name, r]))
const rows = []

function makeRow(srcName, { stl, holes, color, sizeNote, extraSpec }) {
  const src = byName[srcName]
  if (!src) throw new Error('큐보에 ' + srcName + ' 없음')
  const d = JSON.parse(JSON.stringify(src.data))
  delete d.print; delete d.printSkin; delete d.thumbnail3d; delete d.thumbKey; delete d.snapshot; delete d.snapshots
  d.image_svg = ''; d.image_svg_diagonal = '' // 큐보 부품의 옛 svg 그림은 가져오지 않는다(3D 썸네일만 쓴다)
  d.category = JUNIOR; d.volumes = []; d.color = color; d.createdAt = Date.now()
  if (sizeNote) d.size = sizeNote
  const shape = d.spec?.shapes?.[0]
  if (stl) shape && Object.assign(shape, { type: 'import', color: COLORS[color], fileName: srcName + '_로버트론.stl', fileDataUrl: toDataUrl(stl) })
  else if (shape) shape.color = COLORS[color]
  if (extraSpec) Object.assign(d.spec, extraSpec)
  if (d.connectors?.holes && holes) { // 큐보 연결점(id·방향)을 그대로 쓰되 위치는 새 모델의 구멍 중심, 반지름은 로버트론 값. 모델 회전(shape.ry)이 있으면 그만큼 돌린 자리와 맞춘다.
    const ry = shape?.ry || 0, cr = Math.cos(ry), sr = Math.sin(ry)
    const rot = holes.map((q) => ({ x: q.x * cr + q.z * sr, z: -q.x * sr + q.z * cr })) // 모델 좌표(회전 적용 뒤)
    let worst = 0
    const used = new Set()
    for (const h of d.connectors.holes) {
      let bi = -1, bd = 1e9
      rot.forEach((q, i) => { if (used.has(i)) return; const dist = Math.hypot(q.x - h.pos[0], q.z - h.pos[2]); if (dist < bd) { bd = dist; bi = i } })
      worst = Math.max(worst, bd)
      if (bd > 0.3) { d.__holeDiff = 99; continue } // 큐보 연결점과 자리가 안 맞으면 아래에서 새로 만든다
      used.add(bi); h.pos = [+rot[bi].x.toFixed(3), h.pos[1], +rot[bi].z.toFixed(3)]; h.r = JUNIOR_FRAME_STD.boreR
    }
    if (d.__holeDiff === 99) { // 자리가 안 맞는 부품(90도 프레임): 새 모델 구멍으로 연결점을 다시 만든다(id 는 모델 순서대로 h1…)
      d.connectors.holes = rot.map((q, i) => ({ id: 'h' + (i + 1), pos: [+q.x.toFixed(3), 0, +q.z.toFixed(3)], dir: [0, -1, 0], len: 5, r: JUNIOR_FRAME_STD.boreR, through: true }))
      d.connectors.confidence = 'auto'
    }
    d.__holeDiff = +worst.toFixed(3)
  }
  return { id: randomUUID(), data: d }
}

for (const [name, build] of Object.entries(FRAMES)) {
  const { tris, holes } = build()
  const c = check(tris)
  const stl = trianglesToStl(tris)
  fs.writeFileSync(path.join(OUT, name + '.stl'), stl)
  const src = byName[name]?.data
  const row = makeRow(name, { stl, holes, color: '다홍색', sizeNote: src?.size ? src.size.replace(/\(구멍/, '(로버트론·테두리 없음·구멍 지름 4.5, 구멍') : null, extraSpec: { boreRadius: JUNIOR_FRAME_STD.boreR } })
  console.log(name.padEnd(10), 'tris', String(c.tris).padStart(5), '짝없음', c.unpaired, '부피', c.volume, '크기', c.size.join('×'), '구멍위치차', row.data.__holeDiff ?? '-', 'KB', Math.round(stl.length / 1024))
  delete row.data.__holeDiff
  rows.push(row)
}
{ // 리벳
  const tris = juniorRivetTriangles()
  const c = check(tris), stl = trianglesToStl(tris)
  fs.writeFileSync(path.join(OUT, '리벳.stl'), stl)
  console.log('리벳'.padEnd(10), 'tris', c.tris, '짝없음', c.unpaired, '부피', c.volume, '크기', c.size.join('×'), 'KB', Math.round(stl.length / 1024))
  rows.push(makeRow('리벳', { stl, color: '블랙', sizeNote: '6×6×10mm(로버트론: 몸통 반지름 2.1·머리 반지름 2.6, 가운데 마디 반지름 2.2), 스냅핏 결합(프레임 두 장 사이 가운데에 놓임)' }))
}
for (const name of ['부시', '축']) rows.push(makeRow(name, { color: '블랙' })) // 색만 바꾼 복사

console.log('\n등록 대상', rows.length, '개:', rows.map((r) => r.data.name).join(', '))
const again = rows.filter((r) => existing.has(r.data.name)).map((r) => r.data.name)
if (again.length) console.log('이미 로보타미주니어에 있어 같은 행을 새 모양으로 바꿈:', again.join(', '))
if (!WRITE) { console.log('\n(시험 실행: DB 는 바꾸지 않음. 등록하려면 --write)'); process.exit(0) }
const ONLY_MISSING = process.argv.includes('--only-missing') // 이미 등록된 행은 건드리지 않고 없는 것만 새로 등록한다(삭제된 부품 복구용)
for (const r of rows) {
  const old = existing.get(r.data.name)
  if (old && ONLY_MISSING) { console.log('건너뜀(이미 있음):', r.data.name); continue }
  if (old) { // 이미 등록된 행(같은 이름): id·등록 시각은 그대로 두고 모양·연결점만 새 값으로 바꾼다
    r.data.createdAt = old.data.createdAt
    await rest('ivs_part_catalog?id=eq.' + old.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: r.data }) })
    console.log('수정:', r.data.name, old.id)
    continue
  }
  await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(r) })
  console.log('등록:', r.data.name, r.id)
}
