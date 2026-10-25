// 로버트론 제품(로보타미주니어·에이스랩) 프레임 출력용 STL — 구멍 목에 홈 8곳을 판 3D 프린터용(노즐 0.4 PLA, 눕혀서 출력: 두께가 z, 바닥 z=0, 가운데 맞춤).
//   node scripts/make-robotron-print.mjs <junior|acelab> [--write]
//   기본: STL 만 만들어 다운로드/<브랜드>_출력용_홈8/ 에 저장하고 검사한다(index.json 에 이름→파일).
//   --write: 로보타미주니어는 부품 DB 의 같은 이름 행(data.print)에 gzip+base64 로 넣는다(큐보 register-print-stl.mjs 와 같은 방식, 같은 이름이 큐보에도 있어 카테고리로 가려 넣는다). 에이스랩은 아직 DB 에 부품이 없어 파일만 만든다.
// 규격: app/lib/junior-frame-mesh.js · acelab-frame-mesh.js 의 *_PRINT_STD (목 지름 4.5 → 5.10, 홈 8곳 폭 0.8·깊이 0.3).
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import zlib from 'node:zlib'
import { juniorPrintFrame, JUNIOR_PRINT_STD } from '../app/lib/junior-frame-mesh.js'
import { acelabPrintFrame, ACELAB_PRINT_STD } from '../app/lib/acelab-frame-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'

const brand = process.argv[2], WRITE = process.argv.includes('--write')
const BRANDS = {
  junior: { label: '로보타미주니어', gen: juniorPrintFrame, std: JUNIOR_PRINT_STD, category: 'ea24c385-7896-4d40-b343-1cef47e471e7' },
  acelab: { label: '에이스랩', gen: acelabPrintFrame, std: ACELAB_PRINT_STD, category: 'cf342cca-792f-4e70-863b-b12de631f1cc' },
}
const B = BRANDS[brand]
if (!B) { console.error('사용: node scripts/make-robotron-print.mjs <junior|acelab> [--write]'); process.exit(1) }
const OUT = path.join(os.homedir(), 'Downloads', B.label + '_출력용_홈8')
fs.mkdirSync(OUT, { recursive: true })
const g = B.gen
const FRAMES = {
  '115프레임': () => g.straight(15, 1), '15프레임': () => g.straight(5, 1), '17프레임': () => g.straight(7, 1), '19프레임': () => g.straight(9, 1),
  '215프레임': () => g.straight(15, 2), '25프레임': () => g.straight(5, 2), '27프레임': () => g.straight(7, 2), '29프레임': () => g.straight(9, 2),
  '315프레임': () => g.straight(15, 3), '35프레임': () => g.straight(5, 3), '37프레임': () => g.straight(7, 3), '39프레임': () => g.straight(9, 3),
  '515프레임': () => g.straight(15, 5), '59프레임': () => g.straight(9, 5), '713프레임': () => g.straight(13, 7),
  '135도 프레임': () => g.bent(6, 4, 45), '90도 프레임': () => g.bent(3, 3, 90), '반원프레임': () => g.arc(),
}
function check(tris) { // 짝 없는 모서리·부피·크기
  const key = (a) => a.map((v) => Math.round(v * 1e4)).join(',')
  const edges = new Map(), n = tris.length / 9
  let vol = 0
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let t = 0; t < n; t++) {
    const v = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]])
    for (const q of v) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], q[k]); mx[k] = Math.max(mx[k], q[k]) }
    vol += (v[0][0] * (v[1][1] * v[2][2] - v[1][2] * v[2][1]) - v[0][1] * (v[1][0] * v[2][2] - v[1][2] * v[2][0]) + v[0][2] * (v[1][0] * v[2][1] - v[1][1] * v[2][0])) / 6
    for (let e = 0; e < 3; e++) { const a = key(v[e]), b = key(v[(e + 1) % 3]); if (edges.has(b + '>' + a)) edges.delete(b + '>' + a); else edges.set(a + '>' + b, 1) }
  }
  return { tris: n, unpaired: edges.size, volume: +vol.toFixed(1), size: mx.map((m, k) => +(m - mn[k]).toFixed(2)) }
}
const SPEC = `목${(B.std.boreR * 2).toFixed(2)}_총${B.std.thickness}_홈${B.std.notch}`
const idx = {}, stls = {}
for (const [name, build] of Object.entries(FRAMES)) {
  const { tris } = build()
  const c = check(tris)
  const stl = Buffer.from(trianglesToStl(tris))
  const file = `출력용-${name.replace(/ /g, '')}_${SPEC}.stl`
  fs.writeFileSync(path.join(OUT, file), stl)
  idx[name] = file; stls[name] = { stl, file, tris: c.tris }
  console.log(name.padEnd(10), '삼각형', String(c.tris).padStart(6), '짝없음', c.unpaired, '부피', c.volume, '크기', c.size.join('×'), 'KB', Math.round(stl.length / 1024))
}
fs.writeFileSync(path.join(OUT, 'index.json'), JSON.stringify(idx, null, 1))
console.log('\n저장 폴더:', OUT)
if (!WRITE) { console.log('(DB 는 바꾸지 않음. 로보타미주니어를 DB 에 넣으려면 --write)'); process.exit(0) }
if (brand !== 'junior') { console.log('에이스랩은 DB 에 부품이 없어 파일만 만들었습니다.'); process.exit(0) }
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rows = await (await fetch(env.SUPABASE_URL + '/rest/v1/ivs_part_catalog?select=id,data&data->>category=eq.' + B.category, { headers: H })).json()
for (const [name, { stl, file, tris }] of Object.entries(stls)) {
  const row = rows.find((r) => r.data.name === name)
  if (!row) { console.log('❌ DB 에 없음:', name); continue }
  const gz = zlib.gzipSync(stl, { level: 9 })
  row.data.print = { file, 목지름: +(B.std.boreR * 2).toFixed(2), 총두께: B.std.thickness, 홈: B.std.notch, 홈폭: B.std.notchW, 홈깊이: B.std.notchD, 삼각형: tris, 바이트: stl.length, 노즐: 0.4, 재료: 'PLA', 방향: '눕힘(두께가 z, 바닥 z=0)', 등록: new Date().toISOString(), 만든곳: 'scripts/make-robotron-print.mjs', stlGzBase64: gz.toString('base64') }
  const w = await fetch(env.SUPABASE_URL + '/rest/v1/ivs_part_catalog?id=eq.' + row.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: row.data }) })
  console.log(w.ok ? '✅' : '❌ ' + w.status, name, file, (gz.length / 1024).toFixed(0) + 'KB')
}
