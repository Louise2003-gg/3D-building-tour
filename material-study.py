"""Author seamless metre-scale PBR surfaces, a groomed teddy pile, and local reflection probes.

Run with Blender -b --python material-study.py. All sources remain intact.
"""
import bpy as b, os, re, json, struct, zlib, math, random
import numpy as np
from mathutils import Vector
from math import pi, sin, cos
root=os.path.dirname(os.path.abspath(__file__))
base=os.path.join(root,'models','Atrium')
out=os.path.join(base,'MaterialStudy');maps=os.path.join(out,'Maps')
os.makedirs(maps,exist_ok=True)
catalog=json.load(open(os.path.join(root,'finish-library.json')))
surfaces=catalog['surfaces'];rules=catalog['rules']
def png(name,arr):
    a=np.uint8(np.rint(np.clip(arr,0,255)));h,w,ch=a.shape
    delta=a.copy();delta[:,1:]=a[:,1:]-a[:,:-1]
    def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v)&0xffffffff)
    raw=b''.join(b'\x01'+row.tobytes() for row in delta)
    with open(os.path.join(maps,name+'.png'),'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,8))+chunk(b'IEND',b''))
def make_map(name,recipe,seed):
    n=recipe['size'];rng=np.random.default_rng(seed);y,x=np.mgrid[:n,:n]/n
    def noise(w,h=None,X=x,Y=y):
        h=h or w;g=rng.uniform(-1,1,(h,w));i=np.floor(X*w).astype(int);j=np.floor(Y*h).astype(int)
        a=X*w-i;c=Y*h-j;a=a*a*(3-2*a);c=c*c*(3-2*c)
        return (g[j%h,i%w]*(1-a)+g[j%h,(i+1)%w]*a)*(1-c)+(g[(j+1)%h,i%w]*(1-a)+g[(j+1)%h,(i+1)%w]*a)*c
    broad=noise(5)+.38*noise(11)+.15*noise(29);fine=noise(n//3)
    if name=='timber':
        # Bent growth rings around a knot and long open vessel pores.
        dx=(x-.34+.5)%1-.5;dy=(y-.55+.5)%1-.5
        knot=np.exp(-(dx*dx/.012+dy*dy/.004))
        axis=y+.042*noise(2,4)+.011*noise(4,9)+.077*knot
        rings=(.5+.5*np.cos(2*pi*(axis*23+.28*np.sin(2*pi*x))))**6
        fibre=noise(11,220,x,axis);pores=np.maximum(0,noise(47,270,x,axis)-.40)**1.5
        tone=.53+.14*broad+.12*fibre-.23*rings-.47*pores-.19*knot
        ht=.22*fibre-.75*pores-.15*rings+.06*fine;rough=.52+.24*rings+.35*pores+.09*fine
    elif name=='pile':
        u=x+.10*noise(3,4)+.021*noise(10,9)
        strand=noise(290,29,u,y)+.34*noise(480,52,u+.007*broad,y)
        clump=noise(27,9,u,y);tips=np.maximum(0,strand-.29)
        ht=.38*strand+.38*clump+.20*tips;tone=.49+.19*clump+.18*strand+.11*tips;rough=.65+.19*clump+.12*fine
    elif name=='cloth':
        u=x+.0016*noise(9,45);v=y+.0018*noise(41,10)
        warp=np.cos(2*pi*u*69);weft=np.cos(2*pi*v*66)
        over=np.sin(pi*u*70)*np.sin(pi*v*66)
        yarn=np.maximum(warp+.40*over,weft-.40*over)
        ht=.48*yarn+.19*fine+.18*noise(40);tone=.43+.13*yarn+.12*fine+.09*broad;rough=.62-.10*yarn+.15*fine
    elif name=='mineral':
        drift=noise(3)+.29*noise(10)+.08*noise(40)
        vein=np.exp(-((np.sin(2*pi*(x+2*y+.48*drift)))/.10)**2)
        fleck=np.maximum(0,fine-.48)
        tone=.52+.18*drift-.25*vein-.19*fleck+.05*noise(82)
        ht=.12*fine-.14*vein;rough=.48+.26*vein+.14*fine
    elif name=='brushed':
        drag=noise(8,236)+.35*noise(28,128);ht=.34*drag+.08*fine
        tone=.5+.13*drag;rough=.48+.22*drag+.09*broad
    elif name=='plaster':
        grit=noise(56)+.7*fine;pit=np.maximum(0,noise(83)-.47)
        ht=.27*grit+.24*broad-.59*pit;tone=.50+.14*broad+.11*grit-.20*pit;rough=.57+.20*grit
    elif name=='paper':
        pulp=noise(110,39)+.48*noise(46,112);ht=.27*pulp+.19*fine;tone=.50+.13*pulp;rough=.50+.18*pulp+.1*fine
    elif name=='botanical':
        cells=noise(83,112);ht=.16*cells+.1*fine;tone=.50+.08*broad+.09*cells;rough=.52+.18*cells+.12*broad
    else:
        h=noise(73)+.4*fine;ht=.25*h;tone=.50+.14*broad+.12*h;rough=.50+.2*h+.12*noise(17)
    # R/G encode signed surface gradients; B is reflectance variation, A is roughness variation.
    gx=(np.roll(ht,-1,1)-np.roll(ht,1,1))*1.35;gy=(np.roll(ht,-1,0)-np.roll(ht,1,0))*1.35
    png(name,np.stack([.5-.5*np.tanh(gx),.5+.5*np.tanh(gy),tone,rough],axis=-1)*255)
for i,(name,rec) in enumerate(surfaces.items()):make_map(name,rec,1269+i)

b.ops.wm.open_mainfile(filepath=os.path.join(base,'Architectural','Atrium_Architectural.blend'))
sc=b.context.scene;deps=b.context.evaluated_depsgraph_get()
for im in list(b.data.images):
    label=re.sub(r'\.\d+$','',im.name).removesuffix('.png')
    if label in ('keys','studio','library','welcome','security','blocks','cartons'):
        path=os.path.join(base,'Studio','Textures',label+'.png')
        if os.path.exists(path) and im.size[0]<1536:
            hd=b.data.images.load(path);hd.pack();im.user_remap(hd)
bears=[o for o in sc.objects if o.type=='MESH' and o.name.startswith('Stitched toy')]
for me in {o.data for o in bears}:
    for i,m in enumerate(me.materials):
        if 'Sage enamel' in m.name:
            m=m.copy();m.name='Woven sage neckerchief';me.materials[i]=m
def family(m):
    if re.search('indicator|opal| led|emission|lighting|cove light|amber strip|concealed amber',m.name,re.I):return None
    return next((k for exp,k in rules if re.search(exp,m.name,re.I)),'polymer')
# Shared procedural mapping uses object-local physical coordinates rather than stretching the
# same image over a whole desk or a small drawer. The web version uses an equivalent extra UV set.
imgs={}
for name in surfaces:
    im=b.data.images.load(os.path.join(maps,name+'.png'));im.colorspace_settings.name='Non-Color';im.alpha_mode='CHANNEL_PACKED';im.pack();imgs[name]=im
materials={}
for m in list(b.data.materials):
    if not m.use_nodes:continue
    name=family(m);p=m.node_tree.nodes.get('Principled BSDF')
    if not name or not p:continue
    materials[m]=name;rec=surfaces[name];nodes=m.node_tree.nodes;link=m.node_tree.links.new
    uv=nodes.new('ShaderNodeUVMap');uv.uv_map='Surface metres'
    tex=nodes.new('ShaderNodeTexImage');tex.image=imgs[name];tex.label=name+' | surface response';link(uv.outputs[0],tex.inputs[0])
    ch=nodes.new('ShaderNodeSeparateColor');link(tex.outputs['Color'],ch.inputs[0])
    normal=nodes.new('ShaderNodeCombineColor');link(ch.outputs[0],normal.inputs[0]);link(ch.outputs[1],normal.inputs[1]);normal.inputs[2].default_value=1
    nm=nodes.new('ShaderNodeNormalMap');nm.uv_map=uv.uv_map;nm.inputs['Strength'].default_value=rec['bump'];link(normal.outputs[0],nm.inputs['Color']);link(nm.outputs[0],p.inputs['Normal'])
    rough=nodes.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=max(.02,rec['rough']-rec['spread']*.5);rough.inputs['To Max'].default_value=min(1,rec['rough']+rec['spread']*.5)
    link(tex.outputs['Alpha'],rough.inputs[0]);link(rough.outputs[0],p.inputs['Roughness'])
    tone=nodes.new('ShaderNodeMapRange');tone.inputs['To Min'].default_value=1-rec['variation'];tone.inputs['To Max'].default_value=1+rec['variation'];link(ch.outputs[2],tone.inputs[0])
    sock=p.inputs['Base Color'];source=sock.links[0].from_socket if sock.is_linked else None
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=sock.default_value
    if source:link(source,mix.inputs[1])
    link(tone.outputs[0],mix.inputs[2]);link(mix.outputs[0],sock)
    if name in ('cloth','pile'):p.inputs['Sheen Weight'].default_value=.53 if name=='pile' else .26
    anis=p.inputs.get('Anisotropic IOR Level') or p.inputs.get('Anisotropic')
    if name=='brushed' and anis:anis.default_value=.34
    if name in ('ceramic','timber'):p.inputs['Coat Weight'].default_value=.24 if name=='ceramic' else .13
for o in sc.objects:
    if o.type!='MESH' or not any(m in materials for m in o.data.materials):continue
    me=o.data
    if me.uv_layers.get('Surface metres'):continue
    uv=me.uv_layers.new(name='Surface metres',do_init=False)
    for f in me.polygons:
        mat=me.materials[f.material_index];rec=surfaces.get(materials.get(mat))
        if not rec:continue
        w,h=rec['span'];points=[o.matrix_world@me.vertices[me.loops[i].vertex_index].co for i in f.loop_indices]
        n=(points[1]-points[0]).cross(points[-1]-points[0]);axis=max(range(3),key=lambda j:abs(n[j]))
        for i,q in zip(f.loop_indices,points):
            a,c=(q.x,q.y) if axis==2 else (q.y,q.z) if axis==0 else (q.x,q.z)
            if axis!=2 and re.search('flut|batten|door|groove',mat.name,re.I):a,c=c,a
            uv.data[i].uv=(a/w,c/h)
    # Keep the authored print/leaf UV active for existing textures with an implicit UV input.
    if len(me.uv_layers)>1:me.uv_layers.active_index=0;me.uv_layers[0].active_render=True

# Actual velvet pile on plush parts only. Eyes, embroidered noses, scarves and paws stay readable.
assert bears,'No teddy surfaces'
template=bears[0];me=template.data;me.calc_loop_triangles()
tris=[t for t in me.loop_triangles if re.search('nap|plush',me.materials[t.material_index].name,re.I)]
rand=random.Random(862);picked=rand.choices(tris,weights=[t.area for t in tris],k=15000)
v=[];f=[];cols=[];fiber_normals=[]
for t in picked:
    i,j,k=[me.vertices[q] for q in t.vertices];a,c=rand.random(),rand.random()
    if a+c>1:a,c=1-a,1-c
    pt=i.co+(j.co-i.co)*a+(k.co-i.co)*c;n=(i.normal*(1-a-c)+j.normal*a+k.normal*c).normalized()
    if n.length<.5:continue
    direction=Vector((.12*sin(pt.x*10),-.13,-1));tangent=(direction-n*n.dot(direction)).normalized()
    side=n.cross(tangent).normalized()
    length=rand.uniform(.004,.0105);width=rand.uniform(.00085,.0017)
    rootpt=pt-n*.0005;mid=pt+n*length*.63+tangent*length*.23;tip=pt+n*length*.85+tangent*length*.70
    off=len(v);v.extend([rootpt-side*width,rootpt+side*width,mid+side*width*.58,mid-side*width*.58,tip])
    f.extend([(off,off+1,off+2,off+3),(off+3,off+2,off+4)])
    fiber_normals.extend([tuple((n+tangent*t).normalized()) for t in [-.13,-.13,.03,.03,.20]])
    col=(.64,.48,.28) if 'Oat' in me.materials[t.material_index].name else (.39,.20,.088)
    shade=rand.uniform(.73,1.22)
    cols.extend([tuple(min(1,x*shade*g) for x in col)+(1,) for g in [.73,.73,1,1,1.16]])
hair=b.data.meshes.new('Combed pile | shared geometry');hair.from_pydata(v,[],f);hair.update()
hair.polygons.foreach_set('use_smooth',np.ones(len(f),dtype=np.bool_))
hair.normals_split_custom_set_from_vertices(fiber_normals)
attr=hair.color_attributes.new(name='Fiber tint',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(cols,np.float32).ravel())
mat=b.data.materials.new('Velvet guard fibers');mat.use_nodes=True;p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.91;p.inputs['Sheen Weight'].default_value=.6
vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Fiber tint';mat.node_tree.links.new(vc.outputs[0],p.inputs['Base Color']);hair.materials.append(mat)
grooms=[]
for bear in bears:
    o=b.data.objects.new('Pile | '+bear.name,hair);sc.collection.objects.link(o);o.matrix_world=bear.matrix_world.copy();grooms.append(o)
b.ops.object.select_all(action='DESELECT')
for o in grooms:o.select_set(True)
b.context.view_layer.objects.active=grooms[0]
b.ops.export_scene.gltf(filepath=os.path.join(out,'Close_plush.glb'),use_selection=True,export_cameras=False,export_lights=False)
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Atrium_Material_Study.blend'))
# Real room probes for glossy finishes. Separate from the porcelain's planar floor reflection.
sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_percentage=100;sc.render.film_transparent=False
cam=b.data.cameras.new('Reflection probe');probe=b.data.objects.new(cam.name,cam);sc.collection.objects.link(probe);sc.camera=probe
cam.type='PANO';cam.panorama_type='EQUIRECTANGULAR';probe.rotation_euler=(pi/2,0,0)
for lev,pos in enumerate([(-.25,-2.8,1.45),(-2.6,-1,5.55),(0,-2.95,9.52)]):
    probe.location=pos;sc.render.resolution_x=512;sc.render.resolution_y=256
    sc.render.image_settings.file_format='HDR';sc.render.filepath=os.path.join(out,f'Room_0{lev+1}.hdr');b.ops.render.render(write_still=True)
sc.render.image_settings.file_format='PNG';cam.type='PERSP';cam.lens=44
sc.cycles.samples=20;sc.render.resolution_x=1120;sc.render.resolution_y=760
for name,pos,target,lens in [('Plush_and_oak',(5.42,3.02,1.46),(6.51,6.22,.98),34),('Workstation_finish',(-6.05,-1.27,5.44),(-7.58,-.10,5.20),44),('Suite_textiles',(-5.86,-1.98,9.27),(-7.16,-.99,8.79),17)]:
    cam.lens=lens;probe.location=pos;probe.rotation_euler=(Vector(target)-probe.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.join(out,name+'.png');b.ops.render.render(write_still=True)
