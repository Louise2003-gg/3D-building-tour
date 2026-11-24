"""Adapt the three furnished floors around a shared lift, then assemble and render."""
import bpy as b, bmesh, os, math
from mathutils import Vector
from math import pi

root=os.path.dirname(os.path.abspath(__file__))
out=os.path.join(root,'models','Atrium')
os.makedirs(out,exist_ok=True)
names=['First','Second','Third']
titles=['STORE + NURSERY','PRINT / STUDY / DINE','STUDENT SUPPORT']
step=3.96
def paint(name,h,metal=0,alpha=1,glow=0):
    m=b.data.materials.new(name);m.use_nodes=True
    c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    col=tuple(((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in c)+(alpha,)
    p=m.node_tree.nodes.get('Principled BSDF')
    for k,v in [('Base Color',col),('Metallic',metal),('Roughness',.32),('Alpha',alpha),('Emission Color',col),('Emission Strength',glow)]:p.inputs[k].default_value=v
    m.diffuse_color=col;return m
def block(x,y,z,w,d,h,m):
    off=len(vs)
    vs.extend([(x+a*w/2,y+b*d/2,z+c*h/2) for c in (-1,1) for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]])
    fs.extend(tuple(off+j for j in face) for face in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    if m not in mats:mats.append(m)
    ids.extend([mats.index(m)]*6)
def flush(name):
    me=b.data.meshes.new(name);me.from_pydata(vs,[],fs)
    for m in mats:me.materials.append(m)
    me.polygons.foreach_set('material_index',ids);me.update()
    obj=b.data.objects.new(name,me);level.objects.link(obj)
    for a in [vs,fs,ids,mats]:a.clear()
def label(s,x,y,z,size,m,angle=0):
    c=b.data.curves.new(s,'FONT');c.body=s;c.align_x='CENTER';c.align_y='CENTER';c.font=font;c.size=size;c.space_line=.89;c.extrude=.0015;c.materials.append(m)
    o=b.data.objects.new(s,c);level.objects.link(o);o.location=(x,y,z);o.rotation_euler=(pi/2,0,angle)
def remove_boxes(obj,rule):
    """Source shell mesh consists of independent eight-vertex rectangular solids."""
    bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table()
    assert len(bm.verts)%8==0
    drop=[]
    for i in range(0,len(bm.verts),8):
        chunk=[bm.verts[i+j] for j in range(8)];c=sum((v.co for v in chunk),Vector())/8
        if rule(*c):drop.extend(chunk)
    bmesh.ops.delete(bm,geom=drop,context='VERTS');bm.to_mesh(obj.data);bm.free()
def camera(sc,position,target,lens):
    o=sc.camera;o.location=position;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
def render(sc,name):
    sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True
    sc.render.resolution_x=1200;sc.render.resolution_y=850;sc.render.resolution_percentage=100
    sc.render.filepath=os.path.join(out,name+'.png');b.ops.render.render(write_still=True)
for i,n in enumerate(names):
    b.ops.wm.open_mainfile(filepath=os.path.join(root,'models','Reference_'+n+'_Floor.blend'))
    sc=b.context.scene;sc.frame_set(1);b.context.view_layer.update()
    level=b.data.collections.new('Atrium '+str(i+1)+' | '+titles[i]);sc.collection.children.link(level)
    furnished=[o for o in sc.objects if o.type in ('MESH','FONT','CURVE')]
    for o in furnished:
        for col in list(o.users_collection):col.objects.unlink(o)
        level.objects.link(o)
    vs=[];fs=[];ids=[];mats=[]
    font=b.data.fonts.load('C:/Windows/Fonts/arialbd.ttf',check_existing=True)
    stone=paint('Limestone / sand','EADACC');oak=paint('Smoked maple','B98B65');reed=paint('Oak batten','D9AE81')
    bronze=paint('Satin champagne','BCA789',.54);iron=paint('Deep bronze','42403B',.46);glaze=paint('Balustrade glass','B3D2C8',.05,.16)
    teal=paint('Atrium petrol','315954');light=paint('Opal lettering','F8EDD8',0,1,.28);led=paint('Concealed amber','FFDB99',0,1,2)
    def relocate(prefix,x,y,dx,dy):
        for o in furnished:
            if not o.name.startswith(prefix):continue
            if prefix.startswith('Potted'):
                p=o.matrix_world.translation
            else:
                p=sum((o.matrix_world@Vector(c) for c in o.bound_box),Vector())/8
            if abs(p.x-x)<.35 and abs(p.y-y)<.35:o.location.x+=dx;o.location.y+=dy
    if i==0:
        relocate('Stocked',5.71,-5.69,-1.8,2.25)
        relocate('Potted',7.28,-5.57,-1.60,2.22)
    else:
        shell=next(o for o in furnished if o.name.startswith(('Second floor slab','Tiled third-floor slab')))
        # Cut a 2 x 2 shaft through the tiled slab, and remove the level-two street entrance.
        remove_boxes(shell,lambda x,y,z:abs(z+.105)<.001 or (z<.02 and x>6 and y<-5) or (i==1 and abs(y+7.05)<.04 and z>.02))
        for x0,x1,y0,y1 in [(-8.21,6,-7.2,7.2),(6,8,-5,7.2),(6,8,-7.2,-7),(8,8.21,-7.2,7.2)]:
            block((x0+x1)/2,(y0+y1)/2,-.105,x1-x0,y1-y0,.21,stone)
        flush('Floor plate | lift well opening')
        # Replace the upper street frontage with a continuous glazed guard.
        for a in range(7):
            x=-7.02+a*1.98
            block(x,-7.07,.65,1.952,.029,.91,glaze)
            block(x-.985,-7.07,.65,.031,.057,.99,bronze)
        block(-1.08,-7.07,1.13,13.87,.062,.046,bronze)
        block(-1.08,-7.07,.15,13.87,.12,.18,stone)
        flush('Gallery frontage | glazed parapet')
    if i==1:
        relocate('Cafe tables',5.5,-4.5,-1.03,.62)
        relocate('Potted',5.5,-4.5,-1.03,.62)
        relocate('Potted',7.46,-5.96,-.15,2.34)
    if i==2:
        board=b.data.objects.get('Facility directory and lobby cameras')
        for v in board.data.vertices:
            if v.co.z<2.1:v.co.x+=1.02;v.co.y+=1.10
        for o in furnished:
            if o.type=='FONT' and o.location.x>4 and abs(o.location.y+5.38)<.02:o.location.x+=1.02;o.location.y+=1.10
        for x,w in [(4.02,3.03),(6.73,2.42)]:
            block(x,-4.42,.66,w,.035,1.2,glaze);block(x,-4.42,1.28,w,.046,.035,bronze)
        for x in [2.57,4.1,5.56,7.92]:block(x,-4.42,.66,.045,.055,1.28,bronze)
        flush('Security lobby | glazed return to access gates')
    # All landings share exactly the same well. The car is parked only at level one.
    block(8.03,-6,1.88,.085,2.18,4.16,stone)
    block(7,-4.957,1.88,2.11,.086,4.16,stone)
    block(7,-7.043,1.88,2.11,.086,4.16,oak)
    if i==2:block(7,-6,3.985,2.17,2.18,.085,stone)
    for y in [-6.86,-5.14]:block(5.962,y,1.88,.095,.36,4.16,stone)
    block(5.962,-6,3.22,.095,1.39,1.48,stone)
    for sign in (-1,1):
        block(5.919,-6+sign*.69,1.25,.092,.067,2.50,bronze)
        block(6.008,-6+sign*.325,1.22,.06,.64,2.43,bronze)
        block(5.972,-6+sign*.022,1.22,.018,.013,2.42,iron)
    block(5.919,-6,2.49,.092,1.45,.075,bronze)
    block(5.905,-6,2.70,.04,.59,.23,teal);label(f'LIFT   0{i+1}',5.877,-6,2.70,.123,light,-pi/2)
    block(5.90,-5.14,1.03,.05,.15,.37,iron);block(5.865,-5.14,1.04,.02,.076,.076,led)
    block(5.83,-6,.028,.30,1.37,.035,bronze)
    for z in [.92,2.66]:block(7.90,-6,z,.13,.075,2.60 if z==.92 else 1.42,iron)
    if i==0:
        block(7,-6,.055,1.86,1.84,.09,iron)
        block(7.89,-6,1.29,.06,1.84,2.47,bronze)
        for y in [-6.88,-5.12]:block(7,y,1.29,1.83,.052,2.47,stone)
        block(7,-6,2.56,1.86,1.84,.075,iron)
    flush('Aligned elevator | car and landing' if i==0 else 'Aligned elevator | landing doors and well')
    # A single oak tower anchors the facade. Each level gets an inset numbered enamel sign.
    for j in range(17):block(6.015+j*.122,-7.104,1.94,.066,.052,3.78,reed)
    block(7,-7.15,2.24,1.78,.075,1.10,teal)
    label(f'0{i+1}',7,-7.195,2.35,.62,light)
    label(titles[i],7,-7.195,1.93,.116,light)
    block(7,-7.164,2.84,1.74,.035,.025,led)
    for z,h,m in [(3.78,.16,stone),(3.89,.063,iron),(3.7,.022,led)]:
        block(0,-7.095,z,16.39,.21,h,m)
        for side in (-1,1):block(side*8.105,0,z,.16,14.17,h,m)
    for x in (-8.03,-1.65,1.65,5.91):block(x,-7.04,1.9,.086,.14,3.76,bronze)
    if i==0:
        block(0,-7.075,2.56,2.96,.15,.38,teal);label('MAIN ENTRANCE',0,-7.159,2.56,.205,light)
    flush('Facade | fluted tower, floor marker and cornice')
    # Inlaid clear approach at the west-facing landing and a suspended directional blade.
    for y in [-6.65,-5.36]:block(4.78,y,.024,2.04,.022,.015,bronze)
    block(3.77,-6,.024,.022,1.31,.015,bronze)
    block(4.79,-6.81,2.79,1.94,.09,.33,teal)
    for x in [3.95,5.63]:block(x,-6.81,3.31,.024,.027,.73,bronze)
    label('ELEVATOR   ›',4.79,-6.864,2.79,.185,light)
    flush('Elevator lobby | inlay and wayfinding')
    camera(sc,(-9,-20,17),(0,-.6,1),36)
    b.context.preferences.filepaths.save_version=0
    path=os.path.join(out,f'Level_0{i+1}')
    b.ops.wm.save_as_mainfile(filepath=path+'.blend')
    b.ops.export_scene.gltf(filepath=path+'.glb',export_cameras=False,export_lights=False)
    if i:render(sc,'Level_0'+str(i+1)+'_preview')

b.ops.wm.read_factory_settings(use_empty=True);sc=b.context.scene
for i in range(3):
    with b.data.libraries.load(os.path.join(out,f'Level_0{i+1}.blend')) as (src,dst):
        dst.collections=[c for c in src.collections if c.startswith('Atrium ')]
    assert len(dst.collections)==1
    col=dst.collections[0];sc.collection.children.link(col)
    for o in col.objects:o.location.z+=step*i
b.ops.object.camera_add();sc.camera=b.context.object;camera(sc,(-14,-30,15.5),(0,-.4,5.75),38)
for floor in [0,1]:
    for x in [-4,4]:
        b.ops.object.light_add(type='AREA',location=(x,.3,3.64+floor*step))
        o=b.context.object;o.name='Recessed interior lighting';o.data.energy=270;o.data.shape='DISK';o.data.size=4.8;o.data.color=(1,.9,.78)
for pos,power,size in [((-10,-15,19),4800,10),((12,-5,16),3100,8),((0,9,18),2800,9)]:
    b.ops.object.light_add(type='AREA',location=pos);o=b.context.object;o.data.energy=power;o.data.size=size
    o.rotation_euler=(Vector((0,0,5))-o.location).to_track_quat('-Z','Y').to_euler()
sc.world=b.data.worlds.new('Soft daylight');sc.world.color=(.52,.5,.46)
for a in b.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.color_type='MATERIAL'
b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Building.blend'))
render(sc,'Atrium_Building_preview')
