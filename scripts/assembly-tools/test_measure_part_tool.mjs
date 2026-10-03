// MCP 도구 measure_part 연결을 가짜 DB 로 시험한다(가짜 부품은 test_measure_part.mjs 와 같은 상자+돌기).   node scripts/assembly-tools/test_measure_part_tool.mjs
import { registerCuboAssemblyTools } from '../../app/lib/cubo-assembly-tools.js'
const tris = []
const add = (a, b, c) => tris.push([a, b, c])
const quad = (p0, p1, p2, p3) => { const cen = [0, 1, 2].map((i) => (p0[i] + p1[i] + p2[i] + p3[i]) / 4); const u = p1.map((v, i) => v - p0[i]), w = p2.map((v, i) => v - p0[i]); const n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]; if (n[0] * cen[0] + n[1] * cen[1] + n[2] * cen[2] > 0) { add(p0, p1, p2); add(p0, p2, p3) } else { add(p0, p2, p1); add(p0, p3, p2) } }
const [X, Y, Z] = [20, 5, 10]
quad([-X, -Y, -Z], [X, -Y, -Z], [X, Y, -Z], [-X, Y, -Z]); quad([-X, -Y, Z], [X, -Y, Z], [X, Y, Z], [-X, Y, Z]); quad([-X, -Y, -Z], [X, -Y, -Z], [X, -Y, Z], [-X, -Y, Z]); quad([-X, Y, -Z], [X, Y, -Z], [X, Y, Z], [-X, Y, Z]); quad([-X, -Y, -Z], [-X, Y, -Z], [-X, Y, Z], [-X, -Y, Z]); quad([X, -Y, -Z], [X, Y, -Z], [X, Y, Z], [X, -Y, Z])
for (let i = 0; i < 20; i++) { const t0 = (i / 20) * 2 * Math.PI, t1 = ((i + 1) / 20) * 2 * Math.PI; const P = (t, h) => [10 + 3.8 * Math.cos(t), 3.8 * Math.sin(t), h]; const a = P(t0, Z), b = P(t1, Z), c = P(t1, Z + 5), d = P(t0, Z + 5); add(a, b, c); add(a, c, d) }
const buf = Buffer.alloc(84 + tris.length * 50); buf.writeUInt32LE(tris.length, 80)
tris.forEach((t, i) => { const o = 84 + i * 50; t.forEach((p, k) => { buf.writeFloatLE(p[0], o + 12 + k * 12); buf.writeFloatLE(-p[2], o + 16 + k * 12); buf.writeFloatLE(p[1], o + 20 + k * 12) }) })
const row = { id: 'x', name: '가짜부품', shape: { type: 'import', x: 0, y: 0, z: 0, rx: 0, ry: 0, rz: 0, fileDataUrl: 'data:application/octet-stream;base64,' + buf.toString('base64') }, connectors: { pegs: [{ id: 'p1', pos: [10, 0, 10], dir: [0, 0, 1], len: 5, r: 3.8 }], holes: [] } }
const rows = [row, { id: 'y', name: '도형부품', shape: { type: 'box' }, connectors: null }]
const sb = { from: () => { const q = { _n: null, select() { return q }, eq(col, v) { if (col === 'data->>name') q._n = v; return q }, then(res) { res({ data: rows.filter((r) => r.name === q._n), error: null }) } }; return q } }
let handler; registerCuboAssemblyTools({ registerTool: (name, _d, fn) => { if (name === 'measure_part') handler = fn } }, () => sb)
let fails = 0; const ok = (l, c) => { console.log((c ? '✓ ' : '✗ ') + l); if (!c) fails++ }
const a = await handler({ name: '가짜부품' }); const t = a.content[0].text; console.log(t)
ok('실측 보고가 나온다', t.includes('■ 가짜부품 실측') && t.includes('돌기 +z'))
ok('등록 연결점과 일치로 대조된다', t.includes('✓ p1') && t.includes('일치 1'))
const b = await handler({ name: '도형부품' }); ok('도형 부품은 STL 이 아니라고 알려 준다', b.isError && b.content[0].text.includes('STL 모델이 아니라'))
const c = await handler({ name: '없는부품' }); ok('없는 부품은 오류', c.isError)
console.log('실패', fails); process.exit(fails ? 1 : 0)
