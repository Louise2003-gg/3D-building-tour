import * as THREE from 'three';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import catalog from './finish-library.json';

const paths=import.meta.glob('./models/Atrium/MaterialStudy/Maps/*.png',{eager:true,query:'?url',import:'default'});
const mobilePaths=import.meta.glob('./models/Atrium/MaterialStudy/MobileMaps/*.png',{eager:true,query:'?url',import:'default'});
const hdr={
  first:new URL('./models/Atrium/MaterialStudy/Room_01.hdr',import.meta.url),
  second:new URL('./models/Atrium/MaterialStudy/Room_02.hdr',import.meta.url),
  third:new URL('./models/Atrium/Gallery/Room_03.hdr',import.meta.url)
};
const rules=catalog.rules.map(([exp,kind])=>[new RegExp(exp,'i'),kind]);
function family(name){
  if(/indicator|opal| led|emission|lighting|cove light|amber strip|concealed amber|velvet guard fibers/i.test(name))return null;
  return rules.find(([exp])=>exp.test(name))?.[1]||'polymer';
}
// A swatch stores relief direction in RG, albedo variation in B and roughness in A.
// It augments the print, book-cover and LCD maps rather than replacing their pixels.
export function surfaceLibrary(renderer){
  const loader=new THREE.TextureLoader(),textures=new Map(),cm=new THREE.PMREMGenerator(renderer);
  const mobile=navigator.connection?.saveData||matchMedia('(pointer:coarse) and (max-width:1100px)').matches;
  const aniso=Math.min(mobile?8:12,renderer.capabilities.getMaxAnisotropy()||1),tufts=[];
  function swatch(kind){
    const url=mobile?mobilePaths[`./models/Atrium/MaterialStudy/MobileMaps/${kind}.png`]:paths[`./models/Atrium/MaterialStudy/Maps/${kind}.png`];
    if(!textures.has(kind))textures.set(kind,loader.loadAsync(url).then(t=>{
      t.colorSpace=THREE.NoColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=aniso;
      t.generateMipmaps=true;t.minFilter=THREE.LinearMipmapLinearFilter;return t;
    }).catch(e=>{textures.delete(kind);throw e;}));
    return textures.get(kind);
  }
  async function probe(level){
    const src=await new HDRLoader().loadAsync(hdr[level].href);src.mapping=THREE.EquirectangularReflectionMapping;
    const env=cm.fromEquirectangular(src);src.dispose();return env;
  }
  function finish(m,kind,tex,env,origin,boards){
    const recipe=catalog.surfaces[kind];
    m.envMap=env.texture;m.envMapIntensity=kind==='clear'?.52:kind==='brushed'?.81:.49;
    m.roughness=recipe.rough;
    if(kind==='brushed')m.metalness=Math.max(m.metalness,.72);
    if(m.isMeshPhysicalMaterial&&(kind==='pile'||kind==='cloth')){
      m.sheen=kind==='pile'?.65:.33;m.sheenRoughness=.83;
    }
    const vertical=kind==='timber'&&/flut|batten|groove|door/i.test(m.name);
    const previous=m.onBeforeCompile.bind(m),key=m.customProgramCacheKey();
    m.customProgramCacheKey=()=>`${key}|atelier-v4:${kind}:${vertical}:${boards}`;
    m.onBeforeCompile=(sh,r)=>{
      previous(sh,r);
      Object.assign(sh.uniforms,{
        samplePlate:{value:tex},sampleSpan:{value:new THREE.Vector2(...recipe.span)},
        response:{value:new THREE.Vector3(recipe.bump,recipe.variation,recipe.spread)},surfaceOrigin:{value:origin}
      });
      sh.vertexShader=`${boards?'attribute vec4 _board;varying vec4 piece;':''}
        attribute float _contact;varying float nearbyVisibility;uniform vec3 surfaceOrigin;
        varying vec3 studyPosition;varying vec3 studyNormal;\n`+sh.vertexShader.replace('#include <project_vertex>',`#include <project_vertex>
        nearbyVisibility=_contact;${boards?'piece=_board;':''}
        studyPosition=(modelMatrix*vec4(transformed,1.)).xyz-surfaceOrigin;
        studyNormal=inverseTransformDirection(transformedNormal,viewMatrix);`);
      sh.fragmentShader=`${boards?'varying vec4 piece;':''}
      varying float nearbyVisibility;varying vec3 studyPosition;varying vec3 studyNormal;
      uniform sampler2D samplePlate;uniform vec2 sampleSpan;uniform vec3 response;
      void studySide(in vec2 uv,in vec3 axisU,in vec3 axisV,in float w,inout vec2 finishBR,inout vec3 relief){
        // Use explicit gradients so projection changes on a rounded corner do not select a blurry mip.
        vec2 q=uv/sampleSpan;vec2 dx=dFdx(uv)/sampleSpan,dy=dFdy(uv)/sampleSpan;
        if(w>.001){
          vec4 t=textureGrad(samplePlate,q,dx,dy);
          finishBR+=w*t.ba;relief+=w*((t.r*2.-1.)*axisU+(t.g*2.-1.)*axisV);
        }
      }\n`+sh.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
        vec3 P=studyPosition;vec3 n=normalize(studyNormal);
        vec3 w=pow(abs(n),vec3(7.));w/=max(dot(w,vec3(1.)),.0001);
        vec2 finishBR=vec2(0.);vec3 relief=vec3(0.);
        vec3 X=vec3(1,0,0),Y=vec3(0,1,0),Z=vec3(0,0,-1);
        ${boards?`P-=piece.xyz*.001-32.;
        float along=floor(piece.w/4096.);P+=fract(piece.w/4096.)*vec3(1.17,.39,.61);
        if(along==1.){
          studySide(vec2(P.y,-P.z),Y,Z,w.x,finishBR,relief);
          studySide(vec2(P.x,-P.z),X,Z,w.y,finishBR,relief);
          studySide(P.yx,Y,X,w.z,finishBR,relief);
        }else if(along==2.){
          studySide(vec2(-P.z,P.y),Z,Y,w.x,finishBR,relief);
          studySide(vec2(-P.z,P.x),Z,X,w.y,finishBR,relief);
          studySide(P.xy,X,Y,w.z,finishBR,relief);
        }else{`:''}
        studySide(${vertical?'vec2(P.y,-P.z),Y,Z':'vec2(-P.z,P.y),Z,Y'},w.x,finishBR,relief);
        studySide(vec2(P.x,-P.z),X,Z,w.y,finishBR,relief);
        studySide(${vertical?'P.yx,Y,X':'P.xy,X,Y'},w.z,finishBR,relief);
        ${boards?'}':''}
        diffuseColor.rgb*=1.+(finishBR.x-.5)*2.*response.y;`)
      .replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>
        roughnessFactor=clamp(roughnessFactor+(finishBR.y-.5)*response.z,.055,.99);`)
      .replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
        vec3 localRelief=relief-n*dot(relief,n);
        normal=normalize(normal+mat3(viewMatrix)*localRelief*response.x*faceDirection);`)
      .replace('#include <aomap_fragment>',`#include <aomap_fragment>
        reflectedLight.indirectDiffuse*=mix(.64,1.,nearbyVisibility);
        reflectedLight.indirectSpecular*=mix(.78,1.,nearbyVisibility);`);
      if(kind==='pile'||kind==='cloth')sh.fragmentShader=sh.fragmentShader.replace('#include <opaque_fragment>',`
        float grazing=pow(1.-clamp(dot(normal,normalize(vViewPosition)),0.,1.),3.);
        outgoingLight+=diffuseColor.rgb*grazing*${kind==='pile'?'.16':'.065'}*(.65+finishBR.x);
        #include <opaque_fragment>`);
    };
    m.needsUpdate=true;
  }
  return {
    async apply(model,level){
      const materials=new Set(),noBoard=new Set();model.traverse(o=>{if(o.isMesh){materials.add(o.material);if(!o.geometry.attributes._board)noBoard.add(o.material);}});
      const types=[...new Set([...materials].map(m=>family(m.name)).filter(Boolean))];
      const [env,plates,pile]=await Promise.all([probe(level),Promise.all(types.map(swatch)),level==='first'?
        new GLTFLoader().loadAsync(new URL('./models/Atrium/MaterialStudy/Close_plush.glb',import.meta.url).href):null]);
      for(const m of materials){const kind=family(m.name);if(kind)finish(m,kind,plates[types.indexOf(kind)],env,model.position,kind==='timber'&&!noBoard.has(m));}
      if(pile){
        model.add(pile.scene);
        pile.scene.traverse(o=>{if(o.isMesh){
          o.geometry.computeBoundingSphere();o.visible=false;o.receiveShadow=true;o.castShadow=false;
          tufts.push({o,sphere:new THREE.Sphere()});
        }});
      }
    },
    updatePile(camera){
      for(const {o,sphere} of tufts){
        // Short fibers are sub-pixel at a distance. Only submit the groom for close inspection.
        sphere.copy(o.geometry.boundingSphere).applyMatrix4(o.matrixWorld);
        o.visible=camera.position.distanceTo(sphere.center)<sphere.radius*(o.visible?5.2:4.7);
      }
    }
  };
}
