"""Generate the furnished reference scene with Blender in background mode."""
import bpy, math, os, random
from mathutils import Vector
from math import sin, cos, pi

random.seed(41)
b=bpy
b.ops.wm.read_factory_settings(use_empty=True)
root=os.path.dirname(os.path.abspath(__file__))
def mat(name,h,rough=.55):
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    m=b.data.materials.new(name); m.diffuse_color=tuple(((v+.055)/1.055)**2.4 if v>.04045 else v/12.92 for v in rgb)+(1,)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough
    return m
oak=mat('Honey oak','D4A16A'); edge=mat('Maple','E8BC87'); grain=mat('Oak grooves','BA895C')
wall=mat('Peach plaster','F6DEC9'); ivory=mat('Warm porcelain','FFF6E9'); ink=mat('Charcoal','262629'); black=mat('Printed ink','19181A')
tile=mat('Sandstone','EAD8C4'); grout=mat('Grout','CDBAA8'); cement=mat('Pavement','AAA5A6')
pink,blue,green,gold,rose=[mat(n,h) for n,h in [('Petal','F0A7B4'),('Sky','82BED6'),('Pistachio','AFC98A'),('Honey','F4C353'),('Coral','EF987F')]]
colors=[pink,blue,green,gold,rose];leaf=[mat('Leaf '+str(i),h) for i,h in enumerate(['508127','6D972D','385E20'])]
fur=mat('Caramel plush','B87B43'); muzzle=mat('Vanilla plush','E9CBA0'); fabric=mat('Upholstery','F0DFC5')
glass=mat('Clear glazing','D4E3E4');glass.diffuse_color=(*glass.diffuse_color[:3],.085);glass.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.085
light=mat('Amber strip','FFE99C');p=light.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.53,.1,1);p.inputs['Emission Strength'].default_value=2
cache={}; group=[]
def prim(key,create,n,pos,scale,m,rot=(0,0,0)):
    k=(key,m.name)
    if k not in cache:
        create();o=b.context.object;cache[k]=o.data;o.data.materials.append(m);o.data.use_fake_user=True
    else:
        o=b.data.objects.new(n,cache[k]);b.context.collection.objects.link(o)
    o.name=n;o.location=pos;o.scale=scale;o.rotation_euler=rot;group.append(o);return o
def box(n,x,y,z,w,d,h,m,rot=0):
    return prim('box',lambda:b.ops.mesh.primitive_cube_add(size=1),n,(x,y,z),(w,d,h),m,(0,0,rot))
def ball(n,x,y,z,a,c,d,m,rot=(0,0,0)):
    o=prim('ball',lambda:b.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12),n,(x,y,z),(a,c,d),m,rot)
    if o.data.users==2:
        for f in o.data.polygons:f.use_smooth=True
    return o
def cyl(n,x,y,z,r,h,m,r2=None):
    ratio=round((r2 if r2 is not None else r)/r,3)
    return prim(('cyl',ratio),lambda:b.ops.mesh.primitive_cone_add(vertices=40,radius1=ratio,radius2=1,depth=1),n,(x,y,z),(r,r,h),m)
def finish(name):
    if not group:return
    b.ops.object.select_all(action='DESELECT')
    for o in group:o.select_set(True)
    group[0].data=group[0].data.copy()
    b.context.view_layer.objects.active=group[0];b.ops.object.join();b.context.object.name=name;group.clear()
fontpath='C:/Windows/Fonts/arialbd.ttf'
font=b.data.fonts.load(fontpath) if os.path.isfile(fontpath) else None
def text(s,x,y,z,size,m=black):
    c=b.data.curves.new(s,'FONT');c.body=s;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.extrude=.003
    if font:c.font=font
    o=b.data.objects.new(s,c);b.context.collection.objects.link(o);o.location=(x,y,z);o.rotation_euler.x=pi/2;c.materials.append(m)
