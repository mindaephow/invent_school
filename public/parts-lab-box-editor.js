// 부품 수리실의 "도형 에디터" — 예전 자유낙서 스케치북 자리를 대신한다. 도형(박스/바퀴/톱니바퀴) 하나를
// 마우스로 직접 옮기거나 크기를 조절하고(THREE.TransformControls — OrbitControls와 같은 공식 three.js
// 예제, 사용자 요청: "이동/크기 손잡이" 같은 팅커캐드식 조작), 숫자 입력으로도 정확히 맞춘 뒤, 고른 부품의
// spec.shapes에 저장한다(svg 없이 숫자만으로 모양이 재현됨 — 브라켓의 armLen1/armLen2/armWidth와 같은 목적).
//
// parts-lab.html의 공용 헬퍼(baseScene 등)·adminApi는 window.__partsLab로 넘겨받는다(그 파일의 큰 IIFE 안에
// 있어서 직접 접근 불가) — 코드가 길어져서 따로 분리한 파일이라 이렇게 최소한만 내보내 쓴다.

const SHAPE_COLOR = 0x8fb2ff;

// 박스는 그대로 BoxGeometry. 바퀴/톱니바퀴는 원판(Cylinder, 축=Y)이고, 톱니바퀴는 둘레에 작은 이빨(박스)을
// teeth개 붙인다 — 실제 인볼류트 치형까지는 안 만들고(설계 화면의 기존 gear/wheel shapeKind도 원기둥 조합
// 수준이라 이 정도면 앱 다른 곳과 시각적으로 맞음), 톱니바퀴/바퀴가 눈으로 구분되는 정도로만 만든다.
function buildShapeMesh(shape) {
  if (shape.type === 'wheel' || shape.type === 'gear') {
    const group = new THREE.Group();
    const bodyGeo = new THREE.CylinderGeometry(shape.radius, shape.radius, shape.width, 32);
    group.add(new THREE.Mesh(bodyGeo, new THREE.MeshStandardMaterial({ color: SHAPE_COLOR })));
    if (shape.type === 'gear') {
      const teeth = Math.max(4, Math.round(shape.teeth) || 12);
      const toothLen = Math.max(2, shape.radius * 0.18);
      const toothWidth = Math.max(1.5, (2 * Math.PI * shape.radius) / teeth * 0.55);
      for (let i = 0; i < teeth; i++) {
        const angle = (i / teeth) * Math.PI * 2;
        const toothGeo = new THREE.BoxGeometry(toothWidth, shape.width, toothLen);
        const tooth = new THREE.Mesh(toothGeo, new THREE.MeshStandardMaterial({ color: SHAPE_COLOR }));
        const r = shape.radius + toothLen / 2;
        tooth.position.set(Math.cos(angle) * r, 0, Math.sin(angle) * r);
        tooth.rotation.y = -angle;
        group.add(tooth);
      }
    }
    return group;
  }
  const geo = new THREE.BoxGeometry(shape.w, shape.h, shape.d);
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: SHAPE_COLOR }));
}

