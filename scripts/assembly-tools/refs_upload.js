// 교재 참고 그림을 화면(관리자 로그인)에서 표 ivs_assembly_refs 에 올린다 — 브라우저 콘솔(또는 Claude 의 javascript_tool)에서 실행.
// 1) supabase/assembly_refs.sql 을 Supabase SQL 에디터에서 한 번 실행해 둔다(표가 있어야 한다).
// 2) python refs_make.py <이름> 으로 refs/<이름>/ 을 만든 뒤, 그 폴더를 public/_refs_tmp/<이름>/ 으로 잠깐 복사한다(같은 주소에서 받아 올리려고. 올린 뒤 지운다 — 커밋 금지).
// 3) 로컬 개발 서버의 설계 화면(/design.html?subject=robot)에 관리자로 로그인한 뒤 이 파일 내용을 실행한다: await window.__ivsRefsUpload('kidknight', 'cubo-1-kidknight')
window.__ivsRefsUpload = async function (name, assemblyId, steps) { // steps: 올릴 단계 번호 배열(생략하면 index.json 전부)
  const b = window.__ivsAssemblyBridge; if (!b || !b.refStore) throw new Error('조립 보기 화면이 아니에요.');
  const index = await (await fetch('/_refs_tmp/' + name + '/index.json', { cache: 'no-store' })).json();
  let n = 0;
  for (const r of index.filter(r => !steps || steps.includes(r.step))) {
    const blob = await (await fetch('/_refs_tmp/' + name + '/' + r.file, { cache: 'no-store' })).blob();
    const img = await new Promise((ok, no) => { const fr = new FileReader(); fr.onload = () => ok(fr.result); fr.onerror = no; fr.readAsDataURL(blob); });
    await b.refStore.save(assemblyId, r.step, r.idx, img, r.note);
    n++;
  }
  return n + '장 올림';
};
