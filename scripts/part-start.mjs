// 3D 부품 시작 도우미 — "3D 부품 등록할 거야"로 작업을 시작할 때 매번 손으로 하던 준비를 대신한다(조립도의 number_start.py 에 해당).
//   node scripts/part-start.mjs                 → 브랜드별 현황 표(모델·연결점·썸네일·출력용)만 본다
//   node scripts/part-start.mjs <부품이름>       → 그 이름의 DB 행(브랜드·권·수량·모델·연결점·썸네일)과 다음에 할 일
// 하는 일: ① 개발 서버(3178) 응답 ② .env.local 키 ③ DB 읽기 ④ 브랜드별 현황 ⑤ 부품 행 찾기 ⑥ 그 브랜드의 생성기·원본 문서 안내 ⑦ 시작 체크리스트 출력.
// 하지 않는 일: DB 쓰기, 모델 만들기, 판단. 로그인(브라우저)은 확인할 수 없으니 사용자에게 요청하라고 알려 줄 뿐이다.
import fs from 'node:fs'
import path from 'node:path'
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), '..')
const name = process.argv[2]
const line = (s = '') => console.log(s)
line('═══ 3D 부품 시작 점검 ═══')

// ① 개발 서버
try { const r = await fetch('http://localhost:3178/index.html', { signal: AbortSignal.timeout(3000) }); line(`① 개발 서버 http://localhost:3178 : ${r.ok ? '응답함' : '응답 이상 ' + r.status}`) }
catch { line('① 개발 서버 http://localhost:3178 : ❌ 응답 없음 → preview_start invent-school-dev (저장소 CLAUDE.md 1번)') }
line('   로그인: 브라우저 pane 에서 index.html → 부품 관리 탭이 보이면 로그인된 것. 로그인 화면이면 사용자에게 로그인을 요청한다(비밀번호는 대신 입력하지 않는다).')

