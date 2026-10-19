// 부품 관리(index.html)에서 spec.shapes(부품 수리실에서 만든 3D 모델)를 실제로 그려서 보여주는 용도로만
// 쓰는 최소 뷰어 모듈 — 사용자 지시: "부품관리에 기존에 있는 내용은 부품수리실에서 새로 3D 모델이
// 업데이트 되면 보관해두고 대체된 3D모델을 보여줍니다 / 3D모델은 클릭했을경우 화면을 회전,줌,아웃,카메라
// 이동만 가능한 모달을 띄어서 보여줍니다". parts-lab-box-editor.js의 "비교 대상 부품" 화면을 위해 이미
// 만들어둔 renderShapesPreview와 같은 동작(빌드·CSG 계산·OrbitControls만 붙인 읽기 전용 렌더)이지만,
// 그 파일은 편집기(팔레트·TransformControls·저장 등) 전체를 초기화해야 해서 index.html이 그대로 가져다
// 쓸 수 없다 — 그리기에 필요한 부분(도형 지오메트리 생성 함수들 + CSG 합성 + 렌더 루프)만 이 파일에 따로
// 옮겨 담았다(parts-lab-box-editor.js/parts-lab-partmaker.js가 서로 독립 인스턴스로 복제돼 있는 것과 같은
// 이유 — 편집 기능이 전혀 없는 이 파일이 저 두 파일의 수정에 영향받지 않게).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { Evaluator, Brush, ADDITION, SUBTRACTION } from 'three-bvh-csg';

const IMPORT_COLOR = 0xf2ead9;
const SHAPE_PALETTE = [0x5b8def, 0xff9f43, 0x51cf66, 0xa78bfa, 0x22b8cf, 0xff6fa5, 0xfcc419, 0x37b24d, 0x748ffc, 0xf783ac, 0x66d9e8, 0xffa94d, 0x845ef7, 0x20c997, 0xf06595];
function colorForShape(shape, i) {
  if (shape.color) return Number('0x' + shape.color.slice(1));
  return shape.type === 'import' ? IMPORT_COLOR : SHAPE_PALETTE[i % SHAPE_PALETTE.length];
}
function materialColorForShape(shape, i) {
  const base = colorForShape(shape, i);
  const pct = shape.brightness || 100;
  if (pct === 100) return base;
  const scale = (c) => Math.min(255, Math.round(c * pct / 100));
  const r = scale((base >> 16) & 255), g = scale((base >> 8) & 255), b = scale(base & 255);
  return (r << 16) | (g << 8) | b;
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
function baseScene(withAxes) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf3f5f8);
  scene.add(new THREE.AmbientLight(0xffffff, 1.2));
  const dir = new THREE.DirectionalLight(0xffffff, 0.8); dir.position.set(100, 200, 100); scene.add(dir);
  if (withAxes) { scene.add(new THREE.GridHelper(200, 20, 0xcccccc, 0xe5e5e5)); scene.add(makeAxesRods(50)); }
  return scene;
}

let textFont = null;
try {
  textFont = await new FontLoader().loadAsync('https://cdn.jsdelivr.net/gh/mrdoob/three.js@r186/examples/fonts/helvetiker_regular.typeface.json');
} catch (e) {
  console.error('텍스트 도형용 폰트를 못 불러왔어요 — 텍스트 도형은 빈 박스로 대체됩니다.', e);
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
function duploGeometry(w, h, d) {
  const pitch = 16;
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
function technicBeamGeometry(w, h, d) {
  const pitch = 8;
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
    case 'import': return shape._geometry || new THREE.BoxGeometry(10, 10, 10);
    default: return new THREE.BoxGeometry(10, 10, 10);
  }
}
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
function dataUrlToFile(dataUrl, fileName) {
  const [header, b64] = dataUrl.split(',');
  const mime = (header.match(/data:(.*?);base64/) || [])[1] || 'application/octet-stream';
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new File([bytes], fileName, { type: mime });
}
async function resolveImportGeometries(shapesData) {
  const list = (shapesData || []).map((s) => Object.assign({}, s));
  await Promise.all(list.filter((s) => s.type === 'import' && s.fileDataUrl && !s._geometry).map(async (s) => {
    try { s._geometry = await loadImportedGeometry(dataUrlToFile(s.fileDataUrl, s.fileName || 'model')); }
    catch (e) { console.error('불러온 3D 파일을 다시 못 읽었어요.', e); }
  }));
  return list;
}
function computeMergedBrush(list) {
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
// 색칠 조각(shape.paint === true): 모양을 합치는 계산(CSG)에 넣지 않고, 부품 위에 자기 색으로 얹는다(예: DC모터의 축 결합 자리 빨강, 케이블 쪽 흰색).
// 부품 하나는 한 가지 색으로만 그려지는데, 일부만 다른 색으로 보이게 하는 방법이다.
function paintMatrix(s) {
  return new THREE.Matrix4().compose(new THREE.Vector3(s.x || 0, s.y || 0, s.z || 0), new THREE.Quaternion().setFromEuler(new THREE.Euler(s.rx || 0, s.ry || 0, s.rz || 0)), new THREE.Vector3(1, 1, 1));
}
function meshFromShapes(list) {
  const base = list.filter((s) => !s.paint), paints = list.filter((s) => s.paint);
  const result = computeMergedBrush(base);
  if (!result) return null;
  const finalColor = materialColorForShape(base[0], 0);
  result.material = new THREE.MeshBasicMaterial({ color: finalColor });
  addEdgeOutline(result, finalColor);
  paints.forEach((s) => {
    const g = buildShapeGeometry(s); g.applyMatrix4(paintMatrix(s));
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: materialColorForShape(s, 0) }));
    result.add(m); // 합성 결과가 첫 도형의 위치·회전을 물려받으므로 첫 도형이 원점이면 그대로 맞는다
  });
  return result;
}

