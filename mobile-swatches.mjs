// Downfilter channel-packed data in linear space; keep the sharp screen/label art in the GLBs.
import fs from 'node:fs';
import zlib from 'node:zlib';
const dir='models/Atrium/MaterialStudy',src=`${dir}/Maps`,dst=`${dir}/MobileMaps`;fs.mkdirSync(dst,{recursive:true});
const table=Array.from({length:256},(_,i)=>{for(let j=0;j<8;j++)i=i&1?0xedb88320^(i>>>1):i>>>1;return i>>>0;});
function chunk(tag,body){
  const out=Buffer.alloc(body.length+12);out.writeUInt32BE(body.length);out.write(tag,4);body.copy(out,8);
  let crc=0xffffffff;for(const v of out.subarray(4,-4))crc=table[(crc^v)&255]^(crc>>>8);
  out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4);return out;
}
let before=0,after=0;
for(const name of fs.readdirSync(src).filter(n=>n.endsWith('.png'))){
  const file=fs.readFileSync(`${src}/${name}`),w=file.readUInt32BE(16),h=file.readUInt32BE(20),parts=[];
  for(let i=8;i<file.length;){const n=file.readUInt32BE(i);if(file.toString('ascii',i+4,i+8)==='IDAT')parts.push(file.subarray(i+8,i+8+n));i+=12+n;}
  const bytes=zlib.inflateSync(Buffer.concat(parts)),stride=1+4*w;
  for(let y=0;y<h;y++){let p=y*stride;if(bytes[p++]!==1)throw Error('Expected generated sub-filter map');for(let i=4;i<4*w;i++)bytes[p+i]=(bytes[p+i]+bytes[p+i-4])&255;}
  const W=w/2,H=h/2,filtered=Buffer.alloc(H*(1+4*W));
  for(let y=0;y<H;y++){
    const off=y*(1+4*W),prev=[0,0,0,0];filtered[off]=1;
    for(let x=0;x<W;x++)for(let c=0;c<4;c++){
      const p=2*y*stride+1+x*8+c;
      const v=Math.min(255,Math.round((bytes[p]+bytes[p+4]+bytes[p+stride]+bytes[p+stride+4])/8)*2);
      filtered[off+1+x*4+c]=(v-prev[c])&255;prev[c]=v;
    }
  }
  const hdr=Buffer.from(file.subarray(16,29));hdr.writeUInt32BE(W);hdr.writeUInt32BE(H,4);
  const out=Buffer.concat([file.subarray(0,8),chunk('IHDR',hdr),chunk('IDAT',zlib.deflateSync(filtered,{level:9})),chunk('IEND',Buffer.alloc(0))]);
  fs.writeFileSync(`${dst}/${name}`,out);before+=file.length;after+=out.length;
}
console.log(`Shared surface maps: ${(before/1e6).toFixed(2)} MB desktop; ${(after/1e6).toFixed(2)} MB mobile`);
