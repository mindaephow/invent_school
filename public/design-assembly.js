// 조립 보기 — 교재 차시의 조립 순서를 단계별로(앞으로/뒤로/자동재생/역재생/번호로 바로가기) 보여준다.
// 데이터는 design-assemblies.js, 설계 화면과의 연결(부품 놓기·카메라 등)은 design.html이 만드는 window.__ivsAssemblyBridge를 쓴다.
//
// 교재 그림처럼: 지금 단계에 새로 끼우는 부품은 제자리에서 살짝 띄워 두고(끼우기 직전) 초록 화살표와 구멍 원으로
// "여기에 꽂아요"를 보여준다. 다음 단계로 넘어가면 제자리에 끼워지고, 맨 끝 "완성"에서는 전부 제자리에 놓인다.
(function () {
  const $ = (id) => document.getElementById(id);
  const PLAY_MS = 1100;
  const HOVER_RECV = 20; // 프레임 같은 '구멍 받는 부품'이 움직일 때는 더 가까이 띄운다(너무 멀면 공중에 떠 보인다)
  const HOVER = 22;      // 끼우기 직전 부품을 띄우는 거리(mm)
  const PEG_DEPTH = 5;   // 돌기가 구멍 안으로 들어가는 깊이(mm) — 프레임 두께와 같다
  let def = null;        // 지금 고른 차시에 맞는 조립 데이터
  let catId = null;      // 지금 고른 카테고리 id (부품 이름으로 부품을 찾을 때 씀)
  let lastView = 0;      // 지금 보고 있는 각도(90도 단위)
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
        // 옆자리 조립품이 제자리로 합쳐지는 단계(settle)에는 settleDir(없으면 dir)로 띄우고, settleMarks(있는 부품만) 자리로 안내한다
        const settling = !!(pt.side && !useSide);
        const dirH = settling ? (pt.settleDir || pt.dir) : pt.dir;
        // 앞 단계에서 만든 부품을 이번 단계에서 "결합되기 전" 모습으로 띄워 보여준다(예: 14단계 T축+기어를 15프레임 위로)
        const ex = pt.explode && pt.explode.step === target ? pt.explode : null;
        if (ex) {
          pos = add(base, ex.offset, 1);
          (ex.marks || []).forEach((m) => guides.push({ from: ex.from, to: m, dir: [0, -1, 0], idx: list.length }));
        }
        if (isNew && dirH) {
          // 띄우는 거리·돌기가 들어가는 깊이·판 두께는 부품마다 정할 수 있다(T축처럼 길게 꽂히는 것, 두꺼운 부시)
          const hv = settling ? HOVER : (pt.hover || (pt.recv ? HOVER_RECV : HOVER)); // 합쳐지는 묶음은 모두 같은 거리로 띄워야 모양이 흐트러지지 않는다
          const depth = pt.pegDepth || PEG_DEPTH;
          pos = add(base, dirH, hv); // 끼우기 직전: 제자리에서 끼우는 방향으로 띄운다
          const targets = settling ? (pt.settleMarks || []) : (pt.marks && pt.marks.length ? pt.marks : [base]);
          // 화살표는 띄워 놓은 부품의 돌기 끝(구멍에 들어갈 깊이만큼 아래)에서 시작해 구멍 위 원으로 들어간다
          if (pt.recv) {
            // 구멍을 받는 부품(프레임 등)이 움직일 때: 원은 떠 있는 부품의 구멍에, 화살표는 고정된 돌기 끝에서 그 구멍 쪽으로
            // faceMarks: 돌기 끝이 판 바깥 면과 같은 높이가 아닐 때, 제자리에 끼운 뒤 판 바깥 면의 구멍 자리
            const faces = !settling && pt.faceMarks ? pt.faceMarks : targets;
            targets.forEach((m, i) => guides.push({ from: m, to: add(faces[i] || m, dirH, hv), dir: dirH, idx: list.length, both: pt.thick || 5 }));
          } else {
            targets.forEach((m) => guides.push({ from: add(m, dirH, hv - depth), to: m, dir: dirH, idx: list.length }));
          }
        }
        list.push({ name: pt.n, type, mount: 'floor', pos: pos.slice(), quat: b.quat(rot), rot: rot.slice(), isNew, final: (isNew && dirH) || ex ? base.slice() : null }); // ex: 14단계처럼 "결합 전"으로 띄운 부품도 제자리(결합 후)가 있다
      });
    });
    return { list, guides, missing, targets: list.map((d) => d.final || null) };
  }

  // 1, 2, 3 … 단계 번호 버튼(+ 마지막 "완성") — 눌러서 그 단계로 바로 가고, 지금 단계는 진하게 보인다.
  function buildStepButtons() {
    [$('asmSteps'), $('asmStageSteps')].forEach((box) => {
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
    });
  }
  // 왼쪽 카드의 "조립 순서" 목록 — 조립 보기를 열기 전에도 항상 보이고, 누르면 그 단계로 간다.
  function buildOrderList() {
    const ol = $('asmOrderList');
    ol.innerHTML = '';
    if (!def) return;
    def.steps.forEach((s, i) => {
      const li = document.createElement('li');
      const b = document.createElement('button');
      b.type = 'button';
      b.dataset.step = String(i + 1);
      b.className = 'ghost';
      b.style.cssText = 'width:100%; text-align:left; padding:3px 8px; border-radius:8px; font-size:12.5px; font-weight:400;';
      b.textContent = (i + 1) + '. ' + (s.note || '');
      li.appendChild(b);
      ol.appendChild(li);
    });
  }
  function markStepButtons() {
    document.querySelectorAll('#asmOrderList button').forEach((b) => {
      const cur = Number(b.dataset.step) === step;
      b.style.fontWeight = cur ? '800' : '400';
      b.style.background = cur ? 'var(--blueprint, #2b6be0)' : '';
      b.style.color = cur ? '#fff' : '';
      b.setAttribute('aria-current', cur ? 'step' : 'false');
    });
    document.querySelectorAll('#asmSteps button, #asmStageSteps button').forEach((b) => {
      const n = Number(b.dataset.step);
      const cur = n === step;
      b.className = cur ? 'primary' : 'ghost';
      b.style.opacity = n < step ? '0.75' : '1'; // 이미 지나온 단계는 살짝 연하게
      b.setAttribute('aria-current', cur ? 'step' : 'false');
    });
    // 화면 위 단계 줄: 지금 단계가 가운데 오게 옆으로 밀어 준다
    const box = $('asmStageSteps'), curBtn = box.querySelector('button[aria-current="step"]');
    if (curBtn) box.scrollLeft = curBtn.offsetLeft - box.clientWidth / 2 + curBtn.offsetWidth / 2;
  }

  function render() {
    const b = bridge();
    const { list, guides, missing, targets } = buildList(step);
    b.show(list.map(({ isNew, name, final, ...d }) => d), targets);
    // 지금 단계에 보이는 부품(끼우기 직전 위치 포함)에 카메라를 맞춘다 — 처음부터 너무 멀리서 보이지 않게
    // 이번 단계에 끼우는 부품과 그 끼워지는 자리를 화면 가운데에 크게 보여준다(나머지 부품은 배경)
    const focus = list.filter((d) => d.isNew).map((d) => d.pos).concat(guides.map((g) => g.to));
    b.frame(focus.length ? focus : list.map((d) => d.pos), list.map((d) => d.pos));
    b.guides(guides);
    // 앞 벽이 뒤쪽 끝에 있는 단계(flip)는 반대편에서 보여준다
    const view = (step > 0 && step < last() && def.steps[step - 1].view) || 0; // 0: 기본 각도, 1·2: 90도씩 돌려서(부품이 들어오는 쪽에서) 보여준다
    if (b.turn && def.camera && view !== lastView) { b.turn(def.camera.theta + view * Math.PI / 2); lastView = view; } // 각도가 바뀌는 단계에서만 돌린다(직접 돌린 화면은 그대로)
    const n = total();
    $('asmLabel').textContent = step === 0 ? '시작 전' : (step === last() ? '완성!' : step + ' / ' + n + ' 단계');
    $('asmNote').textContent = step === 0 ? '빈 판에서 시작해요. ▶ 를 눌러 한 단계씩 만들어 봐요.'
      : (step === last() ? '완성! 부품이 모두 제자리에 끼워졌어요.' : (def.steps[step - 1].note || ''));
    $('asmSlider').value = String(step);
    $('asmStageNote').textContent = step === last() ? $('asmNote').textContent : $('asmLabel').textContent + ' · ' + $('asmNote').textContent;
    markStepButtons();
    $('asmFirst').disabled = $('asmPrev').disabled = step === 0;
    $('asmNext').disabled = $('asmLast').disabled = step === last();
    if (missing.length) $('asmNote').textContent += ' (부품을 못 찾았어요: ' + missing.join(', ') + ')';
  }

  function stop() {
    clearInterval(timer); clearTimeout(timer); timer = null; timerDir = 0;
    $('asmPlay').textContent = '▶ 재생';
    $('asmReverse').textContent = '◀ 역재생';
    const br = bridge(); if (br && br.guideDots) br.guideDots(true); // 멈추면 초록 점이 다시 보인다
  }
  function go(target) {
    step = Math.max(0, Math.min(last(), target));
    render();
  }
  // 재생: 화살표 표시 → 결합 → 다음 단계 화살표 표시 → 결합 … 을 쭉 이어서 보여준다(재생 중에는 초록 점을 숨기고 화살표만).
  // 역재생은 단계를 거꾸로 한 칸씩 넘긴다.
  const ARROW_MS = 1100, JOIN_MS = 700;
  // 재생 속도(0.5×~3×): 숫자가 클수록 빠르다. 재생 도중에 바꿔도 다음 단계부터 바로 적용된다.
  let speed = 1;
  try { const v = Number(localStorage.getItem('ivs-asm-speed')); if (v >= 0.5 && v <= 3) speed = v; } catch (e) { /* 저장 못 해도 기본 속도 */ }
  const arrowMs = () => ARROW_MS / speed, joinMs = () => JOIN_MS / speed;
  function play(dir) {
    const wasPlaying = timerDir === dir;
    stop();
    if (wasPlaying) return; // 같은 재생 버튼을 다시 누르면 멈춤
    const b = bridge();
    if (dir > 0 && step >= last()) step = 0;
    if (dir < 0 && step <= 0) step = last();
    if (dir > 0 && step === 0) step = 1; // 빈 판에서 바로 첫 단계 화살표부터
    render();
    timerDir = dir;
    if (b && b.guideDots) b.guideDots(false); // 재생 중에는 화살표만(초록 점 숨김)
    if (dir > 0) {
      $('asmPlay').textContent = '⏸ 멈춤';
      const tick = () => {
        if (timerDir !== 1) return;
        const jm = joinMs(); if (b.combineNew) b.combineNew(Math.max(150, jm - 150)); // 결합
        timer = setTimeout(() => {
          if (timerDir !== 1) return;
          const next = step + 1;
          if (next > last()) { stop(); return; }
          go(next); // 다음 단계 화살표 표시
          if (next === last()) { stop(); return; }
          timer = setTimeout(tick, arrowMs());
        }, jm);
      };
      timer = setTimeout(tick, arrowMs());
    } else {
      $('asmReverse').textContent = '⏸ 멈춤';
      const back = () => {
        if (timerDir !== -1) return;
        const next = step - 1;
        if (next < 0) { stop(); return; }
        go(next);
        if (next === 0) { stop(); return; }
        timer = setTimeout(back, PLAY_MS / speed);
      };
      timer = setTimeout(back, PLAY_MS / speed);
    }
  }

  async function open() {
    const b = bridge();
    if (!def || !b) return;
    b.status('3D 부품을 불러오는 중이에요...', null);
    // 등록된 3D 모델을 먼저 받아 두면 부품이 처음부터 제 모양으로 나온다(받는 동안 단순 모양이 잠깐 보이는 것을 막음)
    const names = [...new Set(def.steps.flatMap((s) => (s.parts || []).map((pt) => pt.n)))];
    try { await b.preload(names, catId); } catch (e) { /* 못 받아도 단순 모양으로 계속 보여준다 */ }
    if (!def || viewing) return;
    snapshot = b.serialize();
    viewing = true;
    lastView = 0;
    b.setViewing(true);
    b.camera(def.camera);
    $('asmBar').hidden = false;
    $('asmStageBar').hidden = false;
    $('historyPanel').hidden = true;
    b.axes(true);
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
    $('asmStageBar').hidden = true;
    $('historyPanel').hidden = false;
    if (b) b.axes(false);
    if (b) { b.guides([]); b.restore(snapshot || []); b.setViewing(false); }
    snapshot = null;
  }

  function stopPlayClick(fn) { return () => { stop(); fn(); }; }
  document.addEventListener('DOMContentLoaded', () => {
    if (!$('asmClose')) return;
    $('asmClose').addEventListener('click', close);
    $('asmFirst').addEventListener('click', stopPlayClick(() => go(0)));
    $('asmPrev').addEventListener('click', stopPlayClick(() => go(step - 1)));
    $('asmNext').addEventListener('click', stopPlayClick(() => go(step + 1)));
    $('asmLast').addEventListener('click', stopPlayClick(() => go(last())));
    const sp = $('asmSpeed'), spl = $('asmSpeedLabel');
    if (sp) { sp.value = String(speed); spl.textContent = speed + '×'; sp.addEventListener('input', () => { speed = Number(sp.value) || 1; spl.textContent = speed + '×'; try { localStorage.setItem('ivs-asm-speed', String(speed)); } catch (e) { /* 저장 못 해도 계속 */ } }); }
    $('asmPlay').addEventListener('click', () => play(1));
    $('asmReverse').addEventListener('click', () => play(-1));
    $('asmSlider').addEventListener('input', (e) => { stop(); go(Number(e.target.value)); });
    $('asmCombine').addEventListener('click', () => {
      const r = bridge().combineSelected();
      if (r === 'none') bridge().status('먼저 끼울 부품을 눌러서 고르세요.', 'warn');
      else if (r === 'notTarget') bridge().status('이 부품은 이번 단계에서 끼우는 부품이 아니에요. 떠 있는 부품을 눌러 보세요.', 'warn');
    });
    $('asmReset').addEventListener('click', () => { stop(); go(step); });
    $('asmOrderList').addEventListener('click', async (e) => {
      const b = e.target.closest('button[data-step]');
      if (!b) return;
      stop();
      const n = Number(b.dataset.step);
      if (!viewing) await open();
      if (viewing) go(n);
    });
    $('asmStagePrev').addEventListener('click', stopPlayClick(() => go(step - 1)));
    $('asmStageNext').addEventListener('click', stopPlayClick(() => go(step + 1)));
    $('asmStageSteps').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-step]');
      if (b) { stop(); go(Number(b.dataset.step)); }
    });
    $('asmSteps').addEventListener('click', async (e) => {
      const b = e.target.closest('button[data-step]');
      if (!b) return;
      stop();
      const n = Number(b.dataset.step);
      if (!viewing) await open();
      if (viewing) go(n);
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
      buildOrderList();
      if (def) buildStepButtons(); // 번호 줄도 조립 보기를 열기 전부터 보인다
      $('asmRules').innerHTML = (window.IVS_ASSEMBLY_RULES || []).map((r) => '<li>' + r + '</li>').join('');
    },
    isViewing() { return viewing; },
  };
})();
