// 2열브라켓 3D 모델을 "LONG 글자 새긴" 새 생성기(app/lib/cubo-bracket-mesh.js)로 바꿔 부품 DB 행의 data.spec.shapes[0].fileDataUrl 에 넣는다(사용자 지시 2026-11-13).
//   node scripts/register-bracket-label.mjs [--dry]   — 덮어쓰기 전에 원래 행을 scripts/DB백업/ 에 JSON 으로 저장한다. data.thumbnail3d 는 비운다(썸네일을 다시 그려야 한다).
import fs from 'node:fs'
import { bracketTriangles } from '../app/lib/cubo-bracket-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
const dry = process.argv.includes('--dry'), ID = '792143c3-4555-431d-b72f-fa6cb8e7506c'
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const api = (p, o = {}) => fetch(env.SUPABASE_URL + '/rest/v1/' + p, { ...o, headers: { ...H, ...(o.headers || {}) } })
const rows = await (await api('ivs_part_catalog?select=id,data&id=eq.' + ID)).json()
if (!Array.isArray(rows) || rows.length !== 1) { console.log('❌ 행을 못 찾음', JSON.stringify(rows).slice(0, 200)); process.exit(1) }
const { data } = rows[0], sh = (data.spec && data.spec.shapes) || []
const bbox = (buf, off) => { const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength), n = dv.getUint32(80, true), mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let t = 0; t < n; t++) for (let v = 0; v < 3; v++) for (let k = 0; k < 3; k++) { const x = dv.getFloat32(84 + t * 50 + 12 + v * 12 + k * 4, true); mn[k] = Math.min(mn[k], x); mx[k] = Math.max(mx[k], x) } return { n, mn, mx } }
console.log('기존 shapes', sh.length, '| 이름', data.name, '| thumbnail3d', data.thumbnail3d ? '있음' : '없음')
const oldUrl = sh[0] && sh[0].fileDataUrl, oldBuf = oldUrl ? Buffer.from(oldUrl.split(',')[1], 'base64') : null
if (oldBuf) { const b = bbox(oldBuf); console.log('기존 STL', b.n, '삼각형', b.mn.map((x) => +x.toFixed(2)), b.mx.map((x) => +x.toFixed(2))) }
const tris = bracketTriangles(2, 10), stl = trianglesToStl(tris), nb = bbox(Buffer.from(stl))
console.log('새 STL', nb.n, '삼각형', nb.mn.map((x) => +x.toFixed(2)), nb.mx.map((x) => +x.toFixed(2)), (stl.length / 1024).toFixed(0) + 'KB', JSON.stringify(checkMesh(tris)))
if (dry) process.exit(0)
fs.mkdirSync(new URL('./DB백업/', import.meta.url), { recursive: true })
fs.writeFileSync(new URL('./DB백업/2열브라켓_' + Date.now() + '.json', import.meta.url), JSON.stringify(rows[0]))
const shapes = sh.length ? sh.map((s, i) => (i === 0 ? { ...s, fileDataUrl: 'data:application/octet-stream;base64,' + Buffer.from(stl).toString('base64') } : s)) : null
if (!shapes) { console.log('❌ shapes 가 비어 있어 중단'); process.exit(1) }
const row = { ...data, spec: { ...data.spec, shapes } }; delete row.thumbnail3d
const w = await api('ivs_part_catalog?id=eq.' + ID, { method: 'PATCH', body: JSON.stringify({ data: row }), headers: { Prefer: 'return=minimal' } })
console.log(w.ok ? '✅ 등록' : '❌ ' + w.status + ' ' + (await w.text()).slice(0, 200))
