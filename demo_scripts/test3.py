import bpy
import bmesh
import time

# NOTE: If 'use_blend_file' property enabled in 'add_job' call, reference blend data from source file directly.
# NOTE: Else, pull objects and meshes from source file using 'appendFrom(data_type:str, data_name:str)'.
appendFrom("Mesh", objName)
obj = bpy.data.objects.get(objName)
bm = bmesh.new()
bm.from_mesh(obj.data)
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(obj.data)
time.sleep(5)

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [obj]
