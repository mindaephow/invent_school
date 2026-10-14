# 화면(조립 보기) 조작 코드 모음 — 브라우저 패널의 `javascript_tool` 에 그대로 붙여 실행한다 (2026-10-13)

전제: 개발 서버·로그인은 `CLAUDE.md` "새로 시작하거나 새 세션일 때" 1~2번대로 되어 있다. 브라우저 패널은 `mcp__Claude_Browser__navigate` 로 그 개발 서버 주소를 연다. 화면은 오래 열어 둔 채로 두지 말고 **데이터를 고친 뒤에는 새로 불러온다**(navigate 다시).

## 1. 번호 N 을 연다 (권·차시는 조립도마다 다르다 — 드롭체커 = 2권 3차시, 투석기 = 2권 2차시, 스피드바이크 = 2권 1차시)
```js
await new Promise(r=>setTimeout(r,2500));
const sel=[...document.querySelectorAll('select')];
const vol=sel.find(s=>[...s.options].some(o=>o.textContent==='2권')); vol.value='2'; vol.dispatchEvent(new Event('change',{bubbles:true}));
await new Promise(r=>setTimeout(r,1500));
const les=sel.find(s=>[...s.options].some(o=>o.textContent==='3차시')); les.value='3'; les.dispatchEvent(new Event('change',{bubbles:true}));
await new Promise(r=>setTimeout(r,3500));
const N=26; const b=[...document.querySelectorAll('button')].find(x=>new RegExp('^'+N+'(\\s|$)').test(x.textContent.trim())&&x.textContent.trim().length<6); b&&b.click();   // 번호 버튼 글자는 "26 ✓" 또는 "26 🛠" 처럼 뒤에 표시가 붙는다
await new Promise(r=>setTimeout(r,3500));
document.querySelector('canvas').scrollIntoView({block:'center'});   // 화면이 좁아(창 높이 ~560) 3D 가 아래에 있다 — 스크롤해야 보인다
JSON.stringify({clicked:!!b, cam:window.__ivsAssemblyBridge.camState()})
```
- 번호 버튼 글자 뒤 표시: `✓` 사용자 완료, `🛠` 지금 작업 중. 같은 번호 이름의 다른 버튼(🖼 그림 버튼 "🖼3")과 헷갈리지 않게 위처럼 글자 길이를 제한한다.
- **카메라는 사용자가 📷 로 저장한 시점이 코드 시점보다 우선한다.** `camState()` 의 theta·phi 가 코드(`A.steps[N-1].cam`)와 다르면 사용자 저장 시점이다 — 책과 같은 시점으로 비교하려면 아래 2번으로 맞춘다.

## 2. 카메라를 책 시점으로 맞추고 확대한다 (비교용 — 저장하지 않는다)
**먼저 `number_start` 의 "사용자 📷 카메라" 줄을 본다 — 사용자가 저장한 시점이 있으면 그 값이 우선이다(2026-10-13 사용자: "내가 정해놓은 게 있으면 내가 정해놓은 게 우선"). 그럴 때는 `br.camera` 로 덮어쓰지 말고 번호를 연 그대로(`camState()` 가 그 값) 찍어 비교하고, 코드 `cam` 도 그 값에 맞춘다. 아래 값은 사용자 기록이 없을 때만 쓴다(드롭체커 29번: 사용자 📷 theta −0.832·phi 1.076 vs 판 무늬 풀이 −0.88·0.86 — 사용자 값을 따랐다).**
```js
const br=window.__ivsAssemblyBridge; br.camera({target:[5,30,5], radius:300, theta:-0.76, phi:0.96});   // theta·phi = 그 번호 axes_fit 결과(refs/<이름>/NN_axes.json 의 fit)
await new Promise(r=>setTimeout(r,1500)); document.querySelector('canvas').scrollIntoView({block:'center'});
JSON.stringify(br.camState())
```
그다음 `mcp__Claude_Browser__computer` `screenshot` 으로 찍는다. 책 그림 `refs/<이름>/NN.jpg` 와 나란히 보고(링 수 = 화살표 수, 부품 위치·방향·시점), **그 스크린샷 파일 경로**(도구 결과의 `Image: source: …tool-results\….jpg`)를 `record_check.py` 의 캡처로 쓴다(45분 이내·500×350 이상).

## 3. 그림(refs)을 DB 에 올린다 — 만들자마자
```bash
mkdir -p public/_refs_tmp/<이름>      # 저장소 루트에서 — 올린 뒤 지운다(커밋 금지, .gitignore 에 있음)
cp scripts/assembly-tools/refs/<이름>/index.json scripts/assembly-tools/refs/<이름>/NN.jpg scripts/assembly-tools/refs/<이름>/NN_1.jpg scripts/assembly-tools/refs/<이름>/NN_2.jpg public/_refs_tmp/<이름>/
```
```js
const b = window.__ivsAssemblyBridge;   // 조립 보기 화면에서 (차시를 연 뒤)
const index = await (await fetch('/_refs_tmp/<이름>/index.json', { cache: 'no-store' })).json();
const out=[];
for (const r of index.filter(r => Number(r.step)===26)) {          // 올릴 번호들
  const blob = await (await fetch('/_refs_tmp/<이름>/' + r.file, { cache: 'no-store' })).blob();
  const img = await new Promise((ok, no) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = no; fr.readAsDataURL(blob); });
  await b.refStore.save('cubo-2-dropchecker', Number(r.step), Number(r.idx), img, r.note);   // (조립도 id, 번호, idx, 그림, 설명) — 같은 (번호, idx) 는 덮어쓴다
  out.push([r.step, r.idx, r.file, blob.size]);
}
JSON.stringify(out)
```
```bash
rm -rf public/_refs_tmp/<이름>; rmdir public/_refs_tmp 2>/dev/null     # 올린 뒤 지운다
```
확인: MCP `get_rows` table `ivs_assembly_refs` select `step,idx,note` filter `{"assembly_id":"cubo-2-dropchecker","step":"26"}` order_by `idx` (이 표엔 `created_at` 이 없어서 order_by 를 안 주면 오류), 화면 새로고침 후 번호의 `🖼N` 버튼 숫자. 삭제는 MCP `delete_row`(id 는 `select id` 로 먼저 읽는다) — 사용자 확인 뒤에만.

## 4. 데이터를 고친 뒤 화면에 다시 불러오기
`python build.py <이름> --write` → 브라우저 `navigate` 로 설계 화면을 새로 연다 → 1번. (전체 새로고침이 안 먹는 옛 상황이 있었으면 `design-assemblies.js` 를 `fetch('/design-assemblies.js?cb='+Date.now())` 후 `(0,eval)` 하고 차시를 다른 차시로 바꿨다 돌아온다.)

## 5. 화살표 개수를 데이터로 센다 (눈으로 센 것과 같이 적는다)
```bash
python - <<'EOF'
import json
a=json.load(open('scripts/assembly-tools/<이름>_asm.json',encoding='utf-8'))['steps'][25]   # 번호-1
for p in a['parts']: print(p.get('n') or p.get('name'), 'hover',p.get('hover'), 'marks',len(p.get('marks') or []))
EOF
```
`marks` 의 수 = 그 부품이 그리는 안내 화살표 수(띄운 부품만 화면에 나온다. 꽂힌 채(seated) 둔 부품은 화살표가 없다).
