// 프로보 커넥트 듀얼핀 STL 만들기. 사용: node scripts/make-proboconnect-dualpin.mjs <저장할 파일.stl>
// 사용자 지시(2026-10-30): "듀얼핀은 큐보에 있는 리벳하고 비슷한 모양", "돌리는 방식이 아니야"(눌러 끼우는 스냅핏), "가운데 원통으로 뚫어주고, 위아래 십자 컷팅 말고 일자 컷팅".
// 치수는 큐보 리벳 규격(cubo-rivet-mesh.js RIVET_STD)을 그대로 쓴다: 플랜지 반지름 3.3·두께 2, 몸통 반지름 2.6(플랜지에서 끝 쪽 3), 머리 반지름 3.1(뒷면 경사 0.3, 앞 0.7 은 3.1→2.5 로 가늘어짐), 전체 길이 10.
// 큐보 리벳과 다른 점: ① 가운데를 반지름 1.5 원통으로 뚫는다(관통) ② 양 끝의 홈이 십자가 아니라 일자 한 줄(폭 1.2, 플랜지 면에서 끝까지) — 홈은 x 방향으로 길게 나서 머리가 z(블럭 띠 폭) 방향으로 오므려진다.
// 좌표: 축 y(가운데 0, 위 끝 +5), 홈 방향 x.
import fs from 'node:fs'
import Module from 'manifold-3d'
import { RIVET_STD as R_ } from '../app/lib/cubo-rivet-mesh.js'
import { trianglesToStl } from '../app/lib/cubo-mesh-kit.js'
import { checkMesh } from '../app/lib/cubo-mesh-repair.js'

const out = process.argv[2]
if (!out) { console.error('사용: node scripts/make-proboconnect-dualpin.mjs <저장할 파일.stl>'); process.exit(1) }
const wasm = await Module(); wasm.setup()
const M = wasm.Manifold
const bore = 1.5, L = 2 * R_.pegEnd
// 회전체 단면(반지름, 높이): 위 끝 → 아래 끝
const up = [[R_.tipR, R_.pegEnd], [R_.headR, R_.shaftTo + R_.backRamp], [R_.shaftR, R_.shaftTo], [R_.shaftR, R_.collarHalf], [R_.collarR, R_.collarHalf]]
const prof = [[0, R_.pegEnd], ...up, ...up.slice().reverse().map(([r, y]) => [r, -y]), [0, -R_.pegEnd]]
const area = prof.reduce((s, q, i) => { const n = prof[(i + 1) % prof.length]; return s + (q[0] * n[1] - n[0] * q[1]) }, 0)
const solid = M.revolve([area > 0 ? prof : prof.slice().reverse()], 48).rotate([-90, 0, 0])   // revolve 결과는 축이 z → y 로 세운다
const hole = M.cylinder(L + 2, bore, bore, 32, true).rotate([-90, 0, 0])      // 가운데 원통 구멍(관통)
const slit = (y0, y1) => M.cube([2 * R_.collarR + 2, y1 - y0, R_.slit], false).translate([-R_.collarR - 1, y0, -R_.slit / 2])   // 일자 홈: x 방향으로 길게, 폭(z) 1.2
let body = M.difference(solid, hole)
body = M.difference(M.difference(body, slit(R_.collarHalf, R_.pegEnd + 1)), slit(-R_.pegEnd - 1, -R_.collarHalf))
const m = body.getMesh(), tris = new Float32Array(m.triVerts.length * 3)
for (let i = 0; i < m.triVerts.length; i++) for (let k = 0; k < 3; k++) tris[i * 3 + k] = m.vertProperties[m.triVerts[i] * m.numProp + k]
const stl = trianglesToStl(tris)
fs.writeFileSync(out, stl)
const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9]
for (let i = 0; i < tris.length; i += 3) for (let k = 0; k < 3; k++) { mn[k] = Math.min(mn[k], tris[i + k]); mx[k] = Math.max(mx[k], tris[i + k]) }
console.log(`듀얼핀: 삼각형 ${tris.length / 9}개, ${(stl.length / 1024).toFixed(0)}KB`, JSON.stringify(checkMesh(tris)), '크기 x,y,z', mx.map((v, k) => +(v - mn[k]).toFixed(2)).join('×'), 'y범위', mn[1].toFixed(2), mx[1].toFixed(2), '→', out)
