// set_part_connectors 가 "이 부품을 쓰는 조립도"의 바꾸기 전·후 검사를 비교하는지 가짜 DB 로 시험한다.   node scripts/assembly-tools/test_connector_impact.mjs
import { registerCuboAssemblyTools } from '../../app/lib/cubo-assembly-tools.js'
const frame = (L, W) => { const holes = []; for (let i = 0; i < L; i++) for (let j = 0; j < W; j++) holes.push({ id: `h${i + 1}_${j + 1}`, pos: [(i - (L - 1) / 2) * 10, 0, (j - (W - 1) / 2) * 10], dir: [0, -1, 0], len: 5, r: 3.5, through: true }); return { pegs: [], holes } }
const peg = (id, pos, dir) => ({ id, pos, dir, len: 5, r: 2.5 })
// 오늘 새 모델로 바꾸기 전(옛) / 후(새) DC모터 연결점
const dcOld = { pegs: [peg('p1', [0, 16.5, 20], [0, 1, 0]), peg('p2', [0, 16.5, -20], [0, 1, 0]), peg('p3', [17.5, -1, 10], [1, 0, 0]), peg('p4', [17.5, -1, -10], [1, 0, 0]), peg('p5', [-17.5, -1, 10], [-1, 0, 0]), peg('p6', [-17.5, -1, -10], [-1, 0, 0])], holes: [] }
const dcNew = { pegs: [peg('p1', [0, 16.5, 18.5], [0, 1, 0]), peg('p2', [0, 16.5, -21.5], [0, 1, 0]), peg('p3', [17.5, -1, 8.5], [1, 0, 0]), peg('p4', [17.5, -1, -11.5], [1, 0, 0]), peg('p5', [-17.5, -1, 8.5], [-1, 0, 0]), peg('p6', [-17.5, -1, -11.5], [-1, 0, 0])], holes: [] }
const rows = { '37프레임': frame(7, 3), get 'DC모터'() { return stored ? stored.data.connectors : dcOld } }
let stored = null
const sb = { from: () => {
  const q = { _op: 'select', _upd: null, select() { return q }, update(v) { q._op = 'update'; q._upd = v; return q }, eq() { return q }, in() { return q },
    maybeSingle() { return Promise.resolve({ data: { data: { name: 'DC모터', connectors: stored ? stored.data.connectors : dcOld } }, error: null }) },
    then(res) { if (q._op === 'update') { stored = q._upd; res({ error: null }) } else res({ data: Object.entries(rows).map(([name, connectors]) => ({ name, connectors })), error: null }) } }
  return q } }
let handler
registerCuboAssemblyTools({ registerTool: (name, _d, fn) => { if (name === 'set_part_connectors') handler = fn } }, () => sb)
let fails = 0
const ok = (label, cond) => { console.log((cond ? '✓ ' : '✗ ') + label); if (!cond) fails++ }
const out = (await handler({ partId: 'dc', connectors: dcNew })).content[0].text
console.log(out)
ok('저장이 일어났다', stored && stored.data.connectors === dcNew)
ok('영향받는 조립도 목록이 나온다', out.includes('── 이 부품을 쓰는 조립도 검사') && out.includes('cubo-1-autogun'))
ok('오토건 6단계 DC모터 허공이 해결됨으로 나온다(옛 연결점 → 새 연결점)', out.includes('해결됨') && out.includes('DC모터'))
const same = (await handler({ partId: 'dc', connectors: dcOld })).content[0].text
ok('같은 값을 다시 쓰면 변화 없음이 아니라 이번엔 반대로 새 문제가 보고된다(옛 값은 새 조립도와 어긋남)', same.includes('새로 생김'))
console.log('실패', fails); process.exit(fails ? 1 : 0)