def line(n,a,b,r,m):
    v=Vector(b)-Vector(a);o=cyl(n,*((Vector(a)+Vector(b))/2),r,v.length,m);o.rotation_euler=v.to_track_quat('Z','Y').to_euler()
def plant(x,y,z,s):
    cyl('pot',x,y,z+.26*s,.32*s,.52*s,ivory,.25*s)
    cyl('soil',x,y,z+.523*s,.276*s,.014*s,grain)
    for i in range(16):
        a=i*2.4;t=(.38+.14*(i%3))*s
        ball('leaf',x+cos(a)*.18*s,y+sin(a)*.18*s,z+.53*s+t*.56,.105*s,.039*s,t*.62,leaf[i%3],(0,.48+(i%4)*.15,a))
    finish('Potted foliage')
def teddy(x,y,z,s,m=fur):
    for dx,dy,dz,w,d,h,mt in [(0,0,.48,.33,.24,.41,m),(0,-.02,.97,.33,.25,.31,m),(-.25,0,1.18,.115,.09,.12,m),(.25,0,1.18,.115,.09,.12,m),(0,-.245,.88,.145,.058,.107,muzzle),(0,-.297,.92,.044,.025,.031,ink)]+[(i*.12,-.247,1,.027,.019,.031,ink) for i in (-1,1)]+[(i*.33,-.04,.52,.11,.13,.23,m) for i in (-1,1)]+[(i*.21,-.16,.17,.17,.2,.17,m) for i in (-1,1)]:
        ball('plush',x+dx*s,y+dy*s,z+dz*s,w*s,d*s,h*s,mt)
    finish('Seated teddy')
def shelf(x,y,w,levels,h=2.2,depth=.68,base=0):
    for xx in [-1,1]:box('side',x+xx*(w/2-.04),y,base+h/2,.08,depth,h,oak)
    box('back',x,y+depth/2-.03,base+h/2,w,.06,h,grain)
    for j in range(levels+1):
        z=base+.09+j*(h-.14)/levels;box('shelf',x,y,z,w,depth,.085,edge)
        if j==levels:continue
        count=max(2,int(w/.33))
        for i in range(count):
            px=x-w/2+(i+.5)*w/count; pw=w/count*.77;ph=(h-.14)/levels*random.uniform(.58,.84);py=y-.06
            m=random.choice(colors);box('carton',px,py,z+.045+ph/2,pw,.32,ph,m)
            box('printed label',px,py-.162,z+.05+ph*.57,pw*.91,.008,ph*.52,ivory)
            ball('label motif',px,py-.17,z+.05+ph*.53,pw*.18,.009,pw*.2,m)
    finish('Stocked maple shelves')
def capsule(n,x,y,z,w,d,h,m):
    rim=[]
    for side,start in [(1,-pi/2),(-1,pi/2)]:
        for i in range(21):
            a=start+i*pi/20;rim.append((side*(w-d)/2+d/2*cos(a),d/2*sin(a)))
    k=len(rim);verts=[(u,v,t) for t in (-h/2,h/2) for u,v in rim]
    faces=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
    data=b.data.meshes.new(n);data.from_pydata(verts,[],faces);data.materials.append(m)
    o=b.data.objects.new(n,data);b.context.collection.objects.link(o);o.location=(x,y,z);group.append(o)
def baby(x,y,z,s):
    for dx,dz,w,h,m in [(0,0,.48,.42,ink),(-.41,-.12,.14,.14,ink),(.41,-.12,.14,.14,ink),(-.41,-.12,.1,.09,wall),(.41,-.12,.1,.09,wall),(0,0,.445,.385,wall),(-.15,-.02,.035,.027,ink),(.15,-.02,.035,.027,ink),(0,-.16,.059,.038,ink),(-.24,-.11,.062,.031,pink),(.24,-.11,.062,.031,pink)]:
        ball('sign illustration',x+dx*s,y,z+dz*s,w*s,.018*s,h*s,m);y-=.012*s
    finish('Baby illustration')

