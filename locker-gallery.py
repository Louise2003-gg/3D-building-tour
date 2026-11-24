"""Fit the formerly enclosed rear bay as a two-sided gallery. Blender background script."""
import bpy as b, os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,root)
import architectural_finish as arch
s=arch.s;out=os.path.join(s.base,'Gallery');os.makedirs(os.path.join(out,'source'),exist_ok=True)
start,end=2.49,6.94;pitch=(end-start)/9;front=1.403;bottom=.13;rowH=1.13
lights=[dict(x=x,z=-4.65,h=2.83,w=.066,d=3.96,p=48,kind='linear',temp=3500) for x in [-.97,.97]]
def gallery(sc,off,editable):
    rm=[o for o in sc.objects if o.name.startswith('Central bank of 36 secure lockers') or (o.type=='FONT' and o.data.body=='LOCKER AREA')]
    assert len(rm)==2,[o.name for o in rm]
    for o in rm:b.data.objects.remove(o,do_unlink=True)
    col=b.data.collections.new('Locker gallery | fitted joinery');sc.collection.children.link(col);s.col=col
    def old(key):
        return next(m for m in b.data.materials if m.name==key)
    wood=old('Door oak');edge=old('Maple veneer');metal=old('Brushed steel');ink=old('Graphite');sage=old('Atrium petrol')
    upholstery=next(m for m in b.data.materials if m.name.startswith('Woven slate'))
    white=old('Opal lettering');light=next(m for m in b.data.materials if m.name.startswith('Warm cove light'))
    face=s.material('Mist sage powder enamel',(150,166,159),.37,.22);dark=s.material('Reveal powder enamel',(46,55,54),.58,.25)
    woodblock=lambda x,y,z,w,d,h,m:s.box(x,y,z+off,w,d,h,m)
    def text(body,x,y,z,size,angle=0,m=white,leaf=False):
        c=b.data.curves.new(body,'FONT');c.body=body;c.font=b.data.fonts.load('C:/Windows/Fonts/arialbd.ttf',check_existing=True)
        c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.resolution_u=3;c.materials.append(m)
        o=b.data.objects.new(('Locker leaf ' if leaf else 'Gallery type ')+body,c);col.objects.link(o);o.location=(x,y,z+off);o.rotation_euler=(math.pi/2,0,angle)
    woodblock(0,start-.07,2.64,3.90,.18,.53,wood)
    woodblock(0,start-.17,2.65,3.83,.045,.40,sage)
    text('LOCKER GALLERY',0,start-.197,2.64,.255)
    woodblock(0,start-.13,2.38,3.82,.055,.025,light)
    for side in [-1,1]:
        x=side*1.67;mid=(start+end)/2;length=end-start
        woodblock(x,mid,.069,.56,length,.138,dark)
        woodblock(side*1.91,mid,1.35,.07,length,2.45,wood)
        for z in [bottom,bottom+rowH,bottom+2*rowH]:woodblock(x,mid,z,.535,length,.048,edge)
        for j in range(10):woodblock(x,start+j*pitch,1.26,.535,.022,2.29,edge)
        for y in [start-.017,end+.013]:woodblock(x,y,1.48,.557,.045,2.95,wood)
        woodblock(x,mid,2.68,.555,length,.53,wood)
        woodblock(side*1.38,mid,2.49,.025,length-.04,.022,light)
        woodblock(side*1.38,mid,.097,.022,length-.04,.015,light)
        for j in range(9):
            y=start+(j+.5)*pitch
            for row in range(2):
                z=bottom+(row+.5)*rowH
                # Internal shelf and double peg are visible when the door swings open.
                woodblock(x,y,z+.28,.46,pitch-.035,.023,edge)
                woodblock(side*1.84,y,z+.12,.095,.023,.025,metal)
                woodblock(side*1.80,y,z+.148,.018,.022,.061,metal)
        s.finish('Gallery | full-depth carcass and illuminated cornice')
        for j in range(9):
            y=start+(j+.5)*pitch
            for row in range(2):
                z=bottom+(row+.5)*rowH;num=1+(18 if side==1 else 0)+j*2+row
                woodblock(side*(front+.021),y,z,.036,pitch-.016,rowH-.019,face)
                # Folded perimeter, clean shadow reveals, recessed vents, plate, thumbturn and handle.
                woodblock(side*(front-.003),y,z+.46,.014,pitch-.036,.017,metal)
                for k in range(4):woodblock(side*(front-.001),y-.122+k*.075,z-.455,.010,.055,.009,dark)
                woodblock(side*(front-.010),y+.12,z+.05,.020,.105,.204,dark)
                woodblock(side*(front-.023),y+.12,z+.099,.008,.055,.016,light)
                for h in [-.035,.032]:woodblock(side*(front-.048),y+.12,z+h,.071,.019,.017,metal)
                woodblock(side*(front-.084),y+.12,z,.016,.024,.089,metal)
                woodblock(side*(front-.009),y-.095,z+.32,.014,.148,.092,sage)
                text(f'{num:02d}',side*(front-.018),y-.095,z+.322,.055,-side*math.pi/2,leaf=True)
                s.finish('Locker leaf '+f'{num:02d}'+' | enamel, vents and pull')
    # The back wall terminates in a slatted oak niche and a small upholstered change bench.
    woodblock(0,6.938,1.46,2.82,.07,2.92,dark)
    for j in range(31):woodblock(-1.35+j*.09,6.877,1.46,.061,.086,2.92,wood)
    woodblock(0,6.79,1.68,1.96,.048,.51,sage);text('PERSONAL STORAGE',0,6.76,1.74,.153)
    text('LEVEL   03     /     01 — 36',0,6.76,1.54,.071)
    woodblock(0,6.53,.31,2.28,.51,.17,edge);woodblock(0,6.51,.445,2.23,.49,.101,upholstery)
    for x in [-.91,.91]:woodblock(x,6.53,.16,.054,.39,.29,metal)
    s.finish('Gallery | slatted end wall and upholstered bench')
    if editable:
        # UV set used by the edited building's physically scaled material library.
        for o in col.objects:
            if o.type!='MESH':continue
            me=o.data;uv=me.uv_layers.new(name='Surface metres')
            for p in me.polygons:
                axis=max(range(3),key=lambda i:abs(p.normal[i]))
                for k in p.loop_indices:
                    v=me.vertices[me.loops[k].vertex_index].co
                    uv.data[k].uv=(v.z/1.35,v.y/.42) if axis==0 else (v.x/1.35,(v.y if axis==2 else v.z)/.42)
            me.uv_layers.active_index=0;me.uv_layers[0].active_render=True
            if o.name.startswith('Locker leaf'):
                mod=o.modifiers.new('Folded edge radius','BEVEL');mod.width=.002;mod.segments=2
        for l in lights:
            x,y,z=l['x'],-l['z'],l['h']
            woodblock(x,y,z,.08,l['d'],.045,dark);woodblock(x,y,z-.026,.054,l['d']-.03,.008,light)
            dat=b.data.lights.new('Gallery warm linear','AREA');dat.shape='RECTANGLE';dat.size=.08;dat.size_y=l['d'];dat.energy=l['p'];dat.color=(1,.86,.73)
            o=b.data.objects.new('Gallery shelf wash',dat);col.objects.link(o);o.location=(x,y,off+z-.04)
        s.finish('Gallery | twin ceiling washes')
        woodblock(0,4.69,2.983,3.9,4.55,.07,old('Plaster'));lid=s.finish('Gallery | removable soffit')
        lid.hide_set(True)

