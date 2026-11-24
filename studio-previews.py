"""Render eye-level detail studies from the saved, editable Studio model."""
import bpy as b, os
from mathutils import Vector
sc=b.context.scene;out=os.path.dirname(b.data.filepath)
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.use_denoising=True
sc.render.resolution_x=1080;sc.render.resolution_y=720;sc.render.resolution_percentage=100
for name,pos,target,lens,power in [
    ('Nursery_objects',(3.95,2.05,1.74),(4.76,6.17,1.03),26,95),
    ('Botanical_detail',(-5.99,-2.62,2.24),(-6.41,-1.10,1.96),44,40),
    ('Study_workstations',(-5.85,-1.51,5.53),(-7.59,.55,5.24),31,66)]:
    cam=sc.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    b.ops.object.light_add(type='AREA',location=Vector(pos)+Vector((0,0,1)))
    o=b.context.object;o.data.energy=power;o.data.size=2.3;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.join(out,name+'.png');b.ops.render.render(write_still=True);b.data.objects.remove(o,do_unlink=True)
