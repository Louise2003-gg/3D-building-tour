// Bake obstacle footprints from the furnished GLBs, including narrow rails and tabletops.
// One texel = 6.25 cm. Each triangle is clipped to the walker's body height first.
import fs from 'node:fs';
import {Matrix4,Vector3,Quaternion} from 'three';
const W=256,H=224,S=16;
for(const level of [1,2,3]){
  const buf=fs.readFileSync(`models/Atrium/${level===3?'Gallery':'MaterialStudy'}/Level_0${level}.glb`);
  const len=buf.readUInt32LE(12),g=JSON.parse(buf.toString('utf8',20,20+len)),bin=28+len;
  const grid=new Uint8Array(W*H);
  function attr(id){
    const a=g.accessors[id],v=g.bufferViews[a.bufferView],T={5121:Uint8Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array}[a.componentType];
    const dim=a.type==='VEC3'?3:1,stride=(v.byteStride||dim*T.BYTES_PER_ELEMENT)/T.BYTES_PER_ELEMENT;
    return {arr:new T(buf.buffer,buf.byteOffset+bin+(v.byteOffset||0)+(a.byteOffset||0),(a.count-1)*stride+dim),stride,count:a.count};
  }
  function clip(poly,h,sign){
    const out=[];
    for(let i=0;i<poly.length;i++){
      const a=poly[i],b=poly[(i+1)%poly.length],inside=(a.y-h)*sign>=0;
      if(inside)out.push(a);
      if(inside!==((b.y-h)*sign>=0))out.push(a.clone().lerp(b,(h-a.y)/(b.y-a.y)));
    }return out;
  }
  function stamp(poly){
    const pts=poly.map(v=>[(v.x+8)*S,(v.z+7)*S]);
    const zs=pts.map(v=>v[1]);
    for(let z=Math.max(0,Math.floor(Math.min(...zs)));z<=Math.min(H-1,Math.floor(Math.max(...zs)));z++){
      let lo=Infinity,hi=-Infinity;
      function add(x){lo=Math.min(lo,x);hi=Math.max(hi,x);}
      for(let i=0;i<pts.length;i++){
        const [x,y]=pts[i],[u,v]=pts[(i+1)%pts.length];
        if(y>=z&&y<=z+1)add(x);
        for(const k of [z,z+1])if((y<k)!==(v<k))add(x+(u-x)*(k-y)/(v-y));
      }
      if(lo<=hi&&hi>=0&&lo<W)grid.fill(255,z*W+Math.max(0,Math.floor(lo)),z*W+Math.min(W,Math.floor(hi)+1));
    }
  }
  function visit(id,parent){
    const n=g.nodes[id],mat=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3(...(n.translation||[0,0,0])),new Quaternion(...(n.rotation||[0,0,0,1])),new Vector3(...(n.scale||[1,1,1])));
    mat.premultiply(parent);
    if(n.mesh!=null)for(const p of g.meshes[n.mesh].primitives){
      const pos=attr(p.attributes.POSITION),idx=p.indices!=null?attr(p.indices):null;
      const verts=Array.from({length:pos.count},(_,i)=>new Vector3().fromArray(pos.arr,i*pos.stride).applyMatrix4(mat));
      for(let i=0;i<(idx?.count||pos.count);i+=3){
        const t=[0,1,2].map(k=>verts[idx?idx.arr[i+k]:i+k]);
        if(t.every(v=>v.y<.135)||t.every(v=>v.y>1.84))continue;
        if(n.name==='Two glazed access lanes'&&t.every(v=>Math.abs(v.z-4.53)<.05))continue;
        const poly=clip(clip(t,.135,1),1.84,-1);
        if(poly.length)stamp(poly);
      }
    }
    for(const c of n.children||[])visit(c,mat);
  }
  for(const id of g.scenes[g.scene].nodes)visit(id,new Matrix4());
  // Verify that a 40 cm-wide visitor can reach the lift and the main occupied zones.
  const blocked=(x,z)=>{
    for(let dz=-3;dz<=3;dz++)for(let dx=-3;dx<=3;dx++)if(dx*dx+dz*dz<=10 &&
      (x+dx<0||x+dx>=W||z+dz<0||z+dz>=H||grid[(z+dz)*W+x+dx]))return true;
    return false;
  };
  const cell=([x,z])=>Math.floor((z+7)*S)*W+Math.floor((x+8)*S);
  const spawn=level===1?[0,6.18]:[4.86,6.03],seen=new Uint8Array(W*H),queue=[cell(spawn)];
  if(blocked(queue[0]%W,Math.floor(queue[0]/W)))throw Error(`Blocked spawn ${level}`);
  seen[queue[0]]=1;
  for(let i=0;i<queue.length;i++)for(const d of [-W,W,-1,1]){
    const j=queue[i]+d;if(!seen[j]&&!blocked(j%W,Math.floor(j/W))){queue.push(j);seen[j]=1;}
  }
  const bedrooms=[];
  for(const side of [-1,1])for(const outer of [false,true])for(let j=0;j<5;j++){
    const x=side*(outer?8-1.76:1.95+1.76),z=2.25-(j+.5)*1.85+.51;
    bedrooms.push([x,z],[side*(outer?8-1.32:1.95+1.32),z]);
  }
  for(const dest of (level===1?[[4.86,6.03],[-.45,1.8]]:level===2?[[-2.8,-3.5],[5.45,.1]]:[[.0,3.5],[.0,-1.4],[.1,-3.04],[0,-6.0],[-.95,-5.6],[.95,-5.6],...bedrooms]))
    if(!seen[cell(dest)]){
      for(let z=0;z<H;z+=4)console.log(Array.from({length:W/4},(_,i)=>grid[z*W+i*4]?'#':seen[z*W+i*4]?'.':' ').join(''));
      throw Error(`Unreachable ${dest} on level ${level}`);
    }
  fs.mkdirSync('walkmaps',{recursive:true});fs.writeFileSync(`walkmaps/0${level}.bin`,grid);
  console.log(`Floor ${level}: ${Math.round(queue.length/S**2)} m² reachable.`);
}
