// 부품 수리실의 "도형 에디터" — 예전 자유낙서 스케치북 자리를 대신한다. 도형(박스/바퀴/톱니바퀴) 여러 개를
// 놓고 순서대로 더하기/빼기(뚫기)를 지정해서 진짜 입체 연산(CSG)으로 하나의 모양을 만든다. 마우스로 직접
// 옮기거나 크기를 조절하고(TransformControls), 숫자로도 정확히 맞출 수 있다. 결과는 고른 부품의
// spec.shapes에 저장한다(svg 없이 숫자만으로 모양이 재현됨 — 브라켓의 armLen1/armLen2/armWidth와 같은 목적).
//
// 이 페이지 나머지(브라켓/프레임 편집 등)는 훨씬 오래된 three.js(전역 스크립트, r0.128)를 그대로 쓴다 —
// 진짜 CSG(더하기/빼기)는 그 버전이 못 하고 최신 three.js가 필요해서, 이 파일만 따로 최신 three.js + CSG
// 라이브러리를 ES 모듈로 불러와 쓴다(사용자 지시: "부품수리실만 이걸 사용하고 분리해서 만든다음
// 불러오는식으로"). window.__partsLab로 넘어오는 건 THREE와 무관한 것들(openPickerModal/adminApi)뿐이라
// 두 three.js 버전이 서로 섞이지 않는다.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Evaluator, Brush, ADDITION, SUBTRACTION } from 'three-bvh-csg';

const ADD_COLOR = 0x8fb2ff;
const SUB_COLOR = 0xff8a8a;

function darken(hex, factor) {
  const r = Math.floor(((hex >> 16) & 255) * factor);
  const g = Math.floor(((hex >> 8) & 255) * factor);
  const b = Math.floor((hex & 255) * factor);
  return (r << 16) | (g << 8) | b;
}
function addEdgeOutline(mesh, colorHex) {
  const edges = new THREE.EdgesGeometry(mesh.geometry, 1);
  mesh.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: darken(colorHex, 0.55) })));
}
function baseScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf3f5f8);
  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const dir = new THREE.DirectionalLight(0xffffff, 0.6); dir.position.set(100, 200, 100); scene.add(dir);
  scene.add(new THREE.GridHelper(200, 20, 0xcccccc, 0xe5e5e5));
  scene.add(new THREE.AxesHelper(50));
  return scene;
}

function defaultShapeOfType(type) {
  if (type === 'box') return { type: 'box', op: 'add', x: 0, y: 5, z: 0, w: 30, h: 10, d: 30 };
  const base = { type, op: 'add', x: 0, y: 5, z: 0, radius: 20, width: 10 };
  if (type === 'gear') base.teeth = 12;
  return base;
}

// 도형 하나(박스/바퀴/톱니바퀴)의 실제 BufferGeometry를 만든다 — CSG는 도형당 지오메트리 하나만 다루므로,
// 톱니바퀴는 원판+이빨을 하나로 합쳐(mergeGeometries) 통짜 입체로 만든다.
function buildShapeGeometry(shape) {
  if (shape.type === 'box') return new THREE.BoxGeometry(shape.w, shape.h, shape.d);
  const bodyGeo = new THREE.CylinderGeometry(shape.radius, shape.radius, shape.width, 32);
  if (shape.type === 'wheel') return bodyGeo;
  const teeth = Math.max(4, Math.round(shape.teeth) || 12);
  const toothLen = Math.max(2, shape.radius * 0.18);
  const toothWidth = Math.max(1.5, (2 * Math.PI * shape.radius) / teeth * 0.55);
  const geos = [bodyGeo];
  for (let i = 0; i < teeth; i++) {
    const angle = (i / teeth) * Math.PI * 2;
    const toothGeo = new THREE.BoxGeometry(toothWidth, shape.width, toothLen);
    const r = shape.radius + toothLen / 2;
    toothGeo.rotateY(-angle);
    toothGeo.translate(Math.cos(angle) * r, 0, Math.sin(angle) * r);
    geos.push(toothGeo);
  }
  return mergeGeometries(geos, false);
}

function round1(n) { return Math.round(n * 10) / 10; }

