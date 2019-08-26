# This script creates a new square in the source object data and sends it back
import bpy
import bmesh
import time

# NOTE: Reference blend data from source file directly if 'use_blend_file' is True or data block was passed with 'passed_data_blocks' parameter
mesh = bpy.data.meshes.get(mesh_name)
bm = bmesh.new()
bm.from_mesh(mesh)
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(mesh)
obj = bpy.data.objects.new("Square Object", mesh)
pi = 3.14159

update_job_progress(0.01)

for i in range(100):
    time.sleep(0.05)
    update_job_progress((i + 2) / 100)

# set 'data_blocks' equal to dictionary of python data to be sent back to the Blender host
python_data = {"pi":pi}

# set 'data_blocks' equal to list of object data to be sent back to the Blender host
data_blocks = [obj]
