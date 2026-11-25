// 큐보 N×M 구멍 판(713프레임·515프레임 …) 3D 모델을 큐보 판 생성기(cubo-plate-mesh.js addPlate)로 다시 만들어 부품 행 data.spec.shapes[0].fileDataUrl 에 넣는다.
//   node scripts/register-713frame.mjs <부품이름 예: 713프레임|515프레임> [--dry]  — 덮어쓰기 전 원래 행을 scripts/DB백업/ 에 저장, data.thumbnail3d 는 비운다(썸네일 다시 그려야 함).
import fs from 'node:fs'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { addPlate } from '../app/lib/cubo-plate-mesh.js'
import { checkMesh, conformTJunctions } from '../app/lib/cubo-mesh-repair.js'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]))
const dry = process.argv.includes('--dry'), NAME = process.argv.slice(2).find((a) => !a.startsWith('--'))
const mm = /^(\d)(\d+)프레임$/.exec(NAME || ''); if (!mm) { console.log('사용: node scripts/register-713frame.mjs <713프레임|515프레임> [--dry]'); process.exit(1) }
const M = Number(mm[1]), N = Number(mm[2])
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const api = (p, o = {}) => fetch(env.SUPABASE_URL + '/rest/v1/' + p, { ...o, headers: { ...H, ...(o.headers || {}) } })
const all = await (await api('ivs_part_catalog?select=id,data&data->>name=eq.' + encodeURIComponent(NAME))).json()
const ref = await (await api('ivs_part_catalog?select=id,data&id=eq.14e9efb4-0bff-45a4-8a42-49c8a7f2eb10')).json() // 큐보 713프레임 = 큐보 카테고리 기준
const rows = all.filter((r) => r.data.category === ref[0].data.category)
if (rows.length !== 1) { console.log('큐보 행 수 ' + rows.length + ' (1개여야 함)'); process.exit(1) }
const ID = rows[0].id
const { data } = rows[0], sh = (data.spec && data.spec.shapes) || []
const readStl = (buf) => { const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength), n = dv.getUint32(80, true), t = new Float32Array(n * 9), mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]; for (let i = 0; i < n; i++) for (let v = 0; v < 3; v++) for (let k = 0; k < 3; k++) { const x = dv.getFloat32(84 + i * 50 + 12 + v * 12 + k * 4, true); t[i * 9 + v * 3 + k] = x; mn[k] = Math.min(mn[k], x); mx[k] = Math.max(mx[k], x) } return { n, t, mn: mn.map((x) => +x.toFixed(2)), mx: mx.map((x) => +x.toFixed(2)) } }
console.log('기존 shapes', sh.length, '| size', JSON.stringify(data.size || data.spec?.size), '| thumbnail3d', data.thumbnail3d ? '있음' : '없음')
sh.forEach((s, i) => console.log(' shape', i, Object.keys(s).join(','), s.fileDataUrl ? s.fileDataUrl.length : 0, s.color, s.paint))
if (sh[0] && sh[0].fileDataUrl) { const o = readStl(Buffer.from(sh[0].fileDataUrl.split(',')[1], 'base64')); console.log('기존 STL', o.n, o.mn, o.mx, JSON.stringify(checkMesh(o.t))) }
const kit = makeKit(20)
const xCells = Array.from({ length: N }, (_, i) => ({ lo: -N * S.pitch / 2 + i * S.pitch, hi: -N * S.pitch / 2 + (i + 1) * S.pitch, c: -N * S.pitch / 2 + S.margin + i * S.pitch }))
const zCells = Array.from({ length: M }, (_, i) => ({ lo: -M * S.pitch / 2 + i * S.pitch, hi: -M * S.pitch / 2 + (i + 1) * S.pitch, c: -M * S.pitch / 2 + S.margin + i * S.pitch }))
addPlate(kit, { xCells, zCells })
const tris = conformTJunctions(kit.result()), stl = trianglesToStl(tris), nw = readStl(Buffer.from(stl))
console.log('새 STL', nw.n, nw.mn, nw.mx, (stl.length / 1024).toFixed(0) + 'KB', JSON.stringify(checkMesh(tris)))
if (dry) process.exit(0)
const r = checkMesh(tris); if (r.open || r.same || !(r.volume > 0)) { console.log('검사 실패 — 등록 안 함'); process.exit(1) }
fs.mkdirSync(new URL('./DB백업/', import.meta.url), { recursive: true })
fs.writeFileSync(new URL('./DB백업/' + NAME + '_' + Date.now() + '.json', import.meta.url), JSON.stringify(rows[0]))
if (!sh.length) { console.log('shapes 비어 중단'); process.exit(1) }
const shapes = sh.map((s, i) => (i === 0 ? { ...s, fileDataUrl: 'data:application/octet-stream;base64,' + Buffer.from(stl).toString('base64') } : s))
const row = { ...data, spec: { ...data.spec, shapes } }; delete row.thumbnail3d
const w = await api('ivs_part_catalog?id=eq.' + ID, { method: 'PATCH', body: JSON.stringify({ data: row }), headers: { Prefer: 'return=minimal' } })
console.log(w.ok ? '등록 완료' : '실패 ' + w.status + ' ' + (await w.text()).slice(0, 200))
