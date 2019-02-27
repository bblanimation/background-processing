import bpy
import time

# NOTE: If 'use_blend_file' property enabled in 'add_job' call, reference blend data from source file directly.
# NOTE: Else, pull objects and meshes from source file using 'appendFrom(data_type:str, data_name:str)'.
appendFrom("Object", objName)
obj = bpy.data.objects.get(objName)
rMod = obj.modifiers.new(obj.name + '_remesh', 'REMESH')
m = obj.to_mesh(bpy.context.scene, True, 'PREVIEW')
m.name = objName + "_remesh"
pi = 3.14159

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [obj]

# set 'data_blocks' equal to dictionary of python data to be sent back to the Blender host
python_data = {"pi":pi}
