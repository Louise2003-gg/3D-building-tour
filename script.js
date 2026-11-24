import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const container = document.getElementById('viewer');
const loading = document.getElementById('loading');

const scene = new THREE.Scene();
scene.background = new THREE.Color('#dfe0dc');
scene.fog = new THREE.Fog('#dfe0dc', 34, 58);

const camera = new THREE.PerspectiveCamera(38, container.clientWidth / container.clientHeight, 0.05, 150);
camera.up.set(0, 0, 1);
const overviewTarget = new THREE.Vector3(0, 0, 1.2);
const overviewDirection = new THREE.Vector3(0.45, -0.52, 0.72).normalize();
const halfHorizontalFov = Math.atan(
  Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) *
  (container.clientWidth / container.clientHeight)
);
const overviewPosition = overviewTarget.clone().addScaledVector(
  overviewDirection,
  (10.2 / Math.sin(halfHorizontalFov)) * 1.08
);
camera.position.copy(overviewPosition);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enablePan = true;
controls.minDistance = 12;
controls.maxDistance = 48;
controls.maxPolarAngle = Math.PI * 0.48;
controls.target.copy(overviewTarget);
controls.update();

scene.add(new THREE.HemisphereLight('#fffaf2', '#7d7467', 2.15));

const sun = new THREE.DirectionalLight('#fff5df', 3.1);
sun.position.set(-12, -16, 24);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -16;
sun.shadow.camera.right = 16;
sun.shadow.camera.top = 16;
sun.shadow.camera.bottom = -16;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 48;
sun.shadow.bias = -0.0002;
scene.add(sun);

const fill = new THREE.DirectionalLight('#ffe5d2', 1.05);
fill.position.set(14, 12, 10);
scene.add(fill);

const materials = {
  cream: new THREE.MeshStandardMaterial({ color: '#efe3cf', roughness: 0.62 }),
  warmWhite: new THREE.MeshStandardMaterial({ color: '#fffaf0', roughness: 0.48 }),
  oak: new THREE.MeshStandardMaterial({ color: '#c79a67', roughness: 0.55 }),
  paleOak: new THREE.MeshStandardMaterial({ color: '#dfba82', roughness: 0.48 }),
  darkOak: new THREE.MeshStandardMaterial({ color: '#9b7046', roughness: 0.58 }),
  blush: new THREE.MeshStandardMaterial({ color: '#dfa6a1', roughness: 0.68 }),
  blue: new THREE.MeshStandardMaterial({ color: '#91bdc2', roughness: 0.68 }),
  mint: new THREE.MeshStandardMaterial({ color: '#9bbfa9', roughness: 0.68 }),
  yellow: new THREE.MeshStandardMaterial({ color: '#eccb78', roughness: 0.68 }),
  pink: new THREE.MeshStandardMaterial({ color: '#cf7781', roughness: 0.68 }),
  green: new THREE.MeshStandardMaterial({ color: '#507a50', roughness: 0.72 }),
  dark: new THREE.MeshStandardMaterial({ color: '#30302e', roughness: 0.38 }),
  brass: new THREE.MeshStandardMaterial({ color: '#c79a55', metalness: 0.5, roughness: 0.28 }),
  glass: new THREE.MeshPhysicalMaterial({
    color: '#a7d0d1',
    transparent: true,
    opacity: 0.25,
    roughness: 0.08,
    metalness: 0,
    transmission: 0.3
  }),
  rugDark: new THREE.MeshStandardMaterial({ color: '#c6a4a0', roughness: 0.9 }),
};

function mesh(geometry, material, position, rotation = null) {
  const object = new THREE.Mesh(geometry, material);
  object.position.set(position[0], position[1], position[2]);
  if (rotation) object.rotation.set(rotation[0], rotation[1], rotation[2]);
  object.castShadow = true;
  object.receiveShadow = true;
  return object;
}

function box(name, size, position, material, rotation = null) {
  const object = mesh(new THREE.BoxGeometry(size[0], size[1], size[2]), material, position, rotation);
  object.name = name;
  return object;
}

