"""Build the student support floor, front render and assembled three-story .blend."""
import os, math, bpy
from mathutils import Vector, Matrix
from math import pi, sin, cos

root=os.path.dirname(os.path.abspath(__file__))
models=os.path.join(root,'models')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
level=bpy.data.collections.new('03 | Student Support Center')
sc.collection.children.link(level)
def material(name,hexcode,metal=0,glow=0,alpha=1):
    rgb=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
    rgba=tuple(((c+.055)/1.055)**2.4 if c>.04045 else c/12.92 for c in rgb)+(alpha,)
    m=bpy.data.materials.new(name);m.diffuse_color=rgba;m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    for k,v in [('Base Color',rgba),('Metallic',metal),('Roughness',.32 if metal else .46),('Alpha',alpha),('Emission Color',rgba),('Emission Strength',glow)]:p.inputs[k].default_value=v
    return m
oak=material('Maple veneer','CD9C72');wood=material('Door oak','AC7554');slat=material('Walnut flutes','926749')
ivory=material('Plaster','F9E5D6');sand=material('Blush travertine','EDD9C9');joint=material('Tile joints','CCB8AB')
black=material('Graphite','262329');metal=material('Brushed steel','A7AAA8',.68);bronze=material('Champagne alloy','B79772',.55)
white=material('Porcelain','FFF6EB');amber=material('Warm cove light','FFE1A2',glow=2.8)
pink=material('Rose wing','F3BDCF');pinklight=material('Rose LED','FF97CB',glow=2);berry=material('Berry ink','87395C')
blue=material('Sky wing','BBD8EE');bluelight=material('Sky LED','8FCFFF',glow=2);navy=material('Navy ink','294967')
glass=material('Gate glazing','BADDD9',alpha=.23);green=material('Gate indicator','88FBB2',glow=2)
verts=[];faces=[];slots=[];ids=[]
def mesh(v,f,m):
    if m not in slots:slots.append(m)
    n=len(verts);verts.extend(v);faces.extend(tuple(i+n for i in face) for face in f);ids.extend([slots.index(m)]*len(f))
