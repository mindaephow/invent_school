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
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { STLExporter } from 'three/addons/exporters/STLExporter.js';
import { Evaluator, Brush, ADDITION, SUBTRACTION } from 'three-bvh-csg';

const SUB_COLOR = 0xff8a8a;
// 팅커캐드처럼 도형마다(팔레트 타일도, 캔버스에 놓인 도형도) 서로 다른 색을 준다 — 전부 한 가지 파란색
// 하나로만 칠했더니 도형이 여러 개 겹치면 구분이 안 된다는 지적을 받고 추가함. "빼기(구멍)"로 지정된
// 도형만은 의미 전달을 위해 계속 반투명 빨강(SUB_COLOR) 하나로 통일한다.
const SHAPE_PALETTE = [0x5b8def, 0xff9f43, 0x51cf66, 0xa78bfa, 0x22b8cf, 0xff6fa5, 0xfcc419, 0x37b24d, 0x748ffc, 0xf783ac, 0x66d9e8, 0xffa94d, 0x845ef7, 0x20c997, 0xf06595];
function colorForIndex(i) { return SHAPE_PALETTE[i % SHAPE_PALETTE.length]; }
// 불러온 3D 파일은 팔레트 색 대신 아이보리색으로(사용자 지시: "아이보리색으로") — 1열브라켓과 같은 톤(0xf2ead9).
const IMPORT_COLOR = 0xf2ead9;
// 물체를 고른 뒤 색상 팔레트(HTML <input type="color">)로 직접 정할 수 있게 함(사용자 지시: "물체 선택후
// 색상팔레트 선택할수 있게 해줘") — shape.color(문자열 "#rrggbb")가 있으면 그걸 최우선으로 쓴다.
function colorForShape(shape, i) {
  if (shape.color) return Number('0x' + shape.color.slice(1));
  return shape.type === 'import' ? IMPORT_COLOR : colorForIndex(i);
}
// 사용자 지시: "명암을 더 밝게 해야할꺼 같아~ 안되면 명암조절 기능을 넣던가~~" — 조명 문제를 더 파고드는
// 대신, 화면에 실제로 그리는 색에 밝기(%)를 곱해서 사용자가 직접 밝게 조절할 수 있게 한다(100=원래 색,
// 200=두 배 밝게, 채널별로 255를 넘지 않게 자름). shape.brightness가 없으면(기본 100%) 원래 색 그대로.
function materialColorForShape(shape, i) {
  const base = colorForShape(shape, i);
  const pct = shape.brightness || 100;
  if (pct === 100) return base;
  const scale = (c) => Math.min(255, Math.round(c * pct / 100));
  const r = scale((base >> 16) & 255), g = scale((base >> 8) & 255), b = scale(base & 255);
  return (r << 16) | (g << 8) | b;
}
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
// 선택된 도형은 테두리를 눈에 띄는 노란색으로 강조한다(사용자 지시: "부품을 클릭하면 부품이
// 선택되었다는 표시가 되었으면 좋겠어 — 테두리만 하이라이트 된다던가"). 이동/회전/크기 버튼을 꺼도(토글
// 오프) 기즈모 없이 어떤 도형이 선택돼 있는지 알 수 있어야 하므로, 기즈모와는 별개로 항상 표시한다.
// 사용자 지적(2번째): "하이라이트가 너무 밝아, 선택됐다는 표시만 되면 돼" — 처음엔 눈에 확 띄는 노란색
// (0xffd60a)이었는데, 이 앱 다른 곳(도형 목록·탭)에서 이미 "선택됨"을 나타내는 파란색과 맞춰서 차분하게.
const SELECTED_OUTLINE_COLOR = 0x2b6be0;
function addEdgeOutline(mesh, colorHex, selected) {
  const edges = new THREE.EdgesGeometry(mesh.geometry, 1);
  const lineColor = selected ? SELECTED_OUTLINE_COLOR : darken(colorHex, 0.55);
  mesh.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: lineColor })));
}
// 부품수리실(parts-lab.html)의 makeAxesRods와 동일 — 얇은 GL 선은 배경(밝은 모눈종이 vs 어두운 도형)에
// 따라 같은 색이 두 톤으로 보이는 안티에일리어싱 문제가 있어서(사용자 지적: "빨간색이 왜 두 가지 색으로
// 보여?"), 조명 영향 없는 단색 막대(박스)로 대체한다. depthTest는 켜둔다 — 사용자 지적: "물체 뒷편에 있는
// 선은 물리적으로 안 보여야 하는데 보이고 있어".
function makeAxesRods(size) {
  const group = new THREE.Group();
  const t = 0.6;
  const specs = [[0xff0000, [size / 2, 0, 0], [size, t, t]], [0x00ff00, [0, size / 2, 0], [t, size, t]], [0x0000ff, [0, 0, size / 2], [t, t, size]]];
  specs.forEach(([color, pos, dim]) => {
    const rod = new THREE.Mesh(new THREE.BoxGeometry(dim[0], dim[1], dim[2]), new THREE.MeshBasicMaterial({ color }));
    rod.position.set(pos[0], pos[1], pos[2]);
    group.add(rod);
  });
  return group;
}
function baseScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf3f5f8);
  // 진짜 원인: 이 파일만 최신 three.js(r186, 모듈)를 쓰는데, 최신 버전은 조명 세기의 단위 자체가
  // 예전(브라켓/프레임이 쓰는 r0.128) 방식과 달라서, 같은 숫자(0.6~1.2)를 넣어도 훨씬 어둡게 나온다
  // (사용자 지적: "니가 기본도형에 그린 도형들 색상도 모두 그래" / "도형 에디터만 그런 현상이 있어" /
  // "무슨 필터같은게 있는거 아닐까?" — 정확히 짚으심, 두 three.js 버전의 조명 처리 차이였음). 조명 세기를
  // 더 올리는 방법도 있지만, 근본적으로 도형 색은 "고른 색 그대로" 보여주는 게 목적이라 조명에 아예 영향
  // 안 받는 재질(MeshBasicMaterial)로 바꿔서 해결함 — 이 조명은 그리드/축 막대 등에는 영향 없음(그것들도
  // MeshBasicMaterial이라 원래도 조명 영향 안 받았음).
  scene.add(new THREE.AmbientLight(0xffffff, 1.2));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8); dir.position.set(100, 200, 100); scene.add(dir);
  scene.add(new THREE.GridHelper(200, 20, 0xcccccc, 0xe5e5e5));
  scene.add(makeAxesRods(50));
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
    // GLB/GLTF·STL·OBJ로 불러온 도형 — 숫자(가로/세로/높이 등)로 계산해서 그리는 다른 도형과 달리, 파일
    // 안의 삼각형 좌표를 통째로 쓴다. 그래서 shape._geometry(불러올 때 미리 만들어 캐시해둔 지오메트리)를
    // 그대로 돌려준다 — 다른 도형처럼 매번 새로 계산하지 않음(사용자 지시: "팅커캐드처럼 3D 파일도
    // 불러올 수 있게 해줘").
    case 'import': return shape._geometry || new THREE.BoxGeometry(10, 10, 10);
    default: return new THREE.BoxGeometry(10, 10, 10);
  }
}

