import fs from 'node:fs'
import { resolveConnectorName } from '../../app/lib/cubo-assembly-tools.js'
const win = {}; new Function('window', fs.readFileSync(new URL('../../public/design-faces.js', import.meta.url), 'utf8'))(win)
const F = win.IVS_FACES
const blk = { pegs: [ {id:'p1',dir:[1,0,0],pos:[17.5,0,0]},{id:'p2',dir:[-1,0,0],pos:[-17.5,0,0]},{id:'p3',dir:[0,0,1],pos:[10,0,7.5]},{id:'p4',dir:[0,0,1],pos:[0,0,7.5]},{id:'p5',dir:[0,0,1],pos:[-10,0,7.5]},{id:'p6',dir:[0,0,-1],pos:[0,0,-7.5]},{id:'p7',dir:[0,0,-1],pos:[10,0,-7.5]},{id:'p8',dir:[0,0,-1],pos:[-10,0,-7.5]} ], holes: [ {id:'h1',dir:[0,-1,0],len:10,pos:[-10,0,0],through:true},{id:'h2',dir:[0,-1,0],len:10,pos:[0,0,0],through:true},{id:'h3',dir:[0,-1,0],len:10,pos:[10,0,0],through:true} ] }
let fails = 0
const eq = (label, got, want) => { const ok = got === want; if (!ok) fails++; console.log((ok ? '✓ ' : '✗ ') + label, got, ok ? '' : '(기대 ' + want + ')') }
eq('id 그대로', resolveConnectorName(F, blk, 'h2'), 'h2')
eq('돌기면 +z 1', resolveConnectorName(F, blk, '돌기면 +z 1'), 'p5')
eq('돌기면 +z 3', resolveConnectorName(F, blk, '돌기면 +z 3'), 'p3')
eq('돌기면 -z 1', resolveConnectorName(F, blk, '돌기면 -z 1'), 'p8')
eq('돌기면 −z 3(유니코드 마이너스)', resolveConnectorName(F, blk, '돌기면 −z 3'), 'p7')
eq('홀면 +y 3', resolveConnectorName(F, blk, '홀면 +y 3'), 'h3')
eq('홀면 -y 1(관통 반대 면)', resolveConnectorName(F, blk, '홀면 -y 1'), 'h1')
eq('돌기면 +x(1개뿐이면 번호 생략)', resolveConnectorName(F, blk, '돌기면 +x'), 'p1')
for (const bad of ['돌기면 +z 9', '홀면 +x 1']) { try { resolveConnectorName(F, blk, bad, '3단블록'); fails++; console.log('✗ 오류가 나야 함', bad) } catch (e) { console.log('✓ 오류:', e.message) } }
console.log('실패', fails); process.exit(fails ? 1 : 0)
