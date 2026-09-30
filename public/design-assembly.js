// 조립 보기 — 교재 차시의 조립 순서를 단계별로(앞으로/뒤로/자동재생/역재생) 보여준다.
// 데이터는 design-assemblies.js, 설계 화면과의 연결(부품 놓기·카메라 등)은 design.html이 만드는 window.__ivsAssemblyBridge를 쓴다.
(function () {
  const $ = (id) => document.getElementById(id);
  const PLAY_MS = 1100;
  let def = null;        // 지금 고른 차시에 맞는 조립 데이터
  let catId = null;      // 지금 고른 카테고리 id (부품 이름으로 부품을 찾을 때 씀)
  let viewing = false;   // 조립 보기 중인지
  let step = 0;          // 0 = 빈 판, N = 완성
  let snapshot = null;   // 조립 보기 들어가기 전 작업(닫으면 그대로 되돌린다)
  let timer = null;      // setInterval 번호
  let timerDir = 0;      // 자동재생 방향(1 앞으로, -1 뒤로, 0 멈춤)

  function bridge() { return window.__ivsAssemblyBridge; }
  function total() { return def ? def.steps.length : 0; }

  // step 단계까지의 부품 목록을 만든다. 각 항목에 이번 단계에 새로 놓이거나 제자리로 들어간 것인지(isNew)도 적는다.
  function buildList(target) {
    const b = bridge();
    const list = [];
    const missing = [];
    def.steps.slice(0, target).forEach((s, si) => {
      (s.parts || []).forEach((pt) => {
        const type = b.resolve(pt.n, catId);
        if (!type) { if (!missing.includes(pt.n)) missing.push(pt.n); return; }
        const useSide = pt.side && target < pt.side.until;
        const pos = useSide ? pt.side.p : pt.p;
        const rot = useSide ? pt.side.r : pt.r;
        const isNew = si + 1 === target || (pt.side && pt.side.until === target);
        list.push({ name: pt.n, type, mount: 'floor', pos: pos.slice(), quat: b.quat(rot), rot: rot.slice(), isNew });
      });
    });
    return { list, missing };
  }

  function render() {
    const b = bridge();
    const { list, missing } = buildList(step);
    b.show(list.map(({ isNew, name, ...d }) => d));
    b.tint(list.map((d) => (def.colors && def.colors[d.name]) || null));
    b.highlight(list.map((d, i) => (d.isNew ? i : -1)).filter((i) => i >= 0));
    const n = total();
    $('asmLabel').textContent = step === 0 ? '시작 전' : (step === n ? '완성!' : step + ' / ' + n + ' 단계');
    $('asmNote').textContent = step === 0 ? '빈 판에서 시작해요. ▶ 를 눌러 한 단계씩 만들어 봐요.' : (def.steps[step - 1].note || '');
    $('asmSlider').value = String(step);
    $('asmFirst').disabled = $('asmPrev').disabled = step === 0;
    $('asmNext').disabled = $('asmLast').disabled = step === n;
    if (missing.length) $('asmNote').textContent += ' (부품을 못 찾았어요: ' + missing.join(', ') + ')';
  }

  function stop() {
    clearInterval(timer); timer = null; timerDir = 0;
    $('asmPlay').textContent = '▶ 재생';
    $('asmReverse').textContent = '◀ 역재생';
  }
  function go(target) {
    step = Math.max(0, Math.min(total(), target));
    render();
  }
  function play(dir) {
    const n = total();
    const wasPlaying = timerDir === dir;
    stop();
    if (wasPlaying) return; // 같은 재생 버튼을 다시 누르면 멈춤
    if (dir > 0 && step >= n) step = 0;
    if (dir < 0 && step <= 0) step = n;
    render();
    timerDir = dir;
    timer = setInterval(() => {
      const next = step + dir;
      if (next < 0 || next > n) { stop(); return; }
      go(next);
      if (next === 0 || next === n) stop();
    }, PLAY_MS);
    if (dir > 0) $('asmPlay').textContent = '⏸ 멈춤'; else $('asmReverse').textContent = '⏸ 멈춤';
  }

  async function open() {
    const b = bridge();
    if (!def || !b) return;
    $('asmOpen').disabled = true;
    b.status('3D 부품을 불러오는 중이에요...', null);
    // 등록된 3D 모델을 먼저 받아 두면 부품이 처음부터 제 모양으로 나온다(받는 동안 단순 모양이 잠깐 보이는 것을 막음)
    const names = [...new Set(def.steps.flatMap((s) => (s.parts || []).map((pt) => pt.n)))];
    try { await b.preload(names, catId); } catch (e) { /* 못 받아도 단순 모양으로 계속 보여준다 */ }
    $('asmOpen').disabled = false;
    if (!def || viewing) return;
    snapshot = b.serialize();
    viewing = true;
    b.setViewing(true);
    b.camera(def.camera);
    $('asmBar').hidden = false;
    $('asmOpen').hidden = true;
    $('asmSlider').max = String(total());
    go(total()); // 처음엔 완성된 모습부터 보여준다
    b.status('조립 보기 중이에요. 닫으면 하던 작업으로 돌아가요.', 'success');
  }
  function close() {
    const b = bridge();
    stop();
    if (!viewing) return;
    viewing = false;
    $('asmBar').hidden = true;
    $('asmOpen').hidden = !def;
    if (b) { b.restore(snapshot || []); b.setViewing(false); }
    snapshot = null;
  }

  function stopPlayClick(fn) { return () => { stop(); fn(); }; }
  document.addEventListener('DOMContentLoaded', () => {
    if (!$('asmOpen')) return;
    $('asmOpen').addEventListener('click', open);
    $('asmClose').addEventListener('click', close);
    $('asmFirst').addEventListener('click', stopPlayClick(() => go(0)));
    $('asmPrev').addEventListener('click', stopPlayClick(() => go(step - 1)));
    $('asmNext').addEventListener('click', stopPlayClick(() => go(step + 1)));
    $('asmLast').addEventListener('click', stopPlayClick(() => go(total())));
    $('asmPlay').addEventListener('click', () => play(1));
    $('asmReverse').addEventListener('click', () => play(-1));
    $('asmSlider').addEventListener('input', (e) => { stop(); go(Number(e.target.value)); });
  });

  // 차시 카드에서 카테고리·권·차시를 바꿀 때마다 design.html이 알려준다 — 맞는 조립 데이터가 있을 때만 버튼을 보여준다.
  window.__ivsAssembly = {
    onLessonChange(cat, volume, chapterTitle) {
      const box = $('assemblyBox');
      if (!box) return;
      const title = String(chapterTitle || '').trim();
      const found = (window.IVS_ASSEMBLIES || []).find((a) => a.category === cat.name && Number(a.volume) === Number(volume) && a.chapter === title) || null;
      if (viewing && found !== def) close();
      def = found;
      catId = found ? cat.id : null;
      box.hidden = !found;
      if (!viewing) $('asmOpen').hidden = !found;
    },
    isViewing() { return viewing; },
  };
})();