arch.out=out;s.out=os.path.join(out,'source')
b.ops.wm.open_mainfile(filepath=os.path.join(s.src,'Level_03.blend'));sc=b.context.scene
s.detail(sc);b.context.view_layer.update();arch.upgrade(sc,[3]);gallery(sc,0,False);b.context.view_layer.update()
layout=arch.specs;layout['third']+=lights
with open(os.path.join(root,'luminaire-layout.json'),'w') as f:json.dump(layout,f,indent=1)
arch.bake_volume(sc,3,layout['third']);s.bake(sc,3)
b.ops.wm.open_mainfile(filepath=os.path.join(s.base,'MaterialStudy','Atrium_Material_Study.blend'));sc=b.context.scene
gallery(sc,7.92,True)
cam=b.data.cameras.new('Inside the locker gallery');cam.lens=23;cam.clip_start=.04
o=b.data.objects.new(cam.name,cam);sc.collection.objects.link(o);o.location=(.32,1.82,9.48)
o.rotation_euler=(Vector((-.13,5.76,9.15))-o.location).to_track_quat('-Z','Y').to_euler()
sc.camera=o;b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Locker_Gallery.blend'))
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_percentage=100
sc.render.resolution_x=1152;sc.render.resolution_y=768;sc.render.image_settings.file_format='PNG'
sc.render.filepath=os.path.join(out,'Locker_gallery.png');b.ops.render.render(write_still=True)
cam.type='PANO';cam.panorama_type='EQUIRECTANGULAR';o.location=(0,3.16,9.44);o.rotation_euler=(math.pi/2,0,0)
sc.render.resolution_x=512;sc.render.resolution_y=256;sc.cycles.samples=8;sc.render.image_settings.file_format='HDR'
sc.render.filepath=os.path.join(out,'Room_03.hdr');b.ops.render.render(write_still=True)
