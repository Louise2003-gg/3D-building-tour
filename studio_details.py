"""Create the detailed editable edition, then bake static web batches by room/zone."""
import bpy as b, math, os, re, random, struct, zlib
from math import sin,cos,pi
from mathutils import Vector
import numpy as np
base=os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','Atrium')
src=os.path.join(base,'Furnished');out=os.path.join(base,'Studio');tex=os.path.join(out,'Textures')
os.makedirs(tex,exist_ok=True)
def png(name,a):
    a=np.uint8(np.clip(a,0,255));h,w,_=a.shape
    def chunk(k,x):return struct.pack('>I',len(x))+k+x+struct.pack('>I',zlib.crc32(k+x)&0xffffffff)
    raw=b''.join(b'\0'+r.tobytes() for r in a)
    with open(os.path.join(tex,name+'.png'),'wb') as f:f.write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,8))+chunk(b'IEND',b''))
y,x=np.mgrid[:256,:256];u=(x+.5)/256;v=1-(y+.5)/256;dist=np.abs(u-.5);rng=np.random.default_rng(375)
for name,c in [('laurel',(77,116,57)),('sage',(107,139,89)),('fern',(88,130,64))]:
    rib=np.exp(-((u-.5)/.014)**2);veins=np.exp(-((np.sin(pi*(v*11-dist*4.5)))/.19)**2)
    light=.78+.19*np.cos(dist*pi)+.13*v+.06*np.sin(v*25+u*5)+rng.normal(0,.025,x.shape)
    png(name,light[:,:,None]*c+rib[:,:,None]*[51,55,25]+veins[:,:,None]*[16,18,10])
noise=rng.normal(0,1,x.shape)
nap=(noise+np.roll(noise,1,axis=0)+np.roll(noise,2,axis=0))/2
png('honey-nap',np.array([178,126,83])*(1+.085*nap[:,:,None]))
grain=.99+.032*np.sin(2*pi*(v*19+.10*np.sin(2*pi*u)))+.023*np.sin(2*pi*(v*39+.26*np.sin(2*pi*(u+v))))+.012*noise
png('beech-grain',np.array([213,178,134])*grain[:,:,None])
def material(name,col,rough=.55,metal=0,image=None,emit=0):
    m=b.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    c=np.array(col)/255;c=np.where(c>.04045,((c+.055)/1.055)**2.4,c/12.92);rgba=(*c,1)
    p.inputs['Base Color'].default_value=rgba;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;m.diffuse_color=rgba
    if image:
        im=b.data.images.load(os.path.join(tex,image+'.png'),check_existing=True);im.pack()
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
        if emit:m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emit
    return m
def palette():
    global leaves,clay,soil,vein,fur,oat,coal,rose,teal,wood,gold,plastic,alloy,lcd,keys,abc
    leaves=[material('Veined '+n,(255,255,255),.46,image=n) for n in ['laurel','sage','fern']]
    for m in leaves:m.use_backface_culling=False
    clay=material('Satin ivory ceramic',(231,223,205),.31);soil=material('Rich potting soil',(79,63,49),.98)
    vein=material('Stems and petioles',(112,129,64),.71);fur=material('Brushed teddy nap',(255,255,255),.94,image='honey-nap');fur.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value=.22
    oat=material('Oatmeal plush',(228,205,165),.87);coal=material('Embroidery thread',(51,40,36),.76)
    rose=material('Clay red lacquer',(184,103,82),.46);teal=material('Sage enamel',(98,142,132),.42)
    wood=material('Waxed beech',(215,178,129),.50,image='beech-grain');gold=material('Ochre lacquer',(220,175,92),.45)
    plastic=material('Graphite polymer',(55,59,59),.42);alloy=material('Satin aluminium',(157,161,159),.33,.64)
    lcd={k:material('LCD '+k,(255,255,255),.37,image=k,emit=.28) for k in ['library','studio','welcome','security']}
    keys=material('Scissor key legends',(255,255,255),.55,image='keys')
    abc=material('Block printing',(255,255,255),.54,image='blocks')
vs=[];faces=[];uvs=[];slots=[];ids=[];sm=[]
def face(points,m,uv=None,smooth=False):
    if m not in slots:slots.append(m)
    n=len(vs);vs.extend(points);faces.append(tuple(range(n,n+len(points))));ids.append(slots.index(m));sm.append(smooth)
    uvs.extend(uv or [(p[0]*1.8,p[2]*1.8+p[1]) for p in points])
def box(x,y,z,w,d,h,m):
    p=[(x+i*w/2,y+j*d/2,z+k*h/2) for k in (-1,1) for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in f],m)