function initBoxEditor() {
  const { openPickerModal, adminApi, getAccessToken } = window.__partsLab;
  let targetPart = null;
  let shapes = [defaultShapeOfType('box')];
  let selectedIndex = 0;
  let mode = 'edit'; // 'edit' | 'preview'
  // 지금 캔버스에 떠 있는 씬/렌더러/조작 도구 전체 — 모드를 바꾸거나 도형 목록이 바뀔 때마다 통째로 새로 만든다.
  let live = null;

  function teardownLive() {
    if (live) { cancelAnimationFrame(live.rafId); live.renderer.dispose(); }
    live = null;
  }
  function freshCanvas() {
    const wrap = document.querySelector('#boxEditorPanel .imgWrap');
    wrap.innerHTML = '<canvas id="boxEditorCanvas" width="500" height="500"></canvas>';
    return document.getElementById('boxEditorCanvas');
  }
  function setupCommon(canvas) {
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setSize(500, 500, false);
    const scene = baseScene();
    const camera = new THREE.OrthographicCamera(-120, 120, 120, -120, 0.1, 6000);
    camera.position.set(150, 150, 150);
    camera.lookAt(0, 0, 0);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 0);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.update();
    return { renderer, scene, camera, controls };
  }
  function startLoop(getState) {
    function loop() {
      const s = getState();
      s.controls.update();
      s.renderer.render(s.scene, s.camera);
      live.rafId = requestAnimationFrame(loop);
    }
    live.rafId = requestAnimationFrame(loop);
  }

  // ---------- 편집 모드: 도형을 하나하나 그대로(합치지 않고) 보여주고, 고른 도형만 드래그로 옮기거나 크기 조절 ----------
  function renderEditMode() {
    teardownLive();
    const canvas = freshCanvas();
    const { renderer, scene, camera, controls } = setupCommon(canvas);
    const meshes = shapes.map((shape) => {
      const color = shape.op === 'subtract' ? SUB_COLOR : ADD_COLOR;
      const mat = new THREE.MeshStandardMaterial({ color, transparent: shape.op === 'subtract', opacity: shape.op === 'subtract' ? 0.55 : 1 });
      const mesh = new THREE.Mesh(buildShapeGeometry(shape), mat);
      mesh.position.set(shape.x, shape.y, shape.z);
      addEdgeOutline(mesh, color);
      scene.add(mesh);
      return mesh;
    });
    const transform = new TransformControls(camera, renderer.domElement);
    transform.addEventListener('dragging-changed', (e) => { controls.enabled = !e.value; });
    transform.addEventListener('objectChange', () => syncSelectedShapeFromMesh(meshes));
    scene.add(transform.getHelper ? transform.getHelper() : transform);
    live = { renderer, scene, camera, controls, transform, meshes, rafId: 0 };
    attachSelection();
    renderer.render(scene, camera);
    startLoop(() => live);
  }
  function attachSelection() {
    if (!live || !live.meshes.length) return;
    const mesh = live.meshes[selectedIndex];
    live.transform.attach(mesh);
    live.transform.setMode(document.querySelector('.tfModeBtn.on').dataset.mode);
  }
  // 드래그(이동/크기)한 결과를 그 도형의 숫자로 되읽어 온다. "크기" 모드는 mesh.scale을 곱하는 방식이라,
  // 매번 실제 치수(w/h/d 또는 radius/width) 숫자에 구워넣고 scale은 1로 되돌린 뒤 지오메트리를 다시 만든다 —
  // 안 그러면 드래그를 여러 번 할수록 배율이 겹겹이 쌓여 숫자와 안 맞아진다.
  function syncSelectedShapeFromMesh(meshes) {
    const mesh = meshes[selectedIndex], shape = shapes[selectedIndex];
    shape.x = mesh.position.x; shape.y = mesh.position.y; shape.z = mesh.position.z;
    if (mesh.scale.x !== 1 || mesh.scale.y !== 1 || mesh.scale.z !== 1) {
      if (shape.type === 'box') {
        shape.w = Math.max(1, shape.w * mesh.scale.x);
        shape.h = Math.max(1, shape.h * mesh.scale.y);
        shape.d = Math.max(1, shape.d * mesh.scale.z);
      } else {
        shape.radius = Math.max(1, shape.radius * ((mesh.scale.x + mesh.scale.z) / 2));
        shape.width = Math.max(1, shape.width * mesh.scale.y);
      }
      mesh.scale.set(1, 1, 1);
      mesh.geometry.dispose();
      mesh.geometry = buildShapeGeometry(shape);
      mesh.children.forEach((c) => c.geometry && c.geometry.dispose());
      mesh.clear();
      addEdgeOutline(mesh, shape.op === 'subtract' ? SUB_COLOR : ADD_COLOR);
    }
    renderShapeListUI();
    fillFieldsFromShape(shape);
  }

  // ---------- 미리보기 모드: 실제 CSG로 더하고 뺀 최종 결과 하나만 보여줌(읽기 전용) ----------
  function renderPreviewMode() {
    teardownLive();
    const canvas = freshCanvas();
    const { renderer, scene, camera, controls } = setupCommon(canvas);
    const evaluator = new Evaluator();
    let result = new Brush(buildShapeGeometry(shapes[0]));
    result.position.set(shapes[0].x, shapes[0].y, shapes[0].z);
    result.updateMatrixWorld();
    for (let i = 1; i < shapes.length; i++) {
      const b = new Brush(buildShapeGeometry(shapes[i]));
      b.position.set(shapes[i].x, shapes[i].y, shapes[i].z);
      b.updateMatrixWorld();
      result = evaluator.evaluate(result, b, shapes[i].op === 'subtract' ? SUBTRACTION : ADDITION);
      result.updateMatrixWorld();
    }
    result.material = new THREE.MeshStandardMaterial({ color: ADD_COLOR });
    addEdgeOutline(result, ADD_COLOR);
    scene.add(result);
    live = { renderer, scene, camera, controls, transform: null, meshes: [], rafId: 0 };
    renderer.render(scene, camera);
    startLoop(() => live);
  }

  function setMode(next) {
    mode = next;
    document.getElementById('boxPreviewBtn').hidden = mode === 'preview';
    document.getElementById('boxBackToEditBtn').hidden = mode === 'edit';
    document.getElementById('shapeAddBtn').disabled = mode === 'preview';
    document.getElementById('shapeDeleteBtn').disabled = mode === 'preview';
    document.getElementById('boxRedrawBtn').disabled = mode === 'preview';
    if (mode === 'edit') renderEditMode(); else renderPreviewMode();
  }

  // ---------- 도형 목록 UI ----------
  function shapeLabel(shape, i) {
    const typeLabel = { box: '박스', wheel: '바퀴', gear: '톱니바퀴' }[shape.type];
    const opLabel = i === 0 ? '(베이스)' : (shape.op === 'subtract' ? '(➖ 빼기)' : '(➕ 더하기)');
    return (i + 1) + '. ' + typeLabel + ' ' + opLabel;
  }
  function renderShapeListUI() {
    const el = document.getElementById('shapeList');
    el.innerHTML = shapes.map((shape, i) => {
      const on = i === selectedIndex ? ' style="background:#2b6be0;color:#fff;border-color:#2b6be0;"' : '';
      return '<button type="button" class="shapeListRow" data-i="' + i + '"' + on + ' style="text-align:left; padding:6px 10px; border-radius:6px; border:1px solid #ccc; background:#fff; cursor:pointer;' + (i === selectedIndex ? 'background:#2b6be0;color:#fff;border-color:#2b6be0;' : '') + '">' + shapeLabel(shape, i) + '</button>';
    }).join('');
    el.querySelectorAll('.shapeListRow').forEach((btn) => btn.addEventListener('click', () => selectShape(Number(btn.dataset.i))));
  }
  function selectShape(i) {
    selectedIndex = i;
    fillFieldsFromShape(shapes[i]);
    renderShapeListUI();
    if (mode === 'edit') attachSelection();
  }

  // ---------- 입력칸 <-> 선택된 도형 ----------
  function currentType() { return document.getElementById('shapeType').value; }
  function syncFieldVisibility() {
    const type = currentType();
    // .hidden 속성은 이 파일의 CSS 명시도 때문에 안 먹혀서 style.display를 직접 건드린다.
    document.getElementById('boxOnlyFields').style.display = type === 'box' ? 'flex' : 'none';
    document.getElementById('roundFields').style.display = type === 'box' ? 'none' : 'flex';
    document.getElementById('teethField').style.display = type === 'gear' ? 'flex' : 'none';
    document.getElementById('shapeOpField').style.display = selectedIndex === 0 ? 'none' : 'flex';
  }
  function fillFieldsFromShape(shape) {
    document.getElementById('shapeType').value = shape.type;
    document.getElementById('shapeOp').value = shape.op;
    document.getElementById('boxX').value = round1(shape.x);
    document.getElementById('boxY').value = round1(shape.y);
    document.getElementById('boxZ').value = round1(shape.z);
    if (shape.type === 'box') {
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
  function readFieldsAsShape() {
    const type = currentType();
    const shape = {
      type, op: selectedIndex === 0 ? 'add' : document.getElementById('shapeOp').value,
      x: Number(document.getElementById('boxX').value) || 0,
      y: Number(document.getElementById('boxY').value) || 0,
      z: Number(document.getElementById('boxZ').value) || 0,
    };
    if (type === 'box') {
      shape.w = Math.max(1, Number(document.getElementById('boxW').value) || 1);
      shape.h = Math.max(1, Number(document.getElementById('boxH').value) || 1);
      shape.d = Math.max(1, Number(document.getElementById('boxD').value) || 1);
    } else {
      shape.radius = Math.max(1, Number(document.getElementById('shapeRadius').value) || 1);
      shape.width = Math.max(1, Number(document.getElementById('shapeWidth').value) || 1);
      if (type === 'gear') shape.teeth = Math.max(4, Number(document.getElementById('shapeTeeth').value) || 12);
    }
    return shape;
  }

  function onBoxTargetPicked(p) {
    targetPart = p;
    document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + p.name;
    document.getElementById('boxSaveBtn').disabled = false;
    const saved = p.spec && Array.isArray(p.spec.shapes) && p.spec.shapes.length ? p.spec.shapes : null;
    shapes = saved ? saved.map((s) => Object.assign({}, s)) : [defaultShapeOfType('box')];
    selectedIndex = 0;
    fillFieldsFromShape(shapes[0]);
    renderShapeListUI();
    setMode('edit');
  }

  document.getElementById('shapeType').addEventListener('change', syncFieldVisibility);
  document.getElementById('boxRedrawBtn').addEventListener('click', () => {
    shapes[selectedIndex] = readFieldsAsShape();
    renderShapeListUI();
    renderEditMode();
  });
  document.getElementById('shapeAddBtn').addEventListener('click', () => {
    shapes.push(defaultShapeOfType(currentType()));
    selectedIndex = shapes.length - 1;
    fillFieldsFromShape(shapes[selectedIndex]);
    renderShapeListUI();
    renderEditMode();
  });
  document.getElementById('shapeDeleteBtn').addEventListener('click', () => {
    if (shapes.length <= 1) { document.getElementById('boxEditorMsg').textContent = '도형이 하나는 남아있어야 해요.'; return; }
    shapes.splice(selectedIndex, 1);
    selectedIndex = Math.max(0, selectedIndex - 1);
    fillFieldsFromShape(shapes[selectedIndex]);
    renderShapeListUI();
    renderEditMode();
  });
  document.querySelectorAll('.tfModeBtn').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('.tfModeBtn').forEach((x) => x.classList.toggle('on', x === b));
    if (live && live.transform) live.transform.setMode(b.dataset.mode);
  }));
  document.getElementById('boxPreviewBtn').addEventListener('click', () => setMode('preview'));
  document.getElementById('boxBackToEditBtn').addEventListener('click', () => setMode('edit'));
  document.getElementById('boxTargetPickBtn').addEventListener('click', () => {
    openPickerModal('저장할 부품 고르기', onBoxTargetPicked);
  });
  document.getElementById('boxSaveBtn').addEventListener('click', async () => {
    const msg = document.getElementById('boxEditorMsg'), btn = document.getElementById('boxSaveBtn');
    if (!targetPart) { msg.className = 'msg err'; msg.textContent = '먼저 저장할 부품을 골라주세요.'; return; }
    // 이 부품에 이미 있던 다른 spec 필드(holeLabels 등)를 지우지 않도록 합쳐서 보낸다.
    const spec = Object.assign({}, targetPart.spec || {}, { shapes: shapes.map((s) => Object.assign({}, s)) });
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

  fillFieldsFromShape(shapes[0]);
  renderShapeListUI();
  renderEditMode();
}

window.initBoxEditor = initBoxEditor;