# Open-front cutaway with a glazed entrance and a walk-through divider.
box('site',0,0,-.22,58,48,.26,cement)
box('floor',0,0,-.065,16.4,14.4,.13,grout)
for i in range(16):
    for j in range(14):box('tile',i-7.5,j-6.5,.004,.989,.989,.014,tile)
finish('Paved site and tiled floor')
for x,y,w,d in [(0,7.07,16.4,.2),(-8.1,0,.2,14.3),(8.1,0,.2,14.3)]:
    box('wall',x,y,1.85,w,d,3.7,wall);box('cap',x,y,3.71,w+.05,d+.05,.075,ink)
for x in (-4.71,4.71):
    box('front',x,-7.05,.61,6.65,.18,1.22,oak);box('cap',x,-7.05,1.25,6.65,.22,.075,ink)
for x in (-1.37,0,1.37):box('frame',x,-7.06,1.16,.065,.1,2.32,ink)
box('lintel',0,-7.06,2.32,2.8,.12,.09,ink)
for x in (-.685,.685):
    box('pane',x,-7.06,1.15,1.29,.04,2.2,glass);box('pull',x*.23,-7.15,1.15,.045,.08,.51,ink)
box('doormat',0,-7.64,-.065,2.75,.97,.07,ink)
for y,d,h in [(3.4,7.2,3.7),(-3.58,2.5,2.52)]:
    box('divider',1.16,y,h/2,.17,d,h,edge)
    for j in range(int(d/.33)):box('join',1.25,y-d/2+j*.33,h/2,.01,.012,h,grain)
finish('Cutaway walls, partition and entry')
for x in (-5.2,-2.75,-.3):shelf(x,6.44,2.43,3,2.28)
shelf(-3.45,3.22,2.65,2,1.55,.94)
for i in range(6):
    px=-4.52+i*.42;m=colors[i%5];box('pack',px,3.2,1.76,.31,.26,.43,m);box('label',px,3.063,1.77,.25,.012,.21,ivory)
finish('Countertop merchandise')
shelf(0,0,2.04,3,1.94)
o=b.context.object
from mathutils import Matrix
o.matrix_world=Matrix.Translation((-7.58,.63,0)) @ Matrix.Rotation(pi/2,4,'Z') @ o.matrix_world
for x in [-6.06,-4.98,-2.02,-1.49,-.96,-.43]:teddy(x,6.4,2.28,.48,random.choice([fur,muzzle,ivory]))
text('STORE',-3.75,6.95,3.14,.67)
box('shopping bag',-5.39,6.91,3.13,.38,.06,.38,pink)
for i in range(12):
    a=i*pi/12;t=(i+1)*pi/12
    line('handle',(-5.39+.095*cos(a),6.89,3.31+.13*sin(a)),(-5.39+.095*cos(t),6.89,3.31+.13*sin(t)),.017,ink)
finish('Store bag sign')
for y in (2.85,5.9):cyl('post',-7.16,y,1.23,.036,2.46,edge)
line('rail',(-7.16,2.84,2.45),(-7.16,5.91,2.45),.035,ink)
for i in range(13):
    y=2.98+i*.23;m=[pink,ivory,blue,rose,fabric][i%5]
    for side in (-1,1):
        line('hanger',(-7.16,y,2.4),(-7.16+side*.28,y,2.16),.021,edge)
        o=box('sleeve',-7.16+side*.28,y,2.02,.23,.077,.35,m);o.rotation_euler.y=-side*.48
    box('shirt',-7.16,y,1.73,.47,.09,.83,m)