function cylinder(name, radiusTop, radiusBottom, height, position, material, segments = 32, rotation = null) {
  const object = mesh(new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments), material, position, rotation);
  object.name = name;
  return object;
}

function sphere(name, radius, position, material, scale = null) {
  const object = mesh(new THREE.SphereGeometry(radius, 24, 16), material, position);
  object.name = name;
  if (scale) object.scale.set(scale[0], scale[1], scale[2]);
  return object;
}

function roundedCounter(name, width, depth, height, position, material) {
  const group = new THREE.Group();
  group.name = name;

  const body = box(`${name}-body`, [width - 0.8, depth, height], [0, 0, height / 2], material);
  group.add(body);
  for (const x of [-width / 2 + 0.4, width / 2 - 0.4]) {
    group.add(cylinder(`${name}-rounded-end`, depth / 2, depth / 2, height, [x, 0, height / 2], material, 32));
  }
  group.position.set(position[0], position[1], position[2]);
  group.traverse((child) => { if (child.isMesh) { child.castShadow = true; child.receiveShadow = true; } });
  return group;
}

function makeLabelTexture(title, subtitle = '', accent = '#40352d', bg = '#fffaf0') {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = accent;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '800 106px Arial';
  ctx.fillText(title, canvas.width / 2, subtitle ? 116 : 128);
  if (subtitle) {
    ctx.font = '700 30px Arial';
    ctx.fillStyle = '#8b6d62';
    ctx.fillText(subtitle, canvas.width / 2, 202);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return texture;
}

function makeWallSign(title, subtitle, position, width = 3.4) {
  const material = new THREE.MeshStandardMaterial({
    map: makeLabelTexture(title, subtitle),
    transparent: false,
    roughness: 0.75
  });
  const sign = mesh(new THREE.PlaneGeometry(width, width * 0.25), material, position);
  sign.rotation.x = Math.PI / 2;
  sign.receiveShadow = true;
  return sign;
}

function makeNurseryRug() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f1caca';
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = '#f7e1df';
  for (let i = 0; i < 18; i++) {
    ctx.beginPath();
    ctx.arc((i * 83) % 512, (i * 137) % 512, 35, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.strokeStyle = '#e99a9d';
  ctx.lineWidth = 12;
  ctx.beginPath();
  ctx.moveTo(100, 355);
  ctx.quadraticCurveTo(170, 300, 240, 350);
  ctx.quadraticCurveTo(290, 390, 360, 330);
  ctx.stroke();
  ctx.fillStyle = '#b98a6c';
  ctx.beginPath();
  ctx.arc(256, 288, 42, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#5e4a40';
  ctx.beginPath();
  ctx.arc(238, 278, 5, 0, Math.PI * 2);
  ctx.arc(274, 278, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#5e4a40';
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.arc(256, 300, 15, 0.2, Math.PI - 0.2);
  ctx.stroke();
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return new THREE.MeshStandardMaterial({ map: texture, roughness: 0.92 });
}

function addPlant(parent, x, y, z = 0.28, size = 1) {
  const pot = cylinder('terracotta-planter', 0.38 * size, 0.30 * size, 0.65 * size, [x, y, z], materials.cream, 24);
  parent.add(pot);
  for (let i = 0; i < 9; i++) {
    const angle = i * 2.399;
    const height = 0.78 + (i % 3) * 0.12;
    const leaf = mesh(
      new THREE.SphereGeometry(0.24 * size, 16, 10),
      i % 2 ? materials.green : new THREE.MeshStandardMaterial({ color: '#668d58', roughness: 0.78 }),
      [x + Math.cos(angle) * 0.22 * size, y + Math.sin(angle) * 0.22 * size, z + height * size],
      [0.5, angle, 0.2]
    );
    leaf.scale.set(1.15, 0.25, 1.8);
    parent.add(leaf);
  }
}

function addClothingRack(parent, x, y, rotation = 0) {
  const rack = new THREE.Group();
  rack.position.set(x, y, 0);
  rack.rotation.z = rotation;
  rack.name = 'clothing-rack';
  rack.add(cylinder('rack-post', 0.055, 0.055, 2.45, [-1.15, 0, 1.3], materials.darkOak, 16));
  rack.add(cylinder('rack-post', 0.055, 0.055, 2.45, [1.15, 0, 1.3], materials.darkOak, 16));
  rack.add(cylinder('rack-bar', 0.045, 0.045, 2.3, [0, 0, 2.45], materials.brass, 16, [0, 0, Math.PI / 2]));
  for (let i = -4; i <= 4; i++) {
    const garmentMat = [materials.blush, materials.warmWhite, materials.blue, materials.cream][(i + 4) % 4];
    rack.add(box('clothing-hanger', [0.46, 0.05, 0.9], [i * 0.22, 0, 1.84], garmentMat));
    rack.add(sphere('hanger-head', 0.07, [i * 0.22, 0, 2.29], materials.brass));
  }
  parent.add(rack);
}

function addTeddy(parent, x, y, z, scale = 1, color = '#b98055') {
  const teddyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.86 });
  const teddy = new THREE.Group();
  teddy.position.set(x, y, z);
  teddy.scale.setScalar(scale);
  teddy.add(sphere('teddy-body', 0.48, [0, 0, 0.48], teddyMat));
  teddy.add(sphere('teddy-head', 0.39, [0, 0, 1.05], teddyMat));
  teddy.add(sphere('teddy-ear', 0.16, [-0.28, 0, 1.36], teddyMat));
  teddy.add(sphere('teddy-ear', 0.16, [0.28, 0, 1.36], teddyMat));
  teddy.add(sphere('teddy-eye', 0.045, [-0.12, -0.34, 1.11], materials.dark));
  teddy.add(sphere('teddy-eye', 0.045, [0.12, -0.34, 1.11], materials.dark));
  teddy.add(sphere('teddy-muzzle', 0.11, [0, -0.36, 0.98], materials.cream));
  teddy.add(cylinder('teddy-arm', 0.13, 0.13, 0.65, [-0.48, 0, 0.52], teddyMat, 20, [0, 0, 0.45]));
  teddy.add(cylinder('teddy-arm', 0.13, 0.13, 0.65, [0.48, 0, 0.52], teddyMat, 20, [0, 0, -0.45]));
  teddy.add(sphere('teddy-foot', 0.22, [-0.26, -0.08, 0.16], teddyMat, [1.2, 0.7, 1]));
  teddy.add(sphere('teddy-foot', 0.22, [0.26, -0.08, 0.16], teddyMat, [1.2, 0.7, 1]));
  parent.add(teddy);
}

function addStore(parent) {
  // Back wall shelving
  for (let row = 0; row < 3; row++) {
    const y = 5.4 - row * 1.05;
    const shelf = new THREE.Group();
    shelf.position.set(-3.9, y, 0);
    shelf.add(box('store-shelf-case', [5.8, 0.42, 1.15], [0, 0, 1], materials.oak));
    shelf.add(box('store-shelf-back', [5.58, 0.05, 1.02], [0, 0.19, 1], materials.cream));
    for (const z of [0.55, 1.08, 1.55]) shelf.add(box('store-shelf-board', [5.75, 0.48, 0.055], [0, 0, z], materials.paleOak));
    for (let i = 0; i < 8; i++) {
      const productMat = [materials.blush, materials.blue, materials.mint, materials.yellow, materials.cream][(i + row) % 5];
      shelf.add(box('store-product', [0.48, 0.30, 0.38], [-2.45 + i * 0.70, -0.02, 0.73], productMat));
      shelf.add(box('store-product', [0.48, 0.30, 0.32], [-2.45 + i * 0.70, -0.02, 1.30], productMat));
    }
    parent.add(shelf);
  }

  addClothingRack(parent, -8.1, 4.2, Math.PI / 2);
  addClothingRack(parent, -8.1, 2.2, Math.PI / 2);
  addPlant(parent, -8.4, 5.8, 0.2, 1.15);
  addTeddy(parent, -8.45, 5.15, 1.8, 0.72);
  addTeddy(parent, -7.15, 5.15, 1.8, 0.62, '#d7c2a2');

  // Center freestanding merchandise table
  const table = new THREE.Group();
  table.position.set(-4.1, 1.25, 0);
  table.add(box('store-display-table-top', [4.6, 1.15, 0.12], [0, 0, 0.72], materials.paleOak));
  for (const x of [-2.0, 2.0]) table.add(box('store-display-leg', [0.12, 0.95, 0.62], [x, 0, 0.36], materials.darkOak));
  for (let i = 0; i < 5; i++) {
    table.add(box('store-folded-babywear', [0.62, 0.55, 0.23], [-1.7 + i * 0.85, 0, 0.88], [materials.warmWhite, materials.blush, materials.blue, materials.mint, materials.yellow][i]));
  }
  parent.add(table);

  // Baby baskets and wall decor
  for (let i = 0; i < 3; i++) {
    parent.add(cylinder('store-basket', 0.38, 0.30, 0.72, [-7.7 + i * 0.9, 0.65, 0.36], materials.warmWhite, 24));
  }
  parent.add(makeWallSign('STORE', '', [-4.1, 6.72, 2.62], 3.2));
  parent.add(box('store-framed-art', [1.0, 0.08, 1.25], [-9.6, 2.0, 1.9], materials.paleOak));
}

function addReception(parent) {
  const counter = roundedCounter('curved-reception', 7.2, 1.25, 1.32, [-5.0, -3.55, 0.05], materials.cream);
  parent.add(counter);
  const top = box('reception-white-top', [7.55, 1.45, 0.12], [-5.0, -3.55, 1.48], materials.warmWhite);
  top.geometry.translate(0, 0, 0);
  parent.add(top);
  parent.add(box('reception-oak-front', [6.55, 0.10, 0.62], [-5.0, -4.16, 0.64], materials.paleOak));
  const underglow = new THREE.PointLight('#ffd9a3', 1.4, 5.5);
  underglow.position.set(-5.0, -4.25, 0.45);
  parent.add(underglow);

  const monitor = new THREE.Group();
  monitor.name = 'reception-monitor';
  monitor.add(box('monitor-screen', [1.48, 0.12, 0.92], [-5.0, -3.48, 1.92], materials.dark));
  monitor.add(box('monitor-screen-face', [1.34, 0.02, 0.78], [-5.0, -3.40, 1.92], new THREE.MeshStandardMaterial({ color: '#dfeaf0', roughness: 0.3 })));
  monitor.add(cylinder('monitor-neck', 0.07, 0.07, 0.32, [-5.0, -3.48, 1.35], materials.dark, 16));
  parent.add(monitor);

  parent.add(makeWallSign('FRONT DESK', 'baby reception', [-5.0, -4.23, 1.05], 3.6));
  for (const x of [-7.2, -6.6, -5.9]) {
    parent.add(cylinder('reception-baby-bottle', 0.09, 0.11, 0.38, [x, -3.45, 1.68], materials.warmWhite, 20));
  }
  parent.add(sphere('reception-flower', 0.18, [-3.7, -3.45, 1.62], materials.blush));
  parent.add(sphere('reception-flower', 0.14, [-3.45, -3.45, 1.66], materials.warmWhite));
  parent.add(cylinder('reception-vase', 0.15, 0.22, 0.30, [-3.55, -3.45, 1.55], materials.blue, 20));
  parent.add(makeWallSign('BABY', '', [-5.0, -4.25, 0.92], 0.9));
}

function addWaiting(parent) {
  const rug = box('waiting-rug', [6.1, 3.4, 0.025], [-5.4, -5.45, 0.18], materials.rugDark);
  parent.add(rug);

  for (const x of [-7.25, -3.55]) {
    const chair = new THREE.Group();
    chair.position.set(x, -5.45, 0);
    chair.add(box('waiting-chair-seat', [1.75, 1.15, 0.32], [0, 0, 0.55], materials.cream));
    chair.add(box('waiting-chair-back', [1.75, 0.28, 1.15], [0, 0.52, 1.12], materials.cream));
    for (const lx of [-0.65, 0.65]) chair.add(cylinder('chair-leg', 0.07, 0.07, 0.48, [lx, 0, 0.24], materials.darkOak, 16));
    parent.add(chair);
  }

  const table = new THREE.Group();
  table.position.set(-5.4, -5.45, 0);
  table.add(cylinder('waiting-coffee-top', 0.82, 0.82, 0.12, [0, 0, 0.68], materials.paleOak, 32));
  table.add(cylinder('waiting-coffee-base', 0.09, 0.09, 0.62, [0, 0, 0.34], materials.darkOak, 16));
  table.add(cylinder('waiting-coffee-foot', 0.35, 0.35, 0.08, [0, 0, 0.08], materials.darkOak, 32));
  parent.add(table);

  parent.add(cylinder('waiting-bin', 0.24, 0.24, 0.48, [-8.55, -5.75, 0.24], materials.blue, 20));
  addPlant(parent, -8.55, -6.25, 0.2, 0.9);
  addPlant(parent, -1.9, -5.95, 0.2, 0.9);
}

function addNursery(parent) {
  parent.add(makeWallSign('NURSERY', '', [5.2, 6.72, 2.62], 3.8));
  parent.add(makeWallSign('BABY', '', [5.2, 6.73, 2.05], 1.4));

  const activityRug = mesh(new THREE.PlaneGeometry(7.2, 4.8), makeNurseryRug(), [5.2, 1.25, 0.185]);
  activityRug.rotation.x = -Math.PI / 2;
  activityRug.receiveShadow = true;
  parent.add(activityRug);

  // Toy cabinet along back wall
  const cabinet = new THREE.Group();
  cabinet.position.set(5.2, 5.45, 0);
  cabinet.add(box('nursery-cabinet', [5.8, 0.62, 1.18], [0, 0, 0.72], materials.paleOak));
  cabinet.add(box('nursery-cabinet-top', [6.0, 0.76, 0.10], [0, 0, 1.38], materials.cream));
  for (let i = -2; i <= 2; i++) {
    cabinet.add(box('nursery-cubbies', [0.08, 0.68, 1.02], [i * 1.12, -0.34, 0.72], materials.darkOak));
  }
  for (let i = -2; i <= 2; i++) {
    const toyMat = [materials.blush, materials.blue, materials.yellow, materials.mint][(i + 2) % 4];
    cabinet.add(sphere('nursery-toy', 0.20, [i * 1.12, -0.40, 1.08], toyMat));
  }
  parent.add(cabinet);

  addTeddy(parent, 7.75, 5.25, 1.0, 1.15);
  addPlant(parent, 3.0, 5.75, 0.2, 1.0);

  // Crib on the right
  const crib = new THREE.Group();
  crib.position.set(7.8, 2.55, 0);
  crib.add(box('crib-mattress', [2.65, 1.75, 0.16], [0, 0, 0.72], materials.warmWhite));
  crib.add(box('crib-end', [2.65, 0.12, 1.35], [0, 0.82, 1.22], materials.paleOak));
  crib.add(box('crib-end', [2.65, 0.12, 1.35], [0, -0.82, 1.22], materials.paleOak));
  for (const x of [-1.15, -0.58, 0, 0.58, 1.15]) {
    crib.add(cylinder('crib-slat', 0.045, 0.045, 1.12, [x, -0.82, 1.18], materials.paleOak, 12));
  }
  parent.add(crib);

  // Framed nursery art
  parent.add(box('nursery-frame', [1.15, 0.08, 1.42], [9.55, 3.25, 2.0], materials.paleOak));
  parent.add(box('nursery-art', [0.92, 0.02, 1.16], [9.55, 3.18, 2.0], materials.warmWhite));

  // Illustrated center activity table
  const table = new THREE.Group();
  table.position.set(5.2, 1.05, 0);
  table.add(cylinder('nursery-table-top', 1.45, 1.45, 0.12, [0, 0, 0.78], materials.warmWhite, 48));
  table.add(cylinder('nursery-table-leg', 0.10, 0.10, 0.72, [0, 0, 0.38], materials.darkOak, 16));
  table.add(cylinder('nursery-table-base', 0.55, 0.55, 0.08, [0, 0, 0.06], materials.darkOak, 32));
  parent.add(table);

  const chairPositions = [
    [3.45, 0.55, materials.yellow],
    [6.95, 0.55, materials.blush],
    [3.45, 1.75, materials.mint],
    [6.95, 1.75, materials.blue],
  ];
  for (const [x, y, mat] of chairPositions) {
    const chair = new THREE.Group();
    chair.position.set(x, y, 0);
    chair.add(cylinder('nursery-chair-seat', 0.48, 0.48, 0.12, [0, 0, 0.48], mat, 24));
    chair.add(box('nursery-chair-back', [0.78, 0.12, 0.70], [0, y > 1.2 ? 0.32 : -0.32, 0.82], mat));
    for (const lx of [-0.30, 0.30]) chair.add(cylinder('nursery-chair-leg', 0.035, 0.035, 0.42, [lx, 0, 0.22], materials.darkOak, 12));
    parent.add(chair);
  }

  // Front right changing/table unit and shelf
  const unit = new THREE.Group();
  unit.position.set(8.55, -2.7, 0);
  unit.add(box('changing-unit', [2.65, 1.12, 1.65], [0, 0, 0.84], materials.paleOak));
  unit.add(box('changing-pad', [2.38, 1.02, 0.12], [0, -0.02, 1.68], materials.warmWhite));
  for (const x of [-0.85, 0, 0.85]) {
    unit.add(box('changing-door', [0.75, 0.08, 1.36], [x, -0.58, 0.82], materials.cream));
  }
  parent.add(unit);
  parent.add(makeWallSign('PLAY', '', [8.6, -3.25, 1.5], 1.15));

  // Right wall low shelves
  const rightShelf = new THREE.Group();
  rightShelf.position.set(8.75, -0.8, 0);
  rightShelf.add(box('nursery-book-shelf', [1.15, 2.4, 1.65], [0, 0, 0.84], materials.paleOak));
  for (const z of [0.45, 0.95, 1.45]) rightShelf.add(box('nursery-shelf-board', [1.20, 2.44, 0.07], [0, 0, z], materials.darkOak));
  for (let i = 0; i < 3; i++) {
    rightShelf.add(box('nursery-book', [0.18, 1.4, 0.70], [-0.35 + i * 0.32, -0.28, 0.72], [materials.blush, materials.blue, materials.yellow][i]));
  }
  parent.add(rightShelf);
}

function addFacade(parent) {
  // Double entrance doors
  parent.add(box('door-frame-left', [0.16, 0.22, 3.25], [-1.55, -6.78, 1.65], materials.darkOak));
  parent.add(box('door-frame-right', [0.16, 0.22, 3.25], [1.55, -6.78, 1.65], materials.darkOak));
  parent.add(box('door-header', [3.25, 0.18, 0.16], [0, -6.78, 3.18], materials.darkOak));
  for (const x of [-0.78, 0.78]) {
    parent.add(box('glass-door', [1.42, 0.05, 2.82], [x, -6.82, 1.58], materials.glass));
  }
  for (const x of [-0.78, 0.78]) {
    parent.add(cylinder('door-handle', 0.035, 0.035, 1.0, [x, -6.72, 1.35], materials.brass, 16));
  }
  parent.add(box('entrance-mat', [3.25, 1.1, 0.025], [0, -6.18, 0.17], materials.dark));
  addPlant(parent, -8.75, -6.45, 0.2, 1.05);
  addPlant(parent, 8.75, -6.45, 0.2, 1.05);
}

const interior = new THREE.Group();
interior.name = 'Detailed_First_Floor_Interior';
scene.add(interior);

// The GLTF supplies the preserved 20x14 architectural shell.
const baseLoader = new GLTFLoader();
baseLoader.load(
  './models/first_floor.glb',
  (gltf) => {
    loading.textContent = 'Preparing the interior…';
    const model = gltf.scene;
    model.name = 'Preserved_Base_Shell';
    // Blender's source is Z-up while glTF is Y-up; align the shell with this scene's Z-up furniture.
    model.rotation.x = Math.PI / 2;
    model.traverse((object) => {
      if (!object.isMesh) return;
      object.castShadow = true;
      object.receiveShadow = true;
      const name = object.name.toLowerCase();
      const keepStructure =
        name.includes('floor') ||
        name.includes('wall') ||
        name.includes('partition') ||
        name.includes('divider') ||
        name.includes('entrance') ||
        name.includes('door') ||
        name.includes('header') ||
        name.includes('glass');
      if (!keepStructure) object.visible = false;
    });
    scene.add(model);

    addStore(interior);
    addReception(interior);
    addWaiting(interior);
    addNursery(interior);
    addFacade(interior);

    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    controls.target.copy(center);
    controls.update();
    renderRequested = true;
    loading.classList.add('hidden');
  },
  (event) => {
    if (event.total) loading.textContent = `Loading 3D interior… ${Math.round(event.loaded / event.total * 100)}%`;
  },
  (error) => {
    console.error(error);
    loading.textContent = 'Unable to load models/first_floor.glb. Check that the project is served from this folder.';
    loading.classList.add('error');
  }
);

const viewPresets = {
  overview: { position: overviewPosition, target: overviewTarget },
  store: { position: new THREE.Vector3(-12, -9, 21), target: new THREE.Vector3(-4.5, 1.5, 1.1) },
  nursery: { position: new THREE.Vector3(13, -8, 21), target: new THREE.Vector3(5.2, 2.0, 1.1) },
};

let cameraTween = null;
function setView(name) {
  const preset = name === 'reset' ? viewPresets.overview : viewPresets[name];
  if (!preset) return;
  cameraTween = {
    fromPosition: camera.position.clone(),
    fromTarget: controls.target.clone(),
    toPosition: preset.position.clone(),
    toTarget: preset.target.clone(),
    elapsed: 0,
    duration: 0.75
  };
  document.querySelectorAll('.view-button').forEach((button) => {
    button.classList.toggle('active', button.dataset.view === name || (name === 'reset' && button.dataset.view === 'overview'));
  });
}

document.querySelectorAll('.view-button').forEach((button) => {
  button.addEventListener('click', () => setView(button.dataset.view));
});

let renderRequested = true;
controls.addEventListener('change', () => { renderRequested = true; });
window.addEventListener('error', (event) => {
  if (!event.target || !(event.target instanceof HTMLScriptElement)) {
    loading.textContent = `3D viewer error: ${event.message || 'see browser console'}`;
    loading.classList.add('error');
  }
});
window.addEventListener('unhandledrejection', (event) => {
  console.error(event.reason);
  loading.textContent = `3D viewer error: ${event.reason?.message || 'see browser console'}`;
  loading.classList.add('error');
});

function animate() {
  requestAnimationFrame(animate);
  let tweenActive = false;
  if (cameraTween) {
    cameraTween.elapsed += Math.min(0.05, 1 / 60);
    const t = Math.min(cameraTween.elapsed / cameraTween.duration, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    camera.position.lerpVectors(cameraTween.fromPosition, cameraTween.toPosition, ease);
    controls.target.lerpVectors(cameraTween.fromTarget, cameraTween.toTarget, ease);
    if (t >= 1) cameraTween = null;
    else tweenActive = true;
  }
  controls.update();
  if (renderRequested || tweenActive) {
    renderer.render(scene, camera);
    renderRequested = false;
  }
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});
