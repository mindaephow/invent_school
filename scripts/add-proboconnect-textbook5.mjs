// 프로보 커넥트 5권(5단계) 교재 행을 만들고 차시를 등록한다: 0차시 = 준비, 1차시부터 교재 차례(CHAPTER 01~11) 순서, 차시마다 그 쪽의 "필요한 부품 리스트"를 적는다(사용자 2026-10-27 "5권에서 0차시는 준비로 하고 1차시부터 등록한다음 차시별로 부품을 적어놔").
// 출처: 프로보커넥트/커넥트 5권_231229.pdf — 차례(2~3쪽)와 각 챕터 첫 쪽 뒤의 "필요한 부품 리스트"(7·17·27·37·49·61·77·93·107·121·135쪽).
//   node scripts/add-proboconnect-textbook5.mjs [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b', VOL = 5, NAME = '프로보 커넥트5단계'
// 교재 표기 → 부품 DB 이름
const ALIAS = { '충전 배터리블럭': '충전배터리블럭', '스프링 스위치블럭': '스프링스위치블럭', 'LED 블럭 레드': 'LED블럭 레드', 'LED 블럭 블루': 'LED블럭 블루', '적외선블럭(IR)': '적외선블럭', '모터케이블(2-PIN)': '모터케이블', 캐터타이어: '캐터고무', '45D블럭': '큰삼각블럭' }
const P = (s) => s.split(',').map((x) => x.trim()).filter(Boolean).map((x) => { const m = x.match(/^(.*\S)\s+(\d+)$/); return [ALIAS[m[1]] || m[1], +m[2]] })
const CH = [
  ['참참참', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 4, FND블럭 1, 서보모터블럭 2, 전원케이블 2, 3핀케이블 9, 1X5블럭 5, 2X5블럭 1, 2X11블럭 2, 3X5블럭 1, 3X7블럭 2, 3X9블럭 1, 5X7블럭 2, 7X11블럭 2, L2X2블럭 1, L6X9블럭 7, 변환블럭 1, 아치블럭 1, 힌지블럭A 1, 힌지블럭B 1, 눈블럭 2, 2단핀 62, 듀얼핀 9, 스텝핀 7'],
  ['왓타임', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 2, FND블럭 1, 서보모터블럭 2, 전원케이블 2, 3핀케이블 7, 캐터타이어 2, 1X3블럭 2, 1X7블럭 2, 2X5블럭 1, 3X5블럭 2, 3X9블럭 4, 7X11블럭 3, L2X4블럭 4, L6X9블럭 4, 아치블럭 6, 원형블럭 4, 2단핀 72, 3단핀 4, 듀얼핀 4'],
  ['스틱 붕붕이', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 2, 적외선블럭(IR) 2, FND블럭 1, 모터블럭 1, 모터케이블(2-PIN) 1, 전원케이블 2, 3핀케이블 7, 1X5블럭 4, 1X7블럭 4, 1X9블럭 2, 3X3블럭 2, 3X5블럭 1, 3X9블럭 4, 7X11블럭 2, L2X4블럭 5, L6X9블럭 8, 변환블럭 1, 2단핀 64, 3단핀 10, 듀얼핀 10'],
  ['제로 캐치', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 2, FND블럭 1, 서보모터블럭 1, 전원케이블 2, 3핀케이블 6, 1X3블럭 2, 3X3블럭 1, 3X5블럭 8, 3X7블럭 4, 3X9블럭 2, 5X7블럭 4, 7X11블럭 2, L2X4블럭 2, L6X9블럭 8, 힌지블럭A 12, 변환블럭 1, 폼핀 4, 고무줄 레드 2, 2단핀 76, 3단핀 10, 듀얼핀 14, 링크핀 4, 스텝핀 2'],
  ['롱 트랙볼', 'CPU블럭 1, 충전 배터리블럭 2, 스프링 스위치블럭 2, 적외선블럭(IR) 2, FND블럭 1, 모터블럭 2, 모터케이블(2-PIN) 2, 전원케이블 2, 3핀케이블 5, 1X3블럭 4, 1X5블럭 2, 1X7블럭 4, 1X9블럭 2, 2X11블럭 9, 3X9블럭 2, 5X7블럭 2, 7X11블럭 3, L2X2블럭 2, L2X4블럭 2, L6X9블럭 3, 변환블럭 1, 아치블럭 8, 원형블럭 2, 스티로폼 공 1, 2단핀 70, 3단핀 30, 듀얼핀 7, 스텝핀 6'],
  ['무.꽃.피', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 2, 적외선블럭(IR) 2, 모터블럭 2, 서보모터블럭 1, 모터케이블(2-PIN) 2, 전원케이블 2, 3핀케이블 7, 톱니블럭 2, 1X3블럭 3, 1X5블럭 4, 1X9블럭 6, 2X7블럭 1, 2X11블럭 8, 3X3블럭 4, 3X5블럭 8, 3X9블럭 1, 7X11블럭 1, L1X3블럭 2, L2X2블럭 5, L2X4블럭 5, L6X9블럭 7, 변환블럭 1, 스페이서블럭 4, 아치블럭 2, 원형블럭 4, 힌지블럭A 2, 눈블럭 2, 2단핀 100, 3단핀 29, 듀얼핀 12'],
  ['손가락 펀치', 'CPU블럭 1, 충전 배터리블럭 2, 적외선블럭(IR) 2, FND블럭 1, 서보모터블럭 2, 전원케이블 2, 3핀케이블 5, 캐터타이어 4, 1X3블럭 6, 1X5블럭 1, 1X9블럭 1, 2X5블럭 4, 2X7블럭 1, 2X9블럭 3, 2X11블럭 2, 3X3블럭 7, 3X5블럭 1, 3X9블럭 5, 5X7블럭 1, 7X11블럭 1, L1X3블럭 4, L2X2블럭 6, L2X4블럭 5, 삼각블럭 1, 45D블럭 2, 엣지블럭 2, 원형블럭 5, 아치블럭 4, 2단핀 107, 3단핀 25, 듀얼핀 12, 스텝핀 1, 폼핀 4'],
  ['틈새 게임', 'CPU블럭 1, 충전 배터리블럭 2, 스프링 스위치블럭 1, 적외선블럭(IR) 3, FND블럭 1, 모터블럭 1, 서보모터블럭 1, 모터케이블(2-PIN) 1, 전원케이블 2, 3핀케이블 6, 톱니블럭 2, 캐터필러 72, 1X3블럭 1, 1X5블럭 4, 1X7블럭 2, 1X9블럭 6, 2X5블럭 3, 2X7블럭 2, 3X3블럭 6, 3X5블럭 5, 3X7블럭 1, 3X9블럭 16, L2X2블럭 6, L2X4블럭 1, L6X9블럭 4, 삼각블럭 1, 2단핀 124, 3단핀 36, 듀얼핀 16, 링크핀 2, 스텝핀 1'],
  ['줄넘기', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 4, 모터블럭 1, 서보모터블럭 2, 모터케이블(2-PIN) 1, 전원케이블 2, 3핀케이블 8, 1X3블럭 4, 1X7블럭 10, 2X5블럭 2, 2X9블럭 4, 2X11블럭 2, 3X3블럭 6, 3X5블럭 12, 3X9블럭 2, 5X7블럭 2, 7X11블럭 3, L1X3블럭 6, L2X4블럭 10, L6X9블럭 4, 변환블럭 4, 스페이서블럭 2, 원형블럭 2, 2단핀 140, 3단핀 26, 듀얼핀 8, 링크핀 12'],
  ['스피드 클라이밍', 'CPU블럭 1, 충전 배터리블럭 2, LED 블럭 레드 1, LED 블럭 블루 1, 스프링 스위치블럭 4, 적외선블럭(IR) 2, 모터블럭 2, 서보모터블럭 2, 모터케이블(2-PIN) 2, 전원케이블 2, 3핀케이블 8, 톱니블럭 4, 캐터필러 92, 1X3블럭 10, 1X5블럭 6, 1X9블럭 4, 2X7블럭 1, 2X11블럭 9, 3X3블럭 1, 3X7블럭 2, 3X9블럭 12, 5X7블럭 2, 7X11블럭 1, L2X2블럭 4, L6X9블럭 5, 변환블럭 6, 원형블럭 4, 2단핀 120, 3단핀 18, 듀얼핀 16, 링크핀 44'],
  ['스캔 드로잉', 'CPU블럭 1, 충전 배터리블럭 2, 스프링 스위치블럭 3, 적외선블럭(IR) 1, 모터블럭 2, 서보모터블럭 1, 모터케이블(2-PIN) 2, 전원케이블 2, 3핀케이블 5, 1X3블럭 11, 1X5블럭 3, 1X7블럭 1, 2X5블럭 4, 2X7블럭 3, 2X9블럭 1, 2X11블럭 5, 3X3블럭 3, 3X5블럭 4, 3X7블럭 3, 3X9블럭 7, 5X7블럭 3, 7X11블럭 1, L1X3블럭 2, L2X2블럭 9, L2X4블럭 7, L6X9블럭 4, 스페이서블럭 5, 원형블럭 8, 고무링 블랙 4, 2단핀 122, 3단핀 31, 듀얼핀 4, 링크핀 13'],
]
const parts = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CAT}`)
const idOf = new Map(parts.map((r) => [r.data.name, r.id]))
const qty5 = new Map(); parts.forEach((r) => { let t = 0; (r.data.volumes || []).forEach((e) => { if (e.volume <= 5) t += e.qty }); qty5.set(r.data.name, t) }) // 1~5권 키트 누적 수량
let missing = 0, over = 0
const chapters = [{ id: 'ch_pc5_00', files: [], parts: [], title: '준비', fileUrl: null, fileName: null }]
CH.forEach(([title, list], i) => {
  const ps = P(list).map(([name, qty]) => { if (!idOf.has(name)) { missing++; console.log('부품 DB 에 없음:', i + 1 + '차시', name); return null }
    if (qty > qty5.get(name)) { over++; console.log('키트 수량보다 많음:', i + 1 + '차시', name, qty, '> 1~5권 누적', qty5.get(name)) }
    return { partId: idOf.get(name), qty } }).filter(Boolean)
  chapters.push({ id: 'ch_pc5_' + String(i + 1).padStart(2, '0'), files: [], parts: ps, title, fileUrl: null, fileName: null })
})
console.log('차시', chapters.length, '(0차시 준비 + 1~' + CH.length + '차시)', '차시별 부품 종류', chapters.map((c) => c.parts.length).join(','), '| DB 에 없는 부품', missing, '| 키트 수량 초과', over)
const exist = await rest(`ivs_textbooks?select=id&data->>category=eq.${CAT}&data->>volume=eq.${VOL}`)
console.log('이미 등록된 교재', exist.length)
if (WRITE) {
  if (missing || exist.length) { console.log('중단: 없는 부품이 있거나 이미 교재가 있음'); process.exit(1) }
  await rest('ivs_textbooks', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { name: NAME, files: [], volume: VOL, subject: 'robot', category: CAT, chapters, createdAt: Date.now() } }) })
  console.log('→ 교재 등록', NAME)
}
