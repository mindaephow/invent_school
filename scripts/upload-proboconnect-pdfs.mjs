// 프로보 커넥트 1~6권 교재 PDF 를 Storage(textbook-files)에 올리고 결과 URL 을 JSON 으로 남긴다(사용자 2026-10-27 "커넥트 1~4권 pdf파일 먼저 등록", "5권6권도 등록~ 용량 너무 크면 적당한 해상도로 줄여서").
// 50MB 를 넘는 것(2권 58MB·5권 219MB)은 미리 해상도를 줄여 만든 사본(scratchpad/pdf)을 올린다.
//   node scripts/upload-proboconnect-pdfs.mjs <결과.json> [--write]
import fs from 'node:fs'
import path from 'node:path'

const WRITE = process.argv.includes('--write'), OUT = process.argv.find((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const SP = 'C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Downloads/9a5b1fbd-0b9c-41ca-8aef-d226c290a210/scratchpad/pdf/'
const D = 'C:/Users/user/Downloads/프로보커넥트/'
const FILES = [
  [1, D + '프로보커넥트_LV1/프로보커넥트_LV1.pdf', '프로보커넥트_LV1.pdf'],
  [2, SP + '프로보커넥트_LV2.pdf', '프로보커넥트_LV2.pdf'],
  [3, D + '프로보커넥트_LV3/프로보커넥트_LV3.pdf', '프로보커넥트_LV3.pdf'],
  [4, D + '프로보커넥트_LV4/프로보커넥트_LV4.pdf', '프로보커넥트_LV4.pdf'],
  [5, SP + '커넥트 5권_231229.pdf', '커넥트 5권_231229.pdf'],
  [6, D + '★20240905_커넥트_Lv6_저용량.pdf', '★20240905_커넥트_Lv6_저용량.pdf'],
]
const res = {}
for (const [vol, p, name] of FILES) {
  const size = fs.statSync(p).size
  console.log(vol + '권', name, (size / 1048576).toFixed(1) + 'MB', size > 50 * 1048576 ? '← 50MB 초과' : '')
  if (!WRITE) continue
  if (size > 50 * 1048576) { console.log('  건너뜀(50MB 초과)'); continue }
  const key = Date.now() + '_' + Math.random().toString(36).slice(2, 8) + '.pdf'
  const r = await fetch(env.SUPABASE_URL + '/storage/v1/object/textbook-files/' + key, { method: 'POST', headers: { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/pdf' }, body: fs.readFileSync(p) })
  if (!r.ok) { console.log('  업로드 실패', r.status, (await r.text()).slice(0, 200)); continue }
  res[vol] = { url: env.SUPABASE_URL + '/storage/v1/object/public/textbook-files/' + key, name }
  console.log('  → 업로드', res[vol].url)
}
if (WRITE && OUT) fs.writeFileSync(OUT, JSON.stringify(res, null, 1))
