// Interiors can be seen through the wing openings; the walls themselves stay visible.
// Work in plan coordinates. No per-frame ray casts against the furnished mesh.
const front=2.25,back=-7,depth=1.85;
function clearSight(x,z,tx,tz){
  const dx=tx-x,dz=tz-z;
  if(Math.abs(dx)>.0001)for(const side of [-1,1])for(const wall of [1.95,4.14,5.75,8]){
    const t=(side*wall-x)/dx;if(t<=.001||t>=.999)continue;
    const at=z+t*dz;if(at<back+.04||at>front-.04)continue;
    if(wall===1.95||wall===8)return false;
    const j=Math.min(4,Math.floor((front-at)/depth));
    const door=front-(j+.5)*depth+.35;
    if(Math.abs(at-door)>.62)return false;
  }
  if(Math.abs(dz)>.0001)for(let j=0;j<=5;j++){
    const t=(front-j*depth-z)/dz;if(t<=.001||t>=.999)continue;
    const at=Math.abs(x+t*dx);
    if((at>2.02&&at<4.07)||(at>5.82&&at<7.95))return false;
  }
  return true;
}
export function suiteVisibility(model){
  const rooms=[];
  model.traverse(o=>{
    const m=/^Suite_([GB])(\d\d)_details$/.exec(o.name);if(!m)return;
    const n=Number(m[2])-1,outer=n>=5,side=m[1]==='G'?-1:1;
    rooms.push({o,outer,side,x:side*(outer?5.75:4.14),z:front-(n%5+.5)*depth});
  });
  let px=NaN,pz=NaN;
  return pos=>{
    if(!pos){for(const {o} of rooms)o.visible=true;px=pz=NaN;return;}
    const {x,z}=pos;if(Math.abs(x-px)+Math.abs(z-pz)<.075)return;px=x;pz=z;
    for(const room of rooms){
      const ax=x*room.side,inside=Math.abs(z-room.z)<.98&&(room.outer?ax>=5.70:ax>=1.92&&ax<=4.20);
      room.o.visible=inside||[-.55,-.28,0,.28,.55].some(d=>clearSight(x,z,room.x,room.z+.35+d));
    }
  };
}
