// DB 에 3D 파일(import)로 들어 있는 부품(부시·눈블록·작은바퀴·데코바퀴·큰기어·스프라켓·서보혼·둥근서보혼)을 출력용으로 내보내 DB(data.print)에 등록한다.
//   node scripts/export-print-parts.mjs [저장 폴더] [--dry]   기본 저장: 다운로드/큐보_3D모델_프린트용/기타부품
// 지금은 치수 보정 없이 DB 3D 파일 그대로(원본) 내보낸다 — 출력해 보고 맞지 않는 곳이 생기면 그 부품만 보정해 같은 이름 규칙으로 다시 등록한다.
// 작은바퀴처럼 3D 도형이 여러 개면 도형마다 파일 하나씩(첫째 = print, 나머지 = print.extras). 원래 data.spec 은 건드리지 않는다.
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import zlib from 'node:zlib'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).replace(/^["']|["']$/g, '')]))
const dry = process.argv.includes('--dry'), out = process.argv.find((a, i) => i > 1 && !a.startsWith('--')) || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용', '기타부품')
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const api = (p, o = {}) => fetch(env.SUPABASE_URL + '/rest/v1/' + p, { ...o, headers: { ...H, ...(o.headers || {}) } })
const NAMES = ['부시', '눈블록', '작은바퀴', '데코바퀴', '큰기어', '스프라켓', '서보혼', '둥근서보혼']
const toBinary = (buf) => { // ASCII STL 이면 이진 STL 로 바꾼다
  if (buf.slice(0, 5).toString() !== 'solid' || !buf.slice(0, 400).toString().includes('facet')) return buf
  const t = [...buf.toString().matchAll(/vertex\s+(\S+)\s+(\S+)\s+(\S+)/g)].map((m) => [+m[1], +m[2], +m[3]]), n = t.length / 3, o = Buffer.alloc(84 + n * 50); o.writeUInt32LE(n, 80)
  for (let f = 0; f < n; f++) { const [a, b, c] = [t[f * 3], t[f * 3 + 1], t[f * 3 + 2]], u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [c[0] - a[0], c[1] - a[1], c[2] - a[2]]
    let nx = u[1] * w[2] - u[2] * w[1], ny = u[2] * w[0] - u[0] * w[2], nz = u[0] * w[1] - u[1] * w[0]; const l = Math.hypot(nx, ny, nz) || 1
    ;[nx / l, ny / l, nz / l, ...a, ...b, ...c].forEach((q, k) => o.writeFloatLE(q, 84 + f * 50 + k * 4)) }
  return o }
const bbox = (b) => { const n = b.readUInt32LE(80); let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < n; i++) for (let v = 0; v < 3; v++) for (let k = 0; k < 3; k++) { const x = b.readFloatLE(84 + i * 50 + 12 + v * 12 + k * 4); if (x < mn[k]) mn[k] = x; if (x > mx[k]) mx[k] = x } return mx.map((x, k) => +(x - mn[k]).toFixed(2)) }
fs.mkdirSync(path.join(out, 'DB백업'), { recursive: true })
for (const name of NAMES) {
  const rows = await (await api('ivs_part_catalog?select=id,data&data->>name=eq.' + encodeURIComponent(name))).json()
  if (!Array.isArray(rows) || rows.length !== 1) { console.log('❌', name, '행', Array.isArray(rows) ? rows.length : JSON.stringify(rows).slice(0, 100)); continue }
  const { id, data } = rows[0], shapes = (data.spec?.shapes || []).filter((s) => s.type === 'import' && s.fileDataUrl)
  if (!shapes.length) { console.log('❌', name, '3D 파일 없음'); continue }
  const files = shapes.map((s, i) => { const buf = toBinary(Buffer.from(s.fileDataUrl.split(',')[1], 'base64')), tag = shapes.length > 1 ? '_' + (s.fileName || '').replace(/\.stl$/i, '').replace(name + '_', '').replace(name, '본체') : ''
    return { file: `출력용-${name}${tag}_원본(보정없음).stl`, buf } })
  for (const f of files) fs.writeFileSync(path.join(out, f.file), f.buf)
  const pack = (f) => ({ file: f.file, 삼각형: (f.buf.length - 84) / 50, 바이트: f.buf.length, 크기: bbox(f.buf), stlGzBase64: zlib.gzipSync(f.buf, { level: 9 }).toString('base64') })
  const [main, ...rest] = files.map(pack)
  const print = { ...main, 보정: '없음(DB 3D 파일 그대로)', 노즐: 0.4, 재료: 'PLA', 만든곳: 'scripts/export-print-parts.mjs', 등록: new Date().toISOString(), ...(rest.length ? { extras: rest } : {}) }
  console.log(dry ? '(dry)' : '', name, files.map((f) => f.file + ' ' + bbox(f.buf).join('×')).join(' | '))
  if (dry) continue
  fs.writeFileSync(path.join(out, 'DB백업', name + '.json'), JSON.stringify(rows[0]))
  const w = await api('ivs_part_catalog?id=eq.' + id, { method: 'PATCH', body: JSON.stringify({ data: { ...data, print } }), headers: { Prefer: 'return=minimal' } })
  console.log(w.ok ? '  ✅ 등록' : '  ❌ ' + w.status + ' ' + (await w.text()).slice(0, 150))
}
