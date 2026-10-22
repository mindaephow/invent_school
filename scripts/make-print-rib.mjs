// 프린트용 시험: 구멍 목 6.2(입구·테두리 같이 +0.35)에 가운데 얇은 고리(립)를 넣어 기성품 블록 돌기를 잡는다. 립 안지름 = 6.2 − 2×delta.
//   node scripts/make-print-rib.mjs [저장 폴더]    (기본: 다운로드/큐보_3D모델_프린트용/립시험)   3구멍 프레임 3종(delta 0.10·0.20·0.30, 립 두께 0.8)
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { CUBO_FRAME_STD as S } from '../app/lib/cubo-part-maker.js'
import { makeKit, trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { addPlate } from '../app/lib/cubo-plate-mesh.js'
const out = process.argv[2] || path.join(os.homedir(), 'Downloads', '큐보_3D모델_프린트용', '립시험'); fs.mkdirSync(out, { recursive: true })
const L = 0.35, SEG = 64, base = { ...S }
const flat = (t) => { const a = Float32Array.from(t), n = a.length / 3
    let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], a[i * 3 + k]); mx[k] = Math.max(mx[k], a[i * 3 + k]) }
  for (let i = 0; i < n; i++) { a[i * 3] -= (mn[0] + mx[0]) / 2; a[i * 3 + 2] -= (mn[2] + mx[2]) / 2; a[i * 3 + 1] -= mn[1] }   // 메쉬 좌표(두께 y)에서 가운데 맞춤·바닥 0 — STL 변환(trianglesToStl)이 두께를 z(위)로 눕힌다
  return a }
const save = (name, kit) => { fs.writeFileSync(path.join(out, name), trianglesToStl(flat(kit.result()))); console.log(name) }
const frame3 = () => { const kit = makeKit(SEG), nx = 3, hx = nx * S.pitch / 2, hz = S.pitch / 2
  addPlate(kit, { xCells: Array.from({ length: nx }, (_, i) => ({ lo: -hx + i * S.pitch, hi: -hx + (i + 1) * S.pitch, c: -hx + S.margin + i * S.pitch })), zCells: [{ lo: -hz, hi: hz, c: 0 }] }); return kit }
// ① 목 지름만 6.1·6.15 (6.0 은 축이 안 들어가고 6.2 는 너무 헐거워서 그 사이)
for (const dia of [6.1, 6.15, 6.16]) { const l = dia / 2 - base.boreR; Object.assign(S, base, { boreR: base.boreR + l, rimInnerR: base.rimInnerR + l, rimOuterR: base.rimOuterR + l, edgeWall: base.edgeWall - l }); save(`프레임3_구멍${dia.toFixed(2)}.stl`, frame3()) }
// ③ 목 6.10 고정 + 테두리(입구) 여유를 더 크게: 입구 반지름 3.85·3.95·4.05, 테두리 폭 0.5 유지(바깥 반지름 = 입구 + 0.5; 0.4 는 슬라이서가 빼 버려 안 나왔다 — 사용자 지적 2026-10-22, 가장자리 벽은 그만큼 얇아짐)
for (const entry of [3.85, 3.95, 4.05]) { const outer = entry + 0.5, l = 6.1 / 2 - base.boreR; Object.assign(S, base, { boreR: base.boreR + l, rimInnerR: entry, rimOuterR: outer, edgeWall: base.edgeWall - (outer - base.rimOuterR) }); save(`프레임3_목6.10_입구지름${(entry * 2).toFixed(1)}.stl`, frame3()) }
// ② 목 6.2 + 가운데 얇은 고리(립 두께 0.8): 립 안지름 6.1·6.0·5.9
for (const d of [0.05, 0.1, 0.15]) {
  Object.assign(S, base, { boreR: base.boreR + L, rimInnerR: base.rimInnerR + L, rimOuterR: base.rimOuterR + L, edgeWall: base.edgeWall - L, ribR: base.boreR + L - d, ribH: 0.8 })
  save(`프레임3_목6.20_립안지름${(2 * S.ribR).toFixed(2)}.stl`, frame3())
}
Object.assign(S, base)
