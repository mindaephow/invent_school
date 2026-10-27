// 에이스랩 바퀴 = 휠(80164f14) + 타이어(3dc516eb) 합친 부품(사용자 2026-10-27 "에이스랩에 바퀴 추가해줘, 타이어랑 휠을 합친 거"). 두 부품은 같은 축(y)·같은 높이(0~10)에서 만든 것이라 위치 이동 없이 3D 모양을 그대로 합친다. 새 행(이름 '바퀴')을 만든다.
//   node scripts/make-robotron-wheelset.mjs [--write]
import fs from 'node:fs'
const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method === 'POST' ? r.json() : opt.method ? null : r.json() }
const ACE = 'cf342cca-792f-4e70-863b-b12de631f1cc'
const [wheel] = await rest('ivs_part_catalog?select=id,data&id=eq.80164f14-68a3-438f-978c-6ff37c935c5f'), [tire] = await rest('ivs_part_catalog?select=id,data&id=eq.3dc516eb-8f8a-4527-ab32-bddc0c484e7b')
const have = await rest(`ivs_part_catalog?select=id&data->>category=eq.${ACE}&data->>name=eq.${encodeURIComponent('바퀴')}`)
console.log('휠 도형', wheel.data.spec.shapes.length, '타이어 도형', tire.data.spec.shapes.length, '휠 수량', JSON.stringify(wheel.data.volumes), '이미 있는 바퀴 행', have.length)
const shapes = [...wheel.data.spec.shapes.map((s) => ({ ...s, fileName: '바퀴_' + s.fileName })), ...tire.data.spec.shapes.map((s) => ({ ...s, fileName: '바퀴_' + s.fileName, paint: true }))] // 뷰어는 paint 아닌 조각만 합쳐(CSG) 한 가지 색으로 그리고, paint 조각은 자기 색으로 얹는다 → 타이어는 paint 로 둬야 색(검정)이 따로 나오고 휠과 맞닿은 면을 합치다 깨지지 않는다
const connectors = { ...wheel.data.connectors, note: '바퀴(휠 + 타이어 합침). 바깥 지름 56·두께 10. 휠: ' + wheel.data.connectors.note + ' 타이어: ' + tire.data.connectors.note, size: [56, 10, 56], confidence: 'draft' }
const data = { name: '바퀴', size: `Ø56×10mm (에이스랩: 휠 Ø50 + 타이어 Ø56 합침. 휠: ${wheel.data.size} / 타이어: ${tire.data.size})`, color: '그레이', subject: 'robot', volumes: [], category: ACE, createdAt: Date.now(), spec: { shapes }, connectors, primary_image: 'front' }
console.log('도형', shapes.length, 'KB', Math.round(JSON.stringify(data).length / 1024))
if (WRITE) {
  if (have.length) { await rest('ivs_part_catalog?id=eq.' + have[0].id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data: { ...data, createdAt: undefined, volumes: (await rest('ivs_part_catalog?select=data&id=eq.' + have[0].id))[0].data.volumes } }) }); console.log('  → 갱신', have[0].id) }
  else { const r = await rest('ivs_part_catalog', { method: 'POST', headers: { ...H, Prefer: 'return=representation' }, body: JSON.stringify({ data }) }); console.log('  → 새 행', r[0].id) }
}
