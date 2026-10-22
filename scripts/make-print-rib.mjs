// 프린트용 시험 조각(통판): 규격은 아래 줄 참고. 원래 디자인(고리+가장자리 벽)은 scripts/make-print-csg.mjs.
//   node scripts/make-print-rib.mjs [저장 폴더]   (기본: 다운로드/큐보_3D모델_프린트용/립시험)
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
// 확정 규격 통판(사용자 2026-10-23): 목 6.10·입구 7.7(깊이 1.1)·가장 얇은 곳 2.8·총 5, 가장자리 벽·고리 없음(파인 곳을 메움), 아래 면 평평
Object.assign(S, base, { boreR: 3.05, rimInnerR: 3.85, rimHeight: 1.1, plate: 2.8, total: 5, slab: true }); save('프레임3_통판_목6.10_입구7.7_목두께2.8_총5.stl', frame3())
Object.assign(S, base); delete S.slab
