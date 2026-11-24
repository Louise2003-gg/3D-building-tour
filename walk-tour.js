import * as THREE from 'three';
import {suiteVisibility} from './suite-visibility.js';
import {lockersFor} from './locker-controls.js';

// Retract the two pairs of glazed leaves at the staffed third-floor gates.
function gateLeaves(model){
  const group=model.getObjectByName('Two_glazed_access_lanes') || model.getObjectByName('Two glazed access lanes');
  const leaves=[];
  group?.traverse(o=>{
    if(!o.isMesh)return;
    const p=o.geometry.attributes.position,world=new THREE.Vector3(),inverse=o.matrixWorld.clone().invert();
    const delta=new THREE.Vector3(1,0,0).applyMatrix4(inverse).sub(new THREE.Vector3().applyMatrix4(inverse));
    for(let i=0;i<p.count;i++){
      world.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);
      if(Math.abs(world.z-4.53)>.026 || world.y<.3 || world.y>1.14)continue;
      const lane=world.x<.49?0:1,left=[-1.36,.49][lane],anchor=world.x<left+.925?left+.15:left+1.70;
      leaves.push([p,i,p.getX(i),p.getY(i),p.getZ(i),delta.clone().multiplyScalar(anchor-world.x)]);
    }
  });
  const touched=new Set(leaves.map(a=>a[0]));
  return openness=>{for(const [p,i,x,y,z,d] of leaves)p.setXYZ(i,x+d.x*openness,y+d.y*openness,z+d.z*openness);for(const p of touched)p.needsUpdate=true;};
}
export function walkTour({camera,canvas,controls,render,finish,onExit,onFloor}){
  const walkButton=document.querySelector('#walk'),hud=document.querySelector('#tour'),lift=document.querySelector('#lift-call'),panel=document.querySelector('#lift-panel');
  let active=false,ready=false,current='',grid=null,yaw=0,pitch=0,phase=0,last=0,raf=0,pointer=null,previous,gate=null,openness=0;
  const held=new Set(),facing=new THREE.Euler(0,0,0,'YXZ'),reduce=matchMedia('(prefers-reduced-motion: reduce)');
  const gates=new WeakMap(), names={first:'01 · Store & nursery',second:'02 · Print, study & dining',third:'03 · Student support'};
  let cull=null,lookDirty=false,roomStamp=null,needsStill=false;
  const masks=new WeakMap();
  const lockerButton=document.querySelector('#locker-action'),dir=new THREE.Vector3(),ray=new THREE.Raycaster();
  let lockers=null,aimed=0,down=null,tapTravel=0;
  function refreshLocker(){
    aimed=lockers?.aimed(camera,camera.getWorldDirection(dir))||0;
    lockerButton.hidden=!aimed;
    if(aimed)lockerButton.textContent=lockers.label(aimed);
  }
  function activateLocker(id){if(!ready||!lockers||!id)return;lockers.toggle(id);refreshLocker();wake();}
  lockerButton.onclick=()=>activateLocker(aimed);
  function wake(){
    if(active&&ready&&!raf&&!document.hidden){last=performance.now();raf=requestAnimationFrame(tick);}
  }
  function orient(){camera.quaternion.setFromEuler(facing.set(pitch,yaw,0));}
  function canStand(x,z){
    const r=.19;
    if(lockers?.blocks(x,z))return false;
    if(x-r< -7.96||x+r>7.96||z-r< -6.97||z+r>6.97)return false;
    for(let j=Math.floor((z+7-r)*16);j<=Math.floor((z+7+r)*16);j++)
      for(let i=Math.floor((x+8-r)*16);i<=Math.floor((x+8+r)*16);i++){
        if(!grid[j*256+i])continue;
        const dx=x-THREE.MathUtils.clamp(x,i/16-8,(i+1)/16-8),dz=z-THREE.MathUtils.clamp(z,j/16-7,(j+1)/16-7);
        if(dx*dx+dz*dz<r*r)return false;
      }
    return true;
  }
  function nearLift(){return ready&&Math.abs(camera.position.z-6)<1.25&&camera.position.x>4.24&&camera.position.x<5.94;}
  function showPanel(){
    if(!nearLift())return;
    held.clear();panel.hidden=!panel.hidden;wake();
    if(!panel.hidden)panel.querySelector('button:not(:disabled)').focus();
  }
  lift.onclick=showPanel;
  document.querySelector('#lift-close').onclick=()=>{panel.hidden=true;canvas.focus();wake();};
  for(const b of panel.querySelectorAll('[data-stop]'))b.onclick=()=>{panel.hidden=true;onFloor(b.dataset.stop);};
  function tick(now){
    raf=0;if(!active||document.hidden)return;
    const elapsed=now-last,dt=Math.min(.16,elapsed/1000);last=now;
    if(ready && panel.hidden){
      const forward=Number(held.has('KeyW')||held.has('ArrowUp'))-Number(held.has('KeyS')||held.has('ArrowDown'));
      const side=Number(held.has('KeyD'))-Number(held.has('KeyA'));
      const turn=Number(held.has('ArrowLeft'))-Number(held.has('ArrowRight'));
      const tilt=Number(held.has('KeyI'))-Number(held.has('KeyK'));
      const st=2.05*dt/(Math.hypot(forward,side)||1);
      yaw+=turn*dt*1.55;
      pitch=THREE.MathUtils.clamp(pitch+tilt*dt*1.2,-1.25,1.25);
      const dx=(side*Math.cos(yaw)-forward*Math.sin(yaw))*st,dz=(-forward*Math.cos(yaw)-side*Math.sin(yaw))*st;
      const pos=camera.position,oldX=pos.x,oldZ=pos.z;
      if(dx||dz){
        const steps=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.065));
        for(let s=0;s<steps;s++){
          if(dx&&canStand(pos.x+dx/steps,pos.z))pos.x+=dx/steps;
          if(dz&&canStand(pos.x,pos.z+dz/steps))pos.z+=dz/steps;
        }
      }
      const dist=Math.hypot(pos.x-oldX,pos.z-oldZ);phase+=dist*7.7;
      const height=1.62+(dist&&!reduce.matches?Math.sin(phase)*.006:0);
      let dirty=!!(dist||turn||tilt||lookDirty||Math.abs(pos.y-height)>.001);
      const wasLooking=lookDirty;lookDirty=false;
      pos.y=height;orient();
      let animating=false;
      if(gate){
        const target=(Math.abs(pos.z-4.53)<1.25&&pos.x>-1.6&&pos.x<2.6)?1:0;
        const next=THREE.MathUtils.clamp(target,openness-dt*3.8,openness+dt*3.8);
        if(next!==openness){openness=next;gate(next);dirty=true;animating=next!==target;}
      }
      const swinging=lockers?.advance(dt,pos.x,pos.z);
      if(swinging){dirty=true;animating=true;finish.reflectionChanged();}
      const hideLift=!nearLift();
      if(lift.hidden!==hideLift)lift.hidden=hideLift;
      const moving=!!(dist||turn||tilt||wasLooking||swinging||pointer!==null);
      if(dirty||(needsStill&&!moving)){
        cull?.(pos);
        if(current==='third'){identifyRoom();refreshLocker();}
        render(moving);needsStill=moving;
      }
      if(held.size||animating||dist||pointer!==null)raf=requestAnimationFrame(tick);
    }
  }
  function clear(){held.clear();pointer=null;}
  window.addEventListener('blur',clear);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clear();});
  const movement=['KeyW','KeyA','KeyS','KeyD','KeyI','KeyK','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'];
  window.addEventListener('keydown',e=>{
    if(!active||e.altKey||e.ctrlKey||e.metaKey)return;
    if(!panel.hidden&&e.code==='Tab'){
      const buttons=Array.from(panel.querySelectorAll('button:not(:disabled)'));
      if(document.activeElement===buttons[e.shiftKey?0:buttons.length-1]){
        e.preventDefault();buttons[e.shiftKey?buttons.length-1:0].focus();
      }
      return;
    }
    if(e.code==='Escape'){
      if(document.fullscreenElement||document.webkitFullscreenElement)return;
      if(!panel.hidden){panel.hidden=true;canvas.focus();}else onExit();return;
    }
    if(e.target.tagName==='SELECT'||document.querySelector('#view-options')?.classList.contains('expanded'))return;
    if(e.code==='KeyE'&&!e.repeat){if(aimed)activateLocker(aimed);else showPanel();return;}
    if(e.target.closest?.('button')&&['ArrowLeft','ArrowRight','ArrowDown','ArrowUp'].includes(e.code))return;
    if(panel.hidden&&movement.includes(e.code)){e.preventDefault();held.add(e.code);wake();}
  });
  window.addEventListener('keyup',e=>held.delete(e.code));
  canvas.addEventListener('pointerdown',e=>{
    if(!ready||!panel.hidden||pointer!==null)return;
    canvas.focus();pointer=e.pointerId;canvas.setPointerCapture(pointer);previous=[e.clientX,e.clientY];down=previous;tapTravel=0;
  });
  canvas.addEventListener('pointermove',e=>{
    if(!ready||pointer!==e.pointerId)return;
    tapTravel+=Math.hypot(e.clientX-previous[0],e.clientY-previous[1]);
    yaw-=(e.clientX-previous[0])*.004;pitch=THREE.MathUtils.clamp(pitch-(e.clientY-previous[1])*.004,-1.25,1.25);
    previous=[e.clientX,e.clientY];lookDirty=true;wake();
  });
  canvas.addEventListener('lostpointercapture',()=>pointer=null);
  canvas.addEventListener('pointerup',e=>{
    if(!lockers||e.pointerId!==pointer||!down||tapTravel>6)return;
    const box=canvas.getBoundingClientRect();
    ray.setFromCamera({x:2*(e.clientX-box.left)/box.width-1,y:1-2*(e.clientY-box.top)/box.height},camera);
    activateLocker(lockers.aimed(camera,ray.ray.direction));down=null;
  });
  for(const b of document.querySelectorAll('[data-step]')){
    b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);held.add(b.dataset.step);wake();};
    b.onlostpointercapture=()=>held.delete(b.dataset.step);
  }
  function identifyRoom(){
    const {x,z}=camera.position,ax=Math.abs(x),j=Math.floor((2.25-z)/1.85);
    const inside=j>=0&&j<5&&((ax>1.95&&ax<4.14)||(ax>5.75&&ax<8));
    const gallery=ax<1.92&&z< -2.30;
    const id=inside?(x<0?'G':'B')+String(j+1+(ax>5.75?5:0)).padStart(2,'0'):gallery?'gallery':'';
    if(roomStamp===id)return;roomStamp=id;
    const where=document.querySelector('#tour-location'),name=gallery?'03 · Locker gallery':names.third+(id?` · Bedroom ${id}`:'');
    if(where.textContent!==name)where.textContent=name;
    finish.suite(inside?{x:Math.sign(x)*(ax>5.75?7.73:2.22),z:2.25-(j+.5)*1.85+.10}:null);
  }
  return {
    get active(){return active;},
    get lockerState(){return lockers?.state()||null;},
    begin(){
      active=true;ready=false;controls.enabled=false;document.body.classList.add('walking');
      walkButton.textContent='Exit walk';walkButton.setAttribute('aria-pressed','true');hud.hidden=false;
      camera.fov=walkFov(camera.aspect);camera.near=.045;camera.updateProjectionMatrix();
    },
    pause(){ready=false;clear();lockers?.reset();lockers=null;aimed=0;lockerButton.hidden=true;gate?.(0);gate=null;cull?.(null);cull=null;panel.hidden=true;lift.hidden=true;},
    arrive(level,model,map,landing,suite){
      current=level;grid=map;ready=true;phase=0;openness=0;roomStamp=null;needsStill=false;
      if(current==='third'){
        lockers=lockersFor(model);
        if(!gates.has(model))gates.set(model,gateLeaves(model));
        gate=gates.get(model);
        if(!masks.has(model))masks.set(model,suiteVisibility(model));cull=masks.get(model);
      }
      const entry=current==='first'&&!landing;
      camera.position.set(entry?0:4.86,1.62,entry?6.18:6.03);
      yaw=entry?.49:.54;pitch=entry?-.085:-.025;
      if(current==='third'&&suite==='gallery'){
        camera.position.set(.10,1.62,-3.04);yaw=.98;pitch=-.085;
      }else if(current==='third'&&suite){
        const n=Number(suite.slice(1))-1,outer=n>=5,side=suite[0]==='G'?-1:1;
        camera.position.set(side*(outer?8-1.76:1.95+1.76),1.62,2.25-(n%5+.5)*1.85+.51);
        yaw=Math.atan2(side*(outer?-1:1),.54);pitch=-.38;
      }
      orient();finish.walking(level);
      document.querySelector('#tour-location').textContent=names[level];
      if(current==='third'){identifyRoom();refreshLocker();}
      panel.querySelectorAll('[data-stop]').forEach(b=>b.disabled=b.dataset.stop===level);
      cull?.(camera.position);lift.hidden=!nearLift();canvas.focus({preventScroll:true});render();wake();
    },
    end(){
      lockers?.reset();lockers=null;aimed=0;lockerButton.hidden=true;
      active=false;ready=false;cancelAnimationFrame(raf);raf=0;clear();gate?.(0);gate=null;cull?.(null);cull=null;
      document.body.classList.remove('walking');hud.hidden=panel.hidden=true;
      walkButton.textContent='Walk inside';walkButton.setAttribute('aria-pressed','false');
      finish.walking(null);camera.fov=39;camera.near=.1;camera.updateProjectionMatrix();controls.enabled=true;
    }
  };
}
export function walkFov(aspect){
  return Math.max(62,Math.min(88,THREE.MathUtils.radToDeg(2*Math.atan(Math.tan(THREE.MathUtils.degToRad(24))/aspect))));
}
