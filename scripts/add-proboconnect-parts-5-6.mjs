// 프로보 커넥트 5·6단계(권) 부품을 부품 DB 에 추가한다(사용자 2026-10-27, 근거: 프로보커넥트/★20240905_커넥트_Lv6_저용량.pdf 의 "6단계 부품 수량 확인"·"1~5단계 부품 리스트"·"1~6단계 수량 확인").
// 6단계 = 그 쪽의 6단계 수량, 5단계 = (1~5단계 누적) − (이미 등록된 1~4단계 합). 두 누적 목록과 6단계 쪽이 서로 맞는지 검사한다.
//   node scripts/add-proboconnect-parts-5-6.mjs [--write]
import fs from 'node:fs'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = 'ebef9f3b-69b0-4a4f-9039-bfc81c6e678b' // 프로보 커넥트
// 교재 이름 → 이미 등록한 3·4단계 이름(같은 부품): 수신보드/수신커버, 캐터타이어
const ALIAS = { 'RF 수신보드': 'RF 수신모듈', 'RF 수신커버': 'RF 수신모듈커버', 캐터타이어: '캐터고무', '배터리블럭(건전지용)': '배터리블럭' }
const al = (o) => Object.fromEntries(Object.entries(o).map(([k, v]) => [ALIAS[k] || k, v]))
const S6 = al({ 확장입력블럭: 1, 자석센서블럭: 2, 터치블럭레드: 4, 터치블럭블루: 4, 회전센서블럭: 2, 무한회전센서블럭: 1, '3핀케이블': 4, 터치케이블: 8, '1X3블럭': 3, '1X5블럭': 5, '1X7블럭': 5, '1X9블럭': 2, '2X9블럭': 2, '2X11블럭': 10, '3X3블럭': 6, '3X7블럭': 6, 'L1X3블럭': 14, 'L6X9블럭': 4, 스페이서블럭: 2, '2단핀': 15, 폼핀: 10, 링자석: 9, '고무줄 레드': 1, '고무링 블랙': 2 })
const CUM15 = al({ CPU블럭: 1, 'RF 수신보드': 1, 'RF 수신커버': 1, 'RF 리모컨': 1, 배터리블럭: 2, 충전배터리블럭: 2, 'LED블럭 레드': 2, 'LED블럭 블루': 2, 스위치블럭: 4, 스프링스위치블럭: 4, 적외선블럭: 3, FND블럭: 1, 모터블럭: 2, 서보모터블럭: 2, 고속모터블럭: 2, '3핀롱케이블': 1, 모터케이블: 4,
  전원케이블: 2, '3핀케이블': 9, 톱니블럭: 6, 캐터필러: 100, 캐터타이어: 50, '1X3블럭': 11, '1X5블럭': 10, '1X7블럭': 10, '1X9블럭': 8, '2X5블럭': 12, '2X7블럭': 12, '2X9블럭': 6, '2X11블럭': 10, '3X3블럭': 8, '3X5블럭': 12, '3X7블럭': 8, '3X9블럭': 16,
  '5X7블럭': 6, '7X11블럭': 4, 슬라이드블럭: 2, 'L1X3블럭': 6, 'L2X2블럭': 12, 'L2X4블럭': 12, 'L6X9블럭': 10, 변환블럭: 6, 삼각블럭: 8, 큰삼각블럭: 2, 스페이서블럭: 8, 아치블럭: 8, 엣지블럭: 8, 원형블럭: 8, 힌지블럭A: 16, 힌지블럭B: 2, '2단핀': 165,
  '3단핀': 65, 듀얼핀: 60, 링크핀: 55, 스텝핀: 40, 폼핀: 5, 고무줄: 4, '고무줄 레드': 10, '고무링 블랙': 5, '스티로폼 공': 2, 눈블럭: 2, 실: 1, 휠블럭: 4, 타이어: 4, 핀툴: 2, 부품통: 2, 충전기: 1, 'USB-C 케이블': 2 })
