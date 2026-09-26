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
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { Evaluator, Brush, ADDITION, SUBTRACTION } from 'three-bvh-csg';

const SUB_COLOR = 0xff8a8a;
// 팅커캐드처럼 도형마다(팔레트 타일도, 캔버스에 놓인 도형도) 서로 다른 색을 준다 — 전부 한 가지 파란색
// 하나로만 칠했더니 도형이 여러 개 겹치면 구분이 안 된다는 지적을 받고 추가함. "빼기(구멍)"로 지정된
// 도형만은 의미 전달을 위해 계속 반투명 빨강(SUB_COLOR) 하나로 통일한다.
const SHAPE_PALETTE = [0x5b8def, 0xff9f43, 0x51cf66, 0xa78bfa, 0x22b8cf, 0xff6fa5, 0xfcc419, 0x37b24d, 0x748ffc, 0xf783ac, 0x66d9e8, 0xffa94d, 0x845ef7, 0x20c997, 0xf06595];
function colorForIndex(i) { return SHAPE_PALETTE[i % SHAPE_PALETTE.length]; }
// "텍스트" 도형용 — 모듈이 로드되는 시점에 한 번만 받아온다(top-level await, 페이지 전체를 막지 않고
// 이 모듈 하나만 폰트가 올 때까지 잠깐 기다림 — gate()가 window.initBoxEditor를 폴링해서 기다리는 것과 맞물림).
// unpkg의 three npm 패키지엔 이제 examples/fonts가 안 들어있어서(0 files) three.js 깃허브 저장소를
// jsDelivr로 직접 받는다. 이거 하나가 실패해도 에디터 전체가 죽지 않도록 try/catch로 감싼다 — 실패하면
// textFont가 null로 남고, 텍스트 도형만 못 쓰고 나머지(박스/바퀴 등)는 그대로 동작한다.
let textFont = null;
try {
  textFont = await new FontLoader().loadAsync('https://cdn.jsdelivr.net/gh/mrdoob/three.js@r186/examples/fonts/helvetiker_regular.typeface.json');
} catch (e) {
  console.error('텍스트 도형용 폰트를 못 불러왔어요 — 텍스트 도형은 빈 박스로 대체됩니다.', e);
}

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

// 도형 종류 목록 — app/api/admin/route.js의 SHAPE_TYPES와 반드시 같이 맞춰야 한다.
const SHAPE_TYPES = ['box', 'wheel', 'gear', 'sphere', 'cone', 'pyramid', 'torus', 'hexprism', 'icosahedron', 'dome', 'wedge', 'ring', 'star', 'heart', 'text', 'duplo', 'knexRod', 'knexConnector', 'technicBeam'];
// 팔레트 탭 — 어떤 도형이 어느 탭(기본/휴벨리노형/케이넥스형/테크닉형)에 속하는지. 팔레트 UI에서만 쓰고 저장 스펙과는 무관.
// (내부 type 이름은 'duplo'로 그대로 두되, 사용자가 부르는 이름인 "휴벨리노형"은 화면 라벨(HTML)에서만 씀 —
// 사용자 지적: "난 휴벨리노형이라고 했는데 왜 듀블로형이래?")
const SHAPE_CATEGORY = { duplo: 'duplo', knexRod: 'knex', knexConnector: 'knex', technicBeam: 'technic' };
function categoryOf(type) { return SHAPE_CATEGORY[type] || 'basic'; }
// 반지름만 쓰는 도형(두께 칸 없음), w/h/d를 쓰는 박스류 도형 — 이 둘에 안 속하면 반지름+두께 조합을 쓴다.
// 휴벨리노형/테크닉형 도형은 스터드나 구멍이 몸통에 붙는다는 점만 다르고 몸통 자체는 박스라서 w/h/d를 그대로 재사용한다.
const RADIUS_ONLY = ['sphere', 'icosahedron', 'dome'];
const BOX_LIKE = ['box', 'wedge', 'duplo', 'technicBeam'];
// 반지름+두께를 쓰는 도형들이 "두께" 칸을 각자 다른 뜻으로 쓰므로 — 팔레트에서 고를 때 입력칸 라벨을 그 뜻에 맞게 바꿔준다.
const WIDTH_FIELD_LABEL = { wheel: '두께(mm)', gear: '두께(mm)', cone: '높이(mm)', pyramid: '높이(mm)', torus: '튜브 두께(mm)', hexprism: '높이(mm)', ring: '두께(mm)', star: '두께(mm)', heart: '두께(mm)', text: '두께(mm)', knexRod: '길이(mm)', knexConnector: '두께(mm)' };
const RADIUS_FIELD_LABEL = { knexRod: '굵기(mm)' };

