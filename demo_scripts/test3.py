objName = 'GEO-sintel_proxy'  # DO NOT DELETE THIS LINE
sourceBlendFile = '/Users/cgear13/scripts/my_scripts/resources/blender_test_files/walk_cycle.blend'  # DO NOT DELETE THIS LINE
storagePath = '/tmp/background_processing/test3_data.blend'  # DO NOT DELETE THIS LINE
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
objDirectory = "%(sourceBlendFile)s/Object/" % locals()
meshDirectory = "%(sourceBlendFile)s/Mesh/" % locals()
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
m = bpy.data.meshes.get(objName)
bm = bmesh.new()
bm.from_mesh(m)
v1 = bm.verts.new(( 2,  2, 0))
v2 = bm.verts.new((-2,  2, 0))
v3 = bm.verts.new((-2, -2, 0))
v4 = bm.verts.new(( 2, -2, 0))
f1 = bm.faces.new((v1, v2, v3, v4))
bm.to_mesh(m)
time.sleep(6)

### SET 'data_blocks' EQUAL TO LIST OF OBJECT DATA TO BE SEND BACK TO THE BLENDER HOST ###

data_blocks = [m]

### DO NOT EDIT BEYOND THIS LINE ###

assert None not in data_blocks  # ensures that all data from data_blocks exists
if os.path.exists(storagePath):
    os.remove(storagePath)
bpy.data.libraries.write(storagePath, set(data_blocks), fake_user=True)