// 부품 관리 모달용 — 캔버스 하나에 독립 렌더러·궤도컨트롤(회전·줌·이동만, 편집 도구 없음)·렌더 루프를
// 새로 만든다. 그 캔버스가 문서에서 없어지면(모달 닫힘 → innerHTML 교체) 스스로 멈추고 정리한다
// (parts-lab-box-editor.js의 renderShapesPreview와 동일한 패턴).
async function renderShapesPreview(canvas, shapesData, camPos) {
  camPos = camPos || [150, 150, 150];
  const list = await resolveImportGeometries(shapesData);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(canvas.width, canvas.height, false);
  const scene = baseScene(true);
  const camera = new THREE.OrthographicCamera(-120, 120, 120, -120, 0.1, 6000);
  const mesh = meshFromShapes(list);
  // 부품의 실제 중심이 원점(0,0,0)이 아닐 수 있다(듀프로/휴벨리노 블록처럼 스터드가 한쪽에 몰린 모양 등) —
  // 원점만 보고 원점 기준으로 회전하면 부품이 화면 한쪽으로 치우쳐 보이고 돌릴 때도 부품 밖의 점을
  // 중심으로 빙빙 도는 것처럼 보인다(사용자 지적: "이런거 중심을 좀 맞춰줘"). 카메라·궤도컨트롤 모두
  // 부품의 실제 바운딩박스 중심을 보게 한다.
  const center = new THREE.Vector3();
  if (mesh) { mesh.updateMatrixWorld(true); new THREE.Box3().setFromObject(mesh).getCenter(center); }
  camera.position.set(camPos[0] + center.x, camPos[1] + center.y, camPos[2] + center.z);
  camera.lookAt(center);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(center);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.update();
  if (mesh) scene.add(mesh);
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

// 목록 썸네일용 — 부품마다 새 WebGLRenderer를 만들면 WebGL 컨텍스트 소진 문제가 재발하므로(이미 겪은 버그,
// parts-lab-box-editor.js의 renderPaletteThumbnails와 같은 이유) 렌더러 하나를 재사용해서 정지 이미지
// (dataURL)만 뽑아 <img>로 박아 넣는다. 인터랙션은 모달에서만 필요하고 목록에서는 필요 없음.
let sharedThumbRenderer = null;
async function renderShapesThumbnail(shapesData, size) {
  size = size || 88;
  if (!sharedThumbRenderer) {
    const c = document.createElement('canvas');
    sharedThumbRenderer = new THREE.WebGLRenderer({ canvas: c, antialias: true, alpha: true, preserveDrawingBuffer: true });
  }
  sharedThumbRenderer.setSize(size, size, false);
  const list = await resolveImportGeometries(shapesData);
  const scene = baseScene(false);
  // 목록 카드의 배경색은 화면마다 다르다(index.html은 흰색, design.html 부품 팔레트는 연한 파랑, 다크
  // 모드는 또 다름) — baseScene()의 고정 배경색(연회색 #f3f5f8)을 그대로 구우면 카드 배경과 어긋나 보인다
  // (사용자 지적: "배경색을 맞춰줄수 있을까?"). 투명 배경으로 찍어서 카드 배경이 자연스럽게 비치게 한다.
  scene.background = null;
  const camera = new THREE.OrthographicCamera(-70, 70, 70, -70, 0.1, 6000);
  const mesh = meshFromShapes(list);
  if (mesh) {
    scene.add(mesh);
    // 정육면체를 안전하게 담을 수 있는 대각선 반지름 대신, 지금 이 카메라 각도에서 실제로 화면에
    // 투영되는 가로/세로 폭만큼만 프레임을 잡는다 — 큰 부품은 안 잘리고, 작은 부품은 칸을 꽉 채운다
    // (사용자 지적: "너무 작아~~ 사각형에 최대한 맞춰줘봐").
    mesh.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(mesh);
    const center = new THREE.Vector3();
    box.getCenter(center);
    // 부품의 실제 중심이 원점이 아닐 수 있다(듀프로/휴벨리노 블록처럼 스터드가 한쪽에 몰린 모양 등) —
    // 원점만 보고 프레임을 잡으면 부품이 썸네일 한쪽으로 치우쳐 보인다(사용자 지적: "2단블록/3단블록
    // 이런거 중심을 좀 맞춰줘"). 카메라를 그 중심 기준으로 옮기고 그 중심을 바라보게 한다.
    camera.position.set(90 + center.x, 90 + center.y, 90 + center.z);
    camera.lookAt(center);
    camera.updateMatrixWorld();
    const right = new THREE.Vector3(), up = new THREE.Vector3(), forward = new THREE.Vector3();
    camera.matrixWorld.extractBasis(right, up, forward);
    let maxRight = 0, maxUp = 0;
    for (let i = 0; i < 8; i++) {
      const corner = new THREE.Vector3(
        i & 1 ? box.max.x : box.min.x,
        i & 2 ? box.max.y : box.min.y,
        i & 4 ? box.max.z : box.min.z
      ).sub(center);
      maxRight = Math.max(maxRight, Math.abs(corner.dot(right)));
      maxUp = Math.max(maxUp, Math.abs(corner.dot(up)));
    }
    let half = Math.max(maxRight, maxUp, 1) * 1.08;
    if (!Number.isFinite(half) || half <= 0) half = 60;
    camera.left = -half; camera.right = half; camera.top = half; camera.bottom = -half;
    camera.updateProjectionMatrix();
  } else {
    camera.position.set(90, 90, 90);
    camera.lookAt(0, 0, 0);
  }
  sharedThumbRenderer.render(scene, camera);
  const dataUrl = sharedThumbRenderer.domElement.toDataURL('image/png');
  if (mesh) { mesh.geometry.dispose(); mesh.material.dispose(); }
  return dataUrl;
}

// index.html은 이 파일을 <script type="module">로 그대로 로드해서 쓴다 — export 대신 window에 직접
// 붙여서, index.html의 일반(classic) 스크립트에서 바로 호출할 수 있게 한다(부품 만들기 쪽이
// window.__partsLab로 반대 방향 정보를 주고받는 것과 같은 다리 역할).
// 설계 화면(design.html)이 캔버스에 놓는 부품을 등록된 3D 모델로 그릴 수 있게, spec.shapes를 합성한 모양의 원시 배열
// (위치·법선·인덱스·색)만 꺼내 준다 — 설계 화면은 이 모듈과 다른 three 인스턴스를 쓰므로 객체 대신 숫자 배열로 넘긴다.
async function buildPartGeometryData(shapesData) {
  const list = await resolveImportGeometries(shapesData);
  const baseList = list.filter((s) => !s.paint), paintList = list.filter((s) => s.paint);
  const mesh = meshFromShapes(baseList);
  if (!mesh) return null;
  mesh.updateMatrixWorld(true);
  const geo = mesh.geometry.clone();
  geo.applyMatrix4(mesh.matrixWorld); // 합성 결과가 첫 도형의 위치·회전을 물려받으므로 실제 좌표로 굽는다
  if (!geo.attributes.normal) geo.computeVertexNormals();
  geo.computeBoundingBox();
  const b = geo.boundingBox;
  return {
    position: new Float32Array(geo.attributes.position.array),
    normal: new Float32Array(geo.attributes.normal.array),
    index: geo.index ? new Uint32Array(geo.index.array) : null,
    color: materialColorForShape(baseList[0], 0),
    bbox: { min: [b.min.x, b.min.y, b.min.z], max: [b.max.x, b.max.y, b.max.z] },
    // 색칠 조각: 부품 본체와 같은 좌표(가운데 맞추기 전)로 구운 점·면과 자기 색
    paints: paintList.map((s) => {
      const g = buildShapeGeometry(s); g.applyMatrix4(paintMatrix(s));
      if (!g.attributes.normal) g.computeVertexNormals();
      return { position: new Float32Array(g.attributes.position.array), normal: new Float32Array(g.attributes.normal.array), index: g.index ? new Uint32Array(g.index.array) : null, color: materialColorForShape(s, 0) };
    }),
  };
}
window.__partsLabViewer = { renderShapesPreview, renderShapesThumbnail, buildPartGeometryData };