// ② .env.local  ③ DB
let env = {}
try { env = Object.fromEntries(fs.readFileSync(path.join(root, '.env.local'), 'utf8').split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')])) } catch {}
if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) { line('② .env.local : ❌ SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 없음 → 사용자에게 요청'); process.exit(1) }
line('② .env.local : 키 있음')
const H = { apikey: env.SUPABASE_SERVICE_ROLE_KEY, Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}` }
const get = async (p) => { const r = await fetch(`${env.SUPABASE_URL}/rest/v1/${p}`, { headers: H }); if (!r.ok) throw new Error(r.status + ' ' + (await r.text()).slice(0, 120)); return r.json() }
let cats, rows
try {
  cats = await get('ivs_robot_categories?select=id,data'); rows = await get('ivs_part_catalog?select=id,name:data->>name,cat:data->>category,subject:data->>subject,vol:data->volumes,shape:data->spec->shapes->0->>type,pegs:data->connectors->pegs,holes:data->connectors->holes,thumb:data->>thumbnail3d,print:data->print->>file,size:data->>size,color:data->>color&limit=3000')
  line('③ DB 읽기 : 됨')
} catch (e) { line('③ DB 읽기 : ❌ ' + e.message + ' → 멈추고 사용자에게 알린다(읽지 못했다고 통과시키지 않는다)'); process.exit(1) }
const cn = Object.fromEntries(cats.map((c) => [c.id, c.data.name]))
const hasConn = (r) => (Array.isArray(r.pegs) && r.pegs.length) || (Array.isArray(r.holes) && r.holes.length)

// ④ 브랜드별 현황
line('\n④ 브랜드별 현황 (로봇 과목) — 앞 브랜드들은 "모델 → 연결점 → 3D 썸네일" 순서로 끝냈다. 연결점이 빈 곳은 조립도를 못 만든다.')
const by = {}
for (const r of rows) { if (r.subject !== 'robot') continue; const k = cn[r.cat] || '(공통)'; const s = (by[k] ??= { n: 0, model: 0, conn: 0, thumb: 0, print: 0 }); s.n++; if (r.shape) s.model++; if (hasConn(r)) s.conn++; if (r.thumb) s.thumb++; if (r.print) s.print++ }
for (const [k, s] of Object.entries(by).sort((a, b) => b[1].n - a[1].n)) line(`   ${k.padEnd(9)} 부품 ${String(s.n).padStart(3)} | 3D모델 ${String(s.model).padStart(3)} | 연결점 ${String(s.conn).padStart(3)} | 3D썸네일 ${String(s.thumb).padStart(3)} | 출력용 ${String(s.print).padStart(3)}`)

// ⑤ 부품 행 찾기
const GEN = {
  '큐보': ['scripts/make-part-stl.mjs <frame|block|bracket|arc|bent|rivet|servohorn|roundhorn|bolt|nut|servobolt|peg>', 'app/lib/cubo-*-mesh.js', '규격: get_part_standard(app/lib/cubo-part-maker.js) · 출력용: scripts/make-print-*.mjs, register-print-stl.mjs'],
  '에이스랩': ['scripts/make-robotron-*.mjs (flatplate·curvedplate·rivet·bush·axles·dcmotor·led·tire·wheel…)', 'app/lib/acelab-frame-mesh.js, robotron-*-mesh.js', 'CLAUDE.md "로버트론 부품 3D 모델 규칙", 테두리 선 0.1mm'],
  '로보타미주니어': ['scripts/make-junior-parts.mjs [--write], make-robotron-*.mjs', 'app/lib/junior-frame-mesh.js, junior-rivet-mesh.js', 'CLAUDE.md "로버트론 부품 3D 모델 규칙", 출력용 make-robotron-print.mjs'],
  '프로보 커넥트': ['scripts/make-proboconnect-{block,pin,dualpin,steppin,hinge,gear,arch}.mjs', 'app/lib/proboconnect-block-mesh.js(PROBO_STD)·proboconnect-pin-mesh.js', '등록: scripts/register-proboconnect-parts.mjs <행 id> <STL> <크기> <색>'],
}
if (name) {
  const hit = rows.filter((r) => r.subject === 'robot' && r.name && r.name.replace(/\s+/g, '').toLowerCase().includes(name.replace(/\s+/g, '').toLowerCase()))
  line(`\n⑤ "${name}" 부품 행 ${hit.length}개`)
  if (!hit.length) line('   없음 → 새 행이 필요하다. 먼저 교재 부품표에서 권·수량을 확인하고, 이름은 교재 이름 그대로(센서·리모컨·모터 이름 규칙 포함) 부품 관리 "+ 부품 등록" 또는 add-*.mjs 로 만든다.')
  for (const r of hit) {
    const vols = (r.vol || []).map((v) => `${v.volume}권${v.qty != null ? ' ' + v.qty + '개' : ''}`).join(', ') || '권 미배정'
    line(`   · ${(cn[r.cat] || '(공통)')} / ${r.name} / ${vols} / 크기 ${r.size || '-'} / 색 ${r.color || '-'}`)
    line(`     모델 ${r.shape ? '있음' : '❌ 없음'} | 연결점 ${hasConn(r) ? '있음' : '❌ 없음'} | 3D 썸네일 ${r.thumb ? '있음' : '❌ 없음'} | 출력용 ${r.print ? '있음' : '-'} | id ${r.id}`)
    const g = GEN[cn[r.cat]]
    if (g) { line('     이 브랜드 생성기:'); g.forEach((x) => line('       - ' + x)) } else line('     이 브랜드(익사이팅·테크닉·X로보·메타·스카이로보)는 3D 생성 규칙이 저장소에 없다 → 06_3D부품_만들기_등록.md "알려진 빈틈"')
  }
} else line('\n⑤ 부품 이름을 주면 그 행의 상태를 보여 준다: node scripts/part-start.mjs <부품이름>')

// ⑦ 체크리스트
line(`
⑥ 시작 체크리스트 (06_3D부품_만들기_등록.md 가 원본 — 먼저 읽는다)
  1. 규격 문서(get_part_standard) + 06 문서를 읽고 첫 보고에 "이번 부품에서 지킬 규칙 3개"를 적는다.
  2. 같은 브랜드의 기존 생성기(⑤ 목록)를 읽고 같은 방식으로 새 스크립트를 만든다. 내 방식으로 새로 짜지 않는다.
  3. 교재 부품표·그림을 직접 본다(등록된 PDF, 글자가 깨지면 이미지로). 치수를 모르면 유추하고 "추정"이라 적는다. "규칙이 없다"고 하지 않는다.
  4. 사용자 숫자는 오타일 수 있다(8↔9: 38블록=3X8, 18블럭=1X8). "유추해봐"는 되묻지 말고 계산으로 정한다.
  5. 만든 뒤: 삼각형 수·KB·짝 없는 모서리 0·같은 방향 겹침 0·부피, 사용자가 말한 치수를 다시 잰 값, 짝 부품과 겹쳐 본 결과를 숫자로 보고한다.
  6. 진행 방식: 만들고 → 그 로봇의 부품 행에 바로 등록(06 문서 4절) → ✅ 골라서 그리기(새 부품 id 만)로 썸네일 → 부품 관리의 그 로봇 탭 부품리스트에서 3D 창을 열어 보여 준다. 등록 전 미리보기·오버레이·부품 수리실 화면은 쓰지 않는다. 보고에 "어느 로봇 몇 권 행"을 쓴다.
  7. 3D 썸네일(✅ 골라서 그리기, 새 부품 id 만)과 연결점(measure_part → set_part_connectors)까지 끝내야 "끝"이다. 커밋·푸시는 사용자가 "업로드"라고 할 때만.`)
