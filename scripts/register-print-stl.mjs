// 출력용 프레임 STL 을 부품 DB(ivs_part_catalog)에 등록한다 — 각 부품 행의 data.print 에 gzip+base64 로 넣는다(조립도용 data.spec 은 건드리지 않는다).
//   node scripts/register-print-stl.mjs <STL 폴더(index.json 있는 곳)> [--dry] [--막]
//   빼서 쓰기: node scripts/get-print-stl.mjs <부품 이름|all> [저장 폴더]
// .env.local 의 SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 를 쓴다. 덮어쓰기 전에 원래 행을 <STL 폴더>/DB백업/ 에 JSON 으로 저장한다.
import fs from 'node:fs'
import path from 'node:path'
import zlib from 'node:zlib'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).replace(/^["']|["']$/g, '')]))
const dir = process.argv[2], dry = process.argv.includes('--dry'), KEY = process.argv.includes('--막') ? 'printSkin' : 'print' // --막: 위·아래 막 0.2 버전은 data.printSkin 에 넣는다
if (!dir) { console.log('사용: node scripts/register-print-stl.mjs <STL 폴더> [--dry]'); process.exit(1) }
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const api = (p, o = {}) => fetch(env.SUPABASE_URL + '/rest/v1/' + p, { ...o, headers: { ...H, ...(o.headers || {}) } })
const idx = JSON.parse(fs.readFileSync(path.join(dir, 'index.json'), 'utf8'))
const m = (f) => f.match(/목([\d.]+)_입구([\d.]+)_고리벽([\d.]+)_목두께([\d.]+)_총([\d.]+)(?:\+막([\d.]+))?\.stl$/)
fs.mkdirSync(path.join(dir, 'DB백업'), { recursive: true })
for (const [name, file] of Object.entries(idx)) {
  const buf = fs.readFileSync(path.join(dir, file)), g = zlib.gzipSync(buf, { level: 9 }), s = m(file)
  const r = await api('ivs_part_catalog?select=id,data&data->>name=eq.' + encodeURIComponent(name)); const rows = await r.json()
  if (!Array.isArray(rows) || rows.length !== 1) { console.log('❌', name, '행이', Array.isArray(rows) ? rows.length : JSON.stringify(rows).slice(0, 120), '개'); continue }
  const { id, data } = rows[0]
  fs.writeFileSync(path.join(dir, 'DB백업', name + (KEY === 'print' ? '' : '_막') + '.json'), JSON.stringify(rows[0]))
  const print = { file, 목지름: +s[1], 입구지름: +s[2], 고리벽: +s[3], 목두께: +s[4], 총두께: +s[5], 막: s[6] ? +s[6] : 0, 노즐: 0.4, 재료: 'PLA', 방향: '눕힘(두께가 z, 바닥 z=0)', 삼각형: (buf.length - 84) / 50, 바이트: buf.length, 만든곳: 'scripts/make-print-csg.mjs', 등록: new Date().toISOString(), stlGzBase64: g.toString('base64') }
  const row = { ...data, [KEY]: print }
  if (dry) { console.log('(dry)', name, file, buf.length, '→', g.length, 'gzip'); continue }
  const w = await api('ivs_part_catalog?id=eq.' + id, { method: 'PATCH', body: JSON.stringify({ data: row }), headers: { Prefer: 'return=minimal' } })
  console.log(w.ok ? '✅' : '❌ ' + w.status + ' ' + (await w.text()).slice(0, 150), name, file, (g.length / 1024).toFixed(0) + 'KB')
}
