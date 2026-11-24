"""Finish the editable building and tuck the cafe chairs in for the pedestrian aisle."""
import bpy as b, os, math
from mathutils import Vector
base=os.path.join(os.path.dirname(os.path.abspath(__file__)),'models','Atrium')
def chairs():
    for o in b.context.scene.objects:
        if not o.name.startswith('Cafe tables and chairs'):continue
        vs=o.data.vertices
        for start in range(0,len(vs),8):
            chunk=[vs[i] for i in range(start,start+8)]
            c=sum((v.co for v in chunk),Vector())/8
            if c.y < -3:continue
            cx=min([4.17,6.63],key=lambda x:abs(c.x-x))
            if abs(c.x-cx)>.72:
                for v in chunk:v.co.x-=math.copysign(.23,c.x-cx)
        o.data.update()
b.ops.wm.open_mainfile(filepath=os.path.join(base,'Level_02.blend'));chairs()
b.ops.export_scene.gltf(filepath=os.path.join(base,'Walk_Level_02.glb'),export_cameras=False,export_lights=False)
b.ops.wm.open_mainfile(filepath=os.path.join(base,'Atrium_Building.blend'));chairs()
sc=b.context.scene
origin=b.data.objects.new('Finish mapping | metres',None);sc.collection.objects.link(origin)
for m in b.data.materials:
    if not m.use_nodes:continue
    name=m.name.lower()
    wood=any(t in name for t in ['maple','oak','walnut'])
    stone=any(t in name for t in ['sandstone','sand tile','travertine','limestone','pavement','plaster'])
    cloth=any(t in name for t in ['upholstery','plush','carpet'])
    if not(wood or stone or cloth):continue
    nodes=m.node_tree.nodes;wire=m.node_tree.links.new;p=nodes.get('Principled BSDF')
    color=list(p.inputs['Base Color'].default_value)
    coord=nodes.new('ShaderNodeTexCoord');coord.object=origin
    scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1.8,37,2.5) if wood else (6,6,6) if stone else (85,85,85)
    wire(coord.outputs['Object'],scale.inputs[0]);noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2;noise.inputs['Detail'].default_value=3.5
    noise.inputs['Distortion'].default_value=.32 if wood else .12;wire(scale.outputs[0],noise.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB');a,c=ramp.color_ramp.elements
    a.position=.22;c.position=.78;a.color=tuple(v*(.69 if wood else .83) for v in color[:3])+(1,);c.color=tuple(min(1,v*1.09) for v in color[:3])+(1,)
    wire(noise.outputs['Fac'],ramp.inputs[0]);wire(ramp.outputs[0],p.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.0013 if wood else .00085
    wire(noise.outputs['Fac'],bump.inputs['Height']);wire(bump.outputs[0],p.inputs['Normal'])
    p.inputs['Roughness'].default_value=.43 if wood else .66 if stone else .9
    if cloth:p.inputs['Sheen Weight'].default_value=.21
sc.render.engine='CYCLES';sc.cycles.samples=36;sc.cycles.use_denoising=True
sc.render.resolution_x=1440;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX'
# Small edge highlights on the unit-scale cabinetry, workstations and metalwork.
for o in sc.objects:
    if o.type!='MESH' or max(abs(v-1) for v in o.scale)>.001:continue
    if not any(t in o.name.lower() for t in ['cabinet','printer','table','carrel','workstation','refrigerator','landing doors','security reception','lockers']):continue
    bevel=o.modifiers.new('Softly eased edges','BEVEL');bevel.width=.008;bevel.segments=3
    bevel.limit_method='ANGLE';bevel.harden_normals=True
views=b.data.collections.new('Walkthrough | eye-level cameras');sc.collection.children.link(views)
def viewpoint(name,pos,target):
    cam=b.data.cameras.new(name);cam.lens=23;cam.clip_start=.045
    o=b.data.objects.new(name,cam);views.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
lobby=viewpoint('01 | Main entrance',(.14,-6.32,1.62),(-3.65,-.6,1.40))
viewpoint('02 | Learning commons',(-2.1,-3.8,5.58),(-1.4,3.8,5.45))
viewpoint('03 | Support lobby',(.1,-6.36,9.54),(0,.2,9.58))
b.context.preferences.filepaths.save_version=0
b.ops.wm.save_as_mainfile(filepath=os.path.join(base,'Atrium_Finished.blend'))
sc.camera=lobby;sc.render.resolution_y=864;sc.render.filepath=os.path.join(base,'Entrance_Eye_Level.png')
b.ops.render.render(write_still=True)
