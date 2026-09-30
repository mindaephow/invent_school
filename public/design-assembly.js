// 조립 보기 — 교재 차시의 조립 순서를 단계별로(앞으로/뒤로/자동재생/역재생/번호로 바로가기) 보여준다.
// 데이터는 design-assemblies.js, 설계 화면과의 연결(부품 놓기·카메라 등)은 design.html이 만드는 window.__ivsAssemblyBridge를 쓴다.
//
// 교재 그림처럼: 지금 단계에 새로 끼우는 부품은 제자리에서 살짝 띄워 두고(끼우기 직전) 초록 화살표와 구멍 원으로
// "여기에 꽂아요"를 보여준다. 다음 단계로 넘어가면 제자리에 끼워지고, 맨 끝 "완성"에서는 전부 제자리에 놓인다.
(function () {
  const $ = (id) => document.getElementById(id);
  const PLAY_MS = 1100;
  const HOVER = 22;      // 끼우기 직전 부품을 띄우는 거리(mm)
  const PEG_DEPTH = 5;   // 돌기가 구멍 안으로 들어가는 깊이(mm) — 프레임 두께와 같다
  let def = null;        // 지금 고른 차시에 맞는 조립 데이터
  let catId = null;      // 지금 고른 카테고리 id (부품 이름으로 부품을 찾을 때 씀)
  let viewing = false;   // 조립 보기 중인지
  let step = 0;          // 0 = 빈 판, 1..N = 각 단계, N+1 = 완성
  let snapshot = null;   // 조립 보기 들어가기 전 작업(닫으면 그대로 되돌린다)
  let timer = null;      // setInterval 번호
  let timerDir = 0;      // 자동재생 방향(1 앞으로, -1 뒤로, 0 멈춤)

  function bridge() { return window.__ivsAssemblyBridge; }
  function total() { return def ? def.steps.length : 0; }
  function last() { return total() + 1; } // "완성" 단계 번호
  const add = (p, d, k) => [p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k];

  // target 단계까지의 부품 목록과, 이번 단계의 초록 안내(화살표·구멍 원)를 만든다.
  function buildList(target) {
    const b = bridge();
    const list = [];
    const guides = [];
    const missing = [];
    const n = total();
    const upTo = Math.min(target, n);
    def.steps.slice(0, upTo).forEach((s, si) => {
      (s.parts || []).forEach((pt) => {
        const type = b.resolve(pt.n, catId);
        if (!type) { if (!missing.includes(pt.n)) missing.push(pt.n); return; }
        const useSide = pt.side && upTo < pt.side.until;
        const base = useSide ? pt.side.p : pt.p;
        const rot = useSide ? pt.side.r : pt.r;
        // 이번 단계에 새로 놓이거나(또는 옆자리에서 제자리로 들어가는) 부품 — 완성 단계에선 없다
        const isNew = target <= n && (si + 1 === target || (pt.side && pt.side.until === target));
        let pos = base;
        if (isNew && pt.dir) {
          pos = add(base, pt.dir, HOVER); // 끼우기 직전: 제자리에서 끼우는 방향으로 띄운다
          // 옆자리 조립품이 제자리로 합쳐지는 단계(settle)에는 settleMarks(있는 부품만), 그 밖엔 marks, 없으면 부품 가운데
          const settling = pt.side && !useSide;
          const targets = settling ? (pt.settleMarks || []) : (pt.marks && pt.marks.length ? pt.marks : [base]);
          // 화살표는 띄워 놓은 부품의 돌기 끝(구멍에 들어갈 깊이만큼 아래)에서 시작해 구멍 위 원으로 들어간다
          targets.forEach((m) => guides.push({ from: add(m, pt.dir, HOVER - PEG_DEPTH), to: m, dir: pt.dir, idx: list.length }));
        }
        list.push({ name: pt.n, type, mount: 'floor', pos: pos.slice(), quat: b.quat(rot), rot: rot.slice(), isNew, final: isNew && pt.dir ? base.slice() : null });
      });
    });
    return { list, guides, missing, targets: list.map((d) => d.final || null) };
  }

  // 1, 2, 3 … 단계 번호 버튼(+ 마지막 "완성") — 눌러서 그 단계로 바로 가고, 지금 단계는 진하게 보인다.
  function buildStepButtons() {
    const box = $('asmSteps');
    box.innerHTML = '';
    for (let i = 1; i <= last(); i++) {
      const b = document.createElement('button');
      b.type = 'button';
      b.dataset.step = String(i);
      b.textContent = i === last() ? '완성' : String(i);
      b.title = i === last() ? '완성된 모습' : i + '단계: ' + (def.steps[i - 1].note || '');
      b.style.cssText = i === last() ? 'padding:5px 10px; font-size:13px;' : 'min-width:32px; padding:5px 0; font-size:13px;';
      box.appendChild(b);
    }
  }
  function markStepButtons() {
    document.querySelectorAll('#asmSteps button').forEach((b) => {
      const n = Number(b.dataset.step);
      const cur = n === step;
      b.className = cur ? 'primary' : 'ghost';
      b.style.opacity = n < step ? '0.75' : '1'; // 이미 지나온 단계는 살짝 연하게
      b.setAttribute('aria-current', cur ? 'step' : 'false');
    });
  }

  function render() {
    const b = bridge();
    const { list, guides, missing, targets } = buildList(step);
    b.show(list.map(({ isNew, name, final, ...d }) => d), targets);
    b.guides(guides);
    const n = total();
    $('asmLabel').textContent = step === 0 ? '시작 전' : (step === last() ? '완성!' : step + ' / ' + n + ' 단계');
    $('asmNote').textContent = step === 0 ? '빈 판에서 시작해요. ▶ 를 눌러 한 단계씩 만들어 봐요.'
      : (step === last() ? '완성! 부품이 모두 제자리에 끼워졌어요.' : (def.steps[step - 1].note || ''));
    $('asmSlider').value = String(step);
    markStepButtons();
    $('asmFirst').disabled = $('asmPrev').disabled = step === 0;
    $('asmNext').disabled = $('asmLast').disabled = step === last();
    if (missing.length) $('asmNote').textContent += ' (부품을 못 찾았어요: ' + missing.join(', ') + ')';
  }

  function stop() {
    clearInterval(timer); timer = null; timerDir = 0;
    $('asmPlay').textContent = '▶ 재생';
    $('asmReverse').textContent = '◀ 역재생';
  }
  function go(target) {
    step = Math.max(0, Math.min(last(), target));
    render();
  }
  function play(dir) {
    const wasPlaying = timerDir === dir;
    stop();
    if (wasPlaying) return; // 같은 재생 버튼을 다시 누르면 멈춤
    if (dir > 0 && step >= last()) step = 0;
    if (dir < 0 && step <= 0) step = last();
    render();
    timerDir = dir;
    timer = setInterval(() => {
      const next = step + dir;
      if (next < 0 || next > last()) { stop(); return; }
      go(next);
      if (next === 0 || next === last()) stop();
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
    $('asmSlider').max = String(last());
    buildStepButtons();
    go(last()); // 처음엔 완성된 모습부터 보여준다
    b.status('조립 보기 중이에요. 닫으면 하던 작업으로 돌아가요.', 'success');
  }
  function close() {
    const b = bridge();
    stop();
    if (!viewing) return;
    viewing = false;
    $('asmBar').hidden = true;
    $('asmOpen').hidden = !def;
    if (b) { b.guides([]); b.restore(snapshot || []); b.setViewing(false); }
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
    $('asmLast').addEventListener('click', stopPlayClick(() => go(last())));
    $('asmPlay').addEventListener('click', () => play(1));
    $('asmReverse').addEventListener('click', () => play(-1));
    $('asmSlider').addEventListener('input', (e) => { stop(); go(Number(e.target.value)); });
    $('asmCombine').addEventListener('click', () => {
      const r = bridge().combineSelected();
      if (r === 'none') bridge().status('먼저 끼울 부품을 눌러서 고르세요.', 'warn');
      else if (r === 'notTarget') bridge().status('이 부품은 이번 단계에서 끼우는 부품이 아니에요. 떠 있는 부품을 눌러 보세요.', 'warn');
    });
    $('asmReset').addEventListener('click', () => { stop(); go(step); });
    $('asmSteps').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-step]');
      if (b) { stop(); go(Number(b.dataset.step)); }
    });
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
      $('asmRules').innerHTML = (window.IVS_ASSEMBLY_RULES || []).map((r) => '<li>' + r + '</li>').join('');
      if (!viewing) $('asmOpen').hidden = !found;
    },
    isViewing() { return viewing; },
  };
})();