finish('Rail of pastel baby clothes')
capsule('counter',-4.17,-1.15,.77,5.76,1.42,1.38,oak)
capsule('glow',-4.17,-1.15,.084,5.65,1.36,.085,light)
capsule('worktop',-4.17,-1.15,1.49,5.82,1.48,.085,ivory)
box('monitor',-4.52,-1.17,1.94,1.32,.095,.72,ink);box('stand',-4.52,-1.17,1.61,.2,.17,.19,ink)
ball('office seat',-4.52,.06,.74,.64,.54,.14,ink);ball('office back',-4.52,.45,1.38,.68,.13,.69,ink)
finish('Reception desk and workstation')
text('FRONT DESK',-3.86,-1.872,.81,.48);baby(-5.56,-1.878,.82,.59)
plant(-6.41,-1.1,1.54,.66)
cyl('vase',-2.35,-1.18,1.68,.16,.28,ivory,.12)
for i in range(26):
    a=i*2.4;r=.22*math.sqrt(i/26);ball('flower',-2.35+r*cos(a),-1.18+r*sin(a),1.98+.11*(1-r/.22),.064,.061,.062,[pink,rose,ivory][i%3])
finish('Flower arrangement')
box('waiting rug',-4.1,-4.99,.035,5.99,3.1,.045,mat('Oat carpet','D5BEA6'))
for x,side in [(-5.72,-1),(-2.49,1)]:
    for dx in (-.41,.41):
        for dy in (-.32,.32):cyl('foot',x+dx,-5+dy,.22,.055,.35,oak)
    ball('seat',x,-5,.59,.72,.65,.24,fabric)
    for j in range(15):
        a=(pi if side<0 else 0)+(j/14-.5)*pi*1.18
        ball('curved upholstery',x+.59*cos(a),-5+.52*sin(a),.83,.22,.22,.32+.17*sin(j*pi/14),fabric)
for z in (.27,.86):cyl('coffee table',-4.1,-5,z,.66,.09,edge)
for dx in (-.37,.37):cyl('leg',-4.1+dx,-5,.45,.045,.8,oak)
finish('Lounge seating and coffee table');plant(-4.1,-5,.91,.52)
box('water dispenser',-7.49,-2.93,.61,.67,.63,1.2,ivory);cyl('water bottle',-7.49,-2.93,1.56,.3,.68,blue);finish('Water cooler')
text('NURSERY',4.94,6.94,2.22,.65);baby(4.94,6.93,3.03,1.02)
for x in (3.59,6.27):text('♥',x,6.94,3.04,.47,pink)
shelf(4.54,6.38,3.22,1,.63);teddy(7,6.26,.02,1.48);plant(2.33,6.24,0,1.38)
for i in range(5):cyl('stacking rings',3.86,6.38,.71+i*.086,.19-i*.025,.09,colors[i])
for x in (4.72,5.4):
    ball('toy car',x,6.33,.79,.21,.12,.094,blue if x>5 else gold)
    for dx in (-.12,.12):ball('wheel',x+dx,6.23,.73,.055,.032,.055,ink)
finish('Toy collection')
box('rug',4.28,1.44,.035,3.88,6.8,.045,mat('Pastel play mat','F0C9C6'))
for i in range(66):
    x=random.uniform(2.57,6);y=random.uniform(-1.67,4.57)
    ball('pastel spot',x,y,.061,.1+random.random()*.12,.1,.004,random.choice([fabric,pink,blue,muzzle,ivory]))
for x,y,s,m in [(4.77,-1.12,.88,fur),(3.39,.08,.51,gold),(5.28,.23,.51,fabric)]:
    for dx in (-.55,.55):ball('printed ear',x+dx*s,y+.4*s,.071,.26*s,.26*s,.006,m)
    ball('printed bear',x,y,.078,.8*s,.62*s,.008,m)
    ball('muzzle',x,y-.18*s,.088,.33*s,.24*s,.006,ivory)
    for dx in (-.28,.28):ball('eye',x+dx*s,y+.04*s,.093,.049*s,.049*s,.006,ink)
    ball('nose',x,y-.1*s,.098,.086*s,.052*s,.005,ink)
