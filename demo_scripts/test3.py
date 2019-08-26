# This script bloats the source object with meta balls
import bpy
import bmesh
import time
import math

# NOTE: Reference blend data from source file directly if 'use_blend_file' is True or data block was passed with 'passed_data_blocks' parameter
source_ob = bpy.data.objects.get(obj_name)

meta_data = bpy.data.metaballs.new('Volume Data')
meta_obj = bpy.data.objects.new('Volume Object', meta_data)

last_progress = 0
for i,v in enumerate(source_ob.data.vertices):
    mb = meta_data.elements.new(type='BALL')
    mb.radius = 1.5
    mb.co = v.co
    time.sleep(1)
    progress = (i+1) / len(source_ob.data.vertices)
    if progress - last_progress > 0.1:
        update_job_progress(progress)
        last_progress = progress

scn = bpy.context.scene
if bpy.app.version < (2,80,0):
    scn.objects.link(meta_obj)
    scn.update()
else:
    scn.collection.objects.link(meta_obj)
    bpy.context.view_layer.depsgraph.update()


if bpy.app.version >= (2,80,0):
    out_me = bpy.data.meshes.new_from_object(meta_obj)
else:
    out_me = meta_obj.to_mesh(scn, apply_modifiers=True, settings='PREVIEW')
out_ob = bpy.data.objects.new('Volume Mesh Object', out_me)

bpy.data.objects.remove(meta_obj, do_unlink=True)
bpy.data.metaballs.remove(meta_data)

# set 'data_blocks' equal to dictionary of python data to be sent back to the Blender host
python_data = {}

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [out_ob]
