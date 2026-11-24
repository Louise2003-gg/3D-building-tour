// Refresh authored screen/print artwork without re-exporting the floor geometry.
import fs from 'node:fs';
const art='models/Atrium/Studio/Textures',dir='models/Atrium/Architectural';
const print=new Set(['keys','studio','library','welcome','security','cartons','blocks']);
for(const level of ['01','02','03']){
  const path=`${dir}/Level_${level}.glb`,src=fs.readFileSync(path);
  const jsonSize=src.readUInt32LE(12),g=JSON.parse(src.toString('utf8',20,20+jsonSize));
  const binary=src.subarray(28+jsonSize),replace=new Map();
  for(const image of g.images.filter(i=>print.has(i.name))){
    const data=fs.readFileSync(`${art}/${image.name}.png`);
    if(data.readUInt32BE(16)!==1536||data.readUInt32BE(20)!==896)throw Error(`Regenerate ${image.name} first`);
    image.mimeType='image/png';replace.set(image.bufferView,data);
  }
  const parts=[];let size=0;
  g.bufferViews.forEach((v,i)=>{
    const start=v.byteOffset||0;
    const data=replace.get(i)||binary.subarray(start,start+v.byteLength);
    v.byteOffset=size;v.byteLength=data.length;parts.push(data);
    const pad=(4-data.length%4)%4;parts.push(Buffer.alloc(pad));size+=data.length+pad;
  });
  g.buffers[0].byteLength=size;
  const text=Buffer.from(JSON.stringify(g)),j=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]);
  const hdr=Buffer.from(src.subarray(0,20)),bh=Buffer.alloc(8);
  hdr.writeUInt32LE(28+j.length+size,8);hdr.writeUInt32LE(j.length,12);
  bh.writeUInt32LE(size);bh.write('BIN\0',4);
  fs.writeFileSync(path+'.tmp',Buffer.concat([hdr,j,bh,...parts]));fs.renameSync(path+'.tmp',path);
  console.log(`Floor ${level}: ${replace.size} HD artwork textures embedded`);
}
