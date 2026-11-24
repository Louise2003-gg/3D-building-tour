"""Calibrate fitted workstations, luminaires, porcelain and static lighting for the Atrium."""
import os,sys,math,json,bmesh,bpy as b,numpy as np
from mathutils import Vector
from math import sin,cos,pi
root=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,root)
import studio_details as s
out=os.path.join(s.base,'Architectural');os.makedirs(out,exist_ok=True)
s.out=out
def lights(level):
    arr=[]
    def add(x,y,h,w,d,p,k,temp):
        arr.append(dict(x=x,z=-y,h=h,w=w,d=d,p=p,kind=k,temp=temp))
    if level==1:
        for x,y,w in [(-4.2,-1.12,2.6),(-4.1,2.4,2.3),(-4.5,5.77,2.6),(4.56,5.50,2.05)]:
            add(x,y,3.49,w,.085,62,'linear',3650)
        for x,y in [(-4.1,-4.97),(4.31,2.97)]:add(x,y,2.95,.43,.43,38,'pendant',3100)
        for x,y in [(-6.8,-3.7),(-.1,-5.7),(.1,.9),(3.5,-4.8),(6.95,-2.4),(6.95,1.9),(-7.15,3.8)]:
            add(x,y,3.69,.17,.17,26,'down',3550)
    if level==2:
        for x in [-4.4,-.49,2.02]:
            for y in [.05,3.34]:add(x,y,3.41,.095,2.22,47,'linear',3850)
        for x,y in [(-7.24,1.9),(-5.2,6.17),(.1,6.1),(5.55,6.04)]:
            add(x,y,3.55,1.85,.08,46,'linear',3650)
        for y in [4,1.35,-1.34,-3.88]:
            for x in ([4.47] if y<-3 else [4.17,6.63]):add(x,y,2.94,.34,.34,26,'pendant',3050)
        for x in [-6.2,-3.05,.4,4.86]:add(x,-5.45,3.69,.18,.18,36,'down',3450)
    if level==3:
        for x in [-4.94,4.94]:
            for y in [-.8,2.05,5.16]:add(x,y,3.04,.085,1.66,34,'linear',3500)
        for x,y in [(-4.35,-4.65),(.05,-4.65),(4.92,-5.57),(0,.5)]:
            add(x,y,3.60,1.72,.092,52,'linear',3500)
        for x in [-6.875,-3.045,3.045,6.875]:
            for j in range(5):add(x,-2.25+(j+.5)*1.85-.37,2.912,.17,.17,18,'down',3100)
    return arr
specs={key:lights(i+1) for i,key in enumerate(['first','second','third'])}
if __name__=='__main__':
    with open(os.path.join(root,'luminaire-layout.json'),'w') as f:json.dump(specs,f,indent=1)
def filter_parts(o,rule,inspect=None):
    bm=bmesh.new();bm.from_mesh(o.data);todo=set(bm.verts);drop=[]
    while todo:
        seed=todo.pop();part=[seed]
        for v in part:
            for e in v.link_edges:
                n=e.other_vert(v)
                if n in todo:todo.remove(n);part.append(n)
        pts=np.array([tuple(o.matrix_world@v.co) for v in part]);c=(pts.min(axis=0)+pts.max(axis=0))/2
        if (inspect and inspect(c,pts.max(axis=0)-pts.min(axis=0))) or rule(*c):drop+=part
    bmesh.ops.delete(bm,geom=drop,context='VERTS');bm.to_mesh(o.data);bm.free()
def panel(w,h,depth,z,y,m,r=.012):
    rings=[]
    for yy,shrink in [(y,0),(y+depth*.73,0),(y+depth,depth*.15)]:
        row=[]
        for cx,cz,start in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
            for j in range(5):
                a=math.radians(start+j*22.5)
                row.append((cx*(w/2-r-shrink)+r*cos(a),yy,z+cz*(h/2-r-shrink)+r*sin(a)))
        rings.append(row)
    s.face(rings[0],m);s.face(rings[-1][::-1],m)
    for lo,hi in zip(rings,rings[1:]):
        for i in range(20):
            j=(i+1)%20;s.face([lo[j],lo[i],hi[i],hi[j]],m, smooth=True)
