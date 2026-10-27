// 프로보 익사이팅 LV1~4 교재 PDF 를 Storage(textbook-files)에 올리고 URL 을 JSON 으로 남긴다. 50MB 를 넘으면 건너뛴다.
//   node scripts/upload-proboexciting-pdfs.mjs <결과.json> [--write]
import fs from 'node:fs'
const WRITE = process.argv.includes('--write'), OUT = process.argv.find((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const res = {}
for (const vol of [1, 2, 3, 4]) {
  const name = `익사이팅LV${vol}_내지_대화형_(1).pdf`, p = 'C:/Users/user/Downloads/' + name, size = fs.statSync(p).size
  console.log(vol + '권', name, (size / 1048576).toFixed(1) + 'MB')
  if (!WRITE) continue
  if (size > 50 * 1048576) { console.log('  50MB 초과 — 건너뜀'); continue }
  const key = Date.now() + '_' + Math.random().toString(36).slice(2, 8) + '.pdf'
  const r = await fetch(env.SUPABASE_URL + '/storage/v1/object/textbook-files/' + key, { method: 'POST', headers: { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/pdf' }, body: fs.readFileSync(p) })
  if (!r.ok) { console.log('  업로드 실패', r.status, (await r.text()).slice(0, 200)); continue }
  res[vol] = { url: env.SUPABASE_URL + '/storage/v1/object/public/textbook-files/' + key, name }
  console.log('  → 업로드')
}
if (WRITE && OUT) fs.writeFileSync(OUT, JSON.stringify(res, null, 1))
