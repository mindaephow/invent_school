// 프로보 커넥트 6권(6단계) 교재를 만들고(PDF·0차시 준비·1~10차시·차시별 필요 부품), 5권 교재에 PDF 를 붙인다(사용자 2026-10-27 "5권6권도 등록~ 용량 너무 크면 적당한 해상도로 줄여서").
// 6권 차례(★20240905_커넥트_Lv6_저용량.pdf 4~5쪽): 균형잡기, 폴짝폴짝 눈치 게임, 뒤집기 게임, 두더지 게임, 스핀 터치, 찌르기 게임, 턴 프레스, LED 트래킹, 자석 사냥, 반사 게임.
//   node scripts/add-proboconnect-textbook6.mjs <urls.json> <lv6.json> [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const [URLS, LV6] = process.argv.filter((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b'
const urls = JSON.parse(fs.readFileSync(URLS, 'utf8')), lv6 = JSON.parse(fs.readFileSync(LV6, 'utf8'))
const TITLES = ['균형잡기', '폴짝폴짝 눈치 게임', '뒤집기 게임', '두더지 게임', '스핀 터치', '찌르기 게임', '턴 프레스', 'LED 트래킹', '자석 사냥', '반사 게임']
const ALIAS = { '충전 배터리블럭': '충전배터리블럭', '스프링 스위치블럭': '스프링스위치블럭', '모터케이블(2-PIN)': '모터케이블', '터치케이블(1-PIN)': '터치케이블', '터치블럭 레드': '터치블럭레드', '터치블럭 블루': '터치블럭블루', 캐터타이어: '캐터고무' }
const parts = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CAT}`)
const idOf = new Map(parts.map((r) => [r.data.name, r.id]))
const cum = new Map(); parts.forEach((r) => { let t = 0; (r.data.volumes || []).forEach((e) => { if (e.volume <= 6) t += e.qty }); cum.set(r.data.name, t) })
let problems = 0
if (lv6.length !== TITLES.length) { problems++; console.log('차시 수와 부품 목록 쪽 수가 다름', TITLES.length, lv6.length) }
const chapters = [{ id: 'ch_pc6_00', files: [], parts: [], title: '준비', fileUrl: null, fileName: null }]
TITLES.forEach((title, i) => {
  const merged = new Map(); (lv6[i]?.items || []).forEach(([n0, q]) => { const n = ALIAS[n0] || n0; merged.set(n, (merged.get(n) || 0) + q) })
  const ps = []
  for (const [name, qty] of merged) {
    if (!idOf.has(name)) { problems++; console.log(`  6권 ${i + 1}차시 부품 DB 에 없음:`, name, qty); continue }
    if (qty > (cum.get(name) || 0)) console.log(`  (경고) 6권 ${i + 1}차시 ${name} ${qty} > 1~6단계 키트 누적 ${cum.get(name) || 0}`)
    ps.push({ partId: idOf.get(name), qty })
  }
  chapters.push({ id: 'ch_pc6_' + String(i + 1).padStart(2, '0'), files: [], parts: ps, title, fileUrl: null, fileName: null })
})
console.log('6권 차시', chapters.length, '(0차시 준비 +', TITLES.length + ')', '차시별 부품 종류', chapters.map((c) => c.parts.length).join(','), '| 문제', problems)
const tbs = await rest(`ivs_textbooks?select=id,data&data->>category=eq.${CAT}`)
const t5 = tbs.find((t) => t.data.volume === 5), t6 = tbs.find((t) => t.data.volume === 6)
console.log('5권 교재', t5 ? '있음' : '없음', '· 6권 교재', t6 ? '이미 있음' : '없음')
if (WRITE) {
  if (problems) { console.log('중단: 문제가 있어 등록하지 않음'); process.exit(1) }
  if (t5 && urls[5] && !(t5.data.files || []).length) { await rest('ivs_textbooks?id=eq.' + t5.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { ...t5.data, files: [urls[5]] } }) }); console.log('→ 5권 교재에 PDF 붙임') }
  if (!t6) { await rest('ivs_textbooks', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: '프로보 커넥트6단계', files: urls[6] ? [urls[6]] : [], volume: 6, subject: 'robot', category: CAT, chapters, createdAt: Date.now() } }) }); console.log('→ 6권 교재 등록') }
}