def station(kind,x,y,desk,angle,w):
    h=w*9/16;zc=.388
    # Thin aluminium enclosure with a tapered rear electronics housing, hinge and metal foot.
    panel(w+.014,h+.024,.019,zc,0,graphite)
    panel(w*.80,h*.74,.025,zc,.018,anod)
    panel(w*.34,.076,.012,zc-.041,.040,graphite,.008)
    s.tube((-.062,.045,zc-.040),(.062,.045,zc-.040),.026,anod,n=20)
    s.box(0,.060,(zc-.045)/2,.058,.037,zc-.045,anod)
    s.box(0,.023,.013,w*.46,.182,.020,anod)
    for dx in [-.09,.09]:s.box(dx,.026,.003,.047,.09,.004,s.plastic)
    for j in range(26):s.box((j-12.5)*.009,.044,zc+.072,.004,.002,.023,s.plastic)
    for j in range(3):
        s.box(-w*.32+j*.037,.045,zc-.070,.021,.003,.011,s.coal)
    s.box(w*.42,-.001,zc-h*.5-.007,.012,.002,.0018,indicator)
    s.face([(-w/2,-.001,zc-h/2),(w/2,-.001,zc-h/2),(w/2,-.001,zc+h/2),(-w/2,-.001,zc+h/2)],s.lcd[kind],[(0,0),(1,0),(1,1),(0,1)])
    s.oval(0,-.001,zc+h/2+.006,.0036,.0017,.0036,s.coal,10,5)
    # Mini desktop with milled vents, USB-C sockets and edge highlights.
    s.box(w*.354,.038,.031,.133,.110,.055,anod)
    for j in range(7):s.box(w*.354-.042+j*.014,.038,.059,.005,.063,.002,graphite)
    for j in range(2):s.box(w*.354-.027+j*.033,-.019,.029,.016,.002,.004,graphite)
    path=[(.05,.057,.29),(.069,.080,.19),(.045,.093,.067),(.068,.128,.010),(.155,.135,.009),(w*.354,.096,.026)]
    for a,c in zip(path,path[1:]):s.tube(a,c,.003,s.plastic,n=6)
    o=s.finish(kind+' | slim workstation, articulated stand and mini desktop');o.location=(x,y,desk);o.rotation_euler.z=angle
    # Actual stepped keycaps: top legends sample their corresponding region of the keyboard atlas.
    kb=.44;kd=.153
    s.box(0,0,.007,kb+.012,kd+.011,.013,anod)
    counts=[13,14,13,12,12,9]
    for row,count in enumerate(counts):
        unit=740/(count+(5 if row==5 else 0));left=14
        for j in range(count):
            wid=unit*(6 if row==5 and j==3 else 1);a=(left+2)/768;c=(left+wid-4)/768
            bottom=1-(12+row*71+60)/448;top=1-(12+row*71+3)/448
            xx=(a+c-1)*kb/2;yy=(top+bottom-1)*kd/2;p=(c-a)*kb/2;q=(top-bottom)*kd/2
            s.box(xx,yy,.015,p*2,q*2,.006,graphite)
            s.face([(xx-p,yy-q,.0181),(xx+p,yy-q,.0181),(xx+p,yy+q,.0181),(xx-p,yy+q,.0181)],s.keys,[(a,bottom),(c,bottom),(c,top),(a,top)])
            left+=wid
    s.box(.297,.002,.002,.116,.145,.004,s.slate if hasattr(s,'slate') else graphite)
    s.oval(.297,.001,.016,.030,.051,.021,anod);s.oval(.297,.016,.035,.004,.010,.004,graphite)
    o=s.finish('Low-profile keyboard, legend caps and contoured mouse');o.rotation_euler.z=angle
    o.location=(x+.255*sin(angle),y-.255*cos(angle),desk)
def office_chair(x,y,z,angle):
    # Breathable back, separate seat/back cushions, armpads, gas lift and five twin-wheel casters.
    for j in range(5):
        a=2*pi*j/5;u,v=.242*cos(a),.242*sin(a)
        s.tube((0,0,.115),(u,v,.071),.017,anod,.014)
        for k in [-1,1]:s.oval(u+k*.014*cos(a),v+k*.014*sin(a),.046,.026,.026,.031,graphite,10,6)
    s.tube((0,0,.10),(0,0,.43),.030,anod)
    s.oval(0,0,.47,.236,.211,.056,uphol,20,10)
    s.tube((0,.12,.41),(0,.198,.68),.019,graphite)
    panel(.405,.364,.026,.774,.195,graphite,.055)
    panel(.377,.331,.022,.774,.186,uphol,.048)
    for d in [-1,1]:
        s.box(d*.223,.022,.554,.022,.04,.137,graphite);s.box(d*.223,0,.63,.047,.153,.024,graphite)
    o=s.finish('Task seating | woven back and caster base');o.rotation_euler.z=angle;o.location=(x,y,z)