// GLB/GLTF·STL·OBJ 파일을 읽어서 하나의 BufferGeometry로 합쳐 돌려준다. 원점 중심으로 맞추고, 바닥(y=0)
// 위에 놓이도록 y를 올려서 다른 도형들과 똑같이 다룰 수 있게 한다. glTF는 보통 미터 단위로 만들어져서
// 이 도구(mm 단위)보다 1000배 작게 들어오는 경우가 많아 — 크기가 아주 작으면(5mm 미만) 1000배 키운다.
async function loadImportedGeometry(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const url = URL.createObjectURL(file);
  try {
    let geometry;
    if (ext === 'glb' || ext === 'gltf') {
      const gltf = await new GLTFLoader().loadAsync(url);
      const geos = [];
      gltf.scene.traverse((obj) => {
        if (obj.isMesh && obj.geometry) {
          const g = obj.geometry.clone();
          obj.updateWorldMatrix(true, false);
          g.applyMatrix4(obj.matrixWorld);
          geos.push(g);
        }
      });
      if (!geos.length) throw new Error('이 파일 안에 메쉬(모양)가 없습니다.');
      geometry = geos.length === 1 ? geos[0] : mergeGeometries(geos, false);
    } else if (ext === 'stl') {
      geometry = await new STLLoader().loadAsync(url);
      // STL은 "위" 축을 정해둔 규격이 없는데, CAD·3D프린팅 쪽에서 만든 파일은 거의 항상 Z축을 위로 두고
      // 만든다(사용자 파일도 Z가 두께(5mm)였음). three.js는 Y축이 위라서, 그대로 불러오면 눕혀서 만든
      // 판이 세워진 것처럼 보인다(사용자 지적: "눕혀있는 파일인데 왜 서있는걸로 불러와???") — Z축을
      // Y축 자리로 돌려서 맞춘다.
      geometry.rotateX(-Math.PI / 2);
    } else if (ext === 'obj') {
      const obj = await new OBJLoader().loadAsync(url);
      const geos = [];
      obj.traverse((o) => { if (o.isMesh && o.geometry) geos.push(o.geometry); });
      if (!geos.length) throw new Error('이 파일 안에 메쉬(모양)가 없습니다.');
      geometry = geos.length === 1 ? geos[0] : mergeGeometries(geos, false);
    } else {
      throw new Error('지원하는 형식이 아닙니다(GLB/GLTF, STL, OBJ만 가능).');
    }
    geometry.computeBoundingBox();
    const size = new THREE.Vector3();
    geometry.boundingBox.getSize(size);
    if (Math.max(size.x, size.y, size.z) < 5) geometry.scale(1000, 1000, 1000);
    geometry.computeBoundingBox();
    const center = new THREE.Vector3();
    geometry.boundingBox.getCenter(center);
    geometry.translate(-center.x, -geometry.boundingBox.min.y, -center.z);
    return geometry;
  } finally {
    URL.revokeObjectURL(url);
  }
}
// 저장(spec.shapes)에는 원본 파일을 base64로 같이 넣어둔다 — 그래야 다른 컴퓨터에서 그 부품을 다시 열었을
// 때도 같은 모양을 다시 만들 수 있다(지오메트리 자체는 숫자 몇 개로 표현이 안 돼서 저장 못 함).
function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
function dataUrlToFile(dataUrl, fileName) {
  const [header, b64] = dataUrl.split(',');
  const mime = (header.match(/data:(.*?);base64/) || [])[1] || 'application/octet-stream';
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new File([bytes], fileName, { type: mime });
}

function round1(n) { return Math.round(n * 10) / 10; }

// 팔레트 타일에 이모지 대신 그 도형의 실제 3D 미리보기를 한 번 그려서 이미지로 박아 넣는다 — 팅커캐드
// 팔레트처럼(사용자가 실제 팅커캐드 스크린샷을 보여주며 "이모지 말고 이렇게" 지적).
// 도형마다 WebGLRenderer(=WebGL 컨텍스트)를 새로 만들었더니, dispose()를 불러도 브라우저가 그 컨텍스트
// 슬롯을 바로 회수해주지 않아서(GC가 나중에 돌 때까지 살아있음) 한 번에 15개를 연달아 만드는 동안 페이지
// 전체의 WebGL 컨텍스트 개수 한도(브라우저마다 보통 16개 안팎)를 넘겨버렸다 — 그 결과 이 페이지에서 먼저
// 떠 있던 "비교 대상 부품"(90도 프레임 위/정면) 같은 오래된 컨텍스트가 브라우저에 의해 강제로 잘려서
// 빈 화면(깨진 아이콘)으로 보이는 사고가 실제로 났다. 그래서 렌더러 하나를 15번 재사용한다.
function renderPaletteThumbnails(panel) {
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
    const mesh = new THREE.Mesh(buildShapeGeometry(shape), new THREE.MeshBasicMaterial({ color }));
    addEdgeOutline(mesh, color);
    scene.add(mesh);
    renderer.render(scene, camera);
    const btn = panel.querySelector('.paletteBtn[data-type="' + type + '"]');
    if (btn) btn.querySelector('.paletteThumb').src = canvas.toDataURL('image/png');
    mesh.geometry.dispose();
    mesh.material.dispose();
    mesh.children.forEach((c) => { c.geometry && c.geometry.dispose(); c.material && c.material.dispose(); });
  });
  renderer.dispose();
}

