// 부품 수리실의 "박스 에디터" — 예전 자유낙서 스케치북 자리를 대신한다. 박스 하나를 x/y/z(위치)·w/h/d(크기)
// 숫자로 놓고 3D로 확인한 뒤, 고른 부품의 spec.boxes에 저장한다(브라켓이 armLen1/armLen2/armWidth 숫자만으로
// 항상 똑같이 재현되는 것과 같은 방식 — svg 없이 숫자만으로 모양이 재현됨).
//
// parts-lab.html의 공용 헬퍼(baseScene 등)·adminApi는 window.__partsLab로 넘겨받는다(그 파일의 큰 IIFE 안에
// 있어서 직접 접근 불가) — 코드가 길어져서 따로 분리한 파일이라 이렇게 최소한만 내보내 쓴다.

function renderBoxScene(canvas, box) {
  const { baseScene, orthoCam, setupOrbit, addZoomButtons, addEdgeOutline } = window.__partsLab;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setSize(500, 500, false);
  const scene = baseScene();
  const camera = orthoCam(120);
  camera.position.set(150, 150, 150);
  camera.lookAt(box.x, box.y, box.z);
  const geo = new THREE.BoxGeometry(box.w, box.h, box.d);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x8fb2ff }));
  mesh.position.set(box.x, box.y, box.z);
  addEdgeOutline(mesh, 0x8fb2ff);
  scene.add(mesh);
  renderer.render(scene, camera);
  const controls = setupOrbit(renderer, scene, camera, [box.x, box.y, box.z]);
  addZoomButtons(canvas, () => ({ camera, controls }));
}

function initBoxEditor() {
  const { openPickerModal, adminApi, getAccessToken } = window.__partsLab;
  let targetPart = null;

  function readBoxInputs() {
    return {
      x: Number(document.getElementById('boxX').value) || 0,
      y: Number(document.getElementById('boxY').value) || 0,
      z: Number(document.getElementById('boxZ').value) || 0,
      w: Math.max(1, Number(document.getElementById('boxW').value) || 1),
      h: Math.max(1, Number(document.getElementById('boxH').value) || 1),
      d: Math.max(1, Number(document.getElementById('boxD').value) || 1),
    };
  }
  function fillBoxInputs(box) {
    document.getElementById('boxX').value = box.x;
    document.getElementById('boxY').value = box.y;
    document.getElementById('boxZ').value = box.z;
    document.getElementById('boxW').value = box.w;
    document.getElementById('boxH').value = box.h;
    document.getElementById('boxD').value = box.d;
  }
  // 이전 렌더러가 캔버스에 붙여둔 확대/축소 버튼 등 잔재를 지우려고, mutate하지 않고 캔버스 엘리먼트 자체를
  // 새로 교체한다 — 부품 수리실의 브라켓/프레임 편집 패널(freshWrap)과 같은 방식.
  function redraw() {
    const wrap = document.querySelector('#boxEditorPanel .imgWrap');
    wrap.innerHTML = '<canvas id="boxEditorCanvas" width="500" height="500"></canvas>';
    renderBoxScene(document.getElementById('boxEditorCanvas'), readBoxInputs());
  }

  function onBoxTargetPicked(p) {
    targetPart = p;
    document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + p.name;
    document.getElementById('boxSaveBtn').disabled = false;
    const box = p.spec && Array.isArray(p.spec.boxes) && p.spec.boxes[0];
    if (box) fillBoxInputs(box);
    redraw();
  }

  document.getElementById('boxRedrawBtn').addEventListener('click', redraw);
  document.getElementById('boxTargetPickBtn').addEventListener('click', () => {
    openPickerModal('저장할 부품 고르기', onBoxTargetPicked);
  });
  document.getElementById('boxSaveBtn').addEventListener('click', async () => {
    const msg = document.getElementById('boxEditorMsg'), btn = document.getElementById('boxSaveBtn');
    if (!targetPart) { msg.className = 'msg err'; msg.textContent = '먼저 저장할 부품을 골라주세요.'; return; }
    const box = readBoxInputs();
    // 이 부품에 이미 있던 다른 spec 필드(holeLabels 등)를 지우지 않도록 합쳐서 보낸다.
    const spec = Object.assign({}, targetPart.spec || {}, { boxes: [box] });
    btn.disabled = true; msg.textContent = '';
    try {
      await adminApi({
        action: 'update_part', partId: targetPart.id,
        name: targetPart.name, icon: targetPart.icon, subject: targetPart.subject, category: targetPart.category || '',
        volumes: targetPart.volumes || [], color: targetPart.color, size: targetPart.size,
        imageSvg: targetPart.imageSvg, imageSvgDiagonal: targetPart.imageSvgDiagonal, primaryImage: targetPart.primaryImage || 'front',
        spec, snapshot: targetPart.snapshot || null, snapshots: targetPart.snapshots || null,
      }, getAccessToken());
      targetPart.spec = spec;
      msg.className = 'msg ok'; msg.textContent = '저장했어요.';
    } catch (e) {
      msg.className = 'msg err'; msg.textContent = '저장 실패: ' + e.message;
    } finally {
      btn.disabled = false;
    }
  });

  redraw();
}

window.initBoxEditor = initBoxEditor;
