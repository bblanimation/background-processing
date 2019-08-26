# This script applies a remesh modifier
import bpy
import time

# NOTE: Reference blend data from source file directly if 'use_blend_file' is True or data block was passed with 'passed_data_blocks' parameter
obj = bpy.data.objects.get(obj_name)
rMod = obj.modifiers.new(obj.name + "_remesh", "REMESH")
if bpy.app.version < (2,80,0):
    m = obj.to_mesh(bpy.context.scene, apply_modifiers=True, settings="PREVIEW")
else:
    m = bpy.data.meshes.new_from_object(obj)
m.name = obj_name + "_remesh"
pi = 3.14159
update_job_progress(0.2)

for i in range(5):
    time.sleep(0.5)
    update_job_progress((i + 2) / 6)


# set 'data_blocks' equal to dictionary of python data to be sent back to the Blender host
python_data = {"pi":pi}

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [obj]
