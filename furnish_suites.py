"""Build twenty furnished rest rooms, public-floor details and the assembled tour model."""
import bpy as b, math, os, re, struct, tempfile, zlib
from math import sin,cos,pi
from mathutils import Vector
import numpy as np

base=os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','Atrium')
out=os.path.join(base,'Furnished');os.makedirs(out,exist_ok=True)
sources=['Level_01.blend','Level_02.blend','Level_03.blend']
oldrooms=re.compile(r'^[BG](0[1-9]|10)( \| solo room)?(?:\.\d+)?$')
def strip_rooms(scene):
    old=[o for o in scene.objects if oldrooms.fullmatch(o.name)]
    assert len(old)==40, ('Unexpected room kit',len(old))
    for o in old:b.data.objects.remove(o,do_unlink=True)
def clear_thresholds(scene,base_z):
    for o in scene.objects:
        if o.name.startswith('Potted foliage') and abs(abs(o.location.x)-5.49)<.15 and abs(o.location.z-base_z)<.6:
            o.location.y+=.89
def png(name,rgb):
    a=np.uint8(np.clip(rgb,0,255));h,w,_=a.shape
    def chunk(k,x):return struct.pack('>I',len(x))+k+x+struct.pack('>I',zlib.crc32(k+x)&0xffffffff)
    blob=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+row.tobytes() for row in a),8))+chunk(b'IEND',b'')
    with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as f:f.write(blob);path=f.name
    im=b.data.images.load(path);im.name=name;im.pack();os.unlink(path);im.filepath='//'+name+'.png';return im