function initBoxEditor() {
  const { openPickerModal, openNamePromptModal, adminApi, getAccessToken, getSubject } = window.__partsLab;
  // "부품 만들기" 탭이 이 파일의 복사본(parts-lab-partmaker.js)으로 따로 떠 있을 수 있는데, 그쪽도
  // .paletteBtn/.paletteTabBtn/.tfModeBtn 같은 같은 클래스명을 그대로 쓴다. document.querySelectorAll로
  // 페이지 전체를 뒤지면 서로 다른 편집기의 버튼까지 같이 걸려서 두 탭이 서로 간섭한다 — 반드시 이 패널
  // 안에서만 찾아야 진짜 독립된 편집기가 된다.
  const panel = document.getElementById('boxEditorPanel');
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
    const wrap = panel.querySelector('.imgWrap');
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
    // 관성감쇠(damping)가 가라앉는 동안은 마우스를 놓아도 몇 프레임 더 카메라가 움직이므로, 그 프레임들도
    // 계속 그려지게 controls 자체의 'change' 이벤트로 dirty를 세운다.
    controls.addEventListener('change', () => { if (live) live.dirty = true; });
    return { renderer, scene, camera, controls };
  }
  // 사용자 지적("이상한 짓을 하고있네? 다른 3D 프로그램들은 이렇게 무거워지지 않던데") — 여기도 안 움직일
  // 때는 다시 그리지 않는다. #boxEditorPanel 전체에 위임 리스너 하나(아래 initBoxEditor 끝부분)를 달아서
  // 캔버스 드래그(오빗·기즈모)든 색상/밝기/뒤집기/각도 같은 바깥 입력칸 조작이든 뭐가 됐든 손대면
  // live.dirty를 세우고, 그 프레임만 그린 뒤 다시 잠잠해지면 렌더링을 건너뛴다.
  function startLoop(getState) {
    function loop() {
      const s = getState();
      s.controls.update();
      if (s.dirty) { s.renderer.render(s.scene, s.camera); s.dirty = false; }
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
      const color = shape.op === 'subtract' ? SUB_COLOR : materialColorForShape(shape, i);
      const mat = new THREE.MeshBasicMaterial({ color, transparent: shape.op === 'subtract', opacity: shape.op === 'subtract' ? 0.55 : 1 });
      const mesh = new THREE.Mesh(buildShapeGeometry(shape), mat);
      mesh.position.set(shape.x, shape.y, shape.z);
      mesh.rotation.set(shape.rx || 0, shape.ry || 0, shape.rz || 0);
      addEdgeOutline(mesh, color, i === selectedIndex);
      scene.add(mesh);
      return mesh;
    });
    const transform = new TransformControls(camera, renderer.domElement);
    transform.addEventListener('dragging-changed', (e) => { controls.enabled = !e.value; });
    transform.addEventListener('objectChange', () => syncSelectedShapeFromMesh(meshes));
    // 기즈모(이동/회전/크기 손잡이) 드래그 중에도 계속 다시 그려야 하므로 이것도 dirty를 세운다.
    transform.addEventListener('change', () => { if (live) live.dirty = true; });
    scene.add(transform.getHelper ? transform.getHelper() : transform);
    live = { renderer, scene, camera, controls, transform, meshes, rafId: 0, dirty: true };
    attachSelection();
    renderer.render(scene, camera);
    startLoop(() => live);
  }
  function attachSelection() {
    const activeBtn = panel.querySelector('.tfModeBtn.on');
    // 이동/회전/크기 버튼을 다시 눌러 끄면(아래 클릭 핸들러) 셋 다 off 상태가 될 수 있다 — 그럴 땐 도형을
    // 골랐어도 기즈모(조작 손잡이)를 보여주지 않는다(사용자 지시: "이동클릭하고 한번더 클릭하면 아무기능도
    // 활성화가 안되게끔").
    if (!live || !live.meshes.length || selectedIndex < 0 || !live.meshes[selectedIndex] || !activeBtn) {
      if (live && live.transform) live.transform.detach();
      return;
    }
    const mesh = live.meshes[selectedIndex];
    live.transform.attach(mesh);
    live.transform.setMode(activeBtn.dataset.mode);
  }
  // 도형을 고르면(목록 클릭·캔버스 클릭) 기즈모(attachSelection)와 별개로 테두리 색도 갱신한다 — 이동/
  // 회전/크기를 꺼둔 상태(기즈모 없음)에서도 어떤 도형이 선택돼 있는지 알 수 있어야 하기 때문(사용자 지시:
  // "부품을 클릭하면 부품이 선택되었다는 표시가 되었으면 좋겠어 — 테두리만 하이라이트 된다던가"). 도형이
  // 추가/삭제되어 전체를 다시 그리는 경우(addShape/delete/renderEditMode)는 이미 selectedIndex를 반영해
  // 새로 만들어지므로 여기서 다시 부를 필요 없다 — 이건 "같은 도형들, 선택만 바뀜"일 때만 쓴다.
  function updateSelectionHighlight() {
    if (!live) return;
    live.meshes.forEach((mesh, i) => {
      const shape = shapes[i];
      if (!shape) return;
      const color = shape.op === 'subtract' ? SUB_COLOR : materialColorForShape(shape, i);
      mesh.children.forEach((c) => c.geometry && c.geometry.dispose());
      mesh.clear();
      addEdgeOutline(mesh, color, i === selectedIndex);
    });
    live.dirty = true;
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
      addEdgeOutline(mesh, shape.op === 'subtract' ? SUB_COLOR : materialColorForShape(shape, selectedIndex), true);
    }
    applyFloorClamp(mesh, shape);
    renderShapeListUI();
    fillFieldsFromShape(shape);
  }

  // 여러 도형을 순서대로 더하기/빼기(CSG)한 최종 결과 하나를 계산 — 미리보기 렌더·STL 내보내기·(아래)
  // "비교 대상 부품" 등 다른 화면에서 spec.shapes를 그릴 때가 다 같이 쓴다. shapesArg를 안 주면 지금
  // 도형 에디터에서 편집 중인 shapes를 쓴다.
  function computeMergedBrush(shapesArg) {
    const list = shapesArg || shapes;
    if (!list.length) return null;
    const evaluator = new Evaluator();
    let result = new Brush(buildShapeGeometry(list[0]));
    result.position.set(list[0].x, list[0].y, list[0].z);
    result.rotation.set(list[0].rx || 0, list[0].ry || 0, list[0].rz || 0);
    result.updateMatrixWorld();
    for (let i = 1; i < list.length; i++) {
      const b = new Brush(buildShapeGeometry(list[i]));
      b.position.set(list[i].x, list[i].y, list[i].z);
      b.rotation.set(list[i].rx || 0, list[i].ry || 0, list[i].rz || 0);
      b.updateMatrixWorld();
      result = evaluator.evaluate(result, b, list[i].op === 'subtract' ? SUBTRACTION : ADDITION);
      result.updateMatrixWorld();
    }
    return result;
  }

  // "비교 대상 부품"/"수정할 부품"(parts-lab.html, 옛날 three.js)이 spec.shapes로 저장된 부품을 그릴 수
  // 있게 빌려주는 창구(사용자 지시: "3D파일로 업데이트 된건 이제 3D가 우선 되어야해~ svg파일은 보관만") —
  // 이 화면의 나머지 3D(브라켓/프레임)는 옛날 three.js라 진짜 CSG가 안 되므로, spec.shapes가 있는 부품은
  // 여기(최신 three.js+CSG 모듈) 것으로 그린다. 주어진 캔버스 하나에 독립적인 렌더러·궤도컨트롤·렌더
  // 루프를 새로 만들고, 그 캔버스가 문서에서 없어지면(다른 부품으로 교체됨) 스스로 멈추고 정리한다.
  async function renderShapesPreview(canvas, shapesData, camPos) {
    camPos = camPos || [150, 150, 150];
    const list = (shapesData || []).map((s) => Object.assign({}, s));
    await Promise.all(list.filter((s) => s.type === 'import' && s.fileDataUrl && !s._geometry).map(async (s) => {
      try { s._geometry = await loadImportedGeometry(dataUrlToFile(s.fileDataUrl, s.fileName || 'model')); }
      catch (e) { console.error('불러온 3D 파일을 다시 못 읽었어요.', e); }
    }));
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setSize(canvas.width, canvas.height, false);
    const scene = baseScene();
    const camera = new THREE.OrthographicCamera(-120, 120, 120, -120, 0.1, 6000);
    camera.position.set(camPos[0], camPos[1], camPos[2]);
    camera.lookAt(0, 0, 0);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 0);
    controls.enableDamping = true; controls.dampingFactor = 0.08;
    controls.update();
    const result = computeMergedBrush(list);
    if (result) {
      const finalColor = materialColorForShape(list[0], 0);
      result.material = new THREE.MeshBasicMaterial({ color: finalColor });
      addEdgeOutline(result, finalColor);
      scene.add(result);
    }
    // 안 움직일 땐 다시 안 그림(다른 3D 패널들과 같은 render-on-demand 방식) — 처음 한 번은 그려야 하니
    // dirty를 true로 시작.
    let dirty = true;
    controls.addEventListener('change', () => { dirty = true; });
    ['pointerdown', 'pointermove', 'pointerup', 'wheel'].forEach((evt) => {
      renderer.domElement.addEventListener(evt, () => { dirty = true; }, true);
    });
    (function loop() {
      if (!document.body.contains(canvas)) { renderer.dispose(); return; }
      requestAnimationFrame(loop);
      controls.update();
      if (dirty) { renderer.render(scene, camera); dirty = false; }
    })();
  }
  window.__boxEditorRenderShapes = renderShapesPreview;

  // ---------- 미리보기 모드: 실제 CSG로 더하고 뺀 최종 결과 하나만 보여줌(읽기 전용) ----------
  function renderPreviewMode() {
    teardownLive();
    const canvas = freshCanvas();
    const { renderer, scene, camera, controls } = setupCommon(canvas);
    if (!shapes.length) {
      live = { renderer, scene, camera, controls, transform: null, meshes: [], rafId: 0, dirty: true };
      renderer.render(scene, camera);
      startLoop(() => live);
      document.getElementById('boxEditorMsg').textContent = '도형이 없어요 — 팔레트에서 추가해보세요.';
      return;
    }
    document.getElementById('boxEditorMsg').textContent = '';
    const result = computeMergedBrush();
    // 최종 결과는 여러 도형을 합친 하나의 완성품이라 베이스 도형의 색 하나로 통일해서 보여준다.
    const finalColor = materialColorForShape(shapes[0], 0);
    result.material = new THREE.MeshBasicMaterial({ color: finalColor });
    addEdgeOutline(result, finalColor);
    scene.add(result);
    live = { renderer, scene, camera, controls, transform: null, meshes: [], rafId: 0, dirty: true };
    renderer.render(scene, camera);
    startLoop(() => live);
  }

  // 지금 만든 도형(들)을 하나의 STL 파일로 내보낸다(사용자 지시: "에디터에 있는것을 stl로 저장해서
  // 내보내기 하는 기능"). 화면에 보여주는 것과 같은 computeMergedBrush() 결과를 그대로 내보내서,
  // 미리보기에서 본 모양과 실제 파일이 항상 같게 한다.
  function exportSTL() {
    const msg = document.getElementById('boxEditorMsg');
    if (!shapes.length) { msg.className = 'msg err'; msg.textContent = '내보낼 도형이 없어요.'; return; }
    const result = computeMergedBrush();
    const exporter = new STLExporter();
    const stlText = exporter.parse(result, { binary: false });
    const blob = new Blob([stlText], { type: 'model/stl' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (targetPart ? targetPart.name : '부품') + '.stl';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    msg.className = 'msg ok';
    msg.textContent = 'STL 파일로 내보냈어요.';
  }

  function setMode(next) {
    mode = next;
    document.getElementById('boxPreviewBtn').hidden = mode === 'preview';
    document.getElementById('boxBackToEditBtn').hidden = mode === 'edit';
    panel.querySelectorAll('.paletteBtn').forEach((b) => { b.disabled = mode === 'preview'; });
    document.getElementById('shapeDeleteBtn').disabled = mode === 'preview';
    document.getElementById('boxRedrawBtn').disabled = mode === 'preview';
    document.getElementById('boxFlipBtn').disabled = mode === 'preview';
    document.getElementById('boxFlipYBtn').disabled = mode === 'preview';
    document.getElementById('boxPlaceOnPlaneBtn').disabled = mode === 'preview';
    if (mode === 'edit') renderEditMode(); else renderPreviewMode();
  }

  // ---------- 도형 목록 UI ----------
  function shapeLabel(shape, i) {
    const typeLabel = { box: '박스', wheel: '바퀴', gear: '톱니바퀴', sphere: '구', cone: '원뿔', pyramid: '각뿔', torus: '도넛', hexprism: '육각기둥', icosahedron: '다면체', dome: '반구', wedge: '지붕', ring: '고리', star: '별', heart: '하트', text: '텍스트', duplo: '휴벨리노 블록', knexRod: '케이넥스 막대', knexConnector: '케이넥스 커넥터', technicBeam: '테크닉 빔', import: '불러온 파일(' + (shape.fileName || '') + ')' }[shape.type];
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
    // "선택 도형 삭제" 버튼은 고른 도형이 있을 때만 보이게(사용자 지시: "도형을 선택했을때만 표시해줘") —
    // selectedIndex는 항상 이 함수 호출 직전에 바뀌므로, 여기 한 군데서만 처리해도 모든 경로에서 자동으로
    // 맞게 갱신된다.
    document.getElementById('shapeDeleteBtn').style.display = selectedIndex >= 0 ? '' : 'none';
  }
  function selectShape(i) {
    selectedIndex = i;
    fillFieldsFromShape(shapes[i]);
    renderShapeListUI();
    if (mode === 'edit') { attachSelection(); updateSelectionHighlight(); }
  }

  // ---------- 입력칸 <-> 선택된 도형 ----------
  // 도형 종류는 팔레트에서 고른 순간 정해지고 바뀌지 않는다(팅커캐드처럼 — 종류를 바꾸려면 지우고 팔레트에서
  // 다시 추가) — 그래서 드롭다운 없이 선택된 도형 자체의 type을 그대로 쓴다.
  function syncFieldVisibility(type) {
    // .hidden 속성은 이 파일의 CSS 명시도 때문에 안 먹혀서 style.display를 직접 건드린다.
    const boxLike = BOX_LIKE.includes(type);
    document.getElementById('boxOnlyFields').style.display = boxLike ? 'contents' : 'none';
    document.getElementById('roundFields').style.display = boxLike ? 'none' : 'contents';
    document.getElementById('shapeWidthField').style.display = (RADIUS_ONLY.includes(type) || type === 'import') ? 'none' : 'flex';
    document.getElementById('shapeRadiusLabel').closest('label').style.display = type === 'import' ? 'none' : '';
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
    const fieldsRow = panel.querySelector('.fieldsRow');
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
    {
      const hex = '#' + colorForShape(shape, selectedIndex).toString(16).padStart(6, '0');
      document.getElementById('shapeColor').value = hex;
      document.getElementById('shapeColorR').value = parseInt(hex.slice(1, 3), 16);
      document.getElementById('shapeColorG').value = parseInt(hex.slice(3, 5), 16);
      document.getElementById('shapeColorB').value = parseInt(hex.slice(5, 7), 16);
      document.getElementById('shapeBrightness').value = shape.brightness || 100;
    }
    if (BOX_LIKE.includes(shape.type)) {
      document.getElementById('boxW').value = round1(shape.w);
      document.getElementById('boxH').value = round1(shape.h);
      document.getElementById('boxD').value = round1(shape.d);
    } else if (shape.type !== 'import') {
      // 불러온 3D 파일은 크기가 파일 안 좌표로 정해져서(숫자로 계산하는 도형이 아님) 반지름/두께 칸이 없다.
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
      // 색상 팔레트로 고른 색도(있으면) 그대로 이어받는다 — 위치만 바꾸려고 "적용"을 눌러도 색이 안 없어지게.
      color: document.getElementById('shapeColor').value,
      brightness: Number(document.getElementById('shapeBrightness').value) || 100,
    };
    if (type === 'import') {
      // 불러온 파일 자체(지오메트리·원본 파일)는 숫자칸으로 다시 만드는 게 아니라 그대로 이어받는다 —
      // 안 그러면 위치만 바꾸려고 "이 도형에 적용"을 눌러도 불러온 모양이 사라져버린다.
      shape._geometry = prev._geometry; shape.fileName = prev.fileName; shape.fileDataUrl = prev.fileDataUrl;
    } else if (BOX_LIKE.includes(type)) {
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

  async function onBoxTargetPicked(p) {
    targetPart = p;
    document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + p.name;
    document.getElementById('boxSaveBtn').disabled = false;
    // 캔버스에 이미 도형이 있으면(한창 만들다가 "이제 이 부품에 저장할래" 하는 경우) 그 작업을 지우지
    // 않는다 — 예전엔 무조건 덮어써서, STL 불러와 만들어둔 걸 대상 고르자마자 날려버렸다(사용자 지적:
    // "이거하려고 다 수정한건데???"). 캔버스가 비어있을 때만(처음 시작할 때) 그 부품에 저장돼 있던
    // 도형을 불러와서 이어서 편집할 수 있게 한다.
    if (!shapes.length) {
      const saved = p.spec && Array.isArray(p.spec.shapes) && p.spec.shapes.length ? p.spec.shapes : null;
      shapes = saved ? saved.map((s) => Object.assign({}, s)) : [];
      // 저장된 도형 중 "3D 파일 불러오기"로 만든 게 있으면(type:'import'), 그때 저장해둔 원본 파일
      // (fileDataUrl)을 다시 읽어서 지오메트리를 새로 만들어야 화면에 그릴 수 있다 — 숫자만으로는
      // 못 그리는 도형이라(사용자 지시: "그 숫자로 매번 다시그린다는게 뭐야???" 질문에 답한 그 이유).
      await Promise.all(shapes.filter((s) => s.type === 'import' && s.fileDataUrl && !s._geometry).map(async (s) => {
        try { s._geometry = await loadImportedGeometry(dataUrlToFile(s.fileDataUrl, s.fileName || 'model')); }
        catch (e) { console.error('불러온 3D 파일을 다시 못 읽었어요.', e); }
      }));
      selectedIndex = shapes.length ? 0 : -1;
      fillFieldsFromShape(shapes[0]);
      renderShapeListUI();
      setMode('edit');
    }
  }

  document.getElementById('boxRedrawBtn').addEventListener('click', () => {
    if (!shapes[selectedIndex]) return;
    shapes[selectedIndex] = readFieldsAsShape();
    renderShapeListUI();
    renderEditMode();
  });
  // 물체 선택 후 색상 팔레트로 바로 색을 바꿀 수 있게(사용자 지시: "물체 선택후 색상팔레트 선택할수
  // 있게 해줘") — 다른 숫자칸과 달리 "이 도형에 적용" 버튼 없이 고르는 즉시 반영한다. 색을 바꾸는 경로가
  // 셋(색상칸 직접, 자주쓰는색 클릭, R/G/B 숫자칸)이라 실제 반영은 이 함수 하나로 모은다.
  // 밝기까지 반영한 실제 재질 색을 라이브 메쉬/미리보기에 반영 — 색상칸/RGB/밝기 슬라이더 어느 쪽을
  // 바꾸든 이 함수 하나로 모아서 처리한다.
  function refreshLiveShapeColor() {
    if (!shapes[selectedIndex]) return;
    const hex = '#' + materialColorForShape(shapes[selectedIndex], selectedIndex).toString(16).padStart(6, '0');
    if (mode === 'edit' && live && live.meshes[selectedIndex]) {
      live.meshes[selectedIndex].material.color.set(hex);
    } else if (mode === 'preview') {
      renderPreviewMode();
    }
  }
  function applyShapeColor(hex) {
    if (!shapes[selectedIndex]) return;
    shapes[selectedIndex].color = hex;
    document.getElementById('shapeColor').value = hex;
    const rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    document.getElementById('shapeColorR').value = rgb[0];
    document.getElementById('shapeColorG').value = rgb[1];
    document.getElementById('shapeColorB').value = rgb[2];
    refreshLiveShapeColor();
  }
  document.getElementById('shapeColor').addEventListener('input', (e) => applyShapeColor(e.target.value));
  // 밝기 슬라이더(사용자 지시: "명암을 더 밝게 해야할꺼 같아~ 안되면 명암조절 기능을 넣던가~~") — 100%가
  // 원래 색, 최대 200%까지 밝게. 색상 자체(shape.color)는 그대로 두고 렌더링에만 곱해서 적용.
  document.getElementById('shapeBrightness').addEventListener('input', (e) => {
    if (!shapes[selectedIndex]) return;
    shapes[selectedIndex].brightness = Number(e.target.value) || 100;
    refreshLiveShapeColor();
  });
  function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map((v) => Math.max(0, Math.min(255, Math.round(v) || 0)).toString(16).padStart(2, '0')).join('');
  }
  ['shapeColorR', 'shapeColorG', 'shapeColorB'].forEach((id) => {
    document.getElementById(id).addEventListener('input', () => {
      const r = Number(document.getElementById('shapeColorR').value) || 0;
      const g = Number(document.getElementById('shapeColorG').value) || 0;
      const b = Number(document.getElementById('shapeColorB').value) || 0;
      applyShapeColor(rgbToHex(r, g, b));
    });
  });
  // 자주 쓰는 색 10개 — 이 부품 체계에서 실제로 쓰는 아이보리(1열브라켓)·회색(90도 프레임)에, 팔레트
  // 기본색 몇 가지와 무채색(흰/검)을 더함.
  const COLOR_PRESETS = ['#f2ead9', '#c7cbd1', '#ffffff', '#555555', '#222222', '#5b8def', '#ff9f43', '#51cf66', '#e03b2b', '#fcc419'];
  document.getElementById('colorPresets').innerHTML = COLOR_PRESETS.map((hex) =>
    '<button type="button" data-hex="' + hex + '" title="' + hex + '" style="width:22px;height:22px;padding:0;border-radius:5px;border:1px solid #ccc;background:' + hex + ';cursor:pointer;"></button>'
  ).join('');
  document.getElementById('colorPresets').querySelectorAll('button').forEach((btn) => {
    btn.addEventListener('click', () => applyShapeColor(btn.dataset.hex));
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
  panel.querySelectorAll('.paletteBtn').forEach((btn) => {
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
  panel.querySelectorAll('.paletteTabBtn').forEach((tabBtn) => {
    tabBtn.addEventListener('click', () => {
      panel.querySelectorAll('.paletteTabBtn').forEach((b) => b.classList.toggle('on', b === tabBtn));
      panel.querySelectorAll('.paletteBtn').forEach((b) => {
        b.style.display = categoryOf(b.dataset.type) === tabBtn.dataset.category ? '' : 'none';
      });
    });
  });
  const canvasWrap = panel.querySelector('.imgWrap');
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
    if (!hit) {
      // 도형이 아니라 빈 바닥(모눈종이)을 클릭하면 선택을 해제한다(사용자 지적: "다른 바탕을 선택해도
      // 하이라이트가 안 없어지는데?" — 도형을 클릭했을 때 선택되는 것만 있고 빈 곳을 클릭해 선택 해제하는
      // 길이 없었음).
      if (selectedIndex !== -1) {
        selectedIndex = -1;
        fillFieldsFromShape(undefined);
        renderShapeListUI();
        attachSelection();
        updateSelectionHighlight();
      }
      return;
    }
    const idx = live.meshes.indexOf(hit.object);
    if (idx < 0 || idx === selectedIndex) return;
    selectedIndex = idx;
    fillFieldsFromShape(shapes[idx]);
    renderShapeListUI();
    attachSelection();
    updateSelectionHighlight();
  });
  document.getElementById('shapeDeleteBtn').addEventListener('click', () => {
    if (!shapes.length || selectedIndex < 0) return;
    shapes.splice(selectedIndex, 1);
    selectedIndex = shapes.length ? Math.max(0, selectedIndex - 1) : -1;
    fillFieldsFromShape(shapes[selectedIndex]);
    renderShapeListUI();
    renderEditMode();
  });
  // 이동/회전/크기 버튼 — 이미 켜져 있는 버튼을 다시 누르면 끄고(기즈모 없음), 아닌 버튼을 누르면 그
  // 버튼만 켠다(사용자 지시: "이동클릭하고 한번더 클릭하면 아무기능도 활성화가 안되게끔").
  panel.querySelectorAll('.tfModeBtn').forEach((b) => b.addEventListener('click', () => {
    const wasOn = b.classList.contains('on');
    panel.querySelectorAll('.tfModeBtn').forEach((x) => x.classList.remove('on'));
    if (!wasOn) b.classList.add('on');
    attachSelection();
    const showRotateRow = !wasOn && b.dataset.mode === 'rotate';
    document.getElementById('rotateAngleRow').style.display = showRotateRow ? 'flex' : 'none';
    if (showRotateRow) syncRotateAngleUI();
  }));
  // 사용자 지시: "중심으로 반대로 뒤집는 버튼, 위아래로 뒤집는 버튼 추가해줘" / "3D 관련 프로그램에서
  // 누가 시각을 뒤집니?" — 카메라가 아니라 선택된 도형 자체를 180도 돌린다(회전값이 shape에 저장되므로
  // 저장 버튼으로 그대로 남는다). "반대로"는 Y축(세로) 180도, "위아래로"는 X축(가로) 180도.
  function flipSelectedShape(axis){
    const shape = shapes[selectedIndex];
    if (!shape) return;
    shape['r' + axis] = (shape['r' + axis] || 0) + Math.PI;
    if (live && live.meshes[selectedIndex]) {
      const mesh = live.meshes[selectedIndex];
      mesh.rotation[axis] = shape['r' + axis];
      applyFloorClamp(mesh, shape);
    }
    fillFieldsFromShape(shape);
  }
  document.getElementById('boxFlipBtn').addEventListener('click', () => flipSelectedShape('y'));
  document.getElementById('boxFlipYBtn').addEventListener('click', () => flipSelectedShape('x'));
  // "작업 평면에 놓기"(팅커캐드 D 단축키) — 사용자 지시: "D는 각도를 수평을 만들고 바닥에 두는거야".
  // "바닥 위에 붙이기" 체크박스(이동할 때마다 자동으로, 바닥 아래로 파고들 때만 밀어올림)와 다르게
  // 버튼을 눌렀을 때 한 번만 실행되고, 체크박스 상태와 무관하게 항상 동작하며 떠 있어도 끌어내린다.
  // 기울어진 각도(rx/rz, 눕히는 방향)만 0으로 되돌리고 세로축 회전(ry, 어느 쪽을 보는지)은 그대로 둔다.
  function placeSelectedOnWorkplane() {
    const shape = shapes[selectedIndex];
    if (!shape || !live || !live.meshes[selectedIndex]) return;
    shape.rx = 0; shape.rz = 0;
    const mesh = live.meshes[selectedIndex];
    mesh.rotation.x = 0; mesh.rotation.z = 0;
    mesh.updateMatrixWorld(true);
    const worldBox = new THREE.Box3().setFromObject(mesh);
    mesh.position.y -= worldBox.min.y;
    shape.y = round1(mesh.position.y);
    syncRotateAngleUI();
    fillFieldsFromShape(shape);
  }
  document.getElementById('boxPlaceOnPlaneBtn').addEventListener('click', placeSelectedOnWorkplane);
  // 이름 입력칸 등에서 "d"를 칠 때 단축키가 끼어들면 안 되므로 입력 요소에 포커스가 있으면 무시하고,
  // 이 패널이 화면에 안 보이는 동안(다른 탭이 열려있을 때)도 무시한다(두 탭 다 이 리스너를 각자 갖고
  // 있어서, 안 보이는 탭 것까지 같이 반응하면 이중 실행됨).
  document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() !== 'd') return;
    const tag = document.activeElement && document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
    if (!panel.getClientRects().length || mode !== 'edit') return;
    e.preventDefault();
    placeSelectedOnWorkplane();
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
  // showAll=true — 프레임/브라켓뿐 아니라 등록된 부품 전체를 보여줘서, 어떤 부품이든 열어서 지금 만든
  // 도형(들)로 교체 저장할 수 있게 함(사용자 지시: "기존의 등록된 부품을 수정으로 열어서 교체하는 기능").
  document.getElementById('boxTargetPickBtn').addEventListener('click', () => {
    openPickerModal('기존 부품 열어서 교체', onBoxTargetPicked, true);
  });
  // 지금 만든 도형(들)을 완전히 새 부품으로 등록(사용자 지시: "부품등록쪽으로 저장하는기능") — 이름만
  // 입력받고, 나머지(아이콘·과목 등)는 기본값으로 채운 뒤 "스펙 수정" 등 기존 화면에서 더 정리할 수 있다.
  document.getElementById('boxNewPartBtn').addEventListener('click', async () => {
    const msg = document.getElementById('boxEditorMsg');
    if (!shapes.length) { msg.className = 'msg err'; msg.textContent = '등록할 도형이 없어요.'; return; }
    // 이름 입력칸을 버튼 옆에 항상 붙여두면 버튼 줄이 너무 길어져서 옆 팔레트가 화면 밖으로 밀려난다
    // (사용자 지적: "이부분이 너무 길어서 2번째 스샷부분이 밀리자나") — 버튼을 누른 순간에만 모달로 물어본다.
    const name = (await openNamePromptModal() || '').trim();
    if (!name) return;
    const btn = document.getElementById('boxNewPartBtn');
    btn.disabled = true; msg.textContent = '';
    try {
      const shapesToSave = shapes.map((s) => { const { _geometry, ...rest } = s; return rest; });
      const res = await adminApi({
        action: 'add_part', name, icon: '📦', subject: getSubject(), category: '',
        volumes: [], color: null, size: null,
        imageSvg: '', imageSvgDiagonal: '', primaryImage: 'front',
        spec: { shapes: shapesToSave },
      }, getAccessToken());
      const created = (res.parts || []).slice().reverse().find((p) => p.name === name);
      if (created) {
        targetPart = created;
        document.getElementById('boxTargetLabel').textContent = '선택된 부품: ' + created.name;
        document.getElementById('boxSaveBtn').disabled = false;
      }
      msg.className = 'msg ok';
      msg.textContent = '"' + name + '" 새 부품으로 등록했어요.';
    } catch (err) {
      msg.className = 'msg err';
      msg.textContent = '등록 실패: ' + err.message;
    } finally {
      btn.disabled = false;
    }
  });
  document.getElementById('boxExportStlBtn').addEventListener('click', exportSTL);
  // 팅커캐드처럼 GLB/GLTF·STL·OBJ 파일을 불러와서 다른 도형들과 똑같이 더하기/빼기 목록에 추가한다
  // (사용자 지시: "저장할 부품고르기 3D파일 불러올수있게 해줘" → "3가지 모두 불러올수 있게 해줘").
  document.getElementById('boxImportBtn').addEventListener('click', () => {
    document.getElementById('boxImportInput').click();
  });
  document.getElementById('boxImportInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    e.target.value = '';
    if (!file) return;
    const msg = document.getElementById('boxImportMsg');
    msg.textContent = '불러오는 중...';
    try {
      const geometry = await loadImportedGeometry(file);
      const fileDataUrl = await fileToDataUrl(file);
      const shape = { type: 'import', op: 'add', x: shapes.length * 25, y: 0, z: 0, rx: 0, ry: 0, rz: 0, fileName: file.name, fileDataUrl, _geometry: geometry };
      addShape(shape);
      msg.textContent = '"' + file.name + '" 불러왔어요.';
    } catch (err) {
      msg.textContent = '불러오기 실패: ' + err.message;
    }
  });
  async function saveToTargetPart() {
    const msg = document.getElementById('boxEditorMsg'), btn = document.getElementById('boxSaveBtn');
    // 이 부품에 이미 있던 다른 spec 필드(holeLabels 등)를 지우지 않도록 합쳐서 보낸다.
    // _geometry(불러온 3D 파일을 메모리에 캐시해둔 것)는 숫자·문자열이 아니라 저장(JSON)이 안 되므로 뺀다
    // — 대신 fileDataUrl(원본 파일 자체)이 저장되어 있어서, 다시 열 때 그걸로 지오메트리를 새로 만든다.
    const spec = Object.assign({}, targetPart.spec || {}, {
      shapes: shapes.map((s) => { const { _geometry, ...rest } = s; return rest; })
    });
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
      msg.className = 'msg ok'; msg.textContent = '"' + targetPart.name + '"에 저장했어요.';
    } catch (e) {
      msg.className = 'msg err'; msg.textContent = '저장 실패: ' + e.message;
    } finally {
      btn.disabled = false;
    }
  }
  // "저장"을 눌렀을 때 아직 저장할 부품을 안 골랐으면(위 "기존 부품 불러오기"를 안 눌렀으면) 그 자리에서
  // 바로 부품 목록을 띄운다(사용자 지적: "저장하기를 클릭하고 기존부품리스트에서 선택을 해야하는데 저장하기가
  // 안된다니까" — 버튼이 disabled라 그냥 눌리지 않는 것으로 보였음). 이미 도형이 있으면 onBoxTargetPicked가
  // shapes를 안 건드리고 targetPart만 채워주므로, 고른 직후 바로 이어서 저장까지 진행한다.
  document.getElementById('boxSaveBtn').addEventListener('click', async () => {
    if (!targetPart) {
      openPickerModal('저장할 부품 고르기', async (p) => {
        await onBoxTargetPicked(p);
        await saveToTargetPart();
      }, true);
      return;
    }
    await saveToTargetPart();
  });
  // "저장"이 한 번 부품을 고르면 그 뒤로는 다시 안 묻고 같은 부품에 바로 저장하는 것과 짝을 이루는 버튼
  // — 사용자 지적("두번째부터는 어디에 저장되는지 모르게 그냥 저장을 하고있어" → "다른부품은 저장안해??")으로,
  // "다른 부품으로 바꾸고 싶을 땐 어떻게 하냐"가 전혀 안 보이는 문제를 해결하려고 "저장" 버튼 바로 옆에
  // 명시적으로 둠(예전엔 맨 위 "🔍 기존 부품 불러오기"로만 가능했는데, 이름이 "불러오기"라 저장 대상을 바꾸는
  // 용도라는 게 전혀 안 드러났음). 부품을 고르면 그 즉시 그 부품에 저장까지 진행(다시 "저장"을 누를 필요 없음).
  document.getElementById('boxChangeTargetBtn').addEventListener('click', () => {
    openPickerModal('다른 부품에 저장', async (p) => {
      await onBoxTargetPicked(p);
      await saveToTargetPart();
    }, true);
  });

  // 색상칸·밝기 슬라이더·뒤집기 버튼·회전 각도 드롭다운·바닥붙이기 체크박스처럼 캔버스 바깥에서 라이브
  // 메쉬를 직접 건드리는 조작을 하나하나 다 찾아 고치는 대신, 이 패널 전체에 위임 리스너 하나로 걸어서
  // 뭐가 됐든 손대면 dirty를 세운다(사용자 지적: "다 최적화를 해" — 놓치는 곳 없게 넓게 잡음).
  document.getElementById('boxEditorPanel').addEventListener('input', () => { if (live) live.dirty = true; });
  document.getElementById('boxEditorPanel').addEventListener('change', () => { if (live) live.dirty = true; });
  document.getElementById('boxEditorPanel').addEventListener('click', () => { if (live) live.dirty = true; });

  // 처음엔 "기본 도형" 탭만 보이게 — 듀프로형/케이넥스형 버튼은 그 탭을 눌러야 나온다.
  const initialTab = panel.querySelector('.paletteTabBtn.on') || panel.querySelector('.paletteTabBtn');
  if (initialTab) {
    panel.querySelectorAll('.paletteBtn').forEach((b) => {
      b.style.display = categoryOf(b.dataset.type) === initialTab.dataset.category ? '' : 'none';
    });
  }
  renderPaletteThumbnails(panel);
  fillFieldsFromShape(shapes[0]);
  renderShapeListUI();
  renderEditMode();
}

window.initBoxEditor = initBoxEditor;