finish('Illustrated bear play rug')
tx,ty=4.31,2.97
cyl('table',tx,ty,.83,.89,.09,edge)
for i in range(4):
    a=i*pi/2+.75;cyl('table leg',tx+.63*cos(a),ty+.63*sin(a),.44,.053,.75,oak)
for i in range(6):
    a=i*pi/3-pi/2;x=tx+1.16*cos(a);y=ty+1.16*sin(a);m=[blue,pink,gold,ivory,green,gold][i]
    cyl('seat',x,y,.44,.29,.09,m)
    ball('back',x+.23*cos(a),y+.23*sin(a),.68,.29,.055,.27,m,(0,0,a-pi/2))
    for dx in (-.17,.17):
        for dy in (-.15,.15):cyl('leg',x+dx,y+dy,.22,.025,.38,oak)
cyl('pencil cup',tx,ty,.96,.095,.18,ivory)
for i in range(8):line('pencil',(tx+.044*cos(i),ty+.044*sin(i),.97),(tx+.077*cos(i),ty+.077*sin(i),1.18+.04*sin(i)),.012,colors[i%5])
finish('Activity table and six chairs')
x,y=7.03,2.42
box('cot base',x,y,.48,1.46,2.82,.15,oak);box('mattress',x,y,.66,1.31,2.64,.23,ivory)
for dx in (-.69,.69):
    for dy in (-1.36,1.36):box('post',x+dx,y+dy,.82,.09,.09,1.62,oak)
    box('rail',x+dx,y,1.54,.08,2.8,.095,edge)
    for i in range(12):box('spindle',x+dx,y-1.22+.222*i,1,.035,.044,1,edge)
for dy in (-1.36,1.36):
    box('rail',x,y+dy,1.54,1.43,.08,.095,edge)
    for i in range(6):box('spindle',x-.53+i*.21,y+dy,1,.044,.04,1,edge)
finish('Slatted crib')
box('cabinet',7.21,-2.29,.65,1.13,2.2,1.29,oak);box('pad',7.21,-2.29,1.37,.97,2.06,.15,ivory)
for dx in (-.46,.46):box('pad edge',7.21+dx,-2.29,1.49,.08,2.06,.16,ivory)
for z in (.43,.86):box('drawer seam',6.642,-2.29,z,.014,2.02,.018,grain)
finish('Changing cabinet');shelf(5.71,-5.69,1.82,2,1.34)
for y in (4.73,3.27,-1.84,-2.8):
    box('frame',7.97,y,2.14,.07,.74,1.03,oak);box('paper',7.928,y,2.14,.02,.65,.94,ivory)
    for i in range(4):ball('art',7.91,y+.14*sin(i*2),2.13+.17*cos(i),.01,.095,.14,colors[i])
finish('Framed nursery prints')
for x,y,s in [(-7.37,-5.51,1.3),(7.28,-5.57,1.39),(-2.04,-7.64,.95),(2.05,-7.64,.95),(-7.41,6.23,1.16)]:plant(x,y,0,s)

sc=b.context.scene
b.ops.object.camera_add(location=(0,-20.6,16.7));cam=b.context.object;cam.rotation_euler=(Vector((0,-.47,.85))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=39;sc.camera=cam
def area(pos,power,size):
    b.ops.object.light_add(type='AREA',location=pos);o=b.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area((-5,-7,14),2400,9);area((6,3,11),1600,8)
sc.world=b.data.worlds.new('Soft daylight');sc.world.color=(.48,.48,.48)
sc.render.resolution_x=1536;sc.render.resolution_y=1024;sc.render.resolution_percentage=100
for a in b.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.color_type='MATERIAL'
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(root,'models','Reference_First_Floor.blend'))
b.ops.export_scene.gltf(filepath=os.path.join(root,'models','reference_first_floor.glb'),export_yup=True,export_cameras=False,export_lights=False)
