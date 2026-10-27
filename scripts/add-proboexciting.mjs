// 프로보 익사이팅(LV1~4)을 등록한다(사용자 2026-10-27 "프로보익사이팅 등록"): 로봇 카테고리 → 부품(차시별 필요 부품의 권별 최대 수량) → 교재 4권(PDF·0차시 준비·차시 제목·차시별 필요 부품).
// 익사이팅 교재에는 4단계처럼 키트 전체 "부품수량확인" 쪽이 없어서, 권별 부품 수량은 그 권 차시들 중 가장 많이 필요한 수량(차시는 하나씩 만드니 키트는 최소 그만큼 있다)으로 넣는다.
//   node scripts/add-proboexciting.mjs <exc.json> <urls.json> [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const [EXC, URLS] = process.argv.filter((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT_NAME = '프로보 익사이팅'
const exc = JSON.parse(fs.readFileSync(EXC, 'utf8')), urls = fs.existsSync(URLS) ? JSON.parse(fs.readFileSync(URLS, 'utf8')) : {}
const FIX = { LED블럭레드: 'LED블럭 레드', LED블럭블루: 'LED블럭 블루', 고무링블랙: '고무링 블랙', 고무줄레드: '고무줄 레드', 스티로폼공: '스티로폼 공' }
const fix = (n) => FIX[n] || n
// 권별 부품 최대 수량 + 차시별 목록
const byVol = {}, names = new Set(); let problems = 0
for (const vol of [1, 2, 3, 4]) {
  const { titles, lists } = exc[vol]
  if (titles.length !== lists.length) { problems++; console.log(vol + '권 차시 제목 수와 부품 목록 수가 다름', titles.length, lists.length) }
  byVol[vol] = { titles, chapters: lists.map((l) => { const m = new Map(); l.items.forEach(([n, q]) => m.set(fix(n), (m.get(fix(n)) || 0) + q)); return m }) }
  byVol[vol].chapters.forEach((m, i) => { if (!m.size) { problems++; console.log(`  ${vol}권 ${i + 1}차시 ${titles[i]}: 부품을 못 읽음`) } m.forEach((_, n) => names.add(n)) })
}
const maxQty = new Map() // 이름 → {vol: 최대}
for (const vol of [1, 2, 3, 4]) byVol[vol].chapters.forEach((m) => m.forEach((q, n) => { const o = maxQty.get(n) || {}; o[vol] = Math.max(o[vol] || 0, q); maxQty.set(n, o) }))
console.log('부품 종류', names.size, '| 권별 종류', [1, 2, 3, 4].map((v) => v + '권 ' + [...maxQty.values()].filter((o) => o[v]).length).join(', '), '| 문제', problems)
let cat = (await rest('ivs_robot_categories?select=id,data&data->>name=eq.' + encodeURIComponent(CAT_NAME)))[0]
console.log('카테고리', cat ? '이미 있음 ' + cat.id : '없음(만들 예정)')
if (WRITE) {
  if (problems) { console.log('중단: 문제가 있어 등록하지 않음'); process.exit(1) }
  if (!cat) { await rest('ivs_robot_categories', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: CAT_NAME, volumes: 4, subject: 'robot', description: null, createdAt: Date.now() } }) }); cat = (await rest('ivs_robot_categories?select=id,data&data->>name=eq.' + encodeURIComponent(CAT_NAME)))[0]; console.log('→ 카테고리 등록', cat.id) }
  const have = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat.id}`)
  if (have.length) { console.log('중단: 이 카테고리에 이미 부품이 있음', have.length); process.exit(1) }
  const rows = [...maxQty].map(([name, o]) => ({ data: { name, icon: '', subject: 'robot', category: cat.id, volumes: [1, 2, 3, 4].filter((v) => o[v]).map((v) => ({ volume: v, qty: o[v] })), color: null, size: null, createdAt: Date.now() } }))
  await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(rows) })
  console.log('→ 부품 등록', rows.length)
  const parts = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat.id}`)
  const idOf = new Map(parts.map((r) => [r.data.name, r.id]))
  const exist = await rest(`ivs_textbooks?select=id,data->>volume&data->>category=eq.${cat.id}`)
  for (const vol of [1, 2, 3, 4]) {
    if (exist.some((e) => +e.volume === vol)) { console.log(vol + '권 교재는 이미 있어 건너뜀'); continue }
    const { titles, chapters } = byVol[vol]
    const ch = [{ id: `ch_pe${vol}_00`, files: [], parts: [], title: '준비', fileUrl: null, fileName: null }]
    titles.forEach((title, i) => ch.push({ id: `ch_pe${vol}_${String(i + 1).padStart(2, '0')}`, files: [], parts: [...chapters[i]].map(([n, q]) => ({ partId: idOf.get(n), qty: q })), title, fileUrl: null, fileName: null }))
    await rest('ivs_textbooks', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: `프로보 익사이팅${vol}단계`, files: urls[vol] ? [urls[vol]] : [], volume: vol, subject: 'robot', category: cat.id, chapters: ch, createdAt: Date.now() + vol } }) })
    console.log(`→ 교재 등록 프로보 익사이팅${vol}단계 차시 ${ch.length} PDF ${urls[vol] ? 1 : 0}`)
  }
}
