"""Blender background script: create level two and assemble the two-level building."""
import bpy as b, math, os, random
from mathutils import Vector, Matrix
from math import pi, sin, cos
root=os.path.dirname(os.path.abspath(__file__))
models=os.path.join(root,'models')
first=os.path.join(models,'Reference_First_Floor.blend')
b.ops.wm.read_factory_settings(use_empty=True)
sc=b.context.scene
random.seed(72)
def mat(name,h,emit=False):
    m=b.data.materials.new(name)
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    m.diffuse_color=tuple(((c+.055)/1.055)**2.4 if c>.04045 else c/12.92 for c in rgb)+(1,)
    m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color
    if emit:p.inputs['Emission Color'].default_value=m.diffuse_color;p.inputs['Emission Strength'].default_value=2
    return m
oak=mat('Honey oak','CC945D');maple=mat('Maple tops','E7B881');grain=mat('Fluted oak','AA764B')
cream=mat('Warm plaster','F6DFCA');chalk=mat('Ivory','FCF2E6');seat=mat('Oat upholstery','DBC5AB')
ink=mat('Graphite','28292B');screen=mat('Display glass','39495A');steel=mat('Bronze frames','6D594A')
led=mat('Warm lighting','FFE9AD',True);water=mat('Water blue','719DC7');tile=mat('Sand tile','EAD3BB');joint=mat('Grout','CDB399')
palette=[mat('Spine '+str(i),h) for i,h in enumerate(['C97765','637C95','9EA877','EDC36B','F2EEE2','96775F'])]
verts=[];faces=[];slots=[];indices=[]
def geom(v,f,m):
    if m not in slots:slots.append(m)
    off=len(verts);verts.extend(v);faces.extend([tuple(off+i for i in q) for q in f]);indices.extend([slots.index(m)]*len(f))
