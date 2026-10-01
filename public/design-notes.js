// 스케치북 위에 손으로 그리기·메모 붙이기 — 화면 위에 겹치는 얇은 층이라 3D 부품·저장 데이터에는 영향이 없다(저장되지 않음).
// 켜면 스케치북 드래그가 "회전" 대신 "그리기"가 되고, 끄면 그림·메모는 그대로 보이면서 다시 3D를 돌릴 수 있다.
(function () {
  const wrap = document.querySelector('.scene-wrap');
  if (!wrap) return;

  const COLORS = ['#e53935', '#1e88e5', '#43a047', '#111111'];
  let mode = null, color = COLORS[0], width = 4, erasing = false;

  // 그림 층(캔버스) + 메모 층
  const cv = document.createElement('canvas');
  cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none;touch-action:none;';
  const noteLayer = document.createElement('div');
  noteLayer.style.cssText = 'position:absolute;inset:0;z-index:1;pointer-events:none;overflow:hidden;';
  wrap.appendChild(cv); wrap.appendChild(noteLayer);
  const ctx = cv.getContext('2d');

  function fit() {
    const r = wrap.getBoundingClientRect(), d = window.devicePixelRatio || 1;
    if (!r.width) return;
    const w = Math.round(r.width * d), h = Math.round(r.height * d);
    if (cv.width === w && cv.height === h) return;
    const keep = cv.width ? ctx.getImageData(0, 0, cv.width, cv.height) : null;
    cv.width = w; cv.height = h;
    if (keep) { const t = document.createElement('canvas'); t.width = keep.width; t.height = keep.height; t.getContext('2d').putImageData(keep, 0, 0); ctx.drawImage(t, 0, 0); }
  }
  new ResizeObserver(fit).observe(wrap); fit();

  // 버튼
  // 스케치북 아래쪽 오른쪽 끝에 둔다(위쪽 버튼 줄은 "스케치북" 글자와 겹친다)
  const dock = document.createElement('div');
  dock.style.cssText = 'position:absolute;right:10px;bottom:10px;z-index:5;display:flex;gap:6px;';
  wrap.appendChild(dock);
  function mkBtn(text, title) {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = text; b.title = title; b.setAttribute('aria-pressed', 'false');
    b.style.cssText = 'padding:6px 12px;font-size:12px;font-weight:600;border-radius:999px;background:var(--panel);border:1px solid var(--panel-border);color:var(--ink);';
    dock.appendChild(b); return b;
  }
  const markBtn = mkBtn('📍 표시 옮기기', '초록 구멍 표시를 잡아 끌면 옮긴 자리에 주황 표시가 생겨요(저장 안 됨, 캡처용)'); markBtn.id = 'asmMarkMove2'; markBtn.hidden = true; // 조립 보기 중에만 보인다(design-assembly.js)
  const shotBtn = mkBtn('📸 스샷', '옮긴 표시를 번호와 이동 목록을 붙여 사진으로 복사·저장해요'); shotBtn.id = 'asmMarkShot'; shotBtn.hidden = true; // 조립 보기 중에만 보인다(design-assembly.js)
  const drawBtn = mkBtn('✏️ 그리기', '켜고 스케치북 위에 손으로 그려요');
  const memoBtn = mkBtn('📝 메모', '켜고 스케치북을 누르면 메모지가 붙어요');

  // 그리기 옵션줄
  const bar = document.createElement('div');
  bar.style.cssText = 'position:absolute;right:10px;top:76px;z-index:5;display:none;flex-direction:column;gap:6px;align-items:center;padding:8px 6px;border-radius:16px;background:var(--panel);border:1px solid var(--panel-border);box-shadow:var(--shadow);font-size:12px;';
  const swatches = COLORS.map((c) => {
    const s = document.createElement('button');
    s.type = 'button'; s.title = '색'; s.style.cssText = 'width:22px;height:22px;padding:0;border-radius:50%;border:2px solid #fff;outline:1px solid var(--panel-border);background:' + c + ';';
    s.onclick = () => { color = c; erasing = false; sync(); };
    bar.appendChild(s); return s;
  });
  function opt(text, title, fn) {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = text; b.title = title;
    b.style.cssText = 'padding:4px 9px;font-size:12px;font-weight:600;border-radius:999px;background:var(--panel);border:1px solid var(--panel-border);color:var(--ink);';
    b.onclick = fn; bar.appendChild(b); return b;
  }
  const thin = opt('가늘게', '선 굵기', () => { width = width === 4 ? 9 : 4; thin.textContent = width === 4 ? '가늘게' : '굵게'; });
  const eraser = opt('🧽 지우개', '그린 선을 지워요', () => { erasing = !erasing; sync(); });
  opt('🗑 모두 지우기', '그림과 메모를 싹 지워요', () => { ctx.clearRect(0, 0, cv.width, cv.height); noteLayer.innerHTML = ''; });
  wrap.appendChild(bar);

  function sync() {
    drawBtn.classList.toggle('on', mode === 'draw'); drawBtn.setAttribute('aria-pressed', mode === 'draw');
    memoBtn.classList.toggle('on', mode === 'memo'); memoBtn.setAttribute('aria-pressed', mode === 'memo');
    bar.style.display = mode === 'draw' ? 'flex' : 'none';
    drawBtn.style.background = mode === 'draw' ? 'var(--blueprint)' : 'var(--panel)'; drawBtn.style.color = mode === 'draw' ? '#fff' : 'var(--ink)';
    memoBtn.style.background = mode === 'memo' ? 'var(--blueprint)' : 'var(--panel)'; memoBtn.style.color = mode === 'memo' ? '#fff' : 'var(--ink)';
    swatches.forEach((s, i) => { s.style.outline = (!erasing && COLORS[i] === color) ? '2px solid var(--blueprint)' : '1px solid var(--panel-border)'; });
    eraser.style.background = erasing ? 'var(--blueprint)' : 'var(--panel)'; eraser.style.color = erasing ? '#fff' : 'var(--ink)';
    // 켜져 있는 동안만 이 층이 마우스를 받는다(3D 회전 대신)
    cv.style.pointerEvents = mode === 'draw' ? 'auto' : 'none';
    cv.style.cursor = mode === 'draw' ? 'crosshair' : '';
    noteLayer.style.pointerEvents = mode === 'memo' ? 'auto' : 'none';
    noteLayer.style.cursor = mode === 'memo' ? 'copy' : '';
    noteLayer.querySelectorAll('.ivs-note').forEach((n) => { n.style.pointerEvents = 'auto'; });
  }
  function setMode(m) { mode = mode === m ? null : m; sync(); }
  drawBtn.onclick = () => setMode('draw');
  // 메모 버튼을 누르면 바로 메모지가 스케치북 가운데쯤에 나온다(누를 때마다 하나씩, 조금씩 비껴서). 끌어서 옮기고 ✕로 지운다.
  let memoCount = 0;
  memoBtn.onclick = () => {
    const w = noteLayer.clientWidth || 300, h = noteLayer.clientHeight || 300, k = memoCount++ % 6;
    addNote(Math.max(8, w / 2 - 70 + k * 18), Math.max(8, h / 3 + k * 18));
  };

  // 그리기
  let last = null;
  function pt(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * cv.width / r.width, (e.clientY - r.top) * cv.height / r.height]; }
  cv.addEventListener('pointerdown', (e) => { if (mode !== 'draw') return; e.preventDefault(); e.stopPropagation(); cv.setPointerCapture(e.pointerId); last = pt(e); stroke(last, last); });
  cv.addEventListener('pointermove', (e) => { if (!last) return; const p = pt(e); stroke(last, p); last = p; });
  const end = () => { last = null; };
  cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
  function stroke(a, b) {
    const d = window.devicePixelRatio || 1;
    ctx.save();
    ctx.globalCompositeOperation = erasing ? 'destination-out' : 'source-over';
    ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.lineWidth = (erasing ? 22 : width) * d;
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0] + 0.01, b[1]); ctx.stroke();
    ctx.restore();
  }

  // 메모: 빈 곳을 누르면 메모지가 생긴다. 윗줄을 끌어 옮기고 ✕로 지운다.
  noteLayer.addEventListener('pointerdown', (e) => {
    if (mode !== 'memo' || e.target !== noteLayer) return;
    e.preventDefault(); e.stopPropagation();
    const r = noteLayer.getBoundingClientRect();
    addNote(Math.min(e.clientX - r.left, r.width - 150), Math.min(e.clientY - r.top, r.height - 110));
  });
  function addNote(x, y) {
    const n = document.createElement('div');
    n.className = 'ivs-note';
    n.style.cssText = 'position:absolute;width:140px;background:#fff59d;color:#222;border-radius:6px;box-shadow:0 3px 10px rgba(0,0,0,.28);pointer-events:auto;left:' + Math.max(0, x) + 'px;top:' + Math.max(0, y) + 'px;';
    const head = document.createElement('div');
    head.style.cssText = 'display:flex;justify-content:space-between;align-items:center;height:20px;padding:0 4px 0 8px;background:#fbc02d;border-radius:6px 6px 0 0;cursor:move;font-size:11px;font-weight:700;user-select:none;touch-action:none;';
    head.textContent = '메모';
    const x1 = document.createElement('button');
    x1.type = 'button'; x1.textContent = '✕'; x1.title = '메모 지우기';
    x1.style.cssText = 'padding:0 4px;font-size:12px;background:transparent;border:0;color:#222;cursor:pointer;';
    x1.onclick = () => n.remove();
    head.appendChild(x1);
    const ta = document.createElement('textarea');
    ta.rows = 4; ta.placeholder = '메모를 쓰세요';
    ta.style.cssText = 'display:block;box-sizing:border-box;width:100%;resize:none;border:0;background:transparent;padding:6px 8px;font:13px/1.4 inherit;color:#222;outline:none;';
    n.appendChild(head); n.appendChild(ta); noteLayer.appendChild(n);
    head.addEventListener('pointerdown', (e) => {
      if (e.target === x1) return;
      e.preventDefault(); head.setPointerCapture(e.pointerId);
      const sx = e.clientX, sy = e.clientY, ox = n.offsetLeft, oy = n.offsetTop;
      const mv = (ev) => { n.style.left = Math.max(0, Math.min(noteLayer.clientWidth - n.offsetWidth, ox + ev.clientX - sx)) + 'px'; n.style.top = Math.max(0, Math.min(noteLayer.clientHeight - n.offsetHeight, oy + ev.clientY - sy)) + 'px'; };
      const up = () => { head.removeEventListener('pointermove', mv); head.removeEventListener('pointerup', up); };
      head.addEventListener('pointermove', mv); head.addEventListener('pointerup', up);
    });
    ta.addEventListener('pointerdown', (e) => e.stopPropagation());
    setTimeout(() => ta.focus(), 0);
  }
  sync();
})();