def lounge_chair(x,y,z,angle):
    # A continuous upholstered shell with a turned-over rim rather than overlapping lobes.
    rings=[]
    for i in range(43):
        a=-.53+(pi+1.06)*i/42
        top=.80+.32*(sin(a)*.5+.5)
        rings.append([(rx*cos(a),ry*sin(a),h) for rx,ry,h in [
            (.486,.451,.32),(.549,.518,.37),(.585,.547,top-.11),
            (.581,.543,top-.044),(.559,.523,top-.009),(.526,.486,top),
            (.490,.451,top-.016),(.459,.424,top-.073),(.430,.391,.488),(.437,.397,.356)]])
    for i in range(42):
        for j in range(10):
            k=(j+1)%10;s.face([rings[i][j],rings[i+1][j],rings[i+1][k],rings[i][k]],boucle,
                                 [(i/17,j*.20),((i+1)/17,j*.20),((i+1)/17,k*.20),(i/17,k*.20)],True)
    s.face(rings[0][::-1],boucle);s.face(rings[-1],boucle)
    def cushion(a,fac,h):return (.475*fac*math.copysign(abs(cos(a))**.76,cos(a)),-.036+.434*fac*math.copysign(abs(sin(a))**.76,sin(a)),h)
    sections=[(.36,.325),(.86,.339),(.99,.385),(1,.437),(.985,.462),(.91,.493),(.68,.507),(.25,.513)]
    rr=[[cushion(i*2*pi/40,r,h) for i in range(40)] for r,h in sections]
    for i in range(len(rr)-1):
        for j in range(40):k=(j+1)%40;s.face([rr[i][j],rr[i][k],rr[i+1][k],rr[i+1][j]],boucle,smooth=True)
    s.face(rr[-1],boucle);s.face(rr[0][::-1],boucle)
    for xx in [-.32,.32]:
        for yy in [-.27,.27]:s.tube((xx*1.12,yy*1.12,.058),(xx,yy,.37),.031,s.wood,.041,12)
    o=s.finish('Lounge | tailored wrap chair');o.location=(x,y,z);o.rotation_euler.z=angle
