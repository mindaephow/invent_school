// get_step_context 를 시험한다(연결점은 conn.json, 조립도는 배포된 사이트 데이터, 부품 목록은 오토건 LIST).   node scripts/assembly-tools/test_step_context.mjs
import fs from 'node:fs'
import { registerCuboAssemblyTools } from '../../app/lib/cubo-assembly-tools.js'
const conn = JSON.parse(fs.readFileSync(new URL('./conn.json', import.meta.url), 'utf8'))
const LIST = { '115프레임': 2, '15프레임': 2, '17프레임': 2, '19프레임': 2, '27프레임': 4, '29프레임': 3, '2단블록': 10, '2열브라켓': 1, '315프레임': 4, '35프레임': 2, '37프레임': 3, '3단블록': 10, '59프레임': 2, 'DC모터': 1, 'T축': 4, '리모컨': 1, '리벳': 14, '메인보드': 1, '부시': 4, '작은기어': 1, '축': 1, '큰기어': 2 }
const tables = {
  ivs_textbooks: [{ data: { subject: 'robot', volume: 1, chapters: [{ title: '오토건', parts: Object.entries(LIST).map(([n, q]) => ({ partId: 'id:' + n, qty: q })) }] } }],
}
const sb = { from: (table) => { const q = { _sel: '', _in: null, select(s) { q._sel = s || ''; return q }, eq() { return q }, in(col, vals) { q._in = vals; return q },
  then(res) {
    if (table === 'ivs_textbooks') return res({ data: tables.ivs_textbooks, error: null })
    const names = q._in || []
    if (q._sel.includes('connectors')) return res({ data: names.filter((n) => conn[n]).map((n) => ({ name: n, connectors: conn[n] })), error: null })
    return res({ data: names.map((id) => ({ id, name: String(id).replace('id:', '') })), error: null })
  } }; return q } }
let handler; registerCuboAssemblyTools({ registerTool: (name, _d, fn) => { if (name === 'get_step_context') handler = fn } }, () => sb)
let fails = 0; const ok = (l, c) => { console.log((c ? '✓ ' : '✗ ') + l); if (!c) fails++ }
const t1 = (await handler({ assemblyId: 'cubo-1-autogun', step: 1 })).content[0].text
ok('1단계: 쓴 부품 없음 + 남은 부품 = 전체 LIST', t1.includes('(없음 — 첫 단계)') && t1.includes('315프레임 4') && t1.includes('리벳 14'))
const t13 = (await handler({ assemblyId: 'cubo-1-autogun', step: 13 })).content[0].text
console.log(t13.split('\n').slice(0, 40).join('\n'))
ok('13단계: 메인보드는 아직 안 썼고 남은 부품에 있다', /남은 부품[^\n]*메인보드 1/.test(t13))
ok('13단계: 315프레임에 빈 구멍 목록이 나온다', t13.includes('315프레임') && t13.includes('빈 '))
ok('13단계 데이터: 새 부품 메인보드 1', t13.includes('새 부품: 메인보드 1'))
ok('13단계 결합: 메인보드 돌기 → 315프레임 홀면 열·줄 이름으로', /메인보드 1번 돌기면[^\n]*→\s+315프레임 \d번 홀면 \+y 열\d+·줄\d+/.test(t13))
const tn = (await handler({ assemblyId: 'cubo-1-autogun', step: 34 })).content[0].text
ok('마지막+1 단계: 아직 없는 새 단계로 본다', tn.includes('아직 조립 데이터에 없음'))
const bad = await handler({ assemblyId: 'cubo-1-autogun', step: 99 }); ok('범위 밖 단계는 오류', bad.isError)
console.log('실패', fails); process.exit(fails ? 1 : 0)
