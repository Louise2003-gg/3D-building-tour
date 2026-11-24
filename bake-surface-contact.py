"""Bake short-range hemispherical visibility into the existing web meshes without remeshing.
Run with Blender -b --python bake-surface-contact.py. The original buffers are copied verbatim.
"""
import os,json,struct,math,re,copy,zlib,sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','Atrium')
out=os.path.join(root,'MaterialStudy');os.makedirs(out,exist_ok=True)
gallery='--gallery' in sys.argv
if gallery:out=os.path.join(root,'Gallery')
for level in ([3] if gallery else [1,2,3]):
    name=f'Level_0{level}.glb';data=open(os.path.join(root,'Gallery/source' if gallery else 'Architectural',name),'rb').read()
    size=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+size]);raw=bytearray(data[28+size:])
    assert all(not any(k in n for k in ['matrix','rotation','scale','translation']) for n in g['nodes'])
    def attr(key):
        a=g['accessors'][key];v=g['bufferViews'][a['bufferView']]
        dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];dim=3 if a['type']=='VEC3' else 1
        ofs=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],dim),dt,raw,ofs,strides=(v.get('byteStride',dim*np.dtype(dt).itemsize),np.dtype(dt).itemsize)).copy()
    def put(data,component,shape,count,target=34962,stride=0,normalized=False):
        raw.extend(b'\0'*((-len(raw))%4))
        view=dict(buffer=0,byteOffset=len(raw),byteLength=len(data),target=target)
        if stride:view['byteStride']=stride
        g['bufferViews'].append(view);raw.extend(data)
        a=dict(bufferView=len(g['bufferViews'])-1,componentType=component,count=count,type=shape)
        if normalized:a['normalized']=True
        g['accessors'].append(a);return len(g['accessors'])-1
    if level==1:
        groom=open(os.path.join(out,'Close_plush.glb'),'rb').read()
        gg=json.loads(groom[20:20+struct.unpack_from('<I',groom,12)[0]])
        bears=[(np.array(n['translation']),n['scale'][0]) for n in gg['nodes'] if 'mesh' in n]
        for mesh in g['meshes']:
            for p in mesh['primitives'][:]:
                mat=g['materials'][p['material']]
                if mat['name']!='Sage enamel':continue
                idx=attr(p['indices']).astype('<u4').reshape(-1,3)
                pts=attr(p['attributes']['POSITION'])[idx].mean(axis=1);mask=np.zeros(len(idx),dtype=bool)
                for center,scale in bears:
                    local=(pts-center)/scale
                    mask|=(np.abs(local[:,0])<.26)&(local[:,1]>.47)&(local[:,1]<.77)&(np.abs(local[:,2])<.26)
                if not np.any(mask):continue
                scarf=copy.deepcopy(p);alternate=copy.deepcopy(mat);alternate['name']='Woven sage neckerchief'
                alternate['pbrMetallicRoughness']['roughnessFactor']=.86
                scarf['material']=len(g['materials']);g['materials'].append(alternate)
                scarf['indices']=put(idx[mask].tobytes(),5125,'SCALAR',int(mask.sum())*3,34963)
                if (~mask).any():p['indices']=put(idx[~mask].tobytes(),5125,'SCALAR',int((~mask).sum())*3,34963)
                else:mesh['primitives'].remove(p)
                mesh['primitives'].append(scarf)
    # Identify connected timber pieces even where hard normals split a corner into separate vertices.
    # Store grain direction, center and a stable phase per board so adjacent shelves are not carbon copies.
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            if not re.search('maple|oak|walnut|beech|sawn ash',g['materials'][p['material']]['name'],re.I):continue
            pts=attr(p['attributes']['POSITION']);idx=attr(p['indices']).reshape(-1,3)
            coords,inv=np.unique(np.rint(pts*10000).astype(np.int32),axis=0,return_inverse=True);inv=inv.reshape(-1)
            parent=list(range(len(coords)))
            def find(i):
                while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
                return i
            for a,b,c in inv[idx].tolist():
                rootid=find(a);parent[find(b)]=rootid;parent[find(c)]=rootid
            islands={}
            for i in range(len(coords)):islands.setdefault(find(i),[]).append(i)
            data=np.empty((len(coords),4),'<u2')
            for island in islands.values():
                xyz=coords[island];lo,hi=xyz.min(axis=0),xyz.max(axis=0);center=(hi+lo)/20000
                axis=int(np.argmax(hi-lo));phase=zlib.crc32(lo.tobytes())%4096
                data[island,:3]=np.clip(np.rint((center+32)*1000),0,65535);data[island,3]=4096*axis+phase
            p['attributes']['_BOARD']=put(data[inv].tobytes(),5123,'VEC4',len(inv),stride=8)
    verts=[];tris=[];groups={};offset=0
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            key=(p['attributes']['POSITION'],p['attributes']['NORMAL'])
            groups.setdefault(key,[]).append(p)
            if g['materials'][p['material']].get('alphaMode')=='BLEND':continue
            pts=attr(key[0]);idx=attr(p['indices']).reshape(-1,3)
            verts.extend(pts.tolist());tris.extend((idx.astype(np.int64)+offset).tolist());offset+=len(pts)
    tree=BVHTree.FromPolygons(verts,tris,all_triangles=True);del verts,tris
    golden=math.pi*(3-math.sqrt(5))
    # Cosine-weighted directions and two physical radii capture deep joins as well as chair feet.
    directions=[]
    for k in range(10):
        r=math.sqrt((k+.5)/10);angle=k*golden
        directions.append((r*math.cos(angle),r*math.sin(angle),math.sqrt(1-r*r),.31 if k%2 else .76))
    cache={};added=0
    for (position,normal),prims in groups.items():
        pts=attr(position);ns=attr(normal);values=bytearray(len(pts))
        # Split normals at hard edges are intentionally kept separate.
        for i,(pt,n) in enumerate(zip(pts,ns)):
            key=(*np.rint(pt*1200).astype(int),*np.rint(n*40).astype(int))
            value=cache.get(key)
            if value is None:
                N=Vector(n).normalized();P=Vector(pt)+N*.0035;U=N.orthogonal().normalized();V=N.cross(U)
                occlusion=0.
                for a,b,c,r in directions:
                    hit=tree.ray_cast(P,U*a+V*b+N*c,r)[3]
                    if hit is not None:occlusion+=(1-hit/r)**1.2
                value=round(255*(1-occlusion/10));cache[key]=value
            values[i]=value
        index=len(g['accessors']);view=len(g['bufferViews']);raw.extend(b'\0'*((-len(raw))%4))
        g['bufferViews'].append(dict(buffer=0,byteOffset=len(raw),byteLength=len(values),target=34962,byteStride=4))
        # Vertex attributes have 4-byte aligned elements in a glTF vertex buffer.
        interleaved=bytearray(4*len(values));interleaved[::4]=values;raw+=interleaved
        g['bufferViews'][-1]['byteLength']=len(interleaved)
        g['accessors'].append(dict(bufferView=view,componentType=5121,normalized=True,count=len(values),type='SCALAR'))
        for p in prims:p['attributes']['_CONTACT']=index
        added+=len(values)
    g['buffers'][0]['byteLength']=len(raw);meta=json.dumps(g,separators=(',',':')).encode();meta+=b' '*((-len(meta))%4)
    dst=os.path.join(out,name)
    with open(dst+'.tmp','wb') as f:
        f.write(struct.pack('<4sII',b'glTF',2,28+len(meta)+len(raw))+struct.pack('<I4s',len(meta),b'JSON')+meta+struct.pack('<I4s',len(raw),b'BIN\0')+raw)
    os.replace(dst+'.tmp',dst)
    print(f'{name}: baked contact for {added} vertices, {len(cache)} distinct normal/position samples',flush=True)