def tube(a,c,r,m,rt=None,n=8):
    a,c=Vector(a),Vector(c);axis=(c-a).normalized();p=axis.orthogonal().normalized();q=axis.cross(p);rt=r if rt is None else rt
    rings=[[v+rad*(p*cos(i*2*pi/n)+q*sin(i*2*pi/n)) for i in range(n)] for v,rad in [(a,r),(c,rt)]]
    face(list(reversed(rings[0])),m);face(rings[1],m)
    for i in range(n):j=(i+1)%n;face([rings[0][i],rings[0][j],rings[1][j],rings[1][i]],m,smooth=True)
def oval(x,y,z,w,d,h,m,n=16,k=10):
    def pt(i,j):
        a=i*2*pi/n;t=-pi/2+j*pi/k;return (x+w*cos(t)*cos(a),y+d*cos(t)*sin(a),z+h*sin(t))
    for j in range(k):
        for i in range(n):
            ij=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            if j==0:ij.pop(0)
            if j==k-1:ij.pop()
            face([pt(a,t) for a,t in ij],m,[(a/n,t/k) for a,t in ij],True)
def finish(name):
    import bmesh
    me=b.data.meshes.new(name);me.from_pydata(vs,[],faces)
    for m in slots:me.materials.append(m)
    me.polygons.foreach_set('material_index',ids);me.polygons.foreach_set('use_smooth',sm)
    uv=me.uv_layers.new(name='Detail UV');uv.data.foreach_set('uv',np.array(uvs,dtype=np.float32).ravel());me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.000015);bm.to_mesh(me);bm.free()
    o=b.data.objects.new(name,me);col.objects.link(o)
    for a in [vs,faces,uvs,slots,ids,sm]:a.clear()
    return o
