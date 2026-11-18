// 교구비교용 부품 데이터 만들기 — 부품 DB(교재 차시별 부품·수량)를 public/kit-parts.json 으로 내려받는다.
//   node scripts/make-kit-parts.mjs
// 결과: { 교구이름: { 권: { 모델이름: { 부품이름: 수량 } } } } — 준비·창작 차시는 뺀다.
import fs from 'node:fs'

const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim()]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY }
const rest = async (p) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H }); if (!r.ok) throw new Error(p + ' ' + r.status); return r.json() }

const cats = Object.fromEntries((await rest('ivs_robot_categories?select=id,name:data->>name')).map((c) => [c.id, c.name]))
const parts = Object.fromEntries((await rest('ivs_part_catalog?select=id,name:data->>name&limit=5000')).map((p) => [p.id, p.name]))
const books = await rest('ivs_textbooks?select=data->>category,data->>volume,chapters:data->chapters&limit=500')

const out = {}
let models = 0, missing = 0
for (const b of books) {
  const kit = cats[b.category]; if (!kit) continue
  for (const ch of b.chapters || []) {
    const t = (ch.title || '').trim()
    if (!t || /^준비|창작|나만의/.test(t) || !(ch.parts || []).length) continue
    const m = {}
    for (const p of ch.parts) { const n = parts[p.partId]; if (!n) { missing++; continue } m[n] = (m[n] || 0) + (p.qty || 0) }
    ;((out[kit] ||= {})[b.volume] ||= {})[t] = m; models++
  }
}
fs.writeFileSync(new URL('../public/kit-parts.json', import.meta.url), JSON.stringify(out))
console.log('교구', Object.keys(out).join(', '), '| 모델', models, '| 이름 못 찾은 부품', missing)
for (const k of Object.keys(out)) console.log(' ', k, Object.keys(out[k]).map((v) => v + '권:' + Object.keys(out[k][v]).length).join(' '))
