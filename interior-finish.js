import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { architecturalLight } from './architectural-light.js';

const W=256,H=224;
const mapURLs={
  first:new URL('./walkmaps/01.bin',import.meta.url),
  second:new URL('./walkmaps/02.bin',import.meta.url),
  third:new URL('./walkmaps/03.bin',import.meta.url)
};
const grids={};
export function walkMap(level){
  return grids[level]??=fetch(mapURLs[level]).then(async r=>{
    if(!r.ok)throw Error('Floor navigation map unavailable');
    const data=new Uint8Array(await r.arrayBuffer());
    if(data.length!==W*H)throw Error('Invalid floor navigation map');
    return data;
  }).catch(e=>{delete grids[level];throw e;});
}
function contactTexture(data){
  // Integral image: two scales of indirect contact shading under built geometry.
  const sum=new Uint32Array((W+1)*(H+1)),out=new Uint8Array(W*H);
  for(let z=0;z<H;z++)for(let x=0,acc=0;x<W;x++){
    acc+=data[z*W+x];sum[(z+1)*(W+1)+x+1]=sum[z*(W+1)+x+1]+acc;
  }
  function mean(x,z,r){
    const a=Math.max(0,x-r),b=Math.min(W,x+r+1),c=Math.max(0,z-r),d=Math.min(H,z+r+1),s=W+1;
    return (sum[d*s+b]-sum[c*s+b]-sum[d*s+a]+sum[c*s+a])/((b-a)*(d-c));
  }
  for(let z=0;z<H;z++)for(let x=0;x<W;x++)out[z*W+x]=255-.32*mean(x,z,2)-.17*mean(x,z,7);
  const t=new THREE.DataTexture(out,W,H,THREE.RedFormat);
  t.magFilter=t.minFilter=THREE.LinearFilter;t.needsUpdate=true;return t;
}
export function interiorFinish(renderer,scene){
  const pmrem=new THREE.PMREMGenerator(renderer),studio=new RoomEnvironment();
  const reflection=pmrem.fromScene(studio,.045);
  scene.environment=reflection.texture;scene.environmentIntensity=.55;
  pmrem.dispose();studio.dispose();
  const ceiling=new THREE.Group(),lighting=architecturalLight(renderer,scene);
  const plaster=new THREE.MeshStandardMaterial({color:0xf7eee3,roughness:.95});
  function cuboid(x,y,z,w,h,d,m){
    const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);ceiling.add(o);return o;
  }
  cuboid(0,.07,0,16.36,.12,14.28,plaster).castShadow=true;
  // The cutaway opens onto a planted forecourt at ground level. From upstairs,
  // the same trees and paving are seen at the correct height through the glazing.
  const garden=new THREE.Group();
  function landscape(geo,material,instances){
    const o=new THREE.InstancedMesh(geo,material,instances.length),tmp=new THREE.Object3D();
    instances.forEach(([x,y,z,w,h,d,angle=0,color],i)=>{
      tmp.position.set(x,y,z);tmp.scale.set(w,h,d);tmp.rotation.y=angle;
      tmp.updateMatrix();o.setMatrixAt(i,tmp.matrix);if(color)o.setColorAt(i,new THREE.Color(color));
    });
    o.castShadow=o.receiveShadow=true;garden.add(o);
  }
  const terrain=new THREE.MeshStandardMaterial({roughness:.93});
  landscape(new THREE.BoxGeometry(),terrain,[
    [0,-.44,0,110,.15,110,0,'#aab19a'],[0,-.28,11,26,.12,7,0,'#c5bcb0'],
    ...[-1,1].flatMap(s=>[[s*6,-.15,11.3,6.1,.33,2.3,0,'#c4b6a7'],[s*6,.035,11.3,5.9,.1,2.1,0,'#695e4c']])
  ]);
  const stems=[],crowns=[];
  let seed=234;const rand=()=>((seed=1664525*seed+1013904223>>>0)/4294967296);
  for(const [x,z] of [[-7.5,11],[7,11],[-12,6],[13,4],[-12,-5],[14,-7],[-6,19],[4,22],[13,19]]){
    const h=2.9+rand()*1.4;stems.push([x,h*.48,z,.14,h,.14,0,'#74644c']);
    for(let k=0;k<19;k++){
      const a=rand()*Math.PI*2,r=rand()*1.16;
      crowns.push([x+r*Math.cos(a),h+.68-r*.4+rand()*.9,z+r*Math.sin(a),.62+rand()*.5,.63+rand()*.52,.68+rand()*.47,a,
        ['#76835d','#63764d','#899267','#596b48'][k%4]]);
    }
  }
  landscape(new THREE.CylinderGeometry(.7,1,1,10),terrain,stems);
  landscape(new THREE.IcosahedronGeometry(1,2),terrain,crowns);
  const sky=new THREE.Mesh(new THREE.SphereGeometry(85,32,12),new THREE.ShaderMaterial({
    side:THREE.BackSide,depthWrite:false,vertexShader:`varying vec3 ray; void main(){ray=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader:`varying vec3 ray;void main(){float h=smoothstep(-.04,.65,normalize(ray).y);gl_FragColor=vec4(mix(vec3(.83,.81,.74),vec3(.32,.56,.78),h),1.);
    #include <colorspace_fragment>
    }`
  }));
  garden.add(sky);
  const lids=new THREE.Group();
  const galleryCeiling=new THREE.Mesh(new THREE.BoxGeometry(3.90,.07,4.55),plaster);
  galleryCeiling.position.set(0,2.983,-4.69);lids.add(galleryCeiling);
  // The room ceilings and recessed fixtures are present at eye level and lifted away in plan view.
  for(const side of [-1,1])for(const outer of [false,true]){
    const x=side*(outer?6.875:3.045),w=outer?2.25:2.19;
    const cap=new THREE.Mesh(new THREE.BoxGeometry(w,.07,9.25),plaster);cap.position.set(x,2.956,-2.375);lids.add(cap);
  }
  const reading=new THREE.PointLight(0xffdbab,1.8,2.1,2);
  // Repeated luminaires share a draw call, even when several wings are in frame.
  function instanceFixtures(parent){
    const buckets=new Map();
    for(const o of parent.children){
      if(!o.isMesh)continue;
      const key=o.material.uuid+JSON.stringify(o.geometry.parameters);
      if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(o);
    }
    for(const list of buckets.values()){
      if(list.length<2)continue;
      const first=list[0],batch=new THREE.InstancedMesh(first.geometry,first.material,list.length);
      list.forEach((o,i)=>{o.updateMatrix();batch.setMatrixAt(i,o.matrix);parent.remove(o);if(i)o.geometry.dispose();});
      batch.computeBoundingSphere();parent.add(batch);
    }
  }
  instanceFixtures(lids);instanceFixtures(ceiling);
  scene.add(lids,reading);lids.visible=reading.visible=false;
  scene.add(ceiling,garden);ceiling.visible=garden.visible=false;
  const treated=new WeakSet();
  return {
    prepare:lighting.prepare,stack:lighting.stack,reflectionChanged:lighting.invalidate,
    suite(pos){reading.intensity=pos?1.8:0;if(pos)reading.position.set(pos.x,1.17,pos.z);},
    walking(level){
      lids.visible=reading.visible=level==='third';reading.intensity=0;
      lighting.walking(level);
      ceiling.visible=garden.visible=!!level;ceiling.position.y=level==='third'?4.46:3.74;
      garden.position.y=level==='third'?-7.92:level==='second'?-3.96:0;
      renderer.toneMappingExposure=level ? .86 : .96;
      renderer.shadowMap.needsUpdate=true;
    },
    apply(model,map,key,atlas){
      const contact=contactTexture(map);
      model.traverse(o=>{
        if(!o.isMesh)return;
        const m=o.material;if(treated.has(m))return;treated.add(m);
        if(!/sandstone|sand tile|travertine|oat carpet/i.test(m.name))return;
        m.customProgramCacheKey=()=>'atrium-contact';
        m.onBeforeCompile=shader=>{
          shader.uniforms.contactMap={value:contact};
          shader.vertexShader='varying vec3 finishP;\n'+shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nfinishP=(modelMatrix*vec4(transformed,1.)).xyz;');
          shader.fragmentShader='varying vec3 finishP;\nuniform sampler2D contactMap;\n'+shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
          vec2 footprint=clamp((finishP.xz+vec2(8.,7.))/vec2(16.,14.),0.,1.);
          diffuseColor.rgb*=texture2D(contactMap,footprint).r;`);
        };
      });
      lighting.apply(model,key,atlas);
    }
  };
}