def box(x,y,z,w,d,h,m):
    v=[(x+i*w/2,y+j*d/2,z+k*h/2) for k in (-1,1) for i,j in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    mesh(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)
def cyl(x,y,z,r,h,m,r2=None):
    n=24;v=[(x+R*cos(i*2*pi/n),y+R*sin(i*2*pi/n),z+k*h/2) for k,R in [(-1,r),(1,r2 if r2 is not None else r)] for i in range(n)]
    mesh(v,[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
def finish(name):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces)
    for m in slots:me.materials.append(m)
    me.polygons.foreach_set('material_index',ids);me.update()
    ob=bpy.data.objects.new(name,me);level.objects.link(ob)
    for a in (verts,faces,slots,ids):a.clear()
font=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
def text(body,x,y,z,size,m=black,angle=0):
    c=bpy.data.curves.new(body,'FONT');c.body=body;c.font=font;c.align_x='CENTER';c.align_y='CENTER';c.size=size;c.space_line=.86;c.extrude=.002;c.materials.append(m)
    o=bpy.data.objects.new(body,c);level.objects.link(o);o.location=(x,y,z);o.rotation_euler=(pi/2,0,angle)
def stroke(x,z,u,t,y,width,m):
    dx=u-x;dz=t-z;l=math.hypot(dx,dz);a=-dz/l*width/2;b=dx/l*width/2
    mesh([(xx,y,zz) for xx,zz in [(x+a,z+b),(x-a,z-b),(u-a,t-b),(u+a,t+b)]],[(0,1,2,3)],m)
def disc(x,y,z,r,m):
    mesh([(x+r*cos(i*pi/12),y,z+r*sin(i*pi/12)) for i in range(24)],[tuple(range(24))],m)
def board(x,y,z,w,h,bg,trim):
    box(x,y,z,w,.15,h,bronze);box(x,y-.084,z,w-.09,.025,h-.09,bg)
    for s in (-1,1):
        box(x+s*(w/2-.08),y-.103,z,.023,.018,h-.15,trim)
        box(x,y-.103,z+s*(h/2-.08),w-.15,.018,.023,trim)
def flutes(x,y,w,h):
    box(x,y,h/2,w,.22,h,oak)
    n=max(1,int(w/.12))
    for i in range(n):box(x-w/2+(i+.5)*w/n,y-.13,h/2,.048,.06,h,slat)
def light(name,pos,target,power,color,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

box(0,0,-.105,16.42,14.4,.21,joint)
for i in range(16):
    for j in range(14):box(i-7.5,j-6.5,.006,.991,.991,.012,sand)
box(0,7.05,1.75,16.4,.18,3.5,ivory)
for side in (-1,1):box(side*8.09,0,1.75,.18,14.17,3.5,ivory)
finish('Tiled third-floor slab and perimeter')
# Five rooms on either side of each wing's corridor; divisions are visible from the plan view.
for s,code,accent,tint in [(-1,'G',berry,pink),(1,'B',navy,blue)]:
    for row,(lo,hi,doorx,facing) in enumerate([(1.95,3.84,3.84,1),(5.75,8,5.75,-1)]):
        mid=s*(lo+hi)/2;face=s*facing
        if row==0:box(s*lo,2.38,1.45,.085,9.26,2.9,ivory)
        for j in range(6):box(mid,-2.25+j*1.85,1.45,hi-lo,.08,2.9,ivory)
        for j in range(5):
            y=-2.25+(j+.5)*1.85;x=s*doorx
            for t in (-1,1):box(x,y+t*.685,1.45,.095,.48,2.9,ivory)
            box(x,y,2.57,.11,.92,.66,ivory)
            box(x,y,1.12,.12,.92,2.24,bronze);box(x+face*.067,y,1.095,.035,.835,2.16,wood)
            box(x+face*.105,y-.29,.98,.064,.046,.18,black)
            number=f'{code}{1+5*row+j:02d}'
            box(x+face*.091,y,1.58,.016,.43,.25,accent)
            text(number,x+face*.103,y,1.58,.14,white,face*pi/2)
            box(x+face*.082,y,2.34,.035,.38,.037,tint)
            box(mid,y+.49,.75,hi-lo-.48,.49,.07,oak)
            for dx in (-.5,.5):box(mid+dx,y+.49,.385,.05,.34,.73,wood)
            cyl(mid,y-.04,.44,.21,.085,tint);cyl(mid,y-.04,.23,.066,.41,bronze)
            finish(number+' | solo room')
        if verts:finish(code+' wing partitions')
    board(s*4.78,6.90,2.07,1.54,.56,tint,white);text('QUIET WING',s*4.78,6.79,2.07,.19,accent)
    finish(code+' wing end wall')
# Backlit locker alcove closer to the lobby, with individual hinges, pulls and vents.
box(0,2.69,1.72,3.87,.14,3.44,oak)
board(0,2.55,2.93,3.72,.72,ivory,amber);text('LOCKER AREA',0,2.435,2.93,.36)
for j in range(4):
    for i in range(9):
        x=-1.68+i*.42;z=.38+j*.56
        box(x,2.50,z,.405,.29,.543,oak);box(x+.133,2.344,z,.034,.032,.105,black)
        for k in range(2):box(x-.085,2.347,z+.18+k*.027,.102,.015,.009,slat)
finish('Central bank of 36 secure lockers')
# Open portal frames and shallow ceiling coffers preserve both the eye-level view and cutaway.
for x in [-7.84,-2.75,2.75,7.84]:flutes(x,-2.48,.3,4.42)
for x,w,bg,led in [(-5.29,4.8,pink,pinklight),(0,5.42,ivory,amber),(5.29,4.8,blue,bluelight)]:
    board(x,-2.51,3.80,w,1.15,bg,led)
    box(x,-2.14,4.415,w+.13,.99,.12,oak);box(x,-2.12,3.18,w,.92,.085,bg)
    for t in (-1,1):box(x+t*(w/2-.015),-2.54,1.6,.037,.06,3.15,led)
    box(x,-2.62,3.2,w,.045,.033,led)
for s,m in [(-1,berry),(1,navy)]:
    x=s*5.29
    text(("GIRLS’" if s<0 else "BOYS’")+'\nSOLO ROOMS',x+.34,-2.625,3.91,.335)
    text('(10 ROOMS)',x+.34,-2.625,3.49,.21)
    u=x-1.48;y=-2.63
    disc(u,y,4.09,.115,m);box(u,y,3.83,.245,.017,.28,m)
    for t in (-1,1):
        stroke(u+t*.145,3.95,u+t*.21,3.68,y,.065,m)
        stroke(u+t*.065,3.72,u+t*.065,3.48,y,.075,m)
    if s<0:mesh([(u-.1,y-.013,3.86),(u-.2,y-.013,3.62),(u+.2,y-.013,3.62),(u+.1,y-.013,3.86)],[(0,1,2,3)],m)
text('STUDENT SUPPORT\nCENTER',.46,-2.625,3.97,.39);text('Study  ·  Rest  ·  Recharge',.46,-2.625,3.48,.205)
for s in (-1,1):
    x=-1.69
    for z in (3.56,3.67,3.78,3.89):stroke(x,z,x+s*.34,z+.13,-2.63,.036,black)
    stroke(x+s*.36,3.68,x+s*.36,4.04,-2.63,.041,black)
disc(-1.69,-2.63,4.09,.084,black)
finish('Illuminated lobby portals and wayfinding')
# Reception and access equipment.
box(-4.26,-4.72,.72,4.53,.99,1.4,oak);box(-4.26,-4.72,1.45,4.67,1.08,.09,wood)
board(-4.05,-5.24,.79,3.62,1.09,ivory,amber);text('SECURITY\nDESK',-3.87,-5.36,.8,.38)
box(-3.62,-4.65,1.82,.98,.085,.58,black);box(-3.62,-4.65,1.54,.14,.12,.14,metal);box(-3.62,-4.65,1.505,.45,.26,.032,black)
box(-4.83,-4.67,1.58,.67,.43,.18,black)
cyl(-4.34,-3.70,.54,.34,.13,black);box(-4.34,-3.45,.93,.62,.095,.67,black)
finish('Security reception and monitor')
for i,x in enumerate([-1.36,.49,2.34]):
    box(x,-4.42,.66,.31,1.45,1.29,metal);box(x,-4.42,1.33,.33,1.48,.06,black)
    box(x,-5.158,1,.25,.035,.32,black)
    stroke(x,.89,x,1.11,-5.18,.037,green)
    for s in (-1,1):stroke(x,1.11,x+s*.078,1.02,-5.18,.034,green)
    if i<2:
        for u in (x+.51,x+1.34):
            box(u,-4.53,.71,.67,.037,.76,glass);box(u,-4.53,1.10,.68,.043,.026,metal)
finish('Two glazed access lanes')
board(5.56,-5.26,.96,2.05,1.83,white,bronze);box(5.56,-5.26,.065,2.13,.48,.11,black)
text('FACILITY FEATURES',5.56,-5.38,1.54,.178)
for i,line in enumerate(['10 Girls’ Solo Rooms','10 Boys’ Solo Rooms','Secure Locker Area','CCTV Monitoring','Controlled Access','Study · Rest · Recharge']):
    text(line,5.6,-5.38,1.26-i*.176,.126);disc(4.75,-5.38,1.26-i*.176,.023,bronze)
for s in (-1,1):
    cyl(s*7.51,-2.77,3.15,.16,.11,white);cyl(s*7.51,-2.77,3.053,.101,.11,black,.136)
finish('Facility directory and lobby cameras')
with bpy.data.libraries.load(os.path.join(models,'Reference_First_Floor.blend')) as (src,dst):dst.objects=['Potted foliage']
pot=dst.objects[0];level.objects.link(pot);bpy.context.view_layer.update();transform=pot.matrix_world.copy()
for x,y,z,s in [(-7.05,-4.82,0,1.18),(3.74,-4.93,0,1.01),(-1.74,1.73,0,.82),(1.74,1.73,0,.82),(-5.96,-4.73,1.50,.36),(-2.53,-4.65,1.50,.4)]+[(k*5.49,j,0,.48) for k in (-1,1) for j in (-1.72,1.94,5.67)]:
    o=pot.copy();level.objects.link(o);o.matrix_world=Matrix.Translation((x,y,z))@Matrix.Scale(s/.66,4)@Matrix.Translation((6.41,1.1,-1.54))@transform
level.objects.unlink(pot)
def camera(pos,target,lens):
    bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;sc.camera=cam;return cam
cam=camera((0,-17.6,2.56),(0,-1,2.08),33)
light('Lobby softbox',(0,-9,7),(0,0,1),1600,(1,.89,.76),8)
light('Locker alcove',(0,.4,4.6),(0,2.6,1.4),350,(1,.77,.5),3)
for s in (-1,1):light('Wing accent',(s*4.9,-3,3.4),(s*4.9,3,1),300,(1,.57,.72) if s<0 else (.57,.77,1),2.8)
sc.world=bpy.data.worlds.new('Warm ambient');sc.world.color=(.49,.45,.42)
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.use_denoising=True;sc.render.resolution_x=1200;sc.render.resolution_y=680;sc.render.resolution_percentage=100
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.color_type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(models,'Reference_Third_Floor.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(models,'reference_third_floor.glb'),export_cameras=False,export_lights=False)
sc.render.filepath=os.path.join(root,'third_floor_preview.png');bpy.ops.render.render(write_still=True)
with bpy.data.libraries.load(os.path.join(models,'Reference_Building.blend')) as (src,dst):dst.collections=[n for n in src.collections if n.startswith(('01 |','02 |'))]
assert len(dst.collections)==2
for c in dst.collections:sc.collection.children.link(c)
for o in level.objects:o.location.z+=7.92
for o in sc.objects:
    if o.type=='LIGHT':o.location.z+=7.92
light('Building daylight',(-8,-14,21),(0,0,5),4700,(1,.93,.85),11)
cam.location=(18,-30,22);cam.rotation_euler=(Vector((0,0,5.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=40
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(models,'Reference_Three_Floor_Building.blend'))
