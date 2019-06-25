# This script applies a remesh modifier
import bpy
import time

# NOTE: If 'use_blend_file' property enabled in 'add_job' call, reference blend data from source file directly.
# NOTE: Else, pull objects and meshes from source file using 'append_from(data_type:str, data_name:str)'.
append_from("Object", objName)
obj = bpy.data.objects.get(objName)
rMod = obj.modifiers.new(obj.name + "_remesh", "REMESH")
if bpy.app.version < (2,80,0):
    m = obj.to_mesh(bpy.context.scene, apply_modifiers=True, settings="PREVIEW")
else:
    m = bpy.data.meshes.new_from_object(obj)
m.name = objName + "_remesh"
pi = 3.14159
update_job_progress(0.2)

for i in range(5):
    time.sleep(0.5)
    update_job_progress((i + 2) / 6)


# set 'data_blocks' equal to dictionary of python data to be sent back to the Blender host
python_data = {"pi":pi}

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [obj]
