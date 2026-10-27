// 프로보 커넥트 1~4권(1~4단계) 교재 행을 만들고 PDF·차시(0차시 준비 + 회차별 조립명)·차시별 필요 부품을 등록한다(사용자 2026-10-27 "커넥트 1~4권 pdf파일 먼저 등록 / 0차시는 준비 / 1차시~ 회차별 조립명 등록 / 회차별 필요부품리스트 등록").
// 입력: upload-proboconnect-pdfs.mjs 가 남긴 URL JSON, parse-proboconnect-chapters.py 가 뽑은 차시별 부품 JSON(쪽 순서 = 차례 순서).
//   node scripts/add-proboconnect-textbooks-1-4.mjs <urls.json> <parsed.json> [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const [URLS, PARSED] = process.argv.filter((a) => a.endsWith('.json'))
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b'
const urls = JSON.parse(fs.readFileSync(URLS, 'utf8')), parsed = JSON.parse(fs.readFileSync(PARSED, 'utf8'))
// 차례(교재 각 쪽 4 의 목차) — 마지막 "나만의 창작로봇"은 부품 목록이 없다.
const TITLES = {
  1: ['아기돼지 도니', '아기새로봇 버디', '물개로봇 토토', '토끼로봇 로빗', '원숭이로봇 우키', '개구리로봇 크록', '강아지로봇 몽이', '배틀로봇 어퍼', '보행로봇 워로우', '땅굴로봇 터보', '거미로봇 타란튤', '공룡로봇 티라'],
  2: ['기억력게임 탭탭', '접시쌓기게임 웨이터리', 'CPR실습로봇 피아르', '비행기게임 점핑에어', '가위바위보 위너', '팔씨름게임 쉐이크스틱', '외계인사격 레이저건', '하마게임 하몽', '역도게임 라차차', '스피드터치 해머샷', '테이블농구 슈터', '나만의 창작로봇'],
  3: ['개미로봇 앤보', '청소로봇 워시', '경찰바이크 싸이카', '투석기로봇 던저', '배틀로봇 러쉬', '펜싱로봇 스피어', '4륜구동 터프', '복싱로봇 어택', '탐사머신 탐머', '익룡로봇 꺄오기', '미사일발사 슈크', '나만의 창작로봇'],
  4: ['F1자동차 스피온', '서스펜션카 락크', '버킷굴착기 블라스터', '바이크로봇 스톰', '탱크로봇 CT-1', '스마트 모빌리티 몰리', '공룡로봇 알로', '운반로봇 딜리', '지게차로봇 포리', '굴착기로봇 카베이터', '폐기물처리로봇 로이', '나만의 창작로봇'],
}
const parts = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CAT}`)
const idOf = new Map(parts.map((r) => [r.data.name, r.id]))
const cumQty = (vol) => { const m = new Map(); parts.forEach((r) => { let t = 0; (r.data.volumes || []).forEach((e) => { if (e.volume <= vol) t += e.qty }); m.set(r.data.name, t) }); return m }
let problems = 0
const books = []
for (const vol of [1, 2, 3, 4]) {
  const titles = TITLES[vol], lists = parsed[String(vol)], cum = cumQty(vol)
  const chapters = [{ id: `ch_pc${vol}_00`, files: [], parts: [], title: '준비', fileUrl: null, fileName: null }]
  titles.forEach((title, i) => {
    const items = lists[i] ? lists[i].items : []
    const merged = new Map(); items.forEach(([n0, q]) => { const n = n0 === '바퀴블럭' ? '휠블럭' : n0; merged.set(n, (merged.get(n) || 0) + q) }) // 교재 차시 쪽의 '바퀴블럭' = 키트 목록의 '휠블럭'
    const ps = []
    for (const [name, qty] of merged) {
      if (!idOf.has(name)) { problems++; console.log(`  ${vol}권 ${i + 1}차시 부품 DB 에 없음:`, name, qty); continue }
      if (qty > (cum.get(name) || 0)) console.log(`  (경고) ${vol}권 ${i + 1}차시 ${name} ${qty} > 1~${vol}단계 키트 누적 ${cum.get(name) || 0} — 교재 차시 쪽에 적힌 수량 그대로 등록`)
      ps.push({ partId: idOf.get(name), qty })
    }
    if (title !== '나만의 창작로봇' && !ps.length) { problems++; console.log(`  ${vol}권 ${i + 1}차시 ${title}: 부품을 못 읽음`) }
    chapters.push({ id: `ch_pc${vol}_${String(i + 1).padStart(2, '0')}`, files: [], parts: ps, title, fileUrl: null, fileName: null })
  })
  console.log(`${vol}권: 차시 ${chapters.length}개(0차시 준비 + ${titles.length}), 차시별 부품 종류`, chapters.map((c) => c.parts.length).join(','))
  books.push({ vol, name: `프로보 커넥트${vol}단계`, files: urls[vol] ? [urls[vol]] : [], chapters })
}
console.log('문제', problems, '건')
const exist = await rest(`ivs_textbooks?select=id,data->>volume&data->>category=eq.${CAT}`)
console.log('이미 등록된 프로보 커넥트 교재 권', exist.map((e) => e.volume).join(','))
if (WRITE) {
  if (problems) { console.log('중단: 문제가 있어 등록하지 않음'); process.exit(1) }
  for (const b of books) {
    if (exist.some((e) => +e.volume === b.vol)) { console.log(b.vol + '권은 이미 있어 건너뜀'); continue }
    await rest('ivs_textbooks', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: b.name, files: b.files, volume: b.vol, subject: 'robot', category: CAT, chapters: b.chapters, createdAt: Date.now() + b.vol } }) })
    console.log('→ 교재 등록', b.name, 'PDF', b.files.length)
  }
}