def upgrade(sc,levels):
    global graphite,anod,indicator,uphol,boucle
    s.palette();s.col=b.data.collections.new('Architectural | fitted hardware');sc.collection.children.link(s.col)
    graphite=s.material('Micro-etched graphite',(43,47,49),.38,.25);anod=s.material('Fine blasted aluminium',(152,158,161),.32,.72)
    indicator=s.material('Power indicator',(141,205,179),.3);uphol=s.material('Woven task upholstery',(80,88,87),.88)
    Y,X=np.mgrid[:256,:256];r=np.random.default_rng(2407).normal(0,.027,X.shape)
    weave=.98+.042*np.sin(2*pi*X*81/256)+.035*np.cos(2*pi*(Y*65/256+.22*np.sin(X*.8)))+r
    s.png('flax-boucle',weave[:,:,None]*[211,192,164])
    boucle=s.material('Flax boucle upholstery',(211,192,164),.86,image='flax-boucle');boucle.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value=.25
    labelmat=s.material('Printed nursery stock',(255,255,255),.72,image='cartons')
    # LCDs generate their own light; do not illuminate bright pixels as if printed on paper.
    for m in s.lcd.values():
        p=m.node_tree.nodes['Principled BSDF'];m.node_tree.links.remove(p.inputs['Base Color'].links[0]);p.inputs['Base Color'].default_value=(.010,.014,.018,1)
        p.inputs['Emission Strength'].default_value=.95;p.inputs['Roughness'].default_value=.29
    for o in list(sc.objects):
        n=o.name
        if n.startswith('Baby illustration') or 'calibrated LCD and rear housing' in n or n.startswith('Desktop | key legends'):
            b.data.objects.remove(o,do_unlink=True);continue
        if n=='FRONT DESK':
            o.location.x=-4.17;o.data.body='FRONT DESK';o.data.size=.50;o.data.space_character=1.07;o.data.extrude=.007
        if n.startswith('Reception desk and workstation'):
            filter_parts(o,lambda x,y,z:abs(x+4.52)<.05 and (abs(y+1.17)<.025 and z>1.55 or y>-.1))
        if n.startswith('Reception | keyboard'):
            filter_parts(o,lambda x,y,z:-5.1<x<-4.0 and y> -1.1)
        if n.startswith('Computer workstations'):
            filter_parts(o,lambda x,y,z:x>-7.06 or z>(3.96 if len(levels)>1 else 0)+.917)
        if n.startswith('Security reception and monitor'):
            filter_parts(o,lambda x,y,z:(abs(x+3.62)<.03 and abs(y+4.65)<.03) or abs(x+4.34)<.04)
        if n.startswith('Lounge seating and coffee table'):
            rx,ry,rz=o.matrix_world.translation;left=rx-1.62;right=rx+1.61
            filter_parts(o,lambda x,y,z:min(abs(x-left),abs(x-right))<.84 and abs(y-ry)<.84 and z>rz+.07)
            lounge_chair(left,ry-.01,rz-.035,pi*.5);lounge_chair(right,ry-.01,rz-.035,-pi*.5)
        if n.startswith('Stocked maple shelves'):
            def stock(c,dim):
                dx,dy,h=dim;w=max(dx,dy);thin=min(dx,dy)
                if not (.004<thin<.023 and .019<h<.49 and w<.65):return False
                if thin>.012:return True  # old raised dot illustration
                x,y,z=c;k=(round(x*21)+round(y*17)+round(z*11))%6
                right=Vector((0,1,0) if dx<dy else (1,0,0));normal=Vector((right.y,-right.x,0))
                center=Vector(c)+normal*(thin/2+.001);up=Vector((0,0,h*.5));side=right*w*.5
                a=(k%3)/3;d=1-(k//3+1)/2
                s.face([center-side-up,center+side-up,center+side+up,center-side+up],labelmat,[(a,d),(a+1/3,d),(a+1/3,d+.5),(a,d+.5)])
                return True
            filter_parts(o,lambda *args:False,stock)
            s.finish('Retail | printed product fronts') if s.vs else None
    for lv in levels:
        off=3.96*(lv-1) if len(levels)>1 else 0
        if lv==1:station('welcome',-4.52,-1.21,1.536+off,pi,.694);office_chair(-4.52,-.08,off,0)
        if lv==2:
            for j in range(4):
                y=-.25+j*1.19;station(['library','studio'][j%2],-7.63,y,.913+off,pi/2,.604);office_chair(-6.62,y,off,-pi/2)
        if lv==3:station('security',-3.62,-4.76,1.500+off,pi,.622);office_chair(-4.34,-3.68,off,0)
    for m in b.data.materials:
        if not m.use_nodes or not any(m.name.startswith(n) for n in ['Sandstone','Sand tile','Blush travertine']):continue
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(.60,.52,.43,1);p.inputs['Roughness'].default_value=.195
        p.inputs['Coat Weight'].default_value=.32;p.inputs['Coat Roughness'].default_value=.14;p.inputs['IOR'].default_value=1.50
        # Real-world grain, broad mineral clouds and a fine polished micro-surface.
        nodes=m.node_tree.nodes;link=m.node_tree.links.new;coord=nodes.new('ShaderNodeTexCoord')
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.8;noise.inputs['Detail'].default_value=4;noise.inputs['Distortion'].default_value=.35
        link(coord.outputs['Object'],noise.inputs[0])
        ramp=nodes.new('ShaderNodeValToRGB');a,c=ramp.color_ramp.elements;a.position=.18;a.color=(.45,.39,.33,1);c.position=.82;c.color=(.67,.61,.53,1)
        link(noise.outputs['Fac'],ramp.inputs[0]);link(ramp.outputs[0],p.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.06;bump.inputs['Distance'].default_value=.00055
        link(noise.outputs['Fac'],bump.inputs['Height']);link(bump.outputs[0],p.inputs['Normal'])
        m.diffuse_color=(.58,.50,.43,1)
def bake_volume(sc,lv,fixtures):
    # Visibility to finite ceiling emitters is baked through the actual furnishings/walls.
    # Five height slices let the tour shade vertical surfaces as well as the tile floor.
    w,h=96,84;atlas=np.zeros((h*5,w,3),np.uint8)
    pos=np.array([[l['x'],-l['z'],l['h']-.026] for l in fixtures]);pwr=np.array([l['p'] for l in fixtures])
    tints=np.array([[1,.83 if l['temp']<3300 else .90,.67 if l['temp']<3300 else .79] for l in fixtures])
    deps=b.context.evaluated_depsgraph_get();xs=np.linspace(-8+8/w,8-8/w,w);zs=np.linspace(-7+7/h,7-7/h,h)
    xx,zz=np.meshgrid(xs,zs)
    for k in range(5):
        height=.035+.75*k
        d2=(xx[:,:,None]-pos[:,0])**2+(-zz[:,:,None]-pos[:,1])**2+(height-pos[:,2])**2
        energy=.080*pwr*np.maximum(pos[:,2]-height,.03)/np.maximum(d2,.18)**1.5
        near=np.argsort(-energy,axis=2)[:,:,:5]
        for j in range(h):
            for i in range(w):
                origin=Vector((xs[i],-zs[j],height));irr=np.zeros(3)
                for a in near[j,i]:
                    d=Vector(pos[a])-origin;length=d.length
                    if length<.08:continue
                    visible=not sc.ray_cast(deps,origin,d/length,distance=max(.001,length-.055))[0]
                    irr+=tints[a]*energy[j,i,a]*(1 if visible else .045)
                atlas[j+k*h,i]=np.uint8(np.minimum(255,irr*120))
    path=s.tex;s.tex=out;s.png('Irradiance_0'+str(lv),atlas[::-1]);s.tex=path
def install_lighting(sc):
    ceiling=b.data.collections.new('Ceilings | hide for dollhouse views');sc.collection.children.link(ceiling)
    s.col=ceiling;trim=s.material('Recessed dark bronze',(69,64,57),.41,.44);white=s.material('Acoustic ceiling plaster',(235,230,220),.90)
    lamp=b.data.materials.new('Opal luminous diffuser');lamp.use_nodes=True;p=lamp.node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(1,.84,.65,1);p.inputs['Emission Strength'].default_value=6
    for lv,fixtures in enumerate(specs.values()):
        off=lv*3.96;roof=4.46 if lv==2 else 3.74
        s.box(0,0,roof+off+.045,16.15,14.09,.08,white)
        for l in fixtures:
            x,y,z,w,d=l['x'],-l['z'],off+l['h'],l['w'],l['d']
            if l['kind']=='down':
                s.tube((x,y,z),(x,y,z+.035),w*.55,trim,n=24);s.tube((x,y,z-.005),(x,y,z-.002),w*.44,lamp,n=24)
            elif l['kind']=='pendant':
                s.tube((x,y,z+.14),(x,y,roof+off),.007,trim,n=8)
                s.tube((x,y,z),(x,y,z+.14),w*.50,trim,w*.22,n=32);s.tube((x,y,z-.004),(x,y,z-.001),w*.465,lamp,n=32)
            else:
                s.box(x,y,z,w,d,.055,trim);s.box(x,y,z-.029,w-.025,d-.018,.006,lamp)
                for a in [-1,1]:s.tube((x+a*w*.36,y+a*d*.36,z+.025),(x+a*w*.36,y+a*d*.36,off+roof),.004,trim,n=6)
            dat=b.data.lights.new('Interior '+l['kind'],'AREA');dat.shape='RECTANGLE';dat.size=w;dat.size_y=d
            dat.energy=l['p'];dat.color=(1,.83 if l['temp']<3300 else .91,.67 if l['temp']<3300 else .79)
            o=b.data.objects.new('L%02d | '%(lv+1)+l['kind'],dat);sc.collection.objects.link(o);o.location=(x,y,z-.035)
        s.finish('Level %s | illuminated ceiling system'%(lv+1))
    for o in sc.objects:
        if o.type=='LIGHT' and (o.name.startswith('Recessed interior lighting') or o.name.startswith('Suite ambient')):o.data.energy=0
    ceiling.hide_viewport=True
    # Reveal the top floor for the orbit cutaway; render the eye-level view with its ceilings.
    return ceiling
if __name__=='__main__':
    for lv in [1,2,3]:
        b.ops.wm.open_mainfile(filepath=os.path.join(s.src,f'Level_0{lv}.blend'))
        sc=b.context.scene;s.detail(sc);b.context.view_layer.update();upgrade(sc,[lv]);b.context.view_layer.update()
        bake_volume(sc,lv,lights(lv));s.bake(sc,lv)
    b.ops.wm.open_mainfile(filepath=os.path.join(s.base,'Studio','Atrium_Studio.blend'))
    sc=b.context.scene;upgrade(sc,[1,2,3]);ceiling=install_lighting(sc)
    cam=b.data.cameras.new('Arrival | architectural interior');cam.lens=23
    o=b.data.objects.new(cam.name,cam);sc.collection.objects.link(o);o.location=(.55,-5.86,1.65)
    o.rotation_euler=(Vector((-3.50,-.62,1.08))-o.location).to_track_quat('-Z','Y').to_euler();sc.camera=o
    sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_x=1320;sc.render.resolution_y=880;sc.render.resolution_percentage=100
    b.context.preferences.filepaths.save_version=0;b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Architectural.blend'))
    sc.render.filepath=os.path.join(out,'Reception.png');b.ops.render.render(write_still=True)
    o.location=(-5.95,-1.40,5.42);o.rotation_euler=(Vector((-7.55,.56,5.18))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=27
    sc.render.filepath=os.path.join(out,'Workstations.png');b.ops.render.render(write_still=True)
