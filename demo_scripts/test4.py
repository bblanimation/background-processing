#** DO NOT DELETE THIS LINE OR EDIT THE LINES ABOVE **#

### DO NOT EDIT THESE LINES ###

import bpy
import os
if bpy.data.filepath == "":
    for obj in bpy.data.objects:
        obj.name = "background_removed"
    for mesh in bpy.data.meshes:
        mesh.name = "background_removed"
data_blocks = []
objDirectory = os.path.join(sourceBlendFile, "Object")
meshDirectory = os.path.join(sourceBlendFile, "Mesh")
def appendFrom(directory, filename):
    filepath = directory + filename
    bpy.ops.wm.append(
        filepath=filepath,
        filename=filename,
        directory=directory)

### WRITE YOUR PYTHON CODE HERE ###

import bmesh
import time

appendFrom(meshDirectory, objName)
obj = bpy.data.objects.get(objName)
bm = bmesh.new()
bm.from_mesh(obj.data)
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(obj.data)
time.sleep(3)

### SET 'data_blocks' EQUAL TO LIST OF OBJECT DATA TO BE SEND BACK TO THE BLENDER HOST ###

data_blocks = [obj]

### DO NOT EDIT BEYOND THIS LINE ###

assert None not in data_blocks  # ensures that all data from data_blocks exists
if os.path.exists(storagePath):
    os.remove(storagePath)
bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)