function defaultShapeOfType(type) {
  if (type === 'box') return { type: 'box', op: 'add', x: 0, y: 5, z: 0, w: 30, h: 10, d: 30 };
  if (type === 'wedge') return { type: 'wedge', op: 'add', x: 0, y: 0, z: 0, w: 30, h: 20, d: 20 };
  // 듀프로는 기본 블록보다 훨씬 큼직하게(2×2 스터드 자리) — 실제 듀프로가 레고보다 스터드가 2배 큰 것과 같은 느낌.
  if (type === 'duplo') return { type: 'duplo', op: 'add', x: 0, y: 10, z: 0, w: 32, h: 20, d: 32 };
  if (RADIUS_ONLY.includes(type)) return { type, op: 'add', x: 0, y: 20, z: 0, radius: 20 };
  if (type === 'torus') return { type: 'torus', op: 'add', x: 0, y: 6, z: 0, radius: 20, width: 6 };
  if (type === 'text') return { type: 'text', op: 'add', x: 0, y: 5, z: 0, text: 'A', radius: 20, width: 5 };
  if (type === 'knexRod') return { type: 'knexRod', op: 'add', x: 0, y: 3, z: 0, radius: 3, width: 60 };
  if (type === 'knexConnector') return { type: 'knexConnector', op: 'add', x: 0, y: 4, z: 0, radius: 16, width: 8, holes: 6 };
  // 테크닉형 빔 — 레고 테크닉 표준 간격(듀프로/휴벨리노 간격의 절반)으로 둥근 구멍이 줄줄이 뚫려있음.
  if (type === 'technicBeam') return { type: 'technicBeam', op: 'add', x: 0, y: 4, z: 0, w: 64, h: 8, d: 8 };
  const base = { type, op: 'add', x: 0, y: 5, z: 0, radius: 20, width: 10 };
  if (type === 'gear') base.teeth = 12;
  return base;
}

function wedgeGeometry(w, h, d) {
  const s = new THREE.Shape();
  s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(0, h); s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: d, bevelEnabled: false });
  geo.translate(0, 0, -d / 2);
  return geo;
}
function ringGeometry(outerR, thickness) {
  const s = new THREE.Shape();
  s.absarc(0, 0, outerR, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(0, 0, outerR * 0.5, 0, Math.PI * 2, true);
  s.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(s, { depth: thickness, bevelEnabled: false, curveSegments: 32 });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, -thickness / 2, 0);
  return geo;
}
function starGeometry(outerR, thickness, points) {
  const innerR = outerR * 0.45;
  const s = new THREE.Shape();
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const a = (i / (points * 2)) * Math.PI * 2 - Math.PI / 2;
    const x = Math.cos(a) * r, y = Math.sin(a) * r;
    if (i === 0) s.moveTo(x, y); else s.lineTo(x, y);
  }
  s.closePath();
  const geo = new THREE.ExtrudeGeometry(s, { depth: thickness, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, -thickness / 2, 0);
  return geo;
}
function heartGeometry(scale, thickness) {
  const s = new THREE.Shape();
  s.moveTo(0, scale * 0.35);
  s.bezierCurveTo(0, scale * 0.7, -scale * 0.6, scale * 1.1, -scale, scale * 0.55);
  s.bezierCurveTo(-scale * 1.5, -scale * 0.05, -scale * 0.5, -scale * 0.7, 0, -scale);
  s.bezierCurveTo(scale * 0.5, -scale * 0.7, scale * 1.5, -scale * 0.05, scale, scale * 0.55);
  s.bezierCurveTo(scale * 0.6, scale * 1.1, 0, scale * 0.7, 0, scale * 0.35);
  const geo = new THREE.ExtrudeGeometry(s, { depth: thickness, bevelEnabled: false, curveSegments: 16 });
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, -thickness / 2, 0);
  return geo;
}

