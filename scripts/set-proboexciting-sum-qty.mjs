// 프로보 익사이팅 각 권 부품 수량을 그 권 모든 차시 필요 수량의 합으로 바꾼다(사용자 2026-10-27 "너 한권에 필요한거 계산해서 구할수있으면서 귀찮다고 자꾸 꼼수 피울래?"). 이전 값은 차시 최대 수량이었다.
//   node scripts/set-proboexciting-sum-qty.mjs [--write]
import fs from 'node:fs'
const WRITE = process.argv.includes('--write'), MODE = process.argv.includes('--sum') ? 'sum' : 'max' // 기본은 차시 최대 수량(한 권에 실제로 필요한 키트 수량), --sum 은 차시 합계
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CAT = (await rest('ivs_robot_categories?select=id&data->>name=eq.' + encodeURIComponent('프로보 익사이팅')))[0].id
const parts = await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${CAT}`), books = await rest(`ivs_textbooks?select=id,data&data->>category=eq.${CAT}`)
const sum = new Map() // partId → {vol: 합}
for (const b of books) for (const c of b.data.chapters || []) for (const p of c.parts || []) { const o = sum.get(p.partId) || {}; o[b.data.volume] = MODE === 'sum' ? (o[b.data.volume] || 0) + p.qty : Math.max(o[b.data.volume] || 0, p.qty); sum.set(p.partId, o) }
let changed = 0
for (const r of parts) {
  const o = sum.get(r.id) || {}, vols = [1, 2, 3, 4].filter((v) => o[v]).map((v) => ({ volume: v, qty: o[v] }))
  if (JSON.stringify(vols) === JSON.stringify(r.data.volumes)) continue
  changed++
  if (['2단핀', '3X5블럭', 'CPU블럭', '모터케이블', '충전배터리블럭'].includes(r.data.name)) console.log(r.data.name.padEnd(10), '이전', JSON.stringify(r.data.volumes.map((e) => e.volume + '권:' + e.qty)), '→', MODE, JSON.stringify(vols.map((e) => e.volume + '권:' + e.qty)))
  if (WRITE) await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { ...r.data, volumes: vols } }) })
}
console.log('수량이 바뀌는 부품', changed, '/', parts.length)
