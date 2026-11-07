# 화면(조립 보기) 조작 코드 모음 — 브라우저 패널의 `javascript_tool` 에 그대로 붙여 실행한다 (2026-10-13)

화면을 접거나 카메라를 바꿔 확인했으면 끝난 뒤 기본 모습(왼쪽 패널 펼침·번호판 보임·카메라/패널/관절 표시 손대지 않은 상태)으로 되돌리고, 사용자가 시키지 않으면 화면을 조작하지 않는다 → `큐보 부품결합규칙.md` J1·J2.

전제: 개발 서버·로그인은 `CLAUDE.md` "세션을 시작할 때" 2~3번대로 되어 있다. 브라우저 패널은 `mcp__Claude_Browser__navigate` 로 그 개발 서버 주소를 연다. 화면은 오래 열어 둔 채로 두지 말고 **데이터를 고친 뒤에는 새로 불러온다**(navigate 다시).

## 1. 번호 N 을 연다 (권·차시는 조립도마다 다르다 — `list_assemblies` 로 읽는다)
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
- 카메라는 사용자가 📷 로 저장한 시점이 코드 시점보다 우선한다(규칙 B3·E8). `camState()` 의 theta·phi 가 코드(`A.steps[N-1].cam`)와 다르면 사용자 저장 시점이다 — 책과 같은 시점으로 비교하려면 아래 2번으로 맞춘다.

## 2. 카메라를 책 시점으로 맞추고 확대한다 (비교용 — 저장하지 않는다)
`number_start` 의 "사용자 📷 카메라" 줄을 먼저 본다 — 사용자가 저장한 시점이 있으면 `br.camera` 로 덮어쓰지 말고 번호를 연 그대로(`camState()` 가 그 값) 찍어 비교하고 코드 `cam` 도 그 값에 맞춘다(규칙 B3·E8). 아래 값은 사용자 기록이 없을 때만 쓴다.
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

**3-1. 올린 뒤에는 화면을 `navigate` 로 새로 불러와 🖼 배지로 확인한다(규칙 I1·J2).** 번호 버튼 옆 🖼N 배지는 차시를 열 때 읽으므로 그 번호를 눌러 배지 숫자(그림 장수)가 올린 장수와 같은지 본다. 안 뜨면 올린 것이 아니다.

## 4. 데이터를 고친 뒤 화면에 다시 불러오기
`python build.py <이름> --write` → 브라우저 `navigate` 로 설계 화면을 새로 연다 → 1번.

## 5. 화살표 개수를 데이터로 센다 (눈으로 센 것과 같이 적는다)
```bash
python - <<'EOF'
import json
a=json.load(open('scripts/assembly-tools/<이름>_asm.json',encoding='utf-8'))['steps'][25]   # 번호-1
for p in a['parts']: print(p.get('n') or p.get('name'), 'hover',p.get('hover'), 'marks',len(p.get('marks') or []))
EOF
```
`marks` 의 수 = 그 부품이 그리는 안내 화살표 수(띄운 부품만 화면에 나온다. 꽂힌 채(seated) 둔 부품은 화살표가 없다).

## 6. 연결점(초록 점)이 부품에서 떠 있는지 화면 장면에서 숫자로 잰다 (G23)
번호 버튼을 하나씩 눌러(번호마다 2초 기다린 뒤) 초록 점(`userData.dot`) 마다 가장 가까운 부품(`userData.partRef` 메시) 꼭짓점까지 거리를 잰다. 4mm 넘으면 떠 있는 점이다. `javascript_tool` 로 한 번에 12번호 안쪽(45초 제한)씩 돌린다 — 화면을 새로 불러온 직후엔 장면을 먼저 잡는다(`THREE` 는 r128 전역 `window.THREE`, 모듈 `three` 가 아니다).
```js
const T=window.THREE, o=T.Object3D.prototype.updateMatrixWorld;
T.Object3D.prototype.updateMatrixWorld=function(f){let r=this;while(r.parent)r=r.parent;if(r.isScene||r.type==='Scene')window.__sc=r;return o.apply(this,arguments)};
window.__measure=function(){const sc=window.__sc;sc.updateMatrixWorld(true);const dots=[],parts=[];sc.traverse(o=>{if(!o.isMesh||!o.visible)return;if(o.userData.dot)dots.push(o);else if(o.userData.partRef)parts.push(o)});
 const V=new T.Vector3(),pts=[];parts.forEach(m=>{const p=m.geometry.attributes.position;if(!p)return;for(let i=0;i<p.count;i++){V.fromBufferAttribute(p,i).applyMatrix4(m.matrixWorld);pts.push(V.x,V.y,V.z)}});
 const far=[];dots.forEach(d=>{const w=new T.Vector3();d.getWorldPosition(w);let b=1e9;for(let j=0;j<pts.length;j+=3){const dx=pts[j]-w.x,dy=pts[j+1]-w.y,dz=pts[j+2]-w.z;b=Math.min(b,dx*dx+dy*dy+dz*dz)}b=Math.sqrt(b);if(b>4)far.push([w.x,w.y,w.z].map(v=>+v.toFixed(0)).concat(+b.toFixed(1)))});return {n:dots.length,far}};
window.__go=async function(ks){const bt=[...document.querySelectorAll('button')].filter(b=>/^\d+$/.test(b.textContent.trim()));const out={};for(const k of ks){bt.find(x=>x.textContent.trim()==String(k)).click();await new Promise(r=>setTimeout(r,2000));const m=window.__measure();out[k]=m.n+' dots, far '+m.far.length+(m.far.length?' '+JSON.stringify(m.far[0]):'')}return out};
// 사용: JSON.stringify(await window.__go([1,2,3,4,5,6,7,8,9,10,11,12]))
```
원인 찾는 법: 점이 부품 가장자리에서 떨어져 있으면 `guide` 공식(design-assembly.js 536~575줄)의 받는 쪽(recv) `to = faceMarks(없으면 marks) + dir×hover` 가 떠 있는 부품 구멍과 같은지 본다. 옆자리(`side`)에서 새로 놓이는 묶음(풍차 11·16·17번)은 `hover`·`joinOrder`(보통 모드)가 쓰이고 `settleHover`·`settleOrder` 는 합치는 번호(side.until)에서만 쓰인다.