// 옥스포드/레고식 스터드보다 큰 듀프로식 스터드 — 몸통(w×h×d 박스) 위에 원기둥 돌기를 격자로 붙인다.
function duploGeometry(w, h, d) {
  const pitch = 16; // 스터드 하나가 차지하는 칸 크기(듀프로는 레고/옥스포드보다 이 칸이 큼)
  const studsX = Math.max(1, Math.round(w / pitch));
  const studsZ = Math.max(1, Math.round(d / pitch));
  const studR = pitch * 0.34, studH = pitch * 0.4;
  const geos = [new THREE.BoxGeometry(w, h, d)];
  for (let ix = 0; ix < studsX; ix++) {
    for (let iz = 0; iz < studsZ; iz++) {
      const stud = new THREE.CylinderGeometry(studR, studR, studH, 20);
      const px = (ix - (studsX - 1) / 2) * pitch, pz = (iz - (studsZ - 1) / 2) * pitch;
      stud.translate(px, h / 2 + studH / 2, pz);
      geos.push(stud);
    }
  }
  return mergeGeometries(geos, false);
}
// 케이넥스 막대 — 원기둥 몸통 + 양 끝에 둥근 캡(실제 케이넥스 막대의 둥근 끝 느낌).
function knexRodGeometry(r, len) {
  const bodyLen = Math.max(1, len - r * 2);
  const geos = [new THREE.CylinderGeometry(r, r, bodyLen, 12)];
  const capTop = new THREE.SphereGeometry(r, 12, 8);
  capTop.translate(0, bodyLen / 2, 0);
  const capBottom = new THREE.SphereGeometry(r, 12, 8);
  capBottom.translate(0, -bodyLen / 2, 0);
  geos.push(capTop, capBottom);
  return mergeGeometries(geos, false);
}
// 케이넥스 커넥터 — 원판 허브에 막대를 꽂을 수 있는 구멍을 여러 각도(holeCount개, 방사형)로 실제로 뚫는다
// (이 도형 하나 안에서만 쓰는 CSG라서, 바깥의 더하기/빼기 목록과는 무관하게 여기서 바로 뺀다).
function knexConnectorGeometry(r, thick, holeCount) {
  const n = Math.max(3, Math.min(8, Math.round(holeCount) || 6));
  const holeR = Math.max(1.2, r * 0.14);
  const ringR = r * 0.62;
  const evaluator = new Evaluator();
  let result = new Brush(new THREE.CylinderGeometry(r, r, thick, 24));
  result.updateMatrixWorld();
  for (let i = 0; i < n; i++) {
    const angle = (i / n) * Math.PI * 2;
    const hole = new Brush(new THREE.CylinderGeometry(holeR, holeR, thick * 2.2, 10));
    hole.position.set(Math.cos(angle) * ringR, 0, Math.sin(angle) * ringR);
    hole.updateMatrixWorld();
    result = evaluator.evaluate(result, hole, SUBTRACTION);
  }
  const centerHole = new Brush(new THREE.CylinderGeometry(holeR, holeR, thick * 2.2, 10));
  centerHole.updateMatrixWorld();
  result = evaluator.evaluate(result, centerHole, SUBTRACTION);
  return result.geometry;
}
// 테크닉형 빔 — 박스 몸통에 길이(w) 방향으로 일정 간격(pitch)마다 둥근 구멍을 실제로 뚫는다. 레고 테크닉
// 빔처럼 구멍이 옆에서 훤히 뚫려 보이도록, 구멍 축을 두께(d) 방향으로 눕혀서(rotateX) 배치한다.
function technicBeamGeometry(w, h, d) {
  const pitch = 8; // 휴벨리노 스터드 간격(16)의 절반 — 실제 레고 테크닉이 듀프로의 절반 크기인 것과 같은 비율
  const holeCount = Math.max(1, Math.floor(w / pitch));
  const holeR = Math.min(h, d) * 0.32;
  const evaluator = new Evaluator();
  let result = new Brush(new THREE.BoxGeometry(w, h, d));
  result.updateMatrixWorld();
  for (let i = 0; i < holeCount; i++) {
    const px = (i - (holeCount - 1) / 2) * pitch;
    const holeGeo = new THREE.CylinderGeometry(holeR, holeR, d * 2.2, 16);
    holeGeo.rotateX(Math.PI / 2);
    const hole = new Brush(holeGeo);
    hole.position.set(px, 0, 0);
    hole.updateMatrixWorld();
    result = evaluator.evaluate(result, hole, SUBTRACTION);
  }
  return result.geometry;
}

// 도형 하나의 실제 BufferGeometry를 만든다 — CSG는 도형당 지오메트리 하나만 다루므로, 톱니바퀴는
// 원판+이빨을 하나로 합쳐(mergeGeometries) 통짜 입체로 만든다.
function buildShapeGeometry(shape) {
  switch (shape.type) {
    case 'box': return new THREE.BoxGeometry(shape.w, shape.h, shape.d);
    case 'duplo': return duploGeometry(shape.w, shape.h, shape.d);
    case 'technicBeam': return technicBeamGeometry(shape.w, shape.h, shape.d);
    case 'knexRod': return knexRodGeometry(shape.radius, shape.width);
    case 'knexConnector': return knexConnectorGeometry(shape.radius, shape.width, shape.holes);
    case 'wedge': return wedgeGeometry(shape.w, shape.h, shape.d);
    case 'sphere': return new THREE.SphereGeometry(shape.radius, 24, 16);
    case 'icosahedron': return new THREE.IcosahedronGeometry(shape.radius, 0);
    case 'dome': {
      const dome = new THREE.SphereGeometry(shape.radius, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2);
      const cap = new THREE.CircleGeometry(shape.radius, 24);
      cap.rotateX(Math.PI / 2);
      return mergeGeometries([dome, cap], false);
    }
    case 'cone': return new THREE.ConeGeometry(shape.radius, shape.width, 32);
    case 'pyramid': return new THREE.ConeGeometry(shape.radius, shape.width, 4);
    case 'hexprism': return new THREE.CylinderGeometry(shape.radius, shape.radius, shape.width, 6);
    case 'torus': return new THREE.TorusGeometry(shape.radius, Math.min(shape.width, shape.radius * 0.9), 16, 32);
    case 'ring': return ringGeometry(shape.radius, shape.width);
    case 'star': return starGeometry(shape.radius, shape.width, 5);
    case 'heart': return heartGeometry(shape.radius, shape.width);
    case 'text': {
      if (!textFont) return new THREE.BoxGeometry(shape.radius, shape.width, shape.radius * 0.3);
      const geo = new TextGeometry(shape.text || 'A', { font: textFont, size: shape.radius, depth: shape.width, curveSegments: 6 });
      geo.center();
      return geo;
    }
    case 'wheel': return new THREE.CylinderGeometry(shape.radius, shape.radius, shape.width, 32);
    case 'gear': {
      const bodyGeo = new THREE.CylinderGeometry(shape.radius, shape.radius, shape.width, 32);
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
    default: return new THREE.BoxGeometry(10, 10, 10);
  }
}

function round1(n) { return Math.round(n * 10) / 10; }

// 팔레트 타일에 이모지 대신 그 도형의 실제 3D 미리보기를 한 번 그려서 이미지로 박아 넣는다 — 팅커캐드
// 팔레트처럼(사용자가 실제 팅커캐드 스크린샷을 보여주며 "이모지 말고 이렇게" 지적).
// 도형마다 WebGLRenderer(=WebGL 컨텍스트)를 새로 만들었더니, dispose()를 불러도 브라우저가 그 컨텍스트
// 슬롯을 바로 회수해주지 않아서(GC가 나중에 돌 때까지 살아있음) 한 번에 15개를 연달아 만드는 동안 페이지
// 전체의 WebGL 컨텍스트 개수 한도(브라우저마다 보통 16개 안팎)를 넘겨버렸다 — 그 결과 이 페이지에서 먼저
// 떠 있던 "비교 대상 부품"(90도 프레임 위/정면) 같은 오래된 컨텍스트가 브라우저에 의해 강제로 잘려서
// 빈 화면(깨진 아이콘)으로 보이는 사고가 실제로 났다. 그래서 렌더러 하나를 15번 재사용한다.
function renderPaletteThumbnails() {
  const size = 112;
  const canvas = document.createElement('canvas');
  canvas.width = size; canvas.height = size;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(size, size, false);
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 500);
  camera.position.set(45, 40, 45);
  camera.lookAt(0, 0, 0);
  SHAPE_TYPES.forEach((type, i) => {
    const scene = new THREE.Scene();
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dir = new THREE.DirectionalLight(0xffffff, 0.7); dir.position.set(2, 3, 2); scene.add(dir);
    const shape = defaultShapeOfType(type);
    const color = colorForIndex(i);
    const mesh = new THREE.Mesh(buildShapeGeometry(shape), new THREE.MeshStandardMaterial({ color }));
    addEdgeOutline(mesh, color);
    scene.add(mesh);
    renderer.render(scene, camera);
    const btn = document.querySelector('.paletteBtn[data-type="' + type + '"]');
    if (btn) btn.querySelector('.paletteThumb').src = canvas.toDataURL('image/png');
    mesh.geometry.dispose();
    mesh.material.dispose();
    mesh.children.forEach((c) => { c.geometry && c.geometry.dispose(); c.material && c.material.dispose(); });
  });
  renderer.dispose();
}

