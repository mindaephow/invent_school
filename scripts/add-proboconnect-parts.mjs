// 프로보 커넥트(커넥트 LV1~4) 부품리스트를 부품 DB 에 등록한다(사용자 2026-10-27 "로봇에 커넥트 추가, 부품리스트 보고 리스트 추가해줘").
// 출처: 교재 단계별 "부품수량확인" 쪽(1단계 = 프로보커넥트/LV1_커넥트_표지_5판1쇄_부품수량_페이지.pdf, 2~4단계 = connetLv2~4_부품리스트.jpg). 단계 = 권, 수량은 그 단계에서 새로 받는 개수(누적 목록과 맞는지 아래에서 검사한다).
//   node scripts/add-proboconnect-parts.mjs [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b' // 프로보 커넥트
const S = {
  1: { 스위치블럭: 1, 모터블럭: 2, '3핀롱케이블': 1, 모터케이블: 2, '1X3블럭': 6, '1X5블럭': 8, '1X7블럭': 4, '1X9블럭': 4, '2X5블럭': 4, '2X7블럭': 4, '2X9블럭': 4, '3X3블럭': 4, '3X5블럭': 5, '3X7블럭': 4, '3X9블럭': 4, '5X7블럭': 2, 'L2X2블럭': 4, 'L2X4블럭': 4, 'L6X9블럭': 2, 고무줄: 4, 눈블럭: 2, 배터리블럭: 1, 스페이서블럭: 4, 슬라이드블럭: 2, 실: 1, 엣지블럭: 4, 원형블럭: 4, 핀툴: 1, 타이어: 2, 휠블럭: 2, 힌지블럭A: 12, 힌지블럭B: 2, '2단핀': 75, '3단핀': 15, 듀얼핀: 20, 링크핀: 25, 스텝핀: 10, 부품통: 1 },
  2: { CPU블럭: 1, 'LED블럭 레드': 2, 'LED블럭 블루': 2, 스위치블럭: 3, 적외선블럭: 2, FND블럭: 1, 전원케이블: 1, '3핀케이블': 9, '1X3블럭': 5, '1X5블럭': 2, '1X7블럭': 2, '1X9블럭': 2, '2X5블럭': 2, '2X7블럭': 2, '2X9블럭': 2, '2X11블럭': 4, '3X3블럭': 2, '3X5블럭': 2, '3X7블럭': 2, '3X9블럭': 2, '5X7블럭': 2, '7X11블럭': 1, 'L1X3블럭': 4, 'L2X2블럭': 4, 'L2X4블럭': 2, 'L6X9블럭': 2, 변환블럭: 2, 삼각블럭: 2, 아치블럭: 4, 엣지블럭: 4, 힌지블럭A: 4, '2단핀': 40, '3단핀': 30, 듀얼핀: 20, 스텝핀: 10, '고무줄 레드': 6, '스티로폼 공': 1 },
  3: { 'RF 리모컨': 1, 'RF 수신모듈': 1, 'RF 수신모듈커버': 1, 배터리블럭: 1, 서보모터블럭: 1, 전원케이블: 1, 휠블럭: 2, 타이어: 2, 'L2X4블럭': 6, 'L6X9블럭': 6, '1X7블럭': 2, '1X9블럭': 2, '2X5블럭': 6, '2X7블럭': 6, '3X3블럭': 2, '3X5블럭': 2, '3X7블럭': 2, '3X9블럭': 2, '5X7블럭': 2, '7X11블럭': 1, 스페이서블럭: 2, 삼각블럭: 4, '2단핀': 10, '3단핀': 10, 듀얼핀: 10, 링크핀: 10, 스텝핀: 10 },
  4: { 고속모터블럭: 2, 서보모터블럭: 1, 모터케이블: 2, '1X7블럭': 2, '2X11블럭': 6, '7X11블럭': 1, 삼각블럭: 2, 아치블럭: 4, 원형블럭: 4, 톱니블럭: 6, 캐터필러: 100, 캐터고무: 50, '고무줄 레드': 4, '2단핀': 20, '3단핀': 10, 듀얼핀: 10, 링크핀: 10, 스텝핀: 10 },
}
// 교재의 누적 목록("1+2단계", "1+2+3단계 부품 리스트")과 맞는지 검사 — 어긋나면 옮겨 적은 값이 틀린 것이다.
const CUM12 = { CPU블럭: 1, 배터리블럭: 1, 'LED블럭 레드': 2, 'LED블럭 블루': 2, 스위치블럭: 4, 적외선블럭: 2, FND블럭: 1, 모터블럭: 2, '3핀롱케이블': 1, 모터케이블: 2, 전원케이블: 1, '3핀케이블': 9, 실: 1, '1X3블럭': 11, '1X5블럭': 10, '1X7블럭': 6, '1X9블럭': 6, '2X5블럭': 6, '2X7블럭': 6, '2X9블럭': 6, '2X11블럭': 4, '3X3블럭': 6, '3X5블럭': 7, '3X7블럭': 6, '3X9블럭': 6, '5X7블럭': 4, '7X11블럭': 1, 'L1X3블럭': 4, 'L2X2블럭': 8, 'L2X4블럭': 6, 'L6X9블럭': 4, 변환블럭: 2, 삼각블럭: 2, 스페이서블럭: 4, 슬라이드블럭: 2, 아치블럭: 4, 엣지블럭: 8, 힌지블럭A: 16, 힌지블럭B: 2, 원형블럭: 4, 고무줄: 4, '고무줄 레드': 6, '스티로폼 공': 1, 눈블럭: 2, 휠블럭: 2, 타이어: 2, '2단핀': 115, '3단핀': 45, 듀얼핀: 40, 링크핀: 25, 스텝핀: 20, 핀툴: 1 }
const CUM123 = { ...CUM12, 배터리블럭: 2, 서보모터블럭: 1, 전원케이블: 2, '1X7블럭': 8, '1X9블럭': 8, '2X5블럭': 12, '2X7블럭': 12, '3X3블럭': 8, '3X5블럭': 9, '3X7블럭': 8, '3X9블럭': 8, '5X7블럭': 6, '7X11블럭': 2, 'L2X4블럭': 12, 'L6X9블럭': 10, 삼각블럭: 6, 스페이서블럭: 6, 휠블럭: 4, 타이어: 4, '2단핀': 125, '3단핀': 55, 듀얼핀: 50, 링크핀: 35, 스텝핀: 30, 'RF 리모컨': 1, 'RF 수신모듈': 1, 'RF 수신모듈커버': 1 }
const sum = (n) => { const o = {}; for (let v = 1; v <= n; v++) for (const [k, q] of Object.entries(S[v])) o[k] = (o[k] || 0) + q; return o }
let bad = 0
for (const [label, cum, n] of [['1+2단계', CUM12, 2], ['1+2+3단계', CUM123, 3]]) { const got = sum(n); delete got.부품통
  for (const k of new Set([...Object.keys(cum), ...Object.keys(got)])) if ((cum[k] || 0) !== (got[k] || 0)) { bad++; console.log('불일치', label, k, '교재 누적', cum[k] || 0, '합계', got[k] || 0) } }
console.log(bad ? `누적 불일치 ${bad}건` : '누적 목록과 모두 일치(1+2, 1+2+3단계)')
const names = [...new Set(Object.values(S).flatMap((o) => Object.keys(o)))]
const rows = names.map((name) => ({ name, volumes: [1, 2, 3, 4].filter((v) => S[v][name]).map((v) => ({ volume: v, qty: S[v][name] })) }))
console.log('부품 종류', rows.length, '권별 종류', [1, 2, 3, 4].map((v) => v + '권 ' + Object.keys(S[v]).length).join(', '))
const exist = await rest(`ivs_part_catalog?select=id,data->>name&data->>category=eq.${CAT}`)
console.log('이미 등록된 부품', exist.length)
if (WRITE) {
  if (exist.length) { console.log('중복 방지: 이미 부품이 있어 중단'); process.exit(1) }
  const body = rows.map((r) => ({ data: { name: r.name, icon: '', subject: 'robot', category: CAT, volumes: r.volumes, color: null, size: null, createdAt: Date.now() } }))
  await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(body) })
  console.log('→ 등록', body.length, '개')
}