function initBoxEditor() {
  const { baseScene, orthoCam, setupOrbit, addZoomButtons, addEdgeOutline, openPickerModal, adminApi, getAccessToken } = window.__partsLab;
  let targetPart = null;
  // 지금 캔버스에 떠 있는 씬/카메라/조작 도구 — 숫자칸에서 "다시 그리기"를 누르거나 부품을 새로 고를 때마다
  // 통째로 새로 만든다(브라켓/프레임 편집 패널과 같은 방식). 드래그로 옮기거나 크기를 바꾼 결과는
  // transformControls의 objectChange 이벤트에서 바로 숫자칸에 반영한다.
  let live = null;

  function currentType() { return document.getElementById('shapeType').value; }
  function syncFieldVisibility() {
    const type = currentType();
    document.getElementById('boxOnlyFields').hidden = type !== 'box';
    document.getElementById('roundFields').hidden = type === 'box';
    document.getElementById('teethField').hidden = type !== 'gear';
  }
  function readShapeInputs() {
    const type = currentType();
    const base = {
      type,
      x: Number(document.getElementById('boxX').value) || 0,
      y: Number(document.getElementById('boxY').value) || 0,
      z: Number(document.getElementById('boxZ').value) || 0,
    };
    if (type === 'box') {
      base.w = Math.max(1, Number(document.getElementById('boxW').value) || 1);
      base.h = Math.max(1, Number(document.getElementById('boxH').value) || 1);
      base.d = Math.max(1, Number(document.getElementById('boxD').value) || 1);
    } else {
      base.radius = Math.max(1, Number(document.getElementById('shapeRadius').value) || 1);
      base.width = Math.max(1, Number(document.getElementById('shapeWidth').value) || 1);
      if (type === 'gear') base.teeth = Math.max(4, Number(document.getElementById('shapeTeeth').value) || 12);
    }
    return base;
  }
  function fillShapeInputs(shape) {
    document.getElementById('shapeType').value = shape.type || 'box';
    document.getElementById('boxX').value = round1(shape.x);
    document.getElementById('boxY').value = round1(shape.y);
    document.getElementById('boxZ').value = round1(shape.z);
    if ((shape.type || 'box') === 'box') {
      document.getElementById('boxW').value = round1(shape.w);
      document.getElementById('boxH').value = round1(shape.h);
      document.getElementById('boxD').value = round1(shape.d);
    } else {
      document.getElementById('shapeRadius').value = round1(shape.radius);
      document.getElementById('shapeWidth').value = round1(shape.width);
      if (shape.type === 'gear') document.getElementById('shapeTeeth').value = shape.teeth;
    }
    syncFieldVisibility();
  }
  function round1(n) { return Math.round(n * 10) / 10; }

  // 드래그로 옮기거나("이동") 크기를 바꾼("크기") 결과를 숫자칸에 그대로 되읽어 온다. "크기" 모드는
  // mesh.scale을 곱하는 방식이라, 매번 그 배율을 실제 w/h/d(또는 radius/width) 숫자에 구워넣고
  // scale은 다시 1로 되돌린다 — 안 그러면 드래그를 여러 번 할수록 배율이 겹겹이 쌓여 숫자와 안 맞아진다.
  function syncInputsFromLiveObject() {
    if (!live) return;
    const { target, shape } = live;
    shape.x = target.position.x; shape.y = target.position.y; shape.z = target.position.z;
    if (shape.type === 'box') {
      shape.w = Math.max(1, shape.w * target.scale.x);
      shape.h = Math.max(1, shape.h * target.scale.y);
      shape.d = Math.max(1, shape.d * target.scale.z);
    } else {
      shape.radius = Math.max(1, shape.radius * ((target.scale.x + target.scale.z) / 2));
      shape.width = Math.max(1, shape.width * target.scale.y);
    }
    target.scale.set(1, 1, 1);
    fillShapeInputs(shape);
  }

  // 이전 렌더러/조작 도구가 캔버스에 붙여둔 확대/축소 버튼 등 잔재를 지우려고, mutate하지 않고 캔버스
  // 엘리먼트 자체를 새로 교체한다 — 부품 수리실의 브라켓/프레임 편집 패널(freshWrap)과 같은 방식.
  function redraw() {
    const wrap = document.querySelector('#boxEditorPanel .imgWrap');
    wrap.innerHTML = '<canvas id="boxEditorCanvas" width="500" height="500"></canvas>';
    const canvas = document.getElementById('boxEditorCanvas');
    const shape = readShapeInputs();

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setSize(500, 500, false);
    const scene = baseScene();
    const camera = orthoCam(120);
    camera.position.set(150, 150, 150);
    camera.lookAt(shape.x, shape.y, shape.z);

    const target = buildShapeMesh(shape);
    target.position.set(shape.x, shape.y, shape.z);
    if (target.isMesh) addEdgeOutline(target, SHAPE_COLOR);
    else target.children.forEach((child) => addEdgeOutline(child, SHAPE_COLOR));
    scene.add(target);

    const controls = setupOrbit(renderer, scene, camera, [shape.x, shape.y, shape.z]);
    addZoomButtons(canvas, () => ({ camera, controls }));

    const transform = new THREE.TransformControls(camera, renderer.domElement);
    transform.attach(target);
    transform.setMode(document.querySelector('.tfModeBtn.on') && document.querySelector('.tfModeBtn.on').dataset.mode === 'scale' ? 'scale' : 'translate');
    transform.addEventListener('dragging-changed', (e) => { controls.enabled = !e.value; });
    transform.addEventListener('objectChange', syncInputsFromLiveObject);
    scene.add(transform);

    live = { target, shape, transform };
  }

  function setTransformMode(mode) {
    document.querySelectorAll('.tfModeBtn').forEach((b) => b.classList.toggle('on', b.dataset.mode === mode));
    if (live && live.transform) live.transform.setMode(mode);
  }

  function onBoxTargetPicked(p) {
    targetPart = p;
    document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + p.name;
    document.getElementById('boxSaveBtn').disabled = false;
    const shape = p.spec && Array.isArray(p.spec.shapes) && p.spec.shapes[0];
    if (shape) fillShapeInputs(shape);
    redraw();
  }

  document.getElementById('shapeType').addEventListener('change', () => { syncFieldVisibility(); redraw(); });
  document.getElementById('boxRedrawBtn').addEventListener('click', redraw);
  document.querySelectorAll('.tfModeBtn').forEach((b) => b.addEventListener('click', () => setTransformMode(b.dataset.mode)));
  document.getElementById('boxTargetPickBtn').addEventListener('click', () => {
    openPickerModal('저장할 부품 고르기', onBoxTargetPicked);
  });
  document.getElementById('boxSaveBtn').addEventListener('click', async () => {
    const msg = document.getElementById('boxEditorMsg'), btn = document.getElementById('boxSaveBtn');
    if (!targetPart) { msg.className = 'msg err'; msg.textContent = '먼저 저장할 부품을 골라주세요.'; return; }
    const shape = readShapeInputs();
    // 이 부품에 이미 있던 다른 spec 필드(holeLabels 등)를 지우지 않도록 합쳐서 보낸다.
    const spec = Object.assign({}, targetPart.spec || {}, { shapes: [shape] });
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

  syncFieldVisibility();
  redraw();
}

window.initBoxEditor = initBoxEditor;
