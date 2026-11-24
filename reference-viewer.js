import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { interiorFinish, walkMap } from './interior-finish.js';
import { lightVolume } from './architectural-light.js';
import { walkTour,walkFov } from './walk-tour.js';
import { installFullscreen } from './fullscreen.js';
import { surfaceLibrary } from './surface-library.js';
import { responsiveControls } from './responsive-controls.js';

const host = document.querySelector('#viewer');
const status = document.querySelector('#loading');
installFullscreen(document.querySelector('.app'),document.querySelector('#fullscreen'),document.querySelector('#screen-hint'));
const updateControls=responsiveControls();
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference:'high-performance' });
const gl=renderer.getContext();
const viewportLimits=gl.getParameter(gl.MAX_VIEWPORT_DIMS);
const bufferLimit=gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
const textureDetail=Math.min(16,renderer.capabilities.getMaxAnisotropy()||1);
renderer.shadowMap.enabled = true;
renderer.shadowMap.autoUpdate = false;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
host.append(renderer.domElement);
renderer.domElement.tabIndex = 0;
renderer.domElement.setAttribute('aria-label','Building interior viewport');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xc6c0bc);
const camera = new THREE.PerspectiveCamera(39, 1, .1, 160);
const controls = new OrbitControls(camera, renderer.domElement);
controls.maxPolarAngle = Math.PI * .48;
controls.minDistance = 3;
controls.maxDistance = 90;
scene.add(new THREE.HemisphereLight(0xfff6eb, 0xb4a08e, .89));
const finish = interiorFinish(renderer,scene);
const surfaces=surfaceLibrary(renderer);
const sun = new THREE.DirectionalLight(0xfff0dc, 2.25);
sun.position.set(-7, 17, 7);
sun.castShadow = true;
Object.assign(sun.shadow.camera, { left: -13, right: 13, top: 13, bottom: -13, far: 45 });
sun.shadow.camera.updateProjectionMatrix();
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.normalBias = .010;
scene.add(sun);
const measure=new URLSearchParams(location.search).has('stats');
function render(motion=false) {
  surfaces.updatePile(camera);
  const reflected=finish.prepare(camera,motion===true);
  renderer.render(scene, camera);
  if(measure)window.atriumStats={calls:renderer.info.render.calls,triangles:renderer.info.render.triangles,pixelRatio:renderer.getPixelRatio(),position:camera.position.toArray(),locker:walk.lockerState,motion:motion===true,reflectionPass:!!reflected};
}
controls.addEventListener('change', render);
let preset = 'overview';
const floorSelect = document.querySelector('#floor');
const walk = walkTour({camera,canvas:renderer.domElement,controls,render,finish,
  onExit:leaveWalk,onFloor:key=>{floorSelect.value=key;selectFloor(true);}
});
let beforeWalk='building';
const suiteSelect=document.querySelector('#suite');
const suiteIDs=['G','B'].flatMap(prefix=>Array.from({length:10},(_,i)=>prefix+String(i+1).padStart(2,'0')));
for(const id of suiteIDs)suiteSelect.add(new Option(`Bedroom ${id}`,id));
suiteSelect.onchange=()=>{
  const id=suiteSelect.value;suiteSelect.value='';
  if(!suiteIDs.includes(id))return;
  if(!walk.active){beforeWalk=floorSelect.value;walk.begin();}
  floorSelect.value='third';selectFloor(false,id);
};
function leaveWalk(){
  walk.end();floorSelect.value=beforeWalk;selectFloor();
}
document.querySelector('#walk').onclick=()=>{
  if(walk.active){leaveWalk();return;}
  beforeWalk=floorSelect.value;
  if(beforeWalk==='building')floorSelect.value='first';
  walk.begin();selectFloor();
};
const targets = {store:[-3.6,-.8],nursery:[4.6,-.8],print:[-5.1,-5.2],study:[-.65,-.7],dining:[5.4,0]};
function view(key) {
  preset = key === 'reset' ? 'overview' : key;
  const overview = preset === 'overview';
  const both = floorSelect.value === 'building';
  const [x,z] = targets[preset] || [0,.48];
  controls.target.set(x, both ? 5.7 : .95, z);
  const direction = new THREE.Vector3(both ? -.46 : overview ? 0 : -Math.sign(x)*.17, both ? .36 : .81, 1).normalize();
  // Fit the floor width and its foreshortened depth even on portrait displays.
  const dist = Math.max(overview ? 24 : 16, (overview ? 9.2 : 5.2) / (Math.tan(camera.fov * Math.PI / 360) * camera.aspect) + 5.6);
  controls.maxDistance=Math.max(90,dist*1.55);
  camera.position.copy(controls.target).addScaledVector(direction, dist*(both ? 1.4 : 1));
  if (floorSelect.value === 'third') {
    if (preset === 'plan') {
      controls.target.set(0,.7,0);
      camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(0,1,.27).normalize(),dist+6);
    } else {
      controls.target.set(0,2.08,1);
      const distance = Math.max(14, 8.5/(Math.tan(camera.fov*Math.PI/360)*camera.aspect)+2.1);
      camera.position.set(0,2.08+distance*.07,1+distance);
    }
  }
  if (preset === 'lift') {
    controls.target.set(5.98,1.42,5.98);
    const distance = Math.max(5.8, 3.1 / camera.aspect);
    camera.position.copy(controls.target).addScaledVector(new THREE.Vector3(-1,.48,.50).normalize(),distance);
  }
  controls.update();
  document.querySelectorAll('[data-view]').forEach(el => el.classList.toggle('active', el.dataset.view === preset));
  render();
}
document.querySelectorAll('[data-view]').forEach(el => el.onclick = () => view(el.dataset.view));
function resize() {
  const ratio=Math.min(devicePixelRatio||1,Math.min(bufferLimit,viewportLimits[0])/host.clientWidth,Math.min(bufferLimit,viewportLimits[1])/host.clientHeight);
  renderer.setDrawingBufferSize(host.clientWidth, host.clientHeight,ratio);
  camera.aspect = host.clientWidth / host.clientHeight;
  if(walk.active)camera.fov=walkFov(camera.aspect);
  camera.updateProjectionMatrix();
  if(walk.active)render();else view(preset);
}
resize();
let resizeFrame=0;
new ResizeObserver(()=>{if(!resizeFrame)resizeFrame=requestAnimationFrame(()=>{resizeFrame=0;resize();});}).observe(host);
function watchDisplay(){
  matchMedia(`(resolution: ${devicePixelRatio}dppx)`).addEventListener('change',()=>{resize();watchDisplay();},{once:true});
}
watchDisplay();
const urls = {
  first:new URL('./models/Atrium/MaterialStudy/Level_01.glb', import.meta.url).href,
  second:new URL('./models/Atrium/MaterialStudy/Level_02.glb', import.meta.url).href,
  third:new URL('./models/Atrium/Gallery/Level_03.glb', import.meta.url).href,
};
const requests = {}, loaded = {};
const warmWalk=new Set();
function loadFloor(key) {
  return requests[key] ??= Promise.all([new GLTFLoader().loadAsync(urls[key]),walkMap(key),lightVolume(key)]).then(async ([{scene:model},map,atlas]) => {
    finish.apply(model,map,key,atlas);
    await surfaces.apply(model,key);
    model.traverse(o => {
      if(o!==model){o.updateMatrix();o.matrixAutoUpdate=false;}
      if (!o.isMesh) return;
      for(const slot of ['map','emissiveMap','normalMap','roughnessMap','bumpMap']){
        const tex=o.material[slot];
        if(tex&&tex.anisotropy!==textureDetail){tex.anisotropy=textureDetail;tex.needsUpdate=true;}
      }
      o.castShadow = !o.material.transparent;
      o.receiveShadow = true;
    });
    model.visible = false;
    scene.add(model);
    loaded[key] = model;
  }).catch(err => {delete requests[key];throw err;});
}
let switchID=0;
async function selectFloor(landing=false,suite=null) {
  const ticket=++switchID;
  const key = floorSelect.value, both = key === 'building';
  suiteSelect.hidden=key!=='third';
  if(both && walk.active)walk.end();
  updateControls(walk.active,key);
  if(walk.active)walk.pause();
  const views = {first:['store','nursery','lift'],second:['print','study','dining','lift'],third:['plan','lift'],building:[]}[key];
  document.querySelector('#visit-gallery').hidden=key!=='third';
  document.querySelector('[data-view="overview"]').textContent = key === 'third' ? 'Lobby' : 'Overview';
  document.querySelectorAll('[data-view]').forEach(el => {
    el.hidden = !['overview','reset',...views].includes(el.dataset.view);
  });
  document.querySelector('h1').textContent = {first:'Baby Store & Nursery',second:'Print, Study & Dining',third:'Student Support Center',building:'Atrium Building'}[key];
  document.querySelector('.eyebrow').textContent = both ? 'THREE-FLOOR INTERIOR' : `${key.toUpperCase()} FLOOR INTERIOR`;
  Object.values(loaded).forEach(o => o.visible=false);
  if(!walk.active)view(preset === 'lift' && !both ? 'lift' : 'overview');
  status.classList.remove('hidden','error');
  status.textContent = 'Loading 3D interior…';
  try {
    await Promise.all((both ? Object.keys(urls) : [key]).map(loadFloor));
    if (ticket!==switchID) return;
    for (const [level,model] of Object.entries(loaded)) {
      model.position.y = both ? {first:0,second:3.96,third:7.92}[level] : 0;
      model.visible = both || level === key;
    }
    finish.stack(both);
    renderer.shadowMap.needsUpdate=true;
    if(walk.active){
      loaded[key].updateMatrixWorld(true);
      if(!warmWalk.has(key)){
        finish.walking(key);
        status.textContent='Preparing interior lighting…';
        await renderer.compileAsync(loaded[key],camera,scene);
        if(ticket!==switchID)return;
        warmWalk.add(key);
      }
      walk.arrive(key,loaded[key],await walkMap(key),landing,suite);
    }
    status.classList.add('hidden');if(!walk.active)render();
  } catch(err) {
    if (ticket!==switchID) return;
    console.error(err);status.textContent='Could not load the selected model.';status.classList.add('error');
  }
}
floorSelect.onchange = ()=>selectFloor(walk.active);
const requestedSuite=new URLSearchParams(location.search).get('room')?.toUpperCase();
const requestedGallery=new URLSearchParams(location.search).get('visit')==='lockers';
document.querySelector('#visit-gallery').onclick=()=>{
  if(!walk.active){beforeWalk=floorSelect.value;walk.begin();}
  floorSelect.value='third';selectFloor(false,'gallery');
};
if(requestedGallery||suiteIDs.includes(requestedSuite)){
  floorSelect.value='third';walk.begin();
}else if(new URLSearchParams(location.search).get('tour')==='1'){
  floorSelect.value='first';walk.begin();
}else if(matchMedia('(max-width:760px)').matches||navigator.connection?.saveData){
  floorSelect.value='first';
}
selectFloor(false,requestedGallery?'gallery':suiteIDs.includes(requestedSuite)?requestedSuite:null);
