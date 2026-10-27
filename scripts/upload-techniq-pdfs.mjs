// 프로보 테크닉 1~7권 교재 PDF 를 Storage(textbook-files)에 올리고 URL 을 JSON 으로 남긴다(사용자 2026-10-27 "프로보 테크닉 등록하자"). 1~6권은 50MB 를 넘어 해상도를 줄인 사본(scratchpad/tq)을 올린다. 7권은 본문 + 표지 두 파일.
//   node scripts/upload-techniq-pdfs.mjs <사본폴더> <결과.json> [--write]
import fs from 'node:fs'
import path from 'node:path'
const WRITE = process.argv.includes('--write'), [COPY, OUT] = process.argv.filter((a) => !a.startsWith('--')).slice(2)
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const D = 'C:/Users/user/Downloads/테크닉 교재_LV1-LV7/'
const orig = fs.readdirSync(D).filter((f) => f.endsWith('.pdf'))
const find = (pat) => orig.find((f) => pat.test(f))
const FILES = [
  [1, COPY + '/techniq_1.pdf', find(/테크닉 1권/)], [2, COPY + '/techniq_2.pdf', find(/테크닉 2권/)], [3, COPY + '/techniq_3.pdf', find(/테크닉 3권/)],
  [4, COPY + '/techniq_4.pdf', find(/테크닉 4권/)], [5, COPY + '/techniq_5.pdf', find(/테크닉 5권/)], [6, COPY + '/techniq_6.pdf', find(/테크닉 6권/)],
  [7, D + find(/테크닉 7권_/), find(/테크닉 7권_/)], [7, D + find(/7권 표지/), find(/7권 표지/)],
]
const res = {}
for (const [vol, p, name] of FILES) {
  if (!fs.existsSync(p)) { console.log(vol + '권', name, '사본 없음 — 건너뜀'); continue }
  const size = fs.statSync(p).size
  console.log(vol + '권', name, (size / 1048576).toFixed(1) + 'MB', size > 50 * 1048576 ? '← 50MB 초과' : '')
  if (!WRITE || size > 50 * 1048576) continue
  const key = Date.now() + '_' + Math.random().toString(36).slice(2, 8) + '.pdf'
  const r = await fetch(env.SUPABASE_URL + '/storage/v1/object/textbook-files/' + key, { method: 'POST', headers: { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/pdf' }, body: fs.readFileSync(p) })
  if (!r.ok) { console.log('  업로드 실패', r.status, (await r.text()).slice(0, 200)); continue }
  ;(res[vol] ||= []).push({ url: env.SUPABASE_URL + '/storage/v1/object/public/textbook-files/' + key, name })
  console.log('  → 업로드')
}
if (WRITE && OUT) fs.writeFileSync(OUT, JSON.stringify(res, null, 1))
