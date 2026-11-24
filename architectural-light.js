import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import layout from './luminaire-layout.json';

const atlasURLs={
  first:new URL('./models/Atrium/Architectural/Irradiance_01.png',import.meta.url),
  second:new URL('./models/Atrium/Architectural/Irradiance_02.png',import.meta.url),
  third:new URL('./models/Atrium/Gallery/Irradiance_03.png',import.meta.url)
};
export async function lightVolume(key){
  const t=await new THREE.TextureLoader().loadAsync(atlasURLs[key].href);
  t.colorSpace=THREE.NoColorSpace;t.generateMipmaps=false;t.minFilter=t.magFilter=THREE.LinearFilter;
  return t;
}

// Fixtures are shared instances. Geometry and the baked lighting both use the same photometric layout.
export function architecturalLight(renderer,scene){
  const body=new THREE.MeshStandardMaterial({color:0x62594b,metalness:.55,roughness:.28});
  const opal=[0xffdfae,0xffeaca,0xffefdb].map(color=>new THREE.MeshStandardMaterial({color:0xfff8ef,emissive:color,emissiveIntensity:5.6,roughness:.31}));
  const cube=new THREE.BoxGeometry(),disc=new THREE.CylinderGeometry(.5,.5,1,24);
  const shade=new THREE.CylinderGeometry(.22,.5,1,32);
  const groups={};
  for(const [key,fixtures] of Object.entries(layout)){
    const g=new THREE.Group(),pieces=new Map(),roof=key==='third'?4.46:3.74;
    function add(geo,m,x,y,z,w,h,d){
      const id=geo.uuid+m.uuid;
      if(!pieces.has(id))pieces.set(id,{geo,m,matrices:[]});
      const mat=new THREE.Matrix4().makeScale(w,h,d);mat.setPosition(x,y,z);pieces.get(id).matrices.push(mat);
    }
    for(const {x,z,h,w,d,kind,temp} of fixtures){
      const m=opal[temp<3300?0:temp<3750?1:2];
      if(kind==='linear'){
        add(cube,body,x,h,z,w,.055,d);add(cube,m,x,h-.029,z,w-.025,.006,d-.018);
        for(const s of [-1,1])add(disc,body,x+s*w*.36,(h+roof)/2,z-s*d*.36,.008,roof-h,.008);
      }else if(kind==='pendant'){
        add(shade,body,x,h+.07,z,w,.14,d);add(disc,m,x,h-.003,z,w*.93,.004,d*.93);
        add(disc,body,x,(h+.14+roof)/2,z,.013,roof-h-.14,.013);
      }else{
        add(disc,body,x,h+.012,z,w*1.1,.032,d*1.1);add(disc,m,x,h-.006,z,w*.88,.006,d*.88);
      }
    }
    for(const {geo,m,matrices} of pieces.values()){
      const batch=new THREE.InstancedMesh(geo,m,matrices.length);
      matrices.forEach((matrix,i)=>batch.setMatrixAt(i,matrix));batch.computeBoundingSphere();g.add(batch);
    }
    g.visible=false;scene.add(g);groups[key]=g;
  }
  // An offscreen mirror supplies parallax-correct reflections. Only porcelain samples it.
  // Draw it at a modest resolution, reproject the cached image between updates, and use its
  // mip levels for a rough glazed finish rather than adding a second full-resolution scene.
  const compact=matchMedia('(pointer:coarse) and (max-width:1100px)').matches||navigator.connection?.saveData;
  const mirror=new Reflector(new THREE.PlaneGeometry(1,1),{textureWidth:compact?320:512,textureHeight:compact?200:320,multisample:0,clipBias:.001});
  mirror.rotation.x=-Math.PI/2;mirror.position.y=.015;mirror.updateMatrixWorld();
  const rt=mirror.getRenderTarget();rt.texture.generateMipmaps=true;rt.texture.minFilter=THREE.LinearMipmapLinearFilter;
  const inverse=mirror.matrixWorld.clone().invert(),reflectionMatrix={value:new THREE.Matrix4()},valid={value:0};
  const tiled=new Set(),offsets={},pos=new THREE.Vector3(),rot=new THREE.Quaternion();let active=null,aspect=0,captured=false;
  return {
    invalidate(){captured=false;},
    stack(both){Object.entries(offsets).forEach(([key,u])=>u.value=both?{first:0,second:3.96,third:7.92}[key]:0);},
    walking(level){
      for(const [k,g] of Object.entries(groups))g.visible=k===level;
      active=level;valid.value=0;captured=false;
    },
    prepare(camera,moving){
      if(!active)return;
      const distance=pos.distanceTo(camera.position),angle=rot.angleTo(camera.quaternion);
      if(moving){
        // Reproject the last still capture, fading to the standard PBR environment as
        // it becomes stale. Never render the entire building twice on a motion frame.
        valid.value=captured&&camera.aspect===aspect?Math.max(0,1-distance/1.7-angle/.85):0;
        return false;
      }
      const moved=!captured||distance>.001||angle>.001||camera.aspect!==aspect;
      if(!moved)return;
      camera.updateMatrixWorld();
      const shadow=renderer.shadowMap.needsUpdate;
      // Exclude every recipient of the reflection target, to avoid sampling the active framebuffer.
      try {
        for(const m of tiled)m.visible=false;
        renderer.shadowMap.needsUpdate=false;
        mirror.onBeforeRender(renderer,scene,camera);
        reflectionMatrix.value.copy(mirror.material.uniforms.textureMatrix.value).multiply(inverse);
        pos.copy(camera.position);rot.copy(camera.quaternion);captured=true;valid.value=1;aspect=camera.aspect;
      } finally {renderer.shadowMap.needsUpdate=shadow;for(const m of tiled)m.visible=true;}
      return true;
    },
    apply(model,key,atlas){
      const offset=offsets[key]={value:0},seen=new Set();
      model.traverse(o=>{
        if(!o.isMesh)return;
        const m=o.material;
        if(seen.has(m)||m.transparent||!m.isMeshStandardMaterial)return;seen.add(m);
        const tile=/^(Sandstone|Sand tile|Blush travertine)(\.|$)/i.test(m.name);
        if(tile){
          // Procedural Blender albedo isn't exported as a bitmap; match the porcelain's linear tint.
          m.color.setRGB(.52,.465,.395);m.roughness=.185;m.metalness=0;tiled.add(m);
        }
        const prior=m.onBeforeCompile.bind(m),cache=m.customProgramCacheKey();
        m.customProgramCacheKey=()=>cache+':architectural-light:'+Number(tile);
        m.onBeforeCompile=(shader,r)=>{
          prior(shader,r);
          Object.assign(shader.uniforms,{atelierAtlas:{value:atlas},atelierBase:offset});
          shader.vertexShader='varying vec3 atelierWorld;\n'+shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\natelierWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
          shader.fragmentShader=`varying vec3 atelierWorld;
          uniform sampler2D atelierAtlas; uniform float atelierBase;
          vec3 atelierLight(vec3 p){
            if(abs(p.x)>8.1||abs(p.z)>7.1)return vec3(0.);
            vec2 uv=clamp((p.xz+vec2(8.,7.))/vec2(16.,14.),vec2(.5/96.,.5/84.),vec2(1.-.5/96.,1.-.5/84.));
            float slice=clamp((p.y-atelierBase-.035)/.75,0.,4.);
            vec3 a=texture2D(atelierAtlas,vec2(uv.x,(floor(slice)+uv.y)/5.)).rgb;
            vec3 b=texture2D(atelierAtlas,vec2(uv.x,(min(4.,floor(slice)+1.)+uv.y)/5.)).rgb;
            return mix(a,b,fract(slice));
          }\n`+shader.fragmentShader;
          shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_end>',`#include <lights_fragment_end>
            vec3 fittedLight=atelierLight(atelierWorld);
            reflectedLight.indirectDiffuse*=vec3(.73,.75,.78);
            reflectedLight.indirectDiffuse+=diffuseColor.rgb*fittedLight*1.42;`);
          if(!tile)return;
          Object.assign(shader.uniforms,{glazeCapture:{value:rt.texture},glazeProjection:reflectionMatrix,glazeLive:valid});
          shader.fragmentShader=`uniform sampler2D glazeCapture; uniform mat4 glazeProjection; uniform float glazeLive;\n`+shader.fragmentShader;
          shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
            vec2 slab=floor(atelierWorld.xz);float tone=fract(sin(dot(slab,vec2(41.23,73.57)))*3137.37);
            diffuseColor.rgb*=.92+.11*tone;`)
          .replace('#include <opaque_fragment>',`
            if(glazeLive>.001){
              vec4 proj=glazeProjection*vec4(atelierWorld,1.);
              vec3 coatingNormal=inverseTransformDirection(normal,viewMatrix);
              vec2 st=proj.xy/max(.0001,proj.w)+coatingNormal.xz*.002;
              float edge=smoothstep(0.,.025,min(min(st.x,st.y),min(1.-st.x,1.-st.y)));
              float incidence=clamp(normalize(cameraPosition-atelierWorld).y,0.,1.);
              float fresnel=.085+.48*pow(1.-incidence,3.);
              vec3 glaze=textureLod(glazeCapture,clamp(st,.001,.999),clamp(.45+.85*incidence+(roughnessFactor-.20)*5.,.15,2.4)).rgb;
              outgoingLight=mix(outgoingLight,glaze,glazeLive*edge*fresnel*step(0.,proj.w));
            }
            #include <opaque_fragment>`);
        };
      });
    }
  };
}