const CUM16 = al({ CPU블럭: 1, 'RF 수신보드': 1, 'RF 수신커버': 1, 'RF 리모컨': 1, '배터리블럭(건전지용)': 2, 충전배터리블럭: 2, 확장입력블럭: 1, 자석센서블럭: 2, 'LED블럭 레드': 2, 'LED블럭 블루': 2, 스위치블럭: 4, 스프링스위치블럭: 4, 적외선블럭: 3, 터치블럭레드: 4, 터치블럭블루: 4, FND블럭: 1, 모터블럭: 2, 서보모터블럭: 2, 고속모터블럭: 2, 회전센서블럭: 2, 무한회전센서블럭: 1, '3핀롱케이블': 1, 모터케이블: 4, 전원케이블: 2, '3핀케이블': 13, 터치케이블: 8,
  톱니블럭: 6, 캐터필러: 100, 캐터타이어: 50, '1X3블럭': 14, '1X5블럭': 15, '1X7블럭': 15, '1X9블럭': 10, '2X5블럭': 12, '2X7블럭': 12, '2X9블럭': 8, '2X11블럭': 20, '3X3블럭': 14, '3X5블럭': 12, '3X7블럭': 14, '3X9블럭': 16, '5X7블럭': 6, '7X11블럭': 4, 슬라이드블럭: 2, 'L1X3블럭': 20, 'L2X2블럭': 12, 'L2X4블럭': 12, 'L6X9블럭': 14, 변환블럭: 6, 삼각블럭: 8, 큰삼각블럭: 2, 스페이서블럭: 10,
  아치블럭: 8, 엣지블럭: 8, 원형블럭: 8, 힌지블럭A: 16, 힌지블럭B: 2, '2단핀': 180, '3단핀': 65, 듀얼핀: 60, 링크핀: 55, 스텝핀: 40, 폼핀: 15, 링자석: 9, 고무줄: 4, '고무줄 레드': 11, '고무링 블랙': 7, '스티로폼 공': 2, 눈블럭: 2, 실: 1, 휠블럭: 4, 타이어: 4, 핀툴: 2, 부품통: 2, 충전기: 1, 'USB-C 케이블': 2 })
// 이미 등록된 1~4단계 합
const rows = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CAT}`)
const byName = new Map(rows.map((r) => [r.data.name, r]))
const cum14 = {}; rows.forEach((r) => (r.data.volumes || []).forEach((e) => { if (e.volume <= 4) cum14[r.data.name] = (cum14[r.data.name] || 0) + e.qty }))
const S5 = {}; let bad = 0
for (const k of new Set([...Object.keys(CUM15), ...Object.keys(cum14)])) { const d = (CUM15[k] || 0) - (cum14[k] || 0); if (d < 0) { bad++; console.log('5단계 음수(1~4단계가 1~5단계 누적보다 큼)', k, '1~4', cum14[k], '1~5', CUM15[k]) } else if (d > 0) S5[k] = d }
for (const k of new Set([...Object.keys(CUM15), ...Object.keys(S6), ...Object.keys(CUM16)])) { const got = (CUM15[k] || 0) + (S6[k] || 0); if (got !== (CUM16[k] || 0)) { bad++; console.log('1~6단계 불일치', k, '1~5 + 6단계', got, '교재 1~6', CUM16[k] || 0) } }
console.log(bad ? `불일치 ${bad}건 — 옮겨 적은 값 확인 필요` : '1~5단계·6단계·1~6단계 목록이 서로 모두 일치')
console.log('5단계 새로 받는 부품', Object.keys(S5).length, '종 / 6단계', Object.keys(S6).length, '종')
console.log('5단계:', Object.entries(S5).map(([k, v]) => k + '×' + v).join(', '))
console.log('6단계:', Object.entries(S6).map(([k, v]) => k + '×' + v).join(', '))
const newNames = [...new Set([...Object.keys(S5), ...Object.keys(S6)])].filter((k) => !byName.has(k))
console.log('새로 만들 부품 행', newNames.length, newNames.join(', '))
if (WRITE && !bad) {
  const add = (name, volume, qty) => { const r = byName.get(name); const vols = [...(r.data.volumes || []).filter((e) => e.volume !== volume), { volume, qty }].sort((a, b) => a.volume - b.volume); r.data.volumes = vols; r._dirty = true }
  const inserts = []
  for (const [vol, S] of [[5, S5], [6, S6]]) for (const [name, qty] of Object.entries(S)) {
    if (!byName.has(name)) { const row = { data: { name, icon: '', subject: 'robot', category: CAT, volumes: [], color: null, size: null, createdAt: Date.now() } }; inserts.push(row); byName.set(name, row) }
    const r = byName.get(name); r.data.volumes = [...(r.data.volumes || []).filter((e) => e.volume !== vol), { volume: vol, qty }].sort((a, b) => a.volume - b.volume); r._dirty = true
  }
  for (const r of rows) if (r._dirty) await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: r.data }) })
  if (inserts.length) await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify(inserts.map((r) => ({ data: r.data }))) })
  console.log('→ 수정', rows.filter((r) => r._dirty).length, '개 · 새로 등록', inserts.length, '개')
}