def plant(k):
    # Revolved ceramic with a foot, shoulder, rolled lip and visible dark soil.
    shape=[(.193,.008),(.217,.025),(.231,.094),(.273,.385),(.266,.409),(.248,.413),(.238,.374)]
    for (r,z),(q,h) in zip(shape,shape[1:]):
        for i in range(24):
            a=2*pi*i/24;c=2*pi*(i+1)/24
            face([(r*cos(a),r*sin(a),z),(r*cos(c),r*sin(c),z),(q*cos(c),q*sin(c),h),(q*cos(a),q*sin(a),h)],clay,smooth=True)
    tube((0,0,.365),(0,0,.376),.239,soil,n=24)
    rand=random.Random(341+k)
    for i in range(30):
        a=rand.random()*2*pi;r=.22*rand.random()**.5;x=r*cos(a);y=r*sin(a);s=.004+rand.random()*.009
        face([(x-s,y,.377),(x+s,y-s,.377),(x,y+s,.382)],wood if i%3 else oat)
    for i in range([13,17,8][k]):
        a=i*2.4+.17*rand.random();e=Vector((cos(a),sin(a),0));side=Vector((-sin(a),cos(a),0))
        spread=.16+.25*rand.random();height=.35+.32*rand.random();wide=[.102,.074,.041][k]
        origin=e*rand.uniform(.025,.09)+Vector((0,0,.374));start=origin+e*.08+Vector((0,0,height*.32))
        tube(origin,start,.008,vein,.005,5)
        if k==2:
            def spine(t):return start+e*(spread*1.14*t)+Vector((0,0,.39*sin(t*pi*.83)+.018*t))
            for j in range(6):tube(spine(j/6),spine((j+1)/6),.004*(1-j/9),vein,n=4)
            for j in range(8):
                t=(j+.5)/8;basept=spine(t);length=(.050+.089*sin(pi*t))*(1-.25*t)
                for s in [-1,1]:
                    tip=basept+s*side*length+e*.050+Vector((0,0,-.025))
                    mid=basept.lerp(tip,.46)+Vector((0,0,.013));p=mid-e*.026;q=mid+e*.026
                    face([basept,p,mid],leaves[2],[(.5,0),(0,.46),(.5,.46)],True)
                    face([p,tip,mid],leaves[2],[(0,.46),(.5,1),(.5,.46)],True)
                    face([basept,mid,q],leaves[2],[(.5,0),(.5,.46),(1,.46)],True)
                    face([mid,tip,q],leaves[2],[(.5,.46),(.5,1),(1,.46)],True)
            continue
        def point(t,u):
            width=wide*(max(.012,sin(t*pi))**.77)
            return start+e*(t*t*spread)+side*(u*width+.018*sin(t*pi*2+i)*t)+Vector((0,0,height*(t*.95-.48*t*t)+.10*sin(t*pi)-.24*abs(u)*width+.016*cos(t*9+i)*u))
        for j in range(6):
            for h in range(2):
                ts=[(j/6,h-1),(j/6,h),((j+1)/6,h),((j+1)/6,h-1)]
                face([point(t,u) for t,u in ts],leaves[(k+i//8)%3],[((u+1)/2,t) for t,u in ts],True)
    return finish('Botanical specimen '+str(k))
def bear():
    oval(0,0,.45,.286,.236,.365,fur,20,12);oval(0,-.028,.96,.31,.249,.285,fur,20,12)
    for s in (-1,1):
        oval(s*.24,-.018,1.17,.103,.067,.101,fur);oval(s*.24,-.074,1.178,.057,.017,.053,oat)
        oval(s*.292,-.01,.49,.094,.109,.203,fur);oval(s*.19,-.158,.14,.149,.148,.142,fur)
        oval(s*.19,-.288,.142,.090,.019,.083,oat)
        for i in range(3):oval(s*.19+(i-1)*.036,-.292,.199,.010,.008,.014,coal,8,5)
        oval(s*.107,-.249,.996,.027,.024,.030,coal);oval(s*.107-.007,-.27,1.005,.007,.005,.007,clay,8,5)
    oval(0,-.25,.899,.131,.066,.091,oat);oval(0,-.306,.922,.048,.022,.032,coal)
    tube((0,-.312,.911),(0,-.311,.882),.006,coal)
    for s in [-1,1]:tube((0,-.311,.882),(s*.04,-.30,.874),.005,coal)
    oval(0,-.01,.701,.223,.215,.048,teal)
    face([(-.11,-.216,.717),(.13,-.216,.719),(.048,-.243,.498)],teal)
    for i in range(6):tube((-.093+i*.026,-.223,.693),(-.078+i*.026,-.226,.684),.0025,oat,n=5)
    return finish('Heirloom stitched bear')
def toybox():
    # Small wood pull train on the freestanding store display; lathed wheels, axles & couplers.
    for j,(x,m) in enumerate([(-.48,teal),(0,rose),(.48,gold)]):
        box(x,0,.102,.397,.222,.070,wood)
        if j==0:
            box(x+.094,0,.217,.143,.195,.187,teal);box(x+.088,0,.322,.191,.241,.034,wood)
            tube((x-.149,0,.189),(x+.025,0,.189),.079,teal,n=16)
            tube((x-.11,0,.230),(x-.11,0,.324),.034,rose,.041)
        else:
            box(x,0,.168,.343,.187,.070,m)
            for s in [-1,1]:box(x,s*.092,.219,.35,.021,.111,m)
            for s in [-1,1]:box(x+s*.163,0,.219,.023,.19,.111,m)
        for d in [-.124,.124]:
            for s in [-1,1]:
                tube((x+d,s*.112,.073),(x+d,s*.142,.073),.066,wood,n=16)
                tube((x+d,s*.141,.073),(x+d,s*.149,.073),.022,teal,n=12)
        if j<2:tube((x+.201,0,.098),(x+.276,0,.098),.012,coal)
    return finish('Beech pull-along railway')
def computer(kind,w,h,keyboard=True):
    # Local X is to the right of the operator; negative Y is toward their seat.
    face([(-w/2,-.003,-h/2),(w/2,-.003,-h/2),(w/2,-.003,h/2),(-w/2,-.003,h/2)],lcd[kind],[(0,0),(1,0),(1,1),(0,1)])
    oval(0,-.005,h/2+.013,.010,.003,.009,coal,10,6)
    for i in range(13):box(-.15+i*.026,.076,.065,.013,.006,.037,plastic)
    box(0,.083,0,.07,.009,.014,alloy)
    return finish(kind+' | calibrated LCD and rear housing')
def peripherals(w,d):
    # The high-resolution key face includes bevels, row offsets and individual legends.
    face([(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0)],keys,[(0,0),(1,0),(1,1),(0,1)])
    box(w*.72,0,-.010,.122,.166,.005,teal)
    oval(w*.72,0,.012,.033,.052,.021,plastic);box(w*.72,0,.033,.004,.048,.002,coal)
    oval(w*.72,.014,.035,.004,.012,.004,alloy)
    path=[(-w*.28,d*.5,-.008),(-w*.28,d*.8,-.011),(-w*.35,d*1.06,-.012),(-w*.39,d*1.38,-.012)]
    for a,c in zip(path,path[1:]):tube(a,c,.0026,coal,n=5)
    return finish('Desktop | key legends, optical mouse and braided lead')
def detail(sc):
    global col
    col=b.data.collections.new('Studio | botanical and object detail');sc.collection.children.link(col);palette()
    originals=list(sc.objects)
    templates=[plant(i) for i in range(3)];teddy=bear()
    for i,o in enumerate(originals):
        if o.name.startswith('Potted foliage'):
            size=o.scale.x/.32;x,y,z=o.location
            repl=templates[i%3].copy();col.objects.link(repl);repl.name='Potted specimen '+o.name;repl.location=(x,y,z-.26*size);repl.scale=(size,)*3;repl.rotation_euler.z=i*2.4
            b.data.objects.remove(o,do_unlink=True)
        elif o.name.startswith('Seated teddy'):
            size=o.scale.x/.33;x,y,z=o.location
            repl=teddy.copy();col.objects.link(repl);repl.name='Stitched toy '+o.name;repl.location=(x,y,z-.48*size);repl.scale=(size,)*3
            b.data.objects.remove(o,do_unlink=True)
    for o in templates+[teddy]:b.data.objects.remove(o,do_unlink=True)
    # Use existing station geometry as the dimensional reference, including assembly offsets.
    for o in originals:
        try:n=o.name
        except ReferenceError:continue
        if n.startswith('Reception desk and workstation'):
            t=toybox();t.location=(4.65,6.12,.66);t.scale=(.72,)*3
            for j,(x,y,z) in enumerate([(3.17,6.36,.77),(3.407,6.36,.77),(3.286,6.36,.99)]):
                box(x,y,z,.219,.20,.216,wood)
                face([(x-.101,y-.101,z-.101),(x+.101,y-.101,z-.101),(x+.101,y-.101,z+.101),(x-.101,y-.101,z+.101)],abc,
                    [(j/3,0),((j+1)/3,0),((j+1)/3,1),(j/3,1)])
            finish('Handprinted nursery alphabet blocks')
            screen=computer('welcome',1.20,.62);screen.rotation_euler.z=pi;screen.location=(-4.52,-1.119,1.94)
            kb=peripherals(.61,.181);kb.location=(-4.53,-.86,1.574);kb.rotation_euler.z=pi
        elif n.startswith('Reception | keyboard'):
            for vtx in o.data.vertices:
                p=vtx.co
                if -4.90<p.x<-3.93 and p.y<-1.25:
                    p.x=-9.06-p.x;p.y=-2.30-p.y
        elif n.startswith('Computer workstations'):
            z=o.location.z
            for j in range(4):
                y=-.25+1.19*j
                screen=computer(['library','studio'][j%2],.655,.405);screen.location=(-7.617,y,1.36+z);screen.rotation_euler.z=pi/2
                kb=peripherals(.521,.210);kb.location=(-7.26,y,.942+z);kb.rotation_euler.z=pi/2
        elif n.startswith('Security reception and monitor'):
            z=o.location.z
            screen=computer('security',.90,.5);screen.rotation_euler.z=pi;screen.location=(-3.62,-4.60,1.82+z)
            box(0,0,-.007,.48,.175,.014,plastic);kb=peripherals(.47,.168);kb.rotation_euler.z=pi;kb.location=(-3.62,-4.40,1.525+z)
def bake(sc,level):
    # Resolve modifiers and transformations offline. Draw one primitive per material per zone.
    groups={}
    for o in list(sc.objects):
        if o.type not in ('MESH','FONT','CURVE') or o.name.startswith('Two glazed access lanes'):continue
        if o.type=='FONT':
            o.data.resolution_u=3
            if o.data.size<.65:o.data.extrude=0
        if o.type=='MESH' and any(t in o.name for t in ('Stocked maple shelves','Illustrated bear play rug','Lounge seating','Baby illustration','Flower arrangement')):
            mod=o.modifiers.new('Tour | simplify smooth silhouettes','DECIMATE');mod.ratio=.50
        suite=re.match(r'^([BG]\d\d) \| (.*)',o.name)
        if o.name.startswith('Locker leaf '):key='LockerFronts'
        elif level==3 and suite and not suite[2].startswith('room and sliding'):key='Suite_'+suite[1]+'_details'
        else:
            pos=sum((o.matrix_world@Vector(c) for c in o.bound_box),Vector())/8
            key='Fixed_'+('west' if pos.x<0 else 'east')+('_front' if pos.y<0 else '_back')
        groups.setdefault(key,[]).append(o)
    for key,objs in groups.items():
        b.ops.object.select_all(action='DESELECT')
        for o in objs:o.select_set(True)
        b.context.view_layer.objects.active=objs[0];b.ops.object.convert(target='MESH')
        b.ops.object.join();o=b.context.object;o.name=key
        b.ops.object.transform_apply(location=True,rotation=True,scale=True)
    b.ops.export_scene.gltf(filepath=os.path.join(out,f'Level_0{level}.glb'),export_cameras=False,export_lights=False,export_apply=False)
if __name__=='__main__':
    for level in [1,2,3]:
        b.ops.wm.open_mainfile(filepath=os.path.join(src,f'Level_0{level}.blend'));sc=b.context.scene;detail(sc);b.context.view_layer.update();bake(sc,level)
    b.ops.wm.open_mainfile(filepath=os.path.join(src,'Atrium_Residences.blend'));sc=b.context.scene;detail(sc)
    b.context.preferences.filepaths.save_version=0
    b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Studio.blend'))