function initBoxEditor() {
  const { openPickerModal, adminApi, getAccessToken } = window.__partsLab;
  let targetPart = null;
  // 빈 캔버스로 시작한다 — 3D 디자인 도구는 원래 처음엔 아무것도 없는 게 정상이다(사용자 지적: "3d
  // 디지인중에 처음부터 도형이 있는 경우가 어디있어?????"). 예전엔 기본 박스를 하나 깔아뒀는데, 그러면
  // 그 박스를 지우려고 해도 "도형이 하나는 남아있어야" 막혀서 결국 못 지우는 게 이상하다는 지적도 같이 받음.
  let shapes = [];
  let selectedIndex = -1;
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
    const meshes = shapes.map((shape, i) => {
      const color = shape.op === 'subtract' ? SUB_COLOR : colorForIndex(i);
      const mat = new THREE.MeshStandardMaterial({ color, transparent: shape.op === 'subtract', opacity: shape.op === 'subtract' ? 0.55 : 1 });
      const mesh = new THREE.Mesh(buildShapeGeometry(shape), mat);
      mesh.position.set(shape.x, shape.y, shape.z);
      mesh.rotation.set(shape.rx || 0, shape.ry || 0, shape.rz || 0);
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
    if (!live || !live.meshes.length || selectedIndex < 0 || !live.meshes[selectedIndex]) {
      if (live && live.transform) live.transform.detach();
      return;
    }
    const mesh = live.meshes[selectedIndex];
    live.transform.attach(mesh);
    live.transform.setMode(document.querySelector('.tfModeBtn.on').dataset.mode);
  }
  // 드래그(이동/크기)한 결과를 그 도형의 숫자로 되읽어 온다. "크기" 모드는 mesh.scale을 곱하는 방식이라,
  // 매번 실제 치수(w/h/d 또는 radius/width) 숫자에 구워넣고 scale은 1로 되돌린 뒤 지오메트리를 다시 만든다 —
  // 안 그러면 드래그를 여러 번 할수록 배율이 겹겹이 쌓여 숫자와 안 맞아진다.
  // "바닥 위에 붙이기" — 이동/크기/회전으로 도형이 바닥(y=0) 아래로 파고들면 다시 바닥 위로 밀어올린다.
  // 회전된 상태에서도 정확히 맞도록, 로컬 지오메트리 치수가 아니라 실제 월드 좌표 바운딩박스(회전·크기
  // 반영)로 계산한다. 드래그(syncSelectedShapeFromMesh)와 15도 단위 각도 드롭다운 둘 다 이걸 같이 쓴다.
  function applyFloorClamp(mesh, shape) {
    if (!document.getElementById('floorClampChk').checked) return;
    const worldBox = new THREE.Box3().setFromObject(mesh);
    if (worldBox.min.y < -0.001) {
      mesh.position.y -= worldBox.min.y;
      shape.y = round1(mesh.position.y);
    }
  }
  function syncSelectedShapeFromMesh(meshes) {
    const mesh = meshes[selectedIndex], shape = shapes[selectedIndex];
    shape.x = mesh.position.x; shape.y = mesh.position.y; shape.z = mesh.position.z;
    shape.rx = mesh.rotation.x; shape.ry = mesh.rotation.y; shape.rz = mesh.rotation.z;
    if (mesh.scale.x !== 1 || mesh.scale.y !== 1 || mesh.scale.z !== 1) {
      if (BOX_LIKE.includes(shape.type)) {
        shape.w = Math.max(1, shape.w * mesh.scale.x);
        shape.h = Math.max(1, shape.h * mesh.scale.y);
        shape.d = Math.max(1, shape.d * mesh.scale.z);
      } else if (RADIUS_ONLY.includes(shape.type)) {
        shape.radius = Math.max(1, shape.radius * ((mesh.scale.x + mesh.scale.y + mesh.scale.z) / 3));
      } else {
        shape.radius = Math.max(1, shape.radius * ((mesh.scale.x + mesh.scale.z) / 2));
        shape.width = Math.max(1, shape.width * mesh.scale.y);
      }
      mesh.scale.set(1, 1, 1);
      mesh.geometry.dispose();
      mesh.geometry = buildShapeGeometry(shape);
      mesh.children.forEach((c) => c.geometry && c.geometry.dispose());
      mesh.clear();
      addEdgeOutline(mesh, shape.op === 'subtract' ? SUB_COLOR : colorForIndex(selectedIndex));
    }
    applyFloorClamp(mesh, shape);
    renderShapeListUI();
    fillFieldsFromShape(shape);
  }

  // ---------- 미리보기 모드: 실제 CSG로 더하고 뺀 최종 결과 하나만 보여줌(읽기 전용) ----------
  function renderPreviewMode() {
    teardownLive();
    const canvas = freshCanvas();
    const { renderer, scene, camera, controls } = setupCommon(canvas);
    if (!shapes.length) {
      live = { renderer, scene, camera, controls, transform: null, meshes: [], rafId: 0 };
      renderer.render(scene, camera);
      startLoop(() => live);
      document.getElementById('boxEditorMsg').textContent = '도형이 없어요 — 팔레트에서 추가해보세요.';
      return;
    }
    document.getElementById('boxEditorMsg').textContent = '';
    const evaluator = new Evaluator();
    let result = new Brush(buildShapeGeometry(shapes[0]));
    result.position.set(shapes[0].x, shapes[0].y, shapes[0].z);
    result.rotation.set(shapes[0].rx || 0, shapes[0].ry || 0, shapes[0].rz || 0);
    result.updateMatrixWorld();
    for (let i = 1; i < shapes.length; i++) {
      const b = new Brush(buildShapeGeometry(shapes[i]));
      b.position.set(shapes[i].x, shapes[i].y, shapes[i].z);
      b.rotation.set(shapes[i].rx || 0, shapes[i].ry || 0, shapes[i].rz || 0);
      b.updateMatrixWorld();
      result = evaluator.evaluate(result, b, shapes[i].op === 'subtract' ? SUBTRACTION : ADDITION);
      result.updateMatrixWorld();
    }
    // 최종 결과는 여러 도형을 합친 하나의 완성품이라 베이스 도형의 색 하나로 통일해서 보여준다.
    const finalColor = colorForIndex(0);
    result.material = new THREE.MeshStandardMaterial({ color: finalColor });
    addEdgeOutline(result, finalColor);
    scene.add(result);
    live = { renderer, scene, camera, controls, transform: null, meshes: [], rafId: 0 };
    renderer.render(scene, camera);
    startLoop(() => live);
  }

  function setMode(next) {
    mode = next;
    document.getElementById('boxPreviewBtn').hidden = mode === 'preview';
    document.getElementById('boxBackToEditBtn').hidden = mode === 'edit';
    document.querySelectorAll('.paletteBtn').forEach((b) => { b.disabled = mode === 'preview'; });
    document.getElementById('shapeDeleteBtn').disabled = mode === 'preview';
    document.getElementById('boxRedrawBtn').disabled = mode === 'preview';
    if (mode === 'edit') renderEditMode(); else renderPreviewMode();
  }

  // ---------- 도형 목록 UI ----------
  function shapeLabel(shape, i) {
    const typeLabel = { box: '박스', wheel: '바퀴', gear: '톱니바퀴', sphere: '구', cone: '원뿔', pyramid: '각뿔', torus: '도넛', hexprism: '육각기둥', icosahedron: '다면체', dome: '반구', wedge: '지붕', ring: '고리', star: '별', heart: '하트', text: '텍스트', duplo: '휴벨리노 블록', knexRod: '케이넥스 막대', knexConnector: '케이넥스 커넥터', technicBeam: '테크닉 빔' }[shape.type];
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
  // 도형 종류는 팔레트에서 고른 순간 정해지고 바뀌지 않는다(팅커캐드처럼 — 종류를 바꾸려면 지우고 팔레트에서
  // 다시 추가) — 그래서 드롭다운 없이 선택된 도형 자체의 type을 그대로 쓴다.
  function syncFieldVisibility(type) {
    // .hidden 속성은 이 파일의 CSS 명시도 때문에 안 먹혀서 style.display를 직접 건드린다.
    const boxLike = BOX_LIKE.includes(type);
    document.getElementById('boxOnlyFields').style.display = boxLike ? 'contents' : 'none';
    document.getElementById('roundFields').style.display = boxLike ? 'none' : 'contents';
    document.getElementById('shapeWidthField').style.display = RADIUS_ONLY.includes(type) ? 'none' : 'flex';
    document.getElementById('shapeWidthLabel').textContent = WIDTH_FIELD_LABEL[type] || '두께(mm)';
    document.getElementById('shapeRadiusLabel').textContent = RADIUS_FIELD_LABEL[type] || '반지름(mm)';
    document.getElementById('teethField').style.display = type === 'gear' ? 'flex' : 'none';
    document.getElementById('textField').style.display = type === 'text' ? 'flex' : 'none';
    document.getElementById('knexHolesField').style.display = type === 'knexConnector' ? 'flex' : 'none';
    document.getElementById('shapeOpField').style.display = selectedIndex === 0 ? 'none' : 'flex';
  }
  // 캔버스가 비어있을 수도 있으니(사용자 지적: "3d 디지인중에 처음부터 도형이 있는 경우가 어디있어?????")
  // 고른 도형이 없으면 숫자칸들을 다 숨기고 여기서 끝낸다 — shape가 undefined인 채로 아래로 내려가면
  // shape.op 등에서 바로 에러난다.
  function fillFieldsFromShape(shape) {
    const fieldsRow = document.querySelector('#boxEditorPanel .fieldsRow');
    if (!shape) {
      if (fieldsRow) fieldsRow.style.display = 'none';
      document.getElementById('shapeOpField').style.display = 'none';
      document.getElementById('boxRedrawBtn').disabled = true;
      return;
    }
    if (fieldsRow) fieldsRow.style.display = 'flex';
    document.getElementById('boxRedrawBtn').disabled = false;
    document.getElementById('shapeOp').value = shape.op;
    document.getElementById('boxX').value = round1(shape.x);
    document.getElementById('boxY').value = round1(shape.y);
    document.getElementById('boxZ').value = round1(shape.z);
    if (BOX_LIKE.includes(shape.type)) {
      document.getElementById('boxW').value = round1(shape.w);
      document.getElementById('boxH').value = round1(shape.h);
      document.getElementById('boxD').value = round1(shape.d);
    } else {
      document.getElementById('shapeRadius').value = round1(shape.radius);
      if (!RADIUS_ONLY.includes(shape.type)) document.getElementById('shapeWidth').value = round1(shape.width);
      if (shape.type === 'gear') document.getElementById('shapeTeeth').value = shape.teeth;
      if (shape.type === 'text') document.getElementById('shapeText').value = shape.text;
      if (shape.type === 'knexConnector') document.getElementById('knexHoles').value = shape.holes;
    }
    syncFieldVisibility(shape.type);
    syncRotateAngleUI();
  }
  // 회전축(x/y/z)을 고르면 그 축의 지금 각도를 15도 단위로 반올림해서 드롭다운에 보여준다 — 마우스로
  // 자유롭게 돌린 각도는 15도의 배수가 아닐 수 있으니, "실제 값을 그대로"가 아니라 "가장 가까운 15도"를 표시.
  function syncRotateAngleUI() {
    if (!shapes[selectedIndex]) return;
    const axis = document.getElementById('rotateAxis').value;
    const rad = shapes[selectedIndex]['r' + axis] || 0;
    let deg = Math.round((rad * 180 / Math.PI) / 15) * 15;
    deg = ((deg % 360) + 360) % 360; // 0~359로
    if (deg > 180) deg -= 360; // -180~180로(사용자 지시: "각도를 +180까지 -180꺼지 해야지")
    document.getElementById('rotateAngle').value = String(deg);
  }
  function readFieldsAsShape() {
    const prev = shapes[selectedIndex];
    const type = prev.type;
    const shape = {
      type, op: selectedIndex === 0 ? 'add' : document.getElementById('shapeOp').value,
      x: Number(document.getElementById('boxX').value) || 0,
      y: Number(document.getElementById('boxY').value) || 0,
      z: Number(document.getElementById('boxZ').value) || 0,
      // 회전은 숫자칸이 없고 마우스(↻ 회전)로만 조절하므로, 숫자칸으로 다시 그릴 때 기존 회전값을 그대로 지킨다.
      rx: prev.rx || 0, ry: prev.ry || 0, rz: prev.rz || 0,
    };
    if (BOX_LIKE.includes(type)) {
      shape.w = Math.max(1, Number(document.getElementById('boxW').value) || 1);
      shape.h = Math.max(1, Number(document.getElementById('boxH').value) || 1);
      shape.d = Math.max(1, Number(document.getElementById('boxD').value) || 1);
    } else {
      shape.radius = Math.max(1, Number(document.getElementById('shapeRadius').value) || 1);
      if (!RADIUS_ONLY.includes(type)) shape.width = Math.max(1, Number(document.getElementById('shapeWidth').value) || 1);
      if (type === 'gear') shape.teeth = Math.max(4, Number(document.getElementById('shapeTeeth').value) || 12);
      if (type === 'text') shape.text = (document.getElementById('shapeText').value || 'A').slice(0, 10);
      if (type === 'knexConnector') shape.holes = Math.max(3, Math.min(8, Number(document.getElementById('knexHoles').value) || 6));
    }
    return shape;
  }

  function onBoxTargetPicked(p) {
    targetPart = p;
    document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + p.name;
    document.getElementById('boxSaveBtn').disabled = false;
    const saved = p.spec && Array.isArray(p.spec.shapes) && p.spec.shapes.length ? p.spec.shapes : null;
    shapes = saved ? saved.map((s) => Object.assign({}, s)) : [];
    selectedIndex = shapes.length ? 0 : -1;
    fillFieldsFromShape(shapes[0]);
    renderShapeListUI();
    setMode('edit');
  }

  document.getElementById('boxRedrawBtn').addEventListener('click', () => {
    if (!shapes[selectedIndex]) return;
    shapes[selectedIndex] = readFieldsAsShape();
    renderShapeListUI();
    renderEditMode();
  });
  function addShape(shape) {
    shapes.push(shape);
    selectedIndex = shapes.length - 1;
    fillFieldsFromShape(shapes[selectedIndex]);
    renderShapeListUI();
    renderEditMode();
  }
  // 캔버스 위 마우스 위치를 바닥(y=0) 평면과의 교점으로 바꿔서 그 자리에 도형을 놓는다 — 팔레트에서
  // 드래그해서 캔버스에 놓을 때, 놓은 그 지점에 도형이 나오게 하기 위함(사용자 지시: "도형잡고
  // 스케치북으로 이동하면 해당도형을 옮겨주면되").
  function dropPointOnGround(clientX, clientY) {
    if (!live) return null;
    const canvas = document.getElementById('boxEditorCanvas');
    const rect = canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(
      ((clientX - rect.left) / rect.width) * 2 - 1,
      -((clientY - rect.top) / rect.height) * 2 + 1
    );
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(ndc, live.camera);
    const point = new THREE.Vector3();
    return raycaster.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), point) ? point : null;
  }
  // 팅커캐드처럼 팔레트의 도형을 누르면 그 종류가 바로 캔버스에 추가된다(사용자 지시: "도형이 오른쪽에
  // 쭉 나열되어 있어야지") — 드롭다운으로 종류를 고르고 따로 추가 버튼을 누르는 방식이 아니다. 클릭은
  // 기존대로 두고, 팔레트에서 캔버스로 직접 드래그해서 놓은 자리에 그대로 놓는 방식도 같이 지원한다.
  document.querySelectorAll('.paletteBtn').forEach((btn) => {
    btn.draggable = true;
    btn.addEventListener('dragstart', (e) => {
      if (btn.disabled) { e.preventDefault(); return; }
      e.dataTransfer.setData('text/plain', btn.dataset.type);
      e.dataTransfer.effectAllowed = 'copy';
    });
    btn.addEventListener('click', () => {
      const shape = defaultShapeOfType(btn.dataset.type);
      // 새 도형마다 x를 조금씩 띄워서 등록 — 전부 원점에 완전히 겹쳐 놓이면(특히 도형이 여러 개 쌓일수록)
      // "결과 미리보기"의 CSG 계산이 급격히 느려지는 걸 실제로 확인했다(하트까지 5개 겹쳤을 때 체감 멈춤
      // 수준). 겹치지 않게 놓고 필요하면 드래그로 다시 겹치면 된다.
      shape.x += shapes.length * 25;
      addShape(shape);
    });
  });
  // 도형 팔레트 접기/펼치기(사용자 지시: "도형 팔레트 접었다 폈다 할수있게").
  document.getElementById('paletteToggle').addEventListener('click', () => {
    const wrap = document.getElementById('shapePaletteWrap');
    const nowHidden = wrap.style.display !== 'none';
    wrap.style.display = nowHidden ? 'none' : '';
    document.getElementById('paletteToggle').textContent = nowHidden ? '▶ 펼치기' : '▼ 접기';
  });
  // 팔레트 탭(기본 도형/듀프로형/케이넥스형) — 탭에 안 맞는 도형 버튼은 숨긴다.
  document.querySelectorAll('.paletteTabBtn').forEach((tabBtn) => {
    tabBtn.addEventListener('click', () => {
      document.querySelectorAll('.paletteTabBtn').forEach((b) => b.classList.toggle('on', b === tabBtn));
      document.querySelectorAll('.paletteBtn').forEach((b) => {
        b.style.display = categoryOf(b.dataset.type) === tabBtn.dataset.category ? '' : 'none';
      });
    });
  });
  const canvasWrap = document.querySelector('#boxEditorPanel .imgWrap');
  canvasWrap.addEventListener('dragover', (e) => {
    if (mode !== 'edit' || !live) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  });
  canvasWrap.addEventListener('drop', (e) => {
    e.preventDefault();
    if (mode !== 'edit' || !live) return;
    const type = e.dataTransfer.getData('text/plain');
    if (!SHAPE_TYPES.includes(type)) return;
    const shape = defaultShapeOfType(type);
    const point = dropPointOnGround(e.clientX, e.clientY);
    if (point) { shape.x = round1(point.x); shape.z = round1(point.z); }
    addShape(shape);
  });
  // 캔버스 안 도형을 직접 클릭해서 선택 — 지금까진 오른쪽 "도형 목록"에서만 고를 수 있었다(사용자 지적:
  // "도형선택이 왜 안바뀌어???" — 캔버스에서 도형을 눌러도 아무 반응이 없었음). 회전(오빗)이나 기즈모를
  // 드래그하는 동작과 구분하기 위해, 누른 지점과 뗀 지점이 거의 같을 때(실제 "클릭")만 선택을 바꾼다 —
  // 안 그러면 화면을 돌리려고 드래그만 해도 마우스를 뗀 자리 아래 도형으로 선택이 계속 튀게 된다.
  let pointerDownAt = null;
  canvasWrap.addEventListener('pointerdown', (e) => { pointerDownAt = { x: e.clientX, y: e.clientY }; });
  canvasWrap.addEventListener('pointerup', (e) => {
    const start = pointerDownAt;
    pointerDownAt = null;
    if (!start || mode !== 'edit' || !live || !live.meshes.length) return;
    if (Math.hypot(e.clientX - start.x, e.clientY - start.y) > 4) return;
    const canvas = document.getElementById('boxEditorCanvas');
    const rect = canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(ndc, live.camera);
    const hit = raycaster.intersectObjects(live.meshes, false)[0];
    if (!hit) return;
    const idx = live.meshes.indexOf(hit.object);
    if (idx < 0 || idx === selectedIndex) return;
    selectedIndex = idx;
    fillFieldsFromShape(shapes[idx]);
    renderShapeListUI();
    attachSelection();
  });
  document.getElementById('shapeDeleteBtn').addEventListener('click', () => {
    if (!shapes.length || selectedIndex < 0) return;
    shapes.splice(selectedIndex, 1);
    selectedIndex = shapes.length ? Math.max(0, selectedIndex - 1) : -1;
    fillFieldsFromShape(shapes[selectedIndex]);
    renderShapeListUI();
    renderEditMode();
  });
  document.querySelectorAll('.tfModeBtn').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('.tfModeBtn').forEach((x) => x.classList.toggle('on', x === b));
    if (live && live.transform) live.transform.setMode(b.dataset.mode);
    document.getElementById('rotateAngleRow').style.display = b.dataset.mode === 'rotate' ? 'flex' : 'none';
    if (b.dataset.mode === 'rotate') syncRotateAngleUI();
  }));
  // 사용자 지시: "중심으로 반대로 뒤집는 버튼, 위아래로 뒤집는 버튼 추가해줘" — 도형을 옮기는 게 아니라
  // 카메라를 controls.target(캔버스 중심, 항상 0,0,0) 기준으로 반사시켜서 반대편/아래쪽에서 보게 한다.
  document.getElementById('boxFlipBtn').addEventListener('click', () => {
    if (!live) return;
    const t = live.controls.target, p = live.camera.position;
    live.camera.position.set(2 * t.x - p.x, p.y, 2 * t.z - p.z);
    live.camera.lookAt(t);
    live.controls.update();
  });
  document.getElementById('boxFlipYBtn').addEventListener('click', () => {
    if (!live) return;
    const t = live.controls.target, p = live.camera.position;
    live.camera.position.set(p.x, 2 * t.y - p.y, p.z);
    live.camera.lookAt(t);
    live.controls.update();
  });
  // 회전축 고르기(x/y/z) — 그 축의 지금 각도를 드롭다운에 보여준다.
  document.getElementById('rotateAxis').addEventListener('change', syncRotateAngleUI);
  // 15도 단위 각도 드롭다운으로 정확한 각도를 바로 지정(사용자 지시: "x,y,z선택후 15도 단위로 회전 각도
  // 선택할수 있게 해줘") — 마우스 드래그와 별개로, 캔버스의 도형 회전값을 그 자리에서 바로 반영한다.
  document.getElementById('rotateAngle').addEventListener('change', () => {
    if (!shapes[selectedIndex]) return;
    const axis = document.getElementById('rotateAxis').value;
    const deg = Number(document.getElementById('rotateAngle').value) || 0;
    const rad = deg * Math.PI / 180;
    shapes[selectedIndex]['r' + axis] = rad;
    if (mode === 'edit' && live && live.meshes[selectedIndex]) {
      const mesh = live.meshes[selectedIndex];
      mesh.rotation[axis] = rad;
      applyFloorClamp(mesh, shapes[selectedIndex]);
      fillFieldsFromShape(shapes[selectedIndex]);
    }
  });
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

  // 처음엔 "기본 도형" 탭만 보이게 — 듀프로형/케이넥스형 버튼은 그 탭을 눌러야 나온다.
  const initialTab = document.querySelector('.paletteTabBtn.on') || document.querySelector('.paletteTabBtn');
  if (initialTab) {
    document.querySelectorAll('.paletteBtn').forEach((b) => {
      b.style.display = categoryOf(b.dataset.type) === initialTab.dataset.category ? '' : 'none';
    });
  }
  renderPaletteThumbnails();
  fillFieldsFromShape(shapes[0]);
  renderShapeListUI();
  renderEditMode();
}

window.initBoxEditor = initBoxEditor;