def box(x,y,z,w,d,h,m,a=0):
    v=[]
    for k in (-1,1):
        for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            u=i*w/2;t=j*d/2;v.append((x+u*cos(a)-t*sin(a),y+u*sin(a)+t*cos(a),z+k*h/2))
    geom(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
def cyl(x,y,z,r,h,m,rt=None):
    n=16;r2=r if rt is None else rt
    v=[(x+rad*cos(2*pi*i/n),y+rad*sin(2*pi*i/n),z+k*h/2) for k,rad in [(-1,r),(1,r2)] for i in range(n)]
    geom(v,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
def done(name):
    me=b.data.meshes.new(name);me.from_pydata(verts,[],faces)
    for m in slots:me.materials.append(m)
    me.polygons.foreach_set('material_index',indices);me.update()
    ob=b.data.objects.new(name,me);sc.collection.objects.link(ob)
    for v in (verts,faces,slots,indices):v.clear()
    return ob
font=b.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
def label(body,x,y,z,size,angle=0):
    c=b.data.curves.new(body,'FONT');c.body=body;c.font=font;c.align_x='CENTER';c.align_y='CENTER';c.size=size;c.space_line=.85;c.extrude=.004;c.materials.append(ink)
    ob=b.data.objects.new(body,c);sc.collection.objects.link(ob);ob.location=(x,y,z);ob.rotation_euler=(pi/2,0,angle)
with b.data.libraries.load(first) as (src,dst):
    dst.objects=['Potted foliage','Lounge seating and coffee table']
plant_src,lounge=dst.objects
# The pot was modeled at scale .66. Reuse the mesh with its source transform.
sc.collection.objects.link(plant_src)
b.context.view_layer.update()
plant_matrix=plant_src.matrix_world.copy()
sc.collection.objects.unlink(plant_src)
def plant(x,y,z,s):
    ob=plant_src.copy();sc.collection.objects.link(ob)
    ob.matrix_world=Matrix.Translation((x,y,z)) @ Matrix.Scale(s/.66,4) @ Matrix.Translation((6.41,1.1,-1.54)) @ plant_matrix
sc.collection.objects.link(lounge)
lounge.location.x-=.55;lounge.location.y-=.48
plant(-4.65,-5.48,.91,.48)
box(0,0,-.105,16.42,14.4,.21,joint)
for i in range(16):
    for j in range(14):box(i-7.5,j-6.5,.006,.991,.991,.012,tile)
for x,y,w,d in [(0,7.07,16.4,.2),(-8.1,0,.2,14.3),(8.1,0,.2,14.3)]:
    box(x,y,1.85,w,d,3.7,cream);box(x,y,3.71,w+.04,d+.04,.075,ink)
for x in [-4.72,4.72]:
    box(x,-7.05,.54,6.64,.18,1.08,oak);box(x,-7.05,1.1,6.64,.19,.07,ink)
for x in [-1.39,0,1.39]:box(x,-7.05,1.12,.065,.11,2.24,ink)
box(0,-7.05,2.24,2.84,.12,.08,ink)
for x in [-.13,.13]:box(x,-7.07,1.09,.045,.09,.51,ink)
done('Second floor slab, walls and entry')
for i in range(134):
    box(-7.93+i*.119,6.93,1.85,.078,.09,3.64,oak)
for x,w,title in [(-5.38,4.66,'PRINTING'),(-.49,4.42,'STUDY\nAREA'),(5.15,4.73,'EATING\nAREA')]:
    box(x,6.82,2.45,w,.12,1.33,cream)
    for z in (1.77,3.13):box(x,6.8,z,w,.14,.035,led)
    label(title,x+.35,6.746,2.45,.49)
# Outline glyphs beside the three zone signs.
def stroke(x,z,u,t,r=.035):
    dx=u-x;dz=t-z;v=Vector((dx,0,dz));mid=((x+u)/2,6.738,(z+t)/2)
    # Rectangular strokes in the wall plane.
    L=v.length;nx=-dz/L*r/2;nz=dx/L*r/2
    geom([(a,mid[1],h) for a,h in [(x+nx,z+nz),(x-nx,z-nz),(u-nx,t-nz),(u+nx,t+nz)]],[(0,1,2,3)],ink)
def outline(points):
    for a,c in zip(points,points[1:]):stroke(*a,*c)
outline([(-7.04,2.34),(-7.11,2.34),(-7.11,2.58),(-6.58,2.58),(-6.58,2.34),(-6.65,2.34)])
for z,h in [(2.58,.13),(2.23,.19)]:outline([(-7.01,z),(-7.01,z+h),(-6.69,z+h),(-6.69,z),(-7.01,z)])
for s in (-1,1):
    x=-1.89;outline([(x,2.19),(x+s*.33,2.27),(x+s*.33,2.69),(x,2.61),(x,2.19)])
    for j in range(3):stroke(x+s*.05,2.32+j*.08,x+s*.26,2.37+j*.08,.017)
for x in (3.65,3.93):stroke(x,2.17,x,2.59,.055)
for i in range(3):stroke(3.58+i*.068,2.51,3.58+i*.068,2.73)
stroke(3.58,2.51,3.72,2.51);stroke(3.93,2.54,3.93,2.69,.11)
done('Slatted wall and illuminated pictogram signs')
def cabinet(x,w):
    box(x,6.35,.48,w,.95,.9,oak);box(x,6.35,.96,w+.04,1,.08,maple);box(x,5.87,.11,w,.02,.035,led)
    for i in range(1,int(w/.52)):box(x-w/2+i*.52,5.871,.52,.009,.012,.74,grain)
cabinet(-5.35,4.83)
for i in range(5):
    x=-7.25+i*.95;m=ink if i in (0,3) else chalk
    box(x,6.32,1.23,.77,.65,.47,m);box(x,6.32,1.49,.79,.67,.065,ink);box(x,6.37,1.54,.55,.41,.045,steel)
    box(x,5.989,1.3,.64,.018,.115,ink);box(x,5.96,1.2,.52,.13,.035,chalk)
    for z in (1.08,1.13):box(x,5.986,z,.56,.012,.012,steel)
    box(x+.24,6,1.46,.15,.08,.02,water)
done('Five multifunction printers and cabinetry')
def table(x,y,w,d,h=.82):
    box(x,y,h,w,d,.075,maple)
    for i in (-1,1):
        for j in (-1,1):box(x+i*(w/2-.09),y+j*(d/2-.09),h/2,.043,.043,h,steel)
def chair(x,y,a=0,m=seat):
    def part(dx,dy,z,w,d,h,mt):
        box(x+dx*cos(a)-dy*sin(a),y+dx*sin(a)+dy*cos(a),z,w,d,h,mt,a)
    part(0,0,.46,.46,.46,.09,m);part(0,.213,.72,.45,.065,.46,m)
    for i in (-1,1):
        for j in (-1,1):part(i*.175,j*.16,.225,.028,.033,.45,steel)
table(-.35,6.38,5.06,.82)
for j in range(7):
    x=-2.52+j*.72;chair(x,5.73,pi);plant(x,6.57,.86,.245)
done('Window study bar and seven stools')
for x in [-4.4,-.49,2.02]:
    for j in range(7):
        y=4.29-j*1.09;w=.76 if x>1 else 1.37
        table(x,y,w,1.04);chair(x-w/2-.28,y,pi/2)
        if x<1:chair(x+w/2+.28,y,-pi/2)
        box(x,y,1.05,.025,.94,.4,oak)
        plant(x+.11,y+.32,.86,.22)
    done('Study carrels')
# Wall-facing computers with keyboards and dark swivel chairs.
box(-7.41,1.64,.86,.95,5.16,.1,maple)
for y in [-.87,4.15]:box(-7.41,y,.43,.93,.08,.86,oak)
for j in range(4):
    y=-.25+j*1.19;box(-7.67,y,1.36,.066,.74,.49,ink);box(-7.629,y,1.36,.019,.67,.42,screen)
    box(-7.67,y,1.03,.085,.09,.25,ink);box(-7.26,y,.925,.22,.53,.028,ink);chair(-6.65,y,-pi/2,ink)
done('Computer workstations')
for z in [.09,.64,1.2]:box(-5.58,-3.39,z,4.54,.53,.075,maple)
for x in [-7.83,-6.31,-4.81,-3.33]:box(x,-3.39,.63,.065,.53,1.2,oak)
for j in range(2):
    for i in range(52):
        h=random.uniform(.32,.46);x=-7.72+i*.083
        box(x,-3.39,.135+j*.55+h/2,.063,.31,h,random.choice(palette))
done('Double-tier library shelf')
box(2.69,.29,.55,.28,11.93,1.07,oak)
for i in range(86):
    y=-5.61+i*.138;box(2.846,y,.55,.04,.077,1.06,maple)
for i in range(25):plant(2.69,-5.41+i*.46,1.09,.34)
done('Fluted planter partition')
cabinet(3.64,1.2);cabinet(5.9,1.73)
box(3.65,6.32,1.29,.97,.62,.56,chalk);box(3.57,6,1.29,.67,.018,.39,ink);box(4.05,5.99,1.31,.065,.045,.24,steel)
box(4.63,6.32,.66,.49,.62,1.31,chalk);box(4.63,6,.93,.34,.018,.31,screen);cyl(4.63,6.32,1.58,.205,.53,water)
for i in range(3):
    x=5.67+i*.33;cyl(x,6.31,1.21,.112,.41,palette[i]);cyl(x,6.31,1.425,.118,.035,steel)
box(7.33,6.34,1.3,.98,.9,2.6,ink);box(7.33,5.88,1.35,.84,.05,2.13,screen)
for j in range(4):
    z=.42+j*.49;box(7.33,5.84,z,.83,.07,.035,chalk)
    for i in range(5):
        x=7.02+i*.153;cyl(x,5.8,z+.17,.051,.29,palette[(i+j)%6]);cyl(x,5.8,z+.331,.034,.038,chalk)
done('Refreshment counter, microwave, water cooler and drinks refrigerator')
for y in [4,1.35,-1.34,-4.5]:
    for x in ([5.5] if y<-4 else [4.17,6.63]):
        table(x,y,1.4,.93)
        for dx,dy,a in [(0,-.7,pi),(0,.7,0),(-.92,0,pi/2),(.92,0,-pi/2)]:chair(x+dx,y+dy,a)
        plant(x,y,.86,.3)
    done('Cafe tables and chairs')
for x,y,s in [(-7.54,-5.85,1.13),(7.46,-5.96,1.17),(3.16,-5.98,.91),(-2.83,6.26,.96),(2.69,6.41,1.47),(-7.58,-2.35,.85)]:plant(x,y,0,s)
for x,y,t,a in [(-7.96,2.3,'DREAM\nSTUDY\nCREATE',pi/2),(7.96,1.7,'GOOD\nFOOD\nGOOD\nMOOD',-pi/2)]:
    box(x,y,2.22,.05,1.54,1.72,oak);box(x+(.04 if x<0 else -.04),y,2.22,.04,1.44,1.61,chalk)
    label(t,x+(.07 if x<0 else -.07),y,2.22,.28,a)
done('Framed wall typography')
second=b.data.collections.new('02 | Print, study and dining');sc.collection.children.link(second)
for o in list(sc.objects):second.objects.link(o);sc.collection.objects.unlink(o)
b.ops.object.camera_add(location=(0,-20.6,16.7));cam=b.context.object;cam.rotation_euler=(Vector((0,-.47,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=39;sc.camera=cam
for pos,power,size in [((-5,-7,14),2550,9),((6,3,11),1900,8)]:
    b.ops.object.light_add(type='AREA',location=pos);o=b.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
sc.world=b.data.worlds.new('Daylight');sc.world.color=(.52,.49,.46)
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.use_denoising=True
sc.render.resolution_x=1200;sc.render.resolution_y=800;sc.render.resolution_percentage=100
for a in b.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.color_type='MATERIAL'
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(models,'Reference_Second_Floor.blend'))
b.ops.export_scene.gltf(filepath=os.path.join(models,'reference_second_floor.glb'),export_cameras=False,export_lights=False)
sc.render.film_transparent=False
box(0,0,-.32,70,70,.2,mat('Preview pavement','ADAAAB'));ground=done('Preview ground')
sc.render.filepath=os.path.join(root,'second_floor_preview.png');b.ops.render.render(write_still=True)
b.data.objects.remove(ground,do_unlink=True)
for o in second.objects:o.location.z+=3.96
base=b.data.collections.new('01 | Store and nursery');sc.collection.children.link(base)
with b.data.libraries.load(first) as (src,dst):
    dst.objects=[n for n in src.objects if n not in ('Camera','Area','Area.001')]
for o in dst.objects:
    if o and o.type in ('MESH','FONT'):base.objects.link(o)
cam.location=(15,-25,19);cam.rotation_euler=(Vector((0,0,3.7))-cam.location).to_track_quat('-Z','Y').to_euler()
b.ops.wm.save_as_mainfile(filepath=os.path.join(models,'Reference_Building.blend'))
