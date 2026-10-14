// usage: node insertion_check.js  →  ../../public/design-warnings.js 를 만든다(관리자 화면의 ⚠ 경고 목록).
// 각 단계에서 새로 끼우는 부품이 그 시점의 부품들(같은 창고 슬롯) 사이로 어느 방향으로든 빠지는지 본다(public/design-insertion.js).
// 몸통 상자 근사라 꺾인 프레임·서브 조립 등은 오경고일 수 있다 — 관리자가 화면에서 보고 "문제없음"/"해결요청"을 고른다.
const fs = require('fs'), path = require('path');
global.window = {};
const pub = path.join(__dirname, '..', '..', 'public') + '/';
eval(fs.readFileSync(pub + 'design-mates.js', 'utf8'));
eval(fs.readFileSync(pub + 'design-collision.js', 'utf8'));
eval(fs.readFileSync(pub + 'design-insertion.js', 'utf8'));
const C = window.IVS_COLLISION, M = window.IVS_MATES, I = window.IVS_INSERTION;
const dims = JSON.parse(fs.readFileSync(path.join(__dirname, 'dims.json'), 'utf8'));
function quat(r) { const m = M.matFromEuler(r); const t = m[0][0] + m[1][1] + m[2][2]; let w, x, y, z;
  if (t > 0) { const s = Math.sqrt(t + 1) * 2; w = s / 4; x = (m[2][1] - m[1][2]) / s; y = (m[0][2] - m[2][0]) / s; z = (m[1][0] - m[0][1]) / s; }
  else if (m[0][0] > m[1][1] && m[0][0] > m[2][2]) { const s = Math.sqrt(1 + m[0][0] - m[1][1] - m[2][2]) * 2; w = (m[2][1] - m[1][2]) / s; x = s / 4; y = (m[0][1] + m[1][0]) / s; z = (m[0][2] + m[2][0]) / s; }
  else if (m[1][1] > m[2][2]) { const s = Math.sqrt(1 + m[1][1] - m[0][0] - m[2][2]) * 2; w = (m[0][2] - m[2][0]) / s; x = (m[0][1] + m[1][0]) / s; y = s / 4; z = (m[1][2] + m[2][1]) / s; }
  else { const s = Math.sqrt(1 + m[2][2] - m[0][0] - m[1][1]) * 2; w = (m[1][0] - m[0][1]) / s; x = (m[0][2] + m[2][0]) / s; y = (m[1][2] + m[2][1]) / s; z = s / 4; }
  return { x, y, z, w }; }
const out = {};
for (const f of fs.readdirSync(__dirname).filter((n) => /_asm\.json$/.test(n))) {
  const name = f.replace('_asm.json', '');
  let id; try { id = fs.readFileSync(path.join(__dirname, name + '_entry.js'), 'utf8').match(/id:\s*"([^"]+)"/)[1]; } catch (e) { continue; }
  const asm = JSON.parse(fs.readFileSync(path.join(__dirname, f), 'utf8'));
  const placed = []; const res = {};
  asm.steps.forEach((s, k) => {
    const slot = s.slot == null ? 1 : s.slot;
    const mine = [];
    (s.parts || []).forEach((pt, i) => {
      if (pt.side) return;
      const o = { id: (k + 1) + '.' + i, step: k + 1, slot, name: pt.n, boxes: C.coreBoxes(pt.n, dims[pt.n] || [0, 0, 0]), q: quat(pt.r || [0, 0, 0]), pos: { x: pt.p[0], y: pt.p[1], z: pt.p[2] } };
      placed.push(o); mine.push(o);
    });
    const group = placed.filter((p) => p.slot === slot);
    mine.forEach((p) => {
      if (!p.boxes) return;
      const r = I.findRemovalDir(p, group);
      if (r.dir) return;
      const by = [...new Set(Object.values(r.blockers))].map((bid) => { const b = placed.find((x) => x.id === bid); return b ? b.name + '(' + bid + ')' : bid; });
      (res[k + 1] = res[k + 1] || []).push({ key: p.id + '|' + p.name + '|' + by.join(','), part: p.name, text: p.name + '(' + p.id + ')이(가) ' + by.join(', ') + ' 에 막혀 어느 방향으로도 끼워 넣거나 뺄 수 없는 것으로 보여요' });
    });
  });
  out[id] = res;
  console.log(id, Object.keys(res).map((k) => k + ':' + res[k].length).join(' ') || '(경고 없음)');
}
fs.writeFileSync(pub + 'design-warnings.js', '// 자동 생성 — scripts/assembly-tools/insertion_check.js (직접 고치지 않는다)\nwindow.IVS_ASM_WARNINGS = ' + JSON.stringify(out) + ';\n');