def rgb(hex):return np.array([int(hex[i:i+2],16) for i in (0,2,4)])
def mat(name,color,kind='',rough=.58,metal=0,emit=0):
    m=b.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    srgb=rgb(color)/255;col=tuple(np.where(srgb>.04045,((srgb+.055)/1.055)**2.4,srgb/12.92))+(1,)
    m.diffuse_color=col;p.inputs['Base Color'].default_value=col;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if emit:p.inputs['Emission Color'].default_value=col;p.inputs['Emission Strength'].default_value=emit
    if kind:
        y,x=np.mgrid[:256,:256];rng=np.random.default_rng(87);t=2*pi/256
        if kind=='timber':
            phase=y*t*17+.44*np.sin(x*t*2)+1.1*np.sin(x*t+y*t*2)
            v=.967+.032*np.sin(phase)+.029*np.sin(phase*3)+.018*np.sin(t*y*85)+rng.normal(0,.012,x.shape)
        else:
            v=.98+.034*np.sin(t*x*80)+.04*np.sin(t*y*70)+rng.normal(0,.018,x.shape)
            if kind=='stripe':v-=.20*((y%64<3)|((y+6)%64<2))
            p.inputs['Sheen Weight'].default_value=.27
        im=png(name,v[:,:,None]*rgb(color));node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
        m.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
        bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.0008
        m.node_tree.links.new(node.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m
def palette():
    global plaster,wood,dark,brass,cream,paper,ink,linen,throw,accents,glow,ceramic,leaf,slate
    plaster=mat('Chalk limewash','F1E6DA');wood=mat('Rift sawn ash','CBA881','timber');dark=mat('Oiled walnut','85654F','timber')
    brass=mat('Aged brass','B89B76',rough=.3,metal=.58);cream=mat('Warm enamel','E7E1D5')
    paper=mat('Paper stock','F4ECD9');ink=mat('Charcoal enamel','373B39');linen=mat('Cotton percale','F1ECE2','linen',.82)
    throw=[mat('Throw '+n,c,'stripe',.83) for n,c in [('clay','BE8F7F'),('eucalyptus','8D9E93'),('cornflower','8499AD'),('oat','C0AD90')]]
    accents=[mat('Woven '+n,c,'linen',.82) for n,c in [('terracotta','AC8173'),('olive','8F987B'),('slate','84969D'),('caramel','B49A79')]]
    glow=mat('Opal reading light','FFE2AB',emit=2.1);ceramic=mat('Glazed stoneware','C4D2C4',rough=.29);leaf=mat('Olive foliage','708563');slate=mat('Ink blue','465A63')
v=[];f=[];idx=[];slots=[];smooth=[]
def add(points,faces,m,soft=False):
    if m not in slots:slots.append(m)
    n=len(v);v.extend(points);f.extend(tuple(n+i for i in q) for q in faces);idx.extend([slots.index(m)]*len(faces));smooth.extend([soft]*len(faces))
def box(x,y,z,w,d,h,m):
    add([(x+i*w/2,y+j*d/2,z+k*h/2) for k in (-1,1) for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]],
        [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
def cyl(x,y,z,r,h,m,rt=None,N=20):
    add([(x+rr*cos(i*2*pi/N),y+rr*sin(i*2*pi/N),z+k*h*.5) for k,rr in [(-1,r),(1,rt if rt is not None else r)] for i in range(N)],
        [tuple(reversed(range(N))),tuple(range(N,N*2))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)],m)
def finish(name,bevel=0):
    if not v:return
    me=b.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
    for m in slots:me.materials.append(m)
    me.polygons.foreach_set('material_index',idx);me.polygons.foreach_set('use_smooth',smooth)
    uv=me.uv_layers.new(name='Metre weave')
    for face in me.polygons:
        axis=max(range(3),key=lambda i:abs(face.normal[i]))
        for j in face.loop_indices:
            p=me.vertices[me.loops[j].vertex_index].co
            uv.data[j].uv=((p.y if axis==0 else p.x)*1.8,(p.y if axis==2 else p.z)*1.8)
    o=b.data.objects.new(name,me);col.objects.link(o);o.location=(ox,oy,0);o.scale.x=sign
    if bevel:
        mod=o.modifiers.new('Edge radius','BEVEL');mod.width=bevel;mod.segments=3;mod.harden_normals=True
        mod=o.modifiers.new('Weighted corners','WEIGHTED_NORMAL')
    for a in (v,f,idx,slots,smooth):a.clear()
    return o
def lettering(s,x,y,z,size,m,angle=0):
    c=b.data.curves.new(s,'FONT');c.body=s;c.align_x='CENTER';c.align_y='CENTER';c.font=font;c.size=size;c.extrude=.0006;c.materials.append(m)
    o=b.data.objects.new(s,c);col.objects.link(o);o.location=(ox+sign*x,oy+y,z);o.rotation_euler=(pi/2,0,angle)
def cloth(x0,x1,y0,y1,z,thickness,m,style,seed):
    # Soft crown, pinched pillow ends, hem droop and wrinkles concentrated at the edges.
    nx,ny=26,16;pts=[];faces=[]
    for j in range(ny+1):
        t=j/ny
        for i in range(nx+1):
            s=i/nx;xx=x0+(x1-x0)*s;yy=y0+(y1-y0)*t
            ed=min(s,1-s,t,1-t);crown=max(0,sin(pi*s)*sin(pi*t))
            h=z+thickness*crown**.47
            if style=='pillow':
                xx+=.024*sin(2*pi*s)*(1-sin(pi*t));yy+=.021*sin(2*pi*t)*(1-sin(pi*s))
                h+=.012*cos(25*s+seed)*sin(pi*t)**2
            else:
                h+=.009*sin(24*s+4*sin(t*4)+seed)+.007*cos(33*t+s*4+seed)*math.exp(-ed*8)
                if style=='duvet':h-=.042*math.exp(-ed*27);yy+=.012*sin(19*s+seed)*(2*t-1)**6
            pts.append((xx,yy,h))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
    rim=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    baseidx=len(pts)
    for a in rim:
        x,y,h=pts[a];pts.append((x,y,h-(.045 if style=='pillow' else .020)))
    for i,a in enumerate(rim):
        j=(i+1)%len(rim);faces.append((a,baseidx+i,baseidx+j,rim[j]))
    faces.append(tuple(reversed(range(baseidx,len(pts)))));add(pts,faces,m,True)
def book(x,y,z,w,d,h,m):
    box(x,y,z,w-.009,d-.008,h,paper)
    for k in (-1,1):box(x,y,z+k*h/2,w,d,.004,m)
    box(x,y-d/2,z,w,.007,h,m)
def mug(x,y,z,m):
    cyl(x,y,z+.042,.038,.084,m,.042);cyl(x,y,z+.085,.033,.002,dark)
    for k in (-1,1):box(x+.047,y,z+.045+k*.023,.025,.012,.009,m)
    box(x+.059,y,z+.045,.009,.012,.054,m)
def room(num,code,D,j,row):
    a=accents[(j+row+(2 if code=='B' else 0))%4];t=throw[(j+row+(2 if code=='B' else 0))%4]
    # Shared room partitions; a clear 90 cm opening and an exposed sliding track on the corridor side.
    if row==0:box(0,0,1.46,.07,1.85,2.92,plaster)
    box(D/2,-.925,1.46,D,.065,2.92,plaster)
    if j==4:box(D/2,.925,1.46,D,.065,2.92,plaster)
    for y,d in [(-.87,.11),(.52,.81)]:box(D,y,1.46,.083,d,2.92,plaster)
    box(D,-.35,2.60,.083,.94,.64,plaster)
    box(D/2,-.879,.068,D-.08,.018,.102,wood)
    box(D/2,.879,.068,D-.08,.018,.102,wood)
    box(D+.054,.493,1.10,.045,.85,2.20,wood)
    box(D+.086,.43,1.04,.021,.032,.175,brass)
    box(D+.085,-.01,2.27,.075,1.78,.043,dark)
    box(D+.097,.505,1.66,.03,.46,.24,slate)
    lettering(num,D+.119,.505,1.66,.13,paper,sign*pi/2)
    finish(num+' | room and sliding door',.006)
    # Plinth bed with ventilated shadow gap and drawer fronts.
    box(1.12,.387,.143,1.78,.66,.23,dark);box(1.115,.387,.286,1.98,.905,.20,wood)
    for x in [.65,1.56]:
        box(x,-.072,.278,.85,.020,.145,wood);box(x,-.087,.293,.18,.013,.023,brass)
    box(.103,.39,.68,.09,.98,1.04,wood)
    for k in range(5):box(.167,.018+k*.185,.785,.073,.181,.66,a)
    finish(num+' | storage bed and channel headboard',.018)
    box(1.115,.389,.466,1.945,.874,.205,linen);finish(num+' | sprung mattress',.041)
    cloth(.205,.665,.049,.731,.606,.113,linen,'pillow',j)
    cloth(.625,2.10,-.071,.850,.597,.054,linen,'duvet',j+.4)
    cloth(.645,.806,-.074,.852,.636,.021,linen,'turnback',j+.4)
    cloth(1.54,1.96,-.09,.854,.658,.020,t,'throw',j)
    finish(num+' | pillow, duvet and woven throw')
    # A compact writing ledge and tucked stool keep the passage alongside the bed clear.
    box(.51,-.711,.79,.86,.325,.046,wood)
    for x in [.21,.79]:box(x,-.786,.689,.035,.185,.155,brass)
    cyl(.51,-.65,.425,.148,.071,a)
    for dx,dy in [(-.10,-.07),(.10,-.07),(0,.106)]:cyl(.51+dx,-.65+dy,.215,.021,.37,dark)
    book(.38,-.72,.835,.195,.145,.028,slate);mug(.76,-.71,.814,ceramic)
    box(.39,-.867,1.05,.19,.025,.087,cream)
    for x in [.34,.43]:box(x,-.848,1.05,.024,.009,.022,ink)
    box(.066,-.10,1.30,.08,.14,.17,brass);box(.177,-.10,1.33,.18,.025,.029,brass)
    cyl(.248,-.10,1.29,.088,.108,brass,.068);cyl(.248,-.10,1.232,.075,.009,glow)
    finish(num+' | desk, reading sconce and personal effects',.003)
    # Moulded picture frame with a layered landscape print on the bedside wall.
    box(1.12,.878,1.61,.66,.043,.50,dark);box(1.12,.85,1.61,.615,.012,.456,paper)
    poly=[(.855,.839,1.44),(1.39,.839,1.44),(1.39,.839,1.58),(1.30,.839,1.65),(1.16,.839,1.55),(1.04,.839,1.69)]
    add(poly,[tuple(range(len(poly)))],a)
    pts=[(1.25+.043*cos(i*pi/12),.837,1.72+.043*sin(i*pi/12)) for i in range(24)]
    add(pts,[tuple(range(24))],dark)
    add([(.855,.835,1.44),(1.39,.835,1.44),(1.39,.835,1.49),(1.31,.835,1.52),(1.20,.835,1.49),(1.04,.835,1.58),(.855,.835,1.49)],[(0,1,2,3,4,5,6)],slate)
    box(.09,-.645,1.83,.135,.42,.032,wood)
    for k,m in enumerate([a,slate,cream]):box(.105,-.76+k*.063,1.94,.108,.045,.18+k*.012,m)
    finish(num+' | bedside print and bookshelf')

def public(level):
    if level==1:
        box(-4.53,-1.44,1.548,.62,.185,.022,ink)
        for i in range(13):
            for j in range(4):box(-4.80+i*.044,-1.51+j*.041,1.564,.035,.030,.010,slate)
        box(-4.04,-1.41,1.548,.087,.125,.024,ink)
        for i in range(3):book(-5.37,-1.13,1.55+.026*i,.32,.225,.020,accents[i])
        box(-5.61,-1.42,1.627,.38,.032,.16,cream);lettering('WELCOME',-5.61,-1.44,1.63,.055,ink)
        finish('Reception | keyboard, mouse, welcome card and brochures',.002)
    else:
        for j in range(5):
            x=-7.25+j*.95
            for k in range(3):box(x+.008*k,5.956-.008*k,1.223+k*.005,.27,.18,.003,paper)
        finish('Print counter | fresh output')
        for x,y in [(4.17,4),(6.63,1.35),(4.17,-1.34),(4.47,-3.88)]:
            cyl(x-.38,y,.868,.105,.014,wood);mug(x-.38,y,.877,cream)
            box(x+.30,y-.12,.865,.18,.12,.012,linen)
            box(x+.31,y-.12,.875,.012,.12,.006,brass)
        finish('Cafe | cups, oak saucers and napkins',.002)

b.context.preferences.filepaths.save_version=0
for l in [1,2,3]:
    b.ops.wm.open_mainfile(filepath=os.path.join(base,sources[l-1]))
    sc=b.context.scene
    if l==2:
        # Same chair tuck as the finished building's existing walkable cafe.
        for o in sc.objects:
            if not o.name.startswith('Cafe tables and chairs'):continue
            for i in range(0,len(o.data.vertices),8):
                chunk=list(o.data.vertices[i:i+8]);c=sum((v.co for v in chunk),Vector())/8
                if c.y>=-3:
                    cx=min([4.17,6.63],key=lambda x:abs(c.x-x))
                    if abs(c.x-cx)>.72:
                        for vtx in chunk:vtx.co.x-=math.copysign(.23,c.x-cx)
    col=b.data.collections.new('Furnished edition '+str(l));sc.collection.children.link(col);palette()
    font=b.data.fonts.load('C:/Windows/Fonts/arialbd.ttf',check_existing=True)
    ox=oy=0;sign=1
    if l<3:public(l)
    else:
        strip_rooms(sc)
        clear_thresholds(sc,0)
        for s,code in [(-1,'G'),(1,'B')]:
            for row in [0,1]:
                ox=s*(1.95 if row==0 else 8);sign=s if row==0 else -s
                for j in range(5):
                    oy=-2.25+(j+.5)*1.85;room(f'{code}{1+5*row+j:02d}',code,2.19 if row==0 else 2.25,j,row)
    b.ops.wm.save_as_mainfile(filepath=os.path.join(out,f'Level_0{l}.blend'))
    b.ops.export_scene.gltf(filepath=os.path.join(out,f'Level_0{l}.glb'),export_apply=True,export_cameras=False,export_lights=False)
b.ops.wm.open_mainfile(filepath=os.path.join(base,'Atrium_Finished.blend'));sc=b.context.scene;strip_rooms(sc);clear_thresholds(sc,7.92)
for l in [1,2,3]:
    with b.data.libraries.load(os.path.join(out,f'Level_0{l}.blend')) as (src,dst):dst.collections=[f'Furnished edition {l}']
    col=dst.collections[0];sc.collection.children.link(col)
    for o in col.objects:o.location.z+=3.96*(l-1)
# Local lights and an eye-level camera for a photograph inside the first outer suite.
col=b.data.collections.new('Bedroom ceilings | toggle for cutaway');sc.collection.children.link(col)
ox=oy=0;sign=1;lidMat=mat('Warm ceiling plaster','F5EEE3');downlight=mat('Recessed downlight','FFEACC',emit=2)
for s in [-1,1]:
    for row in [0,1]:
        cx=s*(6.875 if row else 3.045)
        box(cx,2.375,10.876,2.25 if row else 2.19,9.25,.07,lidMat)
        for j in range(5):
            y=-2.25+(j+.5)*1.85;x=s*(2.75 if row==0 else 7.21)
            cyl(cx,y-.37,10.835,.086,.014,downlight)
            data=b.data.lights.new('Suite ambient','AREA');data.energy=38;data.size=.94;data.color=(1,.89,.76)
            o=b.data.objects.new('Suite ambient',data);sc.collection.objects.link(o);o.location=(x,y,10.62)
            data=b.data.lights.new('Bedside pool','POINT');data.energy=3;data.shadow_soft_size=.07;data.color=(1,.75,.48)
            o=b.data.objects.new('Bedside pool',data);sc.collection.objects.link(o);o.location=(s*(2.20 if row==0 else 7.75),y-.10,9.11)
finish('Rest wings | removable ceilings and reading downlights');col.hide_viewport=True;col.hide_render=True
cam=b.data.cameras.new('Suite G06 | doorway');cam.lens=17;cam.clip_start=.025
o=b.data.objects.new(cam.name,cam);sc.collection.objects.link(o);o.location=(-5.86,-1.98,9.27)
o.rotation_euler=(Vector((-7.16,-.99,8.79))-o.location).to_track_quat('-Z','Y').to_euler()
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Residences.blend'))
col.hide_render=False
sc.camera=o;sc.render.engine='CYCLES';sc.cycles.samples=18;sc.cycles.use_denoising=True
sc.render.resolution_x=1250;sc.render.resolution_y=860;sc.render.resolution_percentage=100
sc.render.filepath=os.path.join(out,'Suite_G06.png');b.ops.render.render(write_still=True)
