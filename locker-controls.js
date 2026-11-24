import * as THREE from 'three';

const front=1.423,start=2.49,pitch=(6.94-start)/9,length=pitch-.016;
const maxAngle=1.34;
const hinge=id=>({side:id>18?1:-1,z:-(start+Math.floor(((id-1)%18)/2)*pitch+.008)});
const storage=new WeakMap();
export function lockersFor(model){
  if(storage.has(model))return storage.get(model);
  const group=model.getObjectByName('LockerFronts');
  if(!group)throw Error('Missing fitted locker fronts');
  const doors=Array.from({length:37},()=>[]),seen=new Set();
  group.traverse(o=>{
    if(!o.isMesh)return;
    const p=o.geometry.attributes.position,n=o.geometry.attributes.normal;
    if(seen.has(p))return;seen.add(p);
    const buckets=new Map();
    for(let i=0;i<p.count;i++){
      const x=p.getX(i),y=p.getY(i),z=p.getZ(i),j=THREE.MathUtils.clamp(Math.floor((-z-start)/pitch),0,8);
      const id=(x>0?19:1)+2*j+Number(y>=1.26);
      if(!buckets.has(id))buckets.set(id,[]);
      buckets.get(id).push([i,x,z,n.getX(i),n.getZ(i)]);
    }
    for(const [id,values] of buckets)doors[id].push({p,n,values});
  });
  let open=0,angle=0,target=0,queued=0;
  function pose(id,a){
    if(!id)return;
    const h=hinge(id),x0=h.side*front,c=Math.cos(a),s=Math.sin(a)*h.side;
    for(const {p,n,values} of doors[id]){
      for(const [i,x,z,nx,nz] of values){
        p.setX(i,x0+c*(x-x0)+s*(z-h.z));p.setZ(i,h.z-s*(x-x0)+c*(z-h.z));
        n.setX(i,c*nx+s*nz);n.setZ(i,-s*nx+c*nz);
      }
      p.needsUpdate=n.needsUpdate=true;
    }
  }
  function obstructs(x,z,a){
    if(!open||a<.015)return false;
    const h=hinge(open),dx=-h.side*Math.sin(a),dz=-Math.cos(a);
    const u=x-h.side*front,v=z-h.z,t=THREE.MathUtils.clamp(u*dx+v*dz,0,length);
    return (u-t*dx)**2+(v-t*dz)**2<.215**2;
  }
  const api={
    state(){return {id:open,angle};},
    aimed(camera,direction){
      if(Math.abs(camera.position.x)>1.40||camera.position.z> -1.8||Math.abs(direction.x)<.22)return 0;
      const side=Math.sign(direction.x),t=(side*front-camera.position.x)/direction.x;
      if(t<0||t>2.35)return 0;
      const z=camera.position.z+t*direction.z,y=camera.position.y+t*direction.y;
      if(-z<start||-z>=6.94||y<.13||y>2.39)return 0;
      return (side===1?19:1)+2*Math.floor((-z-start)/pitch)+Number(y>=1.26);
    },
    label(id){return `${id===open&&target?'Close':'Open'} locker ${String(id).padStart(2,'0')}`;},
    toggle(id){
      if(!id)return;
      if(open&&open!==id){queued=id;target=0;}
      else{open=id;queued=0;target=target?0:maxAngle;}
    },
    advance(dt,x,z){
      if(!open||angle===target)return false;
      const next=THREE.MathUtils.clamp(target,angle-2.3*dt,angle+2.3*dt);
      if(obstructs(x,z,next))return false;
      angle=next;pose(open,next);
      if(!angle){open=queued;target=queued?maxAngle:0;queued=0;}
      return true;
    },
    blocks(x,z){return obstructs(x,z,angle);},
    reset(){pose(open,0);open=angle=target=queued=0;}
  };
  storage.set(model,api);return api;
}
