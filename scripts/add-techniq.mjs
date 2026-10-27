// 프로보 테크닉(LV1~7)을 등록한다(사용자 2026-10-27 "프로보 테크닉 등록하자"): 로봇 카테고리 → 부품(권별 키트 부품 목록 = 각 권 "LEVELn의 부품을 살펴보아요" 쪽) → 교재 7권(PDF·0차시 준비·차시 제목·차시별 필요 부품).
//   node scripts/add-techniq.mjs <techniq.json> <urls.json> [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const [SRC, URLS] = process.argv.filter((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT_NAME = '프로보 테크닉'
const src = JSON.parse(fs.readFileSync(SRC, 'utf8')), urls = fs.existsSync(URLS) ? JSON.parse(fs.readFileSync(URLS, 'utf8')) : {}
const key = (n) => n.replace(/\s+/g, '')
// 표기 정리: 같은 부품의 다른 표기를 하나로(키트 목록 표기 우선)
const CANON = { 파랑LED: '파랑LED보드', 빨강LED: '빨강LED보드', 적외선보드: '적외선센서보드', 서보모터: '서보모터(MS-780)', '5mm서포트': '5mm서포트', 메카넘휠A: '메카넘 휠', 메카넘휠B: '메카넘 휠' }
const canon = (n) => CANON[key(n)] || n.replace(/\s+/g, ' ').trim()
// 키트 목록 → 권별 {이름: 수량}. "휠&타이어 N" 은 휠 N + 타이어 N 으로 푼다. 메카넘 휠 A·B 는 합친다.
const kit = {}
for (const v of [1, 2, 3, 4, 5, 6, 7]) {
  kit[v] = new Map()
  const add = (n, q) => kit[v].set(n, (kit[v].get(n) || 0) + q)
  for (const [n0, q] of src[v].kit) { if (key(n0) === '휠&타이어') { add('휠', q); add('타이어', q) } else add(canon(n0), q) }
}
let problems = 0
const books = {}, allNames = new Set()
for (const v of [1, 2, 3, 4, 5, 6, 7]) {
  const chs = src[v].chapters, cumNames = new Map()
  for (let u = 1; u <= v; u++) kit[u].forEach((q, n) => cumNames.set(n, (cumNames.get(n) || 0) + q))
  const list = chs.map((c) => { const m = new Map(); c.items.forEach(([n0, q]) => { const n = canon(n0); m.set(n, (m.get(n) || 0) + q) }); return { no: c.no, title: c.title, m } })
  list.forEach((c) => { if (!c.title) { problems++; console.log(`  ${v}권 쪽 ${chs[list.indexOf(c)].page}: 차시 제목을 못 읽음`) } if (!c.m.size) { problems++; console.log(`  ${v}권 ${c.no}차시: 부품을 못 읽음`) }
    c.m.forEach((q, n) => { allNames.add(n); if (!cumNames.has(n)) { problems++; console.log(`  ${v}권 ${c.no}차시 ${n}: 1~${v}권 키트 목록에 없음`) } else if (q > cumNames.get(n)) console.log(`  (경고) ${v}권 ${c.no}차시 ${n} ${q} > 1~${v}권 키트 누적 ${cumNames.get(n)}`) }) })
  const nums = list.map((c) => c.no); nums.forEach((n, i) => { if (n !== i + 1) { problems++; console.log(`  ${v}권 차시 번호 순서가 이상함`, nums.join(',')) } })
  books[v] = { list, changjak: src[v].toc_has_changjak }
}
for (const v of [1, 2, 3, 4, 5, 6, 7]) kit[v].forEach((_, n) => allNames.add(n))
console.log('부품 종류', allNames.size, '| 권별 키트 부품', [1, 2, 3, 4, 5, 6, 7].map((v) => v + '권 ' + kit[v].size).join(', '), '| 문제', problems)
let cat = (await rest('ivs_robot_categories?select=id,data&data->>name=eq.' + encodeURIComponent(CAT_NAME)))[0]
console.log('카테고리', cat ? '이미 있음' : '없음(만들 예정)')
if (WRITE) {
  if (problems) { console.log('중단: 문제가 있어 등록하지 않음'); process.exit(1) }
  if (!cat) { await rest('ivs_robot_categories', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: CAT_NAME, volumes: 7, subject: 'robot', description: null, createdAt: Date.now() } }) }); cat = (await rest('ivs_robot_categories?select=id,data&data->>name=eq.' + encodeURIComponent(CAT_NAME)))[0]; console.log('→ 카테고리 등록', cat.id) }
  if ((await rest(`ivs_part_catalog?select=id&data->>category=eq.${cat.id}&limit=1`)).length) { console.log('중단: 이 카테고리에 이미 부품이 있음'); process.exit(1) }
  const rows = [...allNames].map((name) => ({ data: { name, icon: '', subject: 'robot', category: cat.id, volumes: [1, 2, 3, 4, 5, 6, 7].filter((v) => kit[v].has(name)).map((v) => ({ volume: v, qty: kit[v].get(name) })), color: null, size: null, createdAt: Date.now() } }))
  await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(rows) })
  console.log('→ 부품 등록', rows.length)
  const idOf = new Map((await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat.id}`)).map((r) => [r.data.name, r.id]))
  for (const v of [1, 2, 3, 4, 5, 6, 7]) {
    const { list, changjak } = books[v]
    const ch = [{ id: `ch_pt${v}_00`, files: [], parts: [], title: '준비', fileUrl: null, fileName: null }]
    list.forEach((c, i) => ch.push({ id: `ch_pt${v}_${String(i + 1).padStart(2, '0')}`, files: [], parts: [...c.m].map(([n, q]) => ({ partId: idOf.get(n), qty: q })), title: c.title, fileUrl: null, fileName: null }))
    if (changjak) ch.push({ id: `ch_pt${v}_${String(list.length + 1).padStart(2, '0')}`, files: [], parts: [], title: '나만의 창작로봇', fileUrl: null, fileName: null })
    await rest('ivs_textbooks', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: `프로보 테크닉${v}단계`, files: urls[v] || [], volume: v, subject: 'robot', category: cat.id, chapters: ch, createdAt: Date.now() + v } }) })
    console.log(`→ 교재 등록 프로보 테크닉${v}단계 차시 ${ch.length} PDF ${(urls[v] || []).length}`)
  }
}
