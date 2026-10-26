// 에이스랩·로보타미주니어 휠풀리(그레이) 기본 모양을 등록한다(권별 수량·이름·색은 그대로). 아직 기본 모양까지만 — 나머지는 정해지면 추가.
//   node scripts/make-robotron-wheelpulley.mjs [--write]
import fs from 'node:fs'
import { wheelPulleyTriangles, WHEELPULLEY_STD as W } from '../app/lib/robotron-wheelpulley-mesh.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { ringFace, circlePts } from '../app/lib/cubo-face-mesh.js'

const WRITE = process.argv.includes('--write')
const env = Object.fromEntries(fs.readFileSync(new URL('../.env.local', import.meta.url), 'utf8').split(/\r?\n/).filter((l) => l.includes('=')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^"|"$/g, '')]))
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' }
const rest = async (p, opt = {}) => { const r = await fetch(env.SUPABASE_URL + '/rest/v1/' + p, { headers: H, ...opt }); if (!r.ok) throw new Error(p + ' ' + r.status + ' ' + (await r.text()).slice(0, 300)); return opt.method ? null : r.json() }
const CATS = { 'cf342cca-792f-4e70-863b-b12de631f1cc': '에이스랩', 'ea24c385-7896-4d40-b343-1cef47e471e7': '로보타미주니어' }
const HEX = { 그레이: '#9ca5af', 블랙: '#555555' }
const toDataUrl = (b) => 'data:application/octet-stream;base64,' + Buffer.from(b).toString('base64')
const tris = wheelPulleyTriangles(), stl = trianglesToStl(tris)
const unp = (() => { const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(','), e = new Map(); for (let t = 0; t < tris.length / 9; t++) { const v = [0, 1, 2].map((k) => [tris[t * 9 + k * 3], tris[t * 9 + k * 3 + 1], tris[t * 9 + k * 3 + 2]]); for (let i = 0; i < 3; i++) { const a = v[i], b = v[(i + 1) % 3], k1 = key(...a) + '>' + key(...b), k2 = key(...b) + '>' + key(...a); if (e.has(k2)) e.delete(k2); else e.set(k1, 1) } } return e.size })()
console.log('휠풀리 메시 짝 없는 모서리', unp, '삼각형', tris.length / 9)
const unpOf = (t) => { const key = (a, b, c) => [a, b, c].map((v) => Math.round(v * 1e4)).join(','), e = new Map(); for (let i = 0; i < t.length / 9; i++) { const v = [0, 1, 2].map((k) => [t[i * 9 + k * 3], t[i * 9 + k * 3 + 1], t[i * 9 + k * 3 + 2]]); for (let j = 0; j < 3; j++) { const a = v[j], b = v[(j + 1) % 3], k1 = key(...a) + '>' + key(...b), k2 = key(...b) + '>' + key(...a); if (e.has(k2)) e.delete(k2); else e.set(k1, 1) } } return e.size }
setTimeout(() => {}, 0)
// 뷰어는 한 부품을 음영 없이 한 색으로 칠해서 원기둥 구멍이 안 보인다 → 구멍 바닥에 밝은(흰색) 고리 판(열십자 홀 자리는 뚫림)과 돌기 끝 구멍 가장자리에 짙은 고리 띠를 색칠 조각으로 얹는다. (모터축·LED센서와 같은 방식. 크기 5mm 이상인 파일만 쓴다.)
const MARK = { floorColor: '#f2f4f8', rimColor: '#555555', floorT: 0.2, rimT: 0.15, rimW: 0.5 }
const crossPoly = () => { const a = W.crossSpan / 2, w = W.crossArm / 2; return [[a, -w], [a, w], [w, w], [w, a], [-w, a], [-w, w], [-a, w], [-a, -w], [-w, -w], [-w, -a], [w, -a], [w, -w]] }
const floorTris = () => { const k = makeKit(48), { quad, P } = k, r = W.boreR - 0.1, d = circlePts(0, 0, r, 48), cr = crossPoly(); k.cyl(0, 0, r, 0, MARK.floorT, 1);
  cr.forEach((A, i) => { const B = cr[(i + 1) % cr.length], dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], MARK.floorT, B[1]), P(A[0], MARK.floorT, A[1]), -dz / l, 0, dx / l) })
  ringFace(k, d, [cr], 0, -1); ringFace(k, d, [cr], MARK.floorT, 1); return k.result() }
const rimTris = () => { // 돌기 끝 구멍 가장자리 짙은 띠: 홈(폭 slotW, ±x 방향)을 가리지 않게 +z·−z 두 조각의 C 모양으로 얹는다
  const k = makeKit(24), { quad, P } = k, sh = W.slotW / 2, ro = W.boreR + MARK.rimW, ao = Math.asin(sh / ro), ai = Math.asin(sh / W.boreR), n = 24
  const arc = (r, t0, t1) => Array.from({ length: n + 1 }, (_, i) => { const t = t0 + ((t1 - t0) * i) / n; return [r * Math.cos(t), r * Math.sin(t)] })
  const wall = (pts, dir) => { for (let i = 0; i < pts.length - 1; i++) { const A = pts[i], B = pts[i + 1], mx = (A[0] + B[0]) / 2, mz = (A[1] + B[1]) / 2, l = Math.hypot(mx, mz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], MARK.rimT, B[1]), P(A[0], MARK.rimT, A[1]), (dir * mx) / l, 0, (dir * mz) / l) } }
  for (const base of [0, Math.PI]) {
    const o = arc(ro, base + ao, base + Math.PI - ao), i = arc(W.boreR, base + ai, base + Math.PI - ai), poly = [...o, ...i.slice().reverse()]
    wall(o, 1); wall(i, -1)
    for (const [A, B] of [[o[o.length - 1], i[i.length - 1]], [i[0], o[0]]]) { const dx = B[0] - A[0], dz = B[1] - A[1], l = Math.hypot(dx, dz); quad(P(A[0], 0, A[1]), P(B[0], 0, B[1]), P(B[0], MARK.rimT, B[1]), P(A[0], MARK.rimT, A[1]), dz / l, 0, -dx / l) } // 양 끝 단면
    ringFace(k, poly, [], 0, -1); ringFace(k, poly, [], MARK.rimT, 1)
  }
  return k.result() }
