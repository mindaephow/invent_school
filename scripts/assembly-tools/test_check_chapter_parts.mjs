// check_chapter_parts 도구를 가짜 DB 로 시험한다.   node scripts/assembly-tools/test_check_chapter_parts.mjs
import { registerCuboAssemblyTools } from '../../app/lib/cubo-assembly-tools.js'
const CUBO = '6fa8abd9-7684-47a2-bd7f-2bc9a6e3fbe6'
const tables = {
  ivs_textbooks: [{ id: 'tb', data: { category: CUBO, volume: '1', files: [{ url: 'https://example.com/book.pdf' }], chapters: [
    { title: '오토건', parts: [] },
    { title: '조종형비행기', parts: [{ partId: 'blk', qty: 8 }, { partId: 'deco', qty: 1 }, { partId: 'dc', qty: 2 }, { partId: 'remote', qty: 1 }, { partId: 'gone', qty: 3 }] },
  ] } }],
  ivs_part_catalog: [
    { id: 'blk', name: '3단블록', shape: 'import', connectors: { pegs: [{}, {}], holes: [{}], confidence: 'checked' } },
    { id: 'deco', name: '데코바퀴', shape: 'import', connectors: { pegs: [], holes: [{}], confidence: 'checked' } },
    { id: 'dc', name: 'DC모터', shape: 'import', connectors: { pegs: [{}], holes: [], confidence: 'auto' } },
    { id: 'remote', name: '리모컨', shape: null, connectors: null },
  ],
}
const sb = { from: (table) => { const q = { _t: table, select() { return q }, eq() { return q }, in(_c, ids) { q._ids = ids; return q }, then(res) { const rows = tables[table].filter((r) => !q._ids || q._ids.includes(r.id)); res({ data: rows, error: null }) } }; return q } }
let handler
registerCuboAssemblyTools({ registerTool: (name, _def, fn) => { if (name === 'check_chapter_parts') handler = fn } }, () => sb)
let fails = 0
const ok = (label, cond) => { console.log((cond ? '✓ ' : '✗ ') + label); if (!cond) fails++ }
const r1 = await handler({ chapter: '조종형 비행기', volume: 1 })
const t1 = r1.content[0].text
console.log(t1)
ok('띄어쓰기 무시하고 차시를 찾는다', t1.includes('■ 조종형비행기') && t1.includes('1차시'))
ok('DB 에 없는 부품을 표시', t1.includes('✗ 3개') && t1.includes('부품 DB 에 없어요'))
ok('자동탐지 연결점 경고', t1.includes('DC모터') && t1.includes('자동탐지'))
ok('3D 모델 없는 부품 표시', t1.includes('리모컨') && t1.includes('3D 모델 없음'))
ok('확정 부품 표시', t1.includes('3단블록') && t1.includes('면 이름 확정'))
ok('해야 할 일 목록', t1.includes('── 해야 할 일 ──') && t1.includes('직접 등록'))
const r2 = await handler({ chapter: '없는차시', volume: 1 })
ok('없는 차시는 오류와 목록', r2.isError && r2.content[0].text.includes('있는 차시'))
console.log('실패', fails); process.exit(fails ? 1 : 0)
