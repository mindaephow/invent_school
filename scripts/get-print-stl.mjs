// DB(ivs_part_catalog) 에 등록한 출력용 STL 을 꺼내 파일로 저장한다.
//   node scripts/get-print-stl.mjs <부품 이름|all> [저장 폴더]   (기본: 다운로드/큐보_3D모델_프린트용/DB에서꺼냄)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import zlib from 'node:zlib'
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => /^[A-Z_]+=/.test(l)).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).replace(/^["']|["']$/g, '')]))
const want = process.argv[2], out = process.argv[3] || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용', 'DB에서꺼냄')
if (!want) { console.log('사용: node scripts/get-print-stl.mjs <부품 이름|all> [저장 폴더]'); process.exit(1) }
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY }
const q = 'ivs_part_catalog?select=data->>name,print:data->print&data->print=not.is.null' + (want === 'all' ? '' : '&data->>name=eq.' + encodeURIComponent(want))
const rows = await (await fetch(env.SUPABASE_URL + '/rest/v1/' + q, { headers: H })).json()
if (!Array.isArray(rows) || !rows.length) { console.log('등록된 출력용 STL 이 없다:', want); process.exit(1) }
fs.mkdirSync(out, { recursive: true })
for (const r of rows) { fs.writeFileSync(path.join(out, r.print.file), zlib.gunzipSync(Buffer.from(r.print.stlGzBase64, 'base64'))); console.log(r.name, '→', r.print.file) }