console.log('구멍바닥 판', unpOf(floorTris()), '구멍테두리 띠', unpOf(rimTris()))
const connectors = { note: `휠풀리(지름 ${W.discR * 2}·원판 두께 ${W.discH}, 옆면 실타래 홈 폭 ${W.grooveW}·깊이 ${W.grooveDepth}, 가운데 지름 ${W.bossR * 2}·높이 ${W.bossH} 돌기에 지름 ${W.boreR * 2}·깊이 ${W.bossH} 원기둥 구멍, 전체 높이 ${W.discH + W.bossH}). 원판 가운데 열십자 홀(${W.crossSpan}×${W.crossSpan}, 팔 폭 ${W.crossArm})이 원판을 관통해 원기둥 구멍과 이어진다. 원판에는 중심에서 피치 ${W.holePitch} 떨어진 규격 홀(지름 ${W.holeR * 2}) 4개(h3~h6, 위·아래·좌·우 = 모델 (±${(W.holePitch / Math.SQRT2).toFixed(2)}, ±${(W.holePitch / Math.SQRT2).toFixed(2)}))가 있다. 바닥 5곳(열십자 + 규격 홀 4개)과 윗면 4곳(규격 홀)에 ${W.pocketSide}×${W.pocketSide}, 깊이 ${W.pocketDepth} 사각 홈이 있다(구멍 줄에 맞춰 45° 돌림). 돌기에는 x 축 방향으로 폭 ${W.slotW}·깊이 ${W.slotDepth} 홈(끝은 반원으로 둥글게)이 있다. 기본 모양까지만 — 나머지는 정해지면 추가.`, pegs: [], holes: [{ id: 'h1', r: W.crossSpan / 2, dir: [0, -1, 0], len: W.discH, pos: [0, 0, 0], through: true }, { id: 'h2', r: W.boreR, dir: [0, 1, 0], len: W.bossH, pos: [0, W.discH + W.bossH, 0] }, ...[[1, 1], [1, -1], [-1, 1], [-1, -1]].map(([a, b], i) => ({ id: 'h' + (i + 3), r: W.holeR, dir: [0, -1, 0], len: W.discH, pos: [(a * W.holePitch) / Math.SQRT2, 0, (b * W.holePitch) / Math.SQRT2], through: true }))], size: [W.discR * 2, W.discH + W.bossH, W.discR * 2], confidence: 'draft' }
for (const [cat, label] of Object.entries(CATS)) {
  for (const r of await rest(`ivs_part_catalog?select=id,data&data->>category=eq.${cat}&data->>name=eq.${encodeURIComponent('휠풀리')}`)) {
    const mk = (st, color, name, extra = {}) => ({ x: 0, y: 0, z: 0, op: 'add', rx: 0, ry: 0, rz: 0, type: 'import', color, fileName: `휠풀리_${name}_${label}.stl`, fileDataUrl: toDataUrl(st), brightness: 100, ...extra })
    const spec = { shapes: [{ ...mk(stl, HEX[r.data.color], '본체'), fileName: `휠풀리_${label}.stl` }, mk(trianglesToStl(floorTris()), MARK.floorColor, '구멍바닥', { paint: true, y: W.discH + 0.01 }), mk(trianglesToStl(rimTris()), MARK.rimColor, '구멍테두리', { paint: true, y: W.discH + W.bossH })] }
    const data = { ...r.data, size: `Ø${W.discR * 2}×${W.discH + W.bossH}mm (${label}, 원판 두께 ${W.discH}, 옆면 실타래 폭 ${W.grooveW}·깊이 ${W.grooveDepth}, 돌기 지름 ${W.bossR * 2}·높이 ${W.bossH} 에 지름 ${W.boreR * 2}·깊이 ${W.bossH} 원기둥 구멍, 가운데 열십자 홀 ${W.crossSpan}×${W.crossSpan}, 피치 ${W.holePitch} 규격 홀 4개, 바닥 홈 5곳·윗면 홈 4곳 ${W.pocketSide}×${W.pocketSide} 깊이 ${W.pocketDepth}, 돌기 x 방향 홈 폭 ${W.slotW}·깊이 ${W.slotDepth}(끝 둥글게), 기본 모양)`, spec, connectors, primary_image: 'front' }
    delete data.thumbnail3d; delete data.thumbKey
    console.log(label, r.data.name, r.data.color, 'KB', Math.round(stl.length / 1024))
    if (WRITE) { await rest('ivs_part_catalog?id=eq.' + r.id, { method: 'PATCH', headers: { ...H, Prefer: 'return=minimal' }, body: JSON.stringify({ data }) }); console.log('  → 등록', r.id) }
  }
}
